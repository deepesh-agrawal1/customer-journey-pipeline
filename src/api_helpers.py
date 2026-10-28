from pathlib import Path

import pandas as pd
from fastapi import HTTPException


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


def read_csv_file(path: Path) -> pd.DataFrame:
    """Read a project CSV or return a useful API error."""
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Required data file not found: {path.name}. "
                "Run the pipeline first."
            ),
        )

    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=500,
            detail=f"Data file is empty or invalid: {path.name}.",
        )
    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.ParserError,
    ) as exc:
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
            detail=(
                f"{filename} is missing required columns: "
                f"{sorted(missing)}"
            ),
        )


def outcome_summary(df: pd.DataFrame) -> dict:
    """Summarize the outcome labels actually present in the data."""
    require_columns(
        df,
        {"session_id", "outcome"},
        OUTCOMES_FILE.name,
    )

    unique = df.drop_duplicates(subset=["session_id"])
    counts = (
        unique["outcome"]
        .fillna("unknown")
        .value_counts()
        .to_dict()
    )
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
            "percentage": (
                round(count / total * 100, 2) if total else 0
            ),
        })

    # Preserve any additional outcome labels in the dataset.
    for key, value in counts.items():
        if key not in labels:
            count = int(value)
            outcomes.append({
                "outcome": str(key),
                "label": str(key).replace("_", " ").title(),
                "count": count,
                "percentage": (
                    round(count / total * 100, 2) if total else 0
                ),
            })

    return {
        "total_sessions": int(total),
        "outcomes": outcomes,
    }


def optional_lookup(
    path: Path,
    id_column: str,
    label_candidates: list[str],
) -> dict:
    """Build an ID-to-label map when a matching lookup column exists."""
    if not path.exists():
        return {}

    try:
        df = pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        OSError,
        pd.errors.ParserError,
    ):
        return {}

    if id_column not in df.columns:
        return {}

    label_column = next(
        (
            column
            for column in label_candidates
            if column in df.columns
        ),
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
