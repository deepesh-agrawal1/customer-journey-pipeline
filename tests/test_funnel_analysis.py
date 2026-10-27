
import pandas as pd

from src.funnel_analysis import calculate_funnel


def test_funnel_counts_and_rates():
    sessions = pd.DataFrame({
        "session_id": ["S1", "S2", "S3", "S4"]
    })

    events = pd.DataFrame([
        {"session_id": "S1", "event_type": "page_view"},
        {"session_id": "S1", "event_type": "item_viewed"},
        {"session_id": "S1", "event_type": "add_to_cart"},
        {"session_id": "S1", "event_type": "purchase"},
        {"session_id": "S2", "event_type": "page_view"},
        {"session_id": "S2", "event_type": "item_viewed"},
        {"session_id": "S3", "event_type": "page_view"},
        {"session_id": "S4", "event_type": "support_contact"},
    ])

    result = calculate_funnel(sessions, events)

    assert result["sessions_reached"].tolist() == [3, 2, 1, 1]
    assert result.iloc[0]["session_reach_rate"] == 0.75
    assert result.iloc[1]["stage_to_stage_rate"] == 2 / 3
    assert result.iloc[2]["stage_to_stage_rate"] == 0.5
    assert result.iloc[3]["stage_to_stage_rate"] == 1.0
