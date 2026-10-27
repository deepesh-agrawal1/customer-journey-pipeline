
# Entity Relationships and Lifecycle Rules

## 1. Relationship conventions

- Every primary key is unique and immutable.
- Every non-null foreign key must reference an existing parent record.
- Optional foreign keys may be null when the relationship is unknown or not applicable.
- Null customer identity is allowed for anonymous journeys.
- Identity links must not be created when consent is denied or unknown.
- Raw events are immutable. Corrections and processing decisions are stored separately.
- Deliberate anomalies are labelled in issue_type and ground_truth; unrelated records remain valid.
- Effective-dated catalogue records must be valid at the time of the event or transaction.

## 2. Cardinality and foreign keys

| Parent | Child | Cardinality | Foreign key / rule |
|---|---|---|---|
| Customer | Session | 1:N | Session.customer_id is optional |
| Session | JourneyEvent | 1:N | JourneyEvent.session_id is optional until assigned |
| Customer | JourneyEvent | 1:N | JourneyEvent.customer_id is optional and consent-aware |
| Page | JourneyEvent | 1:N | JourneyEvent.page_id is optional |
| Product | JourneyEvent | 1:N | JourneyEvent.product_id is optional |
| Customer | Cart | 1:N | Cart.customer_id is optional |
| Session | Cart | 1:N | Cart.session_id is required |
| Cart | CartItem | 1:N | CartItem.cart_id is required |
| Product | CartItem | 1:N | CartItem.product_id is required |
| Customer | Order | 1:N | Order.customer_id is optional |
| Session | Order | 1:N | Order.session_id is optional |
| Cart | Order | 1:N | Order.cart_id is optional |
| Order | OrderItem | 1:N | OrderItem.order_id is required |
| Product | OrderItem | 1:N | OrderItem.product_id is required |
| Customer | SupportTicket | 1:N | SupportTicket.customer_id is optional |
| Session | SupportTicket | 1:N | SupportTicket.session_id is optional |
| Order | SupportTicket | 1:N | SupportTicket.order_id is optional |
| Experiment | ExperimentAssignment | 1:N | ExperimentAssignment.experiment_id is required |
| Customer | ExperimentAssignment | 1:N | Customer or session subject must be identified |
| Session | ExperimentAssignment | 1:N | Customer or session subject must be identified |
| Session | JourneyOutcome | 1:1 | JourneyOutcome.session_id is required and unique |

## 3. Many-to-many relationships

### Cart and Product
Resolved through CartItem. One cart can contain many products, and a product can occur in many carts.

### Order and Product
Resolved through OrderItem. One order can contain many products, and a product can occur in many orders.

### Experiment and Customer/Session
Resolved through ExperimentAssignment. An experiment can have many assignments; a customer or session can participate in multiple experiments, subject to assignment rules.

## 4. Event assignment and sessionization

- Events are ordered by event_timestamp for journey analysis, not by ingestion_timestamp.
- ingestion_timestamp records when the system received an event.
- Events arriving late remain in raw storage and are handled by downstream processing.
- The initial inactivity threshold is 30 minutes.
- A new session begins when the gap between consecutive eligible events exceeds 30 minutes.
- A session's end time must not precede its start time.
- Events must not be assigned to sessions outside their permitted time window unless explicitly labelled as a session-boundary anomaly.

## 5. Identity and consent

- Anonymous journeys may use anonymous_id without customer_id.
- customer_id must not be inferred from a probabilistic match.
- Identity stitching is allowed only when a documented, explicit synthetic identity link is permitted by consent.
- Consent denied or unknown means no cross-device identity merge.
- Incorrect identity merges used for testing must be labelled and excluded from trusted identity data.

## 6. Lifecycle rules

### Cart
active -> converted
active -> abandoned
active -> expired

A converted cart must be linked to a qualifying order. Abandoned and expired carts must not be treated as completed purchases.

### Order
pending -> confirmed -> paid
pending -> failed
confirmed -> cancelled
paid -> refunded

Only a qualifying paid/confirmed transaction according to the documented business rule may establish conversion. Failed, cancelled, or refunded orders must not be counted as successful purchases by default.

### SupportTicket
open -> pending -> resolved -> closed

A ticket may remain open or pending. resolved_at is null until resolution.

### Experiment
draft -> active -> paused or completed
paused -> active or completed

Assignments must reference an existing experiment and a valid variant for that experiment.

## 7. Data reconciliation

- Order.total_amount must equal the sum of its OrderItem.line_total values under the defined rounding rule.
- Cart and order item quantities must be positive integers.
- OrderItem.line_total = quantity * unit_price.
- Every JourneyOutcome must be derived from evidence events and/or qualifying transactions.
- Duplicate conversion events must not create duplicate orders or multiple final outcomes for the same session.
- Every intentional anomaly must have a ground-truth record with its expected detection or handling decision.
