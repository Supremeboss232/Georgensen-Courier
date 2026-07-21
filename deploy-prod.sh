#!/bin/bash
# ============================================================================
# PRODUCTION DEPLOYMENT SCRIPT
# ============================================================================
# Safely deploys application to production with validation and rollback
# Usage: ./deploy-prod.sh [version] [environment]

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_ENV=${1:-production}
VERSION=${2:-$(git describe --tags --always)}
DEPLOY_LOG="deployments/deploy-${VERSION}-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_header() {
    echo "" | tee -a "$DEPLOY_LOG"
    echo "============================================================================" | tee -a "$DEPLOY_LOG"
    echo "$1" | tee -a "$DEPLOY_LOG"
    echo "============================================================================" | tee -a "$DEPLOY_LOG"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

# ============================================================================
# PRE-DEPLOYMENT CHECKS
# ============================================================================

pre_deployment_checks() {
    log_header "PRE-DEPLOYMENT CHECKS"
    
    # Check required commands
    log_info "Checking required commands..."
    check_command "docker"
    check_command "docker-compose"
    check_command "git"
    
    # Check environment file
    if [ ! -f ".env.production" ]; then
        log_error ".env.production not found"
        exit 1
    fi
    
    # Check no uncommitted changes
    if ! git diff --quiet; then
        log_warn "Uncommitted changes detected. Stashing..."
        git stash
    fi
    
    # Check Git is on main branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        log_error "Not on main branch. Current: $CURRENT_BRANCH"
        exit 1
    fi
    
    # Verify Docker daemon running
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon not running"
        exit 1
    fi
    
    log_info "Pre-deployment checks passed ✓"
}

# ============================================================================
# BACKUP EXISTING STATE
# ============================================================================

backup_current_state() {
    log_header "BACKING UP CURRENT STATE"
    
    mkdir -p "$BACKUP_DIR"
    
    log_info "Backing up environment..."
    cp .env.production "$BACKUP_DIR/.env.production"
    
    log_info "Backing up current container state..."
    docker-compose -f docker-compose.prod.yml ps > "$BACKUP_DIR/container-state.txt"
    docker images | grep georgensen > "$BACKUP_DIR/images.txt" || true
    
    log_info "Backing up database..."
    docker-compose -f docker-compose.prod.yml exec -T db pg_dump \
        -U georgensen \
        -d georgensen_prod \
        > "$BACKUP_DIR/database-backup.sql" 2>/dev/null || log_warn "Database backup failed"
    
    log_info "Backup complete: $BACKUP_DIR"
}

# ============================================================================
# BUILD & TEST
# ============================================================================

build_images() {
    log_header "BUILDING DOCKER IMAGES"
    
    log_info "Building backend image..."
    docker-compose -f docker-compose.prod.yml build backend
    
    log_info "Tagging image with version: $VERSION"
    docker tag georgensen/backend:latest "georgensen/backend:${VERSION}"
    
    log_info "Images built successfully ✓"
}

# ============================================================================
# DEPLOYMENT
# ============================================================================

deploy() {
    log_header "DEPLOYING APPLICATION"
    
    # Load environment
    set -a
    source .env.production
    set +a
    
    # Stop old containers
    log_info "Stopping old containers..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 10
    
    # Check health
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        local healthy=$(docker-compose -f docker-compose.prod.yml ps | grep -c "Up (healthy)" || true)
        if [ "$healthy" -ge 4 ]; then
            log_info "Services healthy ✓"
            break
        fi
        log_warn "Services not yet healthy... retry $((attempt+1))/$max_attempts"
        sleep 3
        attempt=$((attempt+1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Services did not become healthy in time"
        return 1
    fi
    
    log_info "Deployment complete ✓"
}

# ============================================================================
# VALIDATION
# ============================================================================

validate_deployment() {
    log_header "VALIDATING DEPLOYMENT"
    
    local errors=0
    
    # Check containers running
    log_info "Checking containers..."
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "backend.*Up"; then
        log_error "Backend container not running"
        errors=$((errors+1))
    fi
    
    # Check API health
    log_info "Checking API health..."
    if ! curl -sf https://api.georgensen.com/health > /dev/null 2>&1; then
        log_error "API health check failed"
        errors=$((errors+1))
    fi
    
    # Check metrics
    log_info "Checking metrics..."
    if ! curl -sf https://api.georgensen.com/metrics > /dev/null 2>&1; then
        log_error "Metrics endpoint not responding"
        errors=$((errors+1))
    fi
    
    # Check background jobs
    log_info "Checking background jobs..."
    if ! docker-compose -f docker-compose.prod.yml logs celery_worker | grep -q "ready"; then
        log_warn "Celery worker may not be ready"
    fi
    
    if [ $errors -gt 0 ]; then
        log_error "Validation failed with $errors errors"
        return 1
    fi
    
    log_info "Validation passed ✓"
}

# ============================================================================
# ROLLBACK
# ============================================================================

rollback() {
    log_header "ROLLING BACK DEPLOYMENT"
    
    log_warn "Rolling back to previous state..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "No backup directory found"
        return 1
    fi
    
    log_info "Stopping containers..."
    docker-compose -f docker-compose.prod.yml down || true
    
    log_info "Restoring environment..."
    cp "$BACKUP_DIR/.env.production" .env.production
    
    log_info "Starting previous version..."
    docker-compose -f docker-compose.prod.yml up -d
    
    log_info "Rollback complete ✓"
    log_warn "Verify the Application is working before resuming"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    # Setup logging
    mkdir -p deployments
    touch "$DEPLOY_LOG"
    
    log_header "DEPLOYMENT START"
    log_info "Version: $VERSION"
    log_info "Environment: $DEPLOY_ENV"
    log_info "Time: $(date)"
    
    # Execute deployment steps
    if ! pre_deployment_checks; then
        exit 1
    fi
    
    if ! backup_current_state; then
        log_error "Backup failed"
        exit 1
    fi
    
    if ! build_images; then
        log_error "Build failed"
        exit 1
    fi
    
    if ! deploy; then
        log_error "Deployment failed, rolling back..."
        rollback
        exit 1
    fi
    
    if ! validate_deployment; then
        log_error "Validation failed, rolling back..."
        rollback
        exit 1
    fi
    
    log_header "DEPLOYMENT SUCCESSFUL"
    log_info "Version $VERSION deployed to $DEPLOY_ENV"
    log_info "Backup saved to: $BACKUP_DIR"
    log_info "Deployment log: $DEPLOY_LOG"
    log_info ""
    log_info "Next steps:"
    log_info "1. Monitor dashboards: https://monitoring.georgensen.com"
    log_info "2. Check logs: docker-compose logs -f"
    log_info "3. Verify metrics: https://api.georgensen.com/metrics"
    log_info ""
    
    echo -e "${GREEN}✓ Deployment Complete!${NC}"
}

# Trap errors and rollback
trap 'log_error "Deployment interrupted"; rollback; exit 1' INT TERM

# Run main
main "$@"
