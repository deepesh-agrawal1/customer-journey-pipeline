
import json
from unittest.mock import MagicMock, patch

import pandas as pd

from src import ai_insights


def sample_metrics():
    return {
        "total_sessions": 100,
        "total_events": 300,
        "converted_sessions": 20,
        "conversion_rate": 0.2,
        "support_sessions": 10,
        "support_contact_rate": 0.1,
        "abandoned_sessions": 30,
        "abandonment_rate": 0.3,
        "funnel": [
            {
                "stage": "Browse",
                "event": "page_view",
                "event_count": 100,
                "sessions": 100,
            },
            {
                "stage": "Product interest",
                "event": "item_viewed",
                "event_count": 60,
                "sessions": 60,
            },
            {
                "stage": "Cart intent",
                "event": "add_to_cart",
                "event_count": 40,
                "sessions": 40,
            },
            {
                "stage": "Purchase",
                "event": "purchase",
                "event_count": 20,
                "sessions": 20,
            },
        ],
    }


def test_calculate_journey_metrics(monkeypatch):
    sessions = pd.DataFrame({
        "session_id": ["S1", "S2", "S3"],
        "device": ["mobile", "desktop", "mobile"],
    })
    outcomes = pd.DataFrame({
        "session_id": ["S1", "S2", "S3"],
        "outcome": ["converted", "abandoned", "converted"],
    })
    events = pd.DataFrame({
        "session_id": ["S1", "S1", "S2", "S3"],
        "event_type": [
            "page_view",
            "purchase",
            "page_view",
            "purchase",
        ],
    })

    def fake_read_csv(path):
        if path == ai_insights.SESSIONS_FILE:
            return sessions.copy()
        if path == ai_insights.OUTCOMES_FILE:
            return outcomes.copy()
        if path == ai_insights.EVENTS_FILE:
            return events.copy()
        return pd.DataFrame()

    monkeypatch.setattr(ai_insights, "_read_csv", fake_read_csv)

    result = ai_insights.calculate_journey_metrics()

    assert result["total_sessions"] == 3
    assert result["converted_sessions"] == 2
    assert result["conversion_rate"] == round(2 / 3, 4)
    assert result["total_events"] == 4
    assert len(result["funnel"]) == 4
    assert len(result["device_performance"]) == 2


def test_fallback_insights_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        ai_insights,
        "calculate_journey_metrics",
        sample_metrics,
    )

    result = ai_insights.generate_ai_insights()

    assert result["provider"] == "rules_based_fallback"
    assert result["metrics"]["total_sessions"] == 100
    assert len(result["insights"]) > 0


def test_gemini_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        ai_insights,
        "calculate_journey_metrics",
        sample_metrics,
    )

    expected = {
        "insights": [
            {
                "title": "Checkout drop-off",
                "finding": "Fewer sessions reach purchase than browse.",
                "evidence": {"browse_sessions": 100, "purchase_sessions": 20},
                "recommendation": "Investigate checkout steps.",
                "priority": "high",
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(expected)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        result = ai_insights.generate_ai_insights()

    assert result["provider"] == "gemini"
    assert result["insights"][0]["title"] == "Checkout drop-off"
    mock_client.models.generate_content.assert_called_once()


def test_gemini_failure_uses_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        ai_insights,
        "calculate_journey_metrics",
        sample_metrics,
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = RuntimeError(
        "Gemini unavailable"
    )

    with patch("google.genai.Client", return_value=mock_client):
        result = ai_insights.generate_ai_insights()

    assert result["provider"] == "rules_based_fallback"
    assert len(result["insights"]) > 0


def test_invalid_gemini_response_uses_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        ai_insights,
        "calculate_journey_metrics",
        sample_metrics,
    )

    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", return_value=mock_client):
        result = ai_insights.generate_ai_insights()

    assert result["provider"] == "rules_based_fallback"
