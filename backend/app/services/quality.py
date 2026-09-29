import numpy as np
from sqlalchemy.orm import Session
from app.models import ValidatedQuote, Anomaly, MarketTruthQuote, QualityStatus, Route, ValidationStatus, RefinedQuote, RawQuote, Source
from sqlalchemy import func

def compute_z_score(db: Session, quote: ValidatedQuote) -> float:
    refined = quote.refined_quote
    # Find historical fares for the same route and lead time bucket
    historical_quotes = db.query(RefinedQuote.total_fare).join(ValidatedQuote).filter(
        RefinedQuote.origin == refined.origin,
        RefinedQuote.destination == refined.destination,
        RefinedQuote.lead_time_bucket == refined.lead_time_bucket,
        ValidatedQuote.validation_status == ValidationStatus.VALID,
        RefinedQuote.total_fare != None
    ).all()
    
    fares = [q[0] for q in historical_quotes]
    if not fares:
        return 0.0 # No history, assume normal
    
    mean_fare = np.mean(fares)
    std_fare = np.std(fares)
    
    if std_fare == 0:
        return 0.0
        
    z = (refined.total_fare - mean_fare) / std_fare
    return float(z)

def check_cross_source_consensus(db: Session, quote: ValidatedQuote) -> float:
    refined = quote.refined_quote
    
    # Get all quotes for the same route and travel date
    concurrent_quotes = db.query(RefinedQuote, Source).select_from(RefinedQuote).join(
        RawQuote, RefinedQuote.raw_quote_id == RawQuote.id
    ).join(
        Source, RawQuote.source_id == Source.id
    ).filter(
        RefinedQuote.origin == refined.origin,
        RefinedQuote.destination == refined.destination,
        RefinedQuote.travel_date == refined.travel_date,
        RefinedQuote.flight_number == refined.flight_number
    ).all()
    
    if not concurrent_quotes:
        return 0.0
        
    # Simplified: check variance between this quote and median of concurrent quotes
    fares = [q[0].total_fare for q in concurrent_quotes if q[0].total_fare > 0]
    if not fares:
        return 0.0
        
    median_fare = np.median(fares)
    if median_fare == 0:
        return 0.0
        
    variance = abs(refined.total_fare - median_fare) / median_fare
    return float(variance)

def process_quality_and_anomaly(db: Session, validated_quote: ValidatedQuote):
    if validated_quote.validation_status == ValidationStatus.INVALID:
        return None
        
    refined = validated_quote.refined_quote
    if refined.availability != "AVAILABLE" or refined.total_fare == 0:
        return None
        
    raw_quote = refined.raw_quote
    source = db.query(Source).filter(Source.id == raw_quote.source_id).first()
    source_reliability = source.reliability_score if source else 1.0

    z_score = compute_z_score(db, validated_quote)
    cross_source_delta = check_cross_source_consensus(db, validated_quote)
    
    anomaly_score = 0.0
    flag_reasons = []
    
    if abs(z_score) > 2.5:
        anomaly_score += 0.5
        flag_reasons.append(f"High Z-Score ({z_score:.2f})")
        
    if cross_source_delta > 0.30:
        anomaly_score += 0.3
        flag_reasons.append(f"High Cross-Source Variance ({cross_source_delta:.0%})")
        
    # Tax missing penalty
    tax_penalty = 1.0
    if refined.taxes is None:
        tax_penalty = 0.9
        
    # Confidence Score
    # Formula: Confidence = (1 - AnomalyScore) * SourceReliabilityWeight * (0.9 if TaxDerived else 1.0)
    anomaly_score = min(anomaly_score, 1.0)
    confidence_score = (1 - anomaly_score) * source_reliability * tax_penalty
    
    quality_status = QualityStatus.ACCEPTED
    if confidence_score < 0.85:
        if anomaly_score > 0:
            quality_status = QualityStatus.FLAGGED
        else:
            quality_status = QualityStatus.REJECTED
    
    # Always record anomaly if it's flagged or there's some anomaly score
    if anomaly_score > 0 or quality_status != QualityStatus.ACCEPTED:
        anomaly = Anomaly(
            validated_quote_id=validated_quote.id,
            z_score=z_score,
            anomaly_score=anomaly_score,
            cross_source_delta=cross_source_delta,
            flag_reason=" | ".join(flag_reasons) if flag_reasons else "Low Confidence",
            quality_status=quality_status
        )
        db.add(anomaly)
    
    if quality_status == QualityStatus.ACCEPTED:
        # Promote to market truth
        route = db.query(Route).filter(
            Route.origin_code == refined.origin,
            Route.dest_code == refined.destination
        ).first()
        
        if route:
            truth = MarketTruthQuote(
                quote_id=validated_quote.id,
                route_id=route.id,
                travel_date=refined.travel_date,
                lead_time_bucket=refined.lead_time_bucket,
                final_fare=refined.total_fare,
                confidence_score=confidence_score
            )
            db.add(truth)
            
    db.commit()
