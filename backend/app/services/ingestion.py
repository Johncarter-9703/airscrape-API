import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import RawQuote, Source
import uuid

ARTIFACTS_DIR = os.path.join(os.getcwd(), "artifacts")

def ensure_artifacts_dir():
    if not os.path.exists(ARTIFACTS_DIR):
        os.makedirs(ARTIFACTS_DIR)

def ingest_raw_quote(db: Session, quote_data: dict) -> RawQuote:
    """
    Ingests a single raw quote dictionary into the database and 
    saves a simulated artifact.
    """
    ensure_artifacts_dir()
    
    # Extract data
    source_name = quote_data.get("source")
    source = db.query(Source).filter(Source.name == source_name).first()
    source_id = source.id if source else None
    
    collection_time_str = quote_data.get("collection_timestamp")
    if isinstance(collection_time_str, str):
        collection_time = datetime.fromisoformat(collection_time_str)
    else:
        collection_time = datetime.utcnow()
        
    origin = quote_data.get("origin")
    destination = quote_data.get("destination")
    travel_date_str = quote_data.get("travel_date")
    travel_date = datetime.strptime(travel_date_str, "%Y-%m-%d").date() if travel_date_str else None
    airline = quote_data.get("airline")
    flight_number = quote_data.get("flight_number")
    
    raw_payload_str = json.dumps(quote_data)
    
    # Save simulated artifact
    quote_uuid = str(uuid.uuid4())
    artifact_filename = f"{quote_uuid}.json"
    artifact_path = os.path.join(ARTIFACTS_DIR, artifact_filename)
    
    with open(artifact_path, "w") as f:
        f.write(raw_payload_str)
        
    raw_quote = RawQuote(
        id=quote_uuid,
        source_id=source_id,
        collection_timestamp=collection_time,
        origin=origin,
        destination=destination,
        travel_date=travel_date,
        airline=airline,
        flight_number=flight_number,
        raw_payload=raw_payload_str,
        artifact_path=artifact_path
    )
    
    db.add(raw_quote)
    db.commit()
    db.refresh(raw_quote)
    return raw_quote

def ingest_batch(db: Session, quotes: list[dict]):
    """Ingests a batch of quotes."""
    ingested = []
    for q in quotes:
        ingested.append(ingest_raw_quote(db, q))
    return ingested
