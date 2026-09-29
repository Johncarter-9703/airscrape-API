import numpy as np
from sqlalchemy.orm import Session
from datetime import date, timedelta
from app.models import (
    MarketTruthQuote, Route, RouteDailyIndex, APIxDaily, APIxWeekly, APIxMonthly, LeadTimeBucket
)
from sqlalchemy import func, extract

def calculate_daily_apix(db: Session, target_date: date):
    # 1. Calculate Representative Fare for each route and lead time bucket
    routes = db.query(Route).all()
    
    total_observations_today = 0
    route_relatives = []
    
    for route in routes:
        # For APIx we usually calculate a blended representative fare across buckets or a specific bucket.
        # Let's aggregate across all buckets for simplicity to get a single route price for the day.
        # Or we can compute the median of all market truth quotes for this route on this travel date.
        
        quotes_today = db.query(MarketTruthQuote.final_fare).filter(
            MarketTruthQuote.route_id == route.id,
            MarketTruthQuote.travel_date == target_date
        ).all()
        
        fares = [q[0] for q in quotes_today]
        total_observations_today += len(fares)
        
        if fares:
            representative_fare = np.median(fares)
            price_relative = (representative_fare / route.base_fare_p0) * 100
            
            # Save route daily index
            rdi = db.query(RouteDailyIndex).filter(
                RouteDailyIndex.date == target_date,
                RouteDailyIndex.route_id == route.id
            ).first()
            
            if not rdi:
                rdi = RouteDailyIndex(
                    date=target_date,
                    route_id=route.id,
                    representative_fare=representative_fare,
                    price_relative=price_relative
                )
                db.add(rdi)
            else:
                rdi.representative_fare = representative_fare
                rdi.price_relative = price_relative
                
            route_relatives.append((route.weight, price_relative))
        else:
            # If no data today, we might use previous day's relative or just ignore (weight redistribution)
            # For this prototype, we'll assume we have some data or price relative remains 100
            pass

    # 3. Aggregated Daily Index (APIx_t)
    if route_relatives:
        total_weight = sum(w for w, r in route_relatives)
        apix_val = sum((w / total_weight) * r for w, r in route_relatives) if total_weight > 0 else 100.0
    else:
        apix_val = 100.0
        
    apix_daily = db.query(APIxDaily).filter(APIxDaily.date == target_date).first()
    if not apix_daily:
        apix_daily = APIxDaily(
            date=target_date,
            index_value=apix_val,
            base_period="P0",
            total_observations=total_observations_today,
            quality_score=96.0 # Placeholder for demo
        )
        db.add(apix_daily)
    else:
        apix_daily.index_value = apix_val
        apix_daily.total_observations = total_observations_today

    db.commit()
    
    # 4. Rollups (Weekly, Monthly)
    # Weekly (using ISO calendar)
    iso_year, iso_week, _ = target_date.isocalendar()
    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    weekly_indices = db.query(APIxDaily.index_value).filter(
        APIxDaily.date >= start_of_week,
        APIxDaily.date <= end_of_week
    ).all()
    
    if weekly_indices:
        weekly_val = np.mean([v[0] for v in weekly_indices])
        apix_weekly = db.query(APIxWeekly).filter(
            APIxWeekly.year == iso_year,
            APIxWeekly.week_number == iso_week
        ).first()
        if not apix_weekly:
            db.add(APIxWeekly(year=iso_year, week_number=iso_week, index_value=weekly_val, start_date=start_of_week, end_date=end_of_week))
        else:
            apix_weekly.index_value = weekly_val

    # Monthly
    month = target_date.month
    year = target_date.year
    
    monthly_indices = db.query(APIxDaily.index_value).filter(
        extract('year', APIxDaily.date) == year,
        extract('month', APIxDaily.date) == month
    ).all()
    
    if monthly_indices:
        monthly_val = np.mean([v[0] for v in monthly_indices])
        apix_monthly = db.query(APIxMonthly).filter(
            APIxMonthly.year == year,
            APIxMonthly.month == month
        ).first()
        if not apix_monthly:
            db.add(APIxMonthly(year=year, month=month, index_value=monthly_val))
        else:
            apix_monthly.index_value = monthly_val

    db.commit()
