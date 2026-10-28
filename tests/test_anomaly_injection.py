import pandas as pd

from src.anomaly_injection import inject_anomalies


def make_sessions():
    return pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
            "device": "desktop",
            "country": "India",
            "duration_minutes": 30,
        },
        {
            "session_id": "SES-2026-000002",
            "customer_id": "CUS-000002",
            "started_at": "2026-01-01T11:00:00+00:00",
            "ended_at": "2026-01-01T11:30:00+00:00",
            "device": "mobile",
            "country": "India",
            "duration_minutes": 30,
        },
    ])


def make_events():
    return pd.DataFrame([
        {
            "event_id": "EVT-001",
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:05:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
            "page_id": "PAG-000001",
            "product_id": None,
        },
        {
            "event_id": "EVT-002",
            "session_id": "SES-2026-000002",
            "customer_id": "CUS-000002",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T11:10:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
            "page_id": "PAG-000003",
            "product_id": "PRD-000001",
        },
    ])


def test_injects_all_four_anomaly_types():
    sessions, events, truth = inject_anomalies(
        make_sessions(),
        make_events(),
        seed=42,
    )

    assert len(truth) == 4
    assert set(truth["anomaly_type"]) == {
        "duplicate_event",
        "event_outside_session",
        "delayed_ingestion",
        "checkout_abandonment",
    }
    assert "SES-ANOM-000001" in set(sessions["session_id"])
    assert "EVT-ANOM-CHECKOUT-000001" in set(events["event_id"])


def test_injection_is_deterministic():
    sessions_a, events_a, truth_a = inject_anomalies(
        make_sessions(), make_events(), seed=42
    )
    sessions_b, events_b, truth_b = inject_anomalies(
        make_sessions(), make_events(), seed=42
    )

    pd.testing.assert_frame_equal(sessions_a, sessions_b)
    pd.testing.assert_frame_equal(events_a, events_b)
    pd.testing.assert_frame_equal(truth_a, truth_b)


def test_injection_does_not_modify_input_data():
    sessions = make_sessions()
    events = make_events()
    original_sessions = sessions.copy(deep=True)
    original_events = events.copy(deep=True)

    inject_anomalies(sessions, events, seed=42)

    pd.testing.assert_frame_equal(sessions, original_sessions)
    pd.testing.assert_frame_equal(events, original_events)


def test_ground_truth_has_unique_anomaly_ids():
    _, _, truth = inject_anomalies(
        make_sessions(),
        make_events(),
        seed=42,
    )

    assert truth["anomaly_id"].is_unique
    assert truth["anomaly_id"].notna().all()
    assert (truth["ground_truth_label"] == 1).all()
