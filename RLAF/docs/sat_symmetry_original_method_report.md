# SAT 对称性主线调研与原创方法报告

日期：2026-06-08
最近更新：2026-06-20

## 1. 结论摘要

当前项目最有价值的主线仍不应直接复刻传统 symmetry-breaking，也不应马上改造成完整动态对称 SAT solver。更可行且更原创的方向是：

```text
Orbit-certified Event Symmetry Breaking

先用静态 orbit audit 证明 GNN 在强对称变量上 collapse，
再用短 CDCL event trace 证明 solver 搜索能在这些 orbit 内产生 identity，
最后训练 event-conditioned adapter，把这种 identity 转成变量引导差异。
```

截至 2026-06-20，主结论必须收紧：

- refined orbit / event trace / adapter representation 这条机制链有 partial evidence，但还不是 solver speedup evidence。
- v2 patched `pre=true` runtime attribution 显示所有 method rows 都 solved，退化主因是 event collection overhead，而不是 adapter inference 本身；主表只能写 viability / attribution，不写 speedup claim。
- 早先关注的 named targets 已从 runtime-positive candidates 降级为 diagnostic targets：`dominating_set_hex_3x6_s4`、`subset_cardinality_bw12`、`random_3sat_control_v20_c85_seed1901` 都不再作为 speedup 正例使用。
- corrected low-warmup sweep 已修复 weighted Glucose `-conf-lim` 实际不生效的问题；warmup CPU 降到约 0.006-0.008s。`complete_coloring` 在低 warmup 下保留 adapter-vs-cached final CPU 下降，`php` 是 mixed，`random_3sat_control` 仍显示 generic perturbation 风险。
- pre-final gate audit v1 只能作为离线回放：feature-only gate 可用 `num_vars <= 120` 排除 random controls，但不能区分 `complete_coloring` 与 `php` 的 ordering cases；这不是可部署 selector 证据。
- formula equivalence audit v1 显示 harder-baseline 中 `complete_coloring/k9_color8` 与 `php_p9_h8`、`k10_color9` 与 `php_p10_h9` 是相同 unordered CNF formula，只是 DIMACS clause order 不同。因此这批 complete_coloring/php 差异不能解释成 family-specific symmetry speedup，只能当 ordering/permutation sensitivity diagnostic。
- canonical DIMACS order audit 已完成：12 个 formula-equivalent CNF × 5 methods × 3 repeats × 5 warmup budgets 全部 solved 且 correctness 通过。canonicalization 后 family-level plain final CPU order delta 最大约 0.216s，adapter final CPU order delta 最大约 0.305s，adapter-vs-cached delta shift 最大约 0.299s；这确认 CDCL/order sensitivity 是当前 complete_coloring/php 差异的重要混杂因素。
- canonical-order runtime protocol v1.2 已完成：45 个 canonical CNF，覆盖 `complete_coloring`、`php`、`random_3sat_control`、`subset_cardinality`，在 warmup conflicts 1/3/5 下共 2025 个 method rows 全部 solved；known expected rows 全部 match，`random_3sat_control` 继续作为 UNKNOWN runtime/control evidence，不进入 correctness denominator。canonical 后 `complete_coloring/k9_color8` 与 `php_p9_h8`、`k10_color9` 与 `php_p10_h9` 的 adapter-vs-cached decisions/conflicts delta 基本对齐，说明先前 complete/php family split 主要不是 symmetry-family-specific signal。
- v1.2 的 adapter signal 仍不够稳定：overall adapter-vs-cached final CPU delta mean 在 wc1/wc3/wc5 分别为 +0.0699s/+0.0806s/+0.0385s，整体不是 final-search gain；`k9_color8`/`php_p9_h8` 在 low warmup 下有 search reduction，但 `k10_color9`/`php_p10_h9` 反向变差；`random_3sat_control` 仍出现 adapter-vs-plain protocol wins，继续支持 generic perturbation 风险。因此下一步应做 objective/order-robustness fix，而不是 gate/selector。
- 当前严格正例仍不能成立为 solver speedup；`random_3sat_control` 的收益不能算 symmetry benefit。
- `subset_cardinality_bw12::perm_seed1730` 是当前最重要的失败样本：valid event orbit 上 signal 很强，adapter separation 也很强，但 final decisions/conflicts 反向变差。这说明下一步重点是 adapter objective / permutation robustness，而不是扩 benchmark 或训练 gate。

这条路线和已有 SAT symmetry 工作的区别是：

- 静态 SBP / BreakID / Satsuma 主要在求解前添加对称破缺子句。
- CDCLSym / SAT modulo symmetries 主要在 solver 内部维护或利用对称群。
- 本项目不先追求完整符号对称推理，而是把“搜索事件本身能否打破 GNN 的对称盲区”作为核心科学问题。

当前仓库已经具备足够基础：

- `src/data/symmetry.py`：SAT-b 风格对称 CNF generator 和手工 orbit 标签。
- `build_symmetry_stress_dataset.py`：构造 60 个 base/permutation stress instances，包含 20 个 base instances，并用 `event_audit_role` 区分 event / static-only。
- `audit_static_symmetry.py`：测静态 GNN orbit collapse 和 permutation stability。
- `audit_event_symmetry.py`：测短 rollout event identity，并输出 valid / event-positive / zero-identity / missing-event 分层。
- `train_trace_distill.py` + `src/training/trace_distill.py`：用 solver event trace 训练 representation-only event adapter。
- `src/solving/solver.py` 和 weighted Glucose：已支持 `-collect-events` 与 `c event var_*` 解析。

最新 refined 正式结果说明：

