from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_MANIFEST = ROOT / "runs/analysis/symmetry_harder_baseline_target_manifest.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "data/echosat_canonical_order_harder_equiv"
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_canonical_order_harder_equiv_manifest.csv"
DEFAULT_DOC = ROOT / "docs/echosat_canonical_order_harder_equiv_manifest.md"
DEFAULT_BASE_IDS = ["k9_color8", "k10_color9", "php_p9_h8", "php_p10_h9"]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_dimacs(path: Path) -> tuple[int, list[list[int]], list[str]]:
    comments: list[str] = []
    num_vars = 0
    clauses: list[list[int]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("c"):
            comments.append(line)
            continue
        if line.startswith("p"):
            parts = line.split()
            if len(parts) < 4 or parts[1] != "cnf":
                raise ValueError(f"Unsupported DIMACS header in {path}: {line}")
            num_vars = int(parts[2])
            continue
        clause = [int(part) for part in line.split() if part != "0"]
        if not clause:
            raise ValueError(f"Empty clause is not supported in {path}")
        clauses.append(clause)
    if num_vars <= 0:
        raise ValueError(f"No DIMACS header found in {path}")
    return num_vars, clauses, comments


def canonical_literal_key(lit: int) -> tuple[int, int]:
    return (abs(int(lit)), 0 if int(lit) > 0 else 1)


def canonical_clause(clause: list[int]) -> tuple[int, ...]:
    return tuple(sorted((int(lit) for lit in clause), key=canonical_literal_key))


def canonical_clauses(clauses: list[list[int]]) -> list[tuple[int, ...]]:
    return sorted((canonical_clause(clause) for clause in clauses), key=lambda clause: (len(clause), clause))


def write_dimacs(path: Path, num_vars: int, clauses: list[tuple[int, ...]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"p cnf {int(num_vars)} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(str(lit) for lit in clause))
            handle.write(" 0\n")


def canonicalize_row(row: pd.Series, output_root: Path) -> dict[str, Any]:
    source_cnf = resolve(str(row["cnf_path"]))
    num_vars, clauses, _comments = parse_dimacs(source_cnf)
    canonical = canonical_clauses(clauses)
    family = str(row["family"])
    instance_id = str(row["instance_id"])
    family_dir = output_root / family
    cnf_path = family_dir / f"{instance_id}.cnf"
    metadata_path = family_dir / f"{instance_id}.metadata.json"
    orbits_path = family_dir / f"{instance_id}.orbits.json"
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
            "canonical_order_audit": True,
            "canonical_clause_order": "literal_abs_sign_then_clause_len_lexicographic",
            "source_cnf_path": str(source_cnf),
            "source_metadata_path": str(source_metadata),
            "source_orbits_path": str(source_orbits),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    updated = row.to_dict()
    updated["cnf_path"] = str(cnf_path.resolve())
    updated["orbits_path"] = str(orbits_path.resolve())
    updated["metadata_path"] = str(metadata_path.resolve())
    updated["source_cnf_path"] = str(source_cnf.resolve())
    updated["canonical_order_audit"] = True
    updated["canonical_clause_order"] = "literal_abs_sign_then_clause_len_lexicographic"
    updated["source"] = f"{row.get('source', '')}; canonical DIMACS order audit"
    return updated


def build_manifest(
    source_manifest: pd.DataFrame,
    *,
    output_root: Path,
    base_ids: list[str],
) -> pd.DataFrame:
    selected = source_manifest[source_manifest["base_instance_id"].astype(str).isin(set(base_ids))].copy()
    selected = selected[selected["family"].astype(str).isin({"complete_coloring", "php"})].copy()
    if selected.empty:
        raise ValueError("No rows selected for canonical order manifest.")
    rows = [canonicalize_row(row, output_root=output_root) for _, row in selected.iterrows()]
    out = pd.DataFrame(rows).sort_values(["family", "base_instance_id", "variant"]).reset_index(drop=True)
    return out


def write_doc(path: Path, manifest: pd.DataFrame, manifest_path: Path, output_root: Path) -> None:
    summary = (
        manifest.groupby(["family", "base_instance_id"], sort=True)
        .agg(
            rows=("instance_id", "count"),
            variants=("variant", lambda values: ",".join(sorted(map(str, values)))),
            num_vars=("num_vars", "first"),
            num_clauses=("num_clauses", "first"),
        )
        .reset_index()
    )
    lines = [
        "# EchoSAT Canonical Order Harder-Equivalent Manifest",
        "",
        "This manifest rewrites formula-equivalent complete_coloring/php harder-baseline rows with a canonical DIMACS clause order. It does not change variable ids, expected labels, or orbit files.",
        "",
        "## Artifacts",
        "",
        f"- manifest CSV: `{display_path(manifest_path)}`",
        f"- CNF root: `{display_path(output_root)}`",
        "",
        "## Scope",
        "",
        "| family | base_instance_id | rows | variants | num_vars | num_clauses |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['family']} | {row['base_instance_id']} | {row['rows']} | {row['variants']} | {row['num_vars']} | {row['num_clauses']} |"
        )
    lines.extend(
        [
            "",
            "## Canonicalization",
            "",
            "- Each clause is sorted by absolute variable id, then positive literal before negative literal.",
            "- Clause rows are sorted by clause length, then lexicographically.",
            "- This deliberately tests CDCL/adapter sensitivity to DIMACS ordering while preserving the unordered formula.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build canonical-order manifest for EchoSAT formula-equivalent audit.")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--base-ids", nargs="*", default=DEFAULT_BASE_IDS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_manifest = pd.read_csv(resolve(args.source_manifest))
    output_root = resolve(args.output_root)
    manifest_path = resolve(args.manifest)
    manifest = build_manifest(
        source_manifest,
        output_root=output_root,
        base_ids=[str(item) for item in args.base_ids],
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False)
    write_doc(resolve(args.doc), manifest=manifest, manifest_path=manifest_path, output_root=output_root)
    print(f"wrote {manifest_path}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
