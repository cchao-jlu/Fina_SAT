from __future__ import annotations

import argparse
import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_target_manifest.csv"
DEFAULT_OBSERVATIONS = ROOT / "runs/analysis/echosat_adapter_delta_v2_iter235_low_warmup_sweep_observations.csv"
DEFAULT_HASH_ROWS = ROOT / "runs/analysis/echosat_formula_equivalence_v1_hash_rows.csv"
DEFAULT_CLASSES = ROOT / "runs/analysis/echosat_formula_equivalence_v1_classes.csv"
DEFAULT_RUNTIME_PAIRS = ROOT / "runs/analysis/echosat_formula_equivalence_v1_runtime_pairs.csv"
DEFAULT_DOC = ROOT / "docs/echosat_formula_equivalence_audit_v1.md"


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def digest_blob(value: Any) -> str:
    return hashlib.sha256(repr(value).encode("utf-8")).hexdigest()


def parse_dimacs(path: Path) -> dict[str, Any]:
    file_bytes = path.read_bytes()
    clauses: list[tuple[int, ...]] = []
    num_vars = math.nan
    num_clauses = math.nan
    header = ""
    for raw_line in file_bytes.decode("utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            parts = line.split()
            if len(parts) >= 4:
                header = " ".join(parts[:4])
                num_vars = int(parts[2])
                num_clauses = int(parts[3])
            continue
        lits = tuple(int(part) for part in line.split() if part != "0")
        if lits:
            clauses.append(lits)
    normalized_clauses = [tuple(sorted(clause, key=lambda lit: (abs(lit), lit < 0))) for clause in clauses]
    clause_length_hist = Counter(len(clause) for clause in clauses)
    return {
        "cnf_path": str(path),
        "file_sha256": hashlib.sha256(file_bytes).hexdigest(),
        "ordered_dimacs_sha256": digest_blob((header, clauses)),
        "unordered_formula_sha256": digest_blob((header, sorted(normalized_clauses))),
        "parsed_num_vars": num_vars,
        "parsed_num_clauses": num_clauses,
        "parsed_clause_rows": len(clauses),
        "clause_length_hist": ";".join(f"{length}:{count}" for length, count in sorted(clause_length_hist.items())),
    }


def manifest_hash_rows(manifest: pd.DataFrame) -> pd.DataFrame:
    if "cnf_path" not in manifest.columns:
        raise ValueError("manifest is missing cnf_path")
    rows: list[dict[str, Any]] = []
    for _, row in manifest.iterrows():
        path = resolve(str(row["cnf_path"]))
        if not path.exists():
            raise FileNotFoundError(path)
        parsed = parse_dimacs(path)
        rows.append(
            {
                "family": row.get("family", ""),
                "instance_id": row.get("instance_id", ""),
                "variant": row.get("variant", ""),
                "base_instance_id": row.get("base_instance_id", ""),
                "expected_result": row.get("expected_result", ""),
                "num_vars": row.get("num_vars", math.nan),
                "num_clauses": row.get("num_clauses", math.nan),
                "control_type": row.get("control_type", ""),
                "scale": row.get("scale", ""),
                "scale_key": row.get("scale_key", ""),
                "benchmark_role": row.get("benchmark_role", ""),
                "variant_role": row.get("variant_role", ""),
                **parsed,
            }
        )
    return pd.DataFrame(rows)


def equivalence_classes(hash_rows: pd.DataFrame) -> pd.DataFrame:
    grouped = hash_rows.groupby(["unordered_formula_sha256", "parsed_num_vars", "parsed_num_clauses"], sort=True)
    rows = []
    for key, group in grouped:
        families = sorted(set(group["family"].astype(str)))
        rows.append(
            {
                "unordered_formula_sha256": key[0],
                "parsed_num_vars": key[1],
                "parsed_num_clauses": key[2],
                "rows": int(len(group)),
                "families": ",".join(families),
                "family_count": int(len(families)),
                "base_instances": ",".join(sorted(set(group["base_instance_id"].astype(str)))),
                "instances": ",".join(sorted(set(group["instance_id"].astype(str)))),
                "variants": ",".join(sorted(set(group["variant"].astype(str)))),
                "file_hash_count": int(group["file_sha256"].nunique()),
                "ordered_hash_count": int(group["ordered_dimacs_sha256"].nunique()),
                "clause_length_hist": str(group["clause_length_hist"].iloc[0]),
            }
        )
    return pd.DataFrame(rows).sort_values(["family_count", "rows", "parsed_num_vars"], ascending=[False, False, True])


def aggregate_runtime(observations: pd.DataFrame) -> pd.DataFrame:
    required = {
        "warmup_conflicts",
        "family",
        "instance_id",
        "base_instance_id",
        "variant",
        "repeat_id",
        "plain_unguided_glucose_final_cpu_time",
        "event_adapter_final_final_cpu_time",
        "event_adapter_final_protocol_accounted_time",
        "adapter_cached_final_cpu_delta",
        "adapter_plain_protocol_delta",
        "neutral_plain_final_cpu_delta",
        "static_neutral_final_cpu_delta",
        "event_state_l2_sum",
        "warmup_decisions",
    }
    missing = sorted(required.difference(observations.columns))
    if missing:
        raise ValueError(f"observations missing required columns: {missing}")
    return observations.copy()


def runtime_equivalence_pairs(hash_rows: pd.DataFrame, observations: pd.DataFrame) -> pd.DataFrame:
    runtime = aggregate_runtime(observations)
    joined = runtime.merge(
        hash_rows[
            [
                "family",
                "instance_id",
                "base_instance_id",
                "variant",
                "unordered_formula_sha256",
                "ordered_dimacs_sha256",
                "file_sha256",
                "parsed_num_vars",
                "parsed_num_clauses",
            ]
        ],
        on=["family", "instance_id", "base_instance_id", "variant"],
        how="left",
        validate="many_to_one",
    )
    if joined["unordered_formula_sha256"].isna().any():
        missing = joined[joined["unordered_formula_sha256"].isna()][["family", "instance_id"]].drop_duplicates()
        raise ValueError(f"runtime rows missing manifest hashes: {missing.to_dict(orient='records')[:10]}")
    rows = []
    pair_key_columns = ["unordered_formula_sha256", "warmup_conflicts", "variant", "repeat_id"]
    for _, group in joined.groupby(pair_key_columns, sort=True):
        families = set(group["family"].astype(str))
        if not {"complete_coloring", "php"}.issubset(families):
            continue
        complete = group[group["family"].astype(str) == "complete_coloring"].sort_values("instance_id")
        php = group[group["family"].astype(str) == "php"].sort_values("instance_id")
        for _, complete_row in complete.iterrows():
            for _, php_row in php.iterrows():
                if int(complete_row["parsed_num_vars"]) != int(php_row["parsed_num_vars"]):
                    continue
                if int(complete_row["parsed_num_clauses"]) != int(php_row["parsed_num_clauses"]):
                    continue
                row = {
                    "unordered_formula_sha256": complete_row["unordered_formula_sha256"],
                    "warmup_conflicts": int(complete_row["warmup_conflicts"]),
                    "variant": complete_row["variant"],
                    "repeat_id": int(complete_row["repeat_id"]),
                    "complete_instance_id": complete_row["instance_id"],
                    "php_instance_id": php_row["instance_id"],
                    "parsed_num_vars": int(complete_row["parsed_num_vars"]),
                    "parsed_num_clauses": int(complete_row["parsed_num_clauses"]),
                    "same_unordered_formula": bool(
                        complete_row["unordered_formula_sha256"] == php_row["unordered_formula_sha256"]
                    ),
                    "same_ordered_dimacs": bool(complete_row["ordered_dimacs_sha256"] == php_row["ordered_dimacs_sha256"]),
                    "same_file_sha256": bool(complete_row["file_sha256"] == php_row["file_sha256"]),
                }
                metric_columns = [
                    "plain_unguided_glucose_final_cpu_time",
                    "event_adapter_final_final_cpu_time",
                    "event_adapter_final_protocol_accounted_time",
                    "adapter_cached_final_cpu_delta",
                    "adapter_plain_protocol_delta",
                    "neutral_plain_final_cpu_delta",
                    "static_neutral_final_cpu_delta",
                    "event_state_l2_sum",
                    "warmup_decisions",
                ]
                for column in metric_columns:
                    row[f"complete_{column}"] = complete_row[column]
                    row[f"php_{column}"] = php_row[column]
                    row[f"complete_minus_php_{column}"] = complete_row[column] - php_row[column]
                rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["warmup_conflicts", "parsed_num_vars", "variant", "repeat_id"],
        ignore_index=True,
    )


