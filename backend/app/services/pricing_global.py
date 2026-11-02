"""
Global Pricing Service for Georgensen Courier

Supports 5 major regions with localized pricing, taxes, and currency handling.
Integrates with regional carrier networks (FedEx, UPS, DHL, local couriers).
"""

from typing import Dict
from enum import Enum
from app.services.pricing_canada import ShippingZone


class GlobalRegion(str, Enum):
    """Global regions supported by Georgensen"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST_AFRICA = "middle_east_africa"
    LATIN_AMERICA = "latin_america"


class RegionalCurrency(str, Enum):
    """Currencies by region"""
    CAD = "CAD"
    USD = "USD"
    GBP = "GBP"
    EUR = "EUR"
    AUD = "AUD"
    SGD = "SGD"
    JPY = "JPY"
    HKD = "HKD"
    NZD = "NZD"
    AED = "AED"
    SAR = "SAR"
    ZAR = "ZAR"
    EGP = "EGP"
    MXN = "MXN"
    BRL = "BRL"
    ARS = "ARS"
    CLP = "CLP"
    COP = "COP"


class GlobalPricingService:
    """Enterprise global pricing service supporting 5 major regions"""

    REGION_COUNTRIES = {
        GlobalRegion.NORTH_AMERICA: ["CA", "US"],
        GlobalRegion.EUROPE: ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "IE"],
        GlobalRegion.ASIA_PACIFIC: ["AU", "SG", "JP", "HK", "NZ", "IN", "TH", "MY", "ID", "PH"],
        GlobalRegion.MIDDLE_EAST_AFRICA: ["AE", "SA", "KW", "QA", "BH", "ZA", "EG", "MA", "NG", "KE"],
        GlobalRegion.LATIN_AMERICA: ["MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC"],
    }

    COUNTRY_CURRENCY = {
        "CA": RegionalCurrency.CAD,
        "US": RegionalCurrency.USD,
        "GB": RegionalCurrency.GBP,
        "DE": RegionalCurrency.EUR, "FR": RegionalCurrency.EUR, "IT": RegionalCurrency.EUR,
        "ES": RegionalCurrency.EUR, "NL": RegionalCurrency.EUR, "BE": RegionalCurrency.EUR,
        "AT": RegionalCurrency.EUR, "CH": RegionalCurrency.EUR, "SE": RegionalCurrency.EUR,
        "NO": RegionalCurrency.EUR, "DK": RegionalCurrency.EUR, "FI": RegionalCurrency.EUR,
        "PL": RegionalCurrency.EUR, "CZ": RegionalCurrency.EUR, "IE": RegionalCurrency.EUR,
        "AU": RegionalCurrency.AUD,
        "SG": RegionalCurrency.SGD,
        "JP": RegionalCurrency.JPY,
        "HK": RegionalCurrency.HKD,
        "NZ": RegionalCurrency.NZD,
        "IN": RegionalCurrency.EUR,
        "TH": RegionalCurrency.EUR,
        "MY": RegionalCurrency.EUR,
        "ID": RegionalCurrency.EUR,
        "PH": RegionalCurrency.EUR,
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
        "MX": RegionalCurrency.MXN,
        "BR": RegionalCurrency.BRL,
        "AR": RegionalCurrency.ARS,
        "CL": RegionalCurrency.CLP,
        "CO": RegionalCurrency.COP,
        "PE": RegionalCurrency.EUR,
        "VE": RegionalCurrency.EUR,
        "EC": RegionalCurrency.EUR,
    }

    REGIONAL_TAXES = {
        GlobalRegion.NORTH_AMERICA: {
            "CA": {
                "default": 0.13,
            },
            "US": {
                "default": 0.08,
                "CA": 0.0725,
                "TX": 0.0625,
                "NY": 0.0800,
                "FL": 0.0600,
                "WA": 0.0650,
            }
        },
        GlobalRegion.EUROPE: {
            "GB": 0.20, "DE": 0.19, "FR": 0.20, "IT": 0.22,
            "ES": 0.21, "NL": 0.21, "BE": 0.21, "AT": 0.20,
            "CH": 0.077, "SE": 0.25, "NO": 0.25, "DK": 0.25,
            "FI": 0.24, "PL": 0.23, "CZ": 0.21, "IE": 0.23,
        },
        GlobalRegion.ASIA_PACIFIC: {
            "AU": 0.10, "SG": 0.08, "JP": 0.10, "HK": 0.00,
            "NZ": 0.15, "IN": 0.05, "TH": 0.07, "MY": 0.06,
            "ID": 0.10, "PH": 0.12,
        },
        GlobalRegion.MIDDLE_EAST_AFRICA: {
            "AE": 0.05, "SA": 0.15, "KW": 0.00, "QA": 0.00,
            "BH": 0.00, "ZA": 0.15, "EG": 0.14, "MA": 0.20,
            "NG": 0.075, "KE": 0.16,
        },
        GlobalRegion.LATIN_AMERICA: {
            "MX": 0.16, "BR": 0.18, "AR": 0.21, "CL": 0.19,
            "CO": 0.19, "PE": 0.18, "VE": 0.16, "EC": 0.12,
        }
    }

    REGIONAL_RATE_MULTIPLIERS = {
        GlobalRegion.NORTH_AMERICA: 1.0,
        GlobalRegion.EUROPE: 1.3,
        GlobalRegion.ASIA_PACIFIC: 1.5,
        GlobalRegion.MIDDLE_EAST_AFRICA: 1.4,
        GlobalRegion.LATIN_AMERICA: 1.25,
    }

    REGIONAL_CUSTOMS_FEES = {
        GlobalRegion.NORTH_AMERICA: 50.00,
        GlobalRegion.EUROPE: 40.00,
        GlobalRegion.ASIA_PACIFIC: 80.00,
        GlobalRegion.MIDDLE_EAST_AFRICA: 60.00,
        GlobalRegion.LATIN_AMERICA: 70.00,
    }

    CURRENCY_RATES = {
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

    REGIONAL_HUBS = {
        GlobalRegion.NORTH_AMERICA: ["YYZ", "YVR", "YUL", "YYC", "YEG", "ORD"],
        GlobalRegion.EUROPE: ["LHR", "CDG", "FRA", "AMS", "DUB"],
        GlobalRegion.ASIA_PACIFIC: ["SYD", "SIN", "NRT", "HKG", "AKL"],
        GlobalRegion.MIDDLE_EAST_AFRICA: ["DXB", "JNB", "CAI", "DOH"],
        GlobalRegion.LATIN_AMERICA: ["MEX", "GIG", "EZE", "SCL"],
    }

    @classmethod
    def detect_region(cls, country_code: str) -> GlobalRegion:
        """Detect region from country code"""
        for region, countries in cls.REGION_COUNTRIES.items():
            if country_code in countries:
                return region
        return GlobalRegion.NORTH_AMERICA

    @classmethod
    def get_currency(cls, country_code: str) -> str:
        """Get currency for country"""
        curr = cls.COUNTRY_CURRENCY.get(country_code, RegionalCurrency.USD)
        return curr.value if hasattr(curr, "value") else str(curr)

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
        """Calculate quote for global shipment with multi-region support"""
        origin_region = cls.detect_region(origin_country)
        dest_region = cls.detect_region(destination_country)
        dest_currency = cls.get_currency(destination_country)
        
        if origin_country == destination_country:
            if origin_country == "CA":
                if distance_km < 15:
                    zone = ShippingZone.ZONE_1_INTRACITY
                elif distance_km < 100:
                    zone = ShippingZone.ZONE_2_REGIONAL
                else:
                    zone = ShippingZone.ZONE_3_CONTINENTAL
            else:
                if distance_km < 50:
                    zone = ShippingZone.ZONE_1_INTRACITY
                elif distance_km < 500:
                    zone = ShippingZone.ZONE_2_REGIONAL
                else:
                    zone = ShippingZone.ZONE_3_CONTINENTAL
        else:
            if service_type in ["express", "overnight"]:
                zone = ShippingZone.ZONE_4_AIR
            else:
                zone = ShippingZone.ZONE_3_CONTINENTAL

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

        regional_multiplier = cls.REGIONAL_RATE_MULTIPLIERS[dest_region]

        base_fare = base_rates[zone] * regional_multiplier
        distance_charge = distance_km * distance_rates[zone] * regional_multiplier
        weight_charge = weight_kg * weight_rates[zone] * regional_multiplier

        speed_multiplier = service_multipliers.get(service_type, 1.0)
        subtotal = (base_fare + distance_charge + weight_charge) * speed_multiplier

        customs_fee = 0.0
        if origin_country != destination_country:
            customs_fee = cls.REGIONAL_CUSTOMS_FEES[dest_region]
            subtotal += customs_fee

        fuel_surcharge = subtotal * 0.12
        subtotal_with_fuel = subtotal + fuel_surcharge

        # Safely resolve nested or flat tax rate
        tax_jurisdiction = cls.REGIONAL_TAXES.get(dest_region, {})
        raw_tax_rate = tax_jurisdiction.get(destination_country, 0.10)
        if isinstance(raw_tax_rate, dict):
            tax_rate = float(raw_tax_rate.get("default", 0.10))
        else:
            tax_rate = float(raw_tax_rate)

        tax_amount = subtotal_with_fuel * tax_rate
        total_usd = subtotal_with_fuel + tax_amount

        try:
            currency_enum = RegionalCurrency(dest_currency)
            exchange_rate = cls.CURRENCY_RATES.get(currency_enum, 1.0)
        except ValueError:
            exchange_rate = 1.0

        total_destination = total_usd / exchange_rate if exchange_rate else total_usd

        if origin_country == destination_country:
            if distance_km < 50:
                min_days, max_days = (0, 1)
            elif distance_km < 500:
                min_days, max_days = (2, 3)
            else:
                min_days, max_days = (3, 5)
        else:
            if service_type == "express":
                min_days, max_days = (2, 3)
            elif service_type == "overnight":
                min_days, max_days = (1, 2)
            else:
                min_days, max_days = (5, 10)

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
                cls.get_currency(country)
                for country in cls.REGION_COUNTRIES[region]
            ))
        return currencies_by_region
