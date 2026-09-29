from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from .models import LeadTimeBucket, QualityStatus

class APIxSummaryResponse(BaseModel):
    current_apix: float
    delta_24h: float
    monthly_average: float
    data_quality_percentage: float

class TimeseriesDataPoint(BaseModel):
    date: date
    index_value: float

class TimeseriesResponse(BaseModel):
    range: str
    interval: str
    data: List[TimeseriesDataPoint]

class RouteResponse(BaseModel):
    route_code: str
    origin: str
    destination: str
    base_fare_p0: float
    current_representative_fare: float
    weight: float
    price_change_percentage: float
    source_prices: dict[str, float] = {}

class RouteLeadTimeData(BaseModel):
    lead_time_bucket: LeadTimeBucket
    representative_fare: float

class RouteLeadTimeResponse(BaseModel):
    route_code: str
    data: List[RouteLeadTimeData]

class AnomalyResponse(BaseModel):
    id: int
    date: date
    route: str
    airline: str
    flight_number: str
    raw_fare: float
    expected_fare: float
    z_score: float
    reason: str
    status: QualityStatus

class SystemHealthResponse(BaseModel):
    active_sources: int
    total_quotes_parsed: int
    invalid_rate_percentage: float
    flagged_rate_percentage: float
    last_ingestion_time: Optional[str] = None

class MessageResponse(BaseModel):
    message: str
