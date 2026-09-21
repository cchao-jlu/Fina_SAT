from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
DEFAULT_OUT_MANIFEST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_strictbest_val_manifest.csv"
DEFAULT_OUT_FILELIST = ROOT / "runs/analysis/echosat_symmetry_grpo_v1_4_strictbest_val_files.txt"
DEFAULT_DOC = ROOT / "docs/echosat_symmetry_grpo_v1_4_strictbest_val.md"

TARGET_BASES = [
    "k9_color8",
    "php_p9_h8",
    "k10_color9",
    "php_p10_h9",
    "subset_cardinality_bw12",
]
RANDOM_CONTROL_BASES = [
    "random_3sat_control_v20_c85_seed1901",
    "random_3sat_control_v24_c102_seed1921",
    "random_3sat_control_v55_c234_seed1926",
    "random_3sat_control_v70_c298_seed1928",
]


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def markdown_table(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return ["_empty_"]
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return lines


def build_val_manifest(manifest: pd.DataFrame, random_bases: list[str]) -> pd.DataFrame:
    base = manifest["base_instance_id"].fillna("").astype(str)
    selected = manifest[base.isin(TARGET_BASES + list(random_bases))].copy()
    if selected.empty:
        raise ValueError("strictbest validation selection is empty")

    missing = sorted(set(TARGET_BASES) - set(selected["base_instance_id"].astype(str)))
    if missing:
        raise ValueError(f"strictbest validation is missing required target bases: {missing}")
    random_seen = sorted(set(selected["base_instance_id"].astype(str)) & set(random_bases))
    if not random_seen:
        raise ValueError("strictbest validation selected no random controls")

    selected["split"] = "strictbest_val"
    selected["strictbest_validation_v1_4"] = True
    selected["strictbest_validation_role"] = "control"
    selected.loc[selected["base_instance_id"].astype(str).isin(TARGET_BASES), "strictbest_validation_role"] = "target"
    selected.loc[
        selected["base_instance_id"].astype(str).isin(["k9_color8", "php_p9_h8"]),
        "strictbest_validation_role",
    ] = "anchor"
    selected.loc[
        selected["base_instance_id"].astype(str).isin(["k10_color9", "php_p10_h9"]),
        "strictbest_validation_role",
    ] = "hard_negative"
    selected.loc[
        selected["base_instance_id"].astype(str).eq("subset_cardinality_bw12"),
        "strictbest_validation_role",
    ] = "subset_failure_guard"
    selected = selected.sort_values(["strictbest_validation_role", "family", "base_instance_id", "variant"]).reset_index(drop=True)
    return selected


def write_doc(path: Path, manifest: pd.DataFrame, manifest_path: Path, filelist_path: Path) -> None:
    summary = (
        manifest.groupby(["strictbest_validation_role", "family"], sort=True)
        .agg(
            rows=("instance_id", "size"),
            bases=("base_instance_id", "nunique"),
            variants=("variant", "nunique"),
            split_source=("source_manifest_name", lambda values: ",".join(sorted(set(map(str, values)))) if "source_manifest_name" in manifest.columns else ""),
        )
        .reset_index()
    )
    bases = (
        manifest.groupby(["strictbest_validation_role", "family", "base_instance_id"], sort=True)
        .agg(rows=("instance_id", "size"), variants=("variant", "nunique"))
        .reset_index()
    )
    lines = [
        "# EchoSAT Symmetry GRPO v1.4 Strict-Best Validation Set",
        "",
        "This validation set is only for online best-checkpoint selection. It is not a new runtime benchmark and does not support a solver speedup claim.",
        "",
        "## Artifacts",
        "",
        f"- manifest: `{display(manifest_path)}`",
        f"- file list: `{display(filelist_path)}`",
        "",
        "## Summary",
        "",
        *markdown_table(summary),
        "",
        "## Base Instances",
        "",
        *markdown_table(bases),
        "",
        "## Intended Use",
        "",
        "- Training still uses the full canonical train split.",
        "- Validation uses this file list so `echosat_strict_search_work_v2` can see anchors, hard negatives, subset failure guard, and random-control suppression rows.",
        "- `best.pt` may be absent if no validation checkpoint passes hard gates; use `iter=*.pt` plus targeted acceptance in that case.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v1.4 strict-best validation manifest/file list.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-manifest", type=Path, default=DEFAULT_OUT_MANIFEST)
    parser.add_argument("--out-filelist", type=Path, default=DEFAULT_OUT_FILELIST)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--random-bases", nargs="*", default=RANDOM_CONTROL_BASES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = pd.read_csv(resolve(args.manifest))
    selected = build_val_manifest(source, random_bases=[str(item) for item in args.random_bases])
    files = selected["split_cnf_path" if "split_cnf_path" in selected.columns else "cnf_path"].fillna("").astype(str)
    missing_files = [path for path in files if not path or not resolve(path).exists()]
    if missing_files:
        raise FileNotFoundError(f"strictbest validation has missing CNF files: {missing_files[:5]}")

    out_manifest = resolve(args.out_manifest)
    out_filelist = resolve(args.out_filelist)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    out_filelist.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out_manifest, index=False)
    out_filelist.write_text("\n".join(str(resolve(path).resolve()) for path in files) + "\n", encoding="utf-8")
    write_doc(resolve(args.doc), selected, manifest_path=out_manifest, filelist_path=out_filelist)
    print(f"wrote {out_manifest}")
    print(f"wrote {out_filelist}")
    print(f"wrote {resolve(args.doc)}")


if __name__ == "__main__":
    main()
