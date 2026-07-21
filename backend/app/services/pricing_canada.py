from typing import Dict, Tuple, Optional
from enum import Enum
from datetime import datetime
import math

class CanadianTaxJurisdiction(str, Enum):
    """Canadian provincial tax rates"""
    ON_HST = "ON"    # Ontario - 13% HST
    QC_GST_PST = "QC"  # Quebec - 5% GST + 9.975% PST = 14.975%
    BC_GST_PST = "BC"  # British Columbia - 5% GST + 7% PST = 12%
    AB_GST = "AB"      # Alberta - 5% GST only
    MB_GST_PST = "MB"  # Manitoba - 5% GST + 8% PST = 13%
    SK_GST_PST = "SK"  # Saskatchewan - 5% GST + 6% PST = 11%
    NS_HST = "NS"      # Nova Scotia - 15% HST
    NB_HST = "NB"      # New Brunswick - 15% HST
    PE_HST = "PE"      # PEI - 15% HST
    NL_HST = "NL"      # Newfoundland & Labrador - 15% HST

class ShippingZone(str, Enum):
    """Zone-based pricing for Backtree logistics"""
    ZONE_1_INTRACITY = "zone_1"      # Same-day courier within metro area
    ZONE_2_REGIONAL = "zone_2"       # 2-3 day regional trucking
    ZONE_3_CONTINENTAL = "zone_3"    # Cross-country/cross-border
    ZONE_4_AIR = "zone_4"            # Express air freight
    ZONE_5_OCEAN = "zone_5"          # Ocean freight (LCL/FCL)

