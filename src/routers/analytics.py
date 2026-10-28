
from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from src.api_helpers import (
    read_csv_file,
    require_columns,
    optional_lookup,
    SESSIONS_FILE,
    EVENTS_FILE,
    OUTCOMES_FILE,
    PAGES_FILE,
    PRODUCTS_FILE,
)

router = APIRouter(tags=["Analytics"])


# --------------------------------------------------
# 1. Device performance
# --------------------------------------------------

@router.get("/api/devices")
def get_device_performance():
    sessions = read_csv_file(SESSIONS_FILE)
    outcomes = read_csv_file(OUTCOMES_FILE)

    require_columns(
        sessions,
        {"session_id", "device"},
        SESSIONS_FILE.name,
    )
    require_columns(
        outcomes,
        {"session_id", "outcome"},
        OUTCOMES_FILE.name,
    )

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
# 2. Page and product performance
# --------------------------------------------------

@router.get("/api/performance")
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

    if "page_id" in events.columns:
        page_events = events.dropna(subset=["page_id"]).copy()
    else:
        page_events = events.iloc[0:0].copy()

    if "product_id" in events.columns:
        product_events = events.dropna(subset=["product_id"]).copy()
    else:
        product_events = events.iloc[0:0].copy()

    pages = []

    if not page_events.empty:
        for page_id, group in page_events.groupby("page_id"):
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
        for product_id, group in product_events.groupby("product_id"):
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
# 3. Time-based trends
# --------------------------------------------------

@router.get("/api/trends")
def get_time_trends(
    interval: str = Query(
        default="day",
        pattern="^(day|week|month)$",
    ),
):
    sessions = read_csv_file(SESSIONS_FILE)
    outcomes = read_csv_file(OUTCOMES_FILE)

    require_columns(
        sessions,
        {"session_id", "started_at"},
        SESSIONS_FILE.name,
    )
    require_columns(
        outcomes,
        {"session_id", "outcome"},
        OUTCOMES_FILE.name,
    )

    sessions = sessions.drop_duplicates(subset=["session_id"]).copy()
    outcomes = outcomes.drop_duplicates(subset=["session_id"])

    sessions["started_at"] = pd.to_datetime(
        sessions["started_at"],
        errors="coerce",
        utc=True,
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
# 4. Session explorer
# --------------------------------------------------

@router.get("/api/sessions")
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
    require_columns(
        outcomes,
        {"session_id", "outcome"},
        OUTCOMES_FILE.name,
    )

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
            merged["session_id"].astype(str).str.contains(
                q, case=False, na=False
            )
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
    records = records.astype(object).where(pd.notna(records), None)

    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "sessions": records.to_dict(orient="records"),
    }


# --------------------------------------------------
# 5. Events for an individual session
# --------------------------------------------------

@router.get("/api/sessions/{session_id}/events")
def get_session_events(session_id: str):
    sessions = read_csv_file(SESSIONS_FILE)
    events = read_csv_file(EVENTS_FILE)

    require_columns(
        sessions,
        {"session_id"},
        SESSIONS_FILE.name,
    )
    require_columns(
        events,
        {
            "session_id",
            "event_id",
            "event_type",
            "event_timestamp",
        },
        EVENTS_FILE.name,
    )

    matching_session = sessions[
        sessions["session_id"].astype(str) == session_id
    ]

    if matching_session.empty:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    matching_events = events[
        events["session_id"].astype(str) == session_id
    ].copy()

    matching_events["event_timestamp"] = pd.to_datetime(
        matching_events["event_timestamp"],
        errors="coerce",
        utc=True,
    )

    matching_events = matching_events.sort_values(
        "event_timestamp",
        na_position="last",
    )

    matching_events["event_timestamp"] = (
        matching_events["event_timestamp"].astype(str)
    )

    matching_events = matching_events.astype(object).where(
        pd.notna(matching_events),
        None,
    )

    return {
        "session_id": session_id,
        "event_count": int(len(matching_events)),
        "events": matching_events.to_dict(orient="records"),
    }
