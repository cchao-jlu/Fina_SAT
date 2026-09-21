# EchoSAT v2 Stage 0-4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate the safety foundation for EchoSAT v2: frozen references, neutral weighted equivalence, weight-only guidance, explicit orbit-relative features, and a constrained pre-normalization GRPO objective.

**Architecture:** Add a focused `src/echosat` package rather than expanding the already-large `train_rlaf.py` with more experiment-specific logic. Repair weighted Glucose so neutral parameters reproduce plain initialization, attach certified orbit tensors to PyG variable nodes, make the event adapter explicitly weight-only and evidence-masked, and route `symmetry_grpo_v2` target/advantage calculations through isolated tested helpers.

**Tech Stack:** Python 3.12, PyTorch 2.5, PyTorch Geometric, pandas, NumPy, Hydra/OmegaConf, C++ Glucose, pytest/unittest.

---

## File Map

### New focused modules

- `src/echosat/__init__.py`: EchoSAT v2 package exports.
- `src/echosat/reference.py`: file hashing and frozen-reference manifests.
- `src/echosat/equivalence.py`: neutral weighted equivalence comparisons and acceptance summaries.
- `src/echosat/orbit_features.py`: certified orbit lookup, graph attachment, and orbit-relative event features.
- `src/echosat/objective_v2.py`: blocked-row masking, masked GRPO normalization, and worst-variant scoring.

### New command-line entry points

- `freeze_echosat_v2_reference.py`: write immutable Stage 0 reference metadata.
- `run_echosat_v2_weighted_equivalence.py`: generate fresh paired deterministic and CPU-limit observations without loading a model.
- `audit_echosat_v2_weighted_equivalence.py`: analyze paired plain/neutral/zero-delta solver rows.
- `replay_echosat_v2_objective.py`: run the Stage 4 objective over saved solver observations without training.

### Existing files modified

- `src/solving/solver.py`: make weighted DIMACS semantics explicit and reusable.
- `solvers/glucose/core/Solver.cc`: check deterministic/interrupt budgets at the same inner-search point as weighted Glucose.
- `solvers/glucose/simp/Main.cc`: expose the same `conf-lim` option as weighted Glucose.
- `solvers/glucose_weighted/core/Dimacs.h`: make neutral weight initialization equivalent to plain Glucose and remove parser debug output.
- `run_symmetry_solver_protocol_preflight.py`: generate true neutral and zero-delta protocol methods.
- `build_echosat_orbit_certification.py`: emit a variable-level certification table.
- `src/model/model.py`: add weight-only fusion and explicit orbit/event evidence masks.
- `train_rlaf.py`: attach orbit tensors and delegate v2 target/advantage logic.
- `configs/config_train_rlaf_echosat_v2_stage4_replay.yaml`: define the short formal-path Stage 4 configuration.

### Tests

- `tests/test_echosat_v2_reference.py`
- `tests/test_echosat_v2_weighted_equivalence.py`
- `tests/test_solver_budget_integration.py`
- `tests/test_echosat_v2_orbit_features.py`
- `tests/test_event_adapter.py`
- `tests/test_echosat_v2_objective.py`
- `tests/test_echosat_v2_replay.py`

## Task 1: Freeze Stage 0 Reference Artifacts

**Files:**
- Create: `src/echosat/__init__.py`
- Create: `src/echosat/reference.py`
- Create: `freeze_echosat_v2_reference.py`
- Create: `tests/test_echosat_v2_reference.py`
- Create at runtime: `runs/analysis/echosat_v2_reference/reference.json`

- [ ] **Step 1: Write the failing reference-manifest tests**

```python
# tests/test_echosat_v2_reference.py
import json
from pathlib import Path

from src.echosat.reference import freeze_reference_artifacts, sha256_file


def test_sha256_file_is_content_stable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("echo-sat\n", encoding="utf-8")
    first = sha256_file(artifact)
    second = sha256_file(artifact)
    assert first == second
    assert len(first) == 64


def test_freeze_reference_artifacts_records_relative_paths_and_hashes(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    checkpoint = root / "runs" / "model.pt"
    manifest = root / "runs" / "manifest.csv"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    manifest.write_text("base_instance_id\nbase-a\n", encoding="utf-8")

    output = root / "runs" / "analysis" / "echosat_v2_reference" / "reference.json"
    payload = freeze_reference_artifacts(
        root=root,
        artifacts=[checkpoint, manifest],
        output_path=output,
        metadata={"reference_checkpoint": "v1.2-iter15"},
    )

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert payload == saved
    assert saved["reference_checkpoint"] == "v1.2-iter15"
    assert [row["path"] for row in saved["artifacts"]] == [
        "runs/manifest.csv",
        "runs/model.pt",
    ]
    assert all(len(row["sha256"]) == 64 for row in saved["artifacts"])
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
pytest -q tests/test_echosat_v2_reference.py
```

Expected: collection succeeds and fails with `ModuleNotFoundError: No module named 'src.echosat'`.

- [ ] **Step 3: Implement the reference helper**

```python
# src/echosat/reference.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_reference_artifacts(
    *,
    root: Path,
    artifacts: Sequence[Path],
    output_path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    root = Path(root).resolve()
    rows = []
    for artifact in sorted((Path(path).resolve() for path in artifacts), key=str):
        if not artifact.is_file():
            raise FileNotFoundError(artifact)
        rows.append(
            {
                "path": str(artifact.relative_to(root)),
                "size_bytes": artifact.stat().st_size,
                "sha256": sha256_file(artifact),
            }
        )
    payload = {**metadata, "artifacts": rows}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
```

Export the functions:

```python
# src/echosat/__init__.py
from src.echosat.reference import freeze_reference_artifacts, sha256_file

__all__ = ["freeze_reference_artifacts", "sha256_file"]
```

- [ ] **Step 4: Add the Stage 0 CLI**

```python
# freeze_echosat_v2_reference.py
from pathlib import Path

from src.echosat.reference import freeze_reference_artifacts


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "runs/analysis/echosat_v2_reference/reference.json"
ARTIFACTS = [
    ROOT / "runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt",
    ROOT / "runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv",
    ROOT / "runs/analysis/echosat_orbit_certification.csv",
    ROOT / "docs/echosat_runtime_v12_canonical_low_warmup.md",
]


def main() -> None:
    payload = freeze_reference_artifacts(
        root=ROOT,
        artifacts=ARTIFACTS,
        output_path=OUTPUT,
        metadata={
            "schema_version": 1,
            "reference_checkpoint": "v1.2_iter15_wc1",
            "purpose": "EchoSAT v2 Stage 0-4 frozen reference",
        },
    )
    print(f"wrote {OUTPUT} artifacts={len(payload['artifacts'])}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests and freeze the real references**

Run:

```bash
pytest -q tests/test_echosat_v2_reference.py
python freeze_echosat_v2_reference.py
```

Expected: `2 passed`; CLI prints `artifacts=4` and creates `runs/analysis/echosat_v2_reference/reference.json`.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/echosat/__init__.py src/echosat/reference.py freeze_echosat_v2_reference.py tests/test_echosat_v2_reference.py runs/analysis/echosat_v2_reference/reference.json
git commit -m "chore: freeze EchoSAT v2 reference artifacts"
```

## Task 2: Make Neutral Weighted DIMACS Equivalent to Plain Initialization

**Files:**
- Modify: `src/solving/solver.py:82`
- Modify: `solvers/glucose_weighted/core/Dimacs.h:64`
- Modify: `train_rlaf.py:658`
- Modify: `run_symmetry_solver_protocol_preflight.py:139`
- Create: `tests/test_echosat_v2_weighted_equivalence.py`

The current neutral helper uses phase `1.0`, while plain Glucose creates variables with default polarity `true`. The weighted parser also passes the absolute weight as both initial activity and activity-bump scale. EchoSAT v2 defines neutral weighted parameters as phase `0.0`, scale `1.0`, initial activity `0.0`.

- [ ] **Step 1: Write failing Python-level neutral-semantics tests**

```python
# tests/test_echosat_v2_weighted_equivalence.py
import numpy as np
import torch
from torch_geometric.data import HeteroData

from run_symmetry_solver_protocol_preflight import neutral_weighted_graphs
from src.solving.solver import cnf_to_dimacs


def _graph(num_vars: int = 3) -> HeteroData:
    graph = HeteroData()
    graph["lit"].num_nodes = 2 * num_vars
    graph["var"].num_nodes = num_vars
    return graph


def test_neutral_weighted_graph_uses_plain_default_phase_and_unit_scale() -> None:
    graph = neutral_weighted_graphs([_graph()])[0]
    params = graph["var"].var_params
    assert torch.equal(params[:, 0, 0], torch.zeros(3))
    assert torch.equal(params[:, 0, 1], torch.ones(3))


def test_neutral_dimacs_encodes_negative_signed_unit_scale() -> None:
    params = np.stack([np.zeros(3), np.ones(3)], axis=1)
    dimacs = cnf_to_dimacs([[1, -2, 3]], var_params=params)
    assert "c weight -1.0000 -1.0000 -1.0000" in dimacs
```

- [ ] **Step 2: Run tests and verify the existing neutral phase fails**

Run:

```bash
pytest -q tests/test_echosat_v2_weighted_equivalence.py
```

