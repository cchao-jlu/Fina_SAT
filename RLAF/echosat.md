# EchoSAT: 面向 SAT 对称性的 Orbit-Certified Event-Guided 优化方案

日期：2026-06-19

本文档给出当前 SAT symmetry 路线的下一版具体优化方案。目标不是直接宣称 solver speedup，而是把已有 event-adapter / GRPO 路线从“泛化 weighted perturbation”收紧为“有 orbit 证据、event 证据、permutation 鲁棒性和 weighted-path 安全边界的 symmetry-guided CDCL”。

## 1. 一句话方案

EchoSAT 的核心是：

```text
Evidence-Certified Hybrid Orbit SAT guidance

静态 orbit 负责证明哪里存在可利用的对称结构；
短 CDCL event trace 负责提供 orbit 内的搜索身份信号；
adapter / GRPO 只在 symmetry evidence 强且 weighted path 安全时改变 branching weights / phase；
否则回退到 plain Glucose 或 static weighted baseline。
```

和传统 symmetry breaking 的区别是：EchoSAT 不先把问题改造成完整动态对称 SAT solver，也不只做预处理 SBP。它关注一个更窄的问题：

```text
当静态 GNN 在对称变量上 collapse 时，
CDCL 搜索事件能否提供足够稳定的 identity signal，
并且这种 signal 能否以低 overhead 改善 final solve search？
```

## 2. 当前实验证据与问题定位

根据当前项目报告，已有结论应保持保守：

- 静态 GNN 在 refined orbit 上确实存在 collapse，说明“只看 CNF 图结构”的模型很难区分强对称变量。
- 短 CDCL rollout 能在 valid orbit 内产生 event identity，event adapter 也能把这种 identity 转成非零 variable guidance。
- patched `pre=true` weighted Glucose 主路径已经稳定，早期 preprocessing / budget 交互导致的 indeterminate 问题已修复。
- runtime protocol 显示主退化来源是 event collection overhead，而不是 adapter inference。adapter inference 本身约毫秒级，不是瓶颈。
- harder random controls 上 GRPO adapter 出现了 final-solve win，说明 learned weighted guidance 有加速潜力。
- 但 random controls 是 non-symmetric，不能算 symmetry benefit。当前信号仍可能是 learned portfolio perturbation。
- dominating_set_hex / vertex_cover_torus 主要输在 weighted path 风险和 event overhead，adapter final solve 相对 static weighted 接近 neutral。
- `subset_cardinality_bw12::perm_seed1730` 是关键失败样本：event 和 adapter separation 都存在，但 permutation 后 final decisions/conflicts 反向变差，说明当前 objective 缺少 permutation-robust search alignment。

2026-07-20 主线状态：

- `symmetry_grpo_v1_7` 的失败归因已经完成：问题集中在训练可见 positive advantage 泄漏和 hard-negative 压力不足，而不是需要扩大 benchmark。
- `symmetry_grpo_v1_8` 的离线 objective-repair dry-run 已完成，并保持 `ALL_V1_8_DRYRUN_CHECKS=True`：`129312` 行 replay 中，blocked rows 为 `95642`，blocked raw/final positive 均为 `0`，hard-negative final pressure 从 v1.7 的 `0.51943` 提升到 `0.657095`。
- `symmetry_grpo_v1_8` 已移植到正式训练 target：`train_rlaf.py` 支持 `echosat_target_mode: symmetry_grpo_v1_8`，训练路径会对 blocked positive signal 同时 clamp raw/final advantage upper bound，并对 search-ok hard-negative 增加 `echosat_v18_hard_negative_pressure`。
- v1.8 dry-run 现在复用正式 helper，避免离线分析和训练路径分叉。
- 新配置 `configs/config_train_rlaf_echosat_symmetry_grpo_v1_8_wc1_objectiverepair.yaml` 是首个 v1.8 formal-path shakeout：仍从 `runs/GNN_Glucose_3SAT_EchoSAT_SymmetryGRPO_v1_2_WC1_HardNeg_Full/iter=15.pt` 起步，先跑 `20` iterations，不作为长训练或 speedup claim。

因此下一步优化重点不是继续堆 benchmark，也不是马上训练 selector，而是：

1. 把 symmetry evidence 变成训练和推理的硬边界。
2. 把 GRPO reward 从“最终跑得快”改成“在 valid orbit 上稳定减少 search work”。
3. 把 weighted path 风险先用规则 veto 控住。
4. 把 event overhead 降到小于可见 final-solve gain 的量级。

