
import json
import os
import re

import pandas as pd
from dotenv import load_dotenv

from src.api_helpers import (
    SESSIONS_FILE,
    EVENTS_FILE,
    OUTCOMES_FILE,
)

load_dotenv()


def _read_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _safe_rate(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else 0.0


def calculate_journey_metrics():
    sessions = _read_csv(SESSIONS_FILE)
    events = _read_csv(EVENTS_FILE)
    outcomes = _read_csv(OUTCOMES_FILE)

    if sessions.empty or "session_id" not in sessions.columns:
        raise ValueError("Sessions data is missing or has no session_id column.")

    sessions = sessions.drop_duplicates("session_id").copy()

    if not outcomes.empty and {"session_id", "outcome"}.issubset(outcomes.columns):
        outcomes = outcomes.drop_duplicates("session_id")
        session_data = sessions.merge(
            outcomes[["session_id", "outcome"]],
            on="session_id",
            how="left",
            validate="one_to_one",
        )
    else:
        session_data = sessions.copy()
        session_data["outcome"] = None

    total_sessions = len(session_data)
    converted = int((session_data["outcome"] == "converted").sum())
    support_sessions = int(
        (session_data["outcome"] == "support_contact").sum()
    )
    abandoned = int(
        (session_data["outcome"] == "abandoned").sum()
    )

    metrics = {
        "total_sessions": total_sessions,
        "total_events": int(len(events)),
        "converted_sessions": converted,
        "conversion_rate": _safe_rate(converted, total_sessions),
        "support_sessions": support_sessions,
        "support_contact_rate": _safe_rate(support_sessions, total_sessions),
        "abandoned_sessions": abandoned,
        "abandonment_rate": _safe_rate(abandoned, total_sessions),
    }

    if not events.empty and {"session_id", "event_type"}.issubset(events.columns):
        event_types = events["event_type"].astype(str).str.lower()

        funnel = []
        for stage, event_name in [
            ("Browse", "page_view"),
            ("Product interest", "item_viewed"),
            ("Cart intent", "add_to_cart"),
            ("Purchase", "purchase"),
        ]:
            matching = events[event_types == event_name]
            funnel.append({
                "stage": stage,
                "event": event_name,
                "event_count": int(len(matching)),
                "sessions": int(matching["session_id"].nunique()),
            })

        metrics["funnel"] = funnel

    if "device" in session_data.columns:
        device_results = []
        for device, group in session_data.groupby("device", dropna=False):
            total = len(group)
            conversions = int((group["outcome"] == "converted").sum())

            device_results.append({
                "device": str(device) if pd.notna(device) else "unknown",
                "sessions": int(total),
                "converted_sessions": conversions,
                "conversion_rate": _safe_rate(conversions, total),
            })

        metrics["device_performance"] = device_results

    return metrics


def _fallback_insights(metrics):
    insights = []
    total = metrics["total_sessions"]
    conversion_rate = metrics["conversion_rate"]

    if total == 0:
        return [{
            "title": "No session data available",
            "finding": "The pipeline contains no sessions to analyze.",
            "evidence": {},
            "recommendation": "Generate or load session data, then rerun the analysis.",
            "priority": "high",
        }]

    insights.append({
        "title": "Overall conversion",
        "finding": (
            f"{metrics['converted_sessions']} of {total} sessions converted "
            f"({conversion_rate:.1%})."
        ),
        "evidence": {
            "sessions": total,
            "converted_sessions": metrics["converted_sessions"],
            "conversion_rate": conversion_rate,
        },
        "recommendation": (
            "Inspect the funnel stages where the largest number of sessions "
            "drop off before purchase."
        ),
        "priority": "high" if conversion_rate < 0.2 else "medium",
    })

    funnel = metrics.get("funnel", [])
    for previous, current in zip(funnel, funnel[1:]):
        previous_count = previous["sessions"]
        current_count = current["sessions"]

        if previous_count > 0 and current_count <= previous_count:
            drop_rate = 1 - current_count / previous_count

            insights.append({
                "title": f"Drop-off: {previous['stage']} to {current['stage']}",
                "finding": (
                    f"Unique sessions decrease from {previous_count} to "
                    f"{current_count} ({drop_rate:.1%} fewer sessions)."
                ),
                "evidence": {
                    "previous_stage": previous["stage"],
                    "previous_sessions": previous_count,
                    "current_stage": current["stage"],
                    "current_sessions": current_count,
                    "drop_rate": round(drop_rate, 4),
                },
                "recommendation": (
                    "Investigate the transition between these stages using "
                    "event sequences and session-level data."
                ),
                "priority": "high" if drop_rate >= 0.5 else "medium",
            })

    return insights


def generate_ai_insights():
    metrics = calculate_journey_metrics()
    fallback = _fallback_insights(metrics)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "provider": "rules_based_fallback",
            "metrics": metrics,
            "insights": fallback,
            "message": "Set GEMINI_API_KEY to enable Gemini-generated explanations.",
        }

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        prompt = f"""
You are a careful customer journey analytics specialist.

Analyze the supplied calculated metrics. Do not invent data, numbers,
causes, or statistical significance. Treat correlations and possible causes
as hypotheses, not proven facts. If evidence is insufficient, say so.

Return ONLY valid JSON in this format:
{{
  "insights": [
    {{
      "title": "Short title",
      "finding": "What the evidence shows",
      "evidence": {{"metric": "value"}},
      "recommendation": "A specific next action",
      "priority": "high|medium|low"
    }}
  ]
}}

Provide 3 to 6 useful insights. Prioritize material funnel drop-offs,
conversion patterns, and device differences where supported. Explain
what to investigate rather than claiming an unproven cause.

Calculated metrics:
{json.dumps(metrics, ensure_ascii=False, default=str)}
"""

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        text = (response.text or "").strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        parsed = json.loads(text)
        insights = parsed.get("insights")

        if not isinstance(insights, list) or not insights:
            raise ValueError("Gemini returned no valid insights.")

        for item in insights:
            if not isinstance(item, dict) or not all(
                key in item
                for key in ("title", "finding", "evidence", "recommendation", "priority")
            ):
                raise ValueError("Gemini returned an invalid insight format.")

        return {
            "provider": "gemini",
            "model": model,
            "metrics": metrics,
            "insights": insights,
        }

    except Exception:
        return {
            "provider": "rules_based_fallback",
            "metrics": metrics,
            "insights": fallback,
            "message": (
                "Gemini was unavailable or returned an invalid response. "
                "Showing rule-based insights instead."
            ),
        }
