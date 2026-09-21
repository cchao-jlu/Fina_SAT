# SAT 对称性主线

## 主线定位

Balanced Improve 线冻结为基线。现在主线改成 SAT 对称性问题：

```text
SAT-b 风格 symmetry stress dataset
-> static GNN orbit collapse audit
-> solver event identity audit
-> event-conditioned symmetry-breaking guidance
-> 通过表示审计后才谈 solver speedup
```

核心问题不是先追求求解速度，而是先证明一件更基础的事：

```text
静态 CNF 图里完全对称的变量，GNN 输出会自然 collapse；
短 CDCL rollout 的变量级事件，能否在这些静态 orbit 内产生 identity？
```

如果 event trace 不能在对称变量内部制造可分辨身份，后续 adapter、GRPO 或 selector 都没有可靠基础。

## SAT-b 可用点

用户给的论文：

```text
S. Giraldez-Cru, J. Levy, and L. Simon,
Solving Pseudo-Boolean Problems with SAT, 2018.
https://www.ugr.es/~jgiraldez/publications/2018_SAT-b_paper.pdf
```

这篇不是专门的 symmetry-breaking 方法论文，但它的 PB/SAT benchmark 家族非常适合做对称性压力测试。当前仓库已经实现或映射了这些族：

| SAT-b 风格族 | 对称性来源 | 当前实现 |
| --- | --- | --- |
| pigeonhole principle | pigeon/hole assignment 可交换 | `pigeonhole_cnf` |
| pigeonhole with emergency exits | 主 assignment orbit + exit orbit | `pigeonhole_with_emergency_exit_cnf` |
| subset cardinality | 行/列 cardinality 结构，带局部例外 | `subset_cardinality_fixed_bandwidth_cnf` |
| even colouring | 网格/环面边变量的局部同构 | `even_colouring_torus_cnf` |
| vertex cover | 图顶点同构 + cardinality bound | `vertex_cover_torus_cnf` |
| dominating set | hex/grid-like 图局部同构 | `dominating_set_hex_cnf` |
| graph colouring | 顶点-颜色 assignment 可交换 | `complete_graph_coloring_cnf` |
| Tseitin/parity | 边变量和 charge 引入的 orbit 分裂 | `complete_graph_tseitin_cnf` |

线性化 pebbling 暂时不放第一批，因为它更像 PB-to-CNF 编码扩展，先把上面这些直接 CNF stress 跑通。

## 相关方法地图

需要把我们的路线和已有 SAT symmetry 方法区分清楚：

| 方向 | 代表思路 | 对本项目的启发 | 不直接照搬的原因 |
| --- | --- | --- | --- |
| static SBP | Shatter、BreakID、lex-leader / row interchangeability | 静态 orbit 是必要 baseline | 一次性预处理，不回答 solver trace 是否产生 identity |
| dynamic CDCL symmetry | CDCLSym 类路线 | 搜索状态会改变 symmetry landscape | 需要深改 solver kernel，先做 Python audit 更稳 |
| SAT modulo symmetries | SMS / canonical augmentation | 可作为后期证明和规范形方向 | 当前先不做专用传播器 |
| neural SAT | NeuroSAT、ANYCSP-SAT/GNN policy | GNN 天然 permutation-equivariant，适合测 orbit collapse | 静态 GNN collapse 是 failure mode，不是解决方案 |
| event-conditioned neural guidance | 当前仓库 event-var/trace-distill 分支 | 短 rollout 事件可能打破静态 orbit | 先证明表示，再谈 adapter 和速度 |

## `example.md` 可借鉴点

`example.md` 的两条路线都值得保留，但优先级不同。

S3 / Streaming Symmetry Solver 适合中长期：

- 增量 WL/color refinement：每条 learned clause 后局部更新候选 orbit。
- GASCI：只实例化有收益的对称 learned clause，避免 clause DB 膨胀。
- orbit entropy restart：用 orbit 熵判断搜索是否在对称区域内打转。
- sr/proof-aware symmetry：后期如果要做可验证 solver 贡献，需要这条线。

这些都需要 solver 内核或证明系统改造，不适合作为第一步。

SymGNN / neural absorption 适合当前第一步：

- orbit entropy、static orbit range、permutation stability 是马上可测指标。
- event identity gain 是当前主指标。
- adapter identity gain 只能在 event adapter checkpoint 上测，不能用 Balanced checkpoint 强行 claim。
- contrastive symmetry loss、soft orbit attention、symmetry-aware decision 先放到第二阶段。

## 当前仓库状态

已可用：

- `src/data/symmetry.py`：SAT-b 风格 CNF generator、变量重命名、sign flip、手工 orbit 标签。
- `build_symmetry_stress_dataset.py`：写出 CNF、orbit JSON、metadata、manifest。
- `audit_static_symmetry.py`：测静态 GNN 在 orbit 内的 `rho/mu` collapse 和重命名稳定性。
- `audit_event_symmetry.py`：短 rollout 收集 `event_var_*`，测 event-induced identity；如果 checkpoint 真有 event adapter，才额外测 adapter output range。
- `src/solving/solver.py`：已能解析 `c event var_*` 输出，并正确传递 Glucose boolean flag。
- `src/solving/state.py`：恢复轻量 event-state 编码，支持 `legacy/enhanced/polarity`。

本次还重建了 `solvers/glucose_weighted/simp/glucose_static`，现在 `--help` 中有：

```text
-collect-events, -no-collect-events
```

## 正式审计结果

命令：

