from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import pandas as pd

from build_symmetry_stress_dataset import write_instance
from src.data.symmetry import (
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
)


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "data/symmetry_grpo_speedup_full"
DEFAULT_MANIFEST_OUT = ROOT / "runs/analysis/symmetry_grpo_speedup_full_manifest.csv"
DEFAULT_SUMMARY_OUT = ROOT / "runs/analysis/symmetry_grpo_speedup_full_split_summary.csv"
DEFAULT_GENERATED_ROOT = ROOT / "data/symmetry_grpo_speedup_generated_ladder"
DEFAULT_GENERATED_MANIFEST = ROOT / "runs/analysis/symmetry_grpo_speedup_generated_ladder_manifest.csv"

DEFAULT_MANIFESTS = [
    ROOT / "runs/analysis/symmetry_runtime_benchmark_v2_manifest_labeled.csv",
    ROOT / "runs/analysis/symmetry_runtime_protocol_v1_manifest_labeled.csv",
    ROOT / "runs/analysis/symmetry_stress_manifest.csv",
]
DEFAULT_EXTRA_ROOTS = [
    ROOT / "data/symmetry_php_exit_single_candidates",
]


def parse_seeds(raw: str) -> list[int]:
    return [int(part.strip()) for part in str(raw).split(",") if part.strip()]


