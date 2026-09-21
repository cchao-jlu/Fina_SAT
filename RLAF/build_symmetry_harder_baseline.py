from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd

from build_symmetry_stress_dataset import (
    benchmark_role,
    control_type,
    event_audit_role,
    scale_key,
    scale_label,
    symmetry_strength,
)
from src.data.symmetry import (
    SAT,
    UNSAT,
    SymmetryCNF,
    complete_graph_coloring_cnf,
    complete_graph_tseitin_cnf,
    dominating_set_hex_cnf,
    even_colouring_torus_cnf,
    pigeonhole_cnf,
    pigeonhole_with_emergency_exit_cnf,
    random_3sat_control_cnf,
    renamed_variant,
    subset_cardinality_fixed_bandwidth_cnf,
    vertex_cover_torus_cnf,
    write_dimacs,
    write_orbits_json,
)
from src.solving.solver import stdout_to_results_dict


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_ROOT = ROOT / "data/symmetry_harder_baseline"
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_manifest.csv"
DEFAULT_CALIBRATION = ROOT / "runs/analysis/symmetry_harder_baseline_plain_glucose_calibration.csv"
DEFAULT_TARGET_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_target_manifest.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_harder_baseline.md"
DEFAULT_GLUCOSE = ROOT / "solvers/glucose/simp/glucose_static"
SOLVED = {SAT, UNSAT}


def parse_seeds(raw: str) -> list[int]:
    return [int(part.strip()) for part in str(raw).split(",") if part.strip()]


def candidate_instances() -> list[SymmetryCNF]:
    """Harder-than-v2 candidates, avoiding known explosive encodings."""
    instances: list[SymmetryCNF] = []

    for pigeons in range(7, 14):
        holes = pigeons - 1
        instances.append(pigeonhole_cnf(pigeons, holes))
        instances.append(pigeonhole_with_emergency_exit_cnf(pigeons, holes, exit_mode="single"))
        if pigeons <= 11:
            instances.append(pigeonhole_with_emergency_exit_cnf(pigeons, holes, exit_mode="all"))

    for size in (12, 14, 16, 18, 20):
        instances.append(subset_cardinality_fixed_bandwidth_cnf(size))

    for rows, cols in ((3, 6), (3, 7), (3, 8), (4, 5), (4, 6), (5, 4)):
        instances.append(dominating_set_hex_cnf(rows, cols))

    for rows, cols in ((4, 6), (5, 5), (5, 6)):
        instances.append(even_colouring_torus_cnf(rows, cols))

    for rows, cols, cover_size in ((3, 6, 6), (3, 6, 7), (4, 5, 6), (4, 5, 8)):
        instances.append(vertex_cover_torus_cnf(rows, cols, version="event", cover_size=cover_size))

    for vertices in range(6, 12):
        instances.append(complete_graph_coloring_cnf(vertices, vertices - 1))
        instances.append(complete_graph_coloring_cnf(vertices, vertices))

    for vertices in range(7, 11):
        instances.append(complete_graph_tseitin_cnf(vertices, odd_charge=False))
        instances.append(complete_graph_tseitin_cnf(vertices, odd_charge=True))

    seed = 2600
    for num_vars in (80, 100, 120, 140, 160):
        for ratio in (4.10, 4.25, 4.40):
            seed += 1
            instances.append(random_3sat_control_cnf(num_vars, int(round(num_vars * ratio)), seed=seed))
    for num_vars, num_clauses, seed in (
        (180, 760, 3301),
        (220, 928, 3303),
        (220, 942, 3304),
        (260, 1097, 3305),
        (260, 1113, 3306),
        (300, 1266, 3307),
    ):
        instances.append(random_3sat_control_cnf(num_vars, num_clauses, seed=seed))

    unique: dict[str, SymmetryCNF] = {}
    for instance in instances:
        unique.setdefault(instance.instance_id, instance)
    return list(unique.values())


