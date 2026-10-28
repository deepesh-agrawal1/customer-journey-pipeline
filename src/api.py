
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.routers.health import router as health_router
from src.routers.overview import router as overview_router
from src.routers.analytics import router as analytics_router
from src.routers.anomalies import router as anomalies_router
from src.routers.insights import router as insights_router
from src.api_helpers import (
    PROJECT_ROOT,
    DATA_DIR,
    STAGED_DIR,
    QUARANTINE_DIR,
    CURATED_DIR,
    METRICS_FILE,
    FUNNEL_FILE,
    OUTCOMES_FILE,
    SESSIONS_FILE,
    EVENTS_FILE,
    CUSTOMERS_FILE,
    PAGES_FILE,
    PRODUCTS_FILE,
    read_csv_file,
    require_columns,
    outcome_summary,
    optional_lookup,
)


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

app = FastAPI(
    title="Customer Journey Analytics API",
    description=(
        "API for customer journey metrics, outcomes, "
        "analytics, and data quality."
    ),
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://deepesh-agrawal1.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(overview_router)
app.include_router(analytics_router)
app.include_router(anomalies_router)
app.include_router(insights_router)