## 3. 相关论文与可借鉴点

### 3.1 静态 symmetry breaking

代表方法：

- Aloul, Ramani, Markov, Sakallah: Shatter / SAT symmetry breaking 系列工作。
- Aloul et al., "Breaking Instance-Independent Symmetries In Exact Graph Coloring"。
- BreakID: 静态 symmetry breaker，重点利用 row interchangeability。
- Anders, Brenner, Rattan, "satsuma: Structure-based Symmetry Breaking in SAT"。
- Anders, Codel, Heule, "Orbitopal Fixing in SAT"。

可借鉴点：

- CNF 应转成 colored graph 或结构化矩阵视图，orbit 不能只靠人工粗标。
- 对称结构往往不是单一 permutation group，而是 row interchangeability、row-column symmetry、Johnson symmetry、product action 等组合。
- 完整 lex-leader SBP 往往太重，低干扰、结构化、局部化的 symmetry breaking 更稳。
- Orbitopal Fixing in SAT 的关键思想是只加 unit clauses，并保持 proof-friendly，这说明 symmetry handling 需要尽量低干扰，而不是大规模改写公式。

对 EchoSAT 的具体转化：

- 不把 SBP 作为主方法，而是把 Satsuma / BreakID 类结构检测作为 orbit teacher。
- 用 orbit teacher 生成 valid orbit mask、structure type、orbit confidence，作为 adapter loss 和 GRPO reward 的证据边界。
- 后续可把 orbitopal fixing 作为独立 baseline，而不是混进 event-adapter 主线。

### 3.2 动态 symmetry handling 和 SAT Modulo Symmetries

代表方向：

- CDCLSym / dynamic symmetry handling。
- SAT Modulo Symmetries。
- Kirchweger, Peitl, Szeider, "Co-Certificate Learning with SAT Modulo Symmetries"。
- `example.md` 中的 S3：Streaming Symmetry Solver。

可借鉴点：

- 对称性不是纯静态对象。搜索轨迹、赋值、冲突子句会改变“当前有效”的对称结构。
- learned clause 的 symmetry image 可能有用，但盲目加入会造成 clause database 膨胀。
- 动态 symmetry handling 必须 budgeted、gain-aware、proof-aware。

对 EchoSAT 的具体转化：

- 第一阶段不深改 Glucose kernel，不做完整 S3。
- 只做 S3-lite：记录 learned/event-active variables 在 orbit 内的分布，计算 orbit entropy、event concentration、representative drift。
- GASCI 暂时不真的添加 symmetry image clauses，只作为 offline score：如果某个 learned/event pattern 在 orbit 上高度集中，再考虑后续 solver-level 实验。

### 3.3 神经 SAT、GNN 对称盲区和 learned branching

代表方法：

- Selsam et al., "Learning a SAT Solver from Single-Bit Supervision" / NeuroSAT。
- Selsam & Bjorner 的 NeuroCore 方向，以及 Han, "Enhancing SAT solvers with glue variable predictions"。
- Yan et al., "Addressing Variable Dependency in GNN-based SAT Solving" / AsymSAT。
- MILP-SAT-GNN 等强调 permutation invariance / foldable formula limitation 的工作。

可借鉴点：

- GNN 的 permutation equivariance 是优势也是限制。对完全对称变量，没有额外输入时输出 collapse 是预期行为。
- AsymSAT 指出 concurrent prediction 在对称 SAT 上会因为变量依赖失败；这支持“需要 search-conditioned asymmetric information”的判断。
- NeuroCore / glue variable prediction 的经验说明：神经网络不应每个 CDCL decision 都调用，更合理的是周期性 refocus heuristic 或一次性提供 variable scores。

对 EchoSAT 的具体转化：

- 不让模型“吸收对称性并继续 collapse”，而是学习“有证据地打破对称”。
- adapter 只输出 residual delta，不替代 Glucose 的 VSIDS / phase saving。
- 训练目标必须绑定 final decisions/conflicts delta，而不是只追求 representation separation。

### 3.4 SAT portfolio / algorithm selection

代表方法：

- Xu, Hutter, Hoos, Leyton-Brown, "SATzilla: Portfolio-based Algorithm Selection for SAT"。

可借鉴点：

- SAT 中通常没有单一 dominant solver；不同实例应走不同路径。
- 对 EchoSAT 来说，plain Glucose、neutral weighted、static weighted、cached trace、event adapter 本质上就是一个小 portfolio。
- 在训练 selector 前，先用规则 veto 证明“避开明显坏路径”是否能改善 protocol。

