# EchoSAT：下一阶段研究与实施计划

更新日期：2026-09-21。状态：研究计划，尚未执行以下新实验。

## 1. 决策摘要

继续研究，但暂停沿现有 v2 目标直接长训。主问题改为：**经过独立验证的对称轨道，是否使短 CDCL 事件成为更有效的搜索控制信号，并在低开销执行中产生端到端收益？**

必须区分三个层级：表征分离、搜索工作下降、完整系统加速。前一层成立不推出后一层成立。不得把控制组上的一般启发式收益解释成对称性贡献。

主体路线为“可靠轨道信息 + 搜索状态条件化的有限启发式干预”。不以增加 adapter 容量、添加更多命名实例惩罚、训练 selector 或扩大训练时长为默认下一步。静态 GNN 是待消融组件，不是不可移除的前提。

## 2. 本地证据与局限

### 2.1 已有基础

- 对称 CNF 生成、变量置换、静态 collapse / event / adapter 审计。
- modified Glucose、低 warmup、cached-no-adapter 配对基线和协议成本分解。
- v2 orbit 特征、weight-only bounded residual、约束目标及训练回放。
- v1.2 iter=15 是历史 wc1 定向验收保留候选，不是已证明的全局最优。
- v2 neutral-equivalence 报告分别记录 deterministic / CPU 模式 4197/4197 pairs 通过；两种模式的标准不同。

### 2.2 不能忽视的负面证据

- Stage 5 Retry1 已保存到 iter=20，但日志中 iteration 0/5/10/15 的 best-checkpoint gate 均失败，无 best.pt。
- 20 轮训练回放共 21072 个采样行，2048 行 eligible，872 行正 advantage，blocked-positive 为 0。
- 同一批回放有 521 行标记 plain solved → guided unsolved。它们是采样行，不是独立实例，也不能直接解释为部署失败率。
- 日志存在 OMP SHM 错误。执行异常、正常 timeout 和策略退化必须拆开归因。
- strictbest 集有 125 个 instance ID，其中 74 个与 train split 重叠；9 个 base 中 6 个重叠。它只能作回归验收，不能作独立泛化评估。
- 当前 orbit confidence 由 strong/weak/pseudo 元数据映射而来，来源为 generator/manual JSON，不等同于数学认证或概率校准。
- 当前选模对 random-control 改善和指定 subset 变体改善施加惩罚。诊断用历史约束不应永久变成“要求某样本继续失败”。
- 历史报告曾出现 weighted coverage 损失、formula-equivalent 的 coloring/PHP 重复和 clause-order 混杂；不得将不同时期的 solver binary 结果混为一组。

原始来源在 `RLAF/docs/`、`RLAF/runs/analysis/` 和 Stage 5 Retry1 的配置、日志及回放 CSV。发布快照索引见 `EXPERIMENT_SNAPSHOT.md`。

## 3. 文献定位与基线要求

本节记录 2026-09-21 调研中识别的相关工作，不声称穷尽检索或绝对新颖性。

| 工作 | 对本项目的约束 |
| --- | --- |
| AsymSAT（DATE 2024） | GNN 对称性盲区和非对称预测已有前作；赋值预测与分支启发式须区分。 |
| On the Expressive Power of GNNs for Boolean Satisfiability（ICLR 2026） | 静态表达能力限制不能独立作为主要创新。 |
| Learning from Algorithm Feedback（ICLR 2026） | GNN 权重、极性和求解器奖励训练已有直接前作；保留原项目归属与引用。 |
| Enhancing SAT solvers with glue variable predictions | 低频神经引导及 glue/event 信号已有基础，必须比较简单规则与随机基线。 |
| Orbitopal Fixing in SAT（TACAS 2026） | 对称处理可以通过单位子句和可检查证明简化公式。 |
| Simplify, Order, Break, Repeat（SAT 2026） | 新版 satsuma 的迭代简化、排序和轻量对称破缺是强基线。 |
| Faster Certified Symmetry Breaking | 对称破缺证明与检查成本是系统设计问题。 |
| On Symmetries and Transformations（CP 2026） | 编码、预处理会改变可见对称性和变量映射。 |
| CDCLSym / SAT Modulo Symmetries | “搜索中利用对称性”本身不是新方向。 |

启动新实验前固定论文、代码 commit、artifact 版本和 solver 编译参数；不得将未核实的竞争结果或模糊 master 分支作为基线。参考入口保留在此前调研回复；这里按论文标题列出，以避免把尚未复查的 URL 当作正式文献记录。

## 4. 可证伪假设

- H1（事件关联）：真实 event→变量对应优于轨道内打乱对应。
- H2（轨道增量）：真实 orbit + event 优于 event-only 和规模匹配伪分组。
- H3（非随机性）：学习策略优于同干预位置、相同幅度及预算的随机扰动。
- H4（泛化）：收益在未见 base/等价组和未见尺度上保持，而非记忆实例或变量编号。
- H5（系统价值）：计入轨道提取、推理、统计、IPC、预处理的完整时间仍改善。
- H6（强基线剩余空间）：现代对称预处理后仍有互补价值，或明确存在另一优势分布。

若 H2 不成立，应改称通用事件启发式；若 H3 不成立，停止复杂模型投入；若 H5 不成立，只能报告机制证据而非加速。

## 5. 分阶段实施

### P0：证据与执行完整性修复

交付：独立划分、回归集标记、异常分类、轨道验证工具及中性路径审计。