- `docs/symmetry_refined_static_audit.md` 证明静态 GNN 在 refined orbit 上仍保持 collapse；`php`、`complete_coloring`、`tseitin_complete`、`subset_cardinality`、`php_exit_single`、`even_colouring`、`dominating_set_hex` 等族上，valid refined orbit 的静态 `mu_range` 仍接近 `1e-8` 到 `1e-7`。
- `docs/symmetry_refined_event_v3_audit.md` 基于 60 行 manifest / 57 个 event-role instances；所有有 valid rollout rows 的 family 都有 event-positive rows。
- `dominating_set_hex` 已补正式小 hex ladder：`3x5` 和 `3x6` emit events 且在 refined orbit 上产生 22 个 event-positive rows；`4x5` 是正式 no-solver-activity negative；`4x7` 保留为 static-only stress。
- `php_exit_single_p5_h4` 保留为 zero-identity negative case；新增 `php_exit_single_p6_h5` 后，3 个 permutation variants 都产生 1 个 event-positive valid row，max event L2 为 0.2988。
- `even_colouring` 是弱证据：42 个 valid rows 中 3 个 event-positive，positive event L2 为 0.298。
- `vertex_cover_torus` 已补正式 event ladder：`3x4_k4`、`3x4_k5`、`3x5_k5`、`3x5_k6` 在 5 秒 / 20-conflict rollout 下产生 12 个 valid/event-positive rows，mean event L2 为 3.542，max event L2 为 5.070；`4x5_norat` 保留为 3 个 no-solver-activity negative rows。
- 已完成第一版 representation-only event adapter：`runs/GNN_Glucose_3SAT_SymmetryTraceAdapter/best.pt`。`docs/symmetry_adapter_event_audit.md` 显示，在 valid refined orbit 上，static `mu_range` 仍约 `1e-8`，adapter 后 `mean_adapted_mu_range_valid` 明显非零：`subset_cardinality` 0.4184、`dominating_set_hex` 0.1722、`php_exit_single` 0.1359、`even_colouring` 0.06924。
- 已完成 adapter permutation consistency audit：`docs/symmetry_adapter_permutation_consistency_audit.md` / `runs/analysis/symmetry_adapter_permutation_consistency.csv`。40 个 event-valid renamed orbit groups 上，static variant std 仍接近数值噪声；event trace 和 adapter 输出在 renamed variants 间有非零差异，说明当前证据是 orbit-level consistency audit，不是逐变量 permutation equivariance proof。
- 已完成 variable-level permutation alignment audit：`docs/symmetry_adapter_permutation_alignment_audit.md` / `runs/analysis/symmetry_adapter_permutation_alignment_pairs.csv`。直接比较 `P^{-1} y(P(CNF))` 和 `y(CNF)` 后，static `mu` MAE 仍约 `1e-8`；adapter `mu` MAE 随 event-state alignment error 增大，最明显的是 `tseitin_complete`、`subset_cardinality`、`complete_coloring`、`php`。这说明变量级不一致主要来自 renamed rollout 的 event trace 自身，而不是静态 GNN 编号伪影。
- 已完成 zero/no-activity negative audit：`docs/symmetry_adapter_negative_case_audit.md`。真正 `event L2 = 0` 的 `vertex_cover_torus` rows 没有 adapter violation；但 `no_activity_event_nonzero` rows 有 36/36 violations，主要是 `php_p4_h3` / `k4_color3` 的 enhanced propagation/assignment 特征让 adapter 产生约 0.192 的 `adapted_mu_range`，`dominating_set_hex_4x5` 也有较小但非零的 0.0074 mean range。
- 已完成 no-activity negative loss + graph gate，并重新训练 `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate/best.pt`。当 graph-level `decisions == 0 and conflicts == 0` 时，训练损失把 adapter 输出拉回 `base_y`，推理端用 `event_state` 的 `[decision, conflict_lits]` 列关闭 adapter delta，避免 enhanced propagation/assignment-only features 单独触发大幅分离。
- NegGate 三类审计已重跑：`docs/symmetry_adapter_neggate_event_audit.md`、`docs/symmetry_adapter_neggate_permutation_alignment_audit.md`、`docs/symmetry_adapter_neggate_negative_case_audit.md`。negative violations 从旧 adapter 的 `no_activity_event_nonzero` 36/36 降到 0/36；positive valid adapter gain 保留并增强，例如 `subset_cardinality` 0.5219、`dominating_set_hex` 0.2188、`php_exit_single` 0.1511、`even_colouring` 0.08404。变量级 adapter alignment MAE 随正向分离变强略升，但 static MAE 仍保持 `1e-8` 量级，且误差仍主要跟随 event-state alignment error。
- 已完成旧 trace 上的 family-heldout adapter audit：`docs/symmetry_adapter_family_heldout_audit.md`。leave-one-family-out adapter-only 训练后，`subset_cardinality` heldout gain 为 0.4297、`dominating_set_hex` 为 0.1327、`php_exit_single` 为 0.1077、`even_colouring` 为 0.03863；当时 `vertex_cover_torus` 有 heldout eval rows 但 0 valid rollout rows，因此只作为 no-activity negative。
- 已完成旧 trace 上的 NegGate family-heldout 3-seed audit：`docs/symmetry_adapter_neggate_family_heldout_multiseed_audit.md`。9 个 heldout family x 3 seeds 共 27 个 adapter-only checkpoint / cached audit；8 个有 valid heldout rows 的 family 都是 3/3 positive-gain seeds。heldout gain mean：`complete_coloring` 0.9881、`php` 1.024、`subset_cardinality` 0.5550、`tseitin_complete` 0.7308、`php_exit_all` 0.2725、`dominating_set_hex` 0.1551、`php_exit_single` 0.1173、`even_colouring` 0.05783。`vertex_cover_torus` 的 heldout 多 seed 需要基于新 60-row trace 重跑。
- 已完成 adapter 侧 permutation consistency loss，并重新训练 `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt`。`docs/symmetry_adapter_neggate_permcons_comparison.md` 显示，逐变量 `P^{-1} y(P(CNF))` alignment 的 overall `adapted_mu_mae` 从 NegGate 的 0.18397 降到 0.16986，约 7.67% 改善；valid adapter identity gain 从 0.29771 降到 0.26994，说明 consistency loss 有效但带来轻微 separation tradeoff；negative audit 仍是 0 violation。
- 已完成 `vertex_cover_torus` valid event rows 补齐、trace 重建和 adapter 复核：`docs/symmetry_vertex_cover_torus_valid_event_rows.md` 显示，新 trace 上旧 PermCons checkpoint 有 132 个 valid rows，其中 torus 12 个；torus mean adapter gain 为 0.974。用新 trace 重训 `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC/best.pt` 后，overall valid adapter gain 从 0.334 提到 0.430，torus gain 从 0.974 提到 1.432，但变量级 alignment MAE 从 0.204 升到 0.263，torus alignment MAE 从 0.265 升到 0.374。也就是说 VC rows 已补成，但新 trace 上 0.25 PermCons weight 的 separation/alignment tradeoff 变差，需要后续调权重。
- 已完成 `permutation_consistency_weight` sweep：`docs/symmetry_adapter_permcons_weight_sweep.md` 显示，`weight=0.5` 是当前折中 checkpoint，overall gain 0.3500、torus gain 1.1510、overall alignment MAE 0.2139、torus alignment MAE 0.3040、negative violations 0；`weight=1.0` alignment 更好但 overall gain 降到 0.2534，低于旧 checkpoint 0.3339。
- 已基于新 60-row trace 重建 family-heldout splits，并补 `vertex_cover_torus` heldout 3-seed：`docs/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_multiseed_audit.md` 显示，训练集排除 torus 后，heldout torus 12 valid rows 上 3/3 positive-gain seeds，heldout gain mean 0.8548，低于 full W05 torus gain 1.1510 但已经是正式 heldout positive case。
- 已完成新 60-row trace 上的 all-family W05 heldout 3-seed audit：`docs/symmetry_adapter_permcons_w05_family_heldout_multiseed_audit.md` 显示，9 个 heldout family 全部有 valid heldout rows，且全部为 3/3 positive-gain seeds。heldout gain mean：`complete_coloring` 0.9719、`vertex_cover_torus` 0.8548、`php` 0.8442、`tseitin_complete` 0.6480、`subset_cardinality` 0.5483、`php_exit_all` 0.3840、`dominating_set_hex` 0.2436、`php_exit_single` 0.1639、`even_colouring` 0.04838。
- all-family W05 heldout negative guardrail 也通过：`runs/analysis/symmetry_adapter_permcons_w05_family_heldout_negative_guardrail_summary.csv` 覆盖 27 个 heldout checkpoint / 1053 行 no-activity rows，`max_adapter_minus_static_mu_range` 为 0，violation rows 为 0。
- 已基于 patched weighted Glucose `pre=true` 主路径重跑 W05 representation protocol：`docs/symmetry_patched_pretrue_w05_event_audit.md` / `runs/analysis/symmetry_patched_pretrue_w05_event_orbits.csv` 覆盖 57 个 event-role CNF、216 个 orbit rows，其中 165 个 valid rollout rows 全部 event-positive，0 zero-identity rows，0 missing-event rows。原先受 preprocessing 卡住的 `dominating_set_hex_4x5_s5` 和 `vertex_cover_torus_4x5_norat` 现在都有 valid/event-positive rows。这仍是 representation-level event identity evidence。
- patched `pre=true` cached adapter audit 已重跑：`docs/symmetry_patched_pretrue_w05_cached_adapter_audit.md` 显示 165 个 valid/event-positive orbit rows 上 mean adapter gain 为 0.3479；`vertex_cover_torus` mean gain 为 1.204，`subset_cardinality` 为 0.6963，`dominating_set_hex` 为 0.1870，`even_colouring` 为 0.07291。
- patched `pre=true` negative guardrail 已重跑：`docs/symmetry_patched_pretrue_w05_negative_case_audit.md` 只剩 6 行 `no_activity_event_nonzero`，都来自 `complete_coloring` / `php` 的 0 decision / 0 conflict rows，adapter violation 为 0。
- patched `pre=true` 逐变量 permutation alignment 已重跑：`docs/symmetry_patched_pretrue_w05_permutation_alignment_audit.md` 覆盖 38 个 base/permuted pairs；static `mu` MAE 仍是 1.5e-08 数值噪声，event-state L2 mean 为 2.180，adapter `mu` MAE 为 0.2573。该值高于旧 trace 的 0.2139，主要因为 patched trace 让 torus/hex 的真实 event-state 差异进入审计；这是 representation tradeoff，不是 runtime 结论。
- patched `pre=true` repeated runtime protocol 已重跑，并把 `solver_path_role` 明确标成 `patched_pretrue_main`：`docs/symmetry_solver_protocol_preflight.md` / `runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv` 显示 855/855 method rows solved，0 `INDETERMINATE`，guided-loss diagnostics 为空，171/171 attribution rows 为 `event_collection_overhead_only`。v2 full protocol 同样显示 runtime 退化由 warmup/event collection accounting 主导：event collection mean protocol delta 约 0.7786s，adapter inference/additional delta 约 0.0011s，adapter final CPU effect 接近 0。主结论是 overhead dominates，不是 speedup。
- `--weighted-no-pre` repeated protocol 也已重跑，但只作为诊断路径，并把 `solver_path_role` 标成 `weighted_no_pre_diagnostic`：`docs/symmetry_solver_protocol_preflight_weighted_no_pre.md` / `runs/analysis/symmetry_solver_protocol_preflight_weighted_no_pre_per_instance.csv` 同样 855/855 solved。该路径用于隔离 preprocessing 影响，不能与 patched `pre=true` 主协议合并，也不能作为 solver speedup 证据。
- runtime-positive mining / targeted audit 已刷新：`docs/symmetry_runtime_positive_subset_v2.md` 和 `docs/symmetry_targeted_mechanism_audit_v2.md` 显示，早先 named candidates 已回落为 diagnostic targets。`dominating_set_hex_3x6_s4` 是 conflicts-driven partial mechanism；`subset_cardinality_bw12` 是 variant-mixed partial mechanism；random control 只能说明 adapter 能扰动 search。
- canonical-order runtime protocol v1.2 已落地：`docs/echosat_runtime_v12_canonical_manifest.md` 记录 canonical manifest，`docs/echosat_runtime_v12_canonical_low_warmup.md` 记录 wc1/wc3/wc5 正式 runtime。该协议只规范化 DIMACS literal/clause order，不改变量编号、orbit 或 expected label；主路径仍锁定 `patched_pretrue_main`，`weighted_no_pre` 不进入主表。
- Symmetry GRPO v1 已实现但尚未训练：`build_echosat_symmetry_grpo_v1_canonical_split.py` 生成 canonical/order-paired 1399-CNF training split，`build_echosat_symmetry_grpo_v1_reward_table.py` 基于 v1.2 canonical low-warmup 结果生成离线 reward ledger，`configs/config_train_rlaf_echosat_symmetry_grpo_v1_full.yaml` 将 online GRPO 目标切到 `echosat_target_mode=symmetry_grpo_v1`。该目标以 cached/static final solve 为主 baseline，奖励 adapter-vs-cached decisions/conflicts reduction，CPU 只 clipped；`random_3sat_control` 无法获得 symmetry-positive reward，formula-equivalent / permutation direction mismatch、weighted-path risk、near-cap risk 和 large perturbation 都作为 penalty。离线 dry-run 显示 random controls 0 positive rows，`k9_color8/php_p9_h8` 的 search-reduction rows 获得正向 reward，`k10_color9/php_p10_h9`、`subset_cardinality_bw12` 和 random controls 为负向 reward。
- Objective Fix v1 已冻结并开始落地：`docs/symmetry_adapter_objective_fix_v1.md`、`docs/symmetry_adapter_objective_fix_v1_proxy.md` 把 primary target 改成 final decisions/conflicts delta，并加入 permutation inconsistency、invalid-orbit identity、non-symmetric perturbation、adapter magnitude 等 penalty。`src/training/trace_distill.py` 已加入默认关闭的 valid-orbit / negative-guard / delta-magnitude / permutation-delta consistency loss。v1.2 canonical runtime 之后，下一步训练应使用 Symmetry GRPO v1 的 low-warmup、canonical/order-consistent、control-penalized adapter-cached search-work reward；仍不做 selector 训练。
- 仍然不能 claim solver speedup；当前 adapter 和 heldout 结果都只是 representation-level separation 与 partial mechanism evidence。

