from typing import Dict
import re
import secrets


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
        "express": 1.5,      # 50% premium
        "overnight": 2.0     # 100% premium
    }
    
    INSURANCE_RATE = 0.05   # 5% of package value
    
    @classmethod
    def calculate_quote(
        cls,
        service_type: str = "local",
        distance: float = 10,
        weight: float = 1,
        speed: str = "standard",
        package_value: float = 0
    ) -> Dict:
        """Calculate complete quote for an order"""
        
        config = cls.PRICING_CONFIG.get(service_type, cls.PRICING_CONFIG["local"])
        
        base_fare = config["base_fare"]
        distance_charge = distance * config["distance_rate"]
        weight_charge = weight * config["weight_rate"]
        
        speed_multiplier = cls.SPEED_MULTIPLIERS.get(speed, 1.0)
        subtotal = (base_fare + distance_charge + weight_charge) * speed_multiplier
        
        insurance_charge = 0.0
        if package_value > 0:
            insurance_charge = package_value * cls.INSURANCE_RATE
        
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
                "base": round(base_fare, 2),
                "distance": round(distance_charge, 2),
                "weight": round(weight_charge, 2),
                "speed": f"{speed}x{speed_multiplier}",
                "insurance": round(insurance_charge, 2)
            }
        }
    
    @classmethod
    def generate_tracking_number(cls, year_suffix: int = 26) -> str:
        """Generate tracking number in format GEO-YY-XXXXXX"""
        random_part = secrets.token_hex(3).upper()
        return f"GEO-{year_suffix}-{random_part}"

    @classmethod
    def estimate_distance(cls, pickup_address: str, delivery_address: str, service_type: str = "local") -> float:
        """Estimate distance between addresses in kilometers."""
        if service_type == "international":
            return 5000.0
        elif service_type == "intercity":
            return 150.0
        else:
            pickup_zip = cls._extract_zip(pickup_address or "")
            delivery_zip = cls._extract_zip(delivery_address or "")
            if pickup_zip and delivery_zip:
                return 5.0 if pickup_zip == delivery_zip else 15.0
            return 10.0
    
    @staticmethod
    def _extract_zip(address: str) -> str:
        """Extract ZIP or postal code from address string"""
        match = re.search(r'\b\d{5}\b', address or "")
        return match.group(0) if match else None


PricingCalculator = PricingService