def stable_score(value: str, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def expanded_ladder_instances() -> list[SymmetryCNF]:
    """Training-only symmetry/control ladder, kept below the very large static-only stress cases."""
    instances: list[SymmetryCNF] = []

    for pigeons in range(6, 13):
        holes = pigeons - 1
        instances.append(pigeonhole_cnf(pigeons, holes))
        instances.append(pigeonhole_with_emergency_exit_cnf(pigeons, holes, exit_mode="single"))
        if pigeons <= 10:
            instances.append(pigeonhole_with_emergency_exit_cnf(pigeons, holes, exit_mode="all"))

    for size in (8, 10, 12, 14, 16, 18):
        instances.append(subset_cardinality_fixed_bandwidth_cnf(size))

    for rows, cols in ((3, 5), (3, 6), (3, 7), (4, 5), (5, 4)):
        instances.append(dominating_set_hex_cnf(rows, cols))

    for rows, cols in ((4, 5), (4, 6), (5, 5), (5, 6), (6, 6)):
        instances.append(even_colouring_torus_cnf(rows, cols))

    for rows, cols, cover_size in (
        (3, 4, 4),
        (3, 4, 5),
        (3, 5, 5),
        (3, 5, 6),
        (3, 6, 6),
        (3, 6, 7),
        (4, 4, 5),
        (4, 4, 6),
        (4, 5, 6),
        (4, 5, 8),
    ):
        instances.append(vertex_cover_torus_cnf(rows, cols, version="event", cover_size=cover_size))

    for vertices in range(4, 9):
        instances.append(complete_graph_coloring_cnf(vertices, vertices - 1))
        if vertices <= 7:
            instances.append(complete_graph_coloring_cnf(vertices, vertices))

    for vertices in range(5, 10):
        instances.append(complete_graph_tseitin_cnf(vertices, odd_charge=False))
        instances.append(complete_graph_tseitin_cnf(vertices, odd_charge=True))

    random_control_specs = [
        (20, 85, 1901),
        (24, 102, 1921),
        (28, 119, 1922),
        (30, 128, 1902),
        (32, 136, 1923),
        (35, 149, 1911),
        (40, 170, 1903),
        (45, 191, 1924),
        (50, 213, 1925),
        (55, 234, 1926),
        (60, 180, 1912),
        (60, 255, 1927),
        (70, 298, 1928),
        (80, 260, 1929),
        (80, 340, 1913),
        (90, 383, 1930),
        (100, 360, 1931),
        (100, 425, 1932),
        (100, 600, 1914),
        (120, 420, 1933),
        (120, 510, 1934),
        (140, 595, 1935),
        (150, 525, 1936),
        (150, 638, 1937),
    ]
    for num_vars, num_clauses, seed in random_control_specs:
        instances.append(random_3sat_control_cnf(num_vars, num_clauses, seed=seed))

    unique: dict[str, SymmetryCNF] = {}
    for instance in instances:
        unique.setdefault(instance.instance_id, instance)
    return list(unique.values())


def generated_ladder_rows(
    output_root: Path,
    manifest_path: Path,
    perm_seeds: list[int],
    signed_perm_seeds: list[int],
    max_clauses: int,
) -> pd.DataFrame:
    rows = []
    source = "symmetry GRPO generated ladder"
    output_root = output_root.resolve()
    for instance in expanded_ladder_instances():
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
        for seed in signed_perm_seeds:
            rows.append(
                write_instance(
                    output_root,
                    renamed_variant(instance, seed=seed, include_sign_flips=True),
                    variant=f"signed_perm_seed{seed}",
                    source=source,
                )
            )

    frame = pd.DataFrame(rows)
    frame["manifest_source"] = str(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(manifest_path, index=False)
    return frame


def apply_size_cap(frame: pd.DataFrame, max_clauses: int) -> pd.DataFrame:
    if max_clauses <= 0 or "num_clauses" not in frame.columns:
        return frame
    out = frame.copy()
    clauses = pd.to_numeric(out["num_clauses"], errors="coerce")
    keep = clauses.isna() | clauses.le(int(max_clauses))
    return out[keep].copy()


def read_manifest(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["manifest_source"] = str(path)
    return frame


def rows_from_extra_roots(roots: list[Path]) -> pd.DataFrame:
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for cnf_path in sorted(root.rglob("*.cnf")):
            family = cnf_path.parent.name
            stem = cnf_path.stem
            if stem.endswith("_perm1730"):
                base = stem[: -len("_perm1730")]
                variant = "perm_seed1730"
            elif stem.endswith("_perm1731"):
                base = stem[: -len("_perm1731")]
                variant = "perm_seed1731"
            else:
                base = stem
                variant = "base"
            rows.append(
                {
                    "family": family,
                    "instance_id": stem,
                    "variant": variant,
                    "base_instance_id": base,
                    "expected_result": "UNKNOWN",
                    "num_vars": pd.NA,
                    "num_clauses": pd.NA,
                    "cnf_path": str(cnf_path.resolve()),
                    "orbits_path": "",
                    "metadata_path": "",
                    "event_audit_role": "event",
                    "symmetry_strength": "weak_symmetry",
                    "control_type": "weak_symmetry",
                    "scale": "extra",
                    "scale_key": base,
                    "benchmark_role": "extra_ladder",
                    "family_scale": f"{family}:extra",
                    "variant_role": "base" if variant == "base" else "permutation_variant",
                    "permutation_variant": variant != "base",
                    "source": "extra symmetry ladder root",
                    "manifest_source": str(root),
                }
            )
    return pd.DataFrame(rows)


def canonicalize(frame: pd.DataFrame) -> pd.DataFrame:
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
        "manifest_source",
    ]
    out = frame.copy()
    for column in required:
        if column not in out.columns:
            out[column] = ""
    out = out[required].copy()
    out["cnf_path"] = out["cnf_path"].map(lambda value: str(Path(str(value)).resolve()))
    out = out[out["cnf_path"].map(lambda value: Path(value).exists())].copy()
    out["event_audit_role"] = out["event_audit_role"].fillna("event").astype(str)
    out = out[out["event_audit_role"].ne("static_only")].copy()
    out["base_instance_id"] = out["base_instance_id"].astype(str)
    out["variant"] = out["variant"].astype(str)
    out["family"] = out["family"].astype(str)
    out["permutation_variant"] = out["permutation_variant"].astype(str).str.lower().isin({"true", "1", "yes"})
    out = out.drop_duplicates(["cnf_path"]).copy()
    out = out.drop_duplicates(["base_instance_id", "variant"], keep="first").copy()
    return out.sort_values(["family", "base_instance_id", "variant"]).reset_index(drop=True)


def clear_old_split_symlinks(out_dir: Path) -> None:
    for split in ("train", "val"):
        split_dir = out_dir / split
        if not split_dir.exists():
            continue
        for path in split_dir.rglob("*.cnf"):
            if path.is_symlink():
                path.unlink()


def assign_split(frame: pd.DataFrame, val_fraction: float, seed: int) -> pd.DataFrame:
    out = frame.copy()
    base_frame = out.drop_duplicates("base_instance_id")[["family", "base_instance_id", "control_type"]].copy()
    val_bases: set[str] = set()
    for family, family_bases in base_frame.groupby("family", sort=True):
        bases = sorted(family_bases["base_instance_id"].astype(str).tolist(), key=lambda value: stable_score(value, seed))
        if not bases:
            continue
        n_val = max(1, round(len(bases) * float(val_fraction))) if len(bases) > 1 else 0
        val_bases.update(bases[:n_val])
    out["split"] = out["base_instance_id"].map(lambda base: "val" if str(base) in val_bases else "train")
    return out


def link_split(frame: pd.DataFrame, out_dir: Path) -> None:
    clear_old_split_symlinks(out_dir)
    for _, row in frame.iterrows():
        split = str(row["split"])
        family = str(row["family"])
        source = Path(str(row["cnf_path"]))
        dest_dir = out_dir / split / family
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        os.symlink(source, dest)
        frame.loc[row.name, "split_cnf_path"] = str(dest.resolve())


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (split, family), group in frame.groupby(["split", "family"], sort=True):
        rows.append(
            {
                "split": split,
                "family": family,
                "rows": int(len(group)),
                "bases": int(group["base_instance_id"].nunique()),
                "permutation_rows": int(group["permutation_variant"].sum()),
                "controls": int(group["control_type"].astype(str).eq("non_symmetric_control").sum()),
            }
        )
    rows.append(
        {
            "split": "all",
            "family": "all",
            "rows": int(len(frame)),
            "bases": int(frame["base_instance_id"].nunique()),
            "permutation_rows": int(frame["permutation_variant"].sum()),
            "controls": int(frame["control_type"].astype(str).eq("non_symmetric_control").sum()),
        }
    )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a base-heldout symmetry GRPO speedup split.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST_OUT)
    parser.add_argument("--summary-out", type=Path, default=DEFAULT_SUMMARY_OUT)
    parser.add_argument("--generated-root", type=Path, default=DEFAULT_GENERATED_ROOT)
    parser.add_argument("--generated-manifest", type=Path, default=DEFAULT_GENERATED_MANIFEST)
    parser.add_argument("--perm-seeds", default="1730,1731,1732,1733,1734,1735,1736,1737,1738,1739,1740,1741,1742,1743,1744,1745")
    parser.add_argument("--signed-perm-seeds", default="")
    parser.add_argument(
        "--max-clauses",
        type=int,
        default=10_000,
        help="Drop generated/manifest CNFs above this clause count; use 0 to disable.",
    )
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--skip-generated-ladder", action="store_true")
    args = parser.parse_args()

    frames = [read_manifest(path) for path in DEFAULT_MANIFESTS if path.exists()]
    if not args.skip_generated_ladder:
        frames.append(
            generated_ladder_rows(
                output_root=args.generated_root,
                manifest_path=args.generated_manifest,
                perm_seeds=parse_seeds(args.perm_seeds),
                signed_perm_seeds=parse_seeds(args.signed_perm_seeds),
                max_clauses=int(args.max_clauses),
            )
        )
    extra = rows_from_extra_roots(DEFAULT_EXTRA_ROOTS)
    if not extra.empty:
        frames.append(extra)
    if not frames:
        raise ValueError("No input manifests or extra CNF roots found")

    frame = canonicalize(pd.concat(frames, ignore_index=True))
    frame = apply_size_cap(frame, max_clauses=int(args.max_clauses))
    frame = assign_split(frame, val_fraction=float(args.val_fraction), seed=int(args.seed))
    link_split(frame, args.out_dir)

    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.manifest_out, index=False)
    summary = summarize(frame)
    summary.to_csv(args.summary_out, index=False)
    print(summary.to_string(index=False))
    print(f"wrote {args.manifest_out}")
    print(f"wrote {args.summary_out}")


if __name__ == "__main__":
    main()