当前已经完成 refined orbit audit、event audit v3、adapter representation audit v1、adapter permutation consistency audit、variable-level permutation alignment audit、zero/no-activity negative audit、no-activity negative loss/gate、NegGate adapter 重训与三类审计重跑、family-heldout adapter audit、NegGate heldout 多 seed / bootstrap、adapter 侧 permutation consistency loss v1、`vertex_cover_torus` valid event rows 补齐、PermCons 权重 sweep、torus heldout 3-seed、60-row all-family W05 heldout 3-seed、patched `pre=true` 主路径下的 representation/runtime protocol 复跑、canonical-order runtime protocol v1.2，以及 Symmetry GRPO v1 reward/config 实现。仍不是直接 claim speedup。

```text
Objective Fix v1
-> corrected low-warmup / pre-final gate / formula-equivalence audit
-> canonicalized DIMACS / order-sensitivity audit
-> canonical-order runtime protocol v1.2
-> Symmetry GRPO v1 objective/order-robustness training
-> only after that solver speedup discussion
```

## 2. 文献路线图

### 2.1 静态 symmetry breaking

代表工作包括 Shatter、BreakID 和近年的 Satsuma。

这类方法的共同模式是：

1. 把 CNF 转换为 colored graph。
2. 用图自同构工具找变量/文字置换群。
3. 添加 symmetry-breaking predicates，例如 lex-leader 或更紧凑的二元 SBP。
4. 再交给 CDCL solver。

可借鉴点：

- orbit 必须结构化。不能把“看起来同类”的变量粗暴放进同一个 orbit。
- 对称破缺必须控制大小。完整展开所有 symmetry image 会造成公式膨胀。
- 很多实际 benchmark 的对称性来自行交换、列交换、Johnson-like 结构和 product action。

对本项目的启发：

- `audit_static_symmetry.py` 里的 hand-labelled orbit 需要更严格；特别是 `even_colouring`、`subset_cardinality`、`php_exit_single` 当前标签偏粗。
- 可以借鉴 BreakID/Satsuma 的结构意识，先实现 lightweight orbit refinement，而不是直接接入 heavyweight automorphism solver。

不直接照搬的原因：

- 静态 SBP 不能回答“CDCL event trace 是否能在对称变量中产生身份信号”。
- 静态 SBP 会改变公式和 solver 行为，容易把项目主问题变成传统 preprocessing 比较。

### 2.2 动态 symmetry handling

代表路线包括 CDCLSym、symmetric explanation learning、symmetry propagation、SAT modulo symmetries。

这类方法关注：

- 在 CDCL 搜索中动态利用对称性。
- 把 learned clause 的 symmetry image 加入子句库。
- 对 assignment 或 partial solution 做 canonical reasoning。
- 用证明系统保证新加推理合法。

可借鉴点：

- 对称性不是纯静态对象。搜索轨迹、赋值、冲突子句会持续改变“当前有效”的对称结构。
- learned clause 的 symmetry image 可能非常有用，但盲目加入会导致 clause DB 膨胀。
- dynamic symmetry 应该是 gain-aware / budgeted 的。

对本项目的启发：

- `example.md` 中 S3 的 GASCI 思想可以保留为后期 solver-level 实验。
- 当前阶段可先离线测一个简化指标：learned/event-active variables 是否集中在某些 orbit representative 上。
- 不应立刻把 weighted Glucose 改成 full dynamic symmetry solver。那会把任务变成 solver kernel 工程，风险过高。

### 2.3 SAT-b / combinatorial PB benchmark

用户给出的 SAT-b paper 对本项目很有价值。它不是专门的 symmetry-breaking paper，但其中的 benchmark family 非常适合构造 symmetry stress set：

