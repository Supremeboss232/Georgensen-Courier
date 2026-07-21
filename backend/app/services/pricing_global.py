"""
Global Pricing Service for Georgensen Courier

Supports 6 major regions with localized pricing, taxes, and currency handling.
Integrates with regional carrier networks (FedEx, UPS, DHL, local couriers).

Regions:
1. North America (CA, US)
2. Europe (UK, EU, others)
3. Asia-Pacific (AU, SG, JP, HK, NZ)
4. Middle East & Africa (UAE, SA, AE, ZA, EG)
5. Latin America (MX, BR, AR, CL, CO)
"""

from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from app.services.pricing_canada import CanadianPricingService, ShippingZone

# ==============================
# Region and Currency Enums
# ==============================

class GlobalRegion(str, Enum):
    """Global regions supported by Georgensen"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST_AFRICA = "middle_east_africa"
    LATIN_AMERICA = "latin_america"


class RegionalCurrency(str, Enum):
    """Currencies by region"""
    # North America
    CAD = "CAD"
    USD = "USD"
    # Europe
    GBP = "GBP"  # UK
    EUR = "EUR"  # EU
    # Asia-Pacific
    AUD = "AUD"  # Australia
    SGD = "SGD"  # Singapore
    JPY = "JPY"  # Japan
    HKD = "HKD"  # Hong Kong
    NZD = "NZD"  # New Zealand
    # Middle East & Africa
    AED = "AED"  # UAE
    SAR = "SAR"  # Saudi Arabia
    ZAR = "ZAR"  # South Africa
    EGP = "EGP"  # Egypt
    # Latin America
    MXN = "MXN"  # Mexico
    BRL = "BRL"  # Brazil
    ARS = "ARS"  # Argentina
    CLP = "CLP"  # Chile
    COP = "COP"  # Colombia


class GlobalPricingService:
    """Enterprise global pricing service supporting 6 major regions"""

    # ==============================
    # Regional Country Mappings
    # ==============================

    REGION_COUNTRIES = {
        GlobalRegion.NORTH_AMERICA: ["CA", "US"],
        GlobalRegion.EUROPE: ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "IE"],
        GlobalRegion.ASIA_PACIFIC: ["AU", "SG", "JP", "HK", "NZ", "IN", "TH", "MY", "ID", "PH"],
        GlobalRegion.MIDDLE_EAST_AFRICA: ["AE", "SA", "KW", "QA", "BH", "ZA", "EG", "MA", "NG", "KE"],
        GlobalRegion.LATIN_AMERICA: ["MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC"],
    }

    COUNTRY_CURRENCY = {
        # North America
        "CA": RegionalCurrency.CAD,
        "US": RegionalCurrency.USD,
        # Europe
        "GB": RegionalCurrency.GBP,
        "DE": RegionalCurrency.EUR, "FR": RegionalCurrency.EUR, "IT": RegionalCurrency.EUR,
        "ES": RegionalCurrency.EUR, "NL": RegionalCurrency.EUR, "BE": RegionalCurrency.EUR,
        "AT": RegionalCurrency.EUR, "CH": RegionalCurrency.EUR, "SE": RegionalCurrency.EUR,
        "NO": RegionalCurrency.EUR, "DK": RegionalCurrency.EUR, "FI": RegionalCurrency.EUR,
        "PL": RegionalCurrency.EUR, "CZ": RegionalCurrency.EUR, "IE": RegionalCurrency.EUR,
        # Asia-Pacific
        "AU": RegionalCurrency.AUD,
        "SG": RegionalCurrency.SGD,
        "JP": RegionalCurrency.JPY,
        "HK": RegionalCurrency.HKD,
        "NZ": RegionalCurrency.NZD,
        "IN": RegionalCurrency.EUR,  # Using placeholder
        "TH": RegionalCurrency.EUR,
        "MY": RegionalCurrency.EUR,
        "ID": RegionalCurrency.EUR,
        "PH": RegionalCurrency.EUR,
        # Middle East & Africa
        "AE": RegionalCurrency.AED,
        "SA": RegionalCurrency.SAR,
        "KW": RegionalCurrency.AED,
        "QA": RegionalCurrency.AED,
        "BH": RegionalCurrency.AED,
        "ZA": RegionalCurrency.ZAR,
        "EG": RegionalCurrency.EGP,
        "MA": RegionalCurrency.EUR,
        "NG": RegionalCurrency.EUR,
        "KE": RegionalCurrency.EUR,
        # Latin America
        "MX": RegionalCurrency.MXN,
        "BR": RegionalCurrency.BRL,
        "AR": RegionalCurrency.ARS,
        "CL": RegionalCurrency.CLP,
        "CO": RegionalCurrency.COP,
        "PE": RegionalCurrency.EUR,
        "VE": RegionalCurrency.EUR,
        "EC": RegionalCurrency.EUR,
    }

    # ==============================
    # Regional Tax/VAT Rates
    # ==============================

    REGIONAL_TAXES = {
        # North America
        GlobalRegion.NORTH_AMERICA: {
            "CA": {  # Canadian provinces handled by CanadianPricingService
                "default": 0.13,  # ON HST
            },
            "US": {  # US state sales tax (simplified - uses destination state)
                "default": 0.08,  # Average US sales tax
                "CA": 0.0725,  # California
                "TX": 0.0625,  # Texas
                "NY": 0.0800,  # New York
                "FL": 0.0600,  # Florida
                "WA": 0.0650,  # Washington
            }
        },
        # Europe - VAT (Value Added Tax)
        GlobalRegion.EUROPE: {
            "GB": 0.20,  # UK VAT
            "DE": 0.19,  # Germany VAT
            "FR": 0.20,  # France VAT
            "IT": 0.22,  # Italy VAT
            "ES": 0.21,  # Spain VAT
            "NL": 0.21,  # Netherlands VAT
            "BE": 0.21,  # Belgium VAT
            "AT": 0.20,  # Austria VAT
            "CH": 0.077,  # Switzerland VAT
            "SE": 0.25,  # Sweden VAT
            "NO": 0.25,  # Norway VAT
            "DK": 0.25,  # Denmark VAT
            "FI": 0.24,  # Finland VAT
            "PL": 0.23,  # Poland VAT
            "CZ": 0.21,  # Czech Republic VAT
            "IE": 0.23,  # Ireland VAT
        },
        # Asia-Pacific
        GlobalRegion.ASIA_PACIFIC: {
            "AU": 0.10,  # Australia GST
            "SG": 0.08,  # Singapore GST
            "JP": 0.10,  # Japan Consumption Tax
            "HK": 0.00,  # Hong Kong (no goods tax, but service tax 5-6%)
            "NZ": 0.15,  # New Zealand GST
            "IN": 0.05,  # India GST (simplified)
            "TH": 0.07,  # Thailand VAT
            "MY": 0.06,  # Malaysia SST
            "ID": 0.10,  # Indonesia PPN
            "PH": 0.12,  # Philippines VAT
        },
        # Middle East & Africa
        GlobalRegion.MIDDLE_EAST_AFRICA: {
            "AE": 0.05,  # UAE VAT
            "SA": 0.15,  # Saudi Arabia VAT
            "KW": 0.00,  # Kuwait (no VAT)
            "QA": 0.00,  # Qatar (no VAT)
            "BH": 0.00,  # Bahrain (no VAT)
            "ZA": 0.15,  # South Africa VAT
            "EG": 0.14,  # Egypt GST
            "MA": 0.20,  # Morocco VAT
            "NG": 0.075,  # Nigeria VAT
            "KE": 0.16,  # Kenya VAT
        },
        # Latin America
        GlobalRegion.LATIN_AMERICA: {
            "MX": 0.16,  # Mexico VAT
            "BR": 0.18,  # Brazil ICMS (simplified)
            "AR": 0.21,  # Argentina VAT
            "CL": 0.19,  # Chile VAT
            "CO": 0.19,  # Colombia VAT
            "PE": 0.18,  # Peru VAT
            "VE": 0.16,  # Venezuela VAT
            "EC": 0.12,  # Ecuador VAT
        }
    }

    # ==============================
    # Regional Pricing Multipliers
    # ==============================
    # Adjusts base North American pricing for regional costs

    REGIONAL_RATE_MULTIPLIERS = {
        GlobalRegion.NORTH_AMERICA: 1.0,   # Base rate (CA/US)
        GlobalRegion.EUROPE: 1.3,          # +30% for EU network costs
        GlobalRegion.ASIA_PACIFIC: 1.5,    # +50% for long-haul air
        GlobalRegion.MIDDLE_EAST_AFRICA: 1.4,  # +40% for Middle East/Africa routes
        GlobalRegion.LATIN_AMERICA: 1.25,  # +25% for Latin America
    }

    # ==============================
    # Regional Customs Fees
    # ==============================

    REGIONAL_CUSTOMS_FEES = {
        GlobalRegion.NORTH_AMERICA: 50.00,    # CAD/USD cross-border
        GlobalRegion.EUROPE: 40.00,           # EUR equivalent
        GlobalRegion.ASIA_PACIFIC: 80.00,     # AUD equivalent
        GlobalRegion.MIDDLE_EAST_AFRICA: 60.00,  # AED equivalent
        GlobalRegion.LATIN_AMERICA: 70.00,    # MXN/BRL equivalent
    }

    # ==============================
    # Currency Exchange Rates (to USD base)
    # ==============================
    # Live rates should be fetched from API; these are examples

    CURRENCY_RATES = {
        # To USD
        RegionalCurrency.CAD: 0.74,
        RegionalCurrency.USD: 1.00,
        RegionalCurrency.GBP: 1.27,
        RegionalCurrency.EUR: 1.10,
        RegionalCurrency.AUD: 0.66,
        RegionalCurrency.SGD: 0.74,
        RegionalCurrency.JPY: 0.0067,
        RegionalCurrency.HKD: 0.128,
        RegionalCurrency.NZD: 0.60,
        RegionalCurrency.AED: 0.272,
        RegionalCurrency.SAR: 0.266,
        RegionalCurrency.ZAR: 0.054,
        RegionalCurrency.EGP: 0.021,
        RegionalCurrency.MXN: 0.058,
        RegionalCurrency.BRL: 0.20,
        RegionalCurrency.ARS: 0.0099,
        RegionalCurrency.CLP: 0.0012,
        RegionalCurrency.COP: 0.00025,
    }

    # ==============================
    # Delivery Hubs by Region
    # ==============================

    REGIONAL_HUBS = {
        GlobalRegion.NORTH_AMERICA: ["YYZ", "YVR", "YUL", "YYC", "YEG", "ORD"],  # Toronto, Vancouver, Montreal, Calgary, Edmonton, Chicago
        GlobalRegion.EUROPE: ["LHR", "CDG", "FRA", "AMS", "DUB"],  # London, Paris, Frankfurt, Amsterdam, Dublin
        GlobalRegion.ASIA_PACIFIC: ["SYD", "SIN", "NRT", "HKG", "AKL"],  # Sydney, Singapore, Tokyo, Hong Kong, Auckland
        GlobalRegion.MIDDLE_EAST_AFRICA: ["DXB", "JNB", "CAI", "DOH"],  # Dubai, Johannesburg, Cairo, Doha
        GlobalRegion.LATIN_AMERICA: ["MEX", "GIG", "EZE", "SCL"],  # Mexico City, Rio, Buenos Aires, Santiago
    }

    @classmethod
    def detect_region(cls, country_code: str) -> GlobalRegion:
        """Detect region from country code"""
        for region, countries in cls.REGION_COUNTRIES.items():
            if country_code in countries:
                return region
        return GlobalRegion.NORTH_AMERICA  # Default

    @classmethod
    def get_currency(cls, country_code: str) -> str:
        """Get currency for country"""
        return cls.COUNTRY_CURRENCY.get(country_code, "USD")

    @classmethod
    def calculate_global_quote(
        cls,
        origin_country: str,
        destination_country: str,
        weight_kg: float,
        distance_km: float = 500,
        service_type: str = "standard",
        item_type: str = "documents",
    ) -> Dict:
        """
        Calculate quote for global shipment with multi-region support
        
        Args:
            origin_country: ISO country code (CA, US, GB, AU, etc.)
            destination_country: ISO country code
            weight_kg: Package weight in kg
            distance_km: Estimated distance in km
            service_type: standard, express, overnight, economy
            item_type: documents, electronics, fragile, perishable, hazmat
            
        Returns:
            dict: Complete quote breakdown in destination country currency
        """
        
        # Detect regions
        origin_region = cls.detect_region(origin_country)
        dest_region = cls.detect_region(destination_country)
        
        # Get currencies
        origin_currency = cls.get_currency(origin_country)
        dest_currency = cls.get_currency(destination_country)
        
        # If domestic (same country) - use Canadian service for CA, fallback for others
        if origin_country == destination_country:
            if origin_country == "CA":
                # Use Canadian postal code pricing (requires postal code)
                # For this global service, estimate zone based on distance
                if distance_km < 15:
                    zone = ShippingZone.ZONE_1_INTRACITY
                elif distance_km < 100:
                    zone = ShippingZone.ZONE_2_REGIONAL
                else:
                    zone = ShippingZone.ZONE_3_CONTINENTAL
            else:
                # Domestic pricing for other countries (simplified)
                if distance_km < 50:
                    zone = ShippingZone.ZONE_1_INTRACITY
                elif distance_km < 500:
                    zone = ShippingZone.ZONE_2_REGIONAL
                else:
                    zone = ShippingZone.ZONE_3_CONTINENTAL
        else:
            # International shipment
            if service_type in ["express", "overnight"]:
                zone = ShippingZone.ZONE_4_AIR
            else:
                zone = ShippingZone.ZONE_3_CONTINENTAL

        # ==============================
        # Calculate Base Pricing
        # ==============================

        base_rates = {
            ShippingZone.ZONE_1_INTRACITY: 8.00,
            ShippingZone.ZONE_2_REGIONAL: 45.00,
            ShippingZone.ZONE_3_CONTINENTAL: 85.00,
            ShippingZone.ZONE_4_AIR: 120.00,
            ShippingZone.ZONE_5_OCEAN: 250.00,
        }

        distance_rates = {
            ShippingZone.ZONE_1_INTRACITY: 0.75,
            ShippingZone.ZONE_2_REGIONAL: 0.45,
            ShippingZone.ZONE_3_CONTINENTAL: 0.25,
            ShippingZone.ZONE_4_AIR: 0.15,
            ShippingZone.ZONE_5_OCEAN: 0.05,
        }

        weight_rates = {
            ShippingZone.ZONE_1_INTRACITY: 3.00,
            ShippingZone.ZONE_2_REGIONAL: 2.50,
            ShippingZone.ZONE_3_CONTINENTAL: 2.00,
            ShippingZone.ZONE_4_AIR: 5.00,
            ShippingZone.ZONE_5_OCEAN: 0.75,
        }

        service_multipliers = {
            "economy": 0.80,
            "standard": 1.00,
            "express": 1.50,
            "overnight": 2.00,
        }

        # Apply regional multiplier
        regional_multiplier = cls.REGIONAL_RATE_MULTIPLIERS[dest_region]

        base_fare = base_rates[zone] * regional_multiplier
        distance_charge = distance_km * distance_rates[zone] * regional_multiplier
        weight_charge = weight_kg * weight_rates[zone] * regional_multiplier

        # Apply service multiplier
        speed_multiplier = service_multipliers.get(service_type, 1.0)
        subtotal = (base_fare + distance_charge + weight_charge) * speed_multiplier

        # ==============================
        # Add Fees
        # ==============================

        # Customs fee (if international)
        customs_fee = 0
        if origin_country != destination_country:
            customs_fee = cls.REGIONAL_CUSTOMS_FEES[dest_region]
            subtotal += customs_fee

        # Fuel surcharge
        fuel_surcharge = subtotal * 0.12

        # ==============================
        # Calculate Tax
        # ==============================

        subtotal_with_fuel = subtotal + fuel_surcharge

        # Get tax rate
        tax_jurisdiction = cls.REGIONAL_TAXES[dest_region]
        tax_rate = tax_jurisdiction.get(destination_country, 0.10)

        tax_amount = subtotal_with_fuel * tax_rate
        total_usd = subtotal_with_fuel + tax_amount

        # ==============================
        # Convert to Destination Currency
        # ==============================

        exchange_rate = cls.CURRENCY_RATES.get(RegionalCurrency(dest_currency), 1.0)
        total_destination = total_usd * exchange_rate

        # ==============================
        # Estimate Delivery Time
        # ==============================

        if origin_country == destination_country:
            if distance_km < 50:
                min_days, max_days = (0, 1)
            elif distance_km < 500:
                min_days, max_days = (2, 3)
            else:
                min_days, max_days = (3, 5)
        else:
            # International
            if service_type == "express":
                min_days, max_days = (2, 3)
            elif service_type == "overnight":
                min_days, max_days = (1, 2)
            else:
                min_days, max_days = (5, 10)

        # Apply service type adjustments
        if service_type == "economy":
            min_days, max_days = (max_days + 2, max_days + 4)

        return {
            "currency": dest_currency,
            "origin_country": origin_country,
            "destination_country": destination_country,
            "origin_region": origin_region.value,
            "destination_region": dest_region.value,
            "zone": zone.value,
            "service_type": service_type,
            "distance_km": round(distance_km, 2),
            "weight_kg": weight_kg,
            "delivery_time": f"{min_days}-{max_days} business days",
            "base_fare": round(base_fare, 2),
            "distance_charge": round(distance_charge, 2),
            "weight_charge": round(weight_charge, 2),
            "customs_fee": round(customs_fee, 2),
            "fuel_surcharge": round(fuel_surcharge, 2),
            "subtotal": round(subtotal_with_fuel, 2),
            "tax_rate": round(tax_rate * 100, 2),
            "tax_amount": round(tax_amount, 2),
            "total_price": round(total_destination, 2),
            "total_usd": round(total_usd, 2),
            "exchange_rate": round(exchange_rate, 4),
            "breakdown": {
                "base": round(base_fare, 2),
                "distance": round(distance_charge, 2),
                "weight": round(weight_charge, 2),
                "customs": round(customs_fee, 2),
                "fuel": round(fuel_surcharge, 2),
                "tax": round(tax_amount, 2),
                "total": round(total_destination, 2),
            },
            "hubs": cls.REGIONAL_HUBS[dest_region]
        }

    @classmethod
    def list_supported_countries(cls) -> Dict:
        """List all supported countries organized by region"""
        return {
            region.value: cls.REGION_COUNTRIES[region]
            for region in GlobalRegion
        }

    @classmethod
    def list_supported_currencies(cls) -> Dict:
        """List all supported currencies by region"""
        currencies_by_region = {}
        for region in GlobalRegion:
            currencies_by_region[region.value] = list(set(
                cls.COUNTRY_CURRENCY.get(country, "USD")
                for country in cls.REGION_COUNTRIES[region]
            ))
        return currencies_by_region
