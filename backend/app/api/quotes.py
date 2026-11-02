"""
Quote & Pricing Calculator API
Calculates shipping rates based on Canadian zone pricing and global multi-region pricing
"""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

from app.services.pricing_canada import CanadianPricingService, ShippingZone, CanadianTaxJurisdiction
from app.services.pricing_global import GlobalPricingService, GlobalRegion

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])


class ServiceTypeEnum(str, Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"


class ItemTypeEnum(str, Enum):
    DOCUMENTS = "documents"
    ELECTRONICS = "electronics"
    FRAGILE = "fragile"
    PERISHABLE = "perishable"
    HAZMAT = "hazmat"
    GENERAL = "general"


class QuoteCalculateRequest(BaseModel):
    """Request to calculate shipping quote - Global multi-region support"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_country": "CA",
                "origin_postal": "M5V 3A8",
                "destination_country": "GB",
                "destination_postal": "SW1A 1AA",
                "weight_kg": 25.5,
                "distance_km": 5580,
                "service_type": "express",
                "item_type": "electronics"
            }
        }
    )

    origin_country: str = Field(default="CA", min_length=2, max_length=2)
    origin_postal: Optional[str] = Field(default="M5V 3A8", max_length=15)
    destination_country: str = Field(default="CA", min_length=2, max_length=2)
    destination_postal: Optional[str] = Field(default="V6B 2W9", max_length=15)
    weight_kg: float = Field(..., gt=0, le=30000)
    distance_km: Optional[float] = Field(default=500, ge=0, le=50000)
    service_type: ServiceTypeEnum = Field(default=ServiceTypeEnum.STANDARD)
    item_type: ItemTypeEnum = Field(default=ItemTypeEnum.GENERAL)
    insurance_value_cad: Optional[float] = Field(default=0, ge=0)


class QuoteCalculateResponse(BaseModel):
    """Global shipping quote response with regional currency and breakdown"""
    quote_id: str
    timestamp: datetime
    valid_until: datetime

    origin_country: str
    origin_region: str
    origin_postal: Optional[str] = None
    destination_country: str
    destination_region: str
    destination_postal: Optional[str] = None
    distance_km: float

    weight_kg: float
    service_type: str
    item_type: str
    zone: str
    delivery_time: str

    currency: str
    base_fare: float
    distance_charge: float
    weight_charge: float
    customs_fee: float
    fuel_surcharge: float
    insurance_charge: float = 0.0
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_price: float
    total_usd: float
    exchange_rate: float

    breakdown: Dict
    hubs: list


@router.post("/calculate", response_model=QuoteCalculateResponse)
async def calculate_quote(request: QuoteCalculateRequest):
    """Calculate shipping quote for global shipment across 5 regions"""
    try:
        origin_country = request.origin_country.upper()
        dest_country = request.destination_country.upper()

        quote_data = GlobalPricingService.calculate_global_quote(
            origin_country=origin_country,
            destination_country=dest_country,
            weight_kg=request.weight_kg,
            distance_km=request.distance_km or 500.0,
            service_type=request.service_type.value,
            item_type=request.item_type.value
        )

        insurance_charge = 0.0
        if request.insurance_value_cad and request.insurance_value_cad > 0:
            insurance_charge = round(request.insurance_value_cad * 0.05, 2)
            quote_data["subtotal"] = round(quote_data["subtotal"] + insurance_charge, 2)
            tax_addition = insurance_charge * (quote_data["tax_rate"] / 100.0)
            quote_data["tax_amount"] = round(quote_data["tax_amount"] + tax_addition, 2)
            quote_data["total_price"] = round(quote_data["subtotal"] + quote_data["tax_amount"], 2)

        import uuid
        quote_id = f"QTE-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        return QuoteCalculateResponse(
            quote_id=quote_id,
            timestamp=datetime.utcnow(),
            valid_until=datetime.fromtimestamp(datetime.utcnow().timestamp() + 86400),
            origin_country=origin_country,
            origin_region=quote_data["origin_region"],
            origin_postal=request.origin_postal,
            destination_country=dest_country,
            destination_region=quote_data["destination_region"],
            destination_postal=request.destination_postal,
            distance_km=quote_data["distance_km"],
            weight_kg=request.weight_kg,
            service_type=request.service_type.value,
            item_type=request.item_type.value,
            zone=quote_data["zone"],
            delivery_time=quote_data["delivery_time"],
            currency=quote_data["currency"],
            base_fare=quote_data["base_fare"],
            distance_charge=quote_data["distance_charge"],
            weight_charge=quote_data["weight_charge"],
            customs_fee=quote_data["customs_fee"],
            fuel_surcharge=quote_data["fuel_surcharge"],
            insurance_charge=insurance_charge,
            subtotal=quote_data["subtotal"],
            tax_rate=quote_data["tax_rate"],
            tax_amount=quote_data["tax_amount"],
            total_price=quote_data["total_price"],
            total_usd=quote_data["total_usd"],
            exchange_rate=quote_data["exchange_rate"],
            breakdown=quote_data["breakdown"],
            hubs=quote_data["hubs"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating quote: {str(e)}"
        )


@router.get("/zones")
async def get_shipping_zones():
    """Get information about all shipping zones and base pricing"""
    zones_info = {}
    for zone in ShippingZone:
        min_days, max_days = CanadianPricingService.estimate_delivery_time(zone, "standard")
        zones_info[zone.value] = {
            "name": zone.name,
            "base_rate_cad": CanadianPricingService.BASE_RATES[zone],
            "distance_rate_per_km": CanadianPricingService.DISTANCE_RATES[zone],
            "weight_rate_per_kg": CanadianPricingService.WEIGHT_RATES[zone],
            "estimated_days": f"{min_days}-{max_days}",
        }
    return {
        "currency": "CAD",
        "zones": zones_info,
        "customs_handling_fee": CanadianPricingService.CUSTOMS_HANDLING_FEE,
        "fuel_surcharge_rate": f"{CanadianPricingService.FUEL_SURCHARGE_RATE * 100}%",
        "insurance_rate": "5% of declared value",
    }


@router.get("/taxes")
async def get_tax_rates():
    """Get Canadian provincial tax rates"""
    taxes = {}
    for jurisdiction in CanadianTaxJurisdiction:
        rate = CanadianPricingService.TAX_RATES[jurisdiction]
        taxes[jurisdiction.value] = {
            "rate": f"{rate * 100:.2f}%",
            "decimal": rate,
        }
    return {"country": "CA", "provinces": taxes}


@router.get("/regions")
async def get_supported_regions():
    """Get all supported global regions, countries, currencies, and hubs"""
    regions_info = {}
    for region in GlobalRegion:
        countries = GlobalPricingService.REGION_COUNTRIES[region]
        currencies = list(set(GlobalPricingService.get_currency(c) for c in countries))
        hubs = GlobalPricingService.REGIONAL_HUBS[region]
        regions_info[region.value] = {
            "name": region.name.replace("_", " "),
            "countries": countries,
            "currencies": currencies,
            "hubs": hubs,
            "rate_multiplier": GlobalPricingService.REGIONAL_RATE_MULTIPLIERS[region],
            "customs_fee": GlobalPricingService.REGIONAL_CUSTOMS_FEES[region]
        }
    return {
        "total_regions": len(GlobalRegion),
        "total_countries": sum(len(c) for c in GlobalPricingService.REGION_COUNTRIES.values()),
        "regions": regions_info
    }


@router.get("/currencies")
async def get_supported_currencies():
    """Get all supported currencies with current exchange rates (to USD)"""
    currencies = {}
    for currency, rate in GlobalPricingService.CURRENCY_RATES.items():
        currencies[currency.value] = {
            "code": currency.value,
            "to_usd": rate,
            "from_usd": round(1 / rate, 4) if rate > 0 else 0
        }
    return {
        "base_currency": "USD",
        "supported_currencies": len(currencies),
        "currencies": currencies
    }


@router.get("/estimate-distance")
async def estimate_distance(
    origin_postal: str = Query(...),
    destination_postal: str = Query(...)
):
    """Estimate shipping distance and zone from Canadian postal codes"""
    origin_clean = origin_postal.replace(" ", "").upper()
    dest_clean = destination_postal.replace(" ", "").upper()

    origin_prov = CanadianPricingService.detect_province_from_postal(origin_clean)
    dest_prov = CanadianPricingService.detect_province_from_postal(dest_clean)

    if origin_clean[:3] == dest_clean[:3]:
        estimated_km = 10
        zone = ShippingZone.ZONE_1_INTRACITY
    elif origin_prov == dest_prov:
        estimated_km = 200
        zone = ShippingZone.ZONE_2_REGIONAL
    else:
        estimated_km = 1500
        zone = ShippingZone.ZONE_3_CONTINENTAL

    min_days, max_days = CanadianPricingService.estimate_delivery_time(zone, "standard")
    return {
        "origin_postal": origin_postal,
        "origin_province": origin_prov.value,
        "destination_postal": destination_postal,
        "destination_province": dest_prov.value,
        "estimated_distance_km": estimated_km,
        "zone": zone.value,
        "estimated_delivery_days": f"{min_days}-{max_days}",
    }
