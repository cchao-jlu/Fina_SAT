# NegGate + Permutation Consistency Adapter Audit

日期：2026-06-08

## 结论

本轮实现了 adapter 侧 variable-level permutation consistency loss，并重新训练 representation-only adapter：

- checkpoint: `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt`
- base checkpoint: `runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt`
- trace: `data/trace_distill/symmetry_event_trace.pt`
- permutation manifest: `runs/analysis/symmetry_stress_manifest.csv`
- loss weight: `permutation_consistency_weight = 0.25`
- output weights: `rho = 0.0`, `mu = 1.0`

结果是一个明确的 tradeoff：

- 逐变量 permutation alignment 改善：overall `adapted_mu_mae` 从 `0.18397` 降到 `0.16986`，相对下降约 `7.67%`。
- event representation separation 保留但略弱：overall valid `adapter_identity_gain` 从 `0.29771` 降到 `0.26994`。
- no-activity negative guardrail 仍然干净：`no_activity_event_nonzero` 和 `no_activity_zero_event` 都是 `0` violation。

这说明 PermCons v1 确实在压变量级编号/renaming 不一致，但还不是完整 equivariance proof；当前不能谈 solver speedup。

## 实现

新增训练目标：

```text
L_perm = || P^{-1} y_adapter(P(CNF)) - y_adapter(CNF) ||^2
```

实现位置：

- `src/training/trace_distill.py`
  - `PermutationConsistencyPair`
  - `build_permutation_consistency_pairs`
  - `align_new_to_old`
  - `permutation_consistency_loss`
  - `train_trace_distillation_epoch(..., permutation_pairs=...)`
- `train_trace_distill.py`
  - 读取 `trace.permutation_manifest_path`
  - 从 trace payload 的 `solver_stats` 和 manifest metadata 构造 base/permuted pairs
- `configs/config_train_trace_distill_symmetry.yaml`
  - 启用 `permutation_consistency_weight: 0.25`

Pair 构造只使用 metadata 中纯变量重命名的 `permutation`；如果 `sign_flips` 非全正则跳过。`event_audit_role == static_only` 的实例不进入 consistency loss。

## Variable-Level Alignment

审计脚本直接比较：

```text
P^{-1} y_adapter(P(CNF)) vs y_adapter(CNF)
```

产物：

- NegGate baseline: `docs/symmetry_adapter_neggate_permutation_alignment_audit.md`
- PermCons: `docs/symmetry_adapter_neggate_permcons_permutation_alignment_audit.md`
- CSV: `runs/analysis/symmetry_adapter_neggate_permcons_permutation_alignment_pairs.csv`

| family | pairs | NegGate mean adapted mu MAE | PermCons mean adapted mu MAE | relative reduction |
| --- | ---: | ---: | ---: | ---: |
| `complete_coloring` | 4 | 0.172946 | 0.159975 | 7.50% |
| `dominating_set_hex` | 6 | 0.133460 | 0.123746 | 7.28% |
| `even_colouring` | 2 | 0.042180 | 0.039910 | 5.38% |
| `php` | 4 | 0.169157 | 0.154900 | 8.43% |
| `php_exit_all` | 2 | 0.227898 | 0.213617 | 6.27% |
| `php_exit_single` | 4 | 0.076607 | 0.072605 | 5.22% |
| `subset_cardinality` | 2 | 0.312766 | 0.287503 | 8.08% |
| `tseitin_complete` | 4 | 0.469429 | 0.430330 | 8.33% |
| `vertex_cover_torus` | 2 | 1.234e-07 | 1.234e-07 | 0.00% |

Overall:

| model | mean adapted mu MAE |
| --- | ---: |
| NegGate | 0.1839668 |
| NegGate + PermCons | 0.1698590 |

## Event Separation Tradeoff

产物：

- PermCons event audit: `docs/symmetry_adapter_neggate_permcons_event_audit.md`
- CSV: `runs/analysis/symmetry_adapter_neggate_permcons_event_orbits.csv`

| family | valid rows | NegGate mean adapter gain | PermCons mean adapter gain | delta |
| --- | ---: | ---: | ---: | ---: |
| `complete_coloring` | 3 | 1.08054 | 0.93985 | -0.14069 |
| `dominating_set_hex` | 33 | 0.21882 | 0.20688 | -0.01193 |
| `even_colouring` | 42 | 0.08404 | 0.07930 | -0.00475 |
| `php` | 3 | 1.16863 | 0.97948 | -0.18916 |
| `php_exit_all` | 6 | 0.35516 | 0.33360 | -0.02157 |
| `php_exit_single` | 12 | 0.15114 | 0.14416 | -0.00698 |
| `subset_cardinality` | 12 | 0.52186 | 0.44832 | -0.07354 |
| `tseitin_complete` | 9 | 0.89112 | 0.81850 | -0.07262 |

Overall valid rows:

| model | rows | mean adapter gain | max adapter gain |
| --- | ---: | ---: | ---: |
| NegGate | 120 | 0.2977109 | 1.30409 |
| NegGate + PermCons | 120 | 0.2699442 | 1.18962 |

## Negative Cases

产物：

- `docs/symmetry_adapter_neggate_permcons_negative_case_audit.md`
- `runs/analysis/symmetry_adapter_neggate_permcons_negative_case_summary.csv`

| negative case | rows | mean adapted mu range | max adapted mu range | violations |
| --- | ---: | ---: | ---: | ---: |
| `no_activity_event_nonzero` | 36 | 1.48e-08 | 3.725e-08 | 0 |
| `no_activity_zero_event` | 3 | 3.353e-08 | 4.843e-08 | 0 |

PermCons 没有破坏 no-activity graph gate / negative loss。`vertex_cover_torus` 仍然只有 no-activity rows，不能作为 event-positive family。

## 判断

PermCons v1 达到了本轮目标：

- 它从训练侧约束了 adapter 的变量级 permutation consistency，而不只是事后 audit。
- 它保留了 event-conditioned identity separation。
- 它没有重新引入 no-activity false separation。

当前不足也很清楚：

- alignment improvement 是中等幅度，不是完整 equivariance。
- event separation 有轻微回落，后续如果调高 `permutation_consistency_weight`，应同步监控 separation loss。
- `vertex_cover_torus` 仍缺 valid event rows，应作为下一条实例/budget 任务单独处理。
- 仍不能 claim solver speedup。
