"""Scores the Matching Agent against a hand-labeled golden set and reports
Spearman correlation (system score vs. human label), missing-skill
precision/recall, and a 3-class confusion matrix. Results are timestamped
under eval/results/ for regression tracking across prompt/weight changes.

Usage (from the repo root, with the backend venv):
    backend/.venv/Scripts/python eval/run_matching_eval.py

Requires eval/golden_set.json — copy eval/golden_set.example.json and fill
in human_label ("good_fit"/"weak_fit"/"poor_fit") and, optionally,
human_missing_skills for each resume_id/job_id pair you want to score
against real ids already in your local SQLite DB.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from agents.matching.graph import run_match  # noqa: E402
from db.jobs import get_job  # noqa: E402
from db.resumes import get_resume  # noqa: E402

GOLDEN_SET_PATH = Path(__file__).resolve().parent / "golden_set.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

LABEL_ORDER = {"poor_fit": 1, "weak_fit": 2, "good_fit": 3}
GOOD_FIT_THRESHOLD = 70
WEAK_FIT_THRESHOLD = 40


def classify(score: float) -> str:
    if score >= GOOD_FIT_THRESHOLD:
        return "good_fit"
    if score >= WEAK_FIT_THRESHOLD:
        return "weak_fit"
    return "poor_fit"


def _rank(values: list[float]) -> list[float]:
    """Average ranks, ties get the mean of the ranks they'd otherwise span."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 2:
        return None
    rx, ry = _rank(x), _rank(y)
    mean_rx, mean_ry = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    std_x = sum((rx[i] - mean_rx) ** 2 for i in range(n)) ** 0.5
    std_y = sum((ry[i] - mean_ry) ** 2 for i in range(n)) ** 0.5
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


def missing_skill_prf(system_missing: list[str], human_missing: list[str]) -> dict:
    sys_norm = {s.strip().lower() for s in system_missing}
    human_norm = {s.strip().lower() for s in human_missing}
    if not human_norm:
        return {"precision": None, "recall": None}
    true_positives = len(sys_norm & human_norm)
    precision = true_positives / len(sys_norm) if sys_norm else 0.0
    recall = true_positives / len(human_norm)
    return {"precision": precision, "recall": recall}


def main():
    if not GOLDEN_SET_PATH.exists():
        raise SystemExit(
            f"No golden set found at {GOLDEN_SET_PATH}.\n"
            f"Copy eval/golden_set.example.json to eval/golden_set.json and fill in "
            f"human_label (good_fit/weak_fit/poor_fit) for 15-20 real resume_id/job_id pairs."
        )

    golden_set = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))

    system_scores, human_scores = [], []
    confusion: dict[str, dict[str, int]] = {}
    precisions, recalls = [], []
    per_pair_results = []

    for entry in golden_set:
        resume_id, job_id = entry["resume_id"], entry["job_id"]
        human_label = entry["human_label"]
        human_missing = entry.get("human_missing_skills", [])

        resume = get_resume(resume_id)
        job = get_job(job_id)
        if resume is None or job is None:
            print(f"Skipping resume_id={resume_id} job_id={job_id}: not found in DB")
            continue

        result = run_match(resume_id, job_id, resume["structured"], job["structured"])
        system_score = result["match_score"]
        predicted_label = classify(system_score)

        system_scores.append(system_score)
        human_scores.append(LABEL_ORDER[human_label])
        confusion.setdefault(human_label, {}).setdefault(predicted_label, 0)
        confusion[human_label][predicted_label] += 1

        prf = missing_skill_prf(result["missing_skills"], human_missing)
        if prf["precision"] is not None:
            precisions.append(prf["precision"])
            recalls.append(prf["recall"])

        per_pair_results.append(
            {
                "resume_id": resume_id,
                "job_id": job_id,
                "human_label": human_label,
                "predicted_label": predicted_label,
                "system_score": system_score,
            }
        )
        print(f"resume={resume_id} job={job_id}: human={human_label} predicted={predicted_label} score={system_score}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_pairs": len(per_pair_results),
        "spearman_correlation": spearman(system_scores, human_scores),
        "missing_skill_precision_avg": sum(precisions) / len(precisions) if precisions else None,
        "missing_skill_recall_avg": sum(recalls) / len(recalls) if recalls else None,
        "confusion_matrix": confusion,
        "per_pair_results": per_pair_results,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"eval_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + json.dumps({k: v for k, v in report.items() if k != "per_pair_results"}, indent=2))
    print(f"\nSaved full report to {out_path}")


if __name__ == "__main__":
    main()