```bash
/home/sunshixin/anaconda3/envs/rlaf/bin/python build_symmetry_stress_dataset.py \
  --output-root data/symmetry_stress \
  --manifest runs/analysis/symmetry_stress_manifest.csv \
  --perm-seeds 1730,1731

/home/sunshixin/anaconda3/envs/rlaf/bin/python audit_static_symmetry.py \
  --checkpoint runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt \
  --manifest runs/analysis/symmetry_stress_manifest.csv \
  --output-csv runs/analysis/symmetry_static_orbits.csv \
  --stability-csv runs/analysis/symmetry_static_permutation_stability.csv \
  --doc docs/symmetry_static_audit.md \
  --device cpu

/home/sunshixin/anaconda3/envs/rlaf/bin/python audit_event_symmetry.py \
  --checkpoint runs/GNN_Glucose_3SAT_FeedbackImprover_Balanced/best.pt \
  --manifest runs/analysis/symmetry_stress_manifest.csv \
  --output-csv runs/analysis/symmetry_event_orbits.csv \
  --stats-csv runs/analysis/symmetry_event_rollout_stats.csv \
  --doc docs/symmetry_event_audit.md \
  --solver glucose \
  --rollout-budget-type conflicts \
  --rollout-conflicts 20 \
  --solver-params rnd-freq=0.0,K=0.1 \
  --event-state-features legacy \
  --device cpu
```

完整 stress set 是 36 个实例：12 个 base families/instances，每个加两个 variable permutation variants。

静态审计结论：

| family | mean_static_mu_range | max_static_mu_range | 备注 |
| --- | ---: | ---: | --- |
| `php` | `1.99e-08` | `2.98e-08` | 静态 GNN 完全 collapse |
| `complete_coloring` | `1.99e-08` | `2.98e-08` | 静态 GNN 完全 collapse |
| `tseitin_complete` | `3.60e-08` | `5.59e-08` | 静态 GNN 完全 collapse |
| `vertex_cover_torus` | `3.35e-08` | `4.84e-08` | 静态 GNN 完全 collapse |
| `php_exit_all` | `2.73e-08` | `3.73e-08` | 主 orbit/exit orbit 稳定 |
| `dominating_set_hex` | `2.25e-04` | `2.25e-04` | 静态 range 很小，但 event solver 在该超大 CNF 上失败 |
| `php_exit_single` | `2.00e-03` | `4.00e-03` | orbit 标签较粗，static 已有轻微区分 |
| `subset_cardinality` | `3.77e-03` | `6.01e-03` | orbit 标签较粗，static 已有区分 |
| `even_colouring` | `4.90e-02` | `9.80e-02` | 手工 orbit 标签明显过粗，需细化 |

Permutation stability 通过：各 family 的 `mu_mean_across_variant_std` 最大量级约 `1e-7`，说明纯变量重命名没有破坏审计。

正式 event identity 结果：

| family | ok rows | missing rows | mean_event_l2_range | max_event_l2_range | 解释 |
| --- | ---: | ---: | ---: | ---: | --- |
| `subset_cardinality` | 6 | 0 | `5.100` | `6.509` | 强 event identity |
| `complete_coloring` | 6 | 0 | `3.462` | `6.655` | 强 event identity |
| `php` | 6 | 0 | `3.445` | `6.692` | 强 event identity |
| `tseitin_complete` | 9 | 0 | `0.342` | `0.721` | 中等 event identity |
| `even_colouring` | 6 | 0 | `0.166` | `0.298` | 有 event identity，但 static orbit 标签需细化 |
| `php_exit_all` | 6 | 0 | `0.131` | `0.784` | 有 event identity |
| `php_exit_single` | 6 | 0 | `0.000964` | `0.001928` | event identity 很弱；该族很快 SAT，rollout 信息少 |
| `vertex_cover_torus` | 3 | 0 | `0.000` | `0.000` | 20-conflict rollout 实际 0 decisions/0 conflicts，没有事件身份 |
| `dominating_set_hex` | 0 | 3 | `NaN` | `NaN` | weighted Glucose 对 310 万子句输入 returncode=1 且无 stdout/stderr |

现在可以成立的 claim：

```text
在 PHP、complete graph colouring、subset cardinality、Tseitin 等强对称 CNF 上，
静态 GNN 输出在 orbit 内 collapse；短 solver rollout 的 event trace 能在同一 orbit 内产生非零 identity。
```

现在不能 claim：

```text
不能 claim adapter separation：当前 Balanced checkpoint 没有 event adapter。
不能 claim solver speedup：本轮只做 representation audit。
不能 claim 所有 SAT-b 风格族都通过：vertex_cover_torus 没有 rollout 事件，dominating_set_hex solver 崩溃。
```

## 下一步

1. 修 orbit 标签：优先细化 `even_colouring`、`subset_cardinality`、`php_exit_single`，避免把静态已可区分变量放进同一个 orbit。
2. 修 solver/benchmark 尺度：`dominating_set_hex_4x7_s7` 太大，weighted Glucose 对 310 万子句输入静默失败；需要更小 hex instance 或改 solver stdin/内存路径。
3. 对 `vertex_cover_torus` 使用更合适 rollout 条件：当前 20-conflict budget 下实际 0 events，不能证明 identity。
4. 恢复最小 event adapter checkpoint，只在 `event_identity_gain > 0` 的族上测 `adapter_identity_gain`。
5. adapter 通过后，再设计 solver speedup 实验；必须用总 wall-clock、rebuild 后 solver、固定 seed、短/长预算分开报告。

严禁跳过第 2-4 步直接做速度 claim。
