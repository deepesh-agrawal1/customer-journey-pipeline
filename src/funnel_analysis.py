
import pandas as pd


FUNNEL_STAGES = [
    ("browse", "page_view"),
    ("product_interest", "item_viewed"),
    ("cart_intent", "add_to_cart"),
    ("purchase", "purchase"),
]


def calculate_funnel(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate session reach and stage-to-stage funnel rates."""

    session_ids = sessions["session_id"].drop_duplicates()

    event_sets = (
        events.groupby("session_id")["event_type"]
        .agg(set)
        .to_dict()
    )

    previous_reached = None
    results = []

    for stage_name, event_name in FUNNEL_STAGES:
        reached_ids = {
            session_id
            for session_id in session_ids
            if event_name in event_sets.get(session_id, set())
        }

        reached_count = len(reached_ids)

        if previous_reached is None:
            stage_rate = (
                reached_count / len(session_ids)
                if len(session_ids) else 0.0
            )
        else:
            stage_rate = (
                reached_count / previous_reached
                if previous_reached else 0.0
            )

        results.append({
            "stage": stage_name,
            "event_type": event_name,
            "sessions_reached": reached_count,
            "session_reach_rate": (
                reached_count / len(session_ids)
                if len(session_ids) else 0.0
            ),
            "stage_to_stage_rate": stage_rate,
        })

        previous_reached = reached_count

    return pd.DataFrame(results)
