#!/usr/bin/env python3
"""
generate_exam.py — Exam generation pipeline for exam.riskrunners.com

Generates ONE practice exam (30 questions with worked solutions) for a given
track (FM or P), persists it as a JSON file under data/<track>/, and updates
data/manifest.json.

Design decisions (from the requirements):
  * FM and P are SEPARATE pipelines but persist into the SAME data/ tree and the
    SAME manifest.json (keyed by track).
  * A track keeps a MAX of 10 exams. This is an upsert / FIFO ("first in, first
    out") queue: generating an 11th exam expunges the oldest and deletes its
    file. The UI labels the surviving 10 as #1..#10 by array position.
  * Every question's numbers are drawn from an RNG, so re-running the pipeline
    produces genuinely different exams rather than the same numbers reworded.
  * Output is plain JSON so the static GitHub Pages site (HTML/CSS/JS only) can
    read it with fetch() — no server, no SQL at runtime.

Usage:
    python3 generate_exam.py FM
    python3 generate_exam.py P
    python3 generate_exam.py FM --max 10        # override cap (testing)
    python3 generate_exam.py FM --seed 123       # reproducible (testing)
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

from content_fm import FM_BUILDERS
from content_p import P_BUILDERS
from llm_authoring import author_problem, VALID_RECIPES
import syllabus

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)               # repo root (exam.riskrunners.com)
DATA_DIR = os.path.join(ROOT, "data")
MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")

TRACKS = {
    "FM": {
        "name": "Financial Mathematics",
        "builders": FM_BUILDERS,
        "config": {"numQuestions": 30, "choices": 5, "timeLimitMinutes": 150},
    },
    "P": {
        "name": "Probability",
        "builders": P_BUILDERS,
        "config": {"numQuestions": 30, "choices": 5, "timeLimitMinutes": 180},
    },
}
MAX_KEEP = 10
LETTERS = ["A", "B", "C", "D", "E"]

# Theme hints nudge the LLM to vary the surface story so problems don't read
# like templates. One is drawn at random per problem.
SEED_HINTS = [
    "a small business owner", "a retirement fund", "a university endowment",
    "a municipal bond investor", "a mortgage borrower", "a pension plan",
    "an insurance reserve", "a savings account", "a startup's runway",
    "a real-estate purchase", "a scholarship trust", "a car loan",
    "a manufacturing line", "a call center", "an e-commerce site",
    "a clinical trial", "a fleet of vehicles", "a data center's servers",
    "a portfolio of policies", "a quality-control process",
]


# --------------------------------------------------------------------------
# Choice formatting / distractors
# --------------------------------------------------------------------------
def _format_value(value, unit, nd):
    if unit == "currency":
        return f"{value:,.{nd}f}"
    if unit == "percent":
        return f"{value:,.{nd}f}%"
    if unit == "probability":
        return f"{value:,.{nd}f}"
    if unit == "years":
        return f"{value:,.{nd}f}"
    return f"{value:,.{nd}f}"


def _make_distractors(rng, correct, unit):
    """Produce 4 plausible-but-wrong numeric distractors around `correct`."""
    factors = set()
    candidates = []
    # multiplicative perturbations
    for mult in (0.9, 0.95, 1.05, 1.1, 1.15, 0.85, 1.2, 0.8):
        candidates.append(correct * mult)
    # sign flips / common student errors
    candidates.append(correct * 1.0 + abs(correct) * rng.uniform(0.03, 0.25))
    candidates.append(correct - abs(correct) * rng.uniform(0.03, 0.25))
    if unit == "probability":
        candidates.append(1 - correct)
    rng.shuffle(candidates)

    chosen = []
    for c in candidates:
        if unit == "probability":
            c = min(max(c, 0.0001), 0.9999)
        # keep distractors distinct from correct and each other
        key = round(c, 4)
        if abs(c - correct) < abs(correct) * 0.01 + 1e-9:
            continue
        if key in factors:
            continue
        factors.add(key)
        chosen.append(c)
        if len(chosen) == 4:
            break
    # top up if we somehow ran short
    bump = 1.25
    while len(chosen) < 4:
        c = correct * bump
        chosen.append(c)
        bump += 0.07
    return chosen[:4]


def _build_question(rng, builder, number):
    raw = builder(rng)
    nd = raw.get("round", 2)
    unit = raw.get("unit", "number")
    correct = raw["correct"]

    values = [correct] + _make_distractors(rng, correct, unit)
    rng.shuffle(values)
    correct_index = min(
        range(len(values)), key=lambda i: abs(values[i] - correct)
    )

    choices = {}
    for i, v in enumerate(values):
        choices[LETTERS[i]] = _format_value(v, unit, nd)
    answer_letter = LETTERS[correct_index]

    return {
        "n": number,
        "topic": raw["topic"],
        "stem": raw["stem"],
        "choices": choices,
        "answer": answer_letter,
        "answerValue": _format_value(correct, unit, nd),
        "solution": raw["solution"],
    }


# --------------------------------------------------------------------------
# Exam assembly
# --------------------------------------------------------------------------
def _weighted_plan(track, rng, n_q):
    """Build a per-question plan honoring the official SOA topic weightings.

    Returns a list of length n_q; each item is a dict:
        {"group": <topic group>, "recipe": <llm recipe or None>,
         "builder": <template builder fn>}
    The list is shuffled so topics are interleaved on the exam, but the COUNTS
    per group match syllabus.allocate() (i.e. the syllabus midpoints).
    """
    alloc = syllabus.allocate(track, n_q)

    # recipes grouped by topic
    recipes_by_group = {}
    for recipe, group in syllabus.RECIPE_GROUPS[track].items():
        recipes_by_group.setdefault(group, []).append(recipe)

    # template builders grouped by topic (by function __name__)
    builders_by_group = {}
    for b in TRACKS[track]["builders"]:
        g = syllabus.TEMPLATE_GROUPS[track].get(b.__name__)
        if g:
            builders_by_group.setdefault(g, []).append(b)

    plan = []
    for group, count in alloc.items():
        group_recipes = recipes_by_group.get(group)
        # FM "General Cash Flows, Portfolios & ALM" has no closed-form verifiable
        # recipe in our set, so those questions come from the template builders
        # (duration, dollar-weighted yield) — group_recipes stays None.
        group_builders = builders_by_group.get(group, TRACKS[track]["builders"])

        for j in range(count):
            recipe = None
            if group_recipes:
                recipe = group_recipes[j % len(group_recipes)]
            builder = group_builders[j % len(group_builders)]
            plan.append({"group": group, "recipe": recipe, "builder": builder})

    rng.shuffle(plan)
    return plan


def build_exam(track, rng, source="auto", client=None):
    """Build a 30-question exam.

    source:
      "template" -> deterministic Python templates only (offline, free).
      "bedrock"  -> LLM-authored + Python-verified; fail hard if unavailable.
      "auto"     -> try LLM per problem, fall back to a template on any failure.
    """
    spec = TRACKS[track]
    n_q = spec["config"]["numQuestions"]

    plan = _weighted_plan(track, rng, n_q)

    questions = []
    llm_count = 0
    for i, item in enumerate(plan):
        num = i + 1
        want_llm = (source in ("bedrock", "auto") and client is not None
                    and item["recipe"])
        q = None
        if want_llm:
            hint = rng.choice(SEED_HINTS)
            try:
                q = author_problem(client, track, item["recipe"], num, rng, hint)
                q.pop("_source", None)
                llm_count += 1
                print(f"  [{num:>2}/{n_q}] LLM: {item['recipe']} ({item['group']})")
            except Exception as e:
                if source == "bedrock":
                    raise
                print(f"  [{num:>2}/{n_q}] LLM failed ({str(e)[:50]}); template ({item['group']})")
        if q is None:
            # template path (also used for groups with no verifiable recipe)
            q = _build_question(rng, item["builder"], num)
        # Tag with the authoritative syllabus group; keep the finer LLM/template
        # label as displayTopic for the UI.
        q["displayTopic"] = q.get("topic", item["group"])
        q["topic"] = item["group"]
        questions.append(q)

    # Realized distribution by SYLLABUS GROUP (authoritative, matches weights).
    dist = {}
    for q in questions:
        dist[q["topic"]] = dist.get(q["topic"], 0) + 1

    ts = int(time.time())
    exam_id = f"{track.lower()}-{ts}"
    return {
        "id": exam_id,
        "track": track,
        "trackName": spec["name"],
        "created": datetime.now(timezone.utc).isoformat(),
        "config": spec["config"],
        "source": source,
        "llmQuestions": llm_count,
        "syllabusWeights": {g: syllabus.weight_label(track, g)
                            for g in syllabus.WEIGHTS[track]},
        "topicDistribution": dist,
        "questions": questions,
    }


# --------------------------------------------------------------------------
# Manifest / persistence (upsert + FIFO cap)
# --------------------------------------------------------------------------
def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
    else:
        data = {}
    for t in TRACKS:
        data.setdefault(t, [])
    return data


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def persist(exam, max_keep):
    track = exam["track"]
    track_dir = os.path.join(DATA_DIR, track.lower())
    os.makedirs(track_dir, exist_ok=True)

    manifest = load_manifest()
    entries = manifest[track]

    # Write the new exam file.
    filename = f"{exam['id']}.json"
    rel_path = f"data/{track.lower()}/{filename}"
    with open(os.path.join(track_dir, filename), "w") as f:
        json.dump(exam, f, indent=2)

    entries.append({
        "id": exam["id"],
        "track": track,
        "title": f"{track} Practice Exam",  # display index applied by UI
        "created": exam["created"],
        "questions": exam["config"]["numQuestions"],
        "timeLimitMinutes": exam["config"]["timeLimitMinutes"],
        "file": rel_path,
    })

    # FIFO: expunge oldest until within cap, deleting their files.
    while len(entries) > max_keep:
        oldest = entries.pop(0)
        old_file = os.path.join(ROOT, oldest["file"])
        if os.path.exists(old_file):
            os.remove(old_file)
        print(f"  FIFO: expunged oldest exam {oldest['id']}")

    manifest[track] = entries
    save_manifest(manifest)
    return rel_path, len(entries)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a practice exam.")
    parser.add_argument("track", choices=list(TRACKS.keys()),
                        help="Exam track: FM or P")
    parser.add_argument("--max", type=int, default=MAX_KEEP,
                        help="Max exams to keep per track (default 10)")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducible output (testing only)")
    parser.add_argument("--source", choices=["auto", "bedrock", "template"],
                        default=os.environ.get("EXAM_SOURCE", "auto"),
                        help="Problem source: auto (LLM with template fallback, "
                             "default), bedrock (LLM only), or template (offline)")
    parser.add_argument("--model", default=None,
                        help="Override Bedrock model id (else BEDROCK_MODEL_ID/.env)")
    parser.add_argument("--region", default=None,
                        help="Override AWS region (else AWS_REGION/.env)")
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)

    # Set up Bedrock unless the user forced templates.
    client = None
    if args.source in ("auto", "bedrock"):
        try:
            from bedrock_client import BedrockClient, BedrockUnavailable
            client = BedrockClient(region=args.region, model_id=args.model)
            client.ping()
            print(f"  Bedrock ready: {client.model_id} @ {client.region}")
        except Exception as e:
            if args.source == "bedrock":
                print(f"ERROR: Bedrock is required but unavailable: {e}")
                return 2
            print(f"  Bedrock unavailable ({str(e)[:80]}); using templates.")
            client = None

    effective_source = args.source
    if args.source in ("auto", "bedrock") and client is None:
        effective_source = "template"

    print(f"Generating a {args.track} ({TRACKS[args.track]['name']}) practice "
          f"exam [source: {effective_source}]...")
    exam = build_exam(args.track, rng, source=effective_source, client=client)
    rel_path, count = persist(exam, args.max)

    print(f"  Created {len(exam['questions'])} questions "
          f"({exam.get('llmQuestions', 0)} LLM-authored, "
          f"{len(exam['questions']) - exam.get('llmQuestions', 0)} template).")
    print(f"  Saved to {rel_path}")
    print(f"  {args.track} library now holds {count} exam(s) (max {args.max}).")
    print("Done. Review the site, then push to main when ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
