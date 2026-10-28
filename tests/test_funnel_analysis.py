
import pandas as pd

from src.funnel_analysis import calculate_funnel


def test_funnel_counts_and_rates():
    sessions = pd.DataFrame({
        "session_id": ["S1", "S2", "S3", "S4"]
    })

    events = pd.DataFrame([
        # S1 completes all funnel stages.
        {
            "session_id": "S1",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:00:00Z",
        },
        {
            "session_id": "S1",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T10:01:00Z",
        },
        {
            "session_id": "S1",
            "event_type": "purchase",
            "event_timestamp": "2026-01-01T10:02:00Z",
        },

        # S2 reaches product interest but does not purchase.
        {
            "session_id": "S2",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T11:00:00Z",
        },
        {
            "session_id": "S2",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T11:01:00Z",
        },

        # S3 only browses.
        {
            "session_id": "S3",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T12:00:00Z",
        },

        # S4 has support activity but no funnel progression.
        {
            "session_id": "S4",
            "event_type": "support_contact",
            "event_timestamp": "2026-01-01T13:00:00Z",
        },
    ])

    result = calculate_funnel(sessions, events)

    assert result["sessions_reached"].tolist() == [3, 2, 1]
    assert result["session_reach_rate"].tolist() == [
        0.75, 0.5, 0.25
    ]
    assert result.iloc[1]["stage_to_stage_rate"] == 2 / 3
    assert result.iloc[2]["stage_to_stage_rate"] == 1 / 2


def test_funnel_rejects_stages_in_wrong_order():
    sessions = pd.DataFrame({
        "session_id": ["S1", "S2"]
    })

    events = pd.DataFrame([
        # S1: purchase occurs before product interest.
        {
            "session_id": "S1",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:00:00Z",
        },
        {
            "session_id": "S1",
            "event_type": "purchase",
            "event_timestamp": "2026-01-01T10:01:00Z",
        },
        {
            "session_id": "S1",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T10:02:00Z",
        },

        # S2: all stages occur in the correct order.
        {
            "session_id": "S2",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T11:00:00Z",
        },
        {
            "session_id": "S2",
            "event_type": "item_viewed",
            "event_timestamp": "2026-01-01T11:01:00Z",
        },
        {
            "session_id": "S2",
            "event_type": "purchase",
            "event_timestamp": "2026-01-01T11:02:00Z",
        },
    ])

    result = calculate_funnel(sessions, events)

    assert result["sessions_reached"].tolist() == [2, 1, 1]
