
import pandas as pd


FUNNEL_STAGES = [
    ("browse", "page_view"),
    ("product_interest", "item_viewed"),
    ("purchase", "purchase"),
]


def calculate_funnel(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate funnel progression in the required event order."""

    session_ids = sessions["session_id"].drop_duplicates().tolist()
    total_sessions = len(session_ids)

    ordered_events = events.copy()

    if "event_timestamp" in ordered_events.columns:
        ordered_events["_event_time"] = pd.to_datetime(
            ordered_events["event_timestamp"],
            utc=True,
            errors="coerce",
        )
        ordered_events = ordered_events.sort_values(
            ["session_id", "_event_time"],
            kind="stable",
        )

    progress_by_session = {}

    for session_id in session_ids:
        session_events = ordered_events.loc[
            ordered_events["session_id"] == session_id,
            "event_type",
        ].tolist()

        progress = 0

        for event_type in session_events:
            if progress >= len(FUNNEL_STAGES):
                break

            expected_event = FUNNEL_STAGES[progress][1]

            if event_type == expected_event:
                progress += 1

            elif event_type in {
                event_name
                for _, event_name in FUNNEL_STAGES[progress + 1:]
            }:
                # A later funnel stage occurred before the expected stage.
                # Stop progression for this session.
                break

        progress_by_session[session_id] = progress

    results = []
    previous_count = total_sessions

    for index, (stage_name, event_name) in enumerate(FUNNEL_STAGES, start=1):
        reached_count = sum(
            progress >= index
            for progress in progress_by_session.values()
        )

        results.append({
            "stage": stage_name,
            "event_type": event_name,
            "sessions_reached": reached_count,
            "session_reach_rate": (
                reached_count / total_sessions
                if total_sessions else 0.0
            ),
            "stage_to_stage_rate": (
                reached_count / previous_count
                if previous_count else 0.0
            ),
        })

        previous_count = reached_count

    return pd.DataFrame(results)
