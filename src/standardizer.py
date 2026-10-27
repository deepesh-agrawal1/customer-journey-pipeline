
import pandas as pd


EVENT_NAME_MAP = {
    "page view": "page_view",
    "page-view": "page_view",
    "page_view": "page_view",
    "search submitted": "search_submitted",
    "search-submitted": "search_submitted",
    "search_submitted": "search_submitted",
    "item viewed": "item_viewed",
    "item-viewed": "item_viewed",
    "item_viewed": "item_viewed",
    "add to cart": "add_to_cart",
    "add-to-cart": "add_to_cart",
    "add_to_cart": "add_to_cart",
    "support contact": "support_contact",
    "support-contact": "support_contact",
    "support_contact": "support_contact",
    "purchase": "purchase",
}


def standardize_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize customer string fields."""
    df = df.copy()

    for column in [
        "country",
        "preferred_device",
        "acquisition_channel",
    ]:
        df[column] = df[column].astype("string").str.strip()

    df["country"] = df["country"].str.title()
    df["preferred_device"] = df["preferred_device"].str.lower()
    df["acquisition_channel"] = df["acquisition_channel"].str.lower()

    df["is_registered"] = (
        df["is_registered"]
        .astype("string")
        .str.lower()
        .map({"true": True, "false": False})
        .astype("boolean")
    )

    return df


def standardize_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize session timestamps and types."""
    df = df.copy()

    for column in ["started_at", "ended_at"]:
        df[column] = pd.to_datetime(
            df[column], utc=True, errors="coerce"
        )

    df["duration_minutes"] = pd.to_numeric(
        df["duration_minutes"], errors="coerce"
    )

    df["device"] = df["device"].astype("string").str.strip().str.lower()
    df["country"] = df["country"].astype("string").str.strip().str.title()

    return df


def standardize_events(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize event names, timestamps, and sequence numbers."""
    df = df.copy()

    raw_names = df["event_type"].astype("string").str.strip().str.lower()
    df["event_type"] = raw_names.map(EVENT_NAME_MAP).fillna(raw_names)

    df["event_timestamp"] = pd.to_datetime(
        df["event_timestamp"], utc=True, errors="coerce"
    )

    df["event_sequence"] = pd.to_numeric(
        df["event_sequence"], errors="coerce"
    ).astype("Int64")

    df["source"] = df["source"].astype("string").str.strip().str.lower()

    return df

