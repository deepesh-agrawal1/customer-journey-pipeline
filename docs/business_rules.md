


# Business Rules

## 1. Reproducibility

- Every generation run must use a configured random seed.
- The same seed and configuration must produce identical logical records.
- Generated timestamps must be derived from fixed reference dates, not the current system time.
- Record counts and file checksums must be recorded in the source manifest.
- Changing the seed may change generated values but must not break referential integrity.

## 2. Data generation order

Generate entities in dependency order:

1. Customer
2. Page, Product, and Experiment
3. Session
4. Cart
5. JourneyEvent
6. CartItem
7. Order and OrderItem
8. SupportTicket
9. ExperimentAssignment
10. JourneyOutcome

Every dependent record must reference an existing parent when the relationship is required.

## 3. Identifier rules

- Customer: CUS-000001
- Session: SES-2026-000001
- Event: EVT-SES-2026-000001-000001
- Experiment: EXP-2026-000001
- Outcome: OUT-SES-2026-000001

IDs must be unique within their entity and stable throughout processing. Bridge tables must have documented primary keys or documented composite keys.

## 4. Sessionization

- The default inactivity threshold is 30 minutes.
- Events for the same eligible identity and channel may belong to the same session when the gap between consecutive events is no greater than the threshold.
- A gap greater than the threshold starts a new session.
- An explicit session boundary takes precedence when valid.
- Events with invalid or unavailable identity information must not be merged based on guesswork.
- Session start and end times must be consistent with the assigned events.
- Store event occurrence time separately from ingestion time.

## 5. Identity and consent

- Anonymous users may have an anonymous_id without a customer_id.
- Do not infer customer identity from unrelated attributes such as device type or country.
- Cross-device identity linking requires an explicit, permitted identifier relationship.
- If consent is denied or unknown, do not perform prohibited identity stitching.
- Preserve anonymous journeys even when they cannot be linked to a registered customer.
- Deliberately incorrect identity merges must be labelled in ground truth.

## 6. Event validation and ordering

- event_id must be unique.
- Required fields must be present and valid.
- event_type and channel must belong to their approved enumerations.
- Required foreign keys must reference existing records.
- event_timestamp must be valid and consistent with applicable lifecycle rules.
- ingestion_timestamp may be later than event_timestamp.
- Events must not be reordered by ingestion time when reconstructing the customer journey.
- For equal event timestamps, use a deterministic tie-breaker such as event sequence or event_id.
- Preserve original records and record standardization or deduplication decisions separately.

## 7. Duplicate handling

- Exact duplicate event IDs must be detected.
- Repeated events with different IDs must not automatically be treated as duplicates; they may represent legitimate repeated actions.
- Duplicate conversion events must not create multiple verified orders for one underlying transaction.
- Deduplication decisions must record the rule applied and the affected event IDs.
- Retain original event records for auditability.

## 8. Cart and order lifecycle

Cart states:
- active
- converted
- abandoned
- expired

Order states:
- pending
- confirmed
- paid
- cancelled
- refunded
- failed

- Lifecycle transitions must follow explicitly allowed state changes.
- A cancelled or failed order is not a successful conversion.
- A refunded order remains historically recorded; reporting treatment must be documented.
- An order must reference valid customer, session, and cart records when those relationships are populated.
- Cart and order relationships must not be inferred if supporting evidence is missing.

## 9. Financial reconciliation

- Quantity must be a positive integer.
- Unit price must be non-negative.
- Each line total must equal quantity multiplied by unit price, subject to the currency's rounding precision.
- Order total must reconcile with its order items, discounts, taxes, shipping, and refunds according to the documented calculation.
- Currency must use a supported currency code.
- Amounts must not be compared across currencies without an explicit conversion rule.

## 10. Verified conversion

A journey is converted only when:
- A qualifying order exists.
- The order satisfies the configured successful lifecycle state.
- The order is not merely a duplicate event or failed transaction.
- Required order totals and relationships pass validation.

The purchase event is evidence of activity, not a substitute for a valid order record.

## 11. Journey outcomes

Produce one current derived outcome per session.

Allowed outcome types:
- converted
- support_contact
- abandoned
- no_conversion

Rules:
- converted requires a verified qualifying order.
- support_contact applies when support interaction occurred without verified conversion.
- abandoned requires meaningful purchase intent without verified conversion.
- no_conversion applies when no stronger outcome is supported.
- If multiple conditions apply, use the documented precedence: converted, support_contact, abandoned, then no_conversion.
- Every outcome must contain evidence references, a derivation timestamp, and a rules version.
- Re-running outcome derivation must replace or version the derived result without altering source events.

## 12. Funnel analytics

Primary funnel:
1. browse
2. product_interest
3. cart_intent
4. checkout
5. verified conversion

- Count distinct sessions reaching each stage.
- Count a stage only when the required event occurs.
- For sequential funnel conversion, a later stage must occur after the previous stage in event time.
- Repeated events within a stage count once per session.
- Report both stage reach rates and stage-to-stage progression rates.
- Document how sessions with missing stages or late-arriving events are treated.

## 13. Anomaly injection

First generate and validate a clean baseline dataset. Then create a separate anomaly-injection step.

Supported anomaly categories:
- late_arrival
- duplicate_conversion
- incorrect_identity_merge
- bot_customer_mixture
- invalid_foreign_key
- invalid_lifecycle_transition

- Each injected anomaly must have a stable anomaly ID.
- Store expected anomaly type, affected entity/record IDs, and expected handling in ground_truth.csv or ground_truth.json.
- Ground truth must remain separate from normal input features.
- Do not silently corrupt baseline data.
- Record anomaly counts in the run manifest.

## 14. Quarantine and recovery

- Invalid records must be written to quarantine with a reason code.
- Valid records should continue through the pipeline when safe.
- A child record with a missing required parent must be quarantined or handled according to an explicit policy.
- Do not silently drop invalid data.
- Validation summaries must report total, valid, and quarantined record counts.
- Quarantined records must retain enough information to trace the original record.

## 15. Dataset scale

Development configuration:
- 100 customers
- 200 sessions

Target configuration:
- 100,000 sessions
- 2,000,000 events

- Development and target runs must use the same generation logic.
- Record counts must be configurable rather than hard-coded.
- Large runs should avoid unnecessary row-by-row DataFrame operations where practical.
