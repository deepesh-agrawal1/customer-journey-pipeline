
import random
from datetime import datetime, timedelta, timezone


def generate_customers(customer_count: int, seed: int = 42) -> list[dict]:
    """Generate deterministic synthetic customer records."""
    rng = random.Random(seed)

    devices = ["desktop", "mobile", "tablet"]
    countries = ["India", "USA", "UK", "Canada"]
    acquisition_channels = [
        "organic_search",
        "paid_search",
        "social",
        "direct",
        "email",
    ]

    customers = []
    generated_at = datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()

    for i in range(1, customer_count + 1):
        customer = {
            "customer_id": f"CUS-{i:06d}",
            "created_at": generated_at,
            "country": rng.choice(countries),
            "preferred_device": rng.choice(devices),
            "acquisition_channel": rng.choice(acquisition_channels),
            "is_registered": rng.choice([True, False]),
        }
        customers.append(customer)

    return customers
def generate_pages() -> list[dict]:
    """Generate deterministic synthetic page master data."""

    pages = [
        {
            "page_id": "PAG-000001",
            "page_name": "Home",
            "page_type": "landing",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000002",
            "page_name": "Search Results",
            "page_type": "search",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000003",
            "page_name": "Product Details",
            "page_type": "product",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000004",
            "page_name": "Shopping Cart",
            "page_type": "cart",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000005",
            "page_name": "Checkout",
            "page_type": "checkout",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000006",
            "page_name": "Order Confirmation",
            "page_type": "confirmation",
            "channel": "web",
            "lifecycle_status": "active",
        },
    ]

    return pages
def generate_products(product_count: int = 20, seed: int = 42) -> list[dict]:
    """Generate deterministic synthetic product master data."""

    rng = random.Random(seed + 3)

    categories = [
        "electronics",
        "clothing",
        "home",
        "books",
        "accessories",
    ]

    products = []

    for i in range(1, product_count + 1):
        product = {
            "product_id": f"PRD-{i:06d}",
            "product_name": f"Product {i:03d}",
            "category": rng.choice(categories),
            "unit_price": round(rng.uniform(10.0, 500.0), 2),
            "currency": "USD",
            "lifecycle_status": "active",
        }

        products.append(product)

    return products
def generate_sessions(
    customers: list[dict],
    session_count: int,
    seed: int = 42,
) -> list[dict]:
    """Generate synthetic sessions linked to existing customers."""
    rng = random.Random(seed + 1)

    sessions = []

    # Use a fixed reference time so generated timestamps are reproducible.
    reference_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for i in range(1, session_count + 1):
        customer = rng.choice(customers)

        start_offset = rng.randint(0, 89 * 24 * 60)
        started_at = reference_time + timedelta(minutes=start_offset)
        duration_minutes = rng.randint(1, 60)
        ended_at = started_at + timedelta(minutes=duration_minutes)

        session = {
            "session_id": f"SES-2026-{i:06d}",
            "customer_id": customer["customer_id"],
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "device": customer["preferred_device"],
            "country": customer["country"],
            "duration_minutes": duration_minutes,
        }

        sessions.append(session)

    return sessions

def generate_events(
    sessions: list[dict],
    pages: list[dict],
    products: list[dict],
    seed: int = 42,
) -> list[dict]:
    """Generate synthetic journey events for existing sessions."""
    rng = random.Random(seed + 2)
    events = []

    event_sequences = [
        ["page_view"],
        ["page_view", "search_submitted", "page_view"],
        ["page_view", "item_viewed", "add_to_cart"],
        ["page_view", "item_viewed", "add_to_cart", "purchase"],
        ["page_view", "search_submitted", "page_view", "item_viewed"],
        ["page_view", "support_contact"],
    ]

    for session in sessions:
        sequence = rng.choice(event_sequences)

        started_at = datetime.fromisoformat(session["started_at"])
        ended_at = datetime.fromisoformat(session["ended_at"])

        # Spread events across the session duration.
        available_seconds = max(
            1,
            int((ended_at - started_at).total_seconds()),
        )

        offsets = sorted(
            rng.randint(0, available_seconds)
            for _ in sequence
        )

        for position, (event_type, offset) in enumerate(
            zip(sequence, offsets),
            start=1,
        ):
            event_time = started_at + timedelta(seconds=offset)

            page_id = None
            product_id = None

            if event_type == "page_view":
                page = rng.choice(pages)
                page_id = page["page_id"]

            elif event_type == "item_viewed":
                page = next(
                    p for p in pages
                    if p["page_type"] == "product"
                )
                product_id = rng.choice(products)["product_id"]
                page_id = page["page_id"]

            elif event_type == "purchase":
                page = next(
                    p for p in pages
                    if p["page_type"] == "confirmation"
                )
                product_id = rng.choice(products)["product_id"]
                page_id = page["page_id"]

            events.append({
                "event_id": (
                    f"EVT-{session['session_id']}-{position:06d}"
                ),
                "session_id": session["session_id"],
                "customer_id": session["customer_id"],
                "event_type": event_type,
                "event_timestamp": event_time.isoformat(),
                "event_sequence": position,
                "source": "synthetic_web",
                "page_id": page_id,
                "product_id": product_id,
            })

    return events
