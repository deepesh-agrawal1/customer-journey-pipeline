
import pandas as pd

from src.analytics import derive_journey_outcomes


def test_purchase_takes_precedence_over_support_and_abandonment():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
        }
    ])

    events = pd.DataFrame([
        {"session_id": "SES-2026-000001", "event_type": "add_to_cart"},
        {"session_id": "SES-2026-000001", "event_type": "support_contact"},
        {"session_id": "SES-2026-000001", "event_type": "purchase"},
    ])

    result = derive_journey_outcomes(sessions, events)

    assert len(result) == 1
    assert result.iloc[0]["outcome"] == "converted"


def test_support_takes_precedence_over_cart_abandonment():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000002",
            "customer_id": "CUS-000002",
        }
    ])

    events = pd.DataFrame([
        {"session_id": "SES-2026-000002", "event_type": "add_to_cart"},
        {"session_id": "SES-2026-000002", "event_type": "support_contact"},
    ])

    result = derive_journey_outcomes(sessions, events)

    assert result.iloc[0]["outcome"] == "support_required"


def test_browsing_without_purchase_is_no_conversion():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000003",
            "customer_id": "CUS-000003",
        }
    ])

    events = pd.DataFrame([
        {"session_id": "SES-2026-000003", "event_type": "page_view"},
        {"session_id": "SES-2026-000003", "event_type": "item_viewed"},
    ])

    result = derive_journey_outcomes(sessions, events)

    assert result.iloc[0]["outcome"] == "no_conversion"


def test_session_without_events_still_gets_outcome():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000004",
            "customer_id": "CUS-000004",
        }
    ])

    events = pd.DataFrame(
        columns=["session_id", "event_type"]
    )

    result = derive_journey_outcomes(sessions, events)

    assert len(result) == 1
    assert result.iloc[0]["outcome"] == "no_conversion"
def test_purchase_before_product_interest_is_not_a_conversion():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000005",
            "customer_id": "CUS-000005",
        }
    ])

    events = pd.DataFrame([
        {
            "session_id": "SES-2026-000005",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:00:00Z",
        },
        {
            "session_id": "SES-2026-000005",
            "event_type": "purchase",
            "event_timestamp": "2026-01-01T10:01:00Z",
        },
        {
            "session_id": "SES-2026-000005",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T10:02:00Z",
        },
    ])

    result = derive_journey_outcomes(sessions, events)

    assert result.iloc[0]["outcome"] == "no_conversion"
    assert result.iloc[0]["reason"] == "no_purchase_event_detected"
