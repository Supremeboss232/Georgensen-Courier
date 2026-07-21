#!/bin/bash
# Installation & Deployment Script for GeorgJensen
# Run from backend directory: bash ../DEPLOY.sh

echo ""
echo "================================================================================"
echo "  GEORGENSEN LOGISTICS - PRODUCTION DEPLOYMENT"
echo "================================================================================"
echo ""

# Check if running from backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must run from backend directory"
    echo "   cd backend && bash ../DEPLOY.sh"
    exit 1
fi

echo "▶ Step 1: Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✓ Dependencies installed"

echo ""
echo "▶ Step 2: Verifying database connection..."
python -c "
from app.core.config import settings
print(f'  Database URL: {settings.DATABASE_URL[:50]}...')
try:
    from app.db.base import engine
    with engine.connect() as conn:
        result = conn.execute('SELECT version();')
        version = result.fetchone()[0]
        print(f'  ✓ Connected to PostgreSQL')
        print(f'    {version}')
except Exception as e:
    print(f'  ❌ Connection failed: {e}')
    exit(1)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed"
    echo "   Check DATABASE_URL in app/core/config.py"
    exit 1
fi

echo ""
echo "▶ Step 3: Running database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Migration failed"
    exit 1
fi
echo "✓ Database schema updated"

echo ""
echo "▶ Step 4: Seeding initial logistics data..."
python scripts/seed_logistics.py

if [ $? -ne 0 ]; then
    echo "❌ Seeding failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo "  ✓ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Database Setup:"
echo "  • PostgreSQL 17.6 configured"
echo "  • 4 hubs created"
echo "  • Fleet vehicles initialized"
echo "  • Test users created"
echo ""
echo "Test Credentials:"
echo "  System Admin: admin@georjensen.local / Admin@GeorgJensen123"
echo "  Manager: manager.nrb@georjensen.local / Manager@123"
echo "  Driver: driver.nrb.1@georjensen.local / Driver@123"
echo ""
echo "Next Steps:"
echo "  1. Start server: python -m uvicorn app.main:app --reload"
echo "  2. View API docs: http://localhost:8000/api/docs"
echo "  3. Build frontend dashboards"
echo ""
echo "================================================================================"
