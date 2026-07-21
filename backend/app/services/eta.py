"""
ETA and Distance Calculation Service for Logistics
Calculates estimated delivery time based on distance, traffic patterns, and service type
"""
from datetime import datetime, timedelta
import math
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Shipment, Hub


def calculate_distance_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points on Earth using Haversine formula
    
    Args:
        lat1, lon1: Starting point latitude and longitude
        lat2, lon2: Ending point latitude and longitude
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def get_average_speed(service_type: str, speed: str) -> int:
    """
    Get average delivery speed based on service type and speed tier
    
    Args:
        service_type: 'local', 'intercity', 'international'
        speed: 'economy', 'standard', 'express'
    
    Returns:
        Average speed in km/h
    """
    speed_matrix = {
        'local': {
            'economy': 30,      # City traffic, multiple stops
            'standard': 40,
            'express': 50,
        },
        'intercity': {
            'economy': 60,      # Highway, fewer stops
            'standard': 80,
            'express': 100,
        },
        'international': {
            'economy': 70,      # Mixed, includes border crossing delays
            'standard': 90,
            'express': 110,
        }
    }
    
    return speed_matrix.get(service_type, {}).get(speed, 50)


def calculate_eta(
    db: Session,
    shipment: Shipment,
    current_lat: Optional[float] = None,
    current_lon: Optional[float] = None,
    use_current_location: bool = True
) -> Tuple[datetime, float, int]:
    """
    Calculate Estimated Time of Arrival (ETA) for a shipment
    
    Args:
        db: Database session
        shipment: Shipment object
        current_lat: Current latitude (if None, uses packaging location)
        current_lon: Current longitude (if None, uses pickup location)
        use_current_location: If True, uses shipment's current location
    
    Returns:
        Tuple of (estimated_delivery_datetime, distance_km, estimated_hours)
    """
    try:
        # Determine starting point
        if use_current_location and shipment.latitude and shipment.longitude:
            start_lat = shipment.latitude
            start_lon = shipment.longitude
        elif current_lat and current_lon:
            start_lat = current_lat
            start_lon = current_lon
        else:
            # Use pickup location as fallback
            # Note: In production, you'd fetch actual coordinates or use geocoding
            start_lat = -1.2872  # Default (replace with actual logic)
            start_lon = 36.8172
        
        # Destination point
        delivery_lat = shipment.latitude if shipment.latitude else -1.2872
        delivery_lon = shipment.longitude if shipment.longitude else 36.8172
        
        # Calculate distance
        distance_km = calculate_distance_haversine(
            start_lat, start_lon,
            delivery_lat, delivery_lon
        )
        
        # Get appropriate speed
        avg_speed = get_average_speed(shipment.service_type, shipment.speed)
        
        # Account for service type delays
        delay_hours = {
            'local': 0.5,          # Local pickup/delivery prep
            'intercity': 1.0,      # Hub sorting time
            'international': 4.0,  # Customs and processing
        }.get(shipment.service_type, 0.5)
        
        # Calculate travel time
        travel_hours = distance_km / avg_speed if avg_speed > 0 else 1
        total_hours = travel_hours + delay_hours
        
        # Calculate ETA
        eta = datetime.utcnow() + timedelta(hours=total_hours)
        
        return eta, distance_km, int(total_hours)
        
    except Exception as e:
        # Fallback: use estimated delivery if already set
        if shipment.estimated_delivery:
            remaining_hours = max(1, (shipment.estimated_delivery - datetime.utcnow()).total_seconds() / 3600)
            return shipment.estimated_delivery, 0.0, int(remaining_hours)
        
        # Last resort: estimate 24 hours
        return datetime.utcnow() + timedelta(hours=24), 0.0, 24


def update_shipment_eta(db: Session, shipment_id: int) -> Optional[datetime]:
    """
    Update a shipment's ETA in the database
    
    Args:
        db: Database session
        shipment_id: Shipment ID
    
    Returns:
        Updated ETA datetime or None if shipment not found
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return None
    
    eta, distance, hours = calculate_eta(db, shipment)
    shipment.estimated_delivery = eta
    db.commit()
    
    return eta


def estimate_delivery_date_range(
    service_type: str,
    speed: str,
    distance_km: float
) -> Tuple[datetime, datetime]:
    """
    Get a delivery date range (best case, worst case)
    
    Args:
        service_type: Service type (local, intercity, international)
        speed: Speed tier (economy, standard, express)
        distance_km: Distance in kilometers
    
    Returns:
        Tuple of (earliest_possible, latest_possible) delivery times
    """
    base_speed = get_average_speed(service_type, speed)
    
    # Best case: optimal speed + minimal delays
    best_hours = (distance_km / (base_speed * 1.2)) + 0.25
    
    # Worst case: slower speed + traffic/delays
    worst_hours = (distance_km / (base_speed * 0.8)) + 2.0
    
    return (
        datetime.utcnow() + timedelta(hours=best_hours),
        datetime.utcnow() + timedelta(hours=worst_hours),
    )
