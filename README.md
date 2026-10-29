# Customer Journey Data Platform

A synthetic customer journey data platform designed to generate, validate, and analyze digital customer interactions. The project models customer sessions, behavioral events, conversion outcomes, and funnel performance to help identify journey drop-offs and potential friction points.

The platform currently includes a configurable Python data generator, CSV-based data storage, data validation, journey outcome classification, and analytics. A FastAPI backend and web interface support the next stage of the project.

## Project Overview

Digital customer journeys often span multiple interactions before a customer completes a purchase, abandons a cart, or contacts support. Analyzing these journeys requires structured event data, consistent identifiers, reliable validation, and meaningful analytics.

This project creates reproducible synthetic journey data that can be used to test data pipelines and develop customer journey analytics without depending on real customer information.

### Current Highlights

- Generates synthetic customers, sessions, events, pages, and products.
- Supports configurable customer and session counts.
- Supports deterministic generation using a configurable random seed.
- Produces consistent, structured identifiers.
- Validates generated records and reports quarantined data.
- Derives one journey outcome per session.
- Calculates conversion, support contact, abandonment, and no-conversion metrics.
- Stores raw data as CSV files.
- Includes automated tests using `pytest`.

## Current Dataset

The following results were produced by the latest successful run.

| Dataset / Metric | Current Result |
|---|---:|
| Customers | 5,000 |
| Sessions | 10,000 |
| Journey events | 200,000 |
| Journey outcomes | 10,000 |
| Pages | 6 |
| Products | 20 |
| Validated events | 200,000 |
| Quarantined events | 0 |

### Journey Metrics

| Metric | Result |
|---|---:|
| Converted sessions | 2,508 |
| Conversion rate | 25.08% |
| Sessions involving support | 2,513 |
| Support contact rate | 25.13% |
| Abandoned sessions | 1,220 |
| Cart abandonment rate | 12.20% |
| Sessions with no conversion | 3,759 |
| No-conversion rate | 37.59% |

These are results from the current synthetic dataset. They are not real-world customer benchmarks.

## Technology Stack

- **Language:** Python
- **Data processing:** Pandas and Python data-processing modules
- **Backend:** FastAPI
- **Storage:** CSV files
- **Testing:** pytest
- **Frontend:** HTML, CSS, JavaScript
- **Version control:** Git and GitHub

## Project Structure

```text
customer-journey-pipeline/
├── config/
│   └── config.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── quarantine/
├── src/
│   ├── generator.py
│   ├── validator.py
│   ├── pipeline.py
│   ├── standardizer.py
│   ├── analytics.py
│   ├── metrics.py
│   ├── funnel_analysis.py
│   └── api.py
├── tests/
├── main.py
├── requirements.txt
└── README.md
```

