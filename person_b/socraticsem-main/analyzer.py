import numpy as np
from typing import List, Dict, Any
import json
import os
import re

from groq import Groq

def detect_dropout_cliffs(chunk_stats: List[Dict[str, Any]], cliff_threshold: float = 10.0) -> List[Dict[str, Any]]:
    cliffs = []

    for i in range(1, len(chunk_stats)):
        prev_lost = chunk_stats[i - 1]["lost_pct"]
        curr_lost = chunk_stats[i]["lost_pct"]
        spike = curr_lost - prev_lost

        if spike >= cliff_threshold:
            cliffs.append({
                "chunk_index": chunk_stats[i]["chunk_index"],
                "chunk_text": chunk_stats[i]["chunk_text"],
                "key_concepts": chunk_stats[i]["key_concepts"],
                "lost_pct": curr_lost,
                "spike": round(spike, 1),
                "avg_comprehension": chunk_stats[i]["avg_comprehension"],
            })

    if chunk_stats and chunk_stats[0]["lost_pct"] >= cliff_threshold:
        cliffs.insert(0, {
            "chunk_index": 0,
            "chunk_text": chunk_stats[0]["chunk_text"],
            "key_concepts": chunk_stats[0]["key_concepts"],
            "lost_pct": chunk_stats[0]["lost_pct"],
            "spike": chunk_stats[0]["lost_pct"],
            "avg_comprehension": chunk_stats[0]["avg_comprehension"],
        })

    cliffs.sort(key=lambda x: x["spike"], reverse=True)
    return cliffs[:3]


def generate_fix_suggestions(cliffs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fixes = []

    for cliff in cliffs:
        fallback = {
            "diagnosis": "High dropout detected at this chunk - likely due to missing prerequisite context or concept density.",
            "rewritten_chunk": cliff["chunk_text"],
            "changes_made": "No rewrite available.",
            "predicted_recovery_pct": 0,
        }

        try:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("Rewriting is not configured")
            concepts_str = ', '.join(cliff['key_concepts']) if cliff['key_concepts'] else 'unknown'
            prompt = (
                f"You are an expert instructional designer. A lesson chunk caused a dropout cliff.\n\n"
                f"CHUNK: \"{cliff['chunk_text']}\"\n"
                f"KEY CONCEPTS: {concepts_str}\n"
                f"STATS: {cliff['lost_pct']}% students lost, spike={cliff['spike']}%, "
                f"avg_comprehension={cliff['avg_comprehension']}\n\n"
                f"Return ONLY valid JSON:\n"
                f"{{\"diagnosis\":\"...\",\"rewritten_chunk\":\"...\","
                f"\"changes_made\":\"...\",\"predicted_recovery_pct\":number}}"
            )

            with Groq(api_key=api_key, timeout=20) as client:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    max_completion_tokens=2048,
                    reasoning_effort="low",
                    temperature=0.4,
                    messages=[{"role": "user", "content": prompt}],
                )

            raw = (response.choices[0].message.content or "").strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            fix_data = json.loads(raw)
            if not isinstance(fix_data, dict) or not all(key in fix_data for key in fallback):
                raise ValueError("Incomplete rewrite")
            fix_data = {key: fix_data[key] for key in fallback}
            source = "model"
        except Exception:
            fix_data = fallback
            source = "template"

        fixes.append({
            "chunk_index": cliff["chunk_index"],
            "chunk_text": cliff["chunk_text"],
            "lost_pct": cliff["lost_pct"],
            "spike": cliff["spike"],
            **fix_data,
            "suggestion_source": source,
        })

    return fixes


def compute_summary_stats(chunk_stats: List[Dict[str, Any]], n_students: int) -> Dict[str, Any]:
    if not chunk_stats:
        return {}

    final_lost_pct = chunk_stats[-1]["lost_pct"]
    final_struggling_pct = chunk_stats[-1]["struggling_pct"]
    final_engaged_pct = chunk_stats[-1]["engaged_pct"]

    avg_comprehension_curve = [c["avg_comprehension"] for c in chunk_stats]
    overall_avg = float(np.mean(avg_comprehension_curve))

    majority_loss_chunk = None
    for stat in chunk_stats:
        if stat["lost_pct"] >= 50:
            majority_loss_chunk = stat["chunk_index"]
            break

    health_score = round(final_engaged_pct * 0.5 + overall_avg * 100 * 0.5)

    return {
        "health_score": health_score,
        "final_engaged_pct": final_engaged_pct,
        "final_struggling_pct": final_struggling_pct,
        "final_lost_pct": final_lost_pct,
        "overall_avg_comprehension": round(overall_avg, 3),
        "majority_loss_chunk": majority_loss_chunk,
        "total_students_simulated": n_students,
    }


def analyze_results(simulation_results: Dict[str, Any]) -> Dict[str, Any]:
    chunk_stats = simulation_results["chunk_stats"]
    n_students = simulation_results["n_students"]

    cliffs = detect_dropout_cliffs(chunk_stats)
    fixes = generate_fix_suggestions(cliffs) if cliffs else []
    summary = compute_summary_stats(chunk_stats, n_students)

    return {
        "summary": summary,
        "chunk_stats": chunk_stats,
        "dropout_cliffs": cliffs,
        "fix_suggestions": fixes,
        "student_journeys": simulation_results["student_journeys"],
    }
