#!/usr/bin/env python3
"""Audit plain-vs-weighted Glucose path on guided-loss symmetry instances."""

from __future__ import annotations

import argparse
import math
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.solving.solver import stdout_to_results_dict


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_stress_manifest.csv"
DEFAULT_OUT = ROOT / "runs/analysis/symmetry_weighted_glucose_path_audit.csv"
DEFAULT_BY_BASE = ROOT / "runs/analysis/symmetry_weighted_glucose_path_audit_by_base.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_weighted_glucose_path_audit.md"
PLAIN_BIN = ROOT / "solvers/glucose/simp/glucose_static"
WEIGHTED_BIN = ROOT / "solvers/glucose_weighted/simp/glucose_static"
DEFAULT_BASE_INSTANCES = (
    "dominating_set_hex_4x5_s5",
    "vertex_cover_torus_4x5_norat",
)


@dataclass(frozen=True)
class Probe:
    method: str
    binary_kind: str
    weight_mode: str
    weight_value: float | None
    description: str

    @property
    def binary_path(self) -> Path:
        return PLAIN_BIN if self.binary_kind == "plain" else WEIGHTED_BIN


PROBES = (
    Probe(
        method="plain_glucose_no_weight",
        binary_kind="plain",
        weight_mode="none",
        weight_value=None,
        description="Plain Glucose binary with the original DIMACS input.",
    ),
    Probe(
        method="plain_glucose_pos_weight_comment",
        binary_kind="plain",
        weight_mode="all_pos_comment",
        weight_value=1.0,
        description="Plain Glucose binary with a c weight all +1.0 comment line, which plain Glucose ignores.",
    ),
    Probe(
        method="weighted_glucose_no_weight",
        binary_kind="weighted",
        weight_mode="none",
        weight_value=None,
        description="Weighted Glucose binary with the original DIMACS input and no c weight line.",
    ),
    Probe(
        method="weighted_glucose_all_pos_weight",
        binary_kind="weighted",
        weight_mode="all_pos_weight",
        weight_value=1.0,
        description="Weighted Glucose binary with the current neutral baseline input: all +1.0 weights.",
    ),
    Probe(
        method="weighted_glucose_all_neg_weight",
        binary_kind="weighted",
        weight_mode="all_neg_weight",
        weight_value=-1.0,
        description="Weighted Glucose binary with all -1.0 weights, matching the default Glucose polarity sign in the weighted parser.",
    ),
)


def resolve_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return ROOT / path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def add_weight_line(dimacs: str, num_vars: int, weight_value: float) -> str:
    weight_line = "c weight " + " ".join(f"{float(weight_value):.4f}" for _ in range(int(num_vars)))
    out: list[str] = []
    inserted = False
    for line in dimacs.splitlines():
        out.append(line)
        if not inserted and line.lstrip().startswith("p cnf"):
            out.append(weight_line)
            inserted = True
    if not inserted:
        raise ValueError("Could not find p cnf line while adding weight line")
    return "\n".join(out) + "\n"


def dimacs_for_probe(cnf_path: Path, num_vars: int, probe: Probe) -> tuple[str, bool]:
    dimacs = read_text(cnf_path)
    if probe.weight_value is None:
        return dimacs, False
    return add_weight_line(dimacs, num_vars=num_vars, weight_value=float(probe.weight_value)), True


