import pandas as pd


MATCH_COLUMNS = [
    "anomaly_type",
    "entity_type",
    "entity_id",
    "session_id",
]


def evaluate_anomalies(
    ground_truth: pd.DataFrame,
    detected: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compare injected anomalies with detections.

    Returns:
        evaluation: one row per ground-truth anomaly, marked detected or missed
        summary: precision, recall, and F1 score
    """
    if ground_truth.empty:
        evaluation = ground_truth.copy()
        summary = pd.DataFrame([{
            "true_positives": 0,
            "false_positives": len(detected),
            "false_negatives": 0,
            "precision": 0.0 if len(detected) else 1.0,
            "recall": 1.0,
            "f1_score": 0.0 if len(detected) else 1.0,
        }])
        return evaluation, summary

    truth = ground_truth.copy()
    predictions = detected.copy()

    for column in MATCH_COLUMNS:
        if column not in truth.columns:
            raise ValueError(f"Ground truth missing column: {column}")
        if column not in predictions.columns:
            raise ValueError(f"Detections missing column: {column}")

        truth[column] = truth[column].fillna("").astype(str)
        predictions[column] = predictions[column].fillna("").astype(str)

    truth_keys = set(
        map(tuple, truth[MATCH_COLUMNS].to_numpy())
    )
    detected_keys = set(
        map(tuple, predictions[MATCH_COLUMNS].to_numpy())
    )

    matched_keys = truth_keys & detected_keys
    missed_keys = truth_keys - detected_keys
    false_positive_keys = detected_keys - truth_keys

    evaluation = truth.copy()
    evaluation["status"] = evaluation.apply(
        lambda row: (
            "detected"
            if tuple(row[column] for column in MATCH_COLUMNS) in matched_keys
            else "missed"
        ),
        axis=1,
    )

    true_positives = len(matched_keys)
    false_positives = len(false_positive_keys)
    false_negatives = len(missed_keys)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 1.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 1.0
    )
    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    summary = pd.DataFrame([{
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }])

    return evaluation, summary