对 EchoSAT 的具体转化：

- 先实现 rule-based weighted-path veto。
- selector / gate 只有在 rule-based veto 有稳定收益后才训练。

## 4. EchoSAT 总体架构

EchoSAT 分成五层：

```text
CNF
  -> Orbit Certification Layer
  -> Static GNN Layer
  -> Short CDCL Event Layer
  -> Event Adapter / GRPO Policy Layer
  -> Weighted-Path Veto + Final Solver Layer
```

### 4.1 Orbit Certification Layer

输入：

- CNF。
- generator metadata。
- manual orbit labels。
- 可选外部 symmetry detector：Satsuma / BreakID / saucy / bliss / nauty。

输出一张 orbit table：

| 字段 | 含义 |
| --- | --- |
| `base_instance_id` | 聚合单位，permutation variants 不能独立算样本 |
| `variant` | `base` / `perm_seed*` |
| `orbit_id` | orbit 标识 |
| `vars` | orbit 内变量集合 |
| `orbit_size` | orbit 大小 |
| `structure_type` | row / row-column / Johnson / torus / coloring / unknown |
| `symmetry_strength` | strong / weak / pseudo / none |
| `certification_source` | manual / generator / automorphism / structure_detector |
| `orbit_confidence` | 0 到 1 |
| `valid_for_training` | 是否允许作为 adapter symmetry loss 样本 |

关键规则：

- random controls 默认 `symmetry_strength=none`，不进入 symmetry-positive reward denominator。
- weak / pseudo orbit 可以用于 diagnostics，但训练权重要低。
- 如果 manual orbit 和 detector orbit 冲突，进入 `needs_refinement`，不能作为 high-confidence reward。

### 4.2 Static GNN Layer

目标不是直接求解，而是提供 baseline variable guidance：

```text
y_static_i = GNN(CNF)_i
```

必须保留的 audit：

- orbit 内 `static_mu_range`。
- permutation alignment：`P^{-1} y_static(P(CNF))` vs `y_static(CNF)`。
- static weighted vs plain 的 weighted-path risk。

静态 GNN collapse 不是 bug，而是核心对照。只有先证明 static collapse，event-conditioned delta 才有意义。

### 4.3 Short CDCL Event Layer

短 rollout 收集每个变量的搜索事件：

- decisions。
- conflicts。
- propagated / assigned counts。
- conflict literal participation。
- learnt-clause participation。
- activity snapshots。
- optional: phase saving state。

事件状态：

```text
e_i = EventFeatures(CDCL_warmup, variable i)
```

建议先做 event overhead 优化：

- 只对 `valid orbit vars` 和 top-k static candidates 收集完整 event。
- 对 random controls 只收集压缩统计，避免它们主导 event adapter。
- warmup 使用 adaptive early stop。

early stop 条件：

```text
stop if conflicts >= conf_lim
stop if warmup_cpu >= warmup_cpu_lim
stop if event_l2_orbit_gain saturates for K checks
stop if valid_orbit_coverage >= coverage_target
stop if weighted-path veto already fires
```

### 4.4 Event Adapter / GRPO Policy Layer

adapter 只输出 residual：

```text
delta_i = Adapter(y_static_i, e_i, orbit_features_i, graph_features)
y_adapted_i = y_static_i + delta_i
```

转换到 weighted Glucose：

```text
weight_i = clip(exp(scale * y_adapted_i), w_min, w_max)
phase_i = sign_or_probability(y_adapted_i)
```

核心约束：

- 无 valid orbit evidence 时，`delta_i` 应接近 0。
- event L2 为 0 或 no-activity 时，`delta_i` 应接近 0。
- random controls 可以允许小扰动，但不能用作 symmetry-positive reward。
- permutation variants 上，delta 必须在变量重命名后对齐。

### 4.5 Weighted-Path Veto + Final Solver Layer

候选路径：

1. `plain_unguided_glucose`
2. `neutral_weighted_glucose`
3. `static_weighted_glucose`
4. `cached_trace_no_adapter_final`
5. `event_adapter_final`

veto 规则先于 gate/selector：

```text
if neutral_weighted much slower than plain:
    use plain
elif static_weighted much slower than neutral:
    use plain or neutral
elif final solve is near cap in calibration:
    use plain
elif event overhead estimate > expected final gain:
    use static or plain
elif no valid orbit evidence:
    use static or plain
else:
    allow event adapter
```

