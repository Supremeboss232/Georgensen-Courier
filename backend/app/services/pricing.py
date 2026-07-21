from typing import Dict, Tuple
from enum import Enum
import re

class PricingService:
    """Service for quote calculation and pricing"""
    
    PRICING_CONFIG = {
        "local": {
            "base_fare": 5.0,
            "distance_rate": 0.50,  # per km
            "weight_rate": 2.0      # per kg
        },
        "intercity": {
            "base_fare": 15.0,
            "distance_rate": 0.30,
            "weight_rate": 1.50
        },
        "international": {
            "base_fare": 50.0,
            "distance_rate": 0.15,
            "weight_rate": 1.0
        }
    }
    
    SPEED_MULTIPLIERS = {
        "economy": 0.8,      # 20% discount
        "standard": 1.0,     # base rate
        "express": 1.5       # 50% premium
    }
    
    INSURANCE_RATE = 0.05   # 5% of package value
    
    @classmethod
    def calculate_quote(
        cls,
        service_type: str,
        distance: float = 10,
        weight: float = 1,
        speed: str = "standard",
        package_value: float = 0
    ) -> Dict:
        """Calculate complete quote for an order"""
        
        config = cls.PRICING_CONFIG.get(service_type, cls.PRICING_CONFIG["local"])
        
        # Calculate components
        base_fare = config["base_fare"]
        distance_charge = distance * config["distance_rate"]
        weight_charge = weight * config["weight_rate"]
        
        # Apply speed multiplier
        speed_multiplier = cls.SPEED_MULTIPLIERS.get(speed, 1.0)
        subtotal = (base_fare + distance_charge + weight_charge) * speed_multiplier
        
        # Calculate insurance
        insurance_charge = 0
        if package_value > 0:
            insurance_charge = package_value * cls.INSURANCE_RATE
        
        # Total price
        total_price = subtotal + insurance_charge
        
        return {
            "base_fare": round(base_fare, 2),
            "distance_charge": round(distance_charge, 2),
            "weight_charge": round(weight_charge, 2),
            "speed_multiplier": speed_multiplier,
            "insurance_charge": round(insurance_charge, 2),
            "subtotal": round(subtotal, 2),
            "total_price": round(total_price, 2),
            "breakdown": {
                "base": base_fare,
                "distance": distance_charge,
                "weight": weight_charge,
                "speed": f"{speed}x{speed_multiplier}",
                "insurance": insurance_charge
            }
        }
    
    @classmethod
    def generate_tracking_number(cls, year_suffix: int = 26) -> str:
        """Generate tracking number in format GEO-YY-XXXXXX"""
        import secrets
        random_part = secrets.token_hex(3).upper()
        return f"GEO-{year_suffix}-{random_part}"    
    @classmethod
    def estimate_distance(cls, pickup_address: str, delivery_address: str, service_type: str = "local") -> float:
        """
        Estimate distance between addresses.
        
        For MVP: Uses simple estimation based on address length and service type.
        In production: Integrate with Google Maps Distance Matrix API or similar.
        
        Args:
            pickup_address: Pickup address string
            delivery_address: Delivery address string
            service_type: local, intercity, international
        
        Returns:
            Estimated distance in kilometers
        """
        # For MVP, use simple heuristics
        # In production, integrate with Google Maps, Mapbox, etc.
        
        if service_type == "international":
            # Default for international (placeholder until API integrated)
            return 5000.0
        elif service_type == "intercity":
            # Estimate for inter-city (typically 100-500 km)
            # This would be replaced with real geocoding API
            return 150.0
        else:
            # Local delivery estimation
            # Simple heuristic: different zip codes = longer distance
            pickup_zip = cls._extract_zip(pickup_address)
            delivery_zip = cls._extract_zip(delivery_address)
            
            if pickup_zip and delivery_zip:
                # If different zips, estimate longer distance
                distance = 5.0 if pickup_zip == delivery_zip else 15.0
            else:
                # Default local distance
                distance = 10.0
            
            return distance
    
    @staticmethod
    def _extract_zip(address: str) -> str:
        """Extract ZIP code from address string"""
        # Look for 5-digit pattern (US ZIP)
        match = re.search(r'\b\d{5}\b', address)
        return match.group(0) if match else None