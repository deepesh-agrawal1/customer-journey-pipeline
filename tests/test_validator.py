
import pandas as pd

from src.validator import (
    validate_events,
    validate_pages,
    validate_products,
)


def test_event_with_wrong_customer_is_quarantined():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
        }
    ])

    customers = pd.DataFrame([
        {"customer_id": "CUS-000001"},
        {"customer_id": "CUS-000002"},
    ])

    events = pd.DataFrame([
        {
            "event_id": "EVT-001",
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000002",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T10:10:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
        }
    ])

    pages = pd.DataFrame([
        {"page_id": "PAG-000001", "page_type": "product"}
    ])

    products = pd.DataFrame([
        {"product_id": "PRD-000001"}
    ])

    valid, invalid = validate_events(
        events, sessions, customers, pages, products
    )

    assert len(valid) == 0
    assert len(invalid) == 1
    assert invalid.iloc[0]["event_id"] == "EVT-001"


def test_event_outside_session_is_quarantined():
    sessions = pd.DataFrame([
        {
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "started_at": "2026-01-01T10:00:00+00:00",
            "ended_at": "2026-01-01T10:30:00+00:00",
        }
    ])

    customers = pd.DataFrame([
        {"customer_id": "CUS-000001"},
    ])

    events = pd.DataFrame([
        {
            "event_id": "EVT-002",
            "session_id": "SES-2026-000001",
            "customer_id": "CUS-000001",
            "event_type": "page_view",
            "event_timestamp": "2026-01-01T11:00:00+00:00",
            "event_sequence": 1,
            "source": "synthetic_web",
        }
    ])

    pages = pd.DataFrame([
        {"page_id": "PAG-000001", "page_type": "product"}
    ])

    products = pd.DataFrame([
        {"product_id": "PRD-000001"}
    ])

    valid, invalid = validate_events(
        events, sessions, customers, pages, products
    )

    assert len(valid) == 0
    assert len(invalid) == 1
    assert invalid.iloc[0]["event_id"] == "EVT-002"


def test_valid_pages_pass_validation():
    pages = pd.DataFrame([
        {
            "page_id": "PAG-000001",
            "page_name": "Home",
            "page_type": "landing",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000002",
            "page_name": "Checkout",
            "page_type": "checkout",
            "channel": "web",
            "lifecycle_status": "active",
        },
    ])

    valid, invalid = validate_pages(pages)

    assert len(valid) == 2
    assert len(invalid) == 0


def test_duplicate_page_ids_are_quarantined():
    pages = pd.DataFrame([
        {
            "page_id": "PAG-000001",
            "page_name": "Home",
            "page_type": "landing",
            "channel": "web",
            "lifecycle_status": "active",
        },
        {
            "page_id": "PAG-000001",
            "page_name": "Search",
            "page_type": "search",
            "channel": "web",
            "lifecycle_status": "active",
        },
    ])

    valid, invalid = validate_pages(pages)

    assert len(valid) == 0
    assert len(invalid) == 2


def test_valid_products_pass_validation():
    products = pd.DataFrame([
        {
            "product_id": "PRD-000001",
            "product_name": "Product 001",
            "category": "electronics",
            "unit_price": 99.99,
            "currency": "USD",
            "lifecycle_status": "active",
        },
        {
            "product_id": "PRD-000002",
            "product_name": "Product 002",
            "category": "books",
            "unit_price": 15.50,
            "currency": "USD",
            "lifecycle_status": "active",
        },
    ])

    valid, invalid = validate_products(products)

    assert len(valid) == 2
    assert len(invalid) == 0


def test_invalid_product_category_and_price_are_quarantined():
    products = pd.DataFrame([
        {
            "product_id": "PRD-000001",
            "product_name": "Valid Product",
            "category": "electronics",
            "unit_price": 99.99,
            "currency": "USD",
            "lifecycle_status": "active",
        },
        {
            "product_id": "PRD-000002",
            "product_name": "Invalid Category",
            "category": "unknown",
            "unit_price": 25.00,
            "currency": "USD",
            "lifecycle_status": "active",
        },
        {
            "product_id": "PRD-000003",
            "product_name": "Negative Price",
            "category": "books",
            "unit_price": -10.00,
            "currency": "USD",
            "lifecycle_status": "active",
        },
        {
            "product_id": "PRD-000004",
            "product_name": "Non-numeric Price",
            "category": "home",
            "unit_price": "invalid",
            "currency": "USD",
            "lifecycle_status": "active",
        },
    ])

    valid, invalid = validate_products(products)

    assert len(valid) == 1
    assert len(invalid) == 3
    assert invalid["product_id"].tolist() == [
        "PRD-000002",
        "PRD-000003",
        "PRD-000004",
    ]
