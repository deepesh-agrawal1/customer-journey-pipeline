
import pandas as pd

from src.standardizer import (
    standardize_events,
    standardize_sessions,
)


def test_event_names_are_standardized():
    events = pd.DataFrame([
        {
            "event_type": "Page View",
            "event_timestamp": "2026-01-01T10:00:00+00:00",
            "event_sequence": 1,
            "source": " Synthetic_Web ",
        },
        {
            "event_type": "add-to-cart",
            "event_timestamp": "2026-01-01T10:05:00+00:00",
            "event_sequence": 2,
            "source": "SYNTHETIC_WEB",
        },
    ])

    result = standardize_events(events)

    assert result["event_type"].tolist() == [
        "page_view",
        "add_to_cart",
    ]
    assert result["source"].tolist() == [
        "synthetic_web",
        "synthetic_web",
    ]


def test_event_timestamps_are_utc():
    events = pd.DataFrame([
        {
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T15:30:00+05:30",
            "event_sequence": 1,
            "source": "synthetic_web",
        }
    ])

    result = standardize_events(events)

    timestamp = result.loc[0, "event_timestamp"]

    assert str(timestamp.tz) == "UTC"
    assert timestamp == pd.Timestamp("2026-01-01T10:00:00Z")


def test_session_timestamps_are_utc():
    sessions = pd.DataFrame([
        {
            "started_at": "2026-01-01T15:30:00+05:30",
            "ended_at": "2026-01-01T16:00:00+05:30",
            "duration_minutes": "30",
            "device": " Mobile ",
            "country": "india",
        }
    ])

    result = standardize_sessions(sessions)

    assert str(result.loc[0, "started_at"].tz) == "UTC"
    assert result.loc[0, "started_at"] == pd.Timestamp(
        "2026-01-01T10:00:00Z"
    )
    assert result.loc[0, "duration_minutes"] == 30
    assert result.loc[0, "device"] == "mobile"
    assert result.loc[0, "country"] == "India"
