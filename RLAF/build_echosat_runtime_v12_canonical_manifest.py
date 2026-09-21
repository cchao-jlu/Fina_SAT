from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from build_echosat_canonical_order_manifest import canonical_clauses, parse_dimacs, write_dimacs


ROOT = Path(__file__).resolve().parent
DEFAULT_HARDER_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_target_manifest.csv"
DEFAULT_V2_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "data/echosat_runtime_v12_canonical"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_runtime_v12_canonical_manifest.csv"
DEFAULT_DOC = ROOT / "docs/echosat_runtime_v12_canonical_manifest.md"
DEFAULT_MAIN_FAMILIES = ["complete_coloring", "php", "random_3sat_control", "subset_cardinality"]
DEFAULT_DIAGNOSTIC_FAMILIES: list[str] = []


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
    frame["source_manifest_path"] = str(path.resolve())
    frame["source_manifest_name"] = str(source_name)
    return frame


def select_source_rows(
    harder_manifest: pd.DataFrame,
    v2_manifest: pd.DataFrame,
    *,
    main_families: list[str],
    diagnostic_families: list[str],
) -> pd.DataFrame:
    main = set(map(str, main_families))
    diagnostics = set(map(str, diagnostic_families))
    rows: list[pd.DataFrame] = []

    harder_families = {"complete_coloring", "php", "random_3sat_control"}
    harder_selected = harder_manifest[harder_manifest["family"].astype(str).isin(main & harder_families)].copy()
    if not harder_selected.empty:
        harder_selected["canonical_protocol_role"] = "main"
        rows.append(harder_selected)

    v2_main_families = main - harder_families
    v2_selected = v2_manifest[v2_manifest["family"].astype(str).isin(v2_main_families)].copy()
    if not v2_selected.empty:
        v2_selected["canonical_protocol_role"] = "main"
        rows.append(v2_selected)

    if diagnostics:
        diagnostic_selected = v2_manifest[v2_manifest["family"].astype(str).isin(diagnostics)].copy()
        if not diagnostic_selected.empty:
            diagnostic_selected["canonical_protocol_role"] = "diagnostic"
            rows.append(diagnostic_selected)

    if not rows:
        raise ValueError("No rows selected for canonical runtime v1.2 manifest.")
    out = pd.concat(rows, ignore_index=True)
    dedupe_key = ["family", "instance_id", "variant", "base_instance_id"]
    duplicate = out.duplicated(dedupe_key, keep=False)
    if duplicate.any():
        dup_rows = out.loc[duplicate, dedupe_key + ["source_manifest_name"]].to_dict(orient="records")
        raise ValueError(f"Duplicate selected manifest rows: {dup_rows[:10]}")
    return out.sort_values(["canonical_protocol_role", "family", "base_instance_id", "variant"]).reset_index(drop=True)


