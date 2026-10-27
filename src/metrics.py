
import pandas as pd


def calculate_journey_metrics(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Calculate session-level journey metrics."""

    total_sessions = len(outcomes)

    if total_sessions == 0:
        return pd.DataFrame([{
            "total_sessions": 0,
            "converted_sessions": 0,
            "conversion_rate": 0.0,
            "support_sessions": 0,
            "support_contact_rate": 0.0,
            "abandoned_sessions": 0,
            "cart_abandonment_rate": 0.0,
            "no_conversion_sessions": 0,
            "no_conversion_rate": 0.0,
        }])

    converted = int((outcomes["outcome"] == "converted").sum())
    support = int((outcomes["outcome"] == "support_required").sum())
    abandoned = int((outcomes["outcome"] == "abandoned").sum())
    no_conversion = int((outcomes["outcome"] == "no_conversion").sum())

    return pd.DataFrame([{
        "total_sessions": total_sessions,
        "converted_sessions": converted,
        "conversion_rate": converted / total_sessions,
        "support_sessions": support,
        "support_contact_rate": support / total_sessions,
        "abandoned_sessions": abandoned,
        "cart_abandonment_rate": abandoned / total_sessions,
        "no_conversion_sessions": no_conversion,
        "no_conversion_rate": no_conversion / total_sessions,
    }])