Expected: the first test fails because the current neutral helper produces phase ones.

- [ ] **Step 3: Change all neutral baseline constructors to phase zero**

Add one canonical constructor to `src/solving/solver.py`:

```python
def neutral_var_params(num_vars: int, weight: float = 1.0, phase: float = 0.0) -> np.ndarray:
    phases = np.full(int(num_vars), float(phase), dtype=np.float64)
    weights = np.full(int(num_vars), float(weight), dtype=np.float64)
    return np.stack([phases, weights], axis=1)
```

Change `train_rlaf.py`:

```python
params = torch.from_numpy(neutral_var_params(num_vars, weight=weight)).float().unsqueeze(1)
item["var"].var_params = params
```

Change `run_symmetry_solver_protocol_preflight.py`:

```python
def neutral_weighted_graphs(graphs: list[Any], weight: float = 1.0, phase: float = 0.0) -> list[Any]:
    neutral: list[Any] = []
    for graph in graphs:
        updated = graph.clone() if hasattr(graph, "clone") else copy(graph)
        num_vars = int(getattr(updated["var"], "num_nodes", updated["lit"].num_nodes // 2))
        params = torch.from_numpy(
            neutral_var_params(num_vars, weight=weight, phase=phase)
        ).float().unsqueeze(1)
        updated["var"].num_nodes = num_vars
        updated["var"].var_params = params
        neutral.append(updated)
    return neutral
```

Also change the CLI default:

```python
parser.add_argument("--neutral-phase", type=float, default=0.0)
```

- [ ] **Step 4: Repair the weighted Glucose parser initialization**

Replace the `c weight` loop in `solvers/glucose_weighted/core/Dimacs.h` with:

```cpp
if (eagerMatch(in, "c weight")){
    for (int i = 0; i < vars; i++){
        double signed_scale = parsePlainDouble(in);
        bool positive_phase = signed_scale > 0;
        double scale = signed_scale >= 0 ? signed_scale : -signed_scale;
        if (scale <= 0.0) scale = 1.0;
        S.newVar(!positive_phase, true, 0.0, scale);
    }
}else{
    skipLine(in);
}
```

This removes the per-variable `printf`, preserves explicit phase control, gives neutral scale `1.0`, and matches plain initial activity `0.0`.

- [ ] **Step 5: Run Python tests and rebuild weighted Glucose**

Run:

```bash
pytest -q tests/test_echosat_v2_weighted_equivalence.py
make -C solvers/glucose_weighted/simp clean
make -C solvers/glucose_weighted/simp r
```

Expected: `2 passed`; the weighted solver binary rebuilds successfully.

- [ ] **Step 6: Run a direct plain/neutral smoke comparison**

Run the same small CNF through both binaries with `rnd-freq=0`, identical seed, preprocessing enabled, and the same CPU limit:

```bash
python run_symmetry_solver_protocol_preflight.py \
  --manifest runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv \
  --checkpoint runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt \
  --per-instance-csv runs/analysis/echosat_v2_neutral_smoke_per_instance.csv \
  --phases-csv runs/analysis/echosat_v2_neutral_smoke_phases.csv \
  --by-family-csv runs/analysis/echosat_v2_neutral_smoke_by_family.csv \
  --by-base-instance-csv runs/analysis/echosat_v2_neutral_smoke_by_base.csv \
  --attribution-csv runs/analysis/echosat_v2_neutral_smoke_attribution.csv \
  --attribution-by-base-csv runs/analysis/echosat_v2_neutral_smoke_attribution_by_base.csv \
  --loss-diagnostics-csv runs/analysis/echosat_v2_neutral_smoke_loss_diagnostics.csv \
  --timeout-correctness-csv runs/analysis/echosat_v2_neutral_smoke_timeout_correctness.csv \
  --doc docs/echosat_v2_neutral_smoke.md \
  --families complete_coloring \
  --base-only \
  --repeats 1 \
  --neutral-phase 0 \
  --warmup-conflicts 1
```

Expected: plain and neutral rows have identical result and solved status. Decisions/conflicts are recorded for Task 3 rather than silently accepted.

- [ ] **Step 7: Commit Task 2**

```bash
git add src/solving/solver.py solvers/glucose_weighted/core/Dimacs.h train_rlaf.py run_symmetry_solver_protocol_preflight.py tests/test_echosat_v2_weighted_equivalence.py
git commit -m "fix: make neutral weighted Glucose match plain initialization"
```

## Task 3: Add the Formal Neutral Equivalence Audit

**Files:**
- Create: `src/echosat/equivalence.py`
- Create: `audit_echosat_v2_weighted_equivalence.py`
- Modify: `tests/test_echosat_v2_weighted_equivalence.py`
- Create at runtime: `runs/analysis/echosat_v2_weighted_equivalence/summary.csv`
- Create at runtime: `docs/echosat_v2_weighted_equivalence.md`

- [ ] **Step 1: Add failing paired-equivalence tests**

Append:

```python
import pandas as pd

from src.echosat.equivalence import summarize_weighted_equivalence


def test_equivalence_summary_rejects_result_or_search_differences() -> None:
    rows = pd.DataFrame(
        [
            {"pair_id": "a", "method": "plain_unguided_glucose", "Result": "SATISFIABLE", "decisions": 10, "conflicts": 2, "CPU time": 0.1},
            {"pair_id": "a", "method": "neutral_weighted_glucose", "Result": "SATISFIABLE", "decisions": 10, "conflicts": 2, "CPU time": 0.1},
            {"pair_id": "b", "method": "plain_unguided_glucose", "Result": "UNSATISFIABLE", "decisions": 20, "conflicts": 5, "CPU time": 0.2},
            {"pair_id": "b", "method": "neutral_weighted_glucose", "Result": "UNSATISFIABLE", "decisions": 21, "conflicts": 5, "CPU time": 0.2},
        ]
    )
    summary = summarize_weighted_equivalence(rows)
    assert summary.loc[summary["pair_id"].eq("a"), "accepted"].item()
    assert not summary.loc[summary["pair_id"].eq("b"), "accepted"].item()
    assert summary.loc[summary["pair_id"].eq("b"), "rejection_reason"].item() == "SEARCH_DIVERGENCE"
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
pytest -q tests/test_echosat_v2_weighted_equivalence.py::test_equivalence_summary_rejects_result_or_search_differences
```

Expected: import failure for `src.echosat.equivalence`.

- [ ] **Step 3: Implement exact paired comparison**

```python
# src/echosat/equivalence.py
from __future__ import annotations

import numpy as np
import pandas as pd


PLAIN = "plain_unguided_glucose"
NEUTRAL = "neutral_weighted_glucose"


def summarize_weighted_equivalence(rows: pd.DataFrame) -> pd.DataFrame:
    required = {"pair_id", "method", "Result", "decisions", "conflicts", "CPU time"}
    missing = required - set(rows.columns)
    if missing:
        raise ValueError(f"missing equivalence columns: {sorted(missing)}")
    wide = rows.pivot(index="pair_id", columns="method", values=["Result", "decisions", "conflicts", "CPU time"])
    output = []
    for pair_id, row in wide.iterrows():
        plain_result = str(row[("Result", PLAIN)])
        neutral_result = str(row[("Result", NEUTRAL)])
        decision_delta = float(row[("decisions", NEUTRAL)]) - float(row[("decisions", PLAIN)])
        conflict_delta = float(row[("conflicts", NEUTRAL)]) - float(row[("conflicts", PLAIN)])
        cpu_delta = float(row[("CPU time", NEUTRAL)]) - float(row[("CPU time", PLAIN)])
        if plain_result != neutral_result:
            reason = "RESULT_MISMATCH"
        elif not np.isclose(decision_delta, 0.0) or not np.isclose(conflict_delta, 0.0):
            reason = "SEARCH_DIVERGENCE"
        else:
            reason = "ACCEPTED"
        output.append(
            {
                "pair_id": pair_id,
                "result_match": plain_result == neutral_result,
                "decision_delta": decision_delta,
                "conflict_delta": conflict_delta,
                "cpu_delta": cpu_delta,
                "accepted": reason == "ACCEPTED",
                "rejection_reason": reason,
            }
        )
    return pd.DataFrame(output).sort_values("pair_id").reset_index(drop=True)
```

- [ ] **Step 4: Implement the audit CLI**

The CLI reads protocol observations, constructs `pair_id` from `repeat_id`, `base_instance_id`, and `variant`, calls `summarize_weighted_equivalence`, and writes both CSV and Markdown.