初始阈值建议：

| 规则 | 初始阈值 |
| --- | --- |
| neutral weighted slowdown | `neutral_cpu - plain_cpu > max(0.05s, 0.1 * plain_cpu)` |
| static weighted slowdown | `static_cpu - neutral_cpu > max(0.05s, 0.1 * neutral_cpu)` |
| near cap risk | `method_cpu > 0.8 * cpu_cap` |
| event overhead risk | `warmup_cpu > min(1.0s, 0.25 * cpu_cap)` |
| weak event signal | `event_l2_valid_orbits < epsilon` |
| insufficient orbit coverage | `covered_valid_orbit_vars / valid_orbit_vars < 0.2` |

这些阈值是诊断起点，不应直接写成最终结论。每次使用必须报告 vetoed bases、family-level deltas 和 correctness。

## 5. GRPO 优化目标修改

当前 GRPO 如果直接以 runtime speedup 为 reward，容易学到 random-control 上的 generic perturbation。EchoSAT 的 reward 应拆成 evidence-gated reward。

### 5.1 基础 final-solve reward

对每个 instance / variant / repeat，定义：

```text
R_final_cpu =
  clip((cpu_baseline - cpu_adapter) / max(cpu_baseline, eps), -1, 1)
```

baseline 优先级：

1. `static_weighted_glucose`：衡量 adapter 增量是否有用。
2. `cached_trace_no_adapter_final`：隔离 adapter delta。
3. `plain_unguided_glucose`：最终实用对比，但不作为唯一 reward。

不要只看 wall-clock protocol，因为当前 event overhead 会掩盖 final-solve mechanism。训练目标应同时记录 final CPU 和 protocol time。

### 5.2 Search-work reward

SAT 求解时间噪声大，decisions / conflicts 更能反映机制：

```text
R_search =
  a * norm_delta(decisions_baseline, decisions_adapter)
  + b * norm_delta(conflicts_baseline, conflicts_adapter)
```

其中：

```text
norm_delta(x_base, x_adapt) =
  clip((x_base - x_adapt) / max(x_base, 1), -1, 1)
```

建议初始权重：

```text
a = 0.4
b = 0.6
```

原因：conflicts 更接近 CDCL 学习过程，decisions 更受 branching order 影响。

### 5.3 Symmetry evidence gate

只在有 symmetry evidence 时放大奖励：

```text
E_sym =
  orbit_confidence
  * valid_orbit_mask
  * sigmoid(log1p(event_l2_valid_orbits) - tau_event)
  * permutation_alignment_score
```

其中：

```text
permutation_alignment_score =
  exp(-lambda_perm * delta_alignment_mae)
```

最终 symmetry reward：

```text
R_sym = E_sym * (R_final_cpu + R_search)
```

random controls：

```text
E_sym = 0
```

它们可以提供 robustness penalty，但不能提供 symmetry-positive reward。

### 5.4 Protocol overhead penalty

```text
R_overhead =
  - clip((warmup_cpu + event_attach_wall + adapter_infer_wall)
         / max(cpu_baseline, eps), 0, 1)
```

训练时不要让 overhead penalty 完全压死 mechanism 学习。建议分阶段：

- Phase 1：弱 overhead penalty，先学 final-solve mechanism。
- Phase 2：加入真实 overhead penalty。
- Phase 3：配合 veto / early stop。

### 5.5 Weighted-path risk penalty

如果 neutral/static weighted 已经伤 solver，adapter 不应背锅，也不应继续在这类实例上学大 delta：

```text
R_weighted_risk =
  - 1[neutral_slower_than_plain]
  - 1[static_slower_than_neutral]
  - 1[near_cap]
```

实际可用软版本：

```text
risk =
  relu((neutral_cpu - plain_cpu) / max(plain_cpu, eps) - t_neutral)
  + relu((static_cpu - neutral_cpu) / max(neutral_cpu, eps) - t_static)
  + relu(cpu_static / cap - 0.8)
```

### 5.6 Perturbation penalty for controls

对 non-symmetric controls，允许模型作为 portfolio 产生小扰动，但不能靠大幅 weight re-ranking 获得主 reward：

```text
R_control_penalty =
  - control_mask * (
      c1 * mean_abs(delta_weight)
      + c2 * phase_flip_frac
      + c3 * rank_change_penalty
    )
```

这可以防止模型学成“所有实例都强行改权重”的策略。

