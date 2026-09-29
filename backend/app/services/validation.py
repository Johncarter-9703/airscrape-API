from sqlalchemy.orm import Session
from app.models import RefinedQuote, ValidatedQuote, ValidationStatus, Route, AvailabilityStatus

def validate_quote(db: Session, refined_quote: RefinedQuote) -> ValidatedQuote:
    is_valid = True
    reasons = []

    # Schema completeness
    if not refined_quote.origin or not refined_quote.destination:
        is_valid = False
        reasons.append("Missing origin or destination")
    if not refined_quote.travel_date or not refined_quote.collection_date:
        is_valid = False
        reasons.append("Missing dates")

    # Route verification
    if refined_quote.origin == refined_quote.destination:
        is_valid = False
        reasons.append("Origin and destination are the same")
    
    # Check if route exists
    route = db.query(Route).filter(
        Route.origin_code == refined_quote.origin,
        Route.dest_code == refined_quote.destination
    ).first()
    if not route:
        is_valid = False
        reasons.append(f"Route {refined_quote.origin}-{refined_quote.destination} not in target basket")

    # Price boundary checks (only if available)
    if refined_quote.availability == AvailabilityStatus.AVAILABLE:
        if refined_quote.total_fare < 1000:
            is_valid = False
            reasons.append("Fare below minimum threshold (1000)")
        elif refined_quote.total_fare > 150000:
            is_valid = False
            reasons.append("Fare above maximum threshold (150000)")

    # Date integrity
    if refined_quote.travel_date and refined_quote.collection_date:
        if refined_quote.travel_date < refined_quote.collection_date:
            is_valid = False
            reasons.append("Travel date is before collection date")

    status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID
    rejection_reason = " | ".join(reasons) if not is_valid else None
    
    validated_quote = ValidatedQuote(
        refined_quote_id=refined_quote.id,
        validation_status=status,
        rejection_reason=rejection_reason
    )
    
    db.add(validated_quote)
    db.commit()
    db.refresh(validated_quote)
    return validated_quote
