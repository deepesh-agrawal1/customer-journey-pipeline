
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

app = FastAPI(
    title="Customer Journey Analytics API",
    description="API for customer journey metrics, outcomes, analytics, and data quality.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STAGED_DIR = DATA_DIR / "staged"
QUARANTINE_DIR = DATA_DIR / "quarantine"
CURATED_DIR = DATA_DIR / "curated"

METRICS_FILE = CURATED_DIR / "journey_metrics.csv"
FUNNEL_FILE = CURATED_DIR / "journey_funnel.csv"
OUTCOMES_FILE = CURATED_DIR / "journey_outcomes.csv"

SESSIONS_FILE = STAGED_DIR / "sessions.csv"
EVENTS_FILE = STAGED_DIR / "journey_events.csv"
CUSTOMERS_FILE = STAGED_DIR / "customers.csv"
PAGES_FILE = STAGED_DIR / "pages.csv"
PRODUCTS_FILE = STAGED_DIR / "products.csv"


# --------------------------------------------------
# Shared helpers
# --------------------------------------------------

def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a project CSV or return a useful API error."""
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Required data file not found: {path.name}. Run the pipeline first.",
        )

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=500,
            detail=f"Data file is empty or invalid: {path.name}.",
        )
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read {path.name}: {str(exc)}",
        )


def require_columns(
    df: pd.DataFrame,
    columns: set[str],
    filename: str,
) -> None:
    missing = columns - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"{filename} is missing required columns: {sorted(missing)}",
        )


def outcome_summary(df: pd.DataFrame) -> dict:
    """Summarize the outcome labels actually present in the data."""
    require_columns(df, {"session_id", "outcome"}, OUTCOMES_FILE.name)

    unique = df.drop_duplicates(subset=["session_id"])
    counts = unique["outcome"].fillna("unknown").value_counts().to_dict()
    total = len(unique)

    labels = {
        "converted": "Converted",
        "support_required": "Support required",
        "no_conversion": "Non-converted",
        "unknown": "Unknown",
    }

    outcomes = []
    for key in [
        "converted",
        "support_required",
        "no_conversion",
        "unknown",
    ]:
        count = int(counts.get(key, 0))
        outcomes.append({
            "outcome": key,
            "label": labels[key],
            "count": count,
            "percentage": round(count / total * 100, 2) if total else 0,
        })

    # Preserve any additional outcome labels instead of silently discarding them.
    known = set(labels)
    for key, value in counts.items():
        if key not in known:
            count = int(value)
            outcomes.append({
                "outcome": str(key),
                "label": str(key).replace("_", " ").title(),
                "count": count,
                "percentage": round(count / total * 100, 2) if total else 0,
            })

    return {"total_sessions": int(total), "outcomes": outcomes}


def optional_lookup(path: Path, id_column: str, label_candidates: list[str]) -> dict:
    """Build an ID-to-label map when a matching lookup column exists."""
    if not path.exists():
        return {}

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, OSError, pd.errors.ParserError):
        return {}

    if id_column not in df.columns:
        return {}

    label_column = next(
        (column for column in label_candidates if column in df.columns),
        None,
    )
    if not label_column:
        return {}

    return (
        df.dropna(subset=[id_column])
        .drop_duplicates(subset=[id_column])
        .set_index(id_column)[label_column]
        .astype(str)
        .to_dict()
    )


# --------------------------------------------------
# Health and existing dashboard endpoints
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "customer-journey-analytics",
    }


@app.get("/api/metrics")
def get_metrics():
    df = read_csv_file(METRICS_FILE)

    if df.empty:
        raise HTTPException(status_code=404, detail="Metrics file contains no data.")

    return df.iloc[0].to_dict()


@app.get("/api/funnel")
def get_funnel():
    df = read_csv_file(FUNNEL_FILE)

    if df.empty:
        raise HTTPException(status_code=404, detail="Funnel file contains no data.")

    return df.to_dict(orient="records")


@app.get("/api/quality")
def get_quality():
    datasets = {
        "customers": ("customers.csv", "customers_invalid.csv"),
        "sessions": ("sessions.csv", "sessions_invalid.csv"),
        "events": ("journey_events.csv", "journey_events_invalid.csv"),
        "pages": ("pages.csv", "pages_invalid.csv"),
        "products": ("products.csv", "products_invalid.csv"),
    }

    results = []
    total_records = 0
    total_valid = 0
    total_quarantined = 0

    for name, (valid_file, invalid_file) in datasets.items():
        valid_path = STAGED_DIR / valid_file
        invalid_path = QUARANTINE_DIR / invalid_file

        valid_df = read_csv_file(valid_path)
        invalid_df = read_csv_file(invalid_path)

        valid_count = len(valid_df)
        invalid_count = len(invalid_df)
        total = valid_count + invalid_count

        results.append({
            "dataset": name,
            "total_records": total,
            "valid_records": valid_count,
            "quarantined_records": invalid_count,
            "quality_rate": round(valid_count / total, 4) if total else 1.0,
        })

        total_records += total
        total_valid += valid_count
        total_quarantined += invalid_count

    return {
        "total_records": total_records,
        "valid_records": total_valid,
        "quarantined_records": total_quarantined,
        "quality_rate": round(total_valid / total_records, 4)
            if total_records else 1.0,
        "datasets": results,
    }


# --------------------------------------------------
# 1. Journey outcomes
# --------------------------------------------------

@app.get("/api/outcomes")
def get_outcomes():
    outcomes = read_csv_file(OUTCOMES_FILE)
    return outcome_summary(outcomes)


# --------------------------------------------------
# 2. Device performance
# --------------------------------------------------

@app.get("/api/devices")
def get_device_performance():
    sessions = read_csv_file(SESSIONS_FILE)
    outcomes = read_csv_file(OUTCOMES_FILE)

    require_columns(sessions, {"session_id", "device"}, SESSIONS_FILE.name)
    require_columns(outcomes, {"session_id", "outcome"}, OUTCOMES_FILE.name)

    sessions = sessions.drop_duplicates(subset=["session_id"])
    outcomes = outcomes.drop_duplicates(subset=["session_id"])

    merged = sessions[["session_id", "device"]].merge(
        outcomes[["session_id", "outcome"]],
        on="session_id",
        how="left",
        validate="one_to_one",
    )

    merged["device"] = (
        merged["device"].fillna("unknown").astype(str).str.lower()
    )

    results = []
    for device, group in merged.groupby("device", sort=True):
        total = len(group)
        converted = int((group["outcome"] == "converted").sum())

        results.append({
            "device": str(device),
            "total_sessions": int(total),
            "converted_sessions": converted,
            "conversion_rate": round(converted / total, 4) if total else 0,
        })

    return {
        "total_sessions": int(len(merged)),
        "devices": results,
    }


# --------------------------------------------------
# 3. Page and product performance
# --------------------------------------------------

@app.get("/api/performance")
def get_page_product_performance():
    events = read_csv_file(EVENTS_FILE)

    require_columns(
        events,
        {"session_id", "event_type"},
        EVENTS_FILE.name,
    )

    page_labels = optional_lookup(
        PAGES_FILE,
        "page_id",
        ["page_name", "name", "title", "page_title"],
    )
    product_labels = optional_lookup(
        PRODUCTS_FILE,
        "product_id",
        ["product_name", "name", "title"],
    )

    # Only aggregate records that actually have a page or product identifier.
    page_events = events.dropna(subset=["page_id"]).copy() \
        if "page_id" in events.columns else events.iloc[0:0].copy()

    product_events = events.dropna(subset=["product_id"]).copy() \
        if "product_id" in events.columns else events.iloc[0:0].copy()

    pages = []
    if not page_events.empty:
        grouped = page_events.groupby("page_id")
        for page_id, group in grouped:
            pages.append({
                "page_id": str(page_id),
                "page_name": page_labels.get(str(page_id), str(page_id)),
                "event_count": int(len(group)),
                "sessions": int(group["session_id"].nunique()),
                "page_views": int(
                    (group["event_type"] == "page_view").sum()
                ),
            })

    products = []
    if not product_events.empty:
        grouped = product_events.groupby("product_id")
        for product_id, group in grouped:
            products.append({
                "product_id": str(product_id),
                "product_name": product_labels.get(
                    str(product_id), str(product_id)
                ),
                "event_count": int(len(group)),
                "sessions": int(group["session_id"].nunique()),
                "item_views": int(
                    (group["event_type"] == "item_viewed").sum()
                ),
                "add_to_cart_events": int(
                    (group["event_type"] == "add_to_cart").sum()
                ),
                "purchase_events": int(
                    (group["event_type"] == "purchase").sum()
                ),
            })

    pages.sort(key=lambda row: row["sessions"], reverse=True)
    products.sort(key=lambda row: row["sessions"], reverse=True)

    return {
        "total_events": int(len(events)),
        "page_performance": pages,
        "product_performance": products,
    }


# --------------------------------------------------
# 4. Time-based trends
# --------------------------------------------------

@app.get("/api/trends")
def get_time_trends(
    interval: str = Query("day", pattern="^(day|week|month)$"),
):
    sessions = read_csv_file(SESSIONS_FILE)
    outcomes = read_csv_file(OUTCOMES_FILE)

    require_columns(sessions, {"session_id", "started_at"}, SESSIONS_FILE.name)
    require_columns(outcomes, {"session_id", "outcome"}, OUTCOMES_FILE.name)

    sessions = sessions.drop_duplicates(subset=["session_id"]).copy()
    outcomes = outcomes.drop_duplicates(subset=["session_id"])

    sessions["started_at"] = pd.to_datetime(
        sessions["started_at"], errors="coerce", utc=True
    )
    sessions = sessions.dropna(subset=["started_at"])

    merged = sessions.merge(
        outcomes[["session_id", "outcome"]],
        on="session_id",
        how="left",
        validate="one_to_one",
    )

    if interval == "day":
        merged["period"] = merged["started_at"].dt.strftime("%Y-%m-%d")
    elif interval == "week":
        merged["period"] = (
            merged["started_at"].dt.to_period("W").astype(str)
        )
    else:
        merged["period"] = merged["started_at"].dt.strftime("%Y-%m")

    trends = []
    for period, group in merged.groupby("period", sort=True):
        total = len(group)
        converted = int((group["outcome"] == "converted").sum())

        trends.append({
            "period": str(period),
            "sessions": int(total),
            "converted_sessions": converted,
            "conversion_rate": round(converted / total, 4) if total else 0,
        })

    return {
        "interval": interval,
        "total_periods": len(trends),
        "trends": trends,
    }


# --------------------------------------------------
# 5. Session explorer with pagination and filters
# --------------------------------------------------

@app.get("/api/sessions")
def get_sessions(
    q: str | None = Query(default=None, max_length=100),
    device: str | None = Query(default=None, max_length=50),
    outcome: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    sessions = read_csv_file(SESSIONS_FILE)
    outcomes = read_csv_file(OUTCOMES_FILE)

    require_columns(
        sessions,
        {"session_id", "customer_id", "started_at", "device"},
        SESSIONS_FILE.name,
    )
    require_columns(outcomes, {"session_id", "outcome"}, OUTCOMES_FILE.name)

    sessions = sessions.drop_duplicates(subset=["session_id"])
    outcomes = outcomes.drop_duplicates(subset=["session_id"])

    merged = sessions.merge(
        outcomes[["session_id", "outcome"]],
        on="session_id",
        how="left",
        validate="one_to_one",
    )

    if q:
        mask = (
            merged["session_id"].astype(str).str.contains(q, case=False, na=False)
            | merged["customer_id"].astype(str).str.contains(
                q, case=False, na=False
            )
        )
        merged = merged[mask]

    if device:
        merged = merged[
            merged["device"].astype(str).str.lower() == device.lower()
        ]

    if outcome:
        merged = merged[
            merged["outcome"].astype(str).str.lower() == outcome.lower()
        ]

    total = len(merged)
    records = merged.iloc[offset:offset + limit].copy()

    # Make missing CSV values safe for JSON serialization.
    records = records.astype(object).where(pd.notna(records), None)

    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "sessions": records.to_dict(orient="records"),
    }


# --------------------------------------------------
# 6. Events for an individual session
# --------------------------------------------------

@app.get("/api/sessions/{session_id}/events")
def get_session_events(session_id: str):
    sessions = read_csv_file(SESSIONS_FILE)
    events = read_csv_file(EVENTS_FILE)

    require_columns(sessions, {"session_id"}, SESSIONS_FILE.name)
    require_columns(
        events,
        {"session_id", "event_id", "event_type", "event_timestamp"},
        EVENTS_FILE.name,
    )

    matching_session = sessions[
        sessions["session_id"].astype(str) == session_id
    ]

    if matching_session.empty:
        raise HTTPException(status_code=404, detail="Session not found.")

    matching_events = events[
        events["session_id"].astype(str) == session_id
    ].copy()

    matching_events["event_timestamp"] = pd.to_datetime(
        matching_events["event_timestamp"], errors="coerce", utc=True
    )
    matching_events = matching_events.sort_values(
        "event_timestamp", na_position="last"
    )

    matching_events["event_timestamp"] = (
        matching_events["event_timestamp"].astype(str)
    )
    matching_events = matching_events.astype(object).where(
        pd.notna(matching_events), None
    )

    return {
        "session_id": session_id,
        "event_count": int(len(matching_events)),
        "events": matching_events.to_dict(orient="records"),
    }
