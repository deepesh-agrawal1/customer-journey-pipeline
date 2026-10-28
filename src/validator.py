
import pandas as pd


CUSTOMER_COLUMNS = {
    "customer_id",
    "country",
    "preferred_device",
    "acquisition_channel",
    "is_registered",
}

SESSION_COLUMNS = {
    "session_id",
    "customer_id",
    "started_at",
    "ended_at",
    "device",
    "country",
    "duration_minutes",
}

EVENT_COLUMNS = {
    "event_id",
    "session_id",
    "customer_id",
    "event_type",
    "event_timestamp",
    "event_sequence",
    "source",
}

PAGE_COLUMNS = {
    "page_id",
    "page_name",
    "page_type",
    "channel",
    "lifecycle_status",
}

PRODUCT_COLUMNS = {
    "product_id",
    "product_name",
    "category",
    "unit_price",
    "currency",
    "lifecycle_status",
}


def validate_columns(
    df: pd.DataFrame,
    required_columns: set[str],
) -> list[str]:
    """Return required columns that are missing."""
    return sorted(required_columns - set(df.columns))


def validate_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate valid customers from invalid customer records."""
    df = df.copy()

    missing_columns = validate_columns(df, CUSTOMER_COLUMNS)
    if missing_columns:
        raise ValueError(f"Customers missing columns: {missing_columns}")

    invalid = df["customer_id"].isna() | df["customer_id"].duplicated(keep=False)

    for column in [
        "country",
        "preferred_device",
        "acquisition_channel",
        "is_registered",
    ]:
        invalid |= df[column].isna()

    invalid |= ~df["preferred_device"].isin(["desktop", "mobile", "tablet"])
    invalid |= ~df["is_registered"].isin([True, False])

    return df.loc[~invalid].copy(), df.loc[invalid].copy()


def validate_sessions(
    df: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate sessions and customer references."""
    df = df.copy()

    missing_columns = validate_columns(df, SESSION_COLUMNS)
    if missing_columns:
        raise ValueError(f"Sessions missing columns: {missing_columns}")

    invalid = df["session_id"].isna() | df["session_id"].duplicated(keep=False)
    invalid |= df["customer_id"].isna()
    invalid |= ~df["customer_id"].isin(customers["customer_id"])

    start = pd.to_datetime(df["started_at"], utc=True, errors="coerce")
    end = pd.to_datetime(df["ended_at"], utc=True, errors="coerce")

    invalid |= start.isna() | end.isna()
    invalid |= end < start

    duration = pd.to_numeric(df["duration_minutes"], errors="coerce")
    invalid |= duration.isna() | (duration < 0)

    return df.loc[~invalid].copy(), df.loc[invalid].copy()


