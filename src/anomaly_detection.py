from pathlib import Path

import pandas as pd


ANOMALY_COLUMNS = [
    "anomaly_id",
    "anomaly_type",
    "severity",
    "entity_type",
    "entity_id",
    "session_id",
    "description",
    "detected_at",
    "ground_truth_label",
    "detection_method",
    "status",
]


def detect_anomalies(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
    detected_at: str | None = None,
    delayed_ingestion_threshold_minutes: int = 60,
) -> pd.DataFrame:
    """
    Detect event and journey anomalies without modifying input data.

    Expected optional event column for delayed-ingestion detection:
    ingestion_timestamp.
    """
    anomalies = []
    detection_time = (
        pd.Timestamp(detected_at)
        if detected_at
        else pd.Timestamp.now(tz="UTC")
    )

    def add_anomaly(
        anomaly_type: str,
        severity: str,
        entity_type: str,
        entity_id: str,
        session_id: str,
        description: str,
        detection_method: str,
    ) -> None:
        anomalies.append({
            "anomaly_id": f"ANM-{len(anomalies) + 1:06d}",
            "anomaly_type": anomaly_type,
            "severity": severity,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "session_id": session_id,
            "description": description,
            "detected_at": detection_time.isoformat(),
            "ground_truth_label": 0,
            "detection_method": detection_method,
            "status": "detected",
        })

    # 1. Duplicate events: same session, event type and timestamp.
    duplicate_mask = events.duplicated(
        subset=["session_id", "event_type", "event_timestamp"],
        keep=False,
    )

    for _, event in events.loc[duplicate_mask].iterrows():
        add_anomaly(
            "duplicate_event",
            "medium",
            "event",
            str(event["event_id"]),
            str(event["session_id"]),
            "Multiple events share the same session, type and timestamp.",
            "duplicate_event_rule",
        )

    # 2. Events outside their session's start/end boundaries.
    session_times = sessions.set_index("session_id")[
        ["started_at", "ended_at"]
    ]

    event_times = events.copy()
    event_times["event_timestamp"] = pd.to_datetime(
        event_times["event_timestamp"], utc=True, errors="coerce"
    )

    for _, event in event_times.iterrows():
        session_id = event["session_id"]

        if session_id not in session_times.index:
            continue

        session = session_times.loc[session_id]
        start = pd.to_datetime(session["started_at"], utc=True, errors="coerce")
        end = pd.to_datetime(session["ended_at"], utc=True, errors="coerce")
        timestamp = event["event_timestamp"]

        if pd.isna(start) or pd.isna(end) or pd.isna(timestamp):
            continue

        if timestamp < start or timestamp > end:
            add_anomaly(
                "event_outside_session",
                "high",
                "event",
                str(event["event_id"]),
                str(session_id),
                "Event timestamp falls outside the session boundaries.",
                "session_boundary_rule",
            )

    # 3. Delayed ingestion, only when ingestion_timestamp exists.
    if "ingestion_timestamp" in events.columns:
        ingestion = events.copy()
        ingestion["event_timestamp"] = pd.to_datetime(
            ingestion["event_timestamp"], utc=True, errors="coerce"
        )
        ingestion["ingestion_timestamp"] = pd.to_datetime(
            ingestion["ingestion_timestamp"], utc=True, errors="coerce"
        )

        delay = (
            ingestion["ingestion_timestamp"] - ingestion["event_timestamp"]
        ).dt.total_seconds() / 60

        delayed = ingestion.loc[
            delay > delayed_ingestion_threshold_minutes
        ]

        for _, event in delayed.iterrows():
            add_anomaly(
                "delayed_ingestion",
                "medium",
                "event",
                str(event["event_id"]),
                str(event["session_id"]),
                "Event ingestion exceeded the configured delay threshold.",
                "ingestion_delay_rule",
            )

    # 4. Checkout abandonment: checkout exists, purchase does not follow it.
    for session_id, group in event_times.groupby("session_id"):
        group = group.sort_values("event_timestamp")
        event_types = group["event_type"].astype(str).str.lower()

        checkout_rows = group.loc[
            event_types.isin(["checkout", "begin_checkout", "checkout_started"])
    |       group["page_id"].eq("PAG-000005")
            ]
        purchase_rows = group.loc[event_types.eq("purchase")]

        if checkout_rows.empty:
            continue

        last_checkout_time = checkout_rows["event_timestamp"].max()
        purchase_after_checkout = (
            not purchase_rows.empty
            and (purchase_rows["event_timestamp"] > last_checkout_time).any()
        )

        if not purchase_after_checkout:
            add_anomaly(
                "checkout_abandonment",
                "medium",
                "session",
                str(session_id),
                str(session_id),
                "Session reached checkout but had no subsequent purchase event.",
                "checkout_completion_rule",
            )

    return pd.DataFrame(anomalies, columns=ANOMALY_COLUMNS)