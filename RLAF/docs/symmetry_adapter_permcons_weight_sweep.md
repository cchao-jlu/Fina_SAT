# PermCons Weight Sweep on 60-Row Trace

日期：2026-06-08

## Setup

Only `trace.label.permutation_consistency_weight` was changed.
Everything else was kept from `config_train_trace_distill_symmetry`.

Checkpoints:

| model | weight | checkpoint |
| --- | ---: | --- |
| old checkpoint on new trace | 0.25, trained before torus event rows | `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt` |
| VC retrained baseline | 0.25 | `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC/best.pt` |
| weight sweep | 0.5 | `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt` |
| weight sweep | 1.0 | `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W10/best.pt` |

All audits use:

- trace: `data/trace_distill/symmetry_event_trace.pt`
- manifest: `runs/analysis/symmetry_stress_manifest.csv`
- event-state features: `enhanced`
- no solver speedup measurement.

## Summary

| model | valid rows | overall gain | torus gain | overall adapted `mu` MAE | torus adapted `mu` MAE | negative violations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| old PermCons on new trace | 132 | 0.3339 | 0.9740 | 0.2039 | 0.2654 | 0 |
| weight 0.25 retrained | 132 | 0.4299 | 1.4324 | 0.2625 | 0.3738 | 0 |
| weight 0.5 | 132 | 0.3500 | 1.1510 | 0.2139 | 0.3040 | 0 |
| weight 1.0 | 132 | 0.2534 | 0.8374 | 0.1534 | 0.2188 | 0 |

Interpretation:

- `weight=0.25` retrained maximizes separation but worsens alignment.
- `weight=1.0` gives the best alignment but suppresses overall gain below the old checkpoint's `0.3339` baseline.
- `weight=0.5` is the best compromise under the current criteria.

Selected checkpoint:

```text
runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt
```

It satisfies the requested compromise:

- overall alignment MAE `0.2139`, clearly below `0.2625`
- torus alignment MAE `0.3040`, clearly below `0.3738`
- overall gain `0.3500`, still above old checkpoint `0.3339`
- negative violations remain `0`

## Artifacts

Weight 0.5:

- `docs/symmetry_adapter_neggate_permcons_vc_w05_event_audit.md`
- `docs/symmetry_adapter_neggate_permcons_vc_w05_permutation_alignment_audit.md`
- `docs/symmetry_adapter_neggate_permcons_vc_w05_negative_case_audit.md`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w05_event_orbits.csv`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w05_permutation_alignment_pairs.csv`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w05_negative_case_summary.csv`

Weight 1.0:

- `docs/symmetry_adapter_neggate_permcons_vc_w10_event_audit.md`
- `docs/symmetry_adapter_neggate_permcons_vc_w10_permutation_alignment_audit.md`
- `docs/symmetry_adapter_neggate_permcons_vc_w10_negative_case_audit.md`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w10_event_orbits.csv`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w10_permutation_alignment_pairs.csv`
- `runs/analysis/symmetry_adapter_neggate_permcons_vc_w10_negative_case_summary.csv`

Sweep summary:

- `runs/analysis/symmetry_adapter_permcons_weight_sweep_summary.csv`

## Next Step

Completed:

- rebuilt family-heldout splits on the 57-graph trace
- reran `vertex_cover_torus` heldout 3-seed with `weight=0.5`
- result doc: `docs/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_multiseed_audit.md`
- ran the same `weight=0.5` heldout protocol for all 9 families
- all-family result doc: `docs/symmetry_adapter_permcons_w05_family_heldout_multiseed_audit.md`
- all-family no-activity guardrail summary: `runs/analysis/symmetry_adapter_permcons_w05_family_heldout_negative_guardrail_summary.csv`

Next step:

Define a solver-level protocol only after keeping the current representation constraints explicit: no solver-speedup claim is made by this sweep or by the heldout audits.