```python
# audit_echosat_v2_weighted_equivalence.py
from pathlib import Path
import argparse

import pandas as pd

from src.echosat.equivalence import PLAIN, NEUTRAL, summarize_weighted_equivalence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--doc", type=Path, required=True)
    args = parser.parse_args()

    rows = pd.read_csv(args.observations).rename(
        columns={
            "final_result": "Result",
            "final_decisions": "decisions",
            "final_conflicts": "conflicts",
            "final_cpu_time": "CPU time",
        }
    )
    rows = rows[rows["method"].isin({PLAIN, NEUTRAL})].copy()
    rows["pair_id"] = (
        rows["repeat_id"].astype(str)
        + "::" + rows["base_instance_id"].astype(str)
        + "::" + rows["variant"].astype(str)
    )
    summary = summarize_weighted_equivalence(rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    accepted = int(summary["accepted"].sum())
    lines = [
        "# EchoSAT v2 Weighted Equivalence",
        "",
        f"- pairs: `{len(summary)}`",
        f"- accepted: `{accepted}`",
        f"- rejected: `{len(summary) - accepted}`",
        "",
        "Promotion requires every pair to be accepted.",
    ]
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not bool(summary["accepted"].all()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run unit tests and the formal audit**

Run:

```bash
pytest -q tests/test_echosat_v2_weighted_equivalence.py
python audit_echosat_v2_weighted_equivalence.py \
  --observations runs/analysis/echosat_v2_neutral_smoke_per_instance.csv \
  --summary runs/analysis/echosat_v2_weighted_equivalence/summary.csv \
  --doc docs/echosat_v2_weighted_equivalence.md
```

Expected: tests pass. The CLI exits `0` only when all paired results, decisions, and conflicts match exactly; otherwise it exits `2` and preserves rejection rows for diagnosis.

- [ ] **Step 6: Commit Task 3**

```bash
git add src/echosat/equivalence.py audit_echosat_v2_weighted_equivalence.py tests/test_echosat_v2_weighted_equivalence.py docs/echosat_v2_weighted_equivalence.md
git commit -m "feat: add EchoSAT weighted equivalence gate"
```

## Task 3B: Align Budgets and Split the Stage 1 Gates

**Files:**
- Modify: `solvers/glucose/core/Solver.cc`
- Modify: `solvers/glucose/simp/Main.cc`
- Modify: `src/echosat/equivalence.py`
- Create: `run_echosat_v2_weighted_equivalence.py`
- Modify: `audit_echosat_v2_weighted_equivalence.py`
- Modify: `tests/test_solver_budget_integration.py`
- Modify: `tests/test_echosat_v2_weighted_equivalence.py`
- Create at runtime: `runs/analysis/echosat_v2_weighted_equivalence_deterministic.csv`
- Create at runtime: `runs/analysis/echosat_v2_weighted_equivalence_cpu.csv`

- [ ] **Step 1: Write the failing plain conflict-budget integration test**

Add a helper that invokes either solver and a test that requires both binaries
to accept `-conf-lim=1` and return the same result and search counters:

```python
def test_plain_and_neutral_weighted_share_conflict_budget_semantics() -> None:
    clauses = [[1, 2], [-1, 2], [1, -2], [-1, -2]]
    plain = run_solver(PLAIN_SOLVER, cnf_to_dimacs(clauses), "-conf-lim=1")
    neutral = run_solver(
        WEIGHTED_SOLVER,
        cnf_to_dimacs(clauses, neutral_var_params(2)),
        "-conf-lim=1",
    )
    assert plain.returncode == neutral.returncode == 0
    assert parse_solver_trajectory(plain.stdout) == parse_solver_trajectory(neutral.stdout)
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/test_solver_budget_integration.py::test_plain_and_neutral_weighted_share_conflict_budget_semantics
```

Expected: plain Glucose rejects `-conf-lim` or fails to stop at the same
deterministic conflict boundary.

- [ ] **Step 3: Align plain Glucose budget handling**

In `solvers/glucose/simp/Main.cc`, add the same option and budget setup already
used by weighted Glucose:

```cpp
IntOption conf_lim(
    "MAIN",
    "conf-lim",
    "Limit on conflicts allowed before returning INDETERMINATE.\n",
    INT32_MAX,
    IntRange(0, INT32_MAX)
);

if (conf_lim != INT32_MAX)
    S.setConfBudget(conf_lim);
```

In the conflict branch of `solvers/glucose/core/Solver.cc`, immediately after
incrementing the conflict counter and before conflict analysis, add the same
check used by weighted Glucose:

```cpp
if (!withinBudget())
    return l_Undef;
```

Do not change branching, preprocessing, restart, activity, or clause logic.

- [ ] **Step 4: Rebuild both solver binaries and verify GREEN**

Run:

```bash
cd solvers/glucose/simp && make r
cd ../../glucose_weighted/simp && make r
cd ../../..
.venv/bin/python -m pytest -q tests/test_solver_budget_integration.py
```

Expected: the new conflict-budget test and existing event/budget tests pass.

- [ ] **Step 5: Write failing dual-gate audit tests**

Add tests with a deterministic row and a CPU-limited row:

```python
def test_deterministic_gate_requires_exact_search_counters() -> None:
    audit = audit_plain_neutral_equivalence(
        make_preflight_rows(neutral_decisions=11),
        gate_mode="deterministic",
    )
    assert not bool(audit.iloc[0]["accepted"])
    assert "decisions_mismatch" in audit.iloc[0]["rejection_reason"]


def test_cpu_gate_treats_cutoff_search_counters_as_diagnostic() -> None:
    rows = make_preflight_rows(
        plain_result="INDETERMINATE",
        neutral_result="INDETERMINATE",
        plain_solved=False,
        neutral_solved=False,
        neutral_decisions=11,
    )
    audit = audit_plain_neutral_equivalence(rows, gate_mode="cpu")
    assert bool(audit.iloc[0]["accepted"])
    assert not bool(audit.iloc[0]["decisions_match"])


def test_cpu_gate_rejects_plain_solved_to_neutral_unsolved() -> None:
    rows = make_preflight_rows(
        plain_result="SATISFIABLE",
        neutral_result="INDETERMINATE",
        plain_solved=True,
        neutral_solved=False,
    )
    audit = audit_plain_neutral_equivalence(rows, gate_mode="cpu")
    assert not bool(audit.iloc[0]["accepted"])
```

- [ ] **Step 6: Implement explicit gate modes**

Extend `audit_plain_neutral_equivalence` with a required keyword:

```python
GateMode = Literal["deterministic", "cpu"]


def audit_plain_neutral_equivalence(
    rows: pd.DataFrame,
    *,
    gate_mode: GateMode = "deterministic",
    expected_pair_ids: Iterable[str] | None = None,
) -> pd.DataFrame:
```

For `deterministic`, acceptance continues to require exact result, solved
status, decisions, and conflicts. For `cpu`, acceptance requires valid rows,
equal result and solved status, and explicitly rejects
`plain_final_solved=True` with `neutral_final_solved=False`; counter equality is
retained in output but is diagnostic-only. Reject unknown gate modes.

Add `--gate-mode {deterministic,cpu}` to
`audit_echosat_v2_weighted_equivalence.py` and include it in the Markdown
header.

- [ ] **Step 7: Write the failing runner tests**

Test argument construction and artifact provenance without invoking long
solves:

```python
def test_runner_builds_matching_plain_and_neutral_argv() -> None:
    plain, neutral = build_pair_commands(
        seed=3,
        budget_type="conflicts",
        budget_value=100,
    )
    assert plain.options == neutral.options
    assert "-conf-lim=100" in plain.options


def test_runner_records_binary_and_input_hashes(tmp_path: Path) -> None:
    rows = run_manifest_pairs(
        manifest=one_row_manifest(tmp_path),
        repeats=[0],
        budget_type="conflicts",
        budget_value=1,
        workers=1,
    )
    assert rows["solver_sha256"].str.len().eq(64).all()
    assert rows["input_sha256"].str.len().eq(64).all()
    assert not rows["external_timeout"].any()
```

- [ ] **Step 8: Implement the model-free paired runner**

`run_echosat_v2_weighted_equivalence.py` must:

- read the canonical manifest and resolve legacy `/my_rlaf/` paths relative to
  the repository;
- invoke plain and neutral weighted binaries with identical seed, `rnd-freq`,
  `K`, preprocessing, and selected budget;
- support `--budget-type conflicts|cpu`, `--budget-value`, `--repeats`,
  `--workers`, `--external-timeout`, and `--output`;
- record result, solved status, decisions, conflicts, propagations, restarts,
  CPU/wall time, return code, external timeout, resolved binary path, binary
  SHA-256, input SHA-256, argv, budget type, and budget value;
- checkpoint the CSV every 25 completed pairs and resume only when provenance
  columns match the requested run.

The runner must not load a checkpoint or execute static/event adapter paths.

- [ ] **Step 9: Verify focused and full suites**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_solver_budget_integration.py
.venv/bin/python -m pytest -q tests/test_echosat_v2_weighted_equivalence.py
.venv/bin/python -m pytest -q
```

Expected: all tests pass with no new warnings from the modified code.

- [ ] **Step 10: Generate fresh Stage 1 evidence**

Run deterministic evidence first:

```bash
.venv/bin/python run_echosat_v2_weighted_equivalence.py \
  --manifest runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv \
  --budget-type conflicts \
  --budget-value 100000 \
  --repeats 0 1 2 \
  --workers 4 \
  --external-timeout 120 \
  --output runs/analysis/echosat_v2_weighted_equivalence_deterministic.csv

.venv/bin/python audit_echosat_v2_weighted_equivalence.py \
  --input runs/analysis/echosat_v2_weighted_equivalence_deterministic.csv \
  --gate-mode deterministic \
  --expected-repeats 0 1 2
```

Only after the deterministic audit exits `0`, run CPU evidence:

```bash
.venv/bin/python run_echosat_v2_weighted_equivalence.py \
  --manifest runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv \
  --budget-type cpu \
  --budget-value 5 \
  --repeats 0 1 2 \
  --workers 4 \
  --external-timeout 60 \
  --output runs/analysis/echosat_v2_weighted_equivalence_cpu.csv

.venv/bin/python audit_echosat_v2_weighted_equivalence.py \
  --input runs/analysis/echosat_v2_weighted_equivalence_cpu.csv \
  --gate-mode cpu \
  --expected-repeats 0 1 2
```

Expected: zero missing pairs, zero external timeouts, exact deterministic
search equality, and zero CPU-limit result/coverage loss. Any failure keeps
Task 4 blocked.

## Task 4: Emit Variable-Level Orbit Certification

**Files:**
- Modify: `build_echosat_orbit_certification.py:88`
- Create: `tests/test_echosat_v2_orbit_features.py`
- Create at runtime: `runs/analysis/echosat_v2_orbit_variables.csv`

- [ ] **Step 1: Write the failing certification expansion test**

```python
# tests/test_echosat_v2_orbit_features.py
import pandas as pd

from build_echosat_orbit_certification import expand_orbit_variables


def test_expand_orbit_variables_emits_one_row_per_variable() -> None:
    orbit_rows = pd.DataFrame(
        [
            {
                "cnf_path": "data/a.cnf",
                "family": "complete_coloring",
                "control_type": "strong_symmetry",
                "symmetry_strength": "strong",
                "base_instance_id": "a",
                "variant": "base",
                "orbit_id": "orbit-1",
                "vars": "1 3",
                "orbit_size": 2,
                "structure_type": "coloring",
                "orbit_confidence": 1.0,
                "valid_for_training": True,
                "needs_refinement": False,
            }
        ]
    )
    variables = expand_orbit_variables(orbit_rows)
    assert variables["variable_id"].tolist() == [1, 3]
    assert variables["orbit_index"].tolist() == [0, 0]
    assert variables["valid_orbit_mask"].tolist() == [True, True]
```

- [ ] **Step 2: Run the test and verify the helper is missing**

Run:

```bash
pytest -q tests/test_echosat_v2_orbit_features.py::test_expand_orbit_variables_emits_one_row_per_variable
```

Expected: import failure for `expand_orbit_variables`.

- [ ] **Step 3: Implement deterministic variable expansion**

Add:

```python
def expand_orbit_variables(orbit_rows: pd.DataFrame) -> pd.DataFrame:
    output: list[dict[str, Any]] = []
    group_columns = ["cnf_path", "base_instance_id", "variant"]
    for _, instance in orbit_rows.groupby(group_columns, sort=True):
        ordered = instance.sort_values(["orbit_id", "orbit_size"], kind="stable")
        for orbit_index, (_, row) in enumerate(ordered.iterrows()):
            variables = sorted(int(value) for value in str(row["vars"]).split())
            for variable_id in variables:
                output.append(
                    {
                        "cnf_path": row["cnf_path"],
                        "family": row["family"],
                        "control_type": row["control_type"],
                        "symmetry_strength": row["symmetry_strength"],
                        "base_instance_id": row["base_instance_id"],
                        "variant": row["variant"],
                        "variable_id": variable_id,
                        "orbit_id": row["orbit_id"],
                        "orbit_index": orbit_index,
                        "orbit_size": int(row["orbit_size"]),
                        "structure_type": row["structure_type"],
                        "orbit_confidence": float(row["orbit_confidence"]),
                        "valid_orbit_mask": bool(row["valid_for_training"]),
                        "needs_refinement": bool(row["needs_refinement"]),
                    }
                )
    return pd.DataFrame(output).sort_values(
        ["base_instance_id", "variant", "variable_id"]
    ).reset_index(drop=True)
```

Extend CLI arguments:

```python
parser.add_argument(
    "--out-variable-csv",
    type=Path,
    default=ROOT / "runs/analysis/echosat_v2_orbit_variables.csv",
)
```

After writing the orbit table:

```python
variables = expand_orbit_variables(out)
variable_path = resolve(args.out_variable_csv)
variable_path.parent.mkdir(parents=True, exist_ok=True)
variables.to_csv(variable_path, index=False)
```

- [ ] **Step 4: Add random-control and uniqueness tests**

```python
def test_expand_orbit_variables_preserves_invalid_control_mask() -> None:
    orbit_rows = pd.DataFrame(
        [
            {
                "cnf_path": "data/control.cnf",
                "family": "random_3sat_control",
                "control_type": "non_symmetric_control",
                "symmetry_strength": "none",
                "base_instance_id": "control",
                "variant": "base",
                "orbit_id": "singleton:1",
                "vars": "1",
                "orbit_size": 1,
                "structure_type": "none",
                "orbit_confidence": 0.0,
                "valid_for_training": False,
                "needs_refinement": False,
            }
        ]
    )
    variables = expand_orbit_variables(orbit_rows)
    assert variables["variable_id"].is_unique
    assert not variables["valid_orbit_mask"].item()
    assert variables["orbit_confidence"].item() == 0.0
```

- [ ] **Step 5: Run tests and rebuild certification artifacts**

Run:

```bash
pytest -q tests/test_echosat_v2_orbit_features.py
python build_echosat_orbit_certification.py \
  --manifest runs/analysis/echosat_symmetry_grpo_v1_canonical_manifest.csv \
  --out-csv runs/analysis/echosat_v2_orbit_certification.csv \
  --out-variable-csv runs/analysis/echosat_v2_orbit_variables.csv \
  --doc docs/echosat_v2_orbit_certification.md
```

Expected: `2 passed`; variable CSV contains exactly one row per `(cnf_path, variable_id)` and random controls have no true `valid_orbit_mask` rows.

- [ ] **Step 6: Commit Task 4**

```bash
git add build_echosat_orbit_certification.py tests/test_echosat_v2_orbit_features.py docs/echosat_v2_orbit_certification.md
git commit -m "feat: emit variable-level orbit certification"
```

## Task 5: Attach Orbit and Orbit-Relative Event Features

**Files:**
- Create: `src/echosat/orbit_features.py`
- Modify: `src/echosat/__init__.py`
- Modify: `train_rlaf.py:452`
- Modify: `tests/test_echosat_v2_orbit_features.py`

- [ ] **Step 1: Write failing orbit feature tensor tests**

Append:

```python
import torch
from torch_geometric.data import HeteroData

from src.echosat.orbit_features import (
    ORBIT_STRUCTURE_TYPES,
    OrbitFeatureStore,
    attach_orbit_features,
    orbit_relative_event_features,
)


def test_orbit_relative_features_are_computed_within_each_orbit() -> None:
    event_state = torch.tensor([[1.0], [3.0], [10.0]])
    orbit_index = torch.tensor([0, 0, 1])
    valid_mask = torch.tensor([True, True, False])
    relative = orbit_relative_event_features(event_state, orbit_index, valid_mask)
    assert relative.shape == (3, 5)
    assert torch.allclose(relative[:2, 0], torch.tensor([0.0, 1.0]))
    assert torch.equal(relative[2], torch.zeros(5))


def test_attach_orbit_features_fails_closed_for_missing_certification() -> None:
    graph = HeteroData()
    graph["var"].num_nodes = 2
    updated = attach_orbit_features(graph, rows=None)
    assert torch.equal(updated["var"].valid_orbit_mask, torch.zeros(2, dtype=torch.bool))
    assert torch.equal(updated["var"].orbit_confidence, torch.zeros(2))
    assert updated["var"].orbit_features.shape[1] == 3 + len(ORBIT_STRUCTURE_TYPES)
```

- [ ] **Step 2: Run tests and verify the module is missing**

Run:

```bash
pytest -q tests/test_echosat_v2_orbit_features.py -k 'relative or missing'
```

Expected: import failure for `src.echosat.orbit_features`.

- [ ] **Step 3: Implement the feature store and graph attachment**

