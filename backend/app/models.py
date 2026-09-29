from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class LeadTimeBucket(str, enum.Enum):
    T_1 = "T+1"
    T_7 = "T+7"
    T_15 = "T+15"
    T_30 = "T+30"
    T_45 = "T+45"

class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"

class ValidationStatus(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"

class QualityStatus(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    base_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    reliability_score = Column(Float, default=1.0)
    
class Airport(Base):
    __tablename__ = "airports"
    code = Column(String(3), primary_key=True, index=True)
    city_name = Column(String)
    state = Column(String, nullable=True)

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    origin_code = Column(String(3), ForeignKey("airports.code"))
    dest_code = Column(String(3), ForeignKey("airports.code"))
    base_fare_p0 = Column(Float)
    weight = Column(Float)

    origin = relationship("Airport", foreign_keys=[origin_code])
    dest = relationship("Airport", foreign_keys=[dest_code])

class RawQuote(Base):
    __tablename__ = "raw_quotes"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    collection_timestamp = Column(DateTime)
    origin = Column(String)
    destination = Column(String)
    travel_date = Column(Date)
    airline = Column(String)
    flight_number = Column(String)
    raw_payload = Column(Text) # Stored as JSON string
    artifact_path = Column(Text, nullable=True)

class RefinedQuote(Base):
    __tablename__ = "refined_quotes"
    id = Column(Integer, primary_key=True, index=True)
    raw_quote_id = Column(String, ForeignKey("raw_quotes.id"))
    origin = Column(String(3))
    destination = Column(String(3))
    travel_date = Column(Date)
    collection_date = Column(Date)
    lead_time_bucket = Column(Enum(LeadTimeBucket))
    lead_time_days = Column(Integer)
    airline = Column(String)
    flight_number = Column(String)
    base_fare = Column(Float, nullable=True)
    taxes = Column(Float, nullable=True)
    fees = Column(Float, nullable=True)
    total_fare = Column(Float)
    fare_hash = Column(Text, unique=True, index=True)
    availability = Column(Enum(AvailabilityStatus))

    raw_quote = relationship("RawQuote")

class ValidatedQuote(Base):
    __tablename__ = "validated_quotes"
    id = Column(Integer, primary_key=True, index=True)
    refined_quote_id = Column(Integer, ForeignKey("refined_quotes.id"))
    validation_status = Column(Enum(ValidationStatus))
    rejection_reason = Column(Text, nullable=True)

    refined_quote = relationship("RefinedQuote")

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    validated_quote_id = Column(Integer, ForeignKey("validated_quotes.id"))
    z_score = Column(Float, nullable=True)
    anomaly_score = Column(Float)
    cross_source_delta = Column(Float, nullable=True)
    flag_reason = Column(Text)
    quality_status = Column(Enum(QualityStatus))
    
    validated_quote = relationship("ValidatedQuote")

class MarketTruthQuote(Base):
    __tablename__ = "market_truth_quotes"
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("validated_quotes.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    travel_date = Column(Date)
    lead_time_bucket = Column(Enum(LeadTimeBucket))
    final_fare = Column(Float)
    confidence_score = Column(Float)

    validated_quote = relationship("ValidatedQuote")
    route = relationship("Route")

class RouteDailyIndex(Base):
    __tablename__ = "route_daily_indices"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    route_id = Column(Integer, ForeignKey("routes.id"))
    lead_time_bucket = Column(Enum(LeadTimeBucket))
    representative_fare = Column(Float)
    price_relative = Column(Float)

    route = relationship("Route")

class APIxDaily(Base):
    __tablename__ = "apix_daily"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    index_value = Column(Float)
    base_period = Column(Text)
    total_observations = Column(Integer)
    quality_score = Column(Float)

class APIxWeekly(Base):
    __tablename__ = "apix_weekly"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    week_number = Column(Integer)
    index_value = Column(Float)
    start_date = Column(Date)
    end_date = Column(Date)

class APIxMonthly(Base):
    __tablename__ = "apix_monthly"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer)
    month = Column(Integer)
    index_value = Column(Float)