def write_instance(output_root: Path, instance: SymmetryCNF, variant: str, source: str) -> dict[str, object]:
    family_dir = output_root / instance.family
    cnf_path = family_dir / f"{instance.instance_id}.cnf"
    orbits_path = family_dir / f"{instance.instance_id}.orbits.json"
    metadata_path = family_dir / f"{instance.instance_id}.metadata.json"

    write_dimacs(cnf_path, instance.clauses, num_vars=instance.num_vars)
    write_orbits_json(orbits_path, instance.variable_orbits)

    metadata = {
        "family": instance.family,
        "instance_id": instance.instance_id,
        "expected_result": instance.expected_result,
        "num_vars": int(instance.num_vars),
        "num_clauses": int(len(instance.clauses)),
        "variant": variant,
        "base_instance_id": str(instance.metadata.get("base_instance_id", instance.instance_id)),
        "event_audit_role": event_audit_role(instance),
        "symmetry_strength": symmetry_strength(instance),
        "control_type": control_type(instance),
        "scale": scale_label(instance),
        "scale_key": scale_key(instance),
        "benchmark_role": benchmark_role(instance),
        "family_scale": f"{instance.family}:{scale_label(instance)}",
        "variant_role": "base" if variant == "base" else "permutation_variant",
        "permutation_variant": bool(variant != "base"),
        "source": source,
        **instance.metadata,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "family": instance.family,
        "instance_id": instance.instance_id,
        "variant": variant,
        "base_instance_id": str(instance.metadata.get("base_instance_id", instance.instance_id)),
        "expected_result": instance.expected_result,
        "num_vars": int(instance.num_vars),
        "num_clauses": int(len(instance.clauses)),
        "cnf_path": str(cnf_path),
        "orbits_path": str(orbits_path),
        "metadata_path": str(metadata_path),
        "event_audit_role": event_audit_role(instance),
        "symmetry_strength": symmetry_strength(instance),
        "control_type": control_type(instance),
        "scale": scale_label(instance),
        "scale_key": scale_key(instance),
        "benchmark_role": benchmark_role(instance),
        "family_scale": f"{instance.family}:{scale_label(instance)}",
        "variant_role": "base" if variant == "base" else "permutation_variant",
        "permutation_variant": bool(variant != "base"),
        "source": source,
    }


def build_manifest(output_root: Path, perm_seeds: list[int], max_clauses: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    source = "SAT symmetry harder baseline candidate pool"
    for instance in candidate_instances():
        if max_clauses > 0 and len(instance.clauses) > max_clauses:
            continue
        rows.append(write_instance(output_root, instance, variant="base", source=source))
        for seed in perm_seeds:
            rows.append(
                write_instance(
                    output_root,
                    renamed_variant(instance, seed=seed, include_sign_flips=False),
                    variant=f"perm_seed{seed}",
                    source=source,
                )
            )
    return pd.DataFrame(rows).sort_values(["family", "base_instance_id", "variant"]).reset_index(drop=True)


def run_plain_glucose(glucose_bin: Path, cnf_path: Path, cpu_cap: float, external_timeout: float, seed: int) -> dict[str, Any]:
    command = [
        str(glucose_bin),
        f"-cpu-lim={float(cpu_cap):g}",
        f"-rnd-seed={int(seed)}",
        "-verb=1",
        str(cnf_path),
    ]
    start = time.perf_counter()
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=float(external_timeout))
        wall = time.perf_counter() - start
        stats = stdout_to_results_dict(proc.stdout)
        timeout = False
        returncode = int(proc.returncode)
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        wall = time.perf_counter() - start
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stats = stdout_to_results_dict(stdout)
        timeout = True
        returncode = -9

    result = str(stats.get("Result", "INDETERMINATE"))
    return {
        "plain_glucose_result": result,
        "plain_glucose_solved": result in SOLVED,
        "plain_glucose_cpu_time": float(stats.get("CPU time", float("nan"))),
        "plain_glucose_wall_time": float(wall),
        "plain_glucose_decisions": float(stats.get("decisions", float("nan"))),
        "plain_glucose_conflicts": float(stats.get("conflicts", float("nan"))),
        "plain_glucose_propagations": float(stats.get("propagations", float("nan"))),
        "plain_glucose_restarts": float(stats.get("restarts", float("nan"))),
        "plain_glucose_returncode": returncode,
        "plain_glucose_timeout": bool(timeout),
        "plain_glucose_stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "plain_glucose_stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
        "plain_glucose_command": json.dumps(command),
    }


