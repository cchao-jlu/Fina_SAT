# Vertex Cover Torus Valid Event Rows

日期：2026-06-08

## 结论

本轮选择补 `vertex_cover_torus` valid event rows，而不是先调 `permutation_consistency_weight`。

结果：

- `vertex_cover_torus` 从旧 trace 的 0 valid event rows 变为 12 个 valid/event-positive rows。
- `4x5_norat` 保留为 3 个 no-activity negative rows。
- 新 trace 含 57 个 event-role graphs；正式 manifest 含 60 行。
- 旧 `NegGatePermCons` checkpoint 在新 trace 上已能给 torus event rows 产生 adapter separation。
- 用新 trace 重训 `NegGatePermConsVC` 后，adapter separation 更强，但 variable-level permutation alignment 变差。

因此本轮完成的是“补 valid rows + 建立新基线”，不是 solver speedup。

## 实例改动

代码：

- `src/data/symmetry.py`
  - `vertex_cover_torus_cnf(..., cover_size=None)` 支持显式 `cover_size`。
  - 增加 `version="event"`。
  - 新增 `vertex_cover_torus_ladder_instances()`。
  - `default_symmetry_instances()` 改为包含 torus event ladder 和 `4x5_norat` stress。
- `tests/test_symmetry_stress.py`
  - 新增 torus ladder 单测。

ladder：

| instance | role |
| --- | --- |
| `vertex_cover_torus_3x4_k4_event` | event |
| `vertex_cover_torus_3x4_k5_event` | event |
| `vertex_cover_torus_3x5_k5_event` | event |
| `vertex_cover_torus_3x5_k6_event` | event |
| `vertex_cover_torus_4x5_norat` | no-activity stress |

## Static / Event Evidence

专项 static audit：

- doc: `docs/symmetry_vertex_cover_torus_static_audit.md`
- valid orbit rows: 15 / 15
- mean static `mu_range`: `2.26e-08`
- max static `mu_range`: `4.843e-08`

专项 event audit：

- doc: `docs/symmetry_vertex_cover_torus_event_audit.md`
- valid rollout rows: 12
- event-positive rows: 12
- no-solver-activity rows: 3
- mean event L2 valid: `3.542`
- max event L2 valid: `5.070`

Full event v3：

- doc: `docs/symmetry_refined_event_v3_audit.md`
- `vertex_cover_torus`: 15 orbit rows, 12 valid/event-positive rows, 3 no-solver-activity rows.

## Trace / Adapter Audits

Rebuilt trace:

- trace: `data/trace_distill/symmetry_event_trace.pt`
- stats: `runs/analysis/symmetry_event_trace_distill_stats.csv`
- graphs: 57

Old `NegGatePermCons` checkpoint on new trace:

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt`
- event audit: `docs/symmetry_adapter_neggate_permcons_vc_event_audit.md`
- alignment audit: `docs/symmetry_adapter_neggate_permcons_vc_permutation_alignment_audit.md`
- negative audit: `docs/symmetry_adapter_neggate_permcons_vc_negative_case_audit.md`

| metric | value |
| --- | ---: |
| valid adapter rows | 132 |
| torus valid adapter rows | 12 |
| mean adapter gain, all valid | 0.3339 |
| mean adapter gain, torus | 0.9740 |
| variable-level adapted `mu` MAE, all pairs | 0.2039 |
| variable-level adapted `mu` MAE, torus pairs | 0.2654 |
| negative violations | 0 |

Retrained `NegGatePermConsVC` on new trace:

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC/best.pt`
- event audit: `docs/symmetry_adapter_neggate_permcons_vc_retrained_event_audit.md`
- alignment audit: `docs/symmetry_adapter_neggate_permcons_vc_retrained_permutation_alignment_audit.md`
- negative audit: `docs/symmetry_adapter_neggate_permcons_vc_retrained_negative_case_audit.md`

| metric | old checkpoint on new trace | retrained VC checkpoint |
| --- | ---: | ---: |
| valid adapter rows | 132 | 132 |
| mean adapter gain, all valid | 0.3339 | 0.4299 |
| mean adapter gain, torus | 0.9740 | 1.4324 |
| variable-level adapted `mu` MAE, all pairs | 0.2039 | 0.2625 |
| variable-level adapted `mu` MAE, torus pairs | 0.2654 | 0.3738 |
| negative violations | 0 | 0 |

Interpretation:

The VC retrain increases event-conditioned separation, especially on torus, but worsens variable-level permutation alignment. The rollout itself is not permutation-invariant, and the current `permutation_consistency_weight = 0.25` is not strong enough to offset the stronger separation learned from the new torus rows.

## Next Step

Completed follow-up:

- `docs/symmetry_adapter_permcons_weight_sweep.md`
- selected checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt`
- reason: it keeps overall gain above the old checkpoint while reducing alignment MAE versus the 0.25 retrain.

```text
weight=0.5:
overall gain = 0.3500
torus gain = 1.1510
overall adapted mu MAE = 0.2139
torus adapted mu MAE = 0.3040
negative violations = 0
```

Heldout follow-up:

- rebuilt `data/trace_distill/symmetry_family_heldout/`
- torus heldout split: 42 train graphs, 15 heldout graphs
- 3 seeds: 1729, 1730, 1731
- training excludes `vertex_cover_torus`
- doc: `docs/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_multiseed_audit.md`

Result:

| metric | value |
| --- | ---: |
| heldout valid rows | 12 |
| positive-gain seeds | 3 / 3 |
| heldout gain mean | 0.8548 |
| heldout gain min / max | 0.7534 / 0.9485 |
| full W05 torus gain | 1.1510 |
| heldout minus full W05 gain | -0.2963 |

Do not move to solver speedup yet. The next representation step is to run the same W05 heldout protocol across all families on the 60-row trace, then decide whether the selected adapter is stable enough for a solver-level protocol.
