from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from typing import List

from .database import engine, Base, get_db
from . import models, schemas
from .services.seeder import run_seeder
from .services.ingestion import ingest_batch
from .services.refinement import refine_quote
from .services.validation import validate_quote
from .services.quality import process_quality_and_anomaly
from .services.index_engine import calculate_daily_apix

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AIR-SCRAPE APIx Data Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    run_seeder(db, days=30)
    db.close()

@app.get("/api/apix/summary", response_model=schemas.APIxSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    latest = db.query(models.APIxDaily).order_by(desc(models.APIxDaily.date)).first()
    if not latest:
        raise HTTPException(status_code=404, detail="No data available")
        
    previous = db.query(models.APIxDaily).filter(models.APIxDaily.date < latest.date).order_by(desc(models.APIxDaily.date)).first()
    
    delta = 0.0
    if previous and previous.index_value > 0:
        delta = ((latest.index_value - previous.index_value) / previous.index_value) * 100
        
    # monthly average
    month_start = latest.date.replace(day=1)
    monthly_avg = db.query(func.avg(models.APIxDaily.index_value)).filter(models.APIxDaily.date >= month_start).scalar()
    
    return schemas.APIxSummaryResponse(
        current_apix=round(latest.index_value, 2),
        delta_24h=round(delta, 2),
        monthly_average=round(monthly_avg or 0.0, 2),
        data_quality_percentage=round(latest.quality_score, 2)
    )

@app.get("/api/apix/timeseries", response_model=schemas.TimeseriesResponse)
def get_timeseries(range: str = "30d", interval: str = "daily", db: Session = Depends(get_db)):
    days = 30
    if range == "90d": days = 90
    elif range == "1y": days = 365
    
    start_date = date.today() - timedelta(days=days)
    
    if interval == "daily":
        data = db.query(models.APIxDaily).filter(models.APIxDaily.date >= start_date).order_by(models.APIxDaily.date).all()
        points = [schemas.TimeseriesDataPoint(date=d.date, index_value=round(d.index_value, 2)) for d in data]
    else:
        # Simplified: returning daily for now as fallback
        data = db.query(models.APIxDaily).filter(models.APIxDaily.date >= start_date).order_by(models.APIxDaily.date).all()
        points = [schemas.TimeseriesDataPoint(date=d.date, index_value=round(d.index_value, 2)) for d in data]
        
    return schemas.TimeseriesResponse(range=range, interval=interval, data=points)

@app.get("/api/routes", response_model=List[schemas.RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    routes = db.query(models.Route).all()
    latest_date = db.query(func.max(models.RouteDailyIndex.date)).scalar()
    
    res = []
    for r in routes:
        rdi = db.query(models.RouteDailyIndex).filter(
            models.RouteDailyIndex.route_id == r.id,
            models.RouteDailyIndex.date == latest_date
        ).first()
        
        current_fare = rdi.representative_fare if rdi else r.base_fare_p0
        change = ((current_fare - r.base_fare_p0) / r.base_fare_p0) * 100
        
        # Fetch latest source prices by joining through the pipeline to get the OTA name
        quotes = db.query(models.MarketTruthQuote, models.Source.name).join(
            models.ValidatedQuote, models.MarketTruthQuote.quote_id == models.ValidatedQuote.id
        ).join(
            models.RefinedQuote, models.ValidatedQuote.refined_quote_id == models.RefinedQuote.id
        ).join(
            models.RawQuote, models.RefinedQuote.raw_quote_id == models.RawQuote.id
        ).join(
            models.Source, models.RawQuote.source_id == models.Source.id
        ).filter(
            models.MarketTruthQuote.route_id == r.id,
            models.RefinedQuote.collection_date == latest_date
        ).all()
        
        source_prices = {source_name: round(mq.final_fare, 2) for mq, source_name in quotes if source_name}
        
        res.append(schemas.RouteResponse(
            route_code=f"{r.origin_code}-{r.dest_code}",
            origin=r.origin_code,
            destination=r.dest_code,
            base_fare_p0=r.base_fare_p0,
            current_representative_fare=round(current_fare, 2),
            weight=r.weight,
            price_change_percentage=round(change, 2),
            source_prices=source_prices
        ))
    return res

@app.get("/api/routes/{route_code}/lead-time", response_model=schemas.RouteLeadTimeResponse)
def get_route_lead_time(route_code: str, db: Session = Depends(get_db)):
    parts = route_code.split("-")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid route code")
        
    route = db.query(models.Route).filter(models.Route.origin_code == parts[0], models.Route.dest_code == parts[1]).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    latest_date = db.query(func.max(models.MarketTruthQuote.travel_date)).scalar()
    
    quotes = db.query(
        models.MarketTruthQuote.lead_time_bucket,
        func.avg(models.MarketTruthQuote.final_fare).label('avg_fare')
    ).filter(
        models.MarketTruthQuote.route_id == route.id,
        models.MarketTruthQuote.travel_date >= date.today()
    ).group_by(models.MarketTruthQuote.lead_time_bucket).all()
    
    data = []
    for q in quotes:
        data.append(schemas.RouteLeadTimeData(lead_time_bucket=q[0], representative_fare=round(q[1], 2)))
        
    # Sort logically
    order = {"T+1": 1, "T+7": 2, "T+15": 3, "T+30": 4, "T+45": 5}
    data.sort(key=lambda x: order.get(x.lead_time_bucket.value, 99))
    
    return schemas.RouteLeadTimeResponse(route_code=route_code, data=data)

@app.get("/api/anomalies/recent", response_model=List[schemas.AnomalyResponse])
def get_recent_anomalies(limit: int = 10, db: Session = Depends(get_db)):
    anomalies = db.query(models.Anomaly).join(models.ValidatedQuote).join(models.RefinedQuote).order_by(desc(models.Anomaly.id)).limit(limit).all()
    
    res = []
    for a in anomalies:
        refined = a.validated_quote.refined_quote
        # Calculate expected roughly from Z-score if needed or just return raw
        # Expected = raw - (z * std), we'll simplify and say expected is median which we can infer
        
        res.append(schemas.AnomalyResponse(
            id=a.id,
            date=refined.collection_date,
            route=f"{refined.origin}-{refined.destination}",
            airline=refined.airline,
            flight_number=refined.flight_number,
            raw_fare=refined.total_fare,
            expected_fare=0, # Simplified
            z_score=round(a.z_score or 0.0, 2),
            reason=a.flag_reason,
            status=a.quality_status
        ))
    return res

@app.get("/api/system/health", response_model=schemas.SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    active_sources = db.query(func.count(models.Source.id)).filter(models.Source.is_active == True).scalar()
    total_quotes = db.query(func.count(models.RawQuote.id)).scalar()
    
    total_validated = db.query(func.count(models.ValidatedQuote.id)).scalar()
    invalid_count = db.query(func.count(models.ValidatedQuote.id)).filter(models.ValidatedQuote.validation_status == models.ValidationStatus.INVALID).scalar()
    
    invalid_rate = (invalid_count / total_validated * 100) if total_validated > 0 else 0
    
    flagged_count = db.query(func.count(models.Anomaly.id)).filter(models.Anomaly.quality_status == models.QualityStatus.FLAGGED).scalar()
    flagged_rate = (flagged_count / total_validated * 100) if total_validated > 0 else 0
    
    last_quote = db.query(func.max(models.RawQuote.collection_timestamp)).scalar()
    last_time_str = last_quote.isoformat() if last_quote else None
    
    return schemas.SystemHealthResponse(
        active_sources=active_sources,
        total_quotes_parsed=total_quotes,
        invalid_rate_percentage=round(invalid_rate, 2),
        flagged_rate_percentage=round(flagged_rate, 2),
        last_ingestion_time=last_time_str
    )

from .services.scraper import trigger_live_scraper_sync

def pipeline_task(db: Session, quotes: list[dict]):
    raw_quotes = ingest_batch(db, quotes)
    for raw in raw_quotes:
        refined = refine_quote(db, raw)
        validated = validate_quote(db, refined)
        process_quality_and_anomaly(db, validated)
    calculate_daily_apix(db, date.today())

@app.post("/api/pipeline/trigger-run")
def trigger_pipeline(quotes: list[dict], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(pipeline_task, db, quotes)
    return {"message": f"Pipeline triggered for {len(quotes)} quotes"}

def live_scraper_task(db: Session):
    trigger_live_scraper_sync(db)

@app.post("/api/pipeline/scrape-live")
def trigger_live_scraper(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(live_scraper_task, db)
    return {"message": "Live scraping triggered successfully. Data will update shortly."}