def calibrate_manifest(
    manifest: pd.DataFrame,
    glucose_bin: Path,
    cpu_cap: float,
    external_timeout: float,
    seed: int,
    target_min_cpu: float,
    target_max_cpu: float,
    max_bases: int,
) -> pd.DataFrame:
    base_rows = manifest[manifest["variant"].astype(str).eq("base")].copy()
    if max_bases > 0:
        base_rows = base_rows.head(int(max_bases)).copy()
    rows: list[dict[str, object]] = []
    for index, row in base_rows.reset_index(drop=True).iterrows():
        cnf_path = Path(str(row["cnf_path"]))
        print(f"calibrating {index + 1}/{len(base_rows)} {row['base_instance_id']} clauses={row['num_clauses']}")
        result = run_plain_glucose(
            glucose_bin=glucose_bin,
            cnf_path=cnf_path,
            cpu_cap=cpu_cap,
            external_timeout=external_timeout,
            seed=seed,
        )
        cpu = float(result["plain_glucose_cpu_time"])
        solved = bool(result["plain_glucose_solved"])
        if not solved:
            band = "timeout_or_indeterminate"
        elif cpu < float(target_min_cpu):
            band = "too_easy"
        elif cpu <= float(target_max_cpu):
            band = "target_harder_baseline"
        else:
            band = "too_hard_above_target"
        rows.append(
            {
                **{column: row[column] for column in manifest.columns},
                **result,
                "difficulty_band": band,
                "target_min_cpu": float(target_min_cpu),
                "target_max_cpu": float(target_max_cpu),
                "calibration_cpu_cap": float(cpu_cap),
                "calibration_seed": int(seed),
            }
        )
    return pd.DataFrame(rows)


