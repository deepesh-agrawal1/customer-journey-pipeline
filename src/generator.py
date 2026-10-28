
import random
from datetime import datetime, timedelta, timezone


def generate_customers(
    customer_count: int,
    seed: int = 42,
) -> list[dict]:
    """Generate deterministic synthetic customer records."""
    if customer_count < 0:
        raise ValueError("customer_count cannot be negative.")

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

    generated_at = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    ).isoformat()

    customers = []

    for i in range(1, customer_count + 1):
        customers.append({
            "customer_id": f"CUS-{i:06d}",
            "created_at": generated_at,
            "country": rng.choice(countries),
            "preferred_device": rng.choice(devices),
            "acquisition_channel": rng.choice(acquisition_channels),
            "is_registered": rng.choice([True, False]),
        })

    return customers


def generate_pages() -> list[dict]:
    """Generate deterministic synthetic page master data."""
    return [
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


def generate_products(
    product_count: int = 20,
    seed: int = 42,
) -> list[dict]:
    """Generate deterministic synthetic product master data."""
    if product_count < 0:
        raise ValueError("product_count cannot be negative.")

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
        products.append({
            "product_id": f"PRD-{i:06d}",
            "product_name": f"Product {i:03d}",
            "category": rng.choice(categories),
            "unit_price": round(rng.uniform(10.0, 500.0), 2),
            "currency": "USD",
            "lifecycle_status": "active",
        })

    return products


def generate_sessions(
    customers: list[dict],
    session_count: int,
    seed: int = 42,
) -> list[dict]:
    """Generate deterministic sessions linked to existing customers."""
    if session_count < 0:
        raise ValueError("session_count cannot be negative.")

    if session_count > 0 and not customers:
        raise ValueError(
            "At least one customer is required to generate sessions."
        )

    rng = random.Random(seed + 1)
    sessions = []

    reference_time = datetime(
        2026, 1, 1, tzinfo=timezone.utc
    )

    for i in range(1, session_count + 1):
        customer = rng.choice(customers)

        start_offset = rng.randint(0, 89 * 24 * 60)
        started_at = reference_time + timedelta(
            minutes=start_offset
        )

        duration_minutes = rng.randint(1, 60)
        ended_at = started_at + timedelta(
            minutes=duration_minutes
        )

        sessions.append({
            "session_id": f"SES-2026-{i:06d}",
            "customer_id": customer["customer_id"],
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "device": customer["preferred_device"],
            "country": customer["country"],
            "duration_minutes": duration_minutes,
        })

    return sessions


def generate_events(
    sessions: list[dict],
    pages: list[dict],
    products: list[dict],
    seed: int = 42,
    target_event_count: int | None = None,
) -> list[dict]:
    """
    Generate variable-length synthetic customer journey events.

    When target_event_count is supplied, generate exactly that number
    of events, subject to the requirement that each non-empty session
    has at least one event.

    IDs are deterministic and unique within each session.
    """
    if target_event_count is not None and target_event_count < 0:
        raise ValueError("target_event_count cannot be negative.")

    session_count = len(sessions)

    if target_event_count is not None:
        minimum_events = session_count

        if target_event_count < minimum_events:
            raise ValueError(
                "target_event_count must be at least the number "
                "of sessions."
            )

    if not sessions:
        if target_event_count not in (None, 0):
            raise ValueError(
                "Cannot generate events without sessions."
            )
        return []

    if not pages:
        raise ValueError("Pages cannot be empty.")

    if not products:
        raise ValueError("Products cannot be empty.")

    rng = random.Random(seed + 2)
    events = []

    page_by_type = {
        page["page_type"]: page["page_id"]
        for page in pages
    }

    # Journey templates have different lengths and behaviors.
    templates = [
        ["page_view", "search_submitted", "page_view"],
        [
            "page_view",
            "item_viewed",
            "page_view",
            "item_viewed",
        ],
        [
            "page_view",
            "search_submitted",
            "page_view",
            "item_viewed",
            "page_view",
            "item_viewed",
        ],
        [
            "page_view",
            "item_viewed",
            "add_to_cart",
            "page_view",
            "item_viewed",
            "add_to_cart",
        ],
        [
            "page_view",
            "search_submitted",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "purchase",
        ],
        [
            "page_view",
            "item_viewed",
            "support_contact",
            "page_view",
            "item_viewed",
        ],
        [
            "page_view",
            "search_submitted",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "support_contact",
        ],
        [
            "page_view",
            "item_viewed",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "page_view",
            "item_viewed",
            "add_to_cart",
            "purchase",
        ],
    ]

    # Decide how many events each session receives.
    if target_event_count is None:
        planned_lengths = [
            len(rng.choice(templates))
            for _ in sessions
        ]
    else:
        # Guarantee one event per session, then distribute the remainder.
        planned_lengths = [1] * session_count
        remaining = target_event_count - session_count

        # Balanced deterministic allocation: distribute full rounds
        # across sessions, then distribute the final remainder.
        full_rounds, extra = divmod(remaining, session_count)

        planned_lengths = [
            length + full_rounds
            for length in planned_lengths
        ]

        indices = list(range(session_count))
        rng.shuffle(indices)

        for index in indices[:extra]:
            planned_lengths[index] += 1

    for session_index, session in enumerate(sessions):
        desired_length = planned_lengths[session_index]

        started_at = datetime.fromisoformat(
            session["started_at"]
        )
        ended_at = datetime.fromisoformat(
            session["ended_at"]
        )

        available_seconds = max(
            1,
            int((ended_at - started_at).total_seconds()),
        )

        sequence = rng.choice(templates).copy()

        # Extend the journey with meaningful browsing and product activity.
        while len(sequence) < desired_length:
            extension = rng.choice([
                ["page_view"],
                ["page_view", "item_viewed"],
                ["search_submitted", "page_view"],
                ["page_view", "item_viewed", "page_view"],
            ])

            sequence.extend(extension)

        # Trim to the planned length without exceeding the exact target.
        sequence = sequence[:desired_length]

        # Prevent a purchase from appearing before product interest.
        # Preserve the target event count by converting an invalid purchase
        # to a page_view instead of inserting extra events.
        product_interest_seen = False
        corrected_sequence = []

        for event_type in sequence:
            if event_type == "item_viewed":
                product_interest_seen = True

            elif event_type == "purchase" and not product_interest_seen:
                event_type = "page_view"

            corrected_sequence.append(event_type)

        sequence = corrected_sequence

        # Generate ordered event timestamps within the session.
        offsets = sorted(
            rng.randint(0, available_seconds)
            for _ in sequence
        )

        for position, (event_type, offset) in enumerate(
            zip(sequence, offsets),
            start=1,
        ):
            event_time = started_at + timedelta(
                seconds=offset
            )

            page_id = None
            product_id = None

            if event_type == "page_view":
                page_id = rng.choice(pages)["page_id"]

            elif event_type == "item_viewed":
                page_id = page_by_type.get("product")
                product_id = rng.choice(products)["product_id"]

            elif event_type == "add_to_cart":
                page_id = page_by_type.get("cart")
                product_id = rng.choice(products)["product_id"]

            elif event_type == "purchase":
                page_id = page_by_type.get("confirmation")
                product_id = rng.choice(products)["product_id"]

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

    if (
        target_event_count is not None
        and len(events) != target_event_count
    ):
        raise RuntimeError(
            f"Expected {target_event_count} events, "
            f"generated {len(events)}."
        )

    return events
