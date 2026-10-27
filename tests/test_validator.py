
import pandas as pd

from src.validator import validate_events


def test_event_with_wrong_customer_is_quarantined():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
        }
    ])

    customers = pd.DataFrame([
        {"customer_id": "CUS-000001"},
        {"customer_id": "CUS-000002"},
    ])

    events = pd.DataFrame([
        {
            "event_id": "EVT-001",
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000002",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:10:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
        }
    ])

    valid, invalid = validate_events(events, sessions, customers)

    assert len(valid) == 0
    assert len(invalid) == 1
    assert invalid.iloc[0]["event_id"] == "EVT-001"


def test_event_outside_session_is_quarantined():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
        }
    ])

    customers = pd.DataFrame([
        {"customer_id": "CUS-000001"},
    ])

    events = pd.DataFrame([
        {
            "event_id": "EVT-002",
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T11:00:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
        }
    ])

    valid, invalid = validate_events(events, sessions, customers)

    assert len(valid) == 0
    assert len(invalid) == 1
    assert invalid.iloc[0]["event_id"] == "EVT-002"
