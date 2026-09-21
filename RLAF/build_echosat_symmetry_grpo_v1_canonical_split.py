from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from build_echosat_canonical_order_manifest import canonical_clauses, parse_dimacs, write_dimacs


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_MANIFEST = ROOT / "runs/analysis/symmetry_grpo_speedup_full_manifest.csv"
DEFAULT_V12_MANIFEST = ROOT / "runs/analysis/echosat_runtime_v12_canonical_manifest.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "data/echosat_symmetry_grpo_v1_canonical"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
DEFAULT_SUMMARY = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_summary.csv"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_canonical_manifest.md"

FORMULA_EQUIVALENCE_GROUPS = {
    "k9_color8": "formula_equiv_k9_php_p9",
    "php_p9_h8": "formula_equiv_k9_php_p9",
    "k10_color9": "formula_equiv_k10_php_p10",
    "php_p10_h9": "formula_equiv_k10_php_p10",
}

HIGH_PRIORITY_BASES = {
    "subset_cardinality_bw12",
    "k9_color8",
    "php_p9_h8",
    "k10_color9",
    "php_p10_h9",
}


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_manifest(path: Path, source_name: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["source_manifest_name"] = source_name
    frame["source_manifest_path"] = str(path.resolve())
    return frame


def orbit_summary(orbits_path: Path) -> tuple[int, int]:
    if not orbits_path.exists():
        return 0, 0
    try:
        payload = json.loads(orbits_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0, 0
    groups: dict[str, int] = {}
    if isinstance(payload, dict):
        for value in payload.values():
            groups[str(value)] = groups.get(str(value), 0) + 1
    valid_sizes = [size for size in groups.values() if size >= 2]
    return len(valid_sizes), int(sum(valid_sizes))


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def prepare_rows(source: pd.DataFrame, v12: pd.DataFrame) -> pd.DataFrame:
    source = source.copy()
    source["canonical_source_priority"] = 1
    v12 = v12.copy()
    v12["canonical_source_priority"] = 2
    v12["split"] = "train"
    combined = pd.concat([source, v12], ignore_index=True, sort=False)

    required = [
        "family",
        "instance_id",
        "variant",
        "base_instance_id",
        "expected_result",
        "num_vars",
        "num_clauses",
        "cnf_path",
        "orbits_path",
        "metadata_path",
        "event_audit_role",
        "symmetry_strength",
        "control_type",
        "scale",
        "scale_key",
        "benchmark_role",
        "family_scale",
        "variant_role",
        "permutation_variant",
        "source",
        "split",
        "source_manifest_name",
        "source_manifest_path",
        "canonical_source_priority",
    ]
    for column in required:
        if column not in combined.columns:
            combined[column] = ""
    combined = combined[required].copy()
    combined["base_instance_id"] = combined["base_instance_id"].fillna("").astype(str)
    combined["variant"] = combined["variant"].fillna("").astype(str)
    combined["family"] = combined["family"].fillna("").astype(str)
    combined["split"] = combined["split"].fillna("").astype(str).replace({"": "train"})
    combined["permutation_variant"] = combined["permutation_variant"].map(bool_value)
    combined = combined[combined["event_audit_role"].fillna("event").astype(str).ne("static_only")].copy()
    combined = combined.sort_values(["canonical_source_priority", "family", "base_instance_id", "variant"])
    combined = combined.drop_duplicates(["family", "base_instance_id", "variant"], keep="last").reset_index(drop=True)
    return combined


def canonicalize_row(row: pd.Series, output_root: Path) -> dict[str, Any]:
    source_cnf = resolve(str(row["cnf_path"]))
    source_orbits = resolve(str(row["orbits_path"])) if str(row.get("orbits_path", "")) else Path("")
    source_metadata = resolve(str(row["metadata_path"])) if str(row.get("metadata_path", "")) else Path("")

    num_vars, clauses, _comments = parse_dimacs(source_cnf)
    canonical = canonical_clauses(clauses)
    family = str(row["family"])
    instance_id = str(row["instance_id"])
    family_dir = output_root / "cnf" / family
    cnf_path = family_dir / f"{instance_id}.cnf"
    orbits_path = family_dir / f"{instance_id}.orbits.json"
    metadata_path = family_dir / f"{instance_id}.metadata.json"

    write_dimacs(cnf_path, num_vars=num_vars, clauses=canonical)
    if source_orbits.exists():
        shutil.copyfile(source_orbits, orbits_path)
    else:
        orbits_path.write_text("{}\n", encoding="utf-8")

    metadata: dict[str, Any] = {}
    if source_metadata.exists():
        metadata = json.loads(source_metadata.read_text(encoding="utf-8"))
    base = str(row["base_instance_id"])
    formula_group = FORMULA_EQUIVALENCE_GROUPS.get(base, "")
    sampling_group = formula_group if formula_group else base
    valid_orbit_count, valid_orbit_vars = orbit_summary(orbits_path)
    random_control = family == "random_3sat_control" or str(row.get("control_type", "")) == "non_symmetric_control"
    training_priority = 3 if base in HIGH_PRIORITY_BASES else (1 if random_control else 0)
    metadata.update(
        {
            "canonical_order_training_v1": True,
            "canonical_clause_order": "literal_abs_sign_then_clause_len_lexicographic",
            "source_cnf_path": str(source_cnf.resolve()),
            "source_metadata_path": str(source_metadata.resolve()) if source_metadata else "",
            "source_orbits_path": str(source_orbits.resolve()) if source_orbits else "",
            "formula_equivalence_group": formula_group,
            "echosat_sampling_group_id": sampling_group,
            "training_priority": int(training_priority),
            "valid_orbit_count": int(valid_orbit_count),
            "valid_orbit_vars": int(valid_orbit_vars),
            "orbit_confidence_mean": 0.0 if random_control else (1.0 if valid_orbit_count > 0 else 0.0),
            "orbit_confidence_max": 0.0 if random_control else (1.0 if valid_orbit_count > 0 else 0.0),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    updated = row.to_dict()
    updated["cnf_path"] = str(cnf_path.resolve())
    updated["orbits_path"] = str(orbits_path.resolve())
    updated["metadata_path"] = str(metadata_path.resolve())
    updated["source_cnf_path"] = str(source_cnf.resolve())
    updated["canonical_order_training_v1"] = True
    updated["canonical_clause_order"] = "literal_abs_sign_then_clause_len_lexicographic"
    updated["formula_equivalence_group"] = formula_group
    updated["echosat_sampling_group_id"] = sampling_group
    updated["training_priority"] = int(training_priority)
    updated["valid_orbit_count"] = int(valid_orbit_count)
    updated["valid_orbit_vars"] = int(valid_orbit_vars)
    updated["orbit_confidence_mean"] = metadata["orbit_confidence_mean"]
    updated["orbit_confidence_max"] = metadata["orbit_confidence_max"]
    updated["source"] = f"{row.get('source', '')}; EchoSAT symmetry GRPO v1 canonical order"
    return updated


def clear_split_links(output_root: Path) -> None:
    for split in ("train", "val"):
        split_dir = output_root / split
        if not split_dir.exists():
            continue
        for path in split_dir.rglob("*.cnf"):
            if path.is_symlink() or path.exists():
                path.unlink()


def link_splits(manifest: pd.DataFrame, output_root: Path) -> pd.DataFrame:
    clear_split_links(output_root)
    out = manifest.copy()
    split_paths: list[str] = []
    for _, row in out.iterrows():
        split = str(row.get("split", "train")) or "train"
        family = str(row["family"])
        source = Path(str(row["cnf_path"]))
        dest_dir = output_root / split / family
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        os.symlink(source, dest)
        split_paths.append(str(dest.resolve()))
    out["split_cnf_path"] = split_paths
    return out


def summarize(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, family), group in manifest.groupby(["split", "family"], sort=True):
        rows.append(
            {
                "split": split,
                "family": family,
                "rows": int(len(group)),
                "bases": int(group["base_instance_id"].nunique()),
                "sampling_groups": int(group["echosat_sampling_group_id"].nunique()),
                "priority_rows": int((pd.to_numeric(group["training_priority"], errors="coerce").fillna(0) > 0).sum()),
                "control_rows": int(group["control_type"].astype(str).eq("non_symmetric_control").sum()),
            }
        )
    rows.append(
        {
            "split": "all",
            "family": "all",
            "rows": int(len(manifest)),
            "bases": int(manifest["base_instance_id"].nunique()),
            "sampling_groups": int(manifest["echosat_sampling_group_id"].nunique()),
            "priority_rows": int((pd.to_numeric(manifest["training_priority"], errors="coerce").fillna(0) > 0).sum()),
            "control_rows": int(manifest["control_type"].astype(str).eq("non_symmetric_control").sum()),
        }
    )
    return pd.DataFrame(rows)


def write_doc(path: Path, manifest: pd.DataFrame, summary: pd.DataFrame, manifest_path: Path, output_root: Path) -> None:
    lines = [
        "# EchoSAT Symmetry GRPO v1 Canonical Manifest",
        "",
        "This training manifest rewrites the existing large symmetry GRPO split into canonical DIMACS order and appends the v1.2 canonical hard/order-paired rows. It does not train a model.",
        "",
        "## Artifacts",
        "",
        f"- manifest CSV: `{display_path(manifest_path)}`",
        f"- canonical data root: `{display_path(output_root)}`",
        "",
        "## Summary",
        "",
        "| split | family | rows | bases | sampling_groups | priority_rows | control_rows |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['split']} | {row['family']} | {row['rows']} | {row['bases']} | "
            f"{row['sampling_groups']} | {row['priority_rows']} | {row['control_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Protocol Notes",
            "",
            "- `echosat_sampling_group_id` groups formula-equivalent canonical pairs where known.",
            "- `training_priority > 0` marks repair/control rows for the GRPO sampler.",
            "- Random controls are retained as robustness/control-penalty rows, not positive reward sources.",
            "- Variable ids, orbits, and expected labels are preserved; only DIMACS literal/clause order is normalized.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build canonical/order-paired training split for EchoSAT Symmetry GRPO v1.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--v12-manifest", type=Path, default=DEFAULT_V12_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = read_manifest(resolve(args.source_manifest), "symmetry_grpo_speedup_full")
    v12 = read_manifest(resolve(args.v12_manifest), "echosat_runtime_v12_canonical")
    output_root = resolve(args.output_root)
    rows = prepare_rows(source, v12)
    manifest = pd.DataFrame([canonicalize_row(row, output_root) for _, row in rows.iterrows()])
    manifest = link_splits(manifest.sort_values(["split", "family", "echosat_sampling_group_id", "base_instance_id", "variant"]), output_root)
    manifest_path = resolve(args.manifest)
    summary_path = resolve(args.summary)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False)
    summary = summarize(manifest)
    summary.to_csv(summary_path, index=False)
    write_doc(resolve(args.doc), manifest=manifest, summary=summary, manifest_path=manifest_path, output_root=output_root)
    print(summary.to_string(index=False))
    print(f"wrote {manifest_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