def validate_events(
    df: pd.DataFrame,
    sessions: pd.DataFrame,
    customers: pd.DataFrame,
    pages: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate events and their session/customer references."""
    df = df.copy()

    missing_columns = validate_columns(df, EVENT_COLUMNS)
    if missing_columns:
        raise ValueError(f"Events missing columns: {missing_columns}")

    # 1. Initialize the invalid-record mask.
    invalid = (
        df["event_id"].isna()
        | df["event_id"].duplicated(keep=False)
    )

    # 2. Check required IDs and foreign-key references.
    invalid |= df["session_id"].isna()
    invalid |= ~df["session_id"].isin(sessions["session_id"])

    invalid |= df["customer_id"].isna()
    invalid |= ~df["customer_id"].isin(customers["customer_id"])

    # 3. Check that an event's customer matches its session's customer.
    session_customer_map = sessions.set_index("session_id")["customer_id"]
    expected_customer = df["session_id"].map(session_customer_map)

    invalid |= (
        expected_customer.isna()
        | df["customer_id"].ne(expected_customer)
    )

    # 4. Validate the event type.
    invalid |= (
        df["event_type"].isna()
        | df["event_type"].astype(str).str.strip().eq("")
    )
        # Validate page and product foreign keys.
    page_ids = set(pages["page_id"].dropna())
    product_ids = set(products["product_id"].dropna())

    page_id = df["page_id"]
    product_id = df["product_id"]

    # Non-empty IDs must reference existing records.
    invalid |= (
        page_id.notna()
        & page_id.astype(str).str.strip().ne("")
        & ~page_id.isin(page_ids)
    )

    invalid |= (
        product_id.notna()
        & product_id.astype(str).str.strip().ne("")
        & ~product_id.isin(product_ids)
    )

    # item_viewed events must have both a product and a product page.
    product_page_ids = set(
        pages.loc[pages["page_type"].eq("product"), "page_id"]
    )

    item_viewed = df["event_type"].eq("item_viewed")

    invalid |= item_viewed & ~page_id.isin(product_page_ids)
    invalid |= item_viewed & (
        product_id.isna()
        | product_id.astype(str).str.strip().eq("")
        | ~product_id.isin(product_ids)
    )

    # 5. Validate timestamps.
    timestamp = pd.to_datetime(
        df["event_timestamp"],
        utc=True,
        errors="coerce",
    )
    invalid |= timestamp.isna()

    # Check that each event occurs within its session.
    session_start_map = sessions.set_index("session_id")["started_at"]
    session_end_map = sessions.set_index("session_id")["ended_at"]

    session_start = pd.to_datetime(
        df["session_id"].map(session_start_map),
        utc=True,
        errors="coerce",
    )
    session_end = pd.to_datetime(
        df["session_id"].map(session_end_map),
        utc=True,
        errors="coerce",
    )

    invalid |= (
        timestamp.lt(session_start)
        | timestamp.gt(session_end)
    )

    # 6. Validate event sequence numbers.
    sequence = pd.to_numeric(
        df["event_sequence"],
        errors="coerce",
    )
    invalid |= (
        sequence.isna()
        | (sequence < 1)
        | (sequence % 1 != 0)
    )

    return df.loc[~invalid].copy(), df.loc[invalid].copy()

def validate_pages(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate page master records."""
    df = df.copy()

    missing_columns = validate_columns(df, PAGE_COLUMNS)
    if missing_columns:
        raise ValueError(f"Pages missing columns: {missing_columns}")

    invalid = (
        df["page_id"].isna()
        | df["page_id"].duplicated(keep=False)
    )

    for column in ["page_name", "page_type", "channel", "lifecycle_status"]:
        invalid |= (
            df[column].isna()
            | df[column].astype(str).str.strip().eq("")
        )

    invalid |= ~df["page_type"].isin([
        "landing", "search", "product",
        "cart", "checkout", "confirmation",
    ])

    invalid |= ~df["channel"].isin(["web", "app", "support"])

    invalid |= ~df["lifecycle_status"].isin([
        "active", "inactive", "retired",
    ])

    return df.loc[~invalid].copy(), df.loc[invalid].copy()

def validate_products(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate product master records."""
    df = df.copy()

    missing_columns = validate_columns(df, PRODUCT_COLUMNS)
    if missing_columns:
        raise ValueError(f"Products missing columns: {missing_columns}")

    invalid = (
        df["product_id"].isna()
        | df["product_id"].duplicated(keep=False)
    )

    for column in [
        "product_name", "category", "currency", "lifecycle_status",
    ]:
        invalid |= (
            df[column].isna()
            | df[column].astype(str).str.strip().eq("")
        )

    invalid |= ~df["category"].isin([
        "electronics", "clothing", "home",
        "books", "accessories",
    ])

    invalid |= ~df["currency"].isin(["USD", "INR", "GBP", "EUR", "CAD"])

    invalid |= ~df["lifecycle_status"].isin([
        "active", "inactive", "discontinued",
    ])

    price = pd.to_numeric(df["unit_price"], errors="coerce")
    invalid |= price.isna() | (price < 0)

    return df.loc[~invalid].copy(), df.loc[invalid].copy()