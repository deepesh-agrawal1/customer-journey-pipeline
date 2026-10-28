
# Customer Journey Data Platform — Data Dictionary

## 1. Conventions

- IDs are immutable, unique strings.
- Timestamps use ISO 8601 with UTC timezone information.
- Currency amounts use decimal values and an explicit ISO 4217 currency code.
- Boolean fields must contain true or false, not arbitrary strings.
- Optional fields may be null when the relationship or value is not applicable.
- Foreign keys must reference existing parent records unless the record
  is explicitly labelled as an intentional anomaly.
- Raw source events are preserved; transformations produce new records
  or derived datasets rather than silently rewriting history.
- Synthetic data must not represent real individuals.

## 2. Customer

Purpose: Represents a synthetic customer or an anonymous identity.

Primary key: customer_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| customer_id | string | Yes | Unique; CUS- followed by six digits |
| created_at | timestamp | Yes | Valid UTC timestamp |
| customer_type | string | Yes | registered, guest, anonymous |
| consent_status | string | Yes | granted, denied, unknown |
| consent_updated_at | timestamp | No | UTC timestamp when known |
| country | string | Yes | Valid synthetic country value |
| acquisition_channel | string | Yes | Controlled channel taxonomy |
| lifecycle_status | string | Yes | active, inactive, deleted |

## 3. Session

Purpose: Represents a visit derived from timestamped activity.

Primary key: session_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| session_id | string | Yes | Unique; SES-YYYY- followed by six digits |
| customer_id | string | No | FK to Customer; null for unresolved anonymous identity |
| anonymous_id | string | No | Synthetic anonymous browser/app identifier |
| started_at | timestamp | Yes | UTC timestamp |
| ended_at | timestamp | No | UTC timestamp; not earlier than started_at |
| primary_channel | string | Yes | web, app, support |
| device_type | string | Yes | desktop, mobile, tablet, bot, other |
| session_status | string | Yes | open, closed, timed_out |
| is_bot | boolean | Yes | true or false |

## 4. JourneyEvent

Purpose: Immutable record of one observed action or state transition.

Primary key: event_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| event_id | string | Yes | Unique; EVT-<session-id>- followed by six digits |
| session_id | string | No | FK to Session; null for unassigned events |
| customer_id | string | No | FK to Customer when resolved and permitted |
| anonymous_id | string | No | Synthetic anonymous identifier |
| event_type | string | Yes | Defined event taxonomy |
| event_timestamp | timestamp | Yes | UTC occurrence time |
| ingestion_timestamp | timestamp | Yes | UTC arrival time |
| channel | string | Yes | web, app, support |
| page_id | string | No | FK to Page |
| product_id | string | No | FK to Product |
| order_id | string | No | FK to Order |
| ticket_id | string | No | FK to SupportTicket |
| source_event_id | string | No | Source-system event identifier |
| issue_type | string | No | Null for normal events; controlled anomaly label otherwise |

## 5. Page

Purpose: Catalogue of web or application pages.

Primary key: page_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| page_id | string | Yes | Unique; PAG- followed by six digits |
| page_name | string | Yes | Non-empty |
| page_type | string | Yes | home, listing, product, cart, checkout, support, other |
| channel | string | Yes | web, app, both |
| effective_from | timestamp | Yes | UTC timestamp |
| effective_to | timestamp | No | Later than effective_from when present |
| lifecycle_status | string | Yes | active, inactive |

## 6. Product

Purpose: Catalogue of synthetic products.

Primary key: product_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| product_id | string | Yes | Unique; PRD- followed by six digits |
| product_name | string | Yes | Non-empty |
| category | string | Yes | Controlled category |
| unit_price | decimal | Yes | Non-negative |
| currency | string | Yes | ISO 4217 code |
| lifecycle_status | string | Yes | active, inactive, discontinued |
| effective_from | timestamp | Yes | UTC timestamp |
| effective_to | timestamp | No | Later than effective_from when present |

## 7. Cart

Purpose: Tracks a customer's cart lifecycle.

Primary key: cart_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| cart_id | string | Yes | Unique; CRT- followed by six digits |
| customer_id | string | No | FK to Customer |
| session_id | string | Yes | FK to Session |
| created_at | timestamp | Yes | UTC timestamp |
| updated_at | timestamp | Yes | Not earlier than created_at |
| cart_status | string | Yes | active, converted, abandoned, expired |

## 8. Order

Purpose: Records a completed or attempted purchase transaction.

Primary key: order_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| order_id | string | Yes | Unique; ORD- followed by six digits |
| customer_id | string | No | FK to Customer |
| session_id | string | No | FK to Session |
| cart_id | string | No | FK to Cart |
| created_at | timestamp | Yes | UTC timestamp |
| order_status | string | Yes | pending, confirmed, paid, cancelled, refunded, failed |
| total_amount | decimal | Yes | Non-negative; reconciles with order items |
| currency | string | Yes | ISO 4217 code |

## 9. SupportTicket

Purpose: Tracks support interactions and their lifecycle.

Primary key: ticket_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| ticket_id | string | Yes | Unique; TKT- followed by six digits |
| customer_id | string | No | FK to Customer |
| session_id | string | No | FK to Session |
| order_id | string | No | FK to Order |
| created_at | timestamp | Yes | UTC timestamp |
| resolved_at | timestamp | No | Not earlier than created_at |
| issue_category | string | Yes | payment, delivery, product, account, other |
| ticket_status | string | Yes | open, pending, resolved, closed |

## 10. Experiment

Purpose: Defines an experiment and its active period.

Primary key: experiment_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| experiment_id | string | Yes | Unique; EXP-YYYY- followed by six digits |
| experiment_name | string | Yes | Non-empty |
| experiment_status | string | Yes | draft, active, paused, completed |
| start_at | timestamp | Yes | UTC timestamp |
| end_at | timestamp | No | Later than start_at when present |
| primary_metric | string | Yes | Defined metric identifier |

## 11. JourneyOutcome

Purpose: Stores a derived outcome for a session.

Primary key: outcome_id

| Field | Type | Required | Allowed values / validation |
|---|---|---|---|
| outcome_id | string | Yes | Unique; OUT-<session-id> |
| session_id | string | Yes | FK to Session; one final outcome per session in v1 |
| customer_id | string | No | FK to Customer when known and permitted |
| outcome_type | string | Yes | converted, abandoned, support_contact, no_conversion |
| reason_code | string | Yes | Documented derivation rule |
| evidence_event_ids | string | Yes | Serialized list of contributing event IDs |
| derived_at | timestamp | Yes | UTC processing timestamp |
| rules_version | string | Yes | Version of outcome rules |

## 12. Bridge tables

### CartItem

Primary key: cart_item_id

Fields: cart_item_id (string, required, unique), cart_id (string, required FK), product_id (string, required FK), quantity (integer, positive), unit_price (decimal, non-negative), added_at (UTC timestamp, required).

### OrderItem

Primary key: order_item_id

Fields: order_item_id (string, required, unique), order_id (string, required FK), product_id (string, required FK), quantity (integer, positive), unit_price (decimal, non-negative), line_total (decimal, equal to quantity × unit_price).

### ExperimentAssignment

Primary key: assignment_id

Fields: assignment_id (string, required, unique), experiment_id (string, required FK), customer_id (string, optional FK), session_id (string, optional FK), variant (string, required), assigned_at (UTC timestamp, required).

Constraint: each subject receives at most one assignment per experiment unless the experiment rules explicitly permit reassignment.