1. 冻结代码、solver 源码/二进制哈希、配置、依赖及历史候选；保留失败结果。
2. 将 strictbest 改标 regression；按原始问题与已知公式等价组构建不重叠 train/val/test。子句排序不等同于图同构 canonical labeling，不能声称已解决一般同构去重。
3. 删除长期目标中的实例名例外；保留其作为回归测试。控制组不计对称正例，但真实收益不应受罚。
4. 区分 subprocess 异常、缺失统计、超时、错误结果、正常性能退化；修复 OMP 问题并保存 stderr/returncode。
5. 对生成元检查 signed-literal 置换、取反保持和 CNF 映射；从通过验证的生成元计算子群轨道。不完整但可靠的轨道允许使用。
6. 预处理前后变量映射必须明确。原始 orbit 可作结构特征，不得未经验证作为残余公式剪枝依据。
7. 验证 zero-delta 搜索语义；分别报告 instrumentation 的耗时，不把零动作等价说成零开销。

优先入口：`RLAF/train_rlaf.py`、`RLAF/src/echosat/objective_v2.py`、`RLAF/build_echosat_orbit_certification.py`、`RLAF/src/solving/solver.py` 及对应 tests。

通过门槛：无执行污染；明确数据独立性；可重放配对结果；轨道来源可检查。不通过则不训练。

### P1：强基线与预算上限

比较 plain Glucose、RLAF static、当前 adapter、固定版 CaDiCaL、同版 CaDiCaL + 新版 satsuma。方法归因必须在相同底层 solver 内完成；跨 solver 对比只用于定位竞争力。

记录各阶段 wall time、CPU、decisions、conflicts、propagations、solved 和已知标签匹配。测试分布须包含 SAT/UNSAT、结构家族、弱/强对称和匹配非对称对照，按原始 base 而非置换数计样本量。

先做有限候选动作的离线 oracle 上界（明确它不可部署且受候选集限制）。若 final-search 最大可用收益尚不足以覆盖最低增量成本，就不投资复杂单进程集成。PHP/coloring 若已被 satsuma 轻易消除，降为机制测试而非主加速集。

### P2：核心机制消融

最小矩阵：no-op；orbit 内随机扰动；简单 activity/conflict/low-LBD 规则；event-only；orbit+event；orbit 内 event 对应打乱；规模匹配伪 orbit。

统一干预位置、动作数量、残差幅度、seed 和预算。简单模型先行：线性/MLP，再决定是否加入 GNN embedding。随机组必须匹配幅度和可干预变量，不能用弱随机基线。

通过门槛：真实 orbit+event 在独立 base 上胜过随机和 event-only，并展示关联打乱后下降。报告零结果和反例，不用控制组 mask 产生的“零收益”证明对称性特异性。

### P3：最小同进程、同状态干预

在一个有界检查点采集 event，执行 no-op 或一次有限 score 更新，保留 trail、learned clauses、activity 和已用预算继续 CDCL。先不做多轮在线 RL，也不引入动态符号剪枝。

比较动作时使用同状态复制，或经验证的确定性前缀重放。复制成本与训练成本独立记账。残差可尝试 orbit 内中心化后有界注入；这是候选设计，不预设有效。推理失败走 no-op；已经消耗的探测时间不能撤回，因此不承诺任意实例运行时间不退化。

### P4：简化目标与短训

先做动作偏好/排序学习，再判断 GRPO 是否必要。执行有效性、正确性、收益、尾部风险分开处理。训练奖励使用配对搜索成本的平滑目标，严格双改善可保留为诊断，避免抹掉所有可学习排序。

不再增加命名实例惩罚。评估 variant-level veto 对样本数量的敏感性；保守部署验收不必等同于探索样本的学习资格。使用独立验证集选择 checkpoint，以预先定义的 coverage/尾部限制为约束。

### P5：端到端接受与停走决策

主表：solved、PAR-2、完整 wall-clock、搜索工作、增量开销和每 base 分布。包含 timeout；不只统计共同 solved。重复运行交错执行并控制硬件竞争，按 base/等价组 bootstrap，不把置换当独立样本。

正式接受须同时满足：正确性检查通过；独立测试有效；胜过匹配随机与 event-only；完整成本计入后有收益；现代对称基线后仍有可解释价值。效应阈值、置信水平、seed 数和预算应在测试前登记，不能看完结果再定。

## 6. 后备路线与明确不做的事

若轨道事件路线不通过，优先考虑学习“可认证对称操作的排序和预算”：模型选操作，符号模块检查合法性。它与 satsuma 的排序/迭代方向更直接对应，但需要独立立项，不与当前路线同时大规模开发。

暂不做：完整动态群维护、神经生成未经认证的破缺子句、以 selector 掩盖不稳定策略、无限增加特例、只报 final CPU 或 representation gain 的 speedup claim。

## 7. 下一次实际工作清单

- [ ] 再现 Stage 5 gate 各分项与 OMP 错误来源。
- [ ] 分离 regression 与 disjoint validation，提交重叠审计。
- [ ] 设计实例无关的指标与 checkpoint 选择接口。
- [ ] 在小型生成器上实现并测试生成元检查。
- [ ] 固定 satsuma/CaDiCaL 版本与编译环境，完成小规模强基线试跑。
- [ ] 冻结 P2 消融矩阵和独立测试集，再决定训练规模。

本计划不授予额外长训、数据删除或外部服务部署权限；实施时以用户的具体任务授权为准。
