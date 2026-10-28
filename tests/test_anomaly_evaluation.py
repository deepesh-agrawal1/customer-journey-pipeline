import pandas as pd

from src.anomaly_evaluation import evaluate_anomalies


def test_perfect_detection_scores():
    truth = pd.DataFrame([{
        "anomaly_type": "duplicate_event",
        "entity_type": "event",
        "entity_id": "EVT-001",
        "session_id": "SES-001",
        "ground_truth_label": 1,
    }])
    detected = truth.drop(columns=["ground_truth_label"]).copy()

    evaluation, summary = evaluate_anomalies(truth, detected)

    assert evaluation.iloc[0]["status"] == "detected"
    assert summary.iloc[0]["true_positives"] == 1
    assert summary.iloc[0]["false_positives"] == 0
    assert summary.iloc[0]["false_negatives"] == 0
    assert summary.iloc[0]["precision"] == 1.0
    assert summary.iloc[0]["recall"] == 1.0


def test_missed_anomaly_is_false_negative():
    truth = pd.DataFrame([{
        "anomaly_type": "delayed_ingestion",
        "entity_type": "event",
        "entity_id": "EVT-002",
        "session_id": "SES-002",
        "ground_truth_label": 1,
    }])
    detected = pd.DataFrame(columns=[
        "anomaly_type", "entity_type", "entity_id", "session_id"
    ])

    evaluation, summary = evaluate_anomalies(truth, detected)

    assert evaluation.iloc[0]["status"] == "missed"
    assert summary.iloc[0]["false_negatives"] == 1
    assert summary.iloc[0]["recall"] == 0.0


def test_unexpected_detection_is_false_positive():
    truth = pd.DataFrame([{
        "anomaly_type": "duplicate_event",
        "entity_type": "event",
        "entity_id": "EVT-001",
        "session_id": "SES-001",
        "ground_truth_label": 1,
    }])
    detected = pd.DataFrame([{
        "anomaly_type": "duplicate_event",
        "entity_type": "event",
        "entity_id": "EVT-999",
        "session_id": "SES-999",
    }])

    _, summary = evaluate_anomalies(truth, detected)

    assert summary.iloc[0]["false_positives"] == 1
    assert summary.iloc[0]["false_negatives"] == 1


def test_empty_ground_truth():
    truth = pd.DataFrame(columns=[
        "anomaly_type", "entity_type", "entity_id", "session_id"
    ])
    detected = pd.DataFrame(columns=[
        "anomaly_type", "entity_type", "entity_id", "session_id"
    ])

    _, summary = evaluate_anomalies(truth, detected)

    assert summary.iloc[0]["true_positives"] == 0
    assert summary.iloc[0]["false_positives"] == 0
