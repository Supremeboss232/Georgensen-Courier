#!/usr/bin/env python
"""Verify users exist and check password hashing"""
from app.db.base import SessionLocal
from app.db.models import User
from app.core.security import SecurityUtils

db = SessionLocal()
try:
    users = db.query(User).filter(User.is_active == True).all()
    
    print("\n" + "="*100)
    print("USER VERIFICATION - DATABASE CHECK")
    print("="*100)
    print(f"{'Email':<40} | {'Role':<20} | {'Has Hash':<10} | {'Hash Valid':<10}")
    print("-"*100)
    
    passwords = {
        'admin@example.com': 'Admin123!',
        'admin@georjensen.local': 'Admin@GeorgJensen123',
        'manager.nrb@georjensen.local': 'Manager@123',
        'driver.nrb.1@georjensen.local': 'Driver@123',
        'driver.nrb.2@georjensen.local': 'Driver@123',
        'driver.mba@georjensen.local': 'Driver@123',
        'handler.nrb.1@georjensen.local': 'Handler@123',
        'handler.nrb.2@georjensen.local': 'Handler@123',
    }
    
    for user in users:
        role = str(user.role).split('.')[-1] if hasattr(user.role, '__str__') else str(user.role)
        has_hash = "✓" if user.hashed_password else "✗"
        
        # Test password verification
        test_password = passwords.get(user.email)
        if test_password and user.hashed_password:
            is_valid = "✓" if SecurityUtils.verify_password(test_password, user.hashed_password) else "✗"
        else:
            is_valid = "?"
        
        print(f"{user.email:<40} | {role:<20} | {has_hash:<10} | {is_valid:<10}")
    
    print("="*100)
    print("\n✓ = User exists with valid password hash")
    print("✗ = Issue found")
    print("? = Cannot verify")
    print("\n" + "="*100 + "\n")
    
finally:
    db.close()