```python
# src/echosat/orbit_features.py
from __future__ import annotations

from copy import copy
from dataclasses import dataclass

import pandas as pd
import torch
from torch import Tensor
from torch_geometric.data import HeteroData


ORBIT_STRUCTURE_TYPES = (
    "unknown",
    "php",
    "coloring",
    "row_column",
    "torus",
    "graph_automorphism",
    "cardinality",
    "tseitin",
    "none",
)
ORBIT_STRUCTURE_TO_INDEX = {name: index for index, name in enumerate(ORBIT_STRUCTURE_TYPES)}


@dataclass(frozen=True)
class OrbitFeatureStore:
    rows_by_cnf_id: dict[int, pd.DataFrame]

    @classmethod
    def from_tables(cls, variable_rows: pd.DataFrame, metadata: pd.DataFrame) -> "OrbitFeatureStore":
        key_columns = ["base_instance_id", "variant"]
        merged = variable_rows.merge(metadata[["cnf_id", *key_columns]], on=key_columns, how="inner")
        return cls({int(cnf_id): group.copy() for cnf_id, group in merged.groupby("cnf_id", sort=False)})

    def rows_for(self, cnf_id: int) -> pd.DataFrame | None:
        return self.rows_by_cnf_id.get(int(cnf_id))


def attach_orbit_features(data: HeteroData, rows: pd.DataFrame | None) -> HeteroData:
    data = copy(data)
    num_vars = int(getattr(data["var"], "num_nodes", data["lit"].num_nodes // 2))
    orbit_index = torch.full((num_vars,), -1, dtype=torch.long)
    orbit_size = torch.ones(num_vars, dtype=torch.float32)
    confidence = torch.zeros(num_vars, dtype=torch.float32)
    valid_mask = torch.zeros(num_vars, dtype=torch.bool)
    structure = torch.zeros((num_vars, len(ORBIT_STRUCTURE_TYPES)), dtype=torch.float32)
    structure[:, ORBIT_STRUCTURE_TO_INDEX["unknown"]] = 1.0
    if rows is not None:
        for row in rows.itertuples(index=False):
            idx = int(row.variable_id) - 1
            if 0 <= idx < num_vars:
                orbit_index[idx] = int(row.orbit_index)
                orbit_size[idx] = float(row.orbit_size)
                confidence[idx] = float(row.orbit_confidence)
                valid_mask[idx] = bool(row.valid_orbit_mask)
                structure[idx].zero_()
                structure_name = str(row.structure_type)
                structure_index = ORBIT_STRUCTURE_TO_INDEX.get(
                    structure_name,
                    ORBIT_STRUCTURE_TO_INDEX["unknown"],
                )
                structure[idx, structure_index] = 1.0
    data["var"].num_nodes = num_vars
    data["var"].orbit_index = orbit_index
    data["var"].orbit_size_log = torch.log1p(orbit_size)
    data["var"].orbit_confidence = confidence
    data["var"].valid_orbit_mask = valid_mask
    data["var"].orbit_features = torch.cat(
        [
            torch.stack([valid_mask.float(), confidence, torch.log1p(orbit_size)], dim=1),
            structure,
        ],
        dim=1,
    )
    return data
```

- [ ] **Step 4: Implement orbit-relative event features**

```python
def orbit_relative_event_features(event_state: Tensor, orbit_index: Tensor, valid_mask: Tensor) -> Tensor:
    event_state = event_state.to(dtype=torch.float32)
    channels = []
    for channel in range(event_state.shape[1]):
        values = event_state[:, channel]
        output = torch.zeros((values.shape[0], 5), dtype=torch.float32, device=values.device)
        for orbit in torch.unique(orbit_index[valid_mask]):
            mask = valid_mask & orbit_index.eq(orbit)
            group = values[mask]
            if group.numel() == 0:
                continue
            order = torch.argsort(group, stable=True)
            ranks = torch.zeros_like(group)
            if group.numel() > 1:
                ranks[order] = torch.arange(group.numel(), device=group.device) / float(group.numel() - 1)
            mean = group.mean()
            std = group.std(unbiased=False)
            share = group / group.abs().sum().clamp_min(1.0e-9)
            variance = torch.full_like(group, group.var(unbiased=False))
            coverage = torch.full_like(group, group.ne(0).float().mean())
            output[mask] = torch.stack(
                [ranks, (group - mean) / std.clamp_min(1.0e-6), share, variance, coverage], dim=1
            )
        channels.append(output)
    return torch.cat(channels, dim=1)
```

- [ ] **Step 5: Attach features in the training data path**

Add helpers in `train_rlaf.py`:

```python
from src.echosat.orbit_features import OrbitFeatureStore, attach_orbit_features, orbit_relative_event_features


def attach_echosat_v2_orbits(data_list: list, store: OrbitFeatureStore | None) -> list:
    updated = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        item = attach_orbit_features(data, None if store is None else store.rows_for(cnf_id))
        if hasattr(item["var"], "event_state"):
            item["var"].orbit_event_state = orbit_relative_event_features(
                item["var"].event_state,
                item["var"].orbit_index,
                item["var"].valid_orbit_mask,
            )
        updated.append(item)
    return updated
```

Load `training.echosat_orbit_variable_path`, build the store from `dataset_metadata`, and call `attach_echosat_v2_orbits` immediately after warmup event state is attached for train and validation.

- [ ] **Step 6: Run focused tests**

Run:

```bash
pytest -q tests/test_echosat_v2_orbit_features.py
```

Expected: all orbit certification, fail-closed, and relative-feature tests pass.

- [ ] **Step 7: Commit Task 5**

```bash
git add src/echosat/__init__.py src/echosat/orbit_features.py train_rlaf.py tests/test_echosat_v2_orbit_features.py
git commit -m "feat: attach orbit-relative event features"
```

## Task 6: Add Weight-Only Evidence-Masked Adapter Fusion

**Files:**
- Modify: `src/model/model.py:15`
- Modify: `src/model/model.py:534`
- Modify: `src/model/model.py:599`
- Modify: `tests/test_event_adapter.py`

- [ ] **Step 1: Write failing weight-only and evidence-mask tests**

Append to `tests/test_event_adapter.py`:

```python
def test_weight_only_residual_never_changes_phase_logit():
    model = GNN(
        channels=4,
        lit_feat_dim=1,
        cls_feat_dim=1,
        num_layers=1,
        out_dim=2,
        var_state_dim=EVENT_VAR_STATE_DIM,
        orbit_feature_dim=12,
        orbit_event_state_dim=25,
        event_adapter_enabled=True,
        event_adapter_hidden_dim=8,
        event_adapter_fusion="weight_only_residual",
        event_adapter_require_valid_orbit=True,
    )
    batch = next(iter(DataLoader([make_graph()], batch_size=1)))
    base_y, cache = model(batch, return_cache=True)
    with torch.no_grad():
        model.event_adapter[-1].bias.copy_(torch.tensor([4.0, 2.0]))
    batch["var"].num_nodes = 2
    batch["var"].base_embedding = cache["base_embedding"]
    batch["var"].base_y = cache["base_y"]
    batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM))
    batch["var"].orbit_features = torch.ones((2, 12))
    batch["var"].orbit_event_state = torch.ones((2, 25))
    batch["var"].valid_orbit_mask = torch.tensor([True, True])
    batch["var"].orbit_event_variance = torch.tensor([1.0, 1.0])
    output = model(batch)
    assert torch.equal(output[:, 0], base_y[:, 0])
    assert torch.allclose(output[:, 1], base_y[:, 1] + 2.0)


def test_weight_only_residual_is_zero_without_valid_orbit_or_event_variance():
    model = GNN(
        channels=4,
        lit_feat_dim=1,
        cls_feat_dim=1,
        num_layers=1,
        out_dim=2,
        var_state_dim=EVENT_VAR_STATE_DIM,
        orbit_feature_dim=12,
        orbit_event_state_dim=25,
        event_adapter_enabled=True,
        event_adapter_hidden_dim=8,
        event_adapter_fusion="weight_only_residual",
        event_adapter_require_valid_orbit=True,
        event_adapter_min_orbit_event_variance=0.1,
    )
    batch = next(iter(DataLoader([make_graph()], batch_size=1)))
    base_y, cache = model(batch, return_cache=True)
    with torch.no_grad():
        model.event_adapter[-1].bias.copy_(torch.tensor([0.0, 2.0]))
    batch["var"].num_nodes = 2
    batch["var"].base_embedding = cache["base_embedding"]
    batch["var"].base_y = cache["base_y"]
    batch["var"].event_state = torch.ones((2, EVENT_VAR_STATE_DIM))
    batch["var"].orbit_features = torch.ones((2, 12))
    batch["var"].orbit_event_state = torch.ones((2, 25))
    batch["var"].valid_orbit_mask = torch.tensor([False, True])
    batch["var"].orbit_event_variance = torch.tensor([1.0, 0.2])
    output = model(batch)
    delta = output - base_y
    assert delta[:, 1].tolist() == [0.0, 2.0]
```

Use the existing test helpers in `tests/test_event_adapter.py`; add the two small helper parameters rather than duplicating model construction.

- [ ] **Step 2: Run the tests and verify the new fusion is rejected**

Run:

```bash
pytest -q tests/test_event_adapter.py -k 'weight_only_residual'
```

Expected: failure with `Unknown event adapter fusion 'weight_only_residual'`.

- [ ] **Step 3: Add model configuration fields**

Add constructor arguments:

```python
orbit_feature_dim: int = 0,
orbit_event_state_dim: int = 0,
event_adapter_min_orbit_event_variance: float = 0.0,
event_adapter_require_valid_orbit: bool = False,
```

Store them on the model. Change the adapter input layer to consume all explicit evidence:

```python
self.orbit_feature_dim = int(orbit_feature_dim)
self.orbit_event_state_dim = int(orbit_event_state_dim)
self.event_adapter = nn.Sequential(
    nn.Linear(
        self.var_embedding_dim
        + self.var_state_dim
        + self.orbit_feature_dim
        + self.orbit_event_state_dim,
        int(event_adapter_hidden_dim),
    ),
    nn.SiLU(inplace=True),
    nn.Linear(int(event_adapter_hidden_dim), out_dim),
)
```

Map Hydra keys in `init_model`:

```python
"orbit_feature_dim": int(cfg_value(adapter_cfg, "orbit_feature_dim", 0)),
"orbit_event_state_dim": int(cfg_value(adapter_cfg, "orbit_event_state_dim", 0)),
"event_adapter_min_orbit_event_variance": float(cfg_value(adapter_cfg, "min_orbit_event_variance", 0.0)),
"event_adapter_require_valid_orbit": bool(cfg_value(adapter_cfg, "require_valid_orbit", False)),
```

