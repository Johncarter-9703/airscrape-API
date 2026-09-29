# AIR-SCRAPE: Airfare Price Index (APIx) Data Engine & Intelligence Platform

This project implements an end-to-end data pipeline and intelligence dashboard for calculating and visualizing the Airfare Price Index (APIx).

## Architecture

The system consists of two main components:
1.  **FastAPI Backend (Data Engine)**: Ingests raw JSON flight quotes, refines them, validates them against constraints, identifies anomalies, calculates confidence scores, and determines the APIx base relative prices. It exposes these metrics via REST APIs.
2.  **Next.js Frontend (Intelligence Platform)**: A React-based, high-density dashboard built with Tailwind CSS and Recharts to visualize the daily/weekly indices, route performance, elasticity curves, and system health.

## Running the Prototype Locally

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 1. Booting the Backend Data Engine

The backend comes with a built-in `seeder.py` that will automatically generate 30 days of deterministic historical flight data (with deliberate anomalies) on first boot. The database uses SQLite by default for zero-dependency setup.

```bash
cd backend
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
*The API will be available at http://localhost:8000*
*Swagger Documentation: http://localhost:8000/docs*

### 2. Booting the Frontend Dashboard

Open a new terminal window:

```bash
cd frontend
# Install dependencies
npm install
npm install recharts lucide-react

# Start the Next.js development server
npm run dev
```
*The Dashboard will be available at http://localhost:3000*

## API Features
- `GET /api/apix/summary`: Current APIx score and health metrics.
- `GET /api/apix/timeseries`: Historical index data.
- `GET /api/routes`: Route specific pricing info.
- `GET /api/routes/{code}/lead-time`: Fares categorized by advance booking buckets.
- `GET /api/anomalies/recent`: List of data anomalies caught by the quality engine.
- `POST /api/pipeline/trigger-run`: Webhook to ingest new JSON scraper payloads.