### 5.7 Permutation consistency penalty

对 base / permuted pair：

```text
L_perm_delta =
  || P^{-1} delta(P(CNF), P(event)) - delta(CNF, event) ||_1
```

更细的 orbit 版本：

```text
L_perm_orbit =
  mean_orbit_mae(
    P^{-1} delta_perm[orbit_perm],
    delta_base[orbit_base]
  )
```

只对 valid orbit 强约束；对 event trace 本身不稳定的 pair 降权：

```text
weight_pair = exp(-lambda_event * event_state_alignment_error)
```

### 5.8 Delta magnitude regularization

```text
L_mag =
  mean_i |delta_i| * (1 - E_sym_i)
```

含义：

- 有 evidence 的 orbit 内允许 separation。
- 没有 evidence 的变量应保持静态 GNN 输出。

### 5.9 最终 GRPO reward 草案

```text
R_total =
    w_sym      * E_sym * (R_final_cpu + R_search)
  + w_portfolio * (1 - symmetry_benchmark_mask) * R_final_cpu_control_small
  + w_overhead * R_overhead
  + w_risk     * R_weighted_risk
  + w_control  * R_control_penalty
  + w_correct  * R_correctness
```

建议初始权重：

| 项 | 权重 |
| --- | --- |
| `w_sym` | 1.0 |
| `w_portfolio` | 0.15 |
| `w_overhead` | 0.2 in Phase 1, 0.5 in Phase 2 |
| `w_risk` | 0.5 |
| `w_control` | 0.3 |
| `w_correct` | hard constraint |

correctness 必须是硬约束：

```text
if known_expected_result and solver_result != expected:
    R_total = -large_penalty
```

UNKNOWN rows 不进入 correctness denominator，但保留 runtime / search-work metrics。

## 6. 训练数据设计

训练集应从 random 3-SAT 主导改成 symmetry stress / ladder / permutation-paired 主导，并加入 random controls 防止泛化成纯扰动。

### 6.1 数据族

建议保留和扩展：

- `complete_coloring`
- `php`
- `php_exit_single`
- `php_exit_all`
- `subset_cardinality`
- `tseitin_complete`
- `even_colouring`
- `dominating_set_hex`
- `vertex_cover_torus`
- `random_3sat_control`
- weak-symmetric controls

### 6.2 样本结构

每个 base instance 至少包含：

```text
base
perm_seed1730
perm_seed1731
```

训练和验证必须按 `base_instance_id` 分组，不能把 permutation variants 当独立样本。

### 6.3 推荐配比

| 类别 | 比例 | 作用 |
| --- | --- | --- |
| strong symmetric ladder | 35% | 主 symmetry reward |
| weak symmetric ladder | 20% | 测边界和泛化 |
| diagnostic hard hex/torus | 15% | weighted risk / overhead stress |
| complete_coloring / PHP calibration | 10% | symmetry-positive calibration |
| random controls | 15% | 防止纯 symmetry overfit，检测 generic perturbation |
| static-only / no-activity negatives | 5% | negative guardrail |

### 6.4 训练权重

不是所有样本等权：

```text
sample_weight =
  base_weight
  * orbit_confidence
  * family_balance_weight
  * not_near_duplicate_weight
```

建议：

- random controls 的 positive runtime gain 不进入 `R_sym`。
- near-cap hex/torus 主要用于 veto / risk penalty，不用于鼓励 adapter 放大 delta。
- permutation failure cases 必须提高权重，例如 `subset_cardinality_bw12::perm_seed1730`。

## 7. Event overhead 优化路线

当前 runtime 主要被 event collection overhead 主导，因此必须单独优化。

### 7.1 Warmup budget sweep

先跑小型 sweep：

```text
warmup_cpu_lim in {0.1, 0.25, 0.5, 1.0, 2.0}
conf_lim in {5, 10, 20, 50}
```

每个点报告：

- event-positive orbit coverage。
- event L2。
- adapter delta magnitude。
- final decisions/conflicts delta。
- final CPU delta。
- protocol time delta。

判断标准：

```text
如果 0.25s warmup 已达到 80% event_l2 和 80% search gain，
则默认 warmup 不应超过 0.25s。
```

### 7.2 Orbit-filtered event collection

只对以下变量收集完整 event：

- valid orbit vars。
- static top-k variables。
- recent VSIDS top-k variables。
- conflict-active variables。

其他变量只保留 aggregate counters。

