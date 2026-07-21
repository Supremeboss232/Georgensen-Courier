"""
Quotes API for Canada-global logistics pricing
Handles quote calculations with regional tax, customs, and currency support
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
import logging
from app.db.base import get_db
from app.services.pricing_canada import CanadianPricingService
from app.services.pricing_global import GlobalPricingService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/quotes",
    tags=["Quotes"]
)


# Request schema
class QuoteCalculateRequest(BaseModel):
    """Quote calculation request with Canada-global parameters"""
    
    origin_postal: Optional[str] = Field(
        default=None,
        description="Origin postal code (CA: A1A 1A1 format, US: 5-digit, optional for non-CA/US)",
        example="M5H 2N2"
    )
    destination_postal: Optional[str] = Field(
        default=None,
        description="Destination postal code (CA: A1A 1A1 format, US: 5-digit, optional for non-CA/US)",
        example="V6B 4X8"
    )
    weight_kg: float = Field(
        ...,
        description="Package weight in kilograms",
        example=2.5,
        ge=0.1,
        le=100.0
    )
    distance_km: Optional[float] = Field(
        default=500,
        description="Distance in kilometers (optional, will estimate if not provided)",
        ge=1
    )
    service_type: str = Field(
        default="standard",
        description="Service type: standard, express, overnight, economy",
        example="standard"
    )
    origin_country: str = Field(
        ...,
        description="Origin country code (CA, US, GB, AU, MX, BR, DE, JP, etc.)",
        pattern="^[A-Z]{2}$",
        example="CA"
    )
    destination_country: str = Field(
        ...,
        description="Destination country code (CA, US, GB, AU, MX, BR, DE, JP, etc.)",
        pattern="^[A-Z]{2}$",
        example="US"
    )
    item_type: Optional[str] = Field(
        default="documents",
        description="Type of item: documents, small-parcel, medium-box, large-box, pallet",
        example="documents"
    )
    currency: Optional[str] = Field(
        default=None,
        description="Currency for quote (auto-detected from destination country if not specified)",
        pattern="^[A-Z]{3}$",
        example="CAD"
    )


# Response schema
class PriceBreakdown(BaseModel):
    """Detailed price breakdown"""
    base: float = Field(..., description="Base shipping fare")
    distance: float = Field(..., description="Distance-based charge")
    weight: float = Field(..., description="Weight-based charge")
    customs: float = Field(..., description="Customs handling fee (if international)")
    fuel: float = Field(..., description="Fuel surcharge")
    tax: float = Field(..., description="Provincial tax")
    total: float = Field(..., description="Total price")


class QuoteCalculateResponse(BaseModel):
    """Quote calculation response"""
    currency: str = Field(..., description="Quote currency (CAD, USD, EUR, GBP, AUD, etc.)")
    origin_postal: Optional[str]
    destination_postal: Optional[str]
    origin_country: str = Field(..., description="Origin country code")
    destination_country: str = Field(..., description="Destination country code")
    origin_region: Optional[str] = Field(None, description="Origin region (north_america, europe, etc.)")
    destination_region: Optional[str] = Field(None, description="Destination region")
    distance_km: float
    weight_kg: float
    zone: str = Field(..., description="Shipping zone (zone_1 to zone_5)")
    service_type: str
    is_international: bool = Field(
        ..., 
        description="Whether this is an international shipment"
    )
    origin_timezone: str = Field(..., description="Origin timezone")
    destination_timezone: str = Field(..., description="Destination timezone")
    tax_jurisdiction: str
    tax_rate: float = Field(..., description="Tax rate as percentage (e.g., 13.0)")
    base_fare: float = Field(..., description="Base shipping fare")
    distance_charge: float = Field(..., description="Distance-based charge")
    weight_charge: float = Field(..., description="Weight-based charge")
    customs_fee: float = Field(..., description="Customs handling fee (if international)")
    fuel_surcharge: float = Field(..., description="Fuel surcharge")
    subtotal: float = Field(..., description="Subtotal before tax")
    tax_amount: float = Field(..., description="Tax amount")
    total_price: float = Field(..., description="Total price in specified currency")
    total_usd: Optional[float] = Field(None, description="Total price in USD (for reference)")
    exchange_rate: Optional[float] = Field(None, description="Exchange rate used")
    breakdown: PriceBreakdown
    service_display: str = Field(..., description="Display-friendly service name")
    estimated_delivery_days: int = Field(..., description="Estimated delivery days")
    delivery_time: Optional[str] = Field(None, description="Delivery time range")
    hubs: Optional[list] = Field(None, description="Regional hubs serving the destination")
    notes: Optional[str] = Field(None, description="Additional notes (e.g., customs warnings)")
    
    # Origin details
    origin_country: str
    origin_timezone: str
    
    # Destination details
    destination_country: str
    destination_timezone: str
    
    # Tax information
    tax_jurisdiction: str = Field(..., description="Destination province/state code")
    tax_rate: float = Field(..., description="Applicable tax rate percentage")
    
    # Pricing breakdown
    base_fare: float
    distance_charge: float
    weight_charge: float
    customs_fee: float = Field(default=0, description="Customs fee for international")
    fuel_surcharge: float
    subtotal: float = Field(..., description="Subtotal before tax")
    tax_amount: float
    total_price: float = Field(..., description="Total price in specified currency")
    
    # Additional info
    breakdown: PriceBreakdown
    service_display: str = Field(
        ..., 
        description="Human-readable service type"
    )
    estimated_delivery_days: int = Field(
        ...,
        description="Estimated delivery in business days"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes (e.g., customs warnings)"
    )


@router.post("/calculate", response_model=QuoteCalculateResponse)
async def calculate_quote(
    request: QuoteCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate shipping quote with global pricing support
    
    Supports 6 major regions:
    - North America (CA, US)
    - Europe (GB, DE, FR, IT, ES, NL, BE, AT, CH, SE, NO, DK, FI, PL, CZ, IE)
    - Asia-Pacific (AU, SG, JP, HK, NZ, IN, TH, MY, ID, PH)
    - Middle East & Africa (AE, SA, KW, QA, BH, ZA, EG, MA, NG, KE)
    - Latin America (MX, BR, AR, CL, CO, PE, VE, EC)
    
    Example:
    ```json
    {
        "origin_country": "CA",
        "destination_country": "US",
        "weight_kg": 2.5,
        "distance_km": 500,
        "service_type": "standard"
    }
    ```
    """
    
    # Validate service type
    valid_services = ["economy", "standard", "express", "overnight"]
    if request.service_type not in valid_services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service type. Must be one of: {', '.join(valid_services)}"
        )
    
    # Check if we're using postal codes (North America) or global mode
    is_postal_code_mode = (
        (request.origin_country in ["CA", "US"] and request.origin_postal) and
        (request.destination_country in ["CA", "US"] and request.destination_postal)
    )
    
    try:
        if is_postal_code_mode:
            # Use Canadian pricing service for CA/US with postal codes
            # Validate postal codes format
            def is_valid_postal(code: str, country: str) -> bool:
                if country == "CA":
                    import re
                    pattern = r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$'
                    return bool(re.match(pattern, code.upper()))
                elif country == "US":
                    return code.isdigit() and len(code) == 5
                return False
            
            if not is_valid_postal(request.origin_postal, request.origin_country):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid origin postal code format for {request.origin_country}"
                )
            
            if not is_valid_postal(request.destination_postal, request.destination_country):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid destination postal code format for {request.destination_country}"
                )
            
            # Get quote from Canadian pricing service
            quote_data = CanadianPricingService.calculate_quote(
                origin_postal=request.origin_postal,
                destination_postal=request.destination_postal,
                weight_kg=request.weight_kg,
                distance_km=request.distance_km or 100,
                service_type=request.service_type,
                origin_country=request.origin_country,
                destination_country=request.destination_country,
                item_type=request.item_type or "documents"
            )
            
            # Get timezones for postal codes
            def get_timezone_from_postal(postal_code: str, country: str) -> str:
                if country != "CA":
                    return "EST"  # Default to Eastern for US
                
                first_char = postal_code[0].upper()
                timezone_map = {
                    'A': 'NST', 'B': 'AST', 'C': 'AST', 'E': 'AST',
                    'G': 'EST', 'H': 'EST', 'J': 'EST',
                    'K': 'EST', 'L': 'EST', 'M': 'EST', 'N': 'EST', 'P': 'EST',
                    'R': 'CST', 'S': 'CST',
                    'T': 'MST',
                    'V': 'PST',
                    'X': 'CST', 'Y': 'PST',
                }
                return timezone_map.get(first_char, 'EST')
            
            origin_timezone = get_timezone_from_postal(request.origin_postal, request.origin_country)
            destination_timezone = get_timezone_from_postal(request.destination_postal, request.destination_country)
            
            # Determine currency
            currency = request.currency or ("CAD" if request.destination_country == "CA" else "USD")
            
            # Apply currency conversion if needed
            total_price = quote_data["total_price"]
            if currency == "USD" and request.destination_country == "CA":
                total_price = round(total_price / 1.35, 2)
            elif currency == "CAD" and request.destination_country == "US":
                total_price = round(total_price * 1.35, 2)
            
        else:
            # Use Global pricing service for multi-region support
            supported_countries = GlobalPricingService.list_supported_countries()
            all_countries = []
            for countries in supported_countries.values():
                all_countries.extend(countries)
            
            if request.origin_country not in all_countries:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Origin country {request.origin_country} not supported. Supported countries: {', '.join(sorted(set(all_countries)))}"
                )
            
            if request.destination_country not in all_countries:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Destination country {request.destination_country} not supported. Supported countries: {', '.join(sorted(set(all_countries)))}"
                )
            
            # Get global quote
            quote_data = GlobalPricingService.calculate_global_quote(
                origin_country=request.origin_country,
                destination_country=request.destination_country,
                weight_kg=request.weight_kg,
                distance_km=request.distance_km or 500,
                service_type=request.service_type,
                item_type=request.item_type or "documents"
            )
            
            # Use currency from global service or override
            currency = request.currency or quote_data["currency"]
            origin_timezone = "EST"  # Placeholder - would use geolocation API
            destination_timezone = "EST"  # Placeholder - would use geolocation API
            total_price = quote_data["total_price"]
        
        # Map service type to display name
        service_display_map = {
            "economy": "Economy (5-7 days)",
            "standard": "Standard (2-3 days)",
            "express": "Express (24 hours)",
            "overnight": "Overnight"
        }
        service_display = service_display_map.get(request.service_type, "Standard")
        
        # Estimate delivery days
        est_days_map = {
            "economy": 6,
            "standard": 2,
            "express": 1,
            "overnight": 1
        }
        est_days = est_days_map.get(request.service_type, 2)
        
        # Add customs notes if international
        is_international = request.origin_country != request.destination_country
        notes = None
        if is_international:
            customs_fee_text = f"${quote_data.get('customs_fee', 50):.2f}"
            if quote_data.get("currency") != "CAD":
                customs_fee_text += f" ({quote_data.get('currency', 'USD')})"
            notes = (
                f"International shipment - customs clearance required. "
                f"Estimated clearance: 24-48 hours. Customs fee: {customs_fee_text} included in quote."
            )
        
        # Build response
        response = QuoteCalculateResponse(
            currency=currency,
            origin_postal=request.origin_postal,
            destination_postal=request.destination_postal,
            origin_country=request.origin_country,
            destination_country=request.destination_country,
            origin_region=quote_data.get("origin_region"),
            destination_region=quote_data.get("destination_region"),
            distance_km=request.distance_km or 500,
            weight_kg=request.weight_kg,
            zone=quote_data["zone"],
            service_type=request.service_type,
            is_international=is_international,
            origin_timezone=origin_timezone,
            destination_timezone=destination_timezone,
            tax_jurisdiction=quote_data.get("tax_jurisdiction", "Global"),
            tax_rate=quote_data.get("tax_rate", quote_data.get("tax_amount", 0) / quote_data.get("subtotal", 1) * 100),
            base_fare=quote_data["base_fare"],
            distance_charge=quote_data["distance_charge"],
            weight_charge=quote_data["weight_charge"],
            customs_fee=quote_data["customs_fee"],
            fuel_surcharge=quote_data["fuel_surcharge"],
            subtotal=quote_data["subtotal"],
            tax_amount=quote_data["tax_amount"],
            total_price=total_price,
            total_usd=quote_data.get("total_usd"),
            exchange_rate=quote_data.get("exchange_rate"),
            breakdown=PriceBreakdown(**quote_data["breakdown"]),
            service_display=service_display,
            estimated_delivery_days=est_days,
            delivery_time=quote_data.get("delivery_time"),
            hubs=quote_data.get("hubs"),
            notes=notes
        )
        
        # Log quote calculation
        logger.info(
            f"Quote calculated: {request.origin_country} → {request.destination_country}, "
            f"Weight: {request.weight_kg}kg, Total: {total_price} {currency}"
        )
        
        return response
        
    except HTTPException:
        raise
    except KeyError as e:
        logger.error(f"Quote calculation error - missing field: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quote calculation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Quote calculation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate quote: {str(e)}"
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid quote parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating quote: {str(e)}"
        )
