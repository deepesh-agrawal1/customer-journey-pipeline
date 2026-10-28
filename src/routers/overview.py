
from fastapi import APIRouter, HTTPException

from src.api_helpers import (
    METRICS_FILE,
    FUNNEL_FILE,
    STAGED_DIR,
    OUTCOMES_FILE,
    QUARANTINE_DIR,
    read_csv_file,
    outcome_summary,
)

router = APIRouter(tags=["Overview"])


@router.get("/api/metrics")
def get_metrics():
    df = read_csv_file(METRICS_FILE)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="Metrics file contains no data.",
        )

    return df.iloc[0].to_dict()


@router.get("/api/funnel")
def get_funnel():
    df = read_csv_file(FUNNEL_FILE)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="Funnel file contains no data.",
        )

    return df.to_dict(orient="records")


@router.get("/api/quality")
def get_quality():
    datasets = {
        "customers": ("customers.csv", "customers_invalid.csv"),
        "sessions": ("sessions.csv", "sessions_invalid.csv"),
        "events": (
            "journey_events.csv",
            "journey_events_invalid.csv",
        ),
        "pages": ("pages.csv", "pages_invalid.csv"),
        "products": ("products.csv", "products_invalid.csv"),
    }

    results = []
    total_records = 0
    total_valid = 0
    total_quarantined = 0

    for name, (valid_file, invalid_file) in datasets.items():
        valid_df = read_csv_file(STAGED_DIR / valid_file)
        invalid_df = read_csv_file(QUARANTINE_DIR / invalid_file)

        valid_count = len(valid_df)
        invalid_count = len(invalid_df)
        total = valid_count + invalid_count

        results.append({
            "dataset": name,
            "total_records": total,
            "valid_records": valid_count,
            "quarantined_records": invalid_count,
            "quality_rate": (
                round(valid_count / total, 4) if total else 1.0
            ),
        })

        total_records += total
        total_valid += valid_count
        total_quarantined += invalid_count

    return {
        "total_records": total_records,
        "valid_records": total_valid,
        "quarantined_records": total_quarantined,
        "quality_rate": (
            round(total_valid / total_records, 4)
            if total_records else 1.0
        ),
        "datasets": results,
    }


@router.get("/api/outcomes")
def get_outcomes():
    outcomes = read_csv_file(OUTCOMES_FILE)
    return outcome_summary(outcomes)