*The structure above describes the main project components; additional files and directories may exist in the repository.*

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/deepesh-agrawal1/customer-journey-pipeline.git
cd customer-journey-pipeline
```

### 2. Create a Virtual Environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the Generator

Update `config/config.json` to change the dataset size and generation settings.

Example configuration:

```json
{
  "seed": 20261022,
  "year": 2026,
  "customer_count": 5000,
  "session_count": 10000,
  "target_event_count": 200000,
  "domain": "generic_digital_journey",
  "storage_format": "csv",
  "timezone": "UTC",
  "session_timeout_minutes": 30
}
```

The `target_event_count` setting controls the requested number of generated events when supported by the current generator. Keep it at or above the session count because each generated session requires at least one event.

### 5. Generate and Validate Data

Run the pipeline:

```bash
python main.py
```

The pipeline generates the configured dataset, writes the raw output files, performs validation, and prints journey metrics.

### 6. Run Automated Tests

```bash
python -m pytest -q
```

Use the test results to verify that changes to the generator, validation rules, and analytics do not break existing functionality.

## Data Model

The current generator works with these primary entities:

| Entity | Purpose |
|---|---|
| Customer | Represents a synthetic customer. |
| Session | Represents a customer browsing or interaction session. |
| JourneyEvent | Records an interaction within a session. |
| Page | Represents a page in the digital journey. |
| Product | Represents a product that can be viewed or purchased. |
| JourneyOutcome | Classifies the final outcome of a session. |

Additional entities, such as carts, orders, support tickets, and experiments, can extend the model as the platform develops.

### Identifier Conventions

Identifiers use predictable, zero-padded formats to make relationships easy to inspect.

| Entity | Example |
|---|---|
| Customer | `CUS-000001` |
| Session | `SES-2026-000001` |
| Event | `EVT-SES-2026-000001-000001` |
| Page | `PAG-000001` |
| Product | `PRD-000001` |
| Outcome | `OUT-SES-2026-000001` |

The event identifier includes the session identifier and an event position. Exact formats should remain consistent with the implementation.

## Data Validation

The validation stage checks generated records against the project's schema and integrity rules.

Current validation includes checks for:

- Required columns and fields.
- Identifier consistency and uniqueness where required.
- Valid event types and allowed values.
- References between events, sessions, customers, pages, and products.
- Event timestamps falling within their associated session boundaries.
- Valid records versus quarantined records.

Invalid records should be investigated rather than silently treated as valid analytical data.

## Journey Analytics

The platform derives session outcomes and calculates summary metrics to help understand customer behavior.

### Outcomes

The current analytics classifies sessions into outcome categories such as:

- **Converted:** A qualifying purchase occurred.
- **Support required:** The session involved a support interaction and did not qualify for a higher-priority outcome.
- **Abandoned:** The session was classified as abandoned.
- **No conversion:** No qualifying conversion or other selected outcome occurred.

Outcome precedence and the precise abandonment definition are governed by the implementation and should be verified against the tests.

### Funnel Analysis

A digital journey can be analyzed through stages such as:

1. Browse
2. Product interest
3. Cart intent
4. Purchase

Funnel analysis measures how many sessions reach each stage and how many continue to the next stage. This can reveal where users leave the journey and where further investigation may be useful.

## Reproducibility

The generator uses a configurable random seed. Keeping the seed and configuration fixed helps make generated data reproducible.

The pipeline also creates a run manifest. Retain the configuration, manifest, and test results when comparing different dataset versions.

For reproducible experiments:

1. Keep the random seed unchanged.
2. Record changes to the configuration.
3. Regenerate the dataset.
4. Run validation and automated tests.
5. Compare the resulting metrics.

## Roadmap

The following are planned improvements and should not be interpreted as completed features unless implemented and tested.

- [ ] Scale generation to 100,000 sessions and approximately 2 million events.
- [ ] Add web, app, and support channel interactions.
- [ ] Separate event occurrence timestamps from ingestion timestamps.
- [ ] Implement consent-aware identity resolution.
- [ ] Add explicit ground-truth labels for synthetic journey problems.
- [ ] Generate duplicate purchase events and other data-quality edge cases.
- [ ] Simulate bot traffic and incorrect identity merges.
- [ ] Analyze funnel drop-offs by channel, device, and journey characteristics.
- [ ] Add friction and anomaly detection.
- [ ] Expand automated tests for edge cases and data integrity.
- [ ] Improve the web interface for exploring metrics and generated datasets.

## Running the API

The project includes a FastAPI application in `src/api.py`. The exact startup command depends on the application's module and ASGI object names.

If the application exposes an `app` object in `src/api.py`, try:

```bash
uvicorn src.api:app --reload
```

The interactive API documentation is typically available at:

```text
http://127.0.0.1:8000/docs
```

If the application uses a different ASGI object or startup configuration, adjust the command accordingly.

## Deployment

- **Source code:** [GitHub Repository](https://github.com/deepesh-agrawal1/customer-journey-pipeline)
- **Frontend:** [GitHub Pages](https://deepesh-agrawal1.github.io/customer-journey-pipeline/)
- **API deployment:** [Render Service](https://customer-journey-pipeline.onrender.com)

Deployment availability and API endpoints depend on the current hosting configuration.