- [ ] **Step 4: Implement evidence masks and weight-only fusion**

At the start of `_apply_event_adapter`, validate and concatenate orbit evidence:

```python
adapter_inputs = [base_embedding, var_state]
if self.orbit_feature_dim > 0:
    orbit_features = getattr(data["var"], "orbit_features", None)
    if orbit_features is None or orbit_features.shape[1] != self.orbit_feature_dim:
        orbit_features = torch.zeros(
            (base_y.shape[0], self.orbit_feature_dim),
            dtype=torch.float32,
            device=base_y.device,
        )
    adapter_inputs.append(orbit_features.to(dtype=torch.float32, device=base_y.device))
if self.orbit_event_state_dim > 0:
    orbit_event_state = getattr(data["var"], "orbit_event_state", None)
    if orbit_event_state is None or orbit_event_state.shape[1] != self.orbit_event_state_dim:
        orbit_event_state = torch.zeros(
            (base_y.shape[0], self.orbit_event_state_dim),
            dtype=torch.float32,
            device=base_y.device,
        )
    adapter_inputs.append(orbit_event_state.to(dtype=torch.float32, device=base_y.device))
delta = self.event_adapter(torch.cat(adapter_inputs, dim=1))
```

Replace the previous `delta = self.event_adapter(torch.cat([base_embedding, var_state], dim=1))` line. Then, after existing variable/graph/selector gates, apply:

```python
evidence_mask = torch.ones(delta.shape[0], dtype=torch.float32, device=delta.device)
if self.event_adapter_require_valid_orbit:
    valid = getattr(data["var"], "valid_orbit_mask", None)
    if valid is None:
        evidence_mask.zero_()
    else:
        evidence_mask *= valid.to(dtype=torch.float32, device=delta.device)
if self.event_adapter_min_orbit_event_variance > 0.0:
    variance = getattr(data["var"], "orbit_event_variance", None)
    if variance is None:
        evidence_mask.zero_()
    else:
        evidence_mask *= variance.to(dtype=torch.float32, device=delta.device).ge(
            self.event_adapter_min_orbit_event_variance
        ).float()
delta = delta * evidence_mask.view(-1, 1)
```

Add the fusion before existing `polarity_gated_residual` handling:

```python
if self.event_adapter_fusion == "weight_only_residual":
    weight_delta = torch.zeros_like(delta)
    if delta.shape[1] > 1:
        weight_delta[:, 1] = delta[:, 1]
    delta = weight_delta
elif self.event_adapter_fusion == "polarity_gated_residual":
    polarity_delta = torch.zeros_like(delta)
    if delta.shape[1] > 1:
        if self.event_adapter_polarity_gate_indices:
            indices = [
                idx
                for idx in self.event_adapter_polarity_gate_indices
                if idx < var_state.shape[1]
            ]
            evidence = (
                var_state[:, indices].clamp(0.0, 1.0).mean(dim=1, keepdim=True)
                if indices
                else torch.zeros((var_state.shape[0], 1), device=base_y.device)
            )
        else:
            evidence = torch.zeros((var_state.shape[0], 1), device=base_y.device)
        gate = self.event_adapter_polarity_gate_min + (
            1.0 - self.event_adapter_polarity_gate_min
        ) * 0.5 * evidence
        polarity_delta[:, 1:2] = delta[:, 1:2] * gate
    delta = polarity_delta
elif self.event_adapter_fusion not in {"residual", "sbe"}:
    raise ValueError(f"Unknown event adapter fusion {self.event_adapter_fusion!r}")
```

When orbit-relative features are attached, set:

```python
data["var"].orbit_event_variance = data["var"].orbit_event_state[:, 3::5].mean(dim=1)
```

- [ ] **Step 5: Run adapter and orbit feature tests**

Run:

```bash
pytest -q tests/test_event_adapter.py tests/test_echosat_v2_orbit_features.py
```

Expected: all existing adapter behavior remains green and both new v2 tests pass.

- [ ] **Step 6: Commit Task 6**

```bash
git add src/model/model.py train_rlaf.py tests/test_event_adapter.py tests/test_echosat_v2_orbit_features.py
git commit -m "feat: add weight-only orbit-masked adapter"
```

## Task 7: Add the Constrained v2 Objective Before GRPO Normalization

**Files:**
- Create: `src/echosat/objective_v2.py`
- Modify: `src/policy/evaluate.py:226`
- Modify: `train_rlaf.py:35`
- Modify: `train_rlaf.py:875`
- Modify: `train_rlaf.py:1601`
- Create: `tests/test_echosat_v2_objective.py`

- [ ] **Step 1: Write failing blocked-normalization tests**

```python
# tests/test_echosat_v2_objective.py
import pandas as pd

from src.echosat.objective_v2 import attach_masked_grpo_advantage, worst_variant_scores
from src.policy.evaluate import compute_plain_solver_stats


def test_blocked_rows_do_not_change_eligible_group_normalization() -> None:
    base = pd.DataFrame(
        [
            {"cnf_id": 1, "sample_id": 0, "echosat_cost": 1.0, "v2_positive_eligible": True, "echosat_advantage_weight": 1.0},
            {"cnf_id": 1, "sample_id": 1, "echosat_cost": 3.0, "v2_positive_eligible": True, "echosat_advantage_weight": 1.0},
        ]
    )
    with_blocked = pd.concat(
        [
            base,
            pd.DataFrame(
                [{"cnf_id": 1, "sample_id": 2, "echosat_cost": -1000.0, "v2_positive_eligible": False, "echosat_advantage_weight": 1.0}]
            ),
        ],
        ignore_index=True,
    )
    expected = attach_masked_grpo_advantage(base, target_stat="echosat_cost")
    actual = attach_masked_grpo_advantage(with_blocked, target_stat="echosat_cost")
    assert actual.loc[:1, "grpo_raw_advantage"].tolist() == expected["grpo_raw_advantage"].tolist()
    assert actual.loc[2, "grpo_final_advantage"] <= 0.0


def test_worst_variant_score_uses_minimum_variant() -> None:
    rows = pd.DataFrame(
        [
            {"base_instance_id": "a", "variant": "base", "search_score": 0.3},
            {"base_instance_id": "a", "variant": "perm_seed1730", "search_score": -0.2},
            {"base_instance_id": "a", "variant": "perm_seed1731", "search_score": 0.1},
        ]
    )
    scored = worst_variant_scores(rows, score_column="search_score")
    assert scored["v2_worst_variant_score"].tolist() == [-0.2, -0.2, -0.2]


def test_compute_plain_solver_stats_does_not_attach_weight_parameters(monkeypatch) -> None:
    calls = []

    def fake_solve(clauses, var_params, **params):
        calls.append(var_params)
        return {"Result": "SATISFIABLE", "decisions": 1, "conflicts": 0, "CPU time": 0.01}

    monkeypatch.setattr("src.policy.evaluate.solve_cnf", fake_solve)
    graph = HeteroData()
    graph.cnf_id = torch.tensor(0)
    dataset = SimpleNamespace(
        cnf_list=[SimpleNamespace(clauses=[[1]])],
        id_to_file={0: "a.cnf"},
    )
    stats = compute_plain_solver_stats(dataset=dataset, data_list=[graph], num_workers=1, solver="glucose")
    assert calls == [None]
    assert stats.loc[0, "Result"] == "SATISFIABLE"
```

Add these imports to the test:

```python
from types import SimpleNamespace

import torch
from torch_geometric.data import HeteroData
```

- [ ] **Step 2: Run tests and verify the module is missing**

Run:

```bash
pytest -q tests/test_echosat_v2_objective.py
```

Expected: import failure for `src.echosat.objective_v2`.

- [ ] **Step 3: Implement worst-variant scoring**

```python
# src/echosat/objective_v2.py
from __future__ import annotations

import numpy as np
import pandas as pd


def worst_variant_scores(rows: pd.DataFrame, *, score_column: str) -> pd.DataFrame:
    out = rows.copy()
    score = pd.to_numeric(out[score_column], errors="coerce").fillna(0.0)
    variant_mean = score.groupby(
        [out["base_instance_id"], out["variant"]], sort=False
    ).transform("mean")
    out["v2_worst_variant_score"] = variant_mean.groupby(
        out["base_instance_id"], sort=False
    ).transform("min")
    return out
```

- [ ] **Step 4: Add an unweighted plain solver-stat path**

Add to `src/policy/evaluate.py`:

```python
def compute_plain_solver_stats(
    dataset: DimacsCNFDataset,
    data_list: list[HeteroData],
    num_workers: int = 8,
    **solver_params: Any,
) -> pd.DataFrame:
    inputs = []
    for data in data_list:
        cnf_id = int(data.cnf_id.item() if hasattr(data.cnf_id, "item") else data.cnf_id)
        cnf = dataset.cnf_list[cnf_id]
        inputs.append((cnf_id, 0, cnf, None, solver_params))
    stats = Parallel(n_jobs=num_workers, prefer="threads")(
        delayed(solver_pool_fn)(item) for item in inputs
    )
    frame = pd.DataFrame.from_records(stats)
    frame["file"] = [dataset.id_to_file[int(cnf_id)] for cnf_id in frame["cnf_id"]]
    return frame
```

