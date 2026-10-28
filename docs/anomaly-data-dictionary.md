# Anomaly Data Dictionary

## Purpose

This document defines the schema for anomalies injected into and detected within the synthetic customer journey dataset. The system must preserve the original clean data so that detected anomalies can be compared against known ground-truth labels.

## 1. Anomaly Record Schema

| Field | Type | Required | Description | Validation rule |
|---|---|---|---|---|
| anomaly_id | string | Yes | Unique anomaly identifier | Must be unique and non-empty; format `ANM-000001` |
| anomaly_type | string | Yes | Category of anomaly | Must be one of the supported types |
| severity | string | Yes | Impact level | `low`, `medium`, or `high` |
| entity_type | string | Yes | Affected record type | `event` or `session` |
| entity_id | string | Yes | ID of the affected record | Must reference an existing entity |
| session_id | string | Yes | Related customer session | Must reference an existing session |
| description | string | Yes | Explanation of the anomaly | Must be non-empty |
| detected_at | datetime | Yes | Time the anomaly was detected | Must use ISO 8601 format |
| ground_truth_label | integer | Yes | Whether the record is a known injected anomaly | `1` = anomaly, `0` = normal |
| detection_method | string | Yes | Rule that detected the anomaly | Must be non-empty |
| status | string | Yes | Detection result | `detected`, `missed`, or `false_positive` |

## 2. Supported Anomaly Types

| Anomaly type | Description | Initial severity |
|---|---|---|
| `duplicate_event` | The same event is recorded more than once within a session | Medium |
| `event_outside_session` | An event timestamp falls before the session starts or after it ends | High |
| `delayed_ingestion` | An event arrives substantially later than it occurred | Medium |
| `checkout_abandonment` | A session reaches checkout but has no subsequent purchase event | Medium |

## 3. Ground-Truth Rules

- Injected anomalies must have `ground_truth_label = 1`.
- Normal records must have `ground_truth_label = 0`.
- The detector must not use the ground-truth label as an input.
- A known injected anomaly that the detector fails to identify is a false negative, recorded in evaluation results as a missed anomaly.
- A normal record incorrectly flagged by the detector is a false positive.
- Keep the original clean dataset unchanged and store anomaly-injected data separately.

## 4. Storage

Store the following outputs separately:

- `data/anomalies/ground_truth_anomalies.csv` — records of deliberately injected anomalies.
- `data/anomalies/detected_anomalies.csv` — anomalies identified by the detection rules.
- `data/anomalies/anomaly_evaluation.csv` — comparison of detections against ground truth.

## 5. Initial Scope

Implement the four supported anomaly types first. Use deterministic injection rules and fixed thresholds so the results are reproducible across runs.
