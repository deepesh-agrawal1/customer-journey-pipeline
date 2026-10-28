import pandas as pd

from src.anomaly_detection import detect_anomalies


def make_sessions():
    return pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
        },
        {
            "session_id": "SES-2026-000002",
            "started_at": "2026-01-01T11:00:00+00:00",
            "ended_at": "2026-01-01T11:30:00+00:00",
        },
    ])


def make_events():
    return pd.DataFrame([
        {
            "event_id": "EVT-001",
            "session_id": "SES-2026-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:05:00+00:00",
            "page_id": "PAG-000001",
        },
        {
            "event_id": "EVT-002",
            "session_id": "SES-2026-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:05:00+00:00",
            "page_id": "PAG-000001",
        },
        {
            "event_id": "EVT-003",
            "session_id": "SES-2026-000001",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T10:40:00+00:00",
            "page_id": "PAG-000003",
        },
        {
            "event_id": "EVT-004",
            "session_id": "SES-2026-000002",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T11:05:00+00:00",
            "page_id": "PAG-000005",
        },
    ])


def test_detects_duplicate_events():
    result = detect_anomalies(
        make_sessions(),
        make_events(),
        detected_at="2026-01-01T12:00:00+00:00",
    )

    duplicates = result[result["anomaly_type"] == "duplicate_event"]

    assert len(duplicates) == 2
    assert set(duplicates["entity_id"]) == {"EVT-001", "EVT-002"}


def test_detects_events_outside_session():
    result = detect_anomalies(
        make_sessions(),
        make_events(),
        detected_at="2026-01-01T12:00:00+00:00",
    )

    outside = result[
        result["anomaly_type"] == "event_outside_session"
    ]

    assert len(outside) == 1
    assert outside.iloc[0]["entity_id"] == "EVT-003"


def test_detects_delayed_ingestion():
    events = make_events()
    events["ingestion_timestamp"] = events["event_timestamp"]
    events.loc[
        events["event_id"] == "EVT-001",
        "ingestion_timestamp",
    ] = "2026-01-01T11:30:00+00:00"

    result = detect_anomalies(
        make_sessions(),
        events,
        detected_at="2026-01-01T12:00:00+00:00",
    )

    delayed = result[result["anomaly_type"] == "delayed_ingestion"]

    assert len(delayed) == 1
    assert delayed.iloc[0]["entity_id"] == "EVT-001"


def test_no_anomalies_for_clean_data():
    sessions = make_sessions().iloc[[0]].copy()

    events = pd.DataFrame([
        {
            "event_id": "EVT-CLEAN-001",
            "session_id": "SES-2026-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:05:00+00:00",
            "page_id": "PAG-000001",
        },
        {
            "event_id": "EVT-CLEAN-002",
            "session_id": "SES-2026-000001",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T10:10:00+00:00",
            "page_id": "PAG-000003",
        },
    ])

    result = detect_anomalies(
        sessions,
        events,
        detected_at="2026-01-01T12:00:00+00:00",
    )

    assert result.empty