- [ ] **Step 5: Implement masked GRPO normalization**

```python
def attach_masked_grpo_advantage(rows: pd.DataFrame, *, target_stat: str) -> pd.DataFrame:
    out = rows.copy()
    target = pd.to_numeric(out[target_stat], errors="coerce").replace([np.inf, -np.inf], np.nan)
    target = target.fillna(target[np.isfinite(target)].max() if np.isfinite(target).any() else 0.0)
    eligible = out["v2_positive_eligible"].fillna(False).astype(bool)
    group_mean = pd.Series(0.0, index=out.index)
    group_std = pd.Series(0.0, index=out.index)
    eligible_rows = out.loc[eligible, ["cnf_id"]].copy()
    eligible_rows["target"] = target.loc[eligible]
    grouped = eligible_rows.groupby("cnf_id", sort=False)["target"]
    group_mean.loc[eligible] = grouped.transform("mean")
    group_std.loc[eligible] = grouped.transform("std").fillna(0.0)
    raw = pd.Series(0.0, index=out.index)
    raw.loc[eligible] = -(
        target.loc[eligible] - group_mean.loc[eligible]
    ) / (group_std.loc[eligible] + 1.0e-8)
    raw = raw.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    blocked_source = (
        out["v2_blocked_penalty"]
        if "v2_blocked_penalty" in out.columns
        else pd.Series(0.0, index=out.index)
    )
    blocked_penalty = pd.to_numeric(blocked_source, errors="coerce").fillna(0.0)
    raw.loc[~eligible] = -blocked_penalty.loc[~eligible].clip(lower=0.0)
    weight_source = (
        out["echosat_advantage_weight"]
        if "echosat_advantage_weight" in out.columns
        else pd.Series(1.0, index=out.index)
    )
    weight = pd.to_numeric(weight_source, errors="coerce").fillna(1.0)
    final = raw * weight
    out["grpo_target_value"] = target
    out["grpo_group_mean_cost"] = group_mean
    out["grpo_group_std_cost"] = group_std
    out["grpo_raw_advantage_unclamped"] = raw
    out["grpo_raw_advantage"] = raw
    out["grpo_weighted_advantage_before_clamp"] = final
    out["grpo_final_advantage"] = final
    out["advantage"] = final
    return out
```

- [ ] **Step 6: Add v2 eligibility and hard blocks to target construction**

Add `symmetry_grpo_v2` to supported EchoSAT target modes. After calculating adapter-vs-static decisions/conflicts and risk columns, set:

```python
search_ok = (decision_delta < -eps_dec) & (conflict_delta < -eps_conf)
plain_frame = baseline_stats_by_name["plain_unguided"].sort_values(
    ["cnf_id", "sample_id"]
).drop_duplicates("cnf_id").set_index("cnf_id")
plain_result = plain_frame["Result"].astype(str).reindex(cnf_ids).fillna("INDETERMINATE")
plain_solved = plain_result.isin({"SATISFIABLE", "UNSATISFIABLE"}).to_numpy(dtype=bool)
guided_solved = solved_mask(out).to_numpy(dtype=bool)
lost_plain_solved = plain_solved & ~guided_solved
blocked = (
    is_control.to_numpy(dtype=bool)
    | result_mismatch
    | lost_plain_solved
    | near_cap_mask
    | (weighted_risk > 0.0)
    | (e_sym <= 0.0)
    | ~search_ok
)
out["v2_positive_eligible"] = ~blocked
out["v2_blocked_penalty"] = (
    lost_plain_solved.astype(float) * float(cfg_get(cfg.training, "echosat_v2_plain_loss_penalty", 20.0))
    + result_mismatch.astype(float) * float(cfg_get(cfg.training, "echosat_result_mismatch_penalty", 20.0))
    + search_blowup.astype(float) * float(cfg_get(cfg.training, "echosat_v2_search_blowup_penalty", 4.0))
)
out["search_score"] = decision_reduction + conflict_reduction
out = worst_variant_scores(out, score_column="search_score")
out["echosat_cost"] += float(cfg_get(cfg.training, "echosat_v2_worst_variant_weight", 1.0)) * np.maximum(
    -out["v2_worst_variant_score"].to_numpy(dtype=float), 0.0
)
```

Add the plain baseline to both train and validation maps:

```python
baseline_stats_by_name["plain_unguided"] = compute_plain_solver_stats(
    dataset=dataset,
    data_list=data_list,
    num_workers=cfg.solver.num_workers,
    solver="glucose",
    **solver_params(cfg),
)
```

- [ ] **Step 7: Delegate v2 normalization in `attach_grpo_advantage_columns`**

At the start of the function:

```python
if str(cfg_get(cfg.training, "echosat_target_mode", "")).lower() == "symmetry_grpo_v2":
    from src.echosat.objective_v2 import attach_masked_grpo_advantage

    return attach_masked_grpo_advantage(
        solver_stats,
        target_stat=str(cfg.training.target_stat),
    )
```

Leave all v1.x behavior unchanged.

- [ ] **Step 8: Run objective tests and v1.8 regression tests**

Run:

```bash
pytest -q \
  tests/test_echosat_v2_objective.py \
  tests/test_echosat_symmetry_grpo_v1_8_train_target.py \
  tests/test_echosat_symmetry_grpo_v1_8_reward_replay.py
```

Expected: v2 tests pass and existing v1.8 behavior remains unchanged.

- [ ] **Step 9: Commit Task 7**

```bash
git add src/echosat/objective_v2.py src/policy/evaluate.py train_rlaf.py tests/test_echosat_v2_objective.py
git commit -m "feat: add constrained EchoSAT v2 objective"
```

## Task 8: Add the Stage 4 Configuration and Offline Replay

**Files:**
- Create: `configs/config_train_rlaf_echosat_v2_stage4_replay.yaml`
- Create: `replay_echosat_v2_objective.py`
- Modify: `train_rlaf.py:2025`
- Create: `tests/test_echosat_v2_replay.py`
- Create at runtime: `runs/analysis/echosat_v2_stage4_reward_replay/rows.csv`
- Create at runtime: `runs/analysis/echosat_v2_stage4_reward_replay/checks.csv`
- Create at runtime: `docs/echosat_v2_stage4_reward_replay.md`

- [ ] **Step 1: Write failing replay acceptance tests**

```python
# tests/test_echosat_v2_replay.py
import pandas as pd

from replay_echosat_v2_objective import build_checks


def test_build_checks_requires_blocked_rows_non_positive_and_valid_positives() -> None:
    rows = pd.DataFrame(
        [
            {"v2_positive_eligible": False, "grpo_final_advantage": 0.0, "base_instance_id": "blocked"},
            {"v2_positive_eligible": True, "grpo_final_advantage": 0.5, "base_instance_id": "positive"},
        ]
    )
    checks = build_checks(rows)
    assert bool(checks["passed"].all())
    assert set(checks["check"]) == {
        "blocked_rows_non_positive",
        "eligible_positive_exists",
        "all_v2_stage4_checks",
    }
```

- [ ] **Step 2: Run the test and verify the replay module is missing**

Run:

```bash
pytest -q tests/test_echosat_v2_replay.py
```

Expected: import failure for `replay_echosat_v2_objective`.

- [ ] **Step 3: Create the Stage 4 configuration**

```yaml
# configs/config_train_rlaf_echosat_v2_stage4_replay.yaml
# @package _global_

defaults:
  - config_train_rlaf_echosat_symmetry_grpo_v1_8_wc1_objectiverepair
  - _self_

model_name: GNN_Glucose_3SAT_EchoSAT_v2_Stage4_Replay
model_dir: runs/${model_name}

model:
  event_adapter:
    fusion: weight_only_residual
    orbit_feature_dim: 12
    orbit_event_state_dim: 100
    require_valid_orbit: true
    min_orbit_event_variance: 1.0e-6
    delta_clip: 0.25

training:
  echosat_target_mode: symmetry_grpo_v2
  echosat_orbit_certification_path: runs/analysis/echosat_v2_orbit_certification.csv
  echosat_orbit_variable_path: runs/analysis/echosat_v2_orbit_variables.csv
  echosat_v2_plain_loss_penalty: 20.0
  echosat_v2_search_blowup_penalty: 4.0
  echosat_v2_worst_variant_weight: 1.0
  echosat_replay_only: true
  iterations: 1
  cnf_per_iter: 48
  steps_per_iter: 0
  num_samples: 16

wandb:
  mode: disabled
```

- [ ] **Step 4: Add a no-optimization replay-only path**

Immediately after solver targets, GRPO advantages, metrics, and configured reward-replay artifacts have been written for an iteration, guard the `train_grpo` call:

```python
if bool(cfg_get(cfg.training, "echosat_replay_only", False)):
    print(f"Iteration {iteration}: replay-only mode; skipping optimizer")
    continue
```

Add a validation near configuration setup:

```python
if bool(cfg_get(cfg.training, "echosat_replay_only", False)) and not bool(
    cfg_get(cfg.training, "save_echosat_reward_replay", False)
):
    raise ValueError("echosat_replay_only requires save_echosat_reward_replay=true")
```

