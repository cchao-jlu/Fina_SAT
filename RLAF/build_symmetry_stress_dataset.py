from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.data.symmetry import (
    SymmetryCNF,
    default_symmetry_instances,
    renamed_variant,
    runtime_benchmark_v2_instances,
    write_dimacs,
    write_orbits_json,
)


ROOT = Path(__file__).resolve().parent


def event_audit_role(instance: SymmetryCNF) -> str:
    if instance.family == "dominating_set_hex" and int(instance.metadata.get("rows", 0)) == 4 and int(instance.metadata.get("cols", 0)) == 7:
        return "static_only"
    return "event"


def symmetry_strength(instance: SymmetryCNF) -> str:
    if instance.family == "random_3sat_control":
        return "none"
    if str(instance.metadata.get("symmetry_strength", "")) == "none":
        return "none"
    strong = {"php", "complete_coloring", "tseitin_complete", "vertex_cover_torus"}
    weak = {"even_colouring", "subset_cardinality", "php_exit_single", "php_exit_all", "dominating_set_hex"}
    if instance.family in strong:
        return "strong"
    if instance.family in weak:
        return "weak"
    return "weak"


def control_type(instance: SymmetryCNF) -> str:
    strength = symmetry_strength(instance)
    if strength == "none":
        return "non_symmetric_control"
    if strength == "strong":
        return "strong_symmetry"
    return "weak_symmetry"


def scale_label(instance: SymmetryCNF) -> str:
    role = event_audit_role(instance)
    clauses = len(instance.clauses)
    if role == "static_only" or clauses >= 100_000:
        return "stress"
    if instance.num_vars <= 20 and clauses <= 200:
        return "small"
    if instance.num_vars <= 40 and clauses <= 5_000:
        return "medium"
    return "large"


def scale_key(instance: SymmetryCNF) -> str:
    metadata = instance.metadata
    if "pigeons" in metadata and "holes" in metadata:
        return f"p{metadata['pigeons']}_h{metadata['holes']}"
    if "rows" in metadata and "cols" in metadata:
        return f"{metadata['rows']}x{metadata['cols']}"
    if "size" in metadata:
        return f"size{metadata['size']}"
    if "vertices" in metadata and "colors" in metadata:
        return f"v{metadata['vertices']}_c{metadata['colors']}"
    if "vertices" in metadata:
        return f"k{metadata['vertices']}"
    return f"vars{instance.num_vars}_clauses{len(instance.clauses)}"


def benchmark_role(instance: SymmetryCNF) -> str:
    if event_audit_role(instance) == "static_only":
        return "static_only_stress"
    if symmetry_strength(instance) == "none":
        return "control"
    return "main"


def parse_seeds(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


def select_instances(instances: list[SymmetryCNF], families: set[str]) -> list[SymmetryCNF]:
    if not families:
        return instances
    selected = [instance for instance in instances if instance.family in families]
    missing = sorted(families - {instance.family for instance in selected})
    if missing:
        raise ValueError(f"Requested families are not available: {missing}")
    return selected


def instances_for_profile(profile: str) -> list[SymmetryCNF]:
    if profile == "default":
        return default_symmetry_instances()
    if profile == "runtime_v2":
        return runtime_benchmark_v2_instances()
    raise ValueError(f"Unknown profile: {profile}")


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a SAT symmetry stress-test CNF set.")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data/symmetry_stress")
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--families",
        default="",
        help="Optional comma-separated family filter. Empty means all default families.",
    )
    parser.add_argument("--perm-seeds", default="1730,1731")
    parser.add_argument("--signed-perm-seeds", default="")
    parser.add_argument("--profile", choices=["default", "runtime_v2"], default="default")
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    manifest_path = args.manifest.resolve() if args.manifest else output_root / "manifest.csv"
    families = {part.strip() for part in args.families.split(",") if part.strip()}
    perm_seeds = parse_seeds(args.perm_seeds)
    signed_perm_seeds = parse_seeds(args.signed_perm_seeds)

    rows = []
    source = "SAT-b-inspired symmetry stress set"
    for instance in select_instances(instances_for_profile(args.profile), families=families):
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

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} symmetry stress instances")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
