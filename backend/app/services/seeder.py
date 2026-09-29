import random
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.models import Source, Airport, Route, RawQuote
from app.services.ingestion import ingest_raw_quote
from app.services.refinement import refine_quote
from app.services.validation import validate_quote
from app.services.quality import process_quality_and_anomaly
from app.services.index_engine import calculate_daily_apix

SOURCES = [
    {"name": "MakeMyTrip", "base_url": "https://makemytrip.com", "reliability": 0.95},
    {"name": "Ixigo", "base_url": "https://ixigo.com", "reliability": 0.92},
    {"name": "IndiGo", "base_url": "https://goindigo.in", "reliability": 0.99},
    {"name": "AirIndia", "base_url": "https://airindia.in", "reliability": 0.98},
    {"name": "Akasa", "base_url": "https://akasaair.com", "reliability": 0.97}
]

AIRPORTS = [
    {"code": "DEL", "city": "Delhi"},
    {"code": "BOM", "city": "Mumbai"},
    {"code": "BLR", "city": "Bangalore"},
    {"code": "CCU", "city": "Kolkata"},
    {"code": "MAA", "city": "Chennai"},
    {"code": "HYD", "city": "Hyderabad"}
]

ROUTES_DEF = [
    {"origin": "DEL", "dest": "BOM", "base": 5500, "weight": 0.25},
    {"origin": "DEL", "dest": "BLR", "base": 7200, "weight": 0.20},
    {"origin": "BOM", "dest": "BLR", "base": 4500, "weight": 0.15},
    {"origin": "DEL", "dest": "CCU", "base": 6100, "weight": 0.15},
    {"origin": "BLR", "dest": "HYD", "base": 3200, "weight": 0.15},
    {"origin": "MAA", "dest": "DEL", "base": 6800, "weight": 0.10}
]

LEAD_TIMES = [1, 7, 15, 30, 45]

def seed_static_data(db: Session):
    for s in SOURCES:
        if not db.query(Source).filter(Source.name == s["name"]).first():
            db.add(Source(name=s["name"], base_url=s["base_url"], reliability_score=s["reliability"]))
    
    for a in AIRPORTS:
        if not db.query(Airport).filter(Airport.code == a["code"]).first():
            db.add(Airport(code=a["code"], city_name=a["city"]))
            
    db.commit()
    
    for r in ROUTES_DEF:
        if not db.query(Route).filter(Route.origin_code == r["origin"], Route.dest_code == r["dest"]).first():
            db.add(Route(origin_code=r["origin"], dest_code=r["dest"], base_fare_p0=r["base"], weight=r["weight"]))
            
    db.commit()

def run_seeder(db: Session, days: int = 30):
    if db.query(RawQuote).first():
        print("Database already seeded. Skipping.")
        return

    print("Starting seeder...")
    seed_static_data(db)
    
    random.seed(42) # Deterministic
    today = date.today()
    start_date = today - timedelta(days=days-1)
    
    sources = db.query(Source).all()
    source_names = [s.name for s in sources]
    
    for d in range(days):
        current_date = start_date + timedelta(days=d)
        print(f"Seeding day: {current_date}")
        
        for r in ROUTES_DEF:
            base_price = r["base"]
            
            # Add a slight trend over time
            trend_multiplier = 1.0 + (d * 0.002) # 0.2% increase per day
            
            for lead in LEAD_TIMES:
                # Lead time curve: T+1 is expensive, T+45 is cheap
                lead_multiplier = 1.0
                if lead == 1: lead_multiplier = 1.5
                elif lead == 7: lead_multiplier = 1.2
                elif lead == 15: lead_multiplier = 1.0
                elif lead == 30: lead_multiplier = 0.85
                elif lead == 45: lead_multiplier = 0.75
                
                for source_name in source_names:
                    # Randomize a bit
                    noise = random.uniform(0.95, 1.05)
                    final_base = base_price * trend_multiplier * lead_multiplier * noise
                    taxes = final_base * 0.18
                    fees = 300
                    
                    is_anomaly = random.random() < 0.05
                    
                    origin_str = r["origin"]
                    if is_anomaly and random.random() < 0.5:
                        origin_str = "Bombay" if origin_str == "BOM" else origin_str
                        
                    if is_anomaly and random.random() < 0.5:
                        final_base = 48000
                        
                    if is_anomaly and random.random() < 0.5:
                        taxes = None # Missing taxes
                        
                    total = final_base + (taxes or 0) + fees
                    
                    quote_data = {
                        "source": source_name,
                        "collection_timestamp": current_date.strftime("%Y-%m-%dT10:00:00"),
                        "origin": origin_str,
                        "destination": r["dest"],
                        "travel_date": (current_date + timedelta(days=lead)).strftime("%Y-%m-%d"),
                        "airline": random.choice(["6E", "AI", "QP"]),
                        "flight_number": str(random.randint(100, 999)),
                        "base_fare": final_base,
                        "taxes": taxes,
                        "fees": fees,
                        "total_fare": total
                    }
                    
                    # 1. Ingestion
                    raw = ingest_raw_quote(db, quote_data)
                    # 2. Refinement
                    refined = refine_quote(db, raw)
                    # 3. Validation
                    validated = validate_quote(db, refined)
                    # 4. Quality & Anomaly
                    process_quality_and_anomaly(db, validated)
        
        # 5. Index Engine
        calculate_daily_apix(db, current_date)
        
    print("Seeding complete.")
