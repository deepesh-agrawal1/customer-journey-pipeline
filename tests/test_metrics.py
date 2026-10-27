
import pandas as pd

from src.metrics import calculate_journey_metrics


def test_journey_metrics():
    outcomes = pd.DataFrame([
        {"session_id": "S1", "outcome": "converted"},
        {"session_id": "S2", "outcome": "converted"},
        {"session_id": "S3", "outcome": "support_required"},
        {"session_id": "S4", "outcome": "abandoned"},
        {"session_id": "S5", "outcome": "no_conversion"},
    ])

    result = calculate_journey_metrics(outcomes).iloc[0]

    assert result["total_sessions"] == 5
    assert result["converted_sessions"] == 2
    assert result["conversion_rate"] == 0.4
    assert result["support_contact_rate"] == 0.2
    assert result["cart_abandonment_rate"] == 0.2
    assert result["no_conversion_rate"] == 0.2
