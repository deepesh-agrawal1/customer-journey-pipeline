import random
from pathlib import Path

import pandas as pd


def inject_anomalies(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Inject deterministic anomalies into copies of sessions and events.

    Returns:
        modified_events: event data with injected anomalies
        ground_truth: one record per injected anomaly
    """
    rng = random.Random(seed)

    modified_events = events.copy(deep=True)
    modified_sessions = sessions.copy(deep=True)

    if modified_events.empty or modified_sessions.empty:
        raise ValueError("Sessions and events must not be empty.")

    required_event_columns = {
        "event_id",
        "session_id",
        "customer_id",
        "event_type",
        "event_timestamp",
        "event_sequence",
        "source",
    }
    missing = required_event_columns - set(modified_events.columns)
    if missing:
        raise ValueError(
            f"Events are missing required columns: {sorted(missing)}"
        )

    required_session_columns = {
        "session_id",
        "customer_id",
        "started_at",
        "ended_at",
    }
    missing = required_session_columns - set(modified_sessions.columns)
    if missing:
        raise ValueError(
            f"Sessions are missing required columns: {sorted(missing)}"
        )

    modified_events["event_timestamp"] = pd.to_datetime(
        modified_events["event_timestamp"], utc=True
    )
    modified_events["ingestion_timestamp"] = (
        modified_events["event_timestamp"]
    )

    ground_truth = []

    def record(
        anomaly_type: str,
        entity_type: str,
        entity_id: str,
        session_id: str,
        description: str,
    ) -> None:
        ground_truth.append({
            "anomaly_id": f"ANM-{len(ground_truth) + 1:06d}",
            "anomaly_type": anomaly_type,
            "severity": (
                "high"
                if anomaly_type == "event_outside_session"
                else "medium"
            ),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "session_id": session_id,
            "description": description,
            "ground_truth_label": 1,
        })

    # 1. Duplicate one event with a unique ID.
    source_event = modified_events.iloc[
        rng.randrange(len(modified_events))
    ].copy()

    duplicate = source_event.copy()
    duplicate["event_id"] = "EVT-ANOM-DUP-000001"
    duplicate["event_sequence"] = int(
        pd.to_numeric(modified_events["event_sequence"]).max()
    ) + 1
    modified_events = pd.concat(
        [modified_events, duplicate.to_frame().T],
        ignore_index=True,
    )

    record(
        "duplicate_event",
        "event",
        str(duplicate["event_id"]),
        str(duplicate["session_id"]),
        "Injected duplicate of an existing event.",
    )

    # 2. Move one event beyond its session end.
    sessions_indexed = modified_sessions.set_index("session_id")
    eligible = modified_events[
        modified_events["session_id"].isin(sessions_indexed.index)
    ]

    outside_source = eligible.iloc[
        rng.randrange(len(eligible))
    ].copy()

    outside_id = "EVT-ANOM-OUT-000001"
    outside = outside_source.copy()
    outside["event_id"] = outside_id
    outside["event_timestamp"] = (
        pd.to_datetime(
            sessions_indexed.loc[
                outside["session_id"], "ended_at"
            ],
            utc=True,
        )
        + pd.Timedelta(minutes=10)
    )
    outside["ingestion_timestamp"] = (
        outside["event_timestamp"] + pd.Timedelta(minutes=1)
    )
    outside["event_sequence"] = int(
        pd.to_numeric(modified_events["event_sequence"]).max()
    ) + 2

    modified_events = pd.concat(
        [modified_events, outside.to_frame().T],
        ignore_index=True,
    )

    record(
        "event_outside_session",
        "event",
        outside_id,
        str(outside["session_id"]),
        "Injected event ten minutes after its session ended.",
    )

    # 3. Simulate delayed ingestion for a separate event.
    delay_candidates = modified_events[
        ~modified_events["event_id"].isin(
            ["EVT-ANOM-DUP-000001", outside_id]
        )
    ]

    delay_source = delay_candidates.iloc[
        rng.randrange(len(delay_candidates))
    ].copy()

    delay_id = "EVT-ANOM-DELAY-000001"
    delayed = delay_source.copy()
    delayed["event_id"] = delay_id
    delayed["ingestion_timestamp"] = (
        pd.to_datetime(delayed["event_timestamp"], utc=True)
        + pd.Timedelta(hours=2)
    )
    delayed["event_sequence"] = int(
        pd.to_numeric(modified_events["event_sequence"]).max()
    ) + 3

    modified_events = pd.concat(
        [modified_events, delayed.to_frame().T],
        ignore_index=True,
    )

    record(
        "delayed_ingestion",
        "event",
        delay_id,
        str(delayed["session_id"]),
        "Injected event ingested two hours after it occurred.",
    )

    # 4. Create a checkout-only session with no purchase.
    checkout_session_id = "SES-ANOM-000001"
    checkout_customer_id = str(
        modified_sessions.iloc[0]["customer_id"]
    )

    checkout_session = {
        "session_id": checkout_session_id,
        "customer_id": checkout_customer_id,
        "started_at": "2026-01-01T10:00:00+00:00",
        "ended_at": "2026-01-01T10:30:00+00:00",
    }

    for column in modified_sessions.columns:
        if column not in checkout_session:
            checkout_session[column] = pd.NA

    modified_sessions = pd.concat(
        [
            modified_sessions,
            pd.DataFrame([checkout_session]),
        ],
        ignore_index=True,
    )

    checkout_event = {
        "event_id": "EVT-ANOM-CHECKOUT-000001",
        "session_id": checkout_session_id,
        "customer_id": checkout_customer_id,
        "event_type": "page_view",
        "event_timestamp": pd.Timestamp(
            "2026-01-01T10:10:00+00:00"
        ),
        "event_sequence": 1,
        "source": "synthetic_anomaly",
        "page_id": "PAG-000005",
        "product_id": pd.NA,
        "ingestion_timestamp": pd.Timestamp(
            "2026-01-01T10:11:00+00:00"
        ),
    }

    for column in modified_events.columns:
        if column not in checkout_event:
            checkout_event[column] = pd.NA

    modified_events = pd.concat(
        [
            modified_events,
            pd.DataFrame([checkout_event]),
        ],
        ignore_index=True,
    )

    record(
        "checkout_abandonment",
        "session",
        checkout_session_id,
        checkout_session_id,
        "Injected checkout session with no subsequent purchase.",
    )

    return (
        modified_sessions,
        modified_events,
        pd.DataFrame(ground_truth),
    )

def save_anomaly_data(
    project_root: Path,
    sessions: pd.DataFrame,
    events: pd.DataFrame,
    seed: int = 42,
) -> dict[str, str]:
    """Inject anomalies and save all outputs separately."""
    anomaly_dir = project_root / "data" / "anomalies"
    anomaly_dir.mkdir(parents=True, exist_ok=True)

    modified_sessions, modified_events, ground_truth = inject_anomalies(
        sessions,
        events,
        seed=seed,
    )

    sessions_path = anomaly_dir / "sessions_with_anomalies.csv"
    events_path = anomaly_dir / "events_with_anomalies.csv"
    truth_path = anomaly_dir / "ground_truth_anomalies.csv"

    modified_sessions.to_csv(sessions_path, index=False)
    modified_events.to_csv(events_path, index=False)
    ground_truth.to_csv(truth_path, index=False)

    return {
        "sessions": str(sessions_path),
        "events": str(events_path),
        "ground_truth": str(truth_path),
    }