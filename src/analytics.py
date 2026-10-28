
import pandas as pd


def derive_journey_outcomes(
    sessions: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    """Derive one evidence-based outcome for each session."""

    if "session_id" not in sessions.columns:
        raise ValueError(
            "Sessions missing required column: session_id"
        )

    required_event_columns = {"session_id", "event_type"}
    missing_columns = required_event_columns - set(events.columns)

    if missing_columns:
        raise ValueError(
            f"Events missing required columns: {sorted(missing_columns)}"
        )

    # Group events by session and sort chronologically when timestamps
    # are available.
    event_groups = {}

    for session_id, group in events.groupby("session_id", sort=False):
        group = group.copy()

        if "event_timestamp" in group.columns:
            group["_parsed_timestamp"] = pd.to_datetime(
                group["event_timestamp"],
                errors="coerce",
                utc=True,
            )

            group = group.sort_values(
                "_parsed_timestamp",
                kind="stable",
                na_position="last",
            )

        event_groups[session_id] = group

    outcomes = []

    unique_sessions = sessions.drop_duplicates(
        subset=["session_id"]
    )

    for _, session in unique_sessions.iterrows():
        session_id = session["session_id"]
        session_events = event_groups.get(session_id)

        if session_events is None or session_events.empty:
            event_types = []
            has_timestamps = False
        else:
            event_types = (
                session_events["event_type"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
                .tolist()
            )

            has_timestamps = (
                "event_timestamp" in session_events.columns
                and session_events["event_timestamp"].notna().all()
            )

        # Determine whether a purchase is supported by prior product
        # interest. For legacy records without timestamps, preserve
        # compatibility by accepting a recorded purchase.
        valid_purchase_seen = False

        if "purchase" in event_types:
            if not has_timestamps:
                valid_purchase_seen = True
            else:
                product_interest_seen = False

                for event_type in event_types:
                    if event_type == "item_viewed":
                        product_interest_seen = True

                    elif (
                        event_type == "purchase"
                        and product_interest_seen
                    ):
                        valid_purchase_seen = True
                        break

        # Outcome priority: conversion, support, cart abandonment,
        # then no conversion.
        if valid_purchase_seen:
            outcome = "converted"
            reason = "purchase_event_detected"

        elif "support_contact" in event_types:
            outcome = "support_required"
            reason = "support_contact_event_detected"

        elif "add_to_cart" in event_types:
            outcome = "abandoned"
            reason = "cart_activity_without_valid_conversion"

        elif "purchase" in event_types:
            outcome = "no_conversion"
            reason = "no_purchase_event_detected"

        else:
            outcome = "no_conversion"
            reason = "no_purchase_event_detected"

        outcomes.append({
            "outcome_id": f"OUT-{session_id}",
            "session_id": session_id,
            "outcome": outcome,
            "reason": reason,
        })

    return pd.DataFrame(
        outcomes,
        columns=[
            "outcome_id",
            "session_id",
            "outcome",
            "reason",
        ],
    )
