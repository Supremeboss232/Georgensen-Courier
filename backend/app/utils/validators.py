"""Data validation utilities"""
import re
from typing import Optional


class AddressValidator:
    """Validate address information"""
    
    @staticmethod
    def validate(
        street: str,
        city: str,
        state: str,
        postal_code: str,
        country: str = "AU"
    ) -> tuple[bool, Optional[str]]:
        """Validate address components"""
        
        if not street or len(street) < 5:
            return False, "Invalid street address"
        
        if not city or len(city) < 2:
            return False, "Invalid city"
        
        if not state or len(state) < 2:
            return False, "Invalid state"
        
        if country == "AU" and not PostalCodeValidator.validate_au(postal_code):
            return False, "Invalid postal code for Australia"
        
        return True, None


class PostalCodeValidator:
    """Validate postal codes for different countries"""
    
    @staticmethod
    def validate_au(postal_code: str) -> bool:
        """Validate Australian postal code (4 digits)"""
        if not postal_code:
            return False
        postal_code = postal_code.strip()
        return bool(re.match(r'^\d{4}$', postal_code))
    
    @staticmethod
    def validate_us(postal_code: str) -> bool:
        """Validate US ZIP code"""
        if not postal_code:
            return False
        postal_code = postal_code.strip()
        return bool(re.match(r'^\d{5}(-\d{4})?$', postal_code))
    
    @staticmethod
    def validate_uk(postal_code: str) -> bool:
        """Validate UK postcode"""
        if not postal_code:
            return False
        postal_code = postal_code.strip().upper()
        pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$'
        return bool(re.match(pattern, postal_code))


class PhoneValidator:
    """Validate phone numbers"""
    
    @staticmethod
    def validate_au(phone: str) -> bool:
        """Validate Australian phone number"""
        if not phone:
            return False
        phone = phone.strip().replace(' ', '').replace('-', '')
        # Accept +61 or 0 prefix
        return bool(re.match(r'^(\+61|0)\d{9,10}$', phone))
    
    @staticmethod
    def normalize_au(phone: str) -> str:
        """Normalize Australian phone number to +61 format"""
        phone = phone.strip().replace(' ', '').replace('-', '')
        if phone.startswith('0'):
            phone = '+61' + phone[1:]
        elif not phone.startswith('+61'):
            phone = '+61' + phone
        return phone


class EmailValidator:
    """Validate email addresses"""
    
    @staticmethod
    def validate(email: str) -> bool:
        """Validate email address format"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))


class WeightDimensionValidator:
    """Validate package weight and dimensions"""
    
    @staticmethod
    def validate_weight(weight: float, max_weight: float = 100) -> tuple[bool, Optional[str]]:
        """Validate package weight"""
        if weight <= 0:
            return False, "Weight must be greater than 0"
        if weight > max_weight:
            return False, f"Weight exceeds maximum of {max_weight}kg"
        return True, None
    
    @staticmethod
    def validate_dimensions(
        length: float,
        width: float,
        height: float,
        max_dimension: float = 300
    ) -> tuple[bool, Optional[str]]:
        """Validate package dimensions"""
        for dim in [length, width, height]:
            if dim <= 0:
                return False, "All dimensions must be greater than 0"
            if dim > max_dimension:
                return False, f"Dimension exceeds maximum of {max_dimension}cm"
        
        # Calculate volume
        volume = length * width * height
        if volume > 1000000:  # 1 cubic meter
            return False, "Package volume exceeds limits"
        
        return True, None
    
    @staticmethod
    def calculate_volume(length: float, width: float, height: float) -> float:
        """Calculate package volume"""
        return length * width * height
