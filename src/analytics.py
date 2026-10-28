import pandas as pd


def derive_journey_outcomes(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Derive one outcome for each session."""

    event_groups = {}

    for session_id, group in events.groupby("session_id"):
        if "event_timestamp" in group.columns:
            group = group.copy()
            group["event_timestamp"] = pd.to_datetime(
                group["event_timestamp"], utc=True, errors="coerce"
            )
            group = group.sort_values("event_timestamp", kind="stable")

        event_groups[session_id] = group

    outcomes = []

    for _, session in sessions.iterrows():
        session_id = session["session_id"]
        session_events = event_groups.get(session_id)

        if session_events is None:
            event_types = []
        else:
            event_types = session_events["event_type"].dropna().tolist()

        purchase_is_valid = False

        if "purchase" in event_types:
            purchase_index = event_types.index("purchase")
            prior_events = event_types[:purchase_index]

            if "event_timestamp" not in (
                session_events.columns if session_events is not None else []
            ):
                # Compatibility for inputs without timestamps.
                purchase_is_valid = True
            else:
                purchase_is_valid = (
                    "page_view" in prior_events
                    and "item_viewed" in prior_events
                    and prior_events.index("page_view")
                    < prior_events.index("item_viewed")
                )

        if purchase_is_valid:
            outcome = "converted"
            reason = "purchase_event_detected"
        elif "support_contact" in event_types:
            outcome = "support_required"
            reason = "support_contact_without_valid_conversion"
        else:
            outcome = "no_conversion"
            reason = "no_purchase_event_detected"

        outcomes.append({
            "outcome_id": f"OUT-{session_id}",
            "session_id": session_id,
            "customer_id": session["customer_id"],
            "outcome": outcome,
            "reason": reason,
        })

    return pd.DataFrame(
        outcomes,
        columns=[
            "outcome_id",
            "session_id",
            "customer_id",
            "outcome",
            "reason",
        ],
    )