- pigeonhole principle
- pigeonhole with emergency exits
- subset cardinality
- even colouring
- vertex cover
- dominating set
- graph colouring
- Tseitin/parity
- linearized pebbling

可借鉴点：

- 这些 family 本身有清晰 combinatorial symmetry，可以人工给出 orbit。
- 许多问题对变量顺序、encoding 和 solver branching 极其敏感。
- 这正适合测试“event trace 是否提供了静态 CNF 图之外的变量身份信息”。

对本项目的启发：

- 继续使用 SAT-b 风格家族是正确的。
- 需要从单点实例扩展成 ladder：每个 family 有 small/medium/hard 三档，而不是只靠一个尺度。
- `dominating_set_hex_4x7_s7` 当前 310 万 clauses 过大，不适合作为第一批 event audit；应做更小 hex ladder。

### 2.4 神经 SAT 与 GNN 对称盲区

NeuroSAT 等工作说明 message-passing GNN 可以学习 SAT 相关表示，但 GNN 天然 permutation-equivariant。对完全对称变量，如果没有额外输入，模型输出 collapse 是预期行为。

AsymSAT 这类工作进一步强调：普通 GNN 在对称 SAT 上无法区分对称变量，因此需要 asymmetric 或 search-conditioned 信息。

这正是本项目的突破口：

```text
静态 GNN collapse 是结构限制；
CDCL event trace 是 search-conditioned asymmetric information；
event adapter 是把 asymmetric information 注入 GNN 输出的机制。
```

## 3. example.md 的取舍

`example.md` 提出两条路线：S3 和 SymGNN。结合当前项目，应做如下取舍。

### 3.1 S3 可借鉴但不适合作为第一步

值得保留：

- 增量 WL / color refinement。
- GASCI：gain-aware symmetric clause instantiation。
- orbit entropy restart。
- proof-aware symmetry。

暂不直接做：

- 每条 learned clause 后更新对称群。
- 在 CDCL 内核中注入 symmetry image clause。
- sr proof 系统。

原因：

- 这需要深改 solver kernel。
- 当前还没证明 event adapter 能稳定利用 identity。
- 直接做 speedup 会把变量太多的系统工程问题混入科学问题。

### 3.2 SymGNN 的 audit 思想适合当前阶段

可以马上转化为本项目指标：

- `static orbit range`
- `permutation stability`
- `orbit entropy`
- `event identity gain`
- `adapter identity gain`
- `permutation-consistent adapter output`
- orbit 内 contrastive separation loss

需要修正的一点：

`example.md` 中 SymGNN 倾向“学习对称性并吸收对称性”。但本项目的问题更精确：

```text
不是让模型把对称变量继续压到一起，
而是在静态对称变量中，利用 solver event 产生搜索身份。
```

所以训练目标不应只是 symmetry regularization，还要有 event-conditioned separation。

## 4. 原创方法：Orbit-Certified Event Symmetry Breaking

### 4.1 方法定位

提出一个三阶段方法：

```text
OC-ESB: Orbit-Certified Event Symmetry Breaking

Stage A: Certify static orbit collapse
Stage B: Extract event identity from short CDCL rollouts
Stage C: Train adapter to convert event identity into symmetry-breaking guidance
```

该方法的原创点是：

- 不把 symmetry breaking 视为预处理子句添加。
- 不要求 solver 内核维护完整对称群。
- 把 CDCL 搜索产生的变量级事件作为 symmetry-breaking signal。
- 用 orbit audit 作为训练和验证闭环，保证不是偶然 speedup。

### 4.2 核心对象

设 CNF 变量集合为 `V`，静态 orbit partition 为：

```text
O = {O_1, ..., O_k}
```

静态 GNN 输出：

```text
y_static(v) = (rho_v, mu_v)
```

短 CDCL rollout 事件编码：

```text
e(v) = [
  decisions,
  propagations,
  conflict_lits,
  learnt_lits,
  low_lbd_learnt_lits,
  useful_decisions,
  polarity features,
  activity
]
```

event adapter 输出：

```text
y_event(v) = Adapter(GNN(CNF), e(v))
```

核心指标：

```text
static_range(O_i) = range_{v in O_i} y_static(v)
event_identity(O_i) = range_{v in O_i} ||e(v)||
adapter_gain(O_i) = range_{v in O_i} y_event(v) - range_{v in O_i} y_static(v)
```

### 4.3 阶段 A：Orbit 证据清洗

目标：

```text
确保 orbit 标签真的表示静态同构变量。
```

v2 已修正的 family：

| family | 原问题 | v2 处理 |
| --- | --- | --- |
| `even_colouring` | split edge 打破 torus 全局对称，但仍把大部分 edge 标成同一 orbit | 按 split-edge stabilizer 下的 refined edge orbits 标注 |
| `subset_cardinality` | fixed bandwidth plus corner 使 row/col role 不同 | 用 CNF incidence WL/local signature 细分 |
| `php_exit_single` | single exit 只属于 pigeon 0，但 assignment orbit 仍过粗 | 区分 `exit_pigeon_assignment`、`regular_pigeon_assignment`、`emergency_exit` |
| `dominating_set_hex` | 边界顶点和内部顶点不同，但全标为 `hex_grid_vertex` | 用 hex grid automorphism refined orbits，并保留 4x7 static-only stress |

实现取舍：

- refinement 直接落在 `src/data/symmetry.py` 的 family generator / orbit metadata 中。
- 对通用结构使用 CNF incidence / WL-style signature；对 hex 使用组合自同构 orbit。
- 不接入外部 automorphism 工具，保持可控。

一个可行 signature：

```text
sig(v) = (
  original_orbit_label,
  variable_occurrence_count,
  positive_occurrence_count,
  negative_occurrence_count,
  sorted(clause_lengths_incident_to_v),
  degree-2 WL color after 2 rounds
)
```

这不是完整 automorphism，但足够避免明显粗标签；v2 static audit 已经验证 refined valid orbits 上静态 collapse 干净。

验收标准：

```text
在 refined orbit 上，Balanced static_mu_range 的 family mean 应接近 1e-8 到 1e-4。
如果 static_range 已很大，该 orbit 不进入 event identity 主表。
```

### 4.4 阶段 B：Event Identity Benchmark

目标：

```text
证明短 CDCL rollout 能在静态 collapse orbit 内产生变量身份。
```

v3 正式 event identity 分层：

| family | valid rows | event-positive rows | zero-identity rows | mean L2 valid | 评价 |
| --- | ---: | ---: | ---: | ---: | --- |
| `complete_coloring` | 3 | 3 | 0 | 9.555 | 强，但另有 no-activity 小实例 |
| `dominating_set_hex` | 33 | 33 | 0 | 1.132 | 小 hex ladder 已可运行且有正信号 |
| `even_colouring` | 42 | 42 | 0 | 0.1625 | 弱但稳定正信号 |
| `php` | 3 | 3 | 0 | 9.493 | 强，但另有 no-activity 小实例 |
| `php_exit_all` | 6 | 6 | 0 | 0.5945 | 有信号 |
| `php_exit_single` | 12 | 12 | 0 | 0.4408 | `p6_h5` 后不再是纯 negative family |
| `subset_cardinality` | 12 | 12 | 0 | 0.9573 | 强证据 |
| `tseitin_complete` | 9 | 9 | 0 | 0.6254 | 中等 |
| `vertex_cover_torus` | 12 | 12 | 0 | 3.542 | 新增小 torus ladder，正式 event-positive |

v3 后仍需保留的负例 / 风险项：

| family | 当前状态 | 处理方式 |
| --- | --- | --- |
| `vertex_cover_torus_4x5_norat` | 3 个 variants 仍为 0 decisions / 0 conflicts | 保留为 no-activity negative；正信号由 `3x4_k4`、`3x4_k5`、`3x5_k5`、`3x5_k6` 承担 |
| `dominating_set_hex_4x5_s5` | event rollout 正常返回但 0 decisions / 0 conflicts | 作为正式 no-activity negative case；`3x5`/`3x6` 已承担 event-positive ladder |
| `dominating_set_hex_4x7_s7` | 310 万 clauses，static 可以跑，event 不作为主表输入 | 保留 `static_only` stress，不把 solver crash / no-event 混入 event identity 结论 |
| `php_exit_single_p5_h4` | SAT 太快，仅 1 decision | 保留弱事件 case；`p6_h5` 已给出更强正信号 |