- [ ] **Step 5: Implement replay checks**

```python
# replay_echosat_v2_objective.py
from pathlib import Path
import argparse

import pandas as pd


def build_checks(rows: pd.DataFrame) -> pd.DataFrame:
    blocked = ~rows["v2_positive_eligible"].fillna(False).astype(bool)
    checks = [
        {
            "check": "blocked_rows_non_positive",
            "passed": not bool((pd.to_numeric(rows.loc[blocked, "grpo_final_advantage"], errors="coerce") > 1.0e-12).any()),
        },
        {
            "check": "eligible_positive_exists",
            "passed": bool((pd.to_numeric(rows.loc[~blocked, "grpo_final_advantage"], errors="coerce") > 1.0e-12).any()),
        },
    ]
    checks.append({"check": "all_v2_stage4_checks", "passed": all(row["passed"] for row in checks)})
    return pd.DataFrame(checks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--checks", type=Path, required=True)
    parser.add_argument("--doc", type=Path, required=True)
    args = parser.parse_args()
    rows = pd.read_csv(args.rows)
    checks = build_checks(rows)
    args.checks.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(args.checks, index=False)
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(
        "# EchoSAT v2 Stage 4 Reward Replay\n\n"
        + "\n".join(f"- {row.check}: `{bool(row.passed)}`" for row in checks.itertuples(index=False))
        + "\n",
        encoding="utf-8",
    )
    if not bool(checks.loc[checks["check"].eq("all_v2_stage4_checks"), "passed"].item()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests and generate one no-optimization reward replay**

Run:

```bash
pytest -q tests/test_echosat_v2_replay.py
python train_rlaf.py \
  --config-name config_train_rlaf_echosat_v2_stage4_replay \
  training.save_echosat_reward_replay=true \
  training.save_echosat_reward_replay_every=1 \
  training.echosat_reward_replay_dir=runs/analysis/echosat_v2_stage4_reward_replay
python replay_echosat_v2_objective.py \
  --rows runs/analysis/echosat_v2_stage4_reward_replay/iter=000000_solver_stats.csv \
  --checks runs/analysis/echosat_v2_stage4_reward_replay/checks.csv \
  --doc docs/echosat_v2_stage4_reward_replay.md
```

Expected: replay checks pass; blocked rows have no positive final advantage; at least one eligible symmetric row has positive advantage. Logs contain `replay-only mode; skipping optimizer`, and no optimizer step is performed.

- [ ] **Step 7: Commit Task 8**

```bash
git add configs/config_train_rlaf_echosat_v2_stage4_replay.yaml replay_echosat_v2_objective.py train_rlaf.py tests/test_echosat_v2_replay.py docs/echosat_v2_stage4_reward_replay.md
git commit -m "feat: add EchoSAT v2 Stage 4 reward replay"
```

## Task 9: Run the Stage 0-4 Acceptance Suite and Document the Decision

**Files:**
- Create: `run_echosat_v2_stage0_4_acceptance.py`
- Create: `tests/test_echosat_v2_stage0_4_acceptance.py`
- Create at runtime: `runs/analysis/echosat_v2_stage0_4_acceptance/checks.csv`
- Create at runtime: `docs/echosat_v2_stage0_4_acceptance.md`

- [ ] **Step 1: Write the failing aggregate acceptance test**

```python
# tests/test_echosat_v2_stage0_4_acceptance.py
import pandas as pd

from run_echosat_v2_stage0_4_acceptance import aggregate_checks


def test_aggregate_checks_requires_every_stage_to_pass() -> None:
    checks = aggregate_checks(
        reference_exists=True,
        equivalence=pd.DataFrame([{"accepted": True}, {"accepted": True}]),
        replay=pd.DataFrame([{"check": "all_v2_stage4_checks", "passed": True}]),
        orbit_variables=pd.DataFrame(
            [
                {"base_instance_id": "sym", "valid_orbit_mask": True, "orbit_confidence": 1.0},
                {"base_instance_id": "control", "valid_orbit_mask": False, "orbit_confidence": 0.0},
            ]
        ),
    )
    assert bool(checks["passed"].all())
```

- [ ] **Step 2: Run the test and verify the aggregate runner is missing**

Run:

```bash
pytest -q tests/test_echosat_v2_stage0_4_acceptance.py
```

Expected: import failure for `run_echosat_v2_stage0_4_acceptance`.

- [ ] **Step 3: Implement aggregate acceptance**

```python
# run_echosat_v2_stage0_4_acceptance.py
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parent


def aggregate_checks(
    *,
    reference_exists: bool,
    equivalence: pd.DataFrame,
    replay: pd.DataFrame,
    orbit_variables: pd.DataFrame,
) -> pd.DataFrame:
    controls = orbit_variables[
        orbit_variables["control_type"].astype(str).eq("non_symmetric_control")
    ]
    rows = [
        {"check": "reference_frozen", "passed": bool(reference_exists)},
        {"check": "neutral_equivalence", "passed": bool(equivalence["accepted"].all())},
        {
            "check": "controls_have_no_valid_orbits",
            "passed": not bool(controls["valid_orbit_mask"].astype(bool).any()),
        },
        {
            "check": "stage4_reward_replay",
            "passed": bool(
                replay.loc[replay["check"].eq("all_v2_stage4_checks"), "passed"].astype(bool).item()
            ),
        },
    ]
    rows.append({"check": "all_stage0_4_checks", "passed": all(row["passed"] for row in rows)})
    return pd.DataFrame(rows)


def main() -> None:
    reference = ROOT / "runs/analysis/echosat_v2_reference/reference.json"
    equivalence = pd.read_csv(ROOT / "runs/analysis/echosat_v2_weighted_equivalence/summary.csv")
    replay = pd.read_csv(ROOT / "runs/analysis/echosat_v2_stage4_reward_replay/checks.csv")
    orbit_variables = pd.read_csv(ROOT / "runs/analysis/echosat_v2_orbit_variables.csv")
    checks = aggregate_checks(
        reference_exists=reference.is_file(),
        equivalence=equivalence,
        replay=replay,
        orbit_variables=orbit_variables,
    )
    output = ROOT / "runs/analysis/echosat_v2_stage0_4_acceptance/checks.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(output, index=False)
    doc = ROOT / "docs/echosat_v2_stage0_4_acceptance.md"
    doc.write_text(
        "# EchoSAT v2 Stage 0-4 Acceptance\n\n"
        + "\n".join(f"- {row.check}: `{bool(row.passed)}`" for row in checks.itertuples(index=False))
        + "\n",
        encoding="utf-8",
    )
    if not bool(checks.loc[checks["check"].eq("all_stage0_4_checks"), "passed"].item()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run focused tests, broader symmetry tests, and syntax checks**

Run:

```bash
pytest -q \
  tests/test_echosat_v2_reference.py \
  tests/test_echosat_v2_weighted_equivalence.py \
  tests/test_echosat_v2_orbit_features.py \
  tests/test_event_adapter.py \
  tests/test_echosat_v2_objective.py \
  tests/test_echosat_v2_replay.py \
  tests/test_echosat_v2_stage0_4_acceptance.py \
  tests/test_symmetry_stress.py \
  tests/test_trace_distillation.py \
  tests/test_echosat_symmetry_grpo_v1_8_train_target.py
python3 -m py_compile \
  src/echosat/reference.py \
  src/echosat/equivalence.py \
  src/echosat/orbit_features.py \
  src/echosat/objective_v2.py \
  freeze_echosat_v2_reference.py \
  audit_echosat_v2_weighted_equivalence.py \
  replay_echosat_v2_objective.py \
  run_echosat_v2_stage0_4_acceptance.py
```

Expected: all selected tests pass and syntax checking exits `0`.

- [ ] **Step 5: Run the aggregate acceptance command**

Run:

```bash
python run_echosat_v2_stage0_4_acceptance.py
```

Expected: exits `0`, writes the acceptance CSV and Markdown, and reports every Stage 0-4 check as true. If neutral equivalence fails, stop here and diagnose the weighted solver; do not train a v2 checkpoint.

- [ ] **Step 6: Commit Task 9**

```bash
git add run_echosat_v2_stage0_4_acceptance.py tests/test_echosat_v2_stage0_4_acceptance.py docs/echosat_v2_stage0_4_acceptance.md
git commit -m "test: add EchoSAT v2 Stage 0-4 acceptance gate"
```

## Completion Gate

Stage 0-4 is complete only when all of the following are freshly verified:

- the frozen reference file exists and hashes all four reference artifacts;
- plain and neutral weighted Glucose match result, solved status, decisions, and conflicts on every formal equivalence pair;
- random controls have no valid certified orbit variables;
- missing orbit data produces zero valid masks;
- the adapter changes only the weight logit;
- invalid or weak-event variables receive zero adapter delta;
- blocked rows do not affect eligible GRPO normalization;
- worst-variant scoring propagates the minimum variant score to the whole base;
- v1.8 regression tests still pass;
- Stage 4 replay has no positive blocked advantages and retains eligible positives;
- `run_echosat_v2_stage0_4_acceptance.py` exits `0`.

Do not begin new checkpoint training, gate learning, or single-run solver injection until this completion gate passes.
