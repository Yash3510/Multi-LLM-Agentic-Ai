"""
Measure whether 4CE finds the right clause - the small golden set a knowledge
base should be held to before and after every change.

    cd backend && ../.venv/bin/python ../4ce/eval_retrieval.py          # macOS, Linux
    cd backend && ../.venv/Scripts/python.exe ../4ce/eval_retrieval.py  # Windows

Asks the running backend's knowledge base each question below, as the
orchestrator does, and checks that the passage holding the expected clause
comes back in the top k. Then it applies the orchestrator's relevance guard
(_relevant) and checks the guard kept that passage - and that unrelated
questions, which vector search answers with its nearest chunks regardless,
come back empty once the guard has run.

Re-run it after changing chunking, the embedding model, k or the guard, and
compare the numbers. Exits non-zero on any miss.
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, os.getcwd())

# (question, text the answering passage must contain)
GOLDEN = [
    ("What is the acceptable mechanical seal leakage rate?", "Below 5 drops per minute"),
    ("What must happen if a seal leaks 12 drops per minute?", "supervisor's written concurrence"),
    ("How soon must a seal be replaced when leakage is between 5 and 20 drops per minute?", "within 30 days"),
    ("When must a pump be removed from service for seal leakage?", "Above 20 drops per minute"),
    ("What does SOP-MEC-014 say about atomised spray from a seal?", "atomised or visible spray"),
    ("Which ISO 10816 vibration zones are acceptable?", "Zone A or B"),
    ("What action is required for vibration in Zone C?", "Raise a maintenance notification"),
    ("Is Zone D vibration acceptable?", "Zone D: not acceptable"),
    ("When is equipment fit for service on wall thickness?", "remains above the stated retirement thickness"),
    ("What inspection interval applies when the wall thickness margin is below 2 mm?", "six months"),
    ("Can a pump be started with a coupling guard fastener missing?", "coupling guard fastener missing"),
    ("What was the vibration reading on P-101B?", "4.1 mm/s"),
    ("What is the minimum measured wall thickness of P-101B?", "Minimum measured wall thickness 11.2 mm"),
    ("What is the retirement thickness for P-101B?", "Retirement thickness 9.5 mm"),
    ("Which pump is the crude charge pump on standby?", "P-101B - Crude Charge Pump"),
]

# Questions the plant documents cannot answer: nothing should survive the guard.
UNRELATED = [
    "What is the capital of France?",
    "Suggest a recipe for pasta.",
    "Who wrote Hamlet?",
]


def call(url: str, token: str | None = None, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieval hit rate on 4CE's golden set.")
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    parser.add_argument("--email", default="admin@4ce.local")
    parser.add_argument("--password", default="4ce-demo-password")
    parser.add_argument("--k", type=int, default=4, help="passages per question; the orchestrator's retrieval_k")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    spec = importlib.util.spec_from_file_location(
        "orchestrator", Path(__file__).resolve().parent / "functions" / "orchestrator.py"
    )
    orchestrator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orchestrator)
    strong = orchestrator.Pipe.Valves().retrieval_strong_score

    token = call(f"{base}/api/v1/auths/signin", payload={"email": args.email, "password": args.password})["token"]
    model = call(f"{base}/api/v1/models/model?id=ace_orchestrator.tony", token)
    knowledge = [k["id"] for k in (model.get("meta") or {}).get("knowledge") or [] if isinstance(k, dict)]
    if not knowledge:
        sys.exit("No knowledge base is attached to the orchestrator - run 4ce/install.py.")

    def retrieve(question: str) -> list[dict]:
        found = call(f"{base}/api/v1/retrieval/query/collection", token,
                     {"collection_names": knowledge, "query": question, "k": args.k})
        return [
            {"text": text, "name": (meta or {}).get("name", ""), "distance": score}
            for text, meta, score in zip(found["documents"][0], found["metadatas"][0], found["distances"][0])
        ]

    print(f"\n4CE retrieval golden set - top {args.k}, guard keeps shared words or similarity >= {strong}\n")
    found_at, kept, misses = [], 0, []
    for question, expected in GOLDEN:
        passages = retrieve(question)
        rank = next((n for n, p in enumerate(passages, 1) if flat(expected) in flat(p["text"])), None)
        survived = rank is not None and any(
            flat(expected) in flat(p["text"]) for p in orchestrator._relevant(passages, question, strong)
        )
        found_at.append(rank)
        kept += survived
        mark = "HIT " if rank and survived else "MISS"
        if mark == "MISS":
            misses.append(question)
        print(f"  {mark} rank {rank or '-':>2}  {question}")

    print()
    leaked = 0
    for question in UNRELATED:
        passages = retrieve(question)
        left = orchestrator._relevant(passages, question, strong)
        leaked += bool(left)
        print(f"  {'EMPTY' if not left else 'KEPT '} {len(passages)} -> {len(left)}  {question}")

    hits = sum(1 for r in found_at if r)
    first = sum(1 for r in found_at if r == 1)
    print(
        f"\nRetrieved: {hits}/{len(GOLDEN)} in the top {args.k}, {first} at rank 1. "
        f"Kept by the guard: {kept}/{hits}. "
        f"Unrelated questions emptied by the guard: {len(UNRELATED) - leaked}/{len(UNRELATED)}."
    )
    sys.exit(1 if misses or leaked else 0)


if __name__ == "__main__":
    main()