### 7.3 Single-run injection

当前 pipeline 如果是 warmup solver + final solver 两段式，会天然多付一次启动和 preprocessing 成本。更优方向：

```text
start Glucose
  -> run warmup until event budget
  -> adapter forward
  -> inject weights / phase into same solver state
  -> continue final solve
```

这需要改 solver integration，但它是最终实现真实 speedup 的关键。

短期可先做 no-event-cost oracle accounting：

```text
protocol_oracle_time =
  final_solve_time + adapter_inference_time
```

只用于判断 mechanism 上限，不能作为 speedup claim。

## 8. Weighted-path veto 方案

### 8.1 为什么先做 veto

harder baseline 已说明：

- random controls 上 adapter 有 win。
- hex/torus 上 adapter-minus-static final CPU 近似 neutral。
- hex/torus 主要输在 weighted binary path 和 event overhead。

这意味着继续训练 adapter 不会自动修复 weighted path 风险。先做 veto 是必要的。

### 8.2 Veto 输入特征

| 特征 | 来源 |
| --- | --- |
| `plain_cpu_calib` | plain short/full calibration |
| `neutral_cpu_calib` | neutral weighted |
| `static_cpu_calib` | static weighted |
| `warmup_cpu` | event collection |
| `event_l2_valid` | event audit |
| `orbit_coverage` | orbit event coverage |
| `near_cap` | cpu / cap |
| `num_clauses`, `num_vars` | CNF metadata |
| `family`, `scale`, `symmetry_strength` | manifest |

### 8.3 Veto 输出

```text
solver_path_role =
  plain_fallback
  neutral_weighted_safe
  static_weighted_safe
  event_adapter_allowed
```

### 8.4 评估

必须报告：

- vetoed bases。
- family-level protocol delta。
- family-level final CPU delta。
- correctness。
- random-control wins 是否被杀掉。
- hex/torus losses 是否被消除。

如果 rule-based veto 没有稳定改善，就不应训练 selector。

## 9. 评估协议

### 9.1 主对比方法

固定五个方法：

1. `plain_unguided_glucose`
2. `neutral_weighted_glucose`
3. `static_weighted_glucose`
4. `cached_trace_no_adapter_final`
5. `event_adapter_final`

额外 ablation：

6. `matched_weight_only`
7. `matched_weight_phase`
8. `rule_veto_policy`
9. optional `satsuma_orbitopal_baseline`

### 9.2 聚合单位

主统计单位必须是：

```text
base_instance_id
```

permutation variants 只用于 stability / robustness，不作为独立成功样本。

### 9.3 必报指标

| 指标 | 目的 |
| --- | --- |
| final CPU | adapter 是否改变 final solve |
| protocol wall-clock | 实际可用性 |
| decisions / conflicts | 搜索机制 |
| correctness | 安全边界 |
| timeout / near-cap | 风险 |
| event overhead | overhead attribution |
| adapter inference time | 排除模型推理瓶颈 |
| weighted-path delta | 判断 weighted binary 风险 |
| permutation alignment MAE | 鲁棒性 |
| matched perturbation gap | 排除 generic perturbation |

### 9.4 能否 claim symmetry benefit 的标准

只有同时满足以下条件，才可以写 symmetry benefit：

1. 在 high-confidence symmetric bases 上，event adapter 相对 static/cached 减少 final decisions 或 conflicts。
2. 这种减少在 base / permutation variants 上方向一致。
3. random controls 上的收益不能解释主要结果，matched perturbation baseline 不能复现同等收益。
4. protocol overhead 不吞掉全部 final-solve gain，或 single-run / low-overhead path 已证明可行。
5. weighted-path veto 后，hex/torus 这类高风险 family 不再造成系统性退化。

否则只能写：

```text
partial mechanism evidence
runtime viability evidence
generic perturbation evidence
```

不能写 solver speedup claim。

## 10. 分阶段执行计划

### Phase A: Orbit Teacher 与数据清理

目标：把 orbit evidence 从手工标签升级为可审计的训练边界。

任务：

- 为每个 symmetry family 生成 orbit table。
- 对接 Satsuma / saucy / bliss / nauty 中至少一个 detector，先做 offline audit。
- 标记 `orbit_confidence`、`structure_type`、`valid_for_training`。
- 重跑 static collapse / event-positive / adapter separation audit。

产物：

- `runs/analysis/echosat_orbit_certification.csv`
- `docs/echosat_orbit_certification.md`

通过标准：

