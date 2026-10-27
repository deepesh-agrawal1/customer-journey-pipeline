
import pandas as pd


def derive_journey_outcomes(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Derive one evidence-based outcome for each session."""

    event_groups = {
        session_id: set(group["event_type"].dropna())
        for session_id, group in events.groupby("session_id")
    }

    outcomes = []

    for _, session in sessions.iterrows():
        session_id = session["session_id"]
        event_types = event_groups.get(session_id, set())

        if "purchase" in event_types:
            outcome = "converted"
            reason = "purchase_event_detected"
        elif "support_contact" in event_types:
            outcome = "support_required"
            reason = "support_contact_without_purchase"
        elif "add_to_cart" in event_types:
            outcome = "abandoned"
            reason = "cart_activity_without_purchase"
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

    return pd.DataFrame(outcomes)

