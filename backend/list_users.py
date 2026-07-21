#!/usr/bin/env python
"""List all active users with their roles"""
from app.db.base import SessionLocal
from app.db.models import User

db = SessionLocal()
try:
    users = db.query(User).filter(User.is_active == True).all()
    
    print("\n" + "="*90)
    print("ACTIVE USER ACCOUNTS - LOGIN CREDENTIALS")
    print("="*90)
    print(f"{'Email':<45} | {'Role':<20} | Password")
    print("-"*90)
    
    # Map of emails to known passwords from seed data
    passwords = {
        'admin@georjensen.local': 'Admin@GeorgJensen123',
        'admin@example.com': 'Admin123!',
        'manager.nrb@georjensen.local': 'Manager@123',
        'driver.nrb.1@georjensen.local': 'Driver@123',
        'driver.nrb.2@georjensen.local': 'Driver@123',
        'driver.mba@georjensen.local': 'Driver@123',
        'handler.nrb.1@georjensen.local': 'Handler@123',
        'handler.nrb.2@georjensen.local': 'Handler@123',
    }
    
    for user in users:
        role = str(user.role).split('.')[-1] if hasattr(user.role, '__str__') else str(user.role)
        password = passwords.get(user.email, '(Set during registration)')
        print(f"{user.email:<45} | {role:<20} | {password}")
    
    print("="*90)
    print(f"\nTotal Active Users: {len(users)}")
    print("\n💡 TIP: Use these credentials to log in at http://127.0.0.1:4000")
    print("="*90 + "\n")
    
finally:
    db.close()