def target_manifest(manifest: pd.DataFrame, calibration: pd.DataFrame) -> pd.DataFrame:
    targets = set(
        calibration.loc[
            calibration["difficulty_band"].astype(str).eq("target_harder_baseline"),
            "base_instance_id",
        ].astype(str)
    )
    out = manifest[manifest["base_instance_id"].astype(str).isin(targets)].copy()
    if out.empty:
        return out
    calibration_cols = [
        "base_instance_id",
        "plain_glucose_result",
        "plain_glucose_solved",
        "plain_glucose_cpu_time",
        "plain_glucose_wall_time",
        "plain_glucose_decisions",
        "plain_glucose_conflicts",
        "difficulty_band",
        "calibration_cpu_cap",
        "calibration_seed",
    ]
    return out.merge(calibration[calibration_cols], on="base_instance_id", how="left")


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame[columns].head(max_rows).copy()
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in view.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.6g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_doc(path: Path, manifest: pd.DataFrame, calibration: pd.DataFrame, target: pd.DataFrame) -> None:
    base_count = int(manifest["base_instance_id"].nunique()) if not manifest.empty else 0
    target_bases = int(target["base_instance_id"].nunique()) if not target.empty else 0
    family_summary = (
        manifest.groupby(["family", "control_type"], sort=True)
        .agg(base_instances=("base_instance_id", "nunique"), rows=("instance_id", "count"), max_clauses=("num_clauses", "max"))
        .reset_index()
    )
    band_summary = (
        calibration.groupby(["difficulty_band", "family"], sort=True)
        .agg(base_instances=("base_instance_id", "nunique"), mean_cpu=("plain_glucose_cpu_time", "mean"), median_cpu=("plain_glucose_cpu_time", "median"))
        .reset_index()
        if not calibration.empty
        else pd.DataFrame()
    )
    target_view = (
        calibration[calibration["difficulty_band"].astype(str).eq("target_harder_baseline")]
        .sort_values(["plain_glucose_cpu_time", "family", "base_instance_id"])
        if not calibration.empty
        else pd.DataFrame()
    )

    lines = [
        "# SAT Symmetry Harder Baseline",
        "",
        "This dataset is a harder baseline candidate pool for comparing SAT symmetry checkpoints against plain Glucose. It is separate from v1/v2 and GRPO training artifacts.",
        "",
        "The target subset is selected by base-instance plain Glucose calibration. Permutation variants are included only after a base enters the target band.",
        "",
        "## Outputs",
        "",
        "- full manifest: `runs/analysis/symmetry_harder_baseline_manifest.csv`",
        "- base calibration: `runs/analysis/symmetry_harder_baseline_plain_glucose_calibration.csv`",
        "- target manifest: `runs/analysis/symmetry_harder_baseline_target_manifest.csv`",
        "",
        "## Headline",
        "",
        f"- full base instances: {base_count}",
        f"- full manifest rows: {len(manifest)}",
        f"- target base instances: {target_bases}",
        f"- target manifest rows: {len(target)}",
        "",
        "The target band is not a speedup claim. It only identifies instances where plain Glucose is not trivially fast and is still solved under the calibration cap.",
        "",
        "## Full Candidate Summary",
        "",
        *markdown_table(family_summary, ["family", "control_type", "base_instances", "rows", "max_clauses"], max_rows=60),
        "",
        "## Calibration Bands",
        "",
        *markdown_table(band_summary, ["difficulty_band", "family", "base_instances", "mean_cpu", "median_cpu"], max_rows=80),
        "",
        "## Target Bases",
        "",
        *markdown_table(
            target_view,
            ["family", "base_instance_id", "expected_result", "num_vars", "num_clauses", "plain_glucose_result", "plain_glucose_cpu_time", "plain_glucose_decisions", "plain_glucose_conflicts"],
            max_rows=80,
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and calibrate a harder SAT symmetry baseline.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--calibration-csv", type=Path, default=DEFAULT_CALIBRATION)
    parser.add_argument("--target-manifest", type=Path, default=DEFAULT_TARGET_MANIFEST)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--perm-seeds", default="1730,1731")
    parser.add_argument("--max-clauses", type=int, default=300_000)
    parser.add_argument("--glucose-bin", type=Path, default=DEFAULT_GLUCOSE)
    parser.add_argument("--calibration-cpu-cap", type=float, default=10.0)
    parser.add_argument("--external-timeout", type=float, default=20.0)
    parser.add_argument("--calibration-seed", type=int, default=1)
    parser.add_argument("--target-min-cpu", type=float, default=0.05)
    parser.add_argument("--target-max-cpu", type=float, default=10.0)
    parser.add_argument("--max-calibration-bases", type=int, default=0)
    parser.add_argument("--skip-calibration", action="store_true")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    manifest = build_manifest(
        output_root=output_root,
        perm_seeds=parse_seeds(args.perm_seeds),
        max_clauses=int(args.max_clauses),
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.manifest, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"wrote {args.manifest} rows={len(manifest)} bases={manifest['base_instance_id'].nunique()}")

    calibration = pd.DataFrame()
    target = pd.DataFrame()
    if not bool(args.skip_calibration):
        calibration = calibrate_manifest(
            manifest=manifest,
            glucose_bin=args.glucose_bin.resolve(),
            cpu_cap=float(args.calibration_cpu_cap),
            external_timeout=float(args.external_timeout),
            seed=int(args.calibration_seed),
            target_min_cpu=float(args.target_min_cpu),
            target_max_cpu=float(args.target_max_cpu),
            max_bases=int(args.max_calibration_bases),
        )
        args.calibration_csv.parent.mkdir(parents=True, exist_ok=True)
        calibration.to_csv(args.calibration_csv, index=False)
        print(f"wrote {args.calibration_csv} rows={len(calibration)}")
        target = target_manifest(manifest, calibration)
        args.target_manifest.parent.mkdir(parents=True, exist_ok=True)
        target.to_csv(args.target_manifest, index=False)
        print(f"wrote {args.target_manifest} rows={len(target)} bases={target['base_instance_id'].nunique() if not target.empty else 0}")

    write_doc(args.doc, manifest=manifest, calibration=calibration, target=target)
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
