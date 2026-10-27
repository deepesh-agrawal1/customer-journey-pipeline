
# Event Taxonomy

## 1. Common event fields

Every event must include:

- event_id: immutable unique event identifier
- event_type: canonical event name from the taxonomy
- event_timestamp: UTC time when the action occurred
- ingestion_timestamp: UTC time when the event was received
- channel: web, app, or support
- source: synthetic_web, synthetic_app, or synthetic_support
- session_id: nullable until session assignment is resolved
- customer_id: nullable when identity is unknown or linking is not permitted
- anonymous_id: synthetic anonymous browser/app identity where applicable
- issue_type: nullable for normal events; populated for deliberate anomaly cases

## 2. Navigation and discovery

| Event type | Channel | Required context | Funnel stage |
|---|---|---|---|
| page_view | web, app | page_id | browse |
| search_submitted | web, app | session_id | discovery |
| item_viewed | web, app | product_id | product_interest |
| item_selected | web, app | product_id | product_interest |

## 3. Cart events

| Event type | Channel | Required context | Funnel stage |
|---|---|---|---|
| add_to_cart | web, app | cart_id, product_id | cart_intent |
| remove_from_cart | web, app | cart_id, product_id | cart_update |
| cart_viewed | web, app | cart_id | cart_intent |
| checkout_started | web, app | cart_id | checkout |

## 4. Purchase events

| Event type | Channel | Required context | Funnel stage |
|---|---|---|---|
| payment_started | web, app | cart_id or order_id | checkout |
| payment_succeeded | web, app | order_id | purchase |
| payment_failed | web, app | order_id when available | checkout_failure |
| purchase | web, app | order_id | conversion evidence |

A purchase event alone is not sufficient to establish a verified conversion. The event must reconcile with a qualifying Order record and the documented order lifecycle rule.

## 5. Support events

| Event type | Channel | Required context | Outcome relevance |
|---|---|---|---|
| support_contact | support, web, app | ticket_id when a ticket is created | support interaction |
| support_ticket_created | support | ticket_id | support interaction |
| support_ticket_resolved | support | ticket_id | support resolution |

A support interaction may occur before or after a purchase. Outcome rules must explicitly define whether the outcome represents a successful conversion, support involvement, or unresolved friction.

## 6. Session lifecycle events

| Event type | Channel | Required context |
|---|---|---|
| session_started | web, app | session_id |
| session_ended | web, app | session_id |

Session boundaries are ultimately derived from eligible event timestamps and the configured inactivity threshold. Explicit lifecycle events are supporting evidence, not the sole source of session boundaries.

## 7. Errors and anomaly events

| Event type | Channel | Purpose |
|---|---|---|
| error_occurred | web, app, support | Application or workflow failure |
| action_failed | web, app | A customer action failed |
| event_duplicate_detected | internal processing | Duplicate event detection result |
| identity_conflict_detected | internal processing | Identity-link conflict |
| late_event_detected | internal processing | Event arrived after the expected time window |

Processing-detection events must be distinguishable from original customer activity events.

## 8. Funnel definitions

The primary funnel is:

1. browse: page_view
2. product_interest: item_viewed
3. cart_intent: add_to_cart
4. checkout: checkout_started
5. conversion: verified qualifying order

A session progresses only when the required stages occur in the documented order. Repeated events at the same stage do not count as additional sessions.

## 9. Outcome rules

Outcome precedence for the initial version:

1. converted: a qualifying completed order is verified
2. support_contact: support occurred without verified conversion
3. abandoned: meaningful purchase intent exists but no qualifying conversion occurred
4. no_conversion: no qualifying conversion or stronger outcome evidence exists

Outcome records must include reason_code, evidence references, derived_at, and rules_version.

## 10. Event-time and ingestion-time rules

- event_timestamp represents occurrence time.
- ingestion_timestamp represents arrival time.
- Both timestamps must be valid UTC-aware timestamps.
- ingestion_timestamp may be later than event_timestamp.
- Late-arriving events are preserved and processed according to the late-event policy.
- Journey ordering uses event_timestamp, with a deterministic tie-breaker for equal timestamps.
- Event IDs remain unchanged during standardization, deduplication, and analytics.

## 11. Anomaly labelling

Use issue_type only for explicitly injected or detected issues, such as:

- late_arrival
- duplicate_conversion
- incorrect_identity_merge
- bot_customer_mixture
- invalid_foreign_key
- invalid_lifecycle_transition

Store expected labels and handling decisions separately in ground_truth.csv. Ground-truth labels must not be used as model or detection inputs.