def markdown_table(frame: pd.DataFrame, max_rows: int = 40) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    view = frame.head(max_rows).copy()
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(f"{value:.6g}" if math.isfinite(value) else "nan")
            else:
                text = str(value)
                cells.append(text[:120] + "..." if len(text) > 120 else text)
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_doc(
    path: Path,
    *,
    classes: pd.DataFrame,
    pairs: pd.DataFrame,
    hash_csv: Path,
    classes_csv: Path,
    pairs_csv: Path,
) -> None:
    cross_family = classes[classes["family_count"] > 1].copy()
    pair_summary = pd.DataFrame()
    if not pairs.empty:
        pair_summary = (
            pairs.groupby(["warmup_conflicts", "parsed_num_vars", "parsed_num_clauses"], sort=True)
            .agg(
                pairs=("repeat_id", "size"),
                same_unordered_formula=("same_unordered_formula", "all"),
                same_ordered_dimacs_fraction=("same_ordered_dimacs", "mean"),
                complete_minus_php_adapter_cached_delta_mean=(
                    "complete_minus_php_adapter_cached_final_cpu_delta",
                    "mean",
                ),
                complete_minus_php_adapter_plain_protocol_delta_mean=(
                    "complete_minus_php_adapter_plain_protocol_delta",
                    "mean",
                ),
                complete_minus_php_plain_cpu_mean=("complete_minus_php_plain_unguided_glucose_final_cpu_time", "mean"),
                complete_minus_php_event_l2_mean=("complete_minus_php_event_state_l2_sum", "mean"),
            )
            .reset_index()
        )
    lines = [
        "# EchoSAT Formula Equivalence Audit v1",
        "",
        "This audit checks whether harder-baseline family labels correspond to distinct CNFs. It is offline only: no solver jobs, no training, and no gate/selector is fitted.",
        "",
        "## Artifacts",
        "",
        f"- hash rows CSV: `{display_path(hash_csv)}`",
        f"- equivalence classes CSV: `{display_path(classes_csv)}`",
        f"- runtime pair deltas CSV: `{display_path(pairs_csv)}`",
        "",
        "## Cross-Family Formula Classes",
        "",
        *markdown_table(
            cross_family[
                [
                    "parsed_num_vars",
                    "parsed_num_clauses",
                    "rows",
                    "families",
                    "base_instances",
                    "variants",
                    "file_hash_count",
                    "ordered_hash_count",
                    "clause_length_hist",
                ]
            ],
            max_rows=40,
        ),
        "",
        "## Complete Coloring vs PHP Runtime Pair Summary",
        "",
        *markdown_table(pair_summary, max_rows=80),
        "",
        "## Interpretation",
        "",
        "- `same_unordered_formula=True` means the two family labels encode the same clause set after ignoring clause order.",
        "- Different `ordered_dimacs_sha256` or `file_sha256` still matters for CDCL runs because clause order can affect the solver path.",
        "- If complete_coloring and php differ on runtime while sharing the same unordered formula, this cannot be claimed as a family-specific symmetry mechanism from CNF structure alone.",
        "- The next protocol step should treat these rows as formula-equivalent ordering/permutation diagnostics unless a future run canonicalizes DIMACS order or explicitly models order sensitivity.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit formula equivalence in EchoSAT harder-baseline targets.")
    parser.add_argument("--manifest-csv", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--observations-csv", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--hash-rows-csv", type=Path, default=DEFAULT_HASH_ROWS)
    parser.add_argument("--classes-csv", type=Path, default=DEFAULT_CLASSES)
    parser.add_argument("--runtime-pairs-csv", type=Path, default=DEFAULT_RUNTIME_PAIRS)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = pd.read_csv(resolve(args.manifest_csv))
    observations = pd.read_csv(resolve(args.observations_csv))
    hash_rows = manifest_hash_rows(manifest)
    classes = equivalence_classes(hash_rows)
    pairs = runtime_equivalence_pairs(hash_rows, observations)

    hash_path = resolve(args.hash_rows_csv)
    classes_path = resolve(args.classes_csv)
    pairs_path = resolve(args.runtime_pairs_csv)
    for output_path in [hash_path, classes_path, pairs_path]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    hash_rows.to_csv(hash_path, index=False)
    classes.to_csv(classes_path, index=False)
    pairs.to_csv(pairs_path, index=False)
    write_doc(
        resolve(args.doc),
        classes=classes,
        pairs=pairs,
        hash_csv=hash_path,
        classes_csv=classes_path,
        pairs_csv=pairs_path,
    )
    print(f"wrote {hash_path}")
    print(f"wrote {classes_path}")
    print(f"wrote {pairs_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
