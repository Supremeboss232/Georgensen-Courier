#!/usr/bin/env python
"""
Database initialization script for GeorgJensen
Runs migrations and seeds database
Usage: python scripts/init_db.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Run a shell command and report status"""
    print(f"\n{'='*80}")
    print(f"▶ {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=False,
        )
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e}")
        return False


def main():
    """Initialize database"""
    print("\n" + "="*80)
    print("GEORGENSEN DATABASE INITIALIZATION")
    print("="*80)
    
    # Step 1: Run Alembic migrations
    success = run_command(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        "Running Alembic migrations"
    )
    
    if not success:
        print("\n❌ Migration failed. Check configuration and database connection.")
        return False
    
    # Step 2: Seed database
    success = run_command(
        [sys.executable, "scripts/seed_logistics.py"],
        "Seeding logistics data"
    )
    
    if not success:
        print("\n❌ Seeding failed.")
        return False
    
    print("\n" + "="*80)
    print("✓ DATABASE INITIALIZATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Start the backend server: python -m uvicorn app.main:app --reload")
    print("  2. Check API docs: http://localhost:8000/api/docs")
    print("  3. Build frontend dashboards for each user role")
    print("="*80)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
