from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
SOLVED = {"SATISFIABLE", "UNSATISFIABLE"}
DEFAULT_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_manifest.csv"
DEFAULT_OUT_MANIFEST = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_manifest_labeled.csv"
DEFAULT_PROVENANCE = ROOT / "runs/analysis/symmetry_runtime_protocol_v1_control_label_provenance.csv"
DEFAULT_DOC = ROOT / "docs/symmetry_runtime_protocol_v1_control_labels.md"
DEFAULT_GLUCOSE = ROOT / "solvers/glucose/simp/glucose_static"
DEFAULT_CADICAL = ROOT / "solvers/cadical/cadical"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_solver_result(stdout: str) -> str:
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("s "):
            parts = stripped.split()
            if len(parts) >= 2:
                return parts[1]
    return "UNKNOWN"


def solver_version(command: list[str], name: str) -> str:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"version_error:{exc}"
    text = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if name == "glucose":
        for line in lines:
            if "glucose" in line.lower():
                return line
    return lines[0] if lines else ""


def run_solver(name: str, binary: Path, cnf_path: Path, cpu_cap: int, external_timeout: int) -> dict[str, Any]:
    if name == "glucose":
        command = [str(binary), f"-cpu-lim={int(cpu_cap)}", "-verb=0", str(cnf_path)]
        version_command = [str(binary), "--help"]
    elif name == "cadical":
        command = [str(binary), "-n", "-t", str(int(cpu_cap)), str(cnf_path)]
        version_command = [str(binary), "--version"]
    else:
        raise ValueError(f"unknown solver {name}")

    start = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True, timeout=int(external_timeout))
    wall = time.perf_counter() - start
    result = parse_solver_result(proc.stdout)
    return {
        "solver": name,
        "solver_binary": str(binary.resolve()),
        "solver_version": solver_version(version_command, name=name),
        "command_json": json.dumps(command),
        "cpu_cap": int(cpu_cap),
        "external_timeout": int(external_timeout),
        "result": result,
        "returncode": int(proc.returncode),
        "wall_time": float(wall),
        "stdout_bytes": len(proc.stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(proc.stderr.encode("utf-8", errors="replace")),
    }


def annotate_manifest(
    manifest: pd.DataFrame,
    provenance: pd.DataFrame,
) -> pd.DataFrame:
    out = manifest.copy()
    out["label_provenance"] = out.get("label_provenance", "")
    if provenance.empty:
        return out
    agreed = provenance[provenance["agreement_status"].eq("agreed")].copy()
    label_by_path = agreed.drop_duplicates("cnf_path").set_index("cnf_path")["agreed_expected_result"].to_dict()
    prov_by_path = agreed.drop_duplicates("cnf_path").set_index("cnf_path")["label_provenance_id"].to_dict()
    mask = out["cnf_path"].astype(str).isin(label_by_path)
    out.loc[mask, "expected_result"] = out.loc[mask, "cnf_path"].astype(str).map(label_by_path)
    out.loc[mask, "label_provenance"] = out.loc[mask, "cnf_path"].astype(str).map(prov_by_path)
    return out


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    if frame.empty:
        return ["_None._"]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.4g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def protocol_label(path: Path) -> str:
    stem = path.stem
    if "runtime_benchmark_v2" in stem:
        return "Runtime benchmark v2"
    if "runtime_protocol_v1" in stem:
        return "Runtime protocol v1"
    return "Runtime protocol"


def write_doc(path: Path, provenance: pd.DataFrame, out_manifest: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = (
        provenance.groupby(["agreement_status", "agreed_expected_result"], dropna=False)
        .agg(rows=("cnf_path", "count"), base_instances=("base_instance_id", "nunique"))
        .reset_index()
        if not provenance.empty
        else pd.DataFrame()
    )
    view = provenance[
        [
            "instance_id",
            "variant",
            "glucose_result",
            "cadical_result",
            "agreement_status",
            "agreed_expected_result",
            "cnf_sha256",
            "label_provenance_id",
        ]
    ].copy() if not provenance.empty else pd.DataFrame()
    lines = [
        f"# {protocol_label(path)} Random Control Expected Labels",
        "",
        "Scope: label only `random_3sat_control` rows in the selected runtime manifest.",
        "A label is written only when trusted plain Glucose and CaDiCaL agree on SAT/UNSAT.",
        "No neural model, adapter, selector, or gate is trained or changed.",
        "",
        f"- labeled manifest: `{out_manifest}`",
        "",
        "## Summary",
        "",
        *markdown_table(summary, list(summary.columns) if not summary.empty else []),
        "",
        "## Per-CNF Provenance",
        "",
        *markdown_table(view, list(view.columns) if not view.empty else [],),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Label random_3sat_control rows with trusted plain Glucose and CaDiCaL.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-manifest", type=Path, default=DEFAULT_OUT_MANIFEST)
    parser.add_argument("--provenance-csv", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--glucose-bin", type=Path, default=DEFAULT_GLUCOSE)
    parser.add_argument("--cadical-bin", type=Path, default=DEFAULT_CADICAL)
    parser.add_argument("--cpu-cap", type=int, default=60)
    parser.add_argument("--external-timeout", type=int, default=75)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = pd.read_csv(manifest_path)
    controls = manifest[manifest["family"].astype(str).eq("random_3sat_control")].copy()
    if controls.empty:
        raise ValueError("manifest contains no random_3sat_control rows")

    rows: list[dict[str, Any]] = []
    for _, instance in controls.iterrows():
        cnf_path = Path(str(instance["cnf_path"])).resolve()
        cnf_hash = sha256_file(cnf_path)
        glucose = run_solver("glucose", args.glucose_bin.resolve(), cnf_path, args.cpu_cap, args.external_timeout)
        cadical = run_solver("cadical", args.cadical_bin.resolve(), cnf_path, args.cpu_cap, args.external_timeout)
        agreement = glucose["result"] == cadical["result"] and glucose["result"] in SOLVED
        status = "agreed" if agreement else "disagreed_or_unknown"
        agreed_result = glucose["result"] if agreement else "UNKNOWN"
        rows.append(
            {
                "label_provenance_id": f"plain_glucose_cadical_sha256:{cnf_hash[:16]}",
                "manifest": str(manifest_path),
                "family": str(instance["family"]),
                "instance_id": str(instance["instance_id"]),
                "base_instance_id": str(instance["base_instance_id"]),
                "variant": str(instance["variant"]),
                "cnf_path": str(cnf_path),
                "cnf_sha256": cnf_hash,
                "cpu_cap": int(args.cpu_cap),
                "glucose_binary": glucose["solver_binary"],
                "glucose_version": glucose["solver_version"],
                "glucose_result": glucose["result"],
                "glucose_returncode": glucose["returncode"],
                "glucose_wall_time": glucose["wall_time"],
                "cadical_binary": cadical["solver_binary"],
                "cadical_version": cadical["solver_version"],
                "cadical_result": cadical["result"],
                "cadical_returncode": cadical["returncode"],
                "cadical_wall_time": cadical["wall_time"],
                "agreement_status": status,
                "agreed_expected_result": agreed_result,
                "glucose_command_json": glucose["command_json"],
                "cadical_command_json": cadical["command_json"],
            }
        )

    provenance = pd.DataFrame(rows)
    labeled_manifest = annotate_manifest(manifest, provenance)
    args.provenance_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_manifest.parent.mkdir(parents=True, exist_ok=True)
    provenance.to_csv(args.provenance_csv, index=False)
    labeled_manifest.to_csv(args.out_manifest, index=False)
    write_doc(args.doc, provenance=provenance, out_manifest=args.out_manifest)
    print(f"wrote {args.provenance_csv}")
    print(f"wrote {args.out_manifest}")
    print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
