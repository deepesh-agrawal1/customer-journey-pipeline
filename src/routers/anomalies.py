
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api_helpers import PROJECT_ROOT
from src.pipeline import run_anomaly_analysis

router = APIRouter(tags=["Anomaly Detection"])

ANOMALY_DIR = Path(PROJECT_ROOT) / "data" / "anomalies"
DETECTED_FILE = ANOMALY_DIR / "detected_anomalies.csv"
EVALUATION_FILE = ANOMALY_DIR / "anomaly_evaluation.csv"
METRICS_FILE = ANOMALY_DIR / "anomaly_metrics.csv"


def read_anomaly_file(path: Path) -> pd.DataFrame:
    """Read an anomaly output file, returning an empty DataFrame if absent."""
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def records_from_dataframe(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to JSON-friendly records."""
    if df.empty:
        return []

    clean_df = df.astype(object).where(pd.notna(df), None)
    return clean_df.to_dict(orient="records")


# --------------------------------------------------
# 1. List and filter detected anomalies
# --------------------------------------------------

@router.get("/api/anomalies")
def get_anomalies(
    severity: str | None = Query(default=None, max_length=30),
    anomaly_type: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    anomalies = read_anomaly_file(DETECTED_FILE)

    if anomalies.empty:
        return {
            "total": 0,
            "limit": limit,
            "offset": offset,
            "anomalies": [],
        }

    for column, value in [
        ("severity", severity),
        ("anomaly_type", anomaly_type),
        ("status", status),
    ]:
        if value and column in anomalies.columns:
            anomalies = anomalies[
                anomalies[column].astype(str).str.lower() == value.lower()
            ]

    total = len(anomalies)
    selected = anomalies.iloc[offset:offset + limit]

    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "anomalies": records_from_dataframe(selected),
    }


# --------------------------------------------------
# 2. Read evaluation metrics and results
# --------------------------------------------------

@router.get("/api/anomalies/metrics")
def get_anomaly_metrics():
    metrics = read_anomaly_file(METRICS_FILE)
    evaluation = read_anomaly_file(EVALUATION_FILE)

    return {
        "metrics": records_from_dataframe(metrics),
        "evaluation": records_from_dataframe(evaluation),
    }


# --------------------------------------------------
# 3. Run the existing anomaly analysis pipeline
# --------------------------------------------------

@router.post("/api/anomalies/run")
def run_anomalies():
    try:
        result = run_anomaly_analysis(PROJECT_ROOT)

        return {
            "status": "completed",
            "results": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly analysis failed: {str(exc)}",
        ) from exc
