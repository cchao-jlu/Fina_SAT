

---

# SAT 对称性问题的两种新型解法：S³ 与 SymGNN

> **摘要**：SAT（可满足性问题）中的对称性导致求解器在对称等价的搜索空间中反复探索，造成指数级的效率损失。现有方法（Satsuma、BreakID、CDCLSym）或依赖于预处理阶段的单次图自同构检测（忽略学习子句带来的对称性演化），或需要深度修改求解器内核。本文提出两个全新方法——**S³（Streaming Symmetry Solver，流式符号方法）** 与 **SymGNN（Symmetry-aware Graph Neural Network，神经吸收方法）**——分别从符号推理与神经网络两个截然不同的技术路线解决该问题。S³ 首次将对称性检测从一次性预处理扩展为与 CDCL 求解过程交织进行的流式计算；SymGNN 则在神经 SAT 求解器（基于 ANYCSP-SAT）中通过自监督对比学习使 GNN 隐式吸收对称性并指导搜索决策。两者技术路线正交、优势互补，可协同使用。

---

## 目录

1. [问题背景](#1-问题背景)
2. [S³：流式符号方法](#2-s³流式符号方法)
3. [SymGNN：神经吸收方法](#3-symgnn神经吸收方法)
4. [对比分析](#4-对比分析)
5. [协同框架](#5-协同框架)
6. [实验设计与预期结果](#6-实验设计与预期结果)
7. [总结与展望](#7-总结与展望)

---

## 1. 问题背景

### 1.1 SAT 对称性的定义

在布尔可满足性问题（SAT）中，设 $\mathcal{X}=\{X_1,X_2,\dots,X_n\}$ 为变量集。若置换 $\theta:\mathcal{X}\to\mathcal{X}$ 作用于公式 $\varphi$ 的变量后，得到的 $\theta(\varphi)$ 与 $\varphi$ 句法结构完全相同，则称 $\theta$ 是 $\varphi$ 的**对称性**。所有对称性构成一个**自同构群**。

**示例**：考虑 $\varphi = (a\lor b)\land(a\lor c)\land(b\lor d)$，置换 $\theta=(a\;b)(c\;d)$ 是它的一个对称性——交换 $a\leftrightarrow b$ 且 $c\leftrightarrow d$ 后公式不变。

### 1.2 对称性造成的核心问题

1. **搜索空间膨胀**：每个解及其所有对称等价解共同构成一个**轨道**。CDCL 求解器在同一轨道内反复搜索，做大量无用功。

2. **子句学习的局部性**：CDCL 中的子句学习只剪枝当前搜索路径，但对该路径的对称等价路径无效。求解器在一个对称区域中"学到的教训"无法自动传播到其他对称区域。

3. **实际影响广泛**：鸽巢原理、图着色、拉丁方、Ramsey 图生成、电路验证等领域的问题天然蕴含大量对称性，不处理则求解器几乎无法在合理时间内求解。

### 1.3 现有方法及其局限性

| 方法 | 年份 | 核心思路 | 局限性 |
|------|------|---------|--------|
| **Shatter** | 2002 | 预处理检测对称群 + 添加 lex-leader SBP 子句 | 对称检测一次完成，无法处理学习子句后的新对称性 |
| **BreakID** | 2016 | 检测行可交换性 + 生成二进制 SBP | 同上；局限于行交换结构 |
| **Satsuma** | 2024–26 | 结构驱动的多型对称性检测（行/列/Johnson） | 同上；预处理阶段全图自同构开销大 |
| **CDCLSym** | 2018 | 动态跟踪对称性状态，生成有效 esbp | 依赖预处理检测的固定对称群；需修改求解器 |
| **SMS** | 2019–24 | 将规范形检查嵌入 CDCL 作为额外推导规则 | 需专用传播器；难以与主流求解器集成 |

**所有现有方法的共同盲点**：对称性在预处理阶段被一次性检测，然后被视为固定不变的。然而，已知结果（Mears & Soos, 2022）表明，**学习子句不保持对称性**——新的子句可能破坏旧的对称性，也可能创建新的对称关系。现有方法**完全忽略了后一种可能性**。

---

## 2. S³：流式符号方法

### 2.1 核心洞察

> **对称性不应是公式的静态属性，而是随求解过程动态演化的信息流。**

S³ 将对称性检测从一次性预处理重新定义为与 CDCL 求解**交织进行的流式计算**——每当学习一条新子句，局部更新图结构，运行受限的 Weisfeiler-Lehman（WL）颜色精化，并增量维护演化中的对称群。这个演化群反过来被用于指导决策、重启和内处理。

### 2.2 系统架构

```
                    ┌─────────────────────────────────────────┐
                    │          S³ 流式对称性求解器             │
                    │                                         │
  ┌─────────────────┼─────────────────────────────────────────┼──────────────────┐
  │                 │            CDCL 引擎                    │                  │
  │                 │  ┌──────────────┐  ┌──────────────┐     │                  │
  │                 │  │  决策启发式   │  │  子句学习     │     │                  │
  │                 │  └──────┬───────┘  └──────┬───────┘     │                  │
  │                 │         │                  │            │                  │
  │                 │         ▼                  ▼            │                  │
  │                 │  ┌──────────────────────────────────┐   │                  │
  │  ┌──────────────┼──┤  1️⃣ 增量式WL颜色精化引擎         │   │                  │
  │  │              │  │  (流式对称性检测)                 │   │                  │
  │  │              │  └──────────────────────────────────┘   │                  │
  │  │              │         │                              │                  │
  │  │              │         ▼                              │                  │
  │  │              │  ┌──────────────────────────────────┐   │                  │
  │  │              │  │  2️⃣ 增益感知的对称实例化         │   │                  │
  │  │              │  │  (Gain-Aware Symmetric Clause    │   │                  │
  │  │              │  │   Instantiation, GASCI)          │   │                  │
  │  │              │  └──────────────────────────────────┘   │                  │
  │  │              │         │                              │                  │
  │  │              │         ▼                              │                  │
  │  │              │  ┌──────────────────────────────────┐   │                  │
  │  │              │  │  3️⃣ 对称景观驱动的决策启发式     │   │                  │
  │  │              │  │  (Symmetry Landscape Decision)   │   │                  │
  │  │              │  └──────────────────────────────────┘   │                  │
  │  │              │         │                              │                  │
  │  │              │         ▼                              │                  │
  │  │              │  ┌──────────────────────────────────┐   │                  │
  │  │              │  │  4️⃣ 非对称子公式提取与激进内处理  │   │                  │
  │  │              │  │  (Asymmetric Subformula Extract)  │   │                  │
  │  │              │  └──────────────────────────────────┘   │                  │
  │  │              │         │                              │                  │
  │  │              │         ▼                              │                  │
  │  │              │  ┌──────────────────────────────────┐   │                  │
  │  │              │  │  5️⃣ 轨道熵驱动的自适应重启       │   │                  │
  │  │              │  │  (Orbit Entropy Restart)         │   │                  │
  │  │              │  └──────────────────────────────────┘   │                  │
  │  ▼              ▼                                         ▼                  │
  │  ┌──────────────────────────────────────────────────────────────────┐       │
  │  │              6️⃣  正式证明系统 (sr-Stream 扩展)                  │       │
  │  └──────────────────────────────────────────────────────────────────┘       │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 五大核心技术

#### 技术一：增量式 WL 颜色精化引擎（流式对称性检测）

**问题**：全图自同构每次冲突都重新运行是不可接受的（$O(mn\log n)$）。

**方法**：维护增量式带色二分图 $\mathcal{G}^{(t)}=(V_{\text{lit}}^{(t)}, V_{\text{clause}}^{(t)}, E^{(t)}, \chi^{(t)})$，当新子句 $C$ 被学习时：

1. **局部图更新**（非全图重建）：添加子句节点，连接其文字，用 LBD、长度、活动度设置初始颜色。
2. **局部化颜色精化**：将 WL 迭代限制在二阶邻域 $N^2(C)$（变量集 + 涉及这些变量的子句）内运行，极大降低复杂度。
3. **候选对称对提取**：精化后颜色相同的文字节点标记为候选，用置信度阈值过滤。
4. **增量群维护**：用并查集维护等价类，允许合并与分裂。

```
Algorithm: StreamingWLRefinement
Input: 当前图 G^(t), 新子句 C, 参数 k_max, τ_conf
Output: 更新后的对称候选集 S^(t+1)

1.  G^(t+1) ← AddClauseNode(G^(t), C)
2.  V_affected ← N²(C)          // 二阶邻域
3.  colors ← χ^(t)[V_affected]
4.  for iter = 1 to k_max:
5.      for each v ∈ V_affected:
6.          new_color[v] ← hash(colors[v], 
7.                              sorted{colors[u] | u ∈ N(v) ∩ V_affected})
8.      if stable(colors, new_color): break
9.      colors ← new_color
10. S_new ← {(li, lj) | colors(li)=colors(lj), li,lj ∈ V_lit ∩ V_affected}
11. UpdateEquivalenceClasses(S_new, τ_conf)
12. return GetGenerators()
```

#### 技术二：增益感知的对称实例化（GASCI）

**问题**：传统"对称学习"盲目添加所有 $\sigma(C)$ 导致子句库膨胀。

**方法**：对每个 $\sigma \in \mathcal{G}_{\text{act}}^{(t)}$ 计算预计增益：

$$ \text{gain}(\sigma, C) = \frac{\text{BlockedSpace}(\sigma(C))}{\text{Cost}(\sigma(C))} = \frac{2^{n-\text{span}(\sigma(C))}}{\text{len}(\sigma(C)) \times \text{LBD}(C)} $$

- 仅当 $\text{gain} > \theta^{(t)}$（动态自适应阈值）时，将 $\sigma(C)$ 加入优先队列
- 求解器空闲时按 gain 降序处理队列
- 阈值 $\theta^{(t)}$ 随子句库大小自动调整：库越大越保守

$$ \theta^{(t+1)} = \theta^{(t)} \cdot \left(1 + \beta \cdot \frac{|\text{LearnedDB}^{(t)}| - |\text{LearnedDB}^{(t-1)}|}{|\text{LearnedDB}^{(t-1)}|}\right) $$

#### 技术三：对称景观驱动的决策启发式

**问题**：VSIDS 完全忽略对称性信息。

**方法**：定义对称影响向量 $\mathcal{S}(x_i) = \sum_{\sigma\in\mathcal{G}^{(t)}} [\sigma(x_i)\neq x_i] / |\text{orb}(x_i)|$，融合进决策评分：

$$ \text{score}(x_i) = \text{VSIDS}(x_i) \cdot (1 + \alpha \cdot \mathcal{S}(x_i)) \cdot \text{phase\_weight}(x_i) $$

- 高 $\mathcal{S}$ 值（大轨道）的变量优先被决策
- 在同等 VSIDS 分数下，优先决策轨道的代表元

**定理（对称性感知决策优势）**：在高度对称的搜索空间中，优先决策高 $\mathcal{S}$ 变量可以减少预期搜索树大小：

$$ \mathbb{E}[T] \leq 2^{n} \cdot \prod_{i=1}^{d} \frac{1}{1 + \alpha \cdot \mathcal{S}(x_{(i)})} $$

#### 技术四：非对称子公式提取与激进内处理

**问题**：内处理（BVE、BCE）可能破坏对称性，但完全避免会损失效率。

**方法**：将变量分解为**对称核心** $\mathcal{X}_{\text{sym}}$（非平凡轨道）和**非对称核心** $\mathcal{X}_{\text{asym}}$（平凡轨道）：

- $\mathcal{X}_{\text{asym}}$：应用全部内处理技术（BVE、BCE、self-subsumption）
- $\mathcal{X}_{\text{sym}}$：仅应用对称保持内处理（若消除变量 $x_i$，须同时消除整个轨道）
- **跨核心传播**：从 $\mathcal{X}_{\text{asym}}$ 推导出关于 $x_i \in \mathcal{X}_{\text{sym}}$ 的单位子句时，自动扩展到整个轨道

```
传统内处理（SatELite等）:
  ┌──────────────────────────────┐
  │   对所有变量应用统一的内处理  │ ← 可能破坏对称性
  └──────────────────────────────┘

S³ 的对称分区内处理:
  ┌────────────────────┬─────────┐
  │  对称核心          │ 非对称  │
  │  (轨道>1)          │ 核心    │
  │  保守内处理        │ 激进内处│
  │  对称保持          │ 理全集  │
  └────────────────────┴─────────┘
         ↓                    ↓
   对称性保持              完全剪枝
   部分剪枝
```

#### 技术五：轨道熵驱动的自适应重启

**问题**：Luby 等重启策略与对称性无关。

**方法**：定义**轨道熵** $H_{\text{orbit}}^{(t)} = -\sum_{j=1}^{m} \frac{|O_j|}{n} \log \frac{|O_j|}{n}$，将其融入重启间隔：

$$ \text{restart\_scale}^{(t)} = \frac{1}{1 - \gamma \cdot H_{\text{orbit}}^{(t)} / \log n} $$

- $H_{\text{orbit}} = 0$：所有变量都在大小为1的轨道中（无对称性）
- $H_{\text{orbit}} = \log n$：所有变量在同一个大轨道中（完全对称）
- 高 $H_{\text{orbit}}$（强对称性）→ $\text{restart\_scale} > 1$ → 更频繁重启，避免在对称区域中打转
- 当轨道因变量被赋值而"收缩"时，$H_{\text{orbit}}$ 下降，重启频率自动降低

### 2.4 形式化证明系统（sr-Stream）

S³ 的所有推理步骤可编码为**替换冗余（Substitution Redundancy, sr）证明系统**的扩展。每个动作对应一个 sr 步骤：

| S³ 动作 | sr 编码 | 见证 $\omega$ |
|---------|---------|---------------|
| GASCI 实例化 | $\text{sr-add}(\sigma(C))$ | $\omega(x) = \sigma^{-1}(x)$ |
| 轨道传播 | $\text{sr-add}(\neg x_j)$ | 轨道的置换 |
| 对称 SBP 注入 | $\text{sr-add}(\text{lex-leader})$ | 标准 lex-leader 见证 |

### 2.5 完整算法

```
Algorithm: S³ Main Loop
Input: CNF F
Output: SAT/UNSAT + sr 证明

1.  G, G_sym ← BuildAndDetect(F)       // 初始图 + 初始对称群
2.  LearnedDB ← ∅; Queue ← PriorityQueue()
3.  while True:
4.      // 决策阶段
5.      score ← ComputeScore(VSIDS, S_landscape, G_sym)
6.      dec_var ← SelectVariable(score)
7.      trail ← Assign(dec_var)
8.    
9.      // 传播阶段
10.     result ← BCP(trail, F ∪ LearnedDB)
11.   
12.     if result == CONFLICT:
13.         C ← AnalyzeConflict(trail)
14.         LearnedDB ← LearnClause(C)
15.       
16.         // --- S³ 核心：增量对称性更新 ---
17.         G_sym, S_landscape ← StreamingWLRefinement(G, G_sym, C)
18.       
19.         // --- GASCI ---
20.         for σ ∈ ActiveSymmetries(G_sym, C):
21.             gain ← ComputeGain(σ, C, LearnedDB, trail)
22.             if gain > θ_dynamic:
23.                 Queue.push((σ(C), gain))
24.       
25.         // --- 轨道熵重启 ---
26.         H_orbit ← ComputeOrbitEntropy(G_sym)
27.         restart_scale ← 1 / (1 - γ · H_orbit / log n)
28.         if ShouldRestart(Luby, restart_scale):
29.             trail ← Restart()
30.   
31.     if result == SAT: return SAT + ExtractModel(trail)
32.     if AllVariablesAssigned(trail): return UNSAT
33.   
34.     // --- 后台：处理GASCI队列 ---
35.     if IdleCycle():
36.         while (σC, gain) ← Queue.pop() and gain > θ_current:
37.             LearnedDB ← LearnedDB ∪ {σC}
38.             sr_proof ← sr_proof ∪ {sr-add(σC, ω)}
39.   
40.     // --- 非对称核心内处理（每5000冲突） ---
41.     if conflicts % 5000 == 0:
42.         X_asym, X_sym ← SplitByOrbit(G_sym)
43.         F ← AggressiveInprocessing(F, X_asym)
44.         F ← SymmetryPreservingInprocessing(F, X_sym, G_sym)
```

### 2.6 S³ 的复杂度分析

| 操作 | 最坏情况复杂度 | 实际预期复杂度 |
|------|---------------|---------------|
| 初始图构建 | $O(m \log n)$ | $O(m)$ |
| 初始对称检测（一次） | $O(n^3 \log n)$（图自同构） | $O(n^2)$ |
| **增量WL精化（每次冲突）** | $O(k \cdot d^2 \log d)$ | **$O(k \cdot d)$** |
| GASCI（每条子句） | $O(g \cdot n)$ | $O(g_{\text{act}} \cdot \text{len}(C))$ |
| 决策启发式更新 | $O(n)$ | $O(\log n)$（位图优化） |
| 轨道熵计算 | $O(n)$ | $O(n)$（增量维护） |
| ASE分区 | $O(n)$ | $O(n)$（复用轨道数据） |

其中 $n$ = 变量数，$m$ = 子句数，$d = |N^2(C)|$（影响域大小），$k$ = WL迭代次数（通常≤5），$g$ = 对称群大小。**关键优势**：$d \ll n$，增量操作不随问题规模二次增长。

---

## 3. SymGNN：神经吸收方法

### 3.1 核心洞察

> **GNN 的隐表示天然具有排列等变性——为什么不直接训练它学习对称性，并用学习到的表示引导搜索？**

SymGNN 建立在 [ANYCSP-SAT](https://github.com/cchao-jlu/ANYCSP-SAT) 项目之上。ANYCSP-SAT 使用 GNN + GRU 迭代精化 CSP 实例的值-约束二分图，已在无显式对称性处理的情况下取得不错效果。SymGNN 在此基础上增加**三层对称性处理模块**，使 GNN 端到端地学习"哪些变量对称、如何利用对称性、如何避免对称冗余"——**不需要任何外部图自同构工具**。

### 3.2 系统架构

```
                    ┌─────────────────────────────────────────┐
                    │        SymGNN 三层架构                    │
                    │                                         │
  ┌─────────────────┼─────────────────────────────────────────┼──────────────────┐
  │                 │                                         │                  │
  │   Layer 1:      │   Layer 2:         Layer 3:             │                  │
  │  隐式对称表示    │  对称感知决策      对称引导搜索            │                  │
  │                 │                                         │                  │
  │  ┌───────────┐  │  ┌───────────┐   ┌───────────┐         │                  │
  │  │ 对称正则化  │  │ 对称对比学习 │   │ 轨道嵌入   │         │                  │
  │  │ 训练       │  │ 决策        │   │ 引导重启   │         │                  │
  │  └───────────┘  │  └───────────┘   └───────────┘         │                  │
  │                 │                                         │                  │
  │  ┌────────────────────────────────────────────────────┐   │                  │
  │  │  基底: ANYCSP GNN (值→约束→值→变量消息传递 + GRU)  │   │                  │
  │  └────────────────────────────────────────────────────┘   │                  │
  └─────────────────────────────────────────────────────────┴──────────────────┘
```

### 3.3 三大核心模块

#### Layer 1：隐式对称表示

在 ANYCSP-SAT 的 REINFORCE 损失上增加三个正则化项：

**a) 自对称正则化**

$$ \mathcal{L}_{\text{self-sym}} = \mathbb{E}_{x_i, x_j} \big[ w_{ij} \cdot \|h_i - h_j\|_2^2 \big] $$

其中 $w_{ij} = \sigma(\text{MLP}([h_i; h_j; \|h_i-h_j\|_2]))$ 是 GNN 通过注意力机制自学习出的"软对称权重"，$w_{ij} \in [0,1]$ 表示 GNN 认为变量 $i$ 和 $j$ 对称的程度。

**b) 对比对称学习**

受 SimCLR 启发：

$$ \mathcal{L}_{\text{contrast}} = -\mathbb{E}_{x_i} \Big[ \log \frac{\sum_{x_j\in\text{Pos}(x_i)} \exp(\text{sim}(h_i, h_j)/\tau)}{\sum_{x_k\in\mathcal{X}\setminus\{x_i\}} \exp(\text{sim}(h_i, h_k)/\tau)} \Big] $$

正样本对 $\text{Pos}(x_i)$ 从搜索轨迹中在线构造：若交换变量 $i,j$ 后模型的条件收益不变，则 $(i,j)$ 为正样本。

**c) 轨道一致性正则化**

$$ \mathcal{L}_{\text{orbit}} = \sum_i \|h_i - \text{stopgrad}(\text{Pool}_{\text{orbit}}(i))\|_2^2 $$

其中 $\text{Pool}_{\text{orbit}}(i) = \sum_j \tilde{w}_{ij} h_j / \sum_j \tilde{w}_{ij}$ 是变量 $i$ 所在"软轨道"的加权平均表示。

**总训练损失**：

$$ \mathcal{L}_{\text{total}} = \mathcal{L}_{\text{REINFORCE}} + \lambda_1 \mathcal{L}_{\text{self-sym}} + \lambda_2 \mathcal{L}_{\text{contrast}} + \lambda_3 \mathcal{L}_{\text{orbit}} $$

#### Layer 2：对称感知决策

**问题**：ANYCSP-SAT 的 local sampling 随机选择变量修改，未利用对称性。

**方法**：

**a) 对称性熵**：对变量 $x_i$ 定义：

$$ S_{\text{sym}}(x_i) = -\sum_j \frac{\tilde{w}_{ij}}{Z_i} \log \frac{\tilde{w}_{ij}}{Z_i} + \epsilon $$

- 高 $S_{\text{sym}}$：变量在轨道中的角色不明确（可能是高度对称的）
- 低 $S_{\text{sym}}$：变量有独特的角色（非对称或已确定）

**b) 变量选择概率**：

$$ P(x_i) = \text{softmax}_i\big( \alpha \cdot (1 - S_{\text{sym}}(x_i)) + \beta \cdot \text{VSIDS}(x_i) + \gamma \cdot \text{novelty}(x_i) \big) $$

偏向选择**角色明确**（低 $S_{\text{sym}}$）的变量——修改它们对搜索的影响更大。

**c) 对称批量赋值**：改变变量 $x_i$ 时，以概率 $w_{ij}$ 同步改变其软对称伙伴 $x_j$，等价于在每一步执行一次群作用，强制跳出当前轨道。

#### Layer 3：对称引导搜索

**a) 轨道嵌入引导重启**

计算全局对称嵌入 $g_{\text{sym}} = \text{Readout}(\{h_i\})$，维护历史缓冲区 $\mathcal{H} = \{g_{\text{sym}}^{(t-K)}, ..., g_{\text{sym}}^{(t)}\}$。若当前嵌入与历史嵌入高度相似，表明搜索在原地踏步，触发重启：

$$ \text{restart if: } \max_{k} \cos(g_{\text{sym}}^{(t)}, g_{\text{sym}}^{(t-k)}) > \theta_{\text{sim}} $$

**b) 对称景观映射**

为每个赋值 $\alpha$ 计算**对称指纹**：

$$ \text{fingerprint}(\alpha) = \text{hash}\Big( \sum_{i: \alpha(x_i)=v} h_i \Big) $$

若指纹已在缓存中，说明当前赋值属于已探索轨道的对称等价类，强制施加随机扰动。

**c) 对称驱动波束搜索**

维护多个搜索轨迹（波束），波束间距离基于对称感知度量：

$$ d_{\text{sym}}(\alpha^{(a)}, \alpha^{(b)}) = \min_{\sigma \in \hat{G}} \text{Hamming}(\alpha^{(a)}, \sigma(\alpha^{(b)})) $$

其中 $\hat{G}$ 由软对称权重隐式定义。过近的波束（同一轨道内）被丢弃。

### 3.4 训练策略

#### 两阶段训练

| 阶段 | 数据 | 损失 | 目标 |
|------|------|------|------|
| **一：基础训练** | 随机 3-SAT / k-coloring / MaxCut (n=20~50) | $\mathcal{L}_{\text{REINFORCE}}$ | 学会基本的赋值搜索 |
| **二：对称感知微调** | 同上 + 高对称性实例（鸽巢原理、Ramsey、拉丁方） | $\mathcal{L}_{\text{total}}$ | 学会检测和利用对称性 |

#### 课程学习（Curriculum Learning）

```
阶段 1: n=20, 弱对称性实例 —— 学会基本搜索
阶段 2: n=50, 中等对称性 —— 开始学习对称模式
阶段 3: n=100+, 强对称性（鸽巢原理等）—— 掌握高阶对称性
```

#### 教师-学生训练（可选）

用 S³ 或 Satsuma 为训练实例自动标注对称性（软标签），作为额外监督信号辅助 SymGNN 学习：

$$ \mathcal{L}_{\text{distill}} = \text{KL}\big( \text{softmax}(W_{\text{sym}}^{\text{GNN}}) \;\|\; \text{softmax}(W_{\text{sym}}^{\text{teacher}}) \big) $$

### 3.5 推理算法

```
Algorithm: SymGNN Inference
Input: CSP实例 F, 训练好的SymGNN模型 M, 最大步数 T_max
Output: 赋值 α (minimizing unsat count)

1.  α ← RandomInitialAssignment()
2.  h ← M.InitHidden(α)
3.  explored_fingerprints ← ∅
4.
5.  for t = 1 to T_max:
6:      // GNN前向传播
7.      h ← M.MessagePassing(h, α)
8.      logits ← M.Policy(h)
9.    
10.     // 计算对称注意力（每K步）
11.     if t % K == 0:
12.         W_sym ← ComputeSymmetryAttention(h)
13.   
14.     // Layer 2: 选择要改变的变量
15.     x_i ← SelectVariable(logits, W_sym, history)
16.   
17.     // Layer 2: 选择新值（受对称性影响）
18.     v_new ← SelectValue(x_i, logits, W_sym)
19.     α ← UpdateAssignment(α, x_i, v_new)
20.   
21.     // Layer 3: 对称引导
22.     fp ← ComputeFingerprint(α, h, W_sym)
23.     if fp in explored_fingerprints:
24.         α ← RandomPerturbation(α)     // 跳出轨道
25.     else:
26.         explored_fingerprints ← explored_fingerprints ∪ {fp}
27.   
28.     // 重启检查
29.     if NeedRestart(h, trajectory_buffer, W_sym):
30.         α ← NewBeam(W_sym)          // 切换到波束中的另一个轨迹
31.   
32.     if NumberOfUnsatisfied(α) == 0:
33.         return α                      // 找到解
34.   
35. return BestAssignmentFound()
```

---

## 4. 对比分析

### 4.1 方法论对比

| 维度 | **S³（流式符号方法）** | **SymGNN（神经吸收方法）** |
|------|----------------------|--------------------------|
| **方法论** | 符号推理 + 增量式 WL 精化 | 神经网络 + 对比学习 |
| **对称性来源** | 图自同构理论（WL 颜色精化） | GNN 隐表示的自监督学习 |
| **外部依赖** | 需 Saucy/Bliss 做初始检测 | **零外部依赖** |
| **可证明性** | ✅ 有 sr 形式化证明 | ❌ 无形式化保证（黑盒） |
| **泛化能力** | 每个实例独立计算 | **可跨实例/跨问题泛化**（一次训练） |
| **计算模式** | 改造传统 CDCL 求解器 | 端到端 GNN 迭代精化 |
| **与主流求解器集成** | ✅ 可作为预处理/内处理插件 | ❌ 需要替换整个求解范式 |
| **推理开销** | 每次冲突 $O(k\cdot d^2\log d)$ | 每次迭代 $O(\|E\|\cdot D)$（GNN 前向） |
| **对学习子句的反应** | ✅ 利用局部图结构变化 | ✅ 利用隐空间中的语义变化 |

### 4.2 检测能力对比

| 对称性类型 | Satsuma | S³ | SymGNN |
|-----------|---------|----|--------|
| 行交换 | ✅ | ✅ | ✅（自学习） |
| 行列交换 | ✅ | ✅ | ✅（自学习） |
| Johnson 对称性 | ✅ | ✅ | ?（需验证） |
| 混合结构 | ✅ | ✅ | ✅（自学习） |
| **从学习子句中产生的新对称性** | ❌ | **✅（核心创新）** | **✅（隐空间反映）** |
| **零样本泛化到新问题族** | ❌ | ❌ | **✅（一次训练后）** |

### 4.3 复杂度对比

| 操作 | S³ | SymGNN |
|------|----|--------|
| 初始检测 | $O(n^3\log n)$（一次） | $O(\text{训练})$（一次） |
| 每次冲突增量更新 | $O(k\cdot \|N^2(C)\|\log\|N^2(C)\|)$ | 已包含在 GNN 前向中 |
| 推理时单步 | 无额外开销（CDCL 标准步） | $O(\|E\|\cdot D)$ |
| **随问题规模增长** | ✅ 良好（局部化操作，$\|N^2(C)\| \ll n$） | ⚠️ 需注意 $\|E\|$ 增长 |

### 4.4 优缺点汇总

#### S³

| 优点 | 缺点 |
|------|------|
| ✅ 有形式化证明（sr 证明系统） | ❌ 需要 Saucy/Bliss 做初始检测 |
| ✅ 与主流 CDCL 求解器兼容（可作为插件） | ❌ 每实例独立检测，无跨实例泛化 |
| ✅ 增量操作局部化，复杂度可控 | ❌ 对非结构化的"软对称性"可能不敏感 |
| ✅ 能检测学习子句带来的新对称性 | ❌ 符号 WL 精化是近似方法（假阳性） |

#### SymGNN

| 优点 | 缺点 |
|------|------|
| ✅ **零外部依赖**（不依赖图自同构工具） | ❌ 无形式化证明保证 |
| ✅ **端到端可训练**（检测 + 利用一体化） | ❌ 训练成本高（需大量实例） |
| ✅ **可跨问题泛化**（从3-SAT到MaxCut） | ❌ 推理不可解释（黑盒） |
| ✅ 隐式处理"软对称性"（近似对称） | ❌ 对极端大规模图的扩展性待验证 |
| ✅ 能学到"隐藏对称模式" | ❌ 需要改造整个求解范式 |

---

## 5. 协同框架

S³ 与 SymGNN 代表两种**正交互补**的技术路线。它们不仅不冲突，反而可以协同工作——S³ 的符号检测为 SymGNN 提供高质量的监督信号，而 SymGNN 的快速预测为 S³ 提供低成本的对称候选。

### 5.1 双向知识蒸馏框架

```
                      ┌──────────────────────┐
                      │  教师（S³ 符号引擎）  │
                      │  ┌────────────────┐  │
                      │  │ 增量 WL 精化    │  │
                      │  │ 生成精确对称群  │  │
                      │  └──────┬─────────┘  │
                      └─────────┼────────────┘
                                │ 软标签 (W_sym^teacher)
                                ▼
                      ┌──────────────────────┐
                      │  学生（SymGNN 神经网）│
                      │  ┌────────────────┐  │
                      │  │ 对比学习        │  │
                      │  │ 蒸馏损失:       │  │
                      │  │ KL(W^GNN||W^T) │  │
                      │  └──────┬─────────┘  │
                      └─────────┼────────────┘
                                │ 快速预测 (W_sym^student)
                                ▼
                      ┌──────────────────────┐
                      │  辅助 S³ 加速        │
                      │  • SymGNN 指向高     │
                      │    可能对称区域      │
                      │  • S³ 验证/修正      │
                      └──────────────────────┘
```

#### 方向一：S³ → SymGNN（符号教师蒸馏）

- S³ 的增量 WL 精化生成高精度对称权重矩阵 $W_{\text{sym}}^{\text{teacher}}$
- SymGNN 在训练时增加蒸馏损失 $\mathcal{L}_{\text{distill}} = \text{KL}(W^{\text{GNN}} \| W^{\text{teacher}})$
- 结果：SymGNN 学到符号方法的高精度对称性检测能力

#### 方向二：SymGNN → S³（神经加速器）

- SymGNN 快速预测对称候选（仅一次 GNN 前向，$\approx$ 毫秒级）
- 指向最有可能存在对称性的变量子集
- S³ 在其指向的子集上优先运行局部 WL 精化（"热启动"）
- 结果：S³ 的增量更新速度提升（减少不必要的 WL 迭代）

### 5.2 混合推理策略

```
Algorithm: Hybrid Inference (S³ + SymGNN)
Input: CNF F, 训练好的 SymGNN M, 配置阈值 θ_hybrid
Output: SAT/UNSAT + sr 证明

1.  // 初始检测（S³ 主导）
2.  G_sym_initial ← Satsuma_or_S3_initial(F)
3.  h_init ← SymGNN_InitEncoding(F)
4.
5.  while True:
6.      // 决策阶段（混合）
7.      score_s3 ← S3_DecisionScore(G_sym_current)
8.      score_symgnn ← SymGNN_DecisionScore(h_current, trail)
9.      score ← Combine(score_s3, score_symgnn, α_hybrid)
10.     dec_var ← SelectVariable(score)
11.     ...
12.   
13.     if CONFLICT:
14.         C ← LearnClause()
15.       
16.         // 并行对称性检测
17.         promise_s3 ← S3_StreamingWL(C)           // 符号增量检测
18.         promise_symgnn ← SymGNN_UpdateHidden(C)  // GNN 隐状态更新 + 对称预测
19.       
20.         // 合并信息
21.         G_sym_new ← MergeSymmetryInfo(
22.             await promise_s3,     // 精确但稍慢
23.             await promise_symgnn  // 快速但近似
24.         )
25.       
26.         // GASCI（基于合并后的更精确对称群）
27.         GASCI_Add(C, G_sym_new)
```

### 5.3 预期协同收益

| 指标 | S³ 单独 | SymGNN 单独 | S³ + SymGNN 协同 |
|------|---------|-------------|-----------------|
| 对称检测精度 | ✅ 高（符号方法） | ⚠️ 中等（依赖训练） | ✅ 更高（两者校验） |
| 对称检测速度 | 增量但仍有计算 | ✅ 极快（GNN 前向） | ✅ 快（先 GNN 预测，再 S³ 验证） |
| 泛化能力 | ❌ 每实例独立 | ✅ 跨实例泛化 | ✅ 在泛化时保持精度 |
| 形式化证明 | ✅ 有 | ❌ 无 | ✅ 由 S³ 提供证明 |
| 对新问题的适应性 | 慢但可靠 | 快但可能不准确 | ✅ 快且可靠 |

---

## 6. 实验设计与预期结果

### 6.1 基准测试集

| 类别 | 实例族 | 对称性类型 | 规模范围 |
|------|--------|-----------|---------|
| 经典对称 | 鸽巢原理（PHP） | 全对称 | n=5..50 |
| 组合 | Ramsey 图生成 | Johnson 对称 | n=8..25 |
| 组合 | 拉丁方完成 | 行列交换 | n=5..12 |
| 图论 | k-coloring（随机图） | 行交换 | n=50..200 |
| 规划 | 模块化规划问题 | 混合 | 变量 100..2000 |
| 验证 | 电路等价检查 | 部分对称 | 变量 500..10000 |
| **新类别** | 对称性演化实例 | 学习子句**产生**新对称 | 变量 50..500 |

### 6.2 实验设计

#### 实验 A：检测能力验证

- **问题**：S³ / SymGNN 能否正确检测已知对称性？
- **对比基线**：Satsuma、BreakID（作为 ground truth）
- **指标**：精确率、召回率、F1 得分
- **预期**：S³ 匹配或接近 Satsuma 的精度；SymGNN 在训练过的问题族上匹配，在未见问题族上保持良好

#### 实验 B：求解效率

- **问题**：对称性驱动的求解加速效果如何？
- **对比基线**：Glucose / Kissat（无对称处理）、Glucose + Satsuma、Glucose + BreakID
- **指标**：求解时间、冲突数、决策数
- **预期**：
  - S³：在对称性演化实例上优于所有基线（因为只有 S³ 能处理新对称性）
  - SymGNN：在大规模同类实例上表现优异（泛化优势）

#### 实验 C：协同实验

- **问题**：S³ + SymGNN 协同是否优于两者单独使用？
- **指标**：求解时间、证明生成时间、鲁棒性
- **预期**：协同达到最佳的综合性能

### 6.3 消融研究

| 模型配置 | 目的 |
|---------|------|
| S³ 无 GASCI | 验证 GASCI 对效率的贡献 |
| S³ 无轨道熵重启 | 验证自适应重启的作用 |
| S³ 无 ASE | 验证对称感知内处理的作用 |
| SymGNN 无 Layer 1 | 验证隐式对称表示的重要性 |
| SymGNN 无 Layer 2 | 验证对称感知决策的重要性 |
| SymGNN 无 Layer 3 | 验证对称引导搜索的重要性 |

### 6.4 预期实验结果

```
求解时间对比（理想化示意图）:

经典对称实例（PHP, n=30）:
  Glucose (无处理) :  ████████████████████████████ timeout (3600s)
  +Satsuma         :  ████████████ 245.3s
  +S³              :  ██████████ 198.7s     (+19% vs Satsuma)
  SymGNN           :  ████████ 153.2s       (+38% vs Satsuma)
  S³ + SymGNN      :  ██████ 112.5s         (+54% vs Satsuma)

对称性演化实例（诱导新对称）:
  Glucose (无处理) :  ████████████████████████████ timeout
  +Satsuma         :  ████████████████████████████ timeout (无法处理)
  +S³              :  ██████████████ 412.8s    (唯一可解的方法)
  SymGNN           :  █████████████ 378.5s     (GNN 隐式捕捉到变化)
  S³ + SymGNN      :  █████████ 256.1s         (协同最佳)

跨问题泛化（3-SAT → MaxCut）:
  SymGNN（零样本） :  ████████████ 189.3s      (无需重新训练)
  S³（需重新检测）:  ████████████████ 267.4s
```

---

## 7. 总结与展望

### 7.1 与现有方法的对比总览

| 维度 | Satsuma (2024) | BreakID (2016) | CDCLSym (2018) | SMS (2021-24) | **S³** | **SymGNN** |
|------|----------------|----------------|----------------|---------------|--------|------------|
| 对称检测次数 | **1**次 | **1**次 | **1**次 | **1**次 | **持续进行** | **持续学习** |
| 检测时机 | 预处理 | 预处理 | 预处理 | 预处理 | **全求解过程** | **全求解过程** |
| 从学习子句中识别新对称性 | ❌ | ❌ | ❌ | ❌ | **✅** | **✅** |
| 对称性驱动的决策 | ❌ | ❌ | ❌ | ❌ | **✅ 对称景观** | **✅ 对称对比** |
| 对称性自适应重启 | ❌ | ❌ | ❌ | ❌ | **✅ 轨道熵** | **✅ 嵌入相似度** |
| 对称感知内处理 | ❌ | ❌ | ❌ | ❌ | **✅ 分区ASE** | ❌ |
| 实例化代价控制 | 无（一次性） | 无（一次性） | 弱（esbp） | 强（传播器） | **✅ GASCI** | **✅ 软权重** |
| 形式化证明 | ✅ (sr) | ❌ | ❌ | ❌ | **✅ (sr-Stream)** | ❌ |
| 零外部依赖 | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |
| 跨实例泛化 | ❌ | ❌ | ❌ | ❌ | ❌ | **✅** |

### 7.2 核心贡献

| 贡献 | 描述 |
|------|------|
| **S³ 流式符号方法** | 首次将对称性检测从一次性预处理扩展为与 CDCL 交织的流式计算；提出增益感知实例化、对称景观决策、轨道熵重启等五项原创技术 |
| **SymGNN 神经吸收方法** | 首次在神经 SAT 求解器中引入端到端对称性学习；通过对比学习和自监督方法使 GNN 隐式吸收对称性并引导搜索 |
| **S³ + SymGNN 协同框架** | 提出双向知识蒸馏 + 混合推理策略，结合符号方法的可证明性与神经网络的速度和泛化能力 |
| **形式化证明系统** | 为 S³ 设计了 sr-Stream 扩展，确保所有对称推理可被形式化验证 |

### 7.3 预期挑战与缓解策略

#### S³ 的挑战

| 挑战 | 缓解策略 |
|------|---------|
| WL 精化可能将非对称变量误判为对称（false positive） | 置信度阈值 $\tau_{\text{conf}}$ 可调；用后续冲突验证候选对称性 |
| 频繁的增量更新可能累积误差 | 定期（每10万冲突）触发一次完全重检测以校正 |
| GASCI 的增益估计可能不准确 | 采用**后验修正**：若添加的子句长期未被使用，降低其初始增益估计 |
| sr 证明可能因增量对称性更新而复杂化 | 将对称群更新本身编码为 sr 推导（每个新对称性对应一个 sr 步骤） |
| 与现有 CDCL 启发式的交互不可预测 | 保持 S³ 模块为可插拔组件，提供**回退模式**（fallback to Satsuma） |

#### SymGNN 的挑战

| 挑战 | 缓解策略 |
|------|---------|
| 对称性学习缺乏理论保证 | 符号方法（Satsuma/S³）有理论保证，而 SymGNN 是启发式的；可用 S³ 作为"教师"蒸馏知识 |
| 训练数据构造困难 | 使用有明确对称性的合成实例族；同时利用 S³ 自动标注训练实例的对称性（作为弱监督信号） |
| GNN 可能无法捕捉高阶对称性 | 增加 Transformer-style 的全局注意力层，增强捕获长程依赖的能力 |
| 推理时的不稳定性 | 采用波束搜索 + 集成方法（多个 GNN 副本）增加鲁棒性 |

### 7.4 未来方向

1. **SMT 扩展**：将 S³ 的流式对称性检测推广到 SMT（Satisfiability Modulo Theories）领域，处理算术、位向量等理论中的对称性

2. **并行 SAT 中的对称感知分区**：利用对称群信息将搜索空间合理分区，分配到不同线程/节点，避免并行求解中的对称冗余

3. **GNN 架构创新**：探索 Transformer-style 的全局注意力层增强 SymGNN 捕获高阶对称性的能力；研究等变图网络（Equivariant GNN）以更好地编码对称性

4. **理论保证**：研究 SymGNN 中隐式对称表示的理论性质——对称性学习损失与真实对称群之间的关系

5. **实际应用**：将 S³ / SymGNN 集成到主流 SAT 求解器（Kissat、CaDiCaL）中，在实际工业验证场景中测试

6. **自动化方法选择**：开发一个元学习器，根据问题特征自动判断使用 S³、SymGNN 还是两者的混合配置

### 7.5 结语

| | **S³** | **SymGNN** |
|---|-----|--------|
| **一句话总结** | 让对称性检测成为与搜索交织的流水线 | 让 GNN 在隐空间中学会发现和分析对称性 |
| **继承自** | Satsuma、CDCLSym 的符号传统 | ANYCSP-SAT 的神经 SAT 求解传统 |
| **打破的认知** | "对称性是公式的静态属性，一次检测就够了" | "GNN 只能隐式容忍对称性，不能显式学习它" |
| **最大优势** | 形式化可证明、与主流求解器兼容 | 端到端学习、跨问题泛化、零外部依赖 |
| **最大弱点** | 每实例独立计算，无泛化 | 无形式化保证，训练成本高 |

两种方法的**协同**可能是最终的答案——S³ 提供可靠性和可证明性，SymGNN 提供速度和泛化能力，两者在双向蒸馏框架中相互增强。

---

> **参考文献**
>
> 1. Aloul et al., "Shatter: Solving SAT with Symmetry Breaking", 2002
> 2. Devriendt et al., "BreakID", 2016
> 3. Mears et al., "CDCLSym", TACAS 2018
> 4. Anders et al., "Satsuma", JAIR 2026 / SAT 2024
> 5. Kirk et al., "SAT Modulo Symmetries", 2021–2024
> 6. Mears & Soos, "SAT Preprocessors and Symmetry", 2022
> 7. C. Chao et al., "ANYCSP-SAT", GitHub, 2024
> 8. Selsam et al., "NeuroSAT", 2019
> 9. Heule et al., "sr proof system for symmetry reasoning", 2024

---

*本文档于 2026 年 6 月生成，基于对现有文献的深入调研和对 ANYCSP-SAT 项目的分析。S³ 和 SymGNN 均为本文首次提出的原创方法。*