- high-confidence orbit 上 static collapse 仍成立。
- random controls 不被误标为 high-confidence symmetric。
- permutation variants 的 orbit mapping 可追踪。

### Phase B: Weighted-path veto 固化

目标：先避免明显坏路径。

任务：

- 用已有 runtime table 离线 sweep veto thresholds。
- 将 best diagnostic policy 固化为 rule-based protocol variant。
- 在 harder target manifest 上复核。

产物：

- `docs/echosat_weighted_path_veto.md`
- `runs/analysis/echosat_weighted_path_veto_policy.csv`

通过标准：

- hex/torus protocol loss 明显下降。
- random-control win 不被完全杀掉。
- correctness 不变。

### Phase C: Event overhead budget sweep

目标：找出 warmup 的最小有效预算。

任务：

- 跑 `{0.1, 0.25, 0.5, 1.0, 2.0}` warmup CPU。
- 对比 event L2、adapter delta、final decisions/conflicts、protocol delta。
- 估算 single-run injection 的理论收益上限。

产物：

- `docs/echosat_event_overhead_sweep.md`
- `runs/analysis/echosat_event_budget_sweep.csv`

通过标准：

- 找到默认 warmup budget。
- 明确哪些 family 不值得 event path。

### Phase D: Symmetry-specific GRPO v1

目标：训练不再被 random-control perturbation 主导。

任务：

- 实现 evidence-gated reward。
- 加入 permutation delta consistency。
- 加入 control perturbation penalty。
- 加入 weighted-risk penalty。
- 训练 family-heldout 和 seed-heldout 两组 checkpoint。

产物：

- `docs/echosat_grpo_symmetry_reward_v1.md`
- `runs/GNN_Glucose_3SAT_EchoSAT_GRPO_v1/`

通过标准：

- high-confidence symmetric bases 上 final decisions/conflicts 有稳定改善。
- permutation failure case 不再系统性反向。
- random controls 仍可作为 robustness，但不主导 reward。

### Phase E: Runtime viability v1

目标：验证完整 protocol，而不是只看 final solve。

任务：

- 对比 plain / neutral / static / cached / adapter / veto-policy。
- base-level bootstrap。
- family-heldout 汇总。
- matched perturbation ablation。

产物：

- `docs/echosat_runtime_viability_v1.md`
- `runs/analysis/echosat_runtime_viability_v1_per_instance.csv`

通过标准：

- 至少一个 symmetry family 在 base-level 上有稳定 final-solve search-work gain。
- protocol time 不出现大规模退化。
- matched perturbation 不能解释 symmetry-positive 结果。

### Phase F: S3-lite 机制实验

目标：借鉴 `example.md` 的 S3，但不深改 solver。

任务：

- 记录 learned clauses / conflict vars 在 orbit 内的 concentration。
- 计算 orbit entropy over time。
- 评估 event-active representative 是否稳定。
- 离线估算 GASCI candidate gain，不添加 clauses。

产物：

- `docs/echosat_s3_lite_mechanism.md`

通过标准：

- 能解释哪些 orbit 的 event identity 真正影响 final search。
- 决定是否值得进入 solver-kernel 级实验。

## 11. 关键消融实验

| 消融 | 问题 |
| --- | --- |
| no orbit evidence | 模型是否退化成 generic perturbation |
| no event features | static weighted 是否已经解释收益 |
| no permutation loss | permutation failure 是否复现 |
| no control penalty | random controls 是否主导 reward |
| no weighted veto | hex/torus 是否继续系统性退化 |
| matched perturbation | GRPO 是否只是随机 weight re-ranking |
| no-event-cost oracle | mechanism 上限是否存在 |
| low warmup budget | overhead 是否可压缩 |
| family-heldout | 是否跨 family 泛化 |
| seed-heldout | 是否只记住 generator seed |

## 12. 风险与对应处理

### 风险 1：orbit teacher 误标

处理：

- high-confidence orbit 才进入主 reward。
- weak / pseudo orbit 只做 diagnostic。
- manual 和 detector 冲突时降权。

### 风险 2：event trace 本身 permutation 不稳定

处理：

- permutation loss 按 event alignment error 降权。
- 不要求 event 完全一致，只要求最终 delta 不产生反向 search effect。

### 风险 3：weighted path 本身伤 solver

处理：

- veto 先于 adapter。
- neutral/static weighted calibration 必须出现在主表。
- near-cap family 默认保守。

### 风险 4：random controls 继续赢

