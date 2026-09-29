import re
import hashlib
import json
from sqlalchemy.orm import Session
from app.models import RawQuote, RefinedQuote, LeadTimeBucket, AvailabilityStatus
from datetime import datetime

CITY_TO_IATA = {
    "delhi": "DEL", "new delhi": "DEL", "del": "DEL",
    "mumbai": "BOM", "bombay": "BOM", "bom": "BOM",
    "bangalore": "BLR", "bengaluru": "BLR", "blr": "BLR",
    "chennai": "MAA", "madras": "MAA", "maa": "MAA",
    "kolkata": "CCU", "calcutta": "CCU", "ccu": "CCU",
    "hyderabad": "HYD", "hyd": "HYD"
}

def standardize_airport(name: str) -> str:
    if not name:
        return ""
    clean_name = name.strip().lower()
    return CITY_TO_IATA.get(clean_name, clean_name.upper()[:3])

def extract_price(price_str) -> float:
    if price_str is None:
        return 0.0
    if isinstance(price_str, (int, float)):
        return float(price_str)
    
    # Remove non-numeric characters except dot
    clean_str = re.sub(r'[^\d.]', '', str(price_str))
    if not clean_str:
        return 0.0
    try:
        return float(clean_str)
    except ValueError:
        return 0.0

def calculate_lead_time_bucket(days: int) -> LeadTimeBucket:
    if days <= 1:
        return LeadTimeBucket.T_1
    elif 2 <= days <= 7:
        return LeadTimeBucket.T_7
    elif 8 <= days <= 15:
        return LeadTimeBucket.T_15
    elif 16 <= days <= 30:
        return LeadTimeBucket.T_30
    else:
        return LeadTimeBucket.T_45

def generate_fare_hash(source_id, flight_number, origin, destination, travel_date, collection_timestamp, total_fare) -> str:
    hash_input = f"{source_id}-{flight_number}-{origin}-{destination}-{travel_date}-{collection_timestamp}-{total_fare}"
    return hashlib.md5(hash_input.encode()).hexdigest()

def refine_quote(db: Session, raw_quote: RawQuote) -> RefinedQuote:
    raw_payload = json.loads(raw_quote.raw_payload)
    
    origin = standardize_airport(raw_quote.origin)
    destination = standardize_airport(raw_quote.destination)
    
    collection_date = raw_quote.collection_timestamp.date()
    travel_date = raw_quote.travel_date
    lead_time_days = (travel_date - collection_date).days if travel_date and collection_date else 0
    lead_time_bucket = calculate_lead_time_bucket(lead_time_days)
    
    base_fare_str = raw_payload.get("base_fare", "0")
    taxes_str = raw_payload.get("taxes")
    fees_str = raw_payload.get("fees", "0")
    total_fare_str = raw_payload.get("total_fare", "0")
    
    base_fare = extract_price(base_fare_str)
    taxes = extract_price(taxes_str) if taxes_str is not None else None
    fees = extract_price(fees_str)
    total_fare = extract_price(total_fare_str)
    
    if total_fare == 0.0:
        availability = AvailabilityStatus.SOLD_OUT
    else:
        availability = AvailabilityStatus.AVAILABLE
        
    fare_hash = generate_fare_hash(
        raw_quote.source_id,
        raw_quote.flight_number,
        origin,
        destination,
        travel_date,
        raw_quote.collection_timestamp,
        total_fare
    )
    
    # Check deduplication
    existing = db.query(RefinedQuote).filter(RefinedQuote.fare_hash == fare_hash).first()
    if existing:
        return existing
        
    refined_quote = RefinedQuote(
        raw_quote_id=raw_quote.id,
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        collection_date=collection_date,
        lead_time_bucket=lead_time_bucket,
        lead_time_days=lead_time_days,
        airline=raw_quote.airline,
        flight_number=raw_quote.flight_number,
        base_fare=base_fare,
        taxes=taxes,
        fees=fees,
        total_fare=total_fare,
        fare_hash=fare_hash,
        availability=availability
    )
    
    db.add(refined_quote)
    db.commit()
    db.refresh(refined_quote)
    return refined_quote