def clean_number(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def result_value(stats: dict[str, Any]) -> str:
    result = str(stats.get("Result", "UNKNOWN"))
    return result if result else "UNKNOWN"


def is_solved(result: str) -> bool:
    return result in {"SATISFIABLE", "UNSATISFIABLE"}


def selected_stdout_lines(stdout: str) -> str:
    keep_prefixes = (
        "c |  Number of variables:",
        "c |  Number of clauses:",
        "c |  Parse time:",
        "c |  Simplification time:",
        "Solved by simplification",
        "c restarts",
        "c conflicts",
        "c decisions",
        "c propagations",
        "c CPU time",
        "s ",
    )
    lines = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if line.startswith(keep_prefixes):
            lines.append(line)
    return " ; ".join(lines)


def count_weight_echo_lines(stdout: str) -> int:
    count = 0
    for line in stdout.splitlines():
        text = line.strip()
        try:
            float(text)
        except ValueError:
            continue
        count += 1
    return count


def run_probe(
    *,
    instance: pd.Series,
    probe: Probe,
    repeat_id: int,
    seed: int,
    cpu_lim: float,
    rnd_freq: float,
    k_value: float,
) -> dict[str, Any]:
    cnf_path = Path(str(instance["cnf_path"]))
    dimacs, weight_line_present = dimacs_for_probe(
        cnf_path=cnf_path,
        num_vars=int(instance["num_vars"]),
        probe=probe,
    )
    call = [
        str(probe.binary_path),
        f"-rnd-seed={int(seed)}",
        f"-cpu-lim={int(cpu_lim)}",
        f"-rnd-freq={float(rnd_freq)}",
        f"-K={float(k_value)}",
    ]
    start = time.perf_counter()
    with tempfile.TemporaryFile(mode="w+") as tmp:
        tmp.write(dimacs)
        tmp.seek(0)
        result = subprocess.run(
            call,
            stdin=tmp,
            capture_output=True,
            text=True,
            timeout=max(30.0, float(cpu_lim) + 20.0),
        )
    wall = time.perf_counter() - start
    stats = stdout_to_results_dict(result.stdout)
    final_result = result_value(stats)
    return {
        "repeat_id": int(repeat_id),
        "seed": int(seed),
        "family": str(instance["family"]),
        "base_instance_id": str(instance["base_instance_id"]),
        "instance_id": str(instance["instance_id"]),
        "variant": str(instance["variant"]),
        "expected_result": str(instance["expected_result"]),
        "num_vars": int(instance["num_vars"]),
        "num_clauses": int(instance["num_clauses"]),
        "cnf_path": str(cnf_path),
        "method": probe.method,
        "binary_kind": probe.binary_kind,
        "binary_path": str(probe.binary_path),
        "weight_mode": probe.weight_mode,
        "weight_value": "" if probe.weight_value is None else float(probe.weight_value),
        "weight_line_present": bool(weight_line_present),
        "cpu_lim": float(cpu_lim),
        "rnd_freq": float(rnd_freq),
        "K": float(k_value),
        "result": final_result,
        "solved": bool(is_solved(final_result)),
        "expected_match": bool(str(instance["expected_result"]) == final_result)
        if str(instance["expected_result"]) in {"SATISFIABLE", "UNSATISFIABLE"}
        else False,
        "known_expected": bool(str(instance["expected_result"]) in {"SATISFIABLE", "UNSATISFIABLE"}),
        "cpu_time": clean_number(stats.get("CPU time")),
        "wall_time": float(wall),
        "decisions": clean_number(stats.get("decisions")),
        "conflicts": clean_number(stats.get("conflicts")),
        "propagations": clean_number(stats.get("propagations")),
        "restarts": clean_number(stats.get("restarts")),
        "returncode": int(result.returncode),
        "stdout_bytes": len(result.stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(result.stderr.encode("utf-8", errors="replace")),
        "weight_echo_lines": int(count_weight_echo_lines(result.stdout)),
        "solved_by_simplification": bool("Solved by simplification" in result.stdout),
        "stdout_key_lines": selected_stdout_lines(result.stdout),
        "stderr": result.stderr.strip()[:500],
    }


def load_instances(manifest_path: Path, base_instances: list[str], base_only: bool) -> pd.DataFrame:
    manifest = pd.read_csv(manifest_path)
    manifest = manifest[manifest["base_instance_id"].astype(str).isin(set(base_instances))].copy()
    if "event_audit_role" in manifest.columns:
        manifest = manifest[manifest["event_audit_role"].fillna("event").astype(str) != "static_only"].copy()
    if base_only:
        manifest = manifest[manifest["variant"].astype(str) == "base"].copy()
    if manifest.empty:
        raise ValueError("No manifest rows selected for weighted Glucose path audit")
    manifest["cnf_path"] = manifest["cnf_path"].map(lambda value: str(resolve_path(value).resolve()))
    return manifest.sort_values(["family", "base_instance_id", "variant", "instance_id"]).reset_index(drop=True)


def consistency(values: pd.Series) -> bool:
    return int(values.nunique(dropna=False)) <= 1


def summarize_by_base(rows: pd.DataFrame) -> pd.DataFrame:
    grouped = rows.groupby(["family", "base_instance_id", "method"], sort=True)
    summary = grouped.agg(
        rows=("result", "count"),
        repeats=("repeat_id", "nunique"),
        variants=("variant", "nunique"),
        solved_rows=("solved", lambda values: int(pd.Series(values).astype(bool).sum())),
        expected_match_rows=("expected_match", lambda values: int(pd.Series(values).astype(bool).sum())),
        known_expected_rows=("known_expected", lambda values: int(pd.Series(values).astype(bool).sum())),
        sat_rows=("result", lambda values: int((pd.Series(values) == "SATISFIABLE").sum())),
        unsat_rows=("result", lambda values: int((pd.Series(values) == "UNSATISFIABLE").sum())),
        indeterminate_rows=("result", lambda values: int((pd.Series(values) == "INDETERMINATE").sum())),
        mean_cpu_time=("cpu_time", "mean"),
        mean_wall_time=("wall_time", "mean"),
        mean_decisions=("decisions", "mean"),
        mean_conflicts=("conflicts", "mean"),
        weight_echo_lines_mean=("weight_echo_lines", "mean"),
        result_consistent=("result", consistency),
    ).reset_index()

    method_order = {probe.method: i for i, probe in enumerate(PROBES)}
    summary["_method_order"] = summary["method"].map(method_order).fillna(999).astype(int)
    return summary.sort_values(["family", "base_instance_id", "_method_order"]).drop(columns=["_method_order"])


def infer_base_attribution(summary: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for (family, base_id), group in summary.groupby(["family", "base_instance_id"], sort=True):
        by_method = {str(row["method"]): row for _, row in group.iterrows()}

        def solved(method: str) -> bool:
            row = by_method.get(method)
            return bool(row is not None and int(row["solved_rows"]) == int(row["rows"]))

        plain = solved("plain_glucose_no_weight")
        plain_comment = solved("plain_glucose_pos_weight_comment")
        weighted_no = solved("weighted_glucose_no_weight")
        weighted_pos = solved("weighted_glucose_all_pos_weight")
        weighted_neg = solved("weighted_glucose_all_neg_weight")

        if not plain:
            attribution = "plain_unsolved_control"
        elif not plain_comment:
            attribution = "weight_comment_input_unexpected"
        elif not weighted_no:
            attribution = "weighted_binary_core_path"
        elif not weighted_neg and not weighted_pos:
            attribution = "weighted_c_weight_activity_path"
        elif weighted_neg and not weighted_pos:
            attribution = "all_positive_weight_phase_or_polarity"
        elif weighted_no and weighted_pos and weighted_neg:
            attribution = "weighted_path_loss_not_reproduced"
        else:
            attribution = "mixed_or_variant_dependent"

        records.append(
            {
                "family": family,
                "base_instance_id": base_id,
                "primary_weighted_path_attribution": attribution,
                "plain_all_solved": plain,
                "plain_pos_comment_all_solved": plain_comment,
                "weighted_no_weight_all_solved": weighted_no,
                "weighted_all_pos_all_solved": weighted_pos,
                "weighted_all_neg_all_solved": weighted_neg,
            }
        )
    return pd.DataFrame.from_records(records)


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> list[str]:
    if frame.empty:
        return ["(empty)"]
    view = frame.loc[:, columns].copy()
    if max_rows is not None:
        view = view.head(max_rows)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        values = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(
    *,
    doc_path: Path,
    rows: pd.DataFrame,
    summary: pd.DataFrame,
    attribution: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    lines: list[str] = []
    lines.append("# Weighted Glucose Path Audit")
    lines.append("")
    lines.append("This audit diagnoses the guided-loss rows from the symmetry solver protocol preflight.")
    lines.append("It is not a solver speedup claim. It separates the weighted binary path from the `c weight` input path and from the all-positive neutral phase convention.")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- manifest: `{resolve_path(args.manifest).resolve()}`")
    lines.append(f"- repeats: `{int(args.repeats)}`")
    lines.append(f"- seed base: `{int(args.seed)}`")
    lines.append(f"- cpu limit: `{float(args.cpu_lim)}`")
    lines.append(f"- selected base instances: `{', '.join(args.base_instances)}`")
    lines.append("")
    lines.append("## Probes")
    lines.append("")
    for probe in PROBES:
        lines.append(f"- `{probe.method}`: {probe.description}")
    lines.append("")
    lines.append("Note: in `solvers/glucose_weighted/core/Dimacs.h`, a positive `c weight` entry calls `newVar(false, ...)`, while a negative entry calls `newVar(true, ...)`. The unweighted Glucose parser creates variables with the default `newVar(true)` polarity. Therefore all `+1.0` is a uniform phase baseline, but it is not the default Glucose polarity baseline.")
    lines.append("")
    lines.append("## Base Attribution")
    lines.append("")
    lines.extend(markdown_table(attribution, list(attribution.columns)))
    lines.append("")
    lines.append("## Method Summary")
    lines.append("")
    summary_cols = [
        "family",
        "base_instance_id",
        "method",
        "rows",
        "solved_rows",
        "indeterminate_rows",
        "mean_cpu_time",
        "mean_decisions",
        "mean_conflicts",
        "weight_echo_lines_mean",
        "result_consistent",
    ]
    lines.extend(markdown_table(summary, summary_cols))
    lines.append("")
    lines.append("## Per-Variant Rows")
    lines.append("")
    row_cols = [
        "repeat_id",
        "family",
        "base_instance_id",
        "variant",
        "method",
        "result",
        "cpu_time",
        "decisions",
        "conflicts",
        "weight_echo_lines",
    ]
    lines.extend(markdown_table(rows, row_cols, max_rows=80))
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- If `plain_glucose_pos_weight_comment` matches `plain_glucose_no_weight`, the literal comment line itself is harmless for plain Glucose.")
    lines.append("- If `weighted_glucose_no_weight` matches plain Glucose, the weighted binary without parsed weights is not the observed loss source.")
    lines.append("- If `weighted_glucose_all_neg_weight` solves but `weighted_glucose_all_pos_weight` loses, the current all-positive neutral baseline is exposing a phase/polarity convention problem rather than adapter delta.")
    lines.append("- If all weighted probes solve on the selected loss cases, the previous weighted-path loss is not reproduced by the current binary.")
    lines.append("- If all weighted probes lose, the next target is the weighted binary core/preprocessing path.")
    lines.append("")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit weighted Glucose path on symmetry guided-loss instances.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--by-base-csv", type=Path, default=DEFAULT_BY_BASE)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--base-instances", nargs="*", default=list(DEFAULT_BASE_INSTANCES))
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--cpu-lim", type=float, default=5.0)
    parser.add_argument("--rnd-freq", type=float, default=0.0)
    parser.add_argument("--K", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = resolve_path(args.manifest).resolve()
    out_csv = resolve_path(args.out_csv)
    by_base_csv = resolve_path(args.by_base_csv)
    doc_path = resolve_path(args.doc)
    instances = load_instances(manifest_path, list(args.base_instances), base_only=bool(args.base_only))
    print(f"selected {len(instances)} CNFs across {instances['base_instance_id'].nunique()} base instances")

    records: list[dict[str, Any]] = []
    repeats = max(1, int(args.repeats))
    for repeat_id in range(repeats):
        seed = int(args.seed) + repeat_id
        print(f"repeat {repeat_id + 1}/{repeats}: seed={seed}")
        for _, instance in instances.iterrows():
            for probe in PROBES:
                row = run_probe(
                    instance=instance,
                    probe=probe,
                    repeat_id=repeat_id,
                    seed=seed,
                    cpu_lim=float(args.cpu_lim),
                    rnd_freq=float(args.rnd_freq),
                    k_value=float(args.K),
                )
                records.append(row)
                print(
                    f"  {row['base_instance_id']} {row['variant']} {row['method']} -> "
                    f"{row['result']} decisions={row['decisions']:.0f} conflicts={row['conflicts']:.0f}"
                )

    rows = pd.DataFrame.from_records(records)
    summary = summarize_by_base(rows)
    attribution = infer_base_attribution(summary)
    summary = summary.merge(attribution, on=["family", "base_instance_id"], how="left")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(out_csv, index=False)
    by_base_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(by_base_csv, index=False)
    write_doc(doc_path=doc_path, rows=rows, summary=summary, attribution=attribution, args=args)
    print(f"wrote {len(rows)} rows to {out_csv}")
    print(f"wrote {len(summary)} summary rows to {by_base_csv}")
    print(f"wrote report to {doc_path}")


if __name__ == "__main__":
    main()