新增有效性门槛：

```text
valid_event_row =
  solver emitted event columns
  and (decisions > 0 or conflicts > 0)
  and static_mu_range <= static_collapse_threshold
  and orbit_size >= min_orbit_size
```

主表同时报告 valid rollout rows、event-positive rows、zero-identity rows、missing-event rows。无事件不能记作 event identity failure，只能记作 invalid rollout；event L2 为 0 的 valid rows 单独记为 zero-identity negative。

### 4.5 阶段 C：Event Adapter Representation Training

目标：

```text
让模型学会把 event identity 转成输出差异，但仍保持变量重命名稳定性。
```

不建议一开始用 solver runtime 做 RL。先做 representation-first 训练：

```text
L = L_base + lambda_sep L_orbit_sep + lambda_perm L_perm + lambda_budget L_sparsity
```

#### 4.5.1 Orbit separation loss

对静态 collapse 且 event identity 明显的 orbit，鼓励 adapter 输出差异与 event 差异同向：

```text
L_orbit_sep =
  - mean_{u,v in O} margin_rank(
      ||e(u) - e(v)||,
      ||y_event(u) - y_event(v)||
    )
```

更简单的 first version：

```text
target_score(v) = normalized(||e(v)|| or event_learnt_lits(v))
L = MSE(rank(y_event_mu(v)), rank(target_score(v)))
```

这比直接拟合 runtime 更稳。

#### 4.5.2 Permutation consistency loss

对同一个 CNF 的 variable-renamed variants：

```text
L_perm = || P^{-1} y_event(P(CNF)) - y_event(CNF) ||
```

目的：

- adapter 可以利用 event identity。
- 但不能对变量编号产生伪依赖。

#### 4.5.3 Sparsity / budget loss

避免 adapter 把所有变量都乱改：

```text
L_sparsity = mean_v || y_event(v) - y_static(v) ||
```

或者只允许 top-k event-active variables 改动。

#### 4.5.4 No-activity negative loss / gate

enhanced event features 中 propagation / assignment-only 信号可能在 solver 没有实际搜索活动时非零。对 `decisions == 0 and conflicts == 0` 的 graph，这类特征不能单独触发 adapter 大幅分离。

当前实现用两个约束同时处理：

```text
no_activity_graph =
  max_v event_state[v, decision_col] <= eps
  and max_v event_state[v, conflict_lit_col] <= eps

L_no_activity =
  mean_{v in no_activity_graph} || y_event(v) - y_static(v) ||_mu^2
```

训练端在 `src/training/trace_distill.py` 中加入 `no_activity_negative_loss`，默认只约束 `mu`；推理端在 `src/model/model.py` 的 graph gate 中用 `event_adapter.graph_gate_indices: [0, 2]` 和 `graph_gate_threshold: 1e-9` 关闭 no-activity graph 的 adapter residual。

验收指标：

| 指标 | 通过条件 |
| --- | --- |
| `adapter_identity_gain` | 在 `php`, `complete_coloring`, `subset_cardinality` 等强 family 上显著 > 0 |
| permutation consistency | renamed variants 对齐后输出差异小 |
| static collapse preservation | 无 event 或 invalid event 时 adapter 不应产生虚假差异 |
| family generalization | train family 之外至少一个 family 有正 adapter gain |

## 5. 方法二：Event-Guided Soft SBP，不改 solver kernel 的折中方案

OC-ESB 成功后，可以做一个轻量 solver-level 方法，不需要完整 S3。

### 5.1 思想

传统 SBP 是求解前静态添加：

```text
x_1 >= x_2 >= ... >= x_k
```

这里改成 event-guided soft SBP：

```text
在短 rollout 后，对每个 orbit 选 event representative，
只生成少量低成本 soft ordering clauses 或 variable weights。
```

两种实现难度：

1. 低风险：不加 clauses，只改 variable weights。
2. 中风险：只加 bounded pairwise SBP clauses。

### 5.2 Representative selection

对 orbit `O`，选择：

```text
rep(O) = argmax_v score_event(v)
```

score 可用：

```text
score_event(v) =
  a * learnt_lits(v)
  + b * conflict_lits(v)
  + c * useful_decisions(v)
  + d * activity(v)
```

这继承 dynamic symmetry 的“当前搜索状态有用性”，但不维护群。

### 5.3 Bounded pairwise SBP

只对每个 orbit 的 top-k variables 添加非常少的 ordering hints：

```text
not x_j or x_rep
```

或 polarity-aware：

```text
if event suggests rep=True:
  not x_j or x_rep
else:
  x_j or not x_rep
```

这不是完整 sound symmetry breaking，必须谨慎。如果作为 solver hint 改权重更安全；如果真加 clauses，必须证明不排除解，或仅用于 UNSAT-preserving symmetry families。

建议 first version 只做 weights：

```text
rho_v, mu_v = adapter output from event state
```

不要先加 clauses。

## 6. 方法三：Streaming WL 只作为 audit，不进入 solver

`example.md` 的 S3 中，增量 WL 是好想法。但当前可行版本应是：

```text
offline learned-clause/event-local WL audit
```

流程：

1. 短 rollout 收集 learnt clause literals 或 conflict literals。
2. 在 CNF incidence graph 上只对 event-active neighborhood 做 1-2 round WL。
3. 比较 WL-refined orbit 和 event-state identity 是否一致。

用途：

- 验证 event trace 不是随机噪声。
- 找出哪些 learned/conflict neighborhood 真正在破静态对称。
- 为后续 solver-level S3 提供证据。

不做：

- 不维护完整 group。
- 不把 WL 结果直接用于 CDCL kernel。

## 7. 实验路线

### 7.1 第一阶段：Clean Orbit Audit

产物：

- `docs/symmetry_orbit_refinement_audit.md`
- `runs/analysis/symmetry_refined_static_orbits.csv`
- `runs/analysis/symmetry_refined_event_orbits.csv`

新增或修改：

- `src/data/symmetry.py`：加入 local signature refinement。
- `audit_static_symmetry.py`：增加 `--refine-orbits`。
- `audit_event_symmetry.py`：增加 valid row 过滤和 invalid rollout 统计。

验收：

```text
refined static collapse table clean；
event identity 主表只含 valid orbit rows；
失败项被明确归类为 invalid rollout / solver failure / non-collapse orbit。
```

### 7.2 第二阶段：Stress Ladder

每个 family 至少 3 个尺度：

| family | small | medium | hard |
| --- | --- | --- | --- |
| PHP | `p4_h3` | `p5_h4` | `p6_h5` |
| colouring | `k4_c3` | `k5_c4` | `k6_c5` |
| Tseitin | `k5` | `k6` | `k7` |
| vertex cover torus | `3x4` | `4x5` | `5x6` |
| dominating hex | `3x5` | `3x6` | `4x5` |
| subset cardinality | `6` | `8` | `10` |

验收：

```text
同一 family 中 event identity 随规模和 rollout budget 呈合理变化；
不是只在一个 toy instance 上成立。
```

### 7.3 第三阶段：Event Adapter

配置起点：

- `configs/config_train_rlaf_event_var.yaml`
- `var_state_dim: 20`
- `event_adapter.enabled: true`

但训练目标要改成 representation-first：

- 不以 solver runtime 作为第一目标。
- 先用 event/orbit loss 训练 adapter。
- 冻结或半冻结 base GNN，避免破坏 Balanced checkpoint。

验收：

```text
adapter_identity_gain > 0
permutation consistency 通过
invalid/no-event row 不乱动
```

### 7.4 第四阶段：Solver Speedup

