
from asyncio import events
from pathlib import Path
from src.funnel_analysis import calculate_funnel
from src.standardizer import (
    standardize_customers,
    standardize_sessions,
    standardize_events,
)
import pandas as pd
from src.analytics import derive_journey_outcomes
from src.metrics import calculate_journey_metrics
from src.validator import (
    validate_customers,
    validate_sessions,
    validate_events,
    validate_pages,
    validate_products,
)


def run_validation(project_root: Path) -> dict:
    raw_dir = project_root / "data" / "raw"
    staged_dir = project_root / "data" / "staged"
    quarantine_dir = project_root / "data" / "quarantine"

    staged_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    customers_raw = pd.read_csv(raw_dir / "customers.csv")
    sessions_raw = pd.read_csv(raw_dir / "sessions.csv")
    events_raw = pd.read_csv(raw_dir / "journey_events.csv")
    pages_raw = pd.read_csv(raw_dir / "pages.csv")
    products_raw = pd.read_csv(raw_dir / "products.csv")

    customers_valid, customers_bad = validate_customers(customers_raw)

    sessions_valid, sessions_bad = validate_sessions(
        sessions_raw,
        customers_valid,
    )

    events_valid, events_bad = validate_events(
        events_raw,
        sessions_valid,
        customers_valid,
        pages_raw,
        products_raw,
    )
    customers_valid = standardize_customers(customers_valid)
    sessions_valid = standardize_sessions(sessions_valid)
    events_valid = standardize_events(events_valid)
    pages_valid, pages_bad = validate_pages(pages_raw)
    products_valid, products_bad = validate_products(products_raw)

        # Derive one journey outcome per valid session.
    outcomes = derive_journey_outcomes(
        sessions_valid,
        events_valid,
    )

    # Save the curated analytical dataset.
    curated_dir = project_root / "data" / "curated"
    curated_dir.mkdir(parents=True, exist_ok=True)

    outcomes.to_csv(
        curated_dir / "journey_outcomes.csv",
        index=False,
    )
    
    # Calculate funnel analysis from validated, standardized data.
    funnel = calculate_funnel(
        sessions_valid,
        events_valid,
    )

    funnel.to_csv(
        curated_dir / "journey_funnel.csv",
        index=False,
    )

    
    # Calculate business metrics from the curated outcomes.
    metrics = calculate_journey_metrics(outcomes)

    metrics.to_csv(
        curated_dir / "journey_metrics.csv",
        index=False,
    )


    customers_valid.to_csv(staged_dir / "customers.csv", index=False)
    sessions_valid.to_csv(staged_dir / "sessions.csv", index=False)
    events_valid.to_csv(staged_dir / "journey_events.csv", index=False)

    customers_bad.to_csv(quarantine_dir / "customers_invalid.csv", index=False)
    sessions_bad.to_csv(quarantine_dir / "sessions_invalid.csv", index=False)
    events_bad.to_csv(quarantine_dir / "journey_events_invalid.csv", index=False)

    pages_valid.to_csv(staged_dir / "pages.csv", index=False)
    products_valid.to_csv(staged_dir / "products.csv", index=False)

    pages_bad.to_csv(quarantine_dir / "pages_invalid.csv", index=False)
    products_bad.to_csv(quarantine_dir / "products_invalid.csv", index=False)

    return {
        "customers": (len(customers_raw), len(customers_valid), len(customers_bad)),
        "sessions": (len(sessions_raw), len(sessions_valid), len(sessions_bad)),
        "events": (len(events_raw), len(events_valid), len(events_bad)),
        "outcomes": (len(outcomes), len(outcomes), 0),
        "pages": (len(pages_raw), len(pages_valid), len(pages_bad)),
        "products": (len(products_raw), len(products_valid), len(products_bad)),
    }
