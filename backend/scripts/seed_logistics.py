"""
Seed script for GeorgJensen logistics database
Creates initial hubs, fleet vehicles, and test users
Run: python scripts/seed_logistics.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import (
    User, Hub, FleetVehicle, Handler, UserRole, HubStatus, 
    VehicleType, VehicleStatus, HandlerType, HandlerStatus
)
from app.core.security import SecurityUtils
from datetime import datetime, timedelta


def seed_hubs(db: Session) -> list:
    """Create initial hub/warehouse locations"""
    hubs = [
        Hub(
            name="Nairobi Central Hub",
            code="HUB-NRB",
            address="Karura Forest Rd, Nairobi",
            city="Nairobi",
            state="KE",
            postal_code="00100",
            latitude=-1.2872,
            longitude=36.8172,
            sorting_capacity=1000,
            storage_capacity=5000,
            operating_hours_start="06:00",
            operating_hours_end="22:00",
            manager_name="Jane Kimani",
            manager_email="jane.kimani@georjensen.local",
            manager_phone="+254701234567",
            status=HubStatus.active,
            is_regional_hub=True,
            total_capacity=5000,
            available_capacity=5000,
            notes="Primary sorting hub for Central Kenya",
        ),
        Hub(
            name="Mombasa Port Hub",
            code="HUB-MBA",
            address="Port Authority Road, Mombasa",
            city="Mombasa",
            state="KE",
            postal_code="80100",
            latitude=-4.0435,
            longitude=39.6682,
            sorting_capacity=800,
            storage_capacity=4000,
            operating_hours_start="07:00",
            operating_hours_end="20:00",
            manager_name="Ahmed Hassan",
            manager_email="ahmed.hassan@georjensen.local",
            manager_phone="+254712345678",
            status=HubStatus.active,
            is_regional_hub=True,
            total_capacity=4000,
            available_capacity=4000,
            notes="Port and international gateway hub",
        ),
        Hub(
            name="Kisumu East Hub",
            code="HUB-KSME",
            address="Jomo Kenyatta Avenue, Kisumu",
            city="Kisumu",
            state="KE",
            postal_code="40100",
            latitude=-0.1022,
            longitude=34.7617,
            sorting_capacity=500,
            storage_capacity=2000,
            operating_hours_start="08:00",
            operating_hours_end="18:00",
            manager_name="Peter Omondi",
            manager_email="peter.omondi@georjensen.local",
            manager_phone="+254722345679",
            status=HubStatus.active,
            is_regional_hub=False,
            parent_hub_id=None,  # Will be set after first hub is created
            total_capacity=2000,
            available_capacity=2000,
            notes="Regional hub for Western Kenya",
        ),
        Hub(
            name="Nakuru Distribution Center",
            code="HUB-NKR",
            address="Milimani Road, Nakuru",
            city="Nakuru",
            state="KE",
            postal_code="20100",
            latitude=-0.3031,
            longitude=36.0800,
            sorting_capacity=600,
            storage_capacity=3000,
            operating_hours_start="07:00",
            operating_hours_end="19:00",
            manager_name="Faith Kipchoge",
            manager_email="faith.kipchoge@georjensen.local",
            manager_phone="+254733456789",
            status=HubStatus.active,
            is_regional_hub=False,
            parent_hub_id=None,  # Will be set after first hub is created
            total_capacity=3000,
            available_capacity=3000,
            notes="Distribution hub for Rift Valley",
        ),
    ]
    
    for hub in hubs:
        db.add(hub)
    db.commit()
    
    # Set parent hubs for secondary zones
    for hub in hubs:
        if hub.code in ["HUB-KSME", "HUB-NKR"]:
            hub.parent_hub_id = hubs[0].id  # Parent is Nairobi Central
    
    db.commit()
    print(f"✓ Created {len(hubs)} hubs")
    return hubs


def seed_fleet(db: Session, hubs: list) -> list:
    """Create initial fleet vehicles"""
    vehicles = [
        # Nairobi fleet
        FleetVehicle(
            plate_number="KCT-100A",
            vin="1HGCM41JXMN109186",
            vehicle_type=VehicleType.van,
            brand="Nissan",
            model="NV200",
            year=2023,
            color="White",
            hub_id=hubs[0].id,
            weight_capacity=1500,
            volume_capacity=12,
            max_packages=50,
            status=VehicleStatus.available,
            registration_expiry=datetime.now() + timedelta(days=365),
            insurance_expiry=datetime.now() + timedelta(days=365),
            fuel_type="petrol",
            notes="Primary delivery van for Nairobi metro",
        ),
        FleetVehicle(
            plate_number="KCT-101B",
            vin="1HGCM41JXMN109187",
            vehicle_type=VehicleType.van,
            brand="Nissan",
            model="NV200",
            year=2023,
            color="White",
            hub_id=hubs[0].id,
            weight_capacity=1500,
            volume_capacity=12,
            max_packages=50,
            status=VehicleStatus.available,
            registration_expiry=datetime.now() + timedelta(days=365),
            insurance_expiry=datetime.now() + timedelta(days=365),
            fuel_type="petrol",
        ),
        FleetVehicle(
            plate_number="KCT-102C",
            vin="1HGCM41JXMN109188",
            vehicle_type=VehicleType.truck,
            brand="Isuzu",
            model="NPR",
            year=2022,
            color="Blue",
            hub_id=hubs[0].id,
            weight_capacity=5000,
            volume_capacity=40,
            max_packages=200,
            status=VehicleStatus.available,
            registration_expiry=datetime.now() + timedelta(days=365),
            insurance_expiry=datetime.now() + timedelta(days=365),
            fuel_type="diesel",
            notes="Heavy cargo truck for long haul",
        ),
        # Mombasa fleet
        FleetVehicle(
            plate_number="KCT-201D",
            vin="1HGCM41JXMN109189",
            vehicle_type=VehicleType.van,
            brand="Nissan",
            model="NV200",
            year=2023,
            color="White",
            hub_id=hubs[1].id,
            weight_capacity=1500,
            volume_capacity=12,
            max_packages=50,
            status=VehicleStatus.available,
            registration_expiry=datetime.now() + timedelta(days=365),
            insurance_expiry=datetime.now() + timedelta(days=365),
            fuel_type="petrol",
        ),
        # Kisumu fleet
        FleetVehicle(
            plate_number="KCT-301E",
            vin="1HGCM41JXMN109190",
            vehicle_type=VehicleType.car,
            brand="Toyota",
            model="Hiace",
            year=2022,
            color="White",
            hub_id=hubs[2].id,
            weight_capacity=1000,
            volume_capacity=10,
            max_packages=40,
            status=VehicleStatus.available,
            registration_expiry=datetime.now() + timedelta(days=365),
            insurance_expiry=datetime.now() + timedelta(days=365),
            fuel_type="petrol",
        ),
    ]
    
    for vehicle in vehicles:
        db.add(vehicle)
    db.commit()
    print(f"✓ Created {len(vehicles)} fleet vehicles")
    return vehicles


def seed_handlers(db: Session, hubs: list) -> list:
    """Create handler/staff users"""
    handlers_data = [
        # Warehouse managers
        {
            "email": "manager.nrb@georjensen.local",
            "password": "Manager@123",
            "full_name": "Daniel Kiplagat",
            "role": UserRole.warehouse_manager,
            "handler_type": HandlerType.warehouse_staff,
            "hub_id": hubs[0].id,
            "phone": "+254701111111",
            "license_number": None,
        },
        # Drivers
        {
            "email": "driver.nrb.1@georjensen.local",
            "password": "Driver@123",
            "full_name": "Robert Mwangi",
            "role": UserRole.driver,
            "handler_type": HandlerType.driver,
            "hub_id": hubs[0].id,
            "phone": "+254702222222",
            "license_number": "DL-2024-001",
        },
        {
            "email": "driver.nrb.2@georjensen.local",
            "password": "Driver@123",
            "full_name": "Samuel Kipchoge",
            "role": UserRole.driver,
            "handler_type": HandlerType.driver,
            "hub_id": hubs[0].id,
            "phone": "+254703333333",
            "license_number": "DL-2024-002",
        },
        {
            "email": "driver.mba@georjensen.local",
            "password": "Driver@123",
            "full_name": "Mohammed Ali",
            "role": UserRole.driver,
            "handler_type": HandlerType.driver,
            "hub_id": hubs[1].id,
            "phone": "+254704444444",
            "license_number": "DL-2024-003",
        },
        # Warehouse staff
        {
            "email": "handler.nrb.1@georjensen.local",
            "password": "Handler@123",
            "full_name": "Grace Njeri",
            "role": UserRole.handler,
            "handler_type": HandlerType.warehouse_staff,
            "hub_id": hubs[0].id,
            "phone": "+254705555555",
            "license_number": None,
        },
        {
            "email": "handler.nrb.2@georjensen.local",
            "password": "Handler@123",
            "full_name": "James Kabui",
            "role": UserRole.handler,
            "handler_type": HandlerType.warehouse_staff,
            "hub_id": hubs[0].id,
            "phone": "+254706666666",
            "license_number": None,
        },
    ]
    
    handlers = []
    for handler_data in handlers_data:
        # Create user first
        user = User(
            email=handler_data["email"],
            full_name=handler_data["full_name"],
            hashed_password=SecurityUtils.get_password_hash(handler_data["password"]),
            is_active=True,
            role=handler_data["role"],
            assigned_hub_id=handler_data["hub_id"],
            phone=handler_data["phone"],
        )
        db.add(user)
        db.flush()  # Flush to get user ID
        
        # Create handler tied to user
        handler = Handler(
            user_id=user.id,
            full_name=handler_data["full_name"],
            email=handler_data["email"],
            phone=handler_data["phone"],
            handler_type=handler_data["handler_type"],
            hub_id=handler_data["hub_id"],
            status=HandlerStatus.active,
            license_number=handler_data.get("license_number"),
            license_expiry=datetime.now() + timedelta(days=365) if handler_data.get("license_number") else None,
            employee_id=f"EMP-{2024000 + len(handlers)}",
            hire_date=datetime.now() - timedelta(days=30),
        )
        db.add(handler)
        handlers.append(handler)
    
    db.commit()
    print(f"✓ Created {len(handlers)} handlers and staff")
    return handlers


def seed_admin_user(db: Session) -> User:
    """Create system admin user"""
    admin = User.query.filter_by(email="admin@georjensen.local").first() if hasattr(User, 'query') else None
    
    if admin:
        print("✓ Admin user already exists")
        return admin
    
    admin = User(
        email="admin@georjensen.local",
        full_name="System Administrator",
        hashed_password=SecurityUtils.get_password_hash("Admin@GeorgJensen123"),
        is_active=True,
        is_superuser=True,
        role=UserRole.system_admin,
        phone="+254700000000",
    )
    db.add(admin)
    db.commit()
    print("✓ Created system admin user")
    return admin


def main():
    """Run all seeding functions"""
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("SEEDING GEORGENSEN LOGISTICS DATABASE")
        print("="*80)
        
        # Check what still needs to be seeded
        existing_hubs = db.query(Hub).count()
        existing_handlers = db.query(Handler).count()
        existing_fleet = db.query(FleetVehicle).count()
        existing_admin = db.query(User).filter(User.role == UserRole.system_admin).count()
        
        print(f"\n📊 Current State:")
        print(f"  • Hubs: {existing_hubs}")
        print(f"  • Fleet: {existing_fleet}")
        print(f"  • Handlers: {existing_handlers}")
        print(f"  • Admin users: {existing_admin}")
        
        print("\nCreating missing infrastructure...")
        hubs = seed_hubs(db) if existing_hubs == 0 else db.query(Hub).all()
        fleet = seed_fleet(db, hubs) if existing_fleet == 0 else []
        handlers = seed_handlers(db, hubs) if existing_handlers == 0 else []
        admin = seed_admin_user(db) if existing_admin == 0 else None
        
        print("\n" + "="*80)
        print("SEEDING COMPLETE ✓")
        print("="*80)
        print(f"\n✓ Database State:")
        total_hubs = db.query(Hub).count()
        total_fleet = db.query(FleetVehicle).count()
        total_handlers = db.query(Handler).count()
        total_admins = db.query(User).filter(User.role == UserRole.system_admin).count()
        print(f"  • Total hubs: {total_hubs}")
        print(f"  • Total vehicles: {total_fleet}")
        print(f"  • Total handlers: {total_handlers}")
        print(f"  • Total admin users: {total_admins}")
        
        print(f"\n📝 Test Credentials:")
        print(f"  System Admin:")
        print(f"    Email: admin@georjensen.local")
        print(f"    Password: Admin@GeorgJensen123")
        print(f"\n  Warehouse Manager (Nairobi):")
        print(f"    Email: manager.nrb@georjensen.local")
        print(f"    Password: Manager@123")
        print(f"\n  Driver (Nairobi):")
        print(f"    Email: driver.nrb.1@georjensen.local")
        print(f"    Password: Driver@123")
        print(f"\n  Handler (Nairobi):")
        print(f"    Email: handler.nrb.1@georjensen.local")
        print(f"    Password: Handler@123")
        print("\n" + "="*80)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