只有前三阶段通过后才做。

协议：

- 总 wall-clock 包含 warmup rollout、GPU inference、final solve。
- 固定 solver seed。
- 报告 solved count、mean time、median time、timeouts、per-instance win/loss。
- 单独报告 representation success 和 solver runtime success，不混成一个 claim。

## 8. 风险与规避

| 风险 | 表现 | 规避 |
| --- | --- | --- |
| orbit 标签过粗 | static range 本来就大，event gain 被夸大 | local signature refinement；只统计 static collapse orbit |
| event identity 是变量编号伪影 | permutation variants 对不齐 | permutation consistency audit |
| event trace 太短 | 0 decisions / 0 conflicts | valid row 过滤；改 budget/实例尺度 |
| event adapter 过拟合 family | train family 有 gain，heldout family 无 gain | family-heldout split |
| solver speedup 噪声大 | representation 成功但 runtime 不稳定 | speedup 放最后，严格 wall-clock 协议 |
| 动态 symmetry 工程过重 | solver kernel 改动不可控 | S3 先做 offline audit，不进 kernel |

## 9. 具体下一步

已完成：

```text
refined orbit audit v3，不训练、不做 speedup。
event adapter representation audit v1，不做 solver speedup。
adapter permutation consistency audit，不做 solver speedup。
variable-level permutation alignment audit，不做 solver speedup。
zero/no-activity negative audit，不做 solver speedup。
family-heldout adapter audit，不做 solver speedup。
no-activity negative loss/gate，并重训 NegGate adapter。
重跑 adapter event / variable-level permutation / negative 三类审计。
NegGate family-heldout 3-seed / bootstrap audit，不做 solver speedup。
adapter 侧 permutation consistency loss v1，并重训 NegGatePermCons adapter。
重跑 NegGatePermCons event / variable-level permutation / negative 三类审计。
vertex_cover_torus valid event ladder，并重建 trace / 重跑 adapter 三类审计。
用新 60-row trace 重训 NegGatePermConsVC adapter，记录 separation/alignment tradeoff。
调 PermCons weight=0.5/1.0，选择 W05 checkpoint。
重建 heldout splits，补 vertex_cover_torus heldout 3-seed。
补齐 60-row all-family W05 heldout 3-seed / bootstrap audit。
补 all-family W05 heldout no-activity negative guardrail。
```

对应产物：

