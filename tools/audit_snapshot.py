#!/usr/bin/env python3
"""Recompute the published evidence audit without training dependencies."""

import argparse
import collections
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def replay_counts(paths):
    counts = collections.Counter()
    for path in paths:
        for row in read_rows(path):
            eligible = row["v2_positive_eligible"].lower() == "true"
            positive = float(row["grpo_final_advantage"]) > 0
            counts["rows"] += 1
            counts["eligible"] += eligible
            counts["positive_advantage"] += positive
            counts["blocked_positive"] += not eligible and positive
            counts["plain_solved_guided_unsolved"] += (
                row.get("v2_plain_solved_guided_unsolved", "").lower() == "true"
            )
    return dict(counts)


def collect_audit():
    published = ROOT / "published"
    manifest = read_rows(published / "analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv")
    validation = read_rows(published / "analysis/echosat_symmetry_grpo_v1_4_strictbest_val_manifest.csv")
    training = [row for row in manifest if row["split"] == "train"]
    overlap = {}
    for field in ("instance_id", "base_instance_id", "formula_equivalence_group"):
        train_values = {row[field] for row in training if row.get(field)}
        val_values = {row[field] for row in validation if row.get(field)}
        overlap[field] = {
            "validation_unique": len(val_values),
            "train_overlap": len(train_values & val_values),
        }
    replay_paths = sorted((published / "stage5/reward_replay").glob("*_solver_stats.csv"))
    if len(replay_paths) != 20:
        raise ValueError(f"Expected 20 Stage 5 replay files, found {len(replay_paths)}")
    return {
        "stage4": replay_counts([published / "stage4/iter=000000_solver_stats.csv"]),
        "stage5": replay_counts(replay_paths),
        "stage5_replay_files": len(replay_paths),
        "canonical_split_rows": dict(collections.Counter(row["split"] for row in manifest)),
        "regression_overlap": overlap,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Refresh the derived audit JSON")
    args = parser.parse_args()
    result = collect_audit()
    output = ROOT / "published/snapshot_audit.json"
    if args.write:
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif json.loads(output.read_text(encoding="utf-8")) != result:
        raise SystemExit("Published audit differs from included raw evidence")
    if result["stage4"]["blocked_positive"] or result["stage5"]["blocked_positive"]:
        raise SystemExit("Blocked-positive invariant failed")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