class CanadianPricingService:
    """Enterprise pricing service for Canadian-based global logistics"""
    
    # Base rates in CAD
    BASE_RATES = {
        ShippingZone.ZONE_1_INTRACITY: 8.00,
        ShippingZone.ZONE_2_REGIONAL: 45.00,
        ShippingZone.ZONE_3_CONTINENTAL: 85.00,
        ShippingZone.ZONE_4_AIR: 120.00,
        ShippingZone.ZONE_5_OCEAN: 250.00,
    }
    
    # Distance-based surcharges (per km)
    DISTANCE_RATES = {
        ShippingZone.ZONE_1_INTRACITY: 0.75,      # $0.75/km local
        ShippingZone.ZONE_2_REGIONAL: 0.45,       # $0.45/km regional
        ShippingZone.ZONE_3_CONTINENTAL: 0.25,    # $0.25/km long-haul
        ShippingZone.ZONE_4_AIR: 0.15,            # $0.15/km air (volumetric)
        ShippingZone.ZONE_5_OCEAN: 0.05,          # $0.05/km ocean (container-based)
    }
    
    # Weight-based surcharges (per kg)
    WEIGHT_RATES = {
        ShippingZone.ZONE_1_INTRACITY: 3.00,      # $3/kg local
        ShippingZone.ZONE_2_REGIONAL: 2.50,       # $2.50/kg regional
        ShippingZone.ZONE_3_CONTINENTAL: 2.00,    # $2/kg long-haul
        ShippingZone.ZONE_4_AIR: 5.00,            # $5/kg air (premium)
        ShippingZone.ZONE_5_OCEAN: 0.75,          # $0.75/kg ocean (volume-based)
    }
    
    # Service speed multipliers
    SERVICE_MULTIPLIERS = {
        "economy": 0.80,        # 20% discount for 5-7 day service
        "standard": 1.00,       # Base rate (2-3 days)
        "express": 1.50,        # 50% premium for 24-hour
        "overnight": 2.00,      # 100% premium for overnight
    }
    
    # Customs & cross-border fees
    CUSTOMS_HANDLING_FEE = 50.00  # CAD per shipment crossing border (matches privacy policy disclosure)
    
    # Fuel surcharge (dynamic - would be updated regularly)
    FUEL_SURCHARGE_RATE = 0.12    # 12% of subtotal
    
    # Tax rates by province
    TAX_RATES = {
        CanadianTaxJurisdiction.ON_HST: 0.13,
        CanadianTaxJurisdiction.QC_GST_PST: 0.14975,
        CanadianTaxJurisdiction.BC_GST_PST: 0.12,
        CanadianTaxJurisdiction.AB_GST: 0.05,
        CanadianTaxJurisdiction.MB_GST_PST: 0.13,
        CanadianTaxJurisdiction.SK_GST_PST: 0.11,
        CanadianTaxJurisdiction.NS_HST: 0.15,
        CanadianTaxJurisdiction.NB_HST: 0.15,
        CanadianTaxJurisdiction.PE_HST: 0.15,
        CanadianTaxJurisdiction.NL_HST: 0.15,
    }
    
    # Postal code to province mapping (first letter of Canadian postal code)
    POSTAL_TO_PROVINCE = {
        'A': CanadianTaxJurisdiction.NL_HST,    # NL
        'B': CanadianTaxJurisdiction.NS_HST,    # NS
        'C': CanadianTaxJurisdiction.PE_HST,    # PE
        'E': CanadianTaxJurisdiction.NB_HST,    # NB
        'G': CanadianTaxJurisdiction.QC_GST_PST,  # QC
        'H': CanadianTaxJurisdiction.QC_GST_PST,  # QC
        'J': CanadianTaxJurisdiction.QC_GST_PST,  # QC
        'K': CanadianTaxJurisdiction.ON_HST,    # ON
        'L': CanadianTaxJurisdiction.ON_HST,    # ON
        'M': CanadianTaxJurisdiction.ON_HST,    # ON
        'N': CanadianTaxJurisdiction.ON_HST,    # ON
        'P': CanadianTaxJurisdiction.ON_HST,    # ON
        'R': CanadianTaxJurisdiction.MB_GST_PST,  # MB
        'S': CanadianTaxJurisdiction.SK_GST_PST,  # SK
        'T': CanadianTaxJurisdiction.AB_GST,    # AB
        'V': CanadianTaxJurisdiction.BC_GST_PST,  # BC
        'X': CanadianTaxJurisdiction.MB_GST_PST,  # MB (Territories shared)
        'Y': CanadianTaxJurisdiction.AB_GST,    # YT/Territories (5% GST)
        'Z': CanadianTaxJurisdiction.AB_GST,    # Postal codes not yet assigned
    }
    
    @classmethod
    def detect_province_from_postal(cls, postal_code: str) -> Optional[CanadianTaxJurisdiction]:
        """Extract province from Canadian postal code (first letter)"""
        if not postal_code or len(postal_code) < 1:
            return CanadianTaxJurisdiction.ON_HST  # Default to Ontario
        
        first_letter = postal_code[0].upper()
        return cls.POSTAL_TO_PROVINCE.get(first_letter, CanadianTaxJurisdiction.ON_HST)
    
    @classmethod
    def determine_zone(
        cls,
        origin_postal: str,
        destination_postal: str,
        origin_country: str = "CA",
        destination_country: str = "CA",
        service_type: str = "air",
        distance_km: float = 0
    ) -> ShippingZone:
        """
        Determine shipping zone based on origin, destination, and service type.
        This implements the "Backtree" zone logic.
        """
        
        # International shipments
        if origin_country != destination_country:
            if service_type == "air":
                return ShippingZone.ZONE_4_AIR
            elif service_type == "ocean":
                return ShippingZone.ZONE_5_OCEAN
            else:
                return ShippingZone.ZONE_3_CONTINENTAL
        
        # Domestic Canadian shipments
        origin_province = cls.detect_province_from_postal(origin_postal)
        dest_province = cls.detect_province_from_postal(destination_postal)
        
        # Same province = regional or intra-city
        if origin_province == dest_province:
            if distance_km < 15:
                return ShippingZone.ZONE_1_INTRACITY
            else:
                return ShippingZone.ZONE_2_REGIONAL
        else:
            # Different provinces = continental
            return ShippingZone.ZONE_3_CONTINENTAL
    
    @classmethod
    def calculate_quote(
        cls,
        origin_postal: str,
        destination_postal: str,
        weight_kg: float,
        distance_km: float = 100,
        service_type: str = "standard",
        origin_country: str = "CA",
        destination_country: str = "CA",
        item_type: str = "documents",
        origin_province: Optional[str] = None,
    ) -> Dict:
        """
        Calculate complete quote with Canadian tax, currency, and zone-based pricing
        
        Returns:
            dict with pricing breakdown, tax info, and total in CAD
        """
        
        # Determine zone
        zone = cls.determine_zone(
            origin_postal,
            destination_postal,
            origin_country,
            destination_country,
            service_type,
            distance_km
        )
        
        # Get tax jurisdiction from destination postal code
        tax_jurisdiction = cls.detect_province_from_postal(destination_postal)
        tax_rate = cls.TAX_RATES.get(tax_jurisdiction, 0.13)
        
        # Calculate base components
        config = {
            "base_fare": cls.BASE_RATES.get(zone, cls.BASE_RATES[ShippingZone.ZONE_2_REGIONAL]),
            "distance_rate": cls.DISTANCE_RATES.get(zone, 0.5),
            "weight_rate": cls.WEIGHT_RATES.get(zone, 2.0),
        }
        
        base_fare = config["base_fare"]
        distance_charge = distance_km * config["distance_rate"]
        weight_charge = weight_kg * config["weight_rate"]
        
        # Apply service speed multiplier
        speed_multiplier = cls.SERVICE_MULTIPLIERS.get(service_type, 1.0)
        subtotal = (base_fare + distance_charge + weight_charge) * speed_multiplier
        
        # Add cross-border customs fee if applicable
        customs_fee = 0
        if origin_country != destination_country:
            customs_fee = cls.CUSTOMS_HANDLING_FEE
            subtotal += customs_fee
        
        # Apply fuel surcharge
        fuel_surcharge = subtotal * cls.FUEL_SURCHARGE_RATE
        
        # Subtotal before tax
        subtotal_with_fuel = subtotal + fuel_surcharge
        
        # Calculate tax based on destination province
        tax_amount = subtotal_with_fuel * tax_rate
        
        # Total price
        total_price = subtotal_with_fuel + tax_amount
        
        return {
            "currency": "CAD",
            "origin_postal": origin_postal,
            "destination_postal": destination_postal,
            "distance_km": distance_km,
            "weight_kg": weight_kg,
            "zone": zone.value,
            "service_type": service_type,
            "tax_jurisdiction": tax_jurisdiction.value,
            "base_fare": round(base_fare, 2),
            "distance_charge": round(distance_charge, 2),
            "weight_charge": round(weight_charge, 2),
            "customs_fee": round(customs_fee, 2),
            "fuel_surcharge": round(fuel_surcharge, 2),
            "subtotal": round(subtotal_with_fuel, 2),
            "tax_rate": round(tax_rate * 100, 2),
            "tax_amount": round(tax_amount, 2),
            "total_price": round(total_price, 2),
            "breakdown": {
                "base": round(base_fare, 2),
                "distance": round(distance_charge, 2),
                "weight": round(weight_charge, 2),
                "customs": round(customs_fee, 2),
                "fuel": round(fuel_surcharge, 2),
                "tax": round(tax_amount, 2),
                "total": round(total_price, 2),
            }
        }
    
    @classmethod
    def convert_to_usd(cls, cad_amount: float, exchange_rate: float = 0.74) -> float:
        """Convert CAD to USD using exchange rate"""
        return round(cad_amount * exchange_rate, 2)
    
    @classmethod
    def convert_from_usd(cls, usd_amount: float, exchange_rate: float = 1.35) -> float:
        """Convert USD to CAD using exchange rate"""
        return round(usd_amount * exchange_rate, 2)
    
    @classmethod
    def estimate_delivery_time(
        cls,
        zone: ShippingZone,
        service_type: str
    ) -> Tuple[int, int]:
        """
        Return estimated delivery time as (min_days, max_days)
        """
        base_times = {
            ShippingZone.ZONE_1_INTRACITY: (0, 1),      # Same day to next day
            ShippingZone.ZONE_2_REGIONAL: (2, 3),       # 2-3 days
            ShippingZone.ZONE_3_CONTINENTAL: (3, 5),    # 3-5 days
            ShippingZone.ZONE_4_AIR: (2, 5),            # 2-5 days international
            ShippingZone.ZONE_5_OCEAN: (7, 21),         # 7-21 days international
        }
        
        min_days, max_days = base_times.get(zone, (2, 5))
        
        # Adjust for service type
        if service_type == "economy":
            return (max_days, max_days + 2)
        elif service_type == "overnight":
            return (1, 1)
        else:
            return (min_days, max_days)
