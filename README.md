# Customer Journey Analytics Platform

A data-driven analytics platform designed to analyze digital customer journeys, identify funnel drop-offs, measure conversion performance, and explore customer behavior across sessions.

The project combines a Python data-processing pipeline, a FastAPI backend, and an interactive web dashboard to transform customer journey events into actionable insights.

## Live Demo

**Frontend Dashboard:** [View Customer Journey Analytics](https://deepesh-agrawal1.github.io/customer-journey-pipeline/)

**GitHub Repository:** [Customer Journey Pipeline](https://github.com/deepesh-agrawal1/customer-journey-pipeline)

> The frontend can be explored as a static website. To load live analytical data and use the complete dashboard functionality, run the backend locally using the instructions below.

## Project Overview

Understanding where customers abandon their journeys is essential for improving digital experiences and conversion rates.

This project generates and processes synthetic customer journey data, validates records, derives journey outcomes, and presents the resulting analytics through an interactive dashboard.

The platform helps answer questions such as:

- How many customer sessions result in a purchase?
- At which stage do customers drop off?
- How do conversion rates differ across devices?
- How many sessions result in support contact?
- Which pages and products receive the most engagement?
- How do customer journey metrics change over time?
- Which records fail data quality validation?

## Key Features

### 1. Customer Journey Funnel
- Visualizes progression through journey stages.
- Tracks page views, product interest, and purchases.
- Identifies conversion drop-offs between stages.

### 2. Journey Outcome Analysis
- Categorizes sessions by their resulting outcomes.
- Tracks conversions, support-required journeys, and non-conversion outcomes.
- Displays outcome counts and percentages.

### 3. Device Performance
- Compares sessions across desktop, mobile, and tablet devices.
- Measures device-level conversion performance.

### 4. Page and Product Analytics
- Analyzes engagement with pages and products.
- Provides performance summaries based on recorded journey events.

### 5. Time-Based Trends
- Groups journey metrics by day, week, or month.
- Helps identify changes in traffic and conversion behavior.

### 6. Session Explorer
- Searches and filters customer sessions.
- Supports exploration of individual session event timelines.

### 7. Data Quality Monitoring
- Validates required fields and identifiers.
- Checks foreign-key relationships and session boundaries.
- Separates valid records from quarantined records.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Visualization | Chart.js |
| Backend | Python, FastAPI |
| Data processing | Pandas, NumPy |
| API server | Uvicorn |
| Data storage | CSV files |
| Testing | Pytest |
| Version control | Git and GitHub |
| Frontend hosting | GitHub Pages |
| Backend hosting | Render (deployment configuration available in the repository) |

## Architecture

```text
Synthetic / Raw Journey Data
            |
            v
   Data Validation Pipeline
            |
            v
  Staged and Curated CSV Data
            |
            v
     FastAPI Backend
            |
            v
       REST Endpoints
            |
            v
 Interactive Web Dashboard
   HTML / CSS / JavaScript
            |
            v
 Funnel, Outcomes, Trends,
 Devices, Sessions and Quality
```

The frontend communicates with the backend through REST APIs. The backend reads the processed CSV datasets and returns aggregated analytics as JSON.

## Project Structure

```text
customer-journey-pipeline/
├── src/
│   ├── api.py
│   ├── generator.py
│   ├── validator.py
│   ├── standardizer.py
│   ├── pipeline.py
│   ├── analytics.py
│   ├── metrics.py
│   └── funnel_analysis.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   ├── raw/
│   ├── staged/
│   ├── curated/
│   ├── quarantine/
│   ├── ground_truth/
│   └── reports/
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## Running the Complete Project Locally

### Prerequisites

- Python 3.10 or later, compatible with the dependencies in `requirements.txt`
- Git
- A modern web browser

### 1. Clone the repository

```bash
git clone https://github.com/deepesh-agrawal1/customer-journey-pipeline.git
cd customer-journey-pipeline
```

### 2. Create a virtual environment

**Windows:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Verify the datasets

Ensure the repository contains the CSV files required by the API in `data/staged` and `data/curated`.

If those datasets are not included in the repository, generate or process them using the project's pipeline before starting the API.

### 5. Start the backend

From the repository root, run:

```bash
python -m uvicorn src.api:app --reload
```

The backend should be available at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

### 6. Configure and start the frontend

Open `frontend/app.js` and check the API base URL used by the dashboard. For local execution, it should point to:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

If the file already defines this variable, update the existing definition rather than adding a duplicate. If the project uses a different configuration pattern, update the existing API URL setting accordingly.

In a second terminal, run:

```cmd
python -m http.server 5500 --directory frontend
```

Open the dashboard at:

http://127.0.0.1:5500

For local development, configure the backend's CORS middleware to allow `http://127.0.0.1:5500`.

## API Endpoints

The backend exposes the following endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/metrics` | Overall journey metrics |
| `GET /api/funnel` | Funnel stage analysis |
| `GET /api/quality` | Data quality summary |
| `GET /api/outcomes` | Journey outcome distribution |
| `GET /api/devices` | Device-level performance |
| `GET /api/performance` | Page and product performance |
| `GET /api/trends?interval=day` | Time-based analytics |
| `GET /api/sessions` | Searchable and filterable sessions |
| `GET /api/sessions/{session_id}/events` | Individual session event timeline |

Interactive API documentation is available at `/docs` when the backend is running.

## Running Tests

Run the automated test suite from the repository root:

```bash
python -m pytest -q
```

The project test suite covers validation behavior, including duplicate identifiers, invalid product data, customer/session consistency, and event timestamps.

## Data Validation

The validation pipeline checks:

- Required columns and missing values.
- Duplicate customer, session, event, page, and product identifiers.
- Valid customer and session references.
- Event customer consistency with the associated session.
- Event timestamps within session boundaries.
- Valid event sequence numbers.
- Page and product references when reference datasets are available.
- Product categories, prices, currencies, and lifecycle status.

Invalid records are separated into quarantine outputs instead of being treated as valid analytical data.

## Dataset and Demonstration Notes

The project uses synthetic customer journey data for demonstration and testing. The results represent the generated dataset and should not be interpreted as real customer or business performance.

The pipeline is designed around CSV-based processing, allowing evaluators to inspect the generated datasets and reproduce the analytics locally.

## Limitations

- The current implementation uses CSV files rather than a production database.
- The demonstration dataset is synthetic.
- Backend-dependent dashboard features require the API and datasets to be available.
- The public frontend and local backend must use compatible API URLs and CORS settings.

## Future Improvements

- Add persistent database storage.
- Introduce larger and more diverse journey datasets.
- Improve cross-channel identity resolution and consent-aware linking.
- Detect anomalous behavior, event delays, and broken journey steps.
- Add advanced segmentation and cohort analysis.
- Containerize the application for reproducible deployment.
- Add automated deployment and monitoring workflows.

## Author

**Deepesh Agrawal**

GitHub: [deepesh-agrawal1](https://github.com/deepesh-agrawal1)

Portfolio: [deepesh.codes](https://deepesh.codes)