- `runs/analysis/symmetry_stress_manifest.csv`：60 行正式 stress manifest；20 个 base instances，57 个 event-role instances。
- `docs/symmetry_refined_static_audit.md`：旧 48-row manifest 上的 refined static collapse。
- `docs/symmetry_vertex_cover_torus_static_audit.md`：新增 torus ladder 的 static collapse；15 个 torus orbit rows 全部 valid，mean `mu_range` 为 `2.26e-08`。
- `docs/symmetry_refined_event_v3_audit.md`：event identity v3 分层主表；`vertex_cover_torus` 有 12 个 valid/event-positive rows。
- `runs/analysis/symmetry_refined_event_v3_orbits.csv`：逐 orbit event identity 明细。
- `runs/analysis/symmetry_refined_event_v3_rollout_stats.csv`：逐实例 solver rollout 状态。
- `data/trace_distill/symmetry_event_trace.pt`：57 个 event-role CNF 的 trace distillation graphs；`dominating_set_hex_4x7_s7` static-only 未进入。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter/best.pt`：冻结 backbone 后训练的 representation-only event adapter。
- `docs/symmetry_adapter_event_audit.md`：`static orbit range -> event-state orbit range -> adapter orbit range` 三段 audit。
- `docs/symmetry_adapter_permutation_consistency_audit.md`：按 `family/base_instance_id/orbit` 对 base 和 permuted variants 做 orbit-level adapter consistency audit。
- `runs/analysis/symmetry_adapter_permutation_consistency.csv`：40 个 event-valid renamed orbit groups 的逐组 consistency 明细。
- `docs/symmetry_adapter_permutation_alignment_audit.md`：用 metadata permutation 做逐变量 `P^{-1} y(P(CNF))` 对齐审计。
- `runs/analysis/symmetry_adapter_permutation_alignment_pairs.csv`：30 个 base/permuted variant pair 的 static/event/adapted 对齐误差。
- `runs/analysis/symmetry_adapter_permutation_alignment_variables.csv`：616 行逐变量对齐明细。
- `docs/symmetry_adapter_negative_case_audit.md`：zero-identity / no-solver-activity / missing-events negative guardrail。
- `runs/analysis/symmetry_adapter_negative_cases.csv`：39 行 negative-case adapter 误动明细。
- `data/trace_distill/symmetry_family_heldout/`：leave-one-family-out trace distillation splits。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_Heldout*/best.pt`：每个 heldout family 的 adapter-only checkpoint。
- `docs/symmetry_adapter_family_heldout_audit.md`：family-heldout representation audit 主表。
- `runs/analysis/symmetry_adapter_family_heldout_summary.csv`：heldout valid rows、heldout adapter gain、与 full-adapter gain 的差值。
- `src/training/trace_distill.py`：新增 no-activity negative loss；当 graph-level decision/conflict evidence 为零时，把 adapter 输出拉回 `base_y`。
- `configs/config_train_trace_distill_symmetry.yaml`：启用 `event_adapter.graph_gate_indices: [0, 2]` 和 `trace.label.no_activity_negative_weight: 2.0`。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate/best.pt`：带 no-activity negative loss/gate 的 representation-only event adapter。
- `docs/symmetry_adapter_neggate_event_audit.md`：NegGate adapter event representation audit；valid positive gain 保留并增强。
- `docs/symmetry_adapter_neggate_permutation_alignment_audit.md`：NegGate 逐变量 `P^{-1} y(P(CNF))` 对齐审计。
- `docs/symmetry_adapter_neggate_negative_case_audit.md`：NegGate negative guardrail；`no_activity_event_nonzero` violation 从 36/36 变为 0/36。
- `run_adapter_family_heldout_multiseed.py`：正式 9 family x 3 seeds 的 NegGate heldout adapter 训练和 cached audit runner。
- `summarize_adapter_family_heldout_multiseed.py`：seed-level 与 bootstrap heldout 汇总。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGate_Heldout*_Seed*/best.pt`：27 个 heldout multi-seed adapter-only checkpoints。
- `runs/analysis/symmetry_adapter_neggate_heldout_*_seed*_orbits.csv`：27 个 heldout cached orbit audit 明细。
- `docs/symmetry_adapter_neggate_family_heldout_multiseed_audit.md`：NegGate family-heldout multi-seed 主表；8 个有 valid heldout rows 的 family 都是 3/3 positive-gain seeds。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermCons/best.pt`：带 no-activity graph gate 和 adapter-side permutation consistency loss 的 representation-only event adapter。
- `docs/symmetry_adapter_neggate_permcons_comparison.md`：NegGate vs NegGatePermCons 对比；变量级 alignment MAE 约 7.67% 改善，event separation 略降，negative guardrail 仍 0 violation。
- `docs/symmetry_adapter_neggate_permcons_event_audit.md`：NegGatePermCons adapter event representation audit；120 个 valid rows 上 mean adapter identity gain 为 0.26994。
- `docs/symmetry_adapter_neggate_permcons_permutation_alignment_audit.md`：NegGatePermCons 逐变量 `P^{-1} y(P(CNF))` 对齐审计。
- `docs/symmetry_adapter_neggate_permcons_negative_case_audit.md`：NegGatePermCons negative guardrail；`no_activity_event_nonzero` 和 `no_activity_zero_event` 都是 0 violation。
- `runs/analysis/symmetry_adapter_neggate_permcons_permutation_alignment_pairs.csv`：30 个 base/permuted pair 的 PermCons 对齐误差。
- `docs/symmetry_vertex_cover_torus_valid_event_rows.md`：本轮 focused report；记录 torus ladder、event audit、trace 重建、adapter 复核和 VC 重训 tradeoff。
- `docs/symmetry_adapter_neggate_permcons_vc_event_audit.md`：旧 PermCons checkpoint 在新 trace 上的 adapter event audit；132 个 valid rows，torus 12 个 valid rows。
- `docs/symmetry_adapter_neggate_permcons_vc_permutation_alignment_audit.md`：旧 PermCons checkpoint 在新 trace 上的逐变量 alignment audit；38 个 base/permuted pairs。
- `docs/symmetry_adapter_neggate_permcons_vc_negative_case_audit.md`：旧 PermCons checkpoint 在新 trace 上的 negative guardrail；0 violation。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC/best.pt`：用新 60-row trace 重训的 representation-only event adapter。
- `docs/symmetry_adapter_neggate_permcons_vc_retrained_event_audit.md`：VC 重训 checkpoint 的 adapter event audit；valid mean gain 0.4299，torus mean gain 1.432。
- `docs/symmetry_adapter_neggate_permcons_vc_retrained_permutation_alignment_audit.md`：VC 重训 checkpoint 的逐变量 alignment audit；overall adapted `mu` MAE 0.2625，torus 0.3738。
- `docs/symmetry_adapter_neggate_permcons_vc_retrained_negative_case_audit.md`：VC 重训 checkpoint 的 negative guardrail；0 violation。
- `docs/symmetry_adapter_permcons_weight_sweep.md`：0.5 / 1.0 权重 sweep；选择 `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_NegGatePermConsVC_W05/best.pt` 作为当前折中 checkpoint。
- `runs/analysis/symmetry_adapter_permcons_weight_sweep_summary.csv`：旧 PermCons、新 trace 0.25、0.5、1.0 的 gain / alignment / negative 对照表。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_PermConsW05_HeldoutVertexCoverTorus_Seed*/best.pt`：3 个 torus-heldout W05 adapter-only checkpoints。
- `docs/symmetry_adapter_permcons_w05_heldout_vertex_cover_torus_multiseed_audit.md`：torus heldout 3-seed audit；3/3 positive-gain seeds，heldout gain mean 0.8548。
- `runs/GNN_Glucose_3SAT_SymmetryTraceAdapter_PermConsW05_Heldout*_Seed*/best.pt`：27 个 all-family W05 heldout adapter-only checkpoints；torus 三个 seed 复用前一轮正式 checkpoint，其余 family 本轮补齐。
- `runs/analysis/symmetry_adapter_permcons_w05_heldout_*_seed*_orbits.csv`：27 个 all-family W05 heldout cached orbit audit 明细。
- `docs/symmetry_adapter_permcons_w05_family_heldout_multiseed_audit.md`：all-family W05 heldout multi-seed 主表；9/9 family 都有 valid heldout rows，且全部 3/3 positive-gain seeds。
- `runs/analysis/symmetry_adapter_permcons_w05_family_heldout_multiseed_by_family.csv`：all-family W05 heldout family-level gain / bootstrap 汇总。
- `runs/analysis/symmetry_adapter_permcons_w05_family_heldout_multiseed_seed_summary.csv`：all-family W05 heldout seed-level 汇总。
- `runs/analysis/symmetry_adapter_permcons_w05_family_heldout_negative_guardrail_summary.csv`：27 个 heldout checkpoint 的 no-activity guardrail 汇总；1053 行 no-activity rows，0 violations。
- `data/trace_distill/symmetry_event_trace_patched_pretrue.pt`：patched weighted Glucose `pre=true` 主路径生成的 57 个 event-role CNF trace graphs；不覆盖旧 `symmetry_event_trace.pt`。
- `runs/analysis/symmetry_event_trace_distill_patched_pretrue_stats.csv`：patched `pre=true` trace rollout stats；57/57 rows 为 SAT/UNSAT，0 `INDETERMINATE`，`vertex_cover_torus_4x5_norat` 三个 variants 都有 decisions/conflicts。
- `docs/symmetry_patched_pretrue_w05_event_audit.md`：直接 rollout 的 patched `pre=true` W05 event orbit audit；165 个 valid rows 全部 event-positive。
- `docs/symmetry_patched_pretrue_w05_cached_adapter_audit.md`：patched `pre=true` cached trace 上的 W05 adapter orbit audit；mean adapter gain valid 为 0.3479。
- `docs/symmetry_patched_pretrue_w05_permutation_alignment_audit.md`：patched `pre=true` cached trace 上的逐变量 `P^{-1} y(P(CNF))` alignment audit；overall adapted `mu` MAE 为 0.2573。
- `docs/symmetry_patched_pretrue_w05_negative_case_audit.md`：patched `pre=true` direct orbit CSV 的 negative guardrail；6 行 no-activity event-nonzero rows，0 violations。
- `runs/analysis/symmetry_patched_pretrue_w05_event_orbits.csv`：patched `pre=true` direct event orbit 明细。
- `runs/analysis/symmetry_patched_pretrue_w05_cached_adapter_orbits.csv`：patched `pre=true` cached adapter orbit 明细。
- `runs/analysis/symmetry_patched_pretrue_w05_permutation_alignment_pairs.csv`：patched `pre=true` 38 个 base/permuted pair alignment 明细。
- `runs/analysis/symmetry_patched_pretrue_w05_negative_cases.csv`：patched `pre=true` negative-case 明细。

已完成的 solver-level protocol preflight：

- `run_symmetry_solver_protocol_preflight.py`：独立 protocol runner；默认排除 `static_only` rows，在 57 个 event-role CNF 上跑通 3-repeat paired preflight；输出 `solver_path_role`，区分 `patched_pretrue_main` 和 `weighted_no_pre_diagnostic`。
- `runs/analysis/symmetry_solver_protocol_preflight_per_instance.csv`：855 行 per-instance 账本，覆盖 `plain_unguided_glucose`、`neutral_weighted_glucose`、`static_weighted_glucose`、`cached_trace_no_adapter_final`、`event_adapter_final`。
- `runs/analysis/symmetry_solver_protocol_preflight_phases.csv`：逐 phase 账本，显式记录 `static_inference`、`warmup_rollout_collect_events`、`event_feature_attach`、`adapter_inference`、`final_solve`。
- `runs/analysis/symmetry_solver_protocol_preflight_by_family.csv`：family/method 汇总。
- `runs/analysis/symmetry_solver_protocol_preflight_by_base_instance.csv`：按 `base_instance_id` 和 method 汇总，避免把 permutation variants 当独立样本。
- `runs/analysis/symmetry_solver_protocol_preflight_attribution.csv`：逐 repeat / variant 的 method attribution。
- `runs/analysis/symmetry_solver_protocol_preflight_attribution_by_base.csv`：按 `base_instance_id` 聚合的退化归因表。
- `runs/analysis/symmetry_solver_protocol_preflight_guided_loss_diagnostics.csv`：guided-loss 诊断明细。
- `docs/symmetry_solver_protocol_preflight.md`：patched `pre=true` 主路径 protocol preflight 文档；明确这是协议和开销账本验证，不是 solver speedup claim。
- `audit_weighted_glucose_path.py`：针对 guided-loss base instances 的 weighted Glucose path 诊断脚本。
- `runs/analysis/symmetry_weighted_glucose_path_audit.csv`：90 行 weighted-path 诊断，覆盖 2 个 loss base instances x 3 variants x 3 repeats x 5 probes。
- `runs/analysis/symmetry_weighted_glucose_path_audit_by_base.csv`：按 `base_instance_id` 聚合的 weighted-path probe summary。
- `docs/symmetry_weighted_glucose_path_audit.md`：weighted binary / `c weight` input / polarity convention 的诊断报告。
- `solvers/glucose_weighted/core/Solver.cc`：已移除 weighted `search()` 循环入口处额外的 `withinBudget()` 检查，保留 `solve_()` 外层 budget check。
- `run_symmetry_solver_protocol_preflight.py --weighted-no-pre`：只对 guided/weighted Glucose calls 加 `-no-pre`，plain unguided baseline 保持原样；该路径标记为 `weighted_no_pre_diagnostic`。
- `runs/analysis/symmetry_solver_protocol_preflight_weighted_no_pre_per_instance.csv`：`--weighted-no-pre` 后的 855 行 repeated paired protocol 诊断账本，全部 rows 标记 `weighted_no_pre_diagnostic`。
- `runs/analysis/symmetry_solver_protocol_preflight_weighted_no_pre_attribution_by_base.csv`：`--weighted-no-pre` 后按 `base_instance_id` 聚合的归因表。
- `docs/symmetry_solver_protocol_preflight_weighted_no_pre.md`：`--weighted-no-pre` 对照报告。
- `docs/glucose_weighted_preprocessing_code_audit.md`：`glucose_weighted` vs plain Glucose 的 preprocessing/code diff audit，覆盖 `simp/Main.cc`、`simp/SimpSolver.*`、`core/Dimacs.h`、`core/Solver.*`。

这次 preflight 的关键协议约束已经落地：

1. warmup rollout、event feature attach、adapter inference、final solve 都单独计时并进入 method-level 总账。
2. `neutral_weighted_glucose` 已加入：它使用 weighted Glucose binary 和全变量同相同权重，隔离 weighted binary / weighted input parsing path。
3. `cached_trace_no_adapter_final` 作为 no-adapter cached-trace ablation 保留：它支付 static inference + event warmup + event attach，但 final solve 复用 static guidance，不运行 adapter。
4. 57/57 event-role CNF 的 warmup 都产生了 event state；3 个 `dominating_set_hex_4x7` static-only stress 仍被排除在 event protocol 之外。
5. summary 已经把 `expected_result=UNKNOWN` 从 correctness 统计中分离；`known_expected_match_instances` 只统计 manifest 中有 SAT/UNSAT 标签的 rows。
6. 补丁前 repeated paired preflight 的 18 个 guided-loss rows 全部归因到 `weighted_binary_or_input_path`：两个 base instances，`dominating_set_hex_4x5_s5` 和 `vertex_cover_torus_4x5_norat`，各 3 variants x 3 repeats。
7. 补丁前这 18 行里 `neutral_weighted_glucose` 已经 `INDETERMINATE`，`static_weighted_glucose` 和 `event_adapter_final` 也都是 `INDETERMINATE`；warmup decisions/conflicts 全为 0，adapter graph gate 全关。因此当时退化不是 static GNN weights，也不是 adapter delta，而是 weighted solver/input path 或其 preprocessing 行为。
8. weighted-path 细分诊断进一步收窄了归因：plain Glucose 加 `c weight` comment 仍 18/18 solved；补丁前 `glucose_weighted` 即使不提供 `c weight` 行也 18/18 `INDETERMINATE` 且 decisions/conflicts 全为 0；all `+1.0` 和 all `-1.0` 权重也同样失败。因此问题不是 adapter delta、不是 static weights、也不是 `c weight` parser 或 all-positive phase，而是 `glucose_weighted` binary 的 core/preprocessing path。
9. 补充 `-no-pre` 诊断显示两个 loss base 在 `glucose_weighted` 上关闭 preprocessing 后恢复 solved：`dominating_set_hex_4x5_s5` 为 SATISFIABLE，`vertex_cover_torus_4x5_norat` 为 UNSATISFIABLE，且都进入 search。因此具体失败点应优先查 weighted binary 的 preprocessing/simplification path，而不是 event adapter。
10. `--weighted-no-pre` repeated paired protocol 已重跑完成：855/855 method rows 有效，所有 5 个 method 都是 171/171 solved，known expected 全部 144/144 match，guided-loss diagnostics 为空，所有 attribution rows 都是 `event_collection_overhead_only`。这说明原始退化确实来自 weighted preprocessing，而不是 static guidance 或 adapter delta。该路径现在显式标记为 `weighted_no_pre_diagnostic`，只用于隔离 preprocessing 影响。
11. code audit 的最强嫌疑点是 `glucose_weighted/core/Solver.cc` 在 `search()` 循环顶部新增的 `if(!withinBudget()) return l_Undef;`。当 preprocessing 触发或接近 CPU-limit 后，`SIGXCPU` 会设置 `asynch_interrupt=true`；weighted search 因入口 budget check 在 0 decisions / 0 conflicts 前返回 `INDETERMINATE`。plain Glucose 没有这个入口检查。
12. 已按 plain Glucose 语义移除 weighted `search()` 入口预算检查，并重新编译 `solvers/glucose_weighted/simp/glucose_static`。定向复测显示两个 loss base 在 `pre=true,cpu=5` 下均恢复 search：`dominating_set_hex_4x5_s5` 返回 SATISFIABLE，15 decisions / 0 conflicts；`vertex_cover_torus_4x5_norat` 返回 UNSATISFIABLE，15 decisions / 16 conflicts。
13. patch 后重跑 weighted-path audit：2 个 former loss base x 3 variants x 3 repeats x 5 probes 共 90 行全部 solved，`weighted_glucose_no_weight`、all `+1.0`、all `-1.0` 都不再产生 `INDETERMINATE`；by-base attribution 更新为 `weighted_path_loss_not_reproduced`。
14. patch 后重跑原始 repeated paired protocol，不加 `--weighted-no-pre`，即 patched `pre=true` 主路径：855/855 method rows solved，known expected 144/144 match for every method，guided-loss diagnostics 为空，171/171 attribution rows 全部为 `event_collection_overhead_only`。former loss bases 也全部 solved：`dominating_set_hex_4x5_s5` 的 neutral/static/event/cached/plain 共 45/45 solved，`vertex_cover_torus_4x5_norat` 共 45/45 solved。该主路径现在显式标记为 `patched_pretrue_main`。
15. patched `pre=true` representation protocol 也已补齐：direct event audit 有 165/165 valid rows event-positive，cached adapter audit mean gain valid 为 0.3479，negative-case violation 为 0，逐变量 alignment overall adapted `mu` MAE 为 0.2573。

现在建议的下一步：

1. 暂时不要做 gate/selector，也不要宣称 speedup。
2. 把 patched pre=true protocol 作为当前主路径；`--weighted-no-pre` 只保留为隔离 preprocessing 的对照 path。
3. 继续保留 neutral weighted baseline 和 cached-trace no-adapter ablation，避免把 weighted path、static weights、event overhead、adapter delta 混在一起。
4. 下一步若进入 solver runtime protocol，必须先设计更严格的 paired wall-clock 实验；当前结果仍只是 protocol attribution 与 bugfix 验证，不是 speedup。

完成后，项目可以形成一个清晰 claim：

```text
Static GNN guidance is orbit-collapsed on certified symmetric SAT variables.
Short CDCL event traces induce orbit-level identity inside those orbits.
Event adapters can convert that identity into heldout-family representation separation.
This provides a representation-level basis for event-conditioned symmetry-breaking guidance.
```

这个 claim 比“我们加速了 SAT solver”更稳，也更原创。

## 10. 参考资料

- Shatter / static SAT symmetry breaking：Aloul, Markov, Sakallah, efficient symmetry breaking for Boolean satisfiability.
- BreakID：Devriendt, Bogaerts 等，improved static symmetry breaking for SAT.
- Satsuma：structure-driven detection of SAT symmetries including row/column/Johnson patterns.
- CDCLSym：effective symmetry breaking inside CDCL-style SAT solving.
- Symmetric explanation learning / symmetry propagation：dynamic symmetry handling for SAT.
- SAT modulo symmetries：canonical reasoning and graph generation/enumeration under symmetry.
- NeuroSAT：GNN-based SAT reasoning from single-bit supervision.
- AsymSAT：针对 GNN 在对称 SAT 上无法区分变量的问题，引入 asymmetric graph-based prediction。
- Giraldez-Cru, Levy, Simon, SAT-b paper：提供 PB/SAT combinatorial benchmark families，包括 PHP、subset cardinality、even colouring、vertex cover、dominating set、pebbling 等。
