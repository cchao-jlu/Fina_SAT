from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.echosat.equivalence import (
    EquivalenceInputError,
    accepted_mask,
    audit_plain_neutral_equivalence,
    build_expected_pair_ids,
    canonicalize_repo_path,
    input_error_audit,
    render_equivalence_markdown,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv"
DEFAULT_OUTPUT_CSV = ROOT / "runs/analysis/echosat_v2_weighted_equivalence_audit.csv"
DEFAULT_OUTPUT_MARKDOWN = ROOT / "docs/echosat_v2_weighted_equivalence_audit.md"
DEFAULT_EXPECTED_MANIFEST = (
    ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit exact plain-vs-neutral weighted Glucose equivalence."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument(
        "--output-markdown", type=Path, default=DEFAULT_OUTPUT_MARKDOWN
    )
    parser.add_argument(
        "--expected-manifest", type=Path, default=DEFAULT_EXPECTED_MANIFEST
    )
    parser.add_argument(
        "--expected-repeats", type=int, nargs="+", default=[0, 1, 2]
    )
    parser.add_argument(
        "--gate-mode",
        choices=("deterministic", "cpu"),
        default="deterministic",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        preflight = pd.read_csv(args.input)
        expected_manifest = pd.read_csv(args.expected_manifest)
        expected_pair_ids = build_expected_pair_ids(
            expected_manifest, repeats=args.expected_repeats
        )
        audit = audit_plain_neutral_equivalence(
            preflight,
            expected_pair_ids=expected_pair_ids,
            gate_mode=args.gate_mode,
        )
    except (OSError, pd.errors.ParserError, EquivalenceInputError) as error:
        audit = input_error_audit(str(error))

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.output_csv, index=False)
    args.output_markdown.write_text(
        render_equivalence_markdown(
            audit,
            canonicalize_repo_path(args.input, ROOT),
            canonicalize_repo_path(args.expected_manifest, ROOT),
            gate_mode=args.gate_mode,
        ),
        encoding="utf-8",
    )
    return 0 if accepted_mask(audit).all() else 2


if __name__ == "__main__":
    raise SystemExit(main())