def canonicalize_row(row: pd.Series, output_root: Path) -> dict[str, Any]:
    source_cnf = resolve(str(row["cnf_path"]))
    num_vars, clauses, _comments = parse_dimacs(source_cnf)
    canonical = canonical_clauses(clauses)
    family = str(row["family"])
    instance_id = str(row["instance_id"])
    family_dir = output_root / family
    cnf_path = family_dir / f"{instance_id}.cnf"
    orbits_path = family_dir / f"{instance_id}.orbits.json"
    metadata_path = family_dir / f"{instance_id}.metadata.json"
    write_dimacs(cnf_path, num_vars=num_vars, clauses=canonical)

    source_orbits = resolve(str(row["orbits_path"]))
    source_metadata = resolve(str(row["metadata_path"]))
    if source_orbits.exists():
        shutil.copyfile(source_orbits, orbits_path)
    else:
        orbits_path.write_text("{}\n", encoding="utf-8")

    metadata: dict[str, Any] = {}
    if source_metadata.exists():
        metadata = json.loads(source_metadata.read_text(encoding="utf-8"))
    metadata.update(
        {
            "canonical_order_runtime_v12": True,
            "canonical_clause_order": "literal_abs_sign_then_clause_len_lexicographic",
            "source_cnf_path": str(source_cnf.resolve()),
            "source_metadata_path": str(source_metadata.resolve()),
            "source_orbits_path": str(source_orbits.resolve()),
            "source_manifest_path": str(row.get("source_manifest_path", "")),
            "source_manifest_name": str(row.get("source_manifest_name", "")),
            "canonical_protocol_role": str(row.get("canonical_protocol_role", "")),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    updated = row.to_dict()
    updated["cnf_path"] = str(cnf_path.resolve())
    updated["orbits_path"] = str(orbits_path.resolve())
    updated["metadata_path"] = str(metadata_path.resolve())
    updated["source_cnf_path"] = str(source_cnf.resolve())
    updated["canonical_order_runtime_v12"] = True
    updated["canonical_clause_order"] = "literal_abs_sign_then_clause_len_lexicographic"
    updated["source"] = f"{row.get('source', '')}; EchoSAT runtime v1.2 canonical DIMACS order"
    return updated


def build_manifest(
    harder_manifest: pd.DataFrame,
    v2_manifest: pd.DataFrame,
    *,
    output_root: Path,
    main_families: list[str],
    diagnostic_families: list[str],
) -> pd.DataFrame:
    selected = select_source_rows(
        harder_manifest,
        v2_manifest,
        main_families=main_families,
        diagnostic_families=diagnostic_families,
    )
    rows = [canonicalize_row(row, output_root=output_root) for _, row in selected.iterrows()]
    return pd.DataFrame(rows).sort_values(["canonical_protocol_role", "family", "base_instance_id", "variant"]).reset_index(drop=True)


def write_doc(path: Path, manifest: pd.DataFrame, manifest_path: Path, output_root: Path) -> None:
    summary = (
        manifest.groupby(["canonical_protocol_role", "family"], sort=True)
        .agg(
            rows=("instance_id", "size"),
            base_instances=("base_instance_id", "nunique"),
            variants=("variant", "nunique"),
            num_vars_min=("num_vars", "min"),
            num_vars_max=("num_vars", "max"),
            num_clauses_min=("num_clauses", "min"),
            num_clauses_max=("num_clauses", "max"),
            source_manifests=("source_manifest_name", lambda values: ",".join(sorted(set(map(str, values))))),
        )
        .reset_index()
    )
    lines = [
        "# EchoSAT Runtime Protocol v1.2 Canonical Manifest",
        "",
        "This manifest is the canonical-order input for the v1.2 runtime protocol. Variable ids, orbit files, and expected labels are preserved; only literal order inside clauses and clause row order are normalized.",
        "",
        "## Artifacts",
        "",
        f"- manifest CSV: `{display_path(manifest_path)}`",
        f"- CNF root: `{display_path(output_root)}`",
        "",
        "## Scope",
        "",
        "| role | family | rows | base_instances | variants | num_vars_min | num_vars_max | num_clauses_min | num_clauses_max | source_manifests |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['canonical_protocol_role']} | {row['family']} | {row['rows']} | {row['base_instances']} | {row['variants']} | "
            f"{row['num_vars_min']} | {row['num_vars_max']} | {row['num_clauses_min']} | {row['num_clauses_max']} | {row['source_manifests']} |"
        )
    lines.extend(
        [
            "",
            "## Canonicalization",
            "",
            "- Each clause is sorted by absolute variable id, then positive literal before negative literal.",
            "- Clause rows are sorted by clause length, then lexicographically.",
            "- Original-order results remain order-sensitivity diagnostics and are not mixed into the v1.2 main tables.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build EchoSAT runtime v1.2 canonical-order manifest.")
    parser.add_argument("--harder-manifest", type=Path, default=DEFAULT_HARDER_MANIFEST)
    parser.add_argument("--v2-manifest", type=Path, default=DEFAULT_V2_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--main-families", nargs="*", default=DEFAULT_MAIN_FAMILIES)
    parser.add_argument("--diagnostic-families", nargs="*", default=DEFAULT_DIAGNOSTIC_FAMILIES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    harder = read_manifest(resolve(args.harder_manifest), source_name="harder_baseline_target")
    v2 = read_manifest(resolve(args.v2_manifest), source_name="runtime_benchmark_v2_labeled")
    output_root = resolve(args.output_root)
    manifest_path = resolve(args.manifest)
    manifest = build_manifest(
        harder,
        v2,
        output_root=output_root,
        main_families=[str(item) for item in args.main_families],
        diagnostic_families=[str(item) for item in args.diagnostic_families],
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False)
    write_doc(resolve(args.doc), manifest=manifest, manifest_path=manifest_path, output_root=output_root)
    print(f"wrote {manifest_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
