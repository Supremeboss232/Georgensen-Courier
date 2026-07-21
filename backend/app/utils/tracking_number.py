"""Tracking number generation and validation"""
import random
import string
from datetime import datetime


class TrackingNumberGenerator:
    """Generate and validate tracking numbers"""
    
    PREFIX = "GC"
    
    @staticmethod
    def generate() -> str:
        """Generate a new tracking number"""
        year = datetime.now().year
        random_suffix = ''.join(random.choices(string.digits, k=6))
        return f"{TrackingNumberGenerator.PREFIX}-{year}-{random_suffix}"
    
    @staticmethod
    def generate_with_order_id(order_id: int) -> str:
        """Generate tracking number based on order ID"""
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{TrackingNumberGenerator.PREFIX}-{order_id:06d}-{random_suffix}"
    
    @staticmethod
    def is_valid(tracking_number: str) -> bool:
        """Validate tracking number format"""
        parts = tracking_number.split('-')
        if len(parts) != 3:
            return False
        
        if parts[0] != TrackingNumberGenerator.PREFIX:
            return False
        
        if not parts[1].isdigit() or len(parts[1]) != 4:
            return False
        
        if not parts[2].isdigit() or len(parts[2]) != 6:
            return False
        
        return True
    
    @staticmethod
    def parse(tracking_number: str) -> dict:
        """Parse tracking number to extract components"""
        if not TrackingNumberGenerator.is_valid(tracking_number):
            return None
        
        parts = tracking_number.split('-')
        return {
            "prefix": parts[0],
            "order_id": int(parts[1]),
            "sequence": int(parts[2])
        }
