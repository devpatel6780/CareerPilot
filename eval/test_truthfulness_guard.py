"""Ad-hoc test for the Tailoring Agent's truthfulness guard (Phase 4's
"Done when" requires this to catch at least one deliberately-injected false
claim). Feeds it a tailored bullet with fabricated content not present in
the original resume, and checks the guard flags it.

Usage (from the repo root, with the backend venv):
    backend/.venv/Scripts/python eval/test_truthfulness_guard.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from agents.tailoring.graph import check_truthfulness  # noqa: E402
from agents.tailoring.schema import TailoredExperience  # noqa: E402

ORIGINAL_EXPERIENCE = [
    {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "bullets": [
            "Built REST APIs in Python using FastAPI.",
            "Improved query performance by optimizing SQL indexes.",
        ],
    }
]

# Deliberately fabricated: "led a team of 12 engineers" and "Kubernetes" do
# not appear anywhere in ORIGINAL_EXPERIENCE above.
TAILORED_EXPERIENCE = [
    TailoredExperience(
        title="Software Engineer",
        company="Acme Corp",
        bullets=[
            "Built and led a team of 12 engineers building REST APIs in Python using FastAPI and Kubernetes.",
            "Improved query performance by optimizing SQL indexes.",
        ],
    )
]


def main():
    check = check_truthfulness(ORIGINAL_EXPERIENCE, TAILORED_EXPERIENCE)
    print(f"Flags found: {len(check.flags)}")
    for flag in check.flags:
        print(f"- bullet: {flag.bullet}\n  concern: {flag.concern}")

    if check.flags:
        print("\nPASS: truthfulness guard caught the injected false claim.")
    else:
        print("\nFAIL: truthfulness guard did not flag the injected false claim.")


if __name__ == "__main__":
    main()