处理：

- random controls 不进入 symmetry-positive reward。
- 保留 portfolio 分支，但单独报告。
- matched perturbation 和 static weighted 必须并列对照。

### 风险 5：event overhead 吞掉收益

处理：

- warmup budget sweep。
- orbit-filtered event collection。
- single-run injection 作为最终工程目标。

## 13. 建议的近期优先级

当前最高优先级：

1. 跑 v1.8 short formal training：使用 `configs/config_train_rlaf_echosat_symmetry_grpo_v1_8_wc1_objectiverepair.yaml`，先只做 20-iteration shakeout。
2. 审 v1.8 reward replay：确认 `echosat_v18_blocked_positive_signal` 覆盖 random/subset/anchor_failure/hard_negative_failure/search_bad/weighted-risk/near-cap，且 blocked raw/final positive 仍为 0。
3. 对比 v1.8 short checkpoint 和保守 runtime candidate `v1.2 iter=15.pt` 的 mechanism 指标：只看 decisions/conflicts、anchor/hard-negative retention、random-control leakage，不做 solver speedup claim。
4. 如果 v1.8 short replay 通过，再决定是否把 v1.8 配置升回 v1.7 的 120-iteration formal size。

后续优先级：

1. Orbit teacher / certification table。
2. Weighted-path veto protocol。
3. Event budget sweep。
4. Symmetry-specific GRPO reward v1。

暂缓：

- 完整 S3 dynamic solver。
- 大规模 benchmark 扩张。
- learned selector / gate。
- SBP 与 event adapter 混合主实验。

原因：

- 当前最弱环节是 objective 和 overhead，不是数据量。
- 如果不先区分 symmetry benefit 和 generic perturbation，继续训练会让结果更难解释。
- 如果不先处理 weighted-path risk，hex/torus 会持续污染 runtime 结论。

## 14. 参考文献

1. F. A. Aloul, A. Ramani, I. L. Markov, K. A. Sakallah. Shatter / SAT symmetry breaking 系列工作。可借鉴 CNF colored graph、graph automorphism、SBP preprocessing。
2. F. A. Aloul, I. L. Markov, A. Ramani, K. A. Sakallah. "Breaking Instance-Independent Symmetries In Exact Graph Coloring." arXiv:1109.2347. https://arxiv.org/abs/1109.2347
3. Jo Devriendt, Bart Bogaerts. "BreakID: Static Symmetry Breaking for ASP." arXiv:1608.08447. https://arxiv.org/abs/1608.08447
4. Markus Anders, Sofia Brenner, Gaurav Rattan. "satsuma: Structure-based Symmetry Breaking in SAT." arXiv:2406.13557. https://arxiv.org/abs/2406.13557
5. Markus Anders, Cayden Codel, Marijn J. H. Heule. "Orbitopal Fixing in SAT." arXiv:2601.16855. https://arxiv.org/abs/2601.16855
6. Volker Kaibel, Matthias Peinhardt, Marc E. Pfetsch. "Orbitopal Fixing." arXiv:math/0611531. https://arxiv.org/abs/math/0611531
7. Markus Kirchweger, Tomas Peitl, Stefan Szeider. "Co-Certificate Learning with SAT Modulo Symmetries." arXiv:2306.10427. https://arxiv.org/abs/2306.10427
8. Daniel Selsam, Matthew Lamm, Benedikt Bunz, Percy Liang, Leonardo de Moura, David L. Dill. "Learning a SAT Solver from Single-Bit Supervision." arXiv:1802.03685. https://arxiv.org/abs/1802.03685
9. Jesse Michael Han. "Enhancing SAT solvers with glue variable predictions." arXiv:2007.02559. https://arxiv.org/abs/2007.02559
10. Zhiyuan Yan, Min Li, Zhengyuan Shi, Wenjie Zhang, Yingcong Chen, Hongce Zhang. "Addressing Variable Dependency in GNN-based SAT Solving." arXiv:2304.08738. https://arxiv.org/abs/2304.08738
11. Lin Xu, Frank Hutter, Holger H. Hoos, Kevin Leyton-Brown. "SATzilla: Portfolio-based Algorithm Selection for SAT." arXiv:1111.2249. https://arxiv.org/abs/1111.2249
12. `example.md`: S3 / SymGNN 方案。本文档采用其中的流式 event、GASCI、orbit entropy、神经对称学习思想，但把第一阶段收缩为 S3-lite 和 evidence-gated adapter。
