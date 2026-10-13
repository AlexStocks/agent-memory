# SE-GoS：面向大规模技能库的自演化技能图（Self-Evolving Graph-of-Skills for Skill Library at Scale）

> **原文标题**：SE-GoS: Self-Evolving Graph-of-Skills for Skill Library at Scale
> **作者**：Dawei Fu†¹², Cheng Jiang³, Sitian Qian⁴, Huainan Wang¹, Zhongkai Hao⁵
> **机构**：¹腾讯（Tencent）、²北京大学（Peking University）、³爱丁堡大学（University of Edinburgh）、⁴西北大学（Northwestern University）、⁵清华大学（Tsinghua University）
> **arXiv**：arXiv:2609.08228v2 [cs.AI]，2026 年 10 月 1 日（正文标注日期 2026 年 10 月 2 日）
> **数据**：huggingface.co/datasets/PKUfudawei/SEGoS-data
> **代码**：github.com/PKUfudawei/SEGoS
> **通讯作者**：Dawei Fu（fudw@pku.edu.cn）
> **说明**：† 该工作完成于作者在腾讯实习期间。

> **翻译说明**：本文按原文结构完整翻译，保留全部公式编号与表格数字。关键术语处理如下：`skill` 译为「技能」（保留 SKILL.md 等文件名原文）；`skill library` 译为「技能库」；`graph-of-skills (GoS)` 保留缩写 GoS；`retrieval substrate` 译为「检索基底」；`bundle` 译为「执行包」；`harness` 保留英文（与系列其他译文一致，指承载 agent 运行的外层工程设施）；`trace` 译为「轨迹」；`avoid edge` 译为「回避边」；`attenuation` 译为「衰减」；`reinforcement` 译为「强化」；`node description` 译为「节点描述」；`lexical seeding` 译为「词法播种」；`PPR` 保留（Personalized PageRank，个性化 PageRank）；`held-out` 译为「留出」。原文 `Table 1` 中的勾选矩阵以表格重绘。

---

## 摘要

LLM agent 会使用大型的可复用技能库。当技能条目达到数千条时，检索成为瓶颈。Graph-of-Skills（GoS）从一张带类型的技能图中检索出依赖感知的执行包，SkillDAG 则表明这样一张图可以在线累积出由执行支撑的结构。但二者都没有追问：执行轨迹能否被蒸馏成一张**更好的、且能泛化到未见任务**的检索图。

我们提出 **Self-Evolving Graph-of-Skills（SE-GoS）**，它把检索图当作**索引**而不是学到的表示：图由执行轨迹维护，而检索流水线、技能库与模型全部保持不变。SE-GoS 施加三类更新：

1. **拓扑（topology）**：从执行证据中归纳出关系，并且只有在**反复成功共用**之后才撤回一条 avoid 边；
2. **边权（edge-weight）**：对缺乏支撑的语义边做软衰减，并对**指向被实际使用技能**的入边做强化；
3. **节点描述（node-description）**：更新那些排名过低、但被检索所面对的描述字段——这些描述存放在图节点上。

在 SkillsBench 上，单轮演化把平均奖励从 52.4% 提升到 59.4%，超过了加载全库、向量检索、静态 GoS 与 SkillDAG；这一排序在三个骨干模型上重复出现。在演化后的图上检索所花费的输入 token 约为加载全库的三分之二。重复该轮次没有帮助。同一张图把一个它从未见过的留出切分从 52.9% 提升到 58.3%，因此它累积的是可迁移的结构，而不是记住了轨迹。

结论：技能图可以仅凭执行经验被改进——不需要模型训练、不需要改动检索算法、不需要修改技能内容，也不需要让某个模型去判定哪些技能彼此相关。

**图 1**：SE-GoS 概览与 SkillsBench 结果。
- (a) 离线、由轨迹驱动的对图拓扑、边权与节点描述的更新；虚线箭头表示可选的多轮演化。
- (b) deepseek-v4-flash-0731 在 SkillsBench 上的奖励（%）：柱状对比各方法；虚线表示第 0 轮的 GoS 与第 1—3 轮的 SE-GoS。

---

## 1 引言

大语言模型（LLM）agent 通过调用外部工具与可复用技能来解决技术任务（Schick et al., 2023; Mialon et al., 2023）。随着技能仓库从数十条增长到数千条（Patil et al., 2023; Li et al., 2023; Xu et al., 2023; Qin et al., 2024），瓶颈不再是「要不要用技能」，而是「该加载哪个小子集」（Shi et al., 2025）。

把整库塞进上下文不可扩展。token 成本线性增长，而模型在过载的上下文中会漏掉它实际需要的技能（Agent Skills, 2026; Liu et al., 2024a）。基于向量的检索（Lewis et al., 2020; Karpukhin et al., 2020）挑出语义相似的技能，却忽略它们的功能性前置条件：排名最高的匹配往往是一个高层求解器，而它底层的解析器或环境准备工具在语义上很弱，却是执行所必需的。我们把这一现象称为**前置条件鸿沟（prerequisite gap）**。

Graph-of-Skills（GoS）（Liu et al., 2026）用一张**带类型的有向技能图**来应对这一问题：图由混合的语义—词法信号播种，并用反向感知的 Personalized PageRank（PPR）（Page et al., 1999; Haveliwala, 2002; Yang et al., 2024）进行探索，返回一个有界、有预算的执行包。在 GPT-5.2 Codex 下的 1,000 技能 SkillsBench 上，GoS 相对全库加载取得约 **25.6% 的峰值奖励增益**，同时把 token 成本削减约 **56.7%**（Liu et al., 2026）。

**但 GoS 的图是静态的。** 它被构建一次，之后永不从执行反馈中更新。当一条归纳出的依赖是错的、一条有用关系缺失、或者某个描述系统性地无法匹配到需要它的查询时，这个仓库无法自我纠正。

**而纠正所需的信号早就在那里。** 每一次尝试都记录了：哪些技能被检索到、哪些被实际使用、以及任务是否成功。

我们提出 **SE-GoS**，它保持词法播种 + 反向 PPR 的检索配置固定不变，只通过三种**免训练**的更新来改进它所读取的图：

- **从轨迹归纳拓扑**：workflow 边来自查询级「播种→使用」共现；dependency 边来自有序使用；avoid 边来自失败尝试中的共现；而 avoid 边的撤回**仅在反复成功共用之后**发生。
- **边权衰减与强化**：对缺乏支撑的语义链接做衰减，对实际被使用的技能做强化。
- **单轮文本梯度优化**：优化那些检索效果差的节点描述（Pryzant et al., 2023）。

PPR 直接读取图的边权，所以改变权重或改变边就改变了被检索的内容。我们不编辑任何技能，也不训练任何参数。**因此，经验被存放在检索 harness 里，而不是存放在模型里或技能里。**

我们的核心贡献如下：

1. 我们识别出结构化技能检索的**静态图瓶颈**——这是 GoS 自己也承认的局限（Liu et al., 2026）——并说明**单次评测本身就已经产生的轨迹**足以修复它。
2. 我们提出 SE-GoS，把该信号转化为检索基底上的三种免训练更新：执行落地的关系归纳与 avoid 边撤回、软性语义边衰减与正向边权强化、以及单轮节点描述优化。这些更新不需要模型训练，也不修改技能文件。节点更新只重写图节点的**面向检索的描述字段**，所以被改变的是检索器对某个技能的看法，而不是技能本身。
3. 我们解释为什么「只改图」就足够。PPR 直接读取边权，因此重连图就改变了检索内容；而置信度加权的更新会保护证据稀少的边。
4. 我们在三种设置下评测。在完整基准上，一轮演化就把静态 GoS 从 52.4% 提升到 59.4%，输入 token 比全库加载少 32%，领先于平铺检索、向量检索与自演化基线。
5. 我们随后回答了静态图基线无法回答的两个问题。**重复更新没有帮助**：增益先平台化然后反转，因此演化是一次性部署步骤。**增益在图上从未见过的留出切分上依然存在**（52.9% → 58.3%），所以累积下来的是可迁移的结构而非被记住的轨迹。

---

## 2 相关工作

### 2.1 图结构检索与技能图

图结构检索改善了文档与工具的访问（Edge et al., 2024; Liu et al., 2024b），通常使用自动构建图上的 Personalized PageRank，例如 HippoRAG（Jiménez Gutiérrez et al., 2024）与工具图重排器（Zheng et al., 2024; Yuan et al., 2024; Liu et al., 2024c）。GoS（Liu et al., 2026）为依赖感知检索构建了一张带类型的技能图，但保持其静态；SkillDAG（Bai et al., 2026）用 LLM 提案在线编辑一张带类型的图；SkillGraph（Li et al., 2026b）联合更新教师蒸馏出的技能与读取它们的策略。相关的工具检索工作学习协同检索模型，包括 COLT（Qu et al., 2024）与 MassTool（Lin et al., 2025）；Tool-REX 研究文档扩展并引入 Tool-Embed 与 Tool-Rank（Lu et al., 2026）。

这些工作处理的是相邻问题，但都没有做到**在检索流水线、技能库与骨干全部固定的前提下，用离线 agent 轨迹演化一张固定的技能检索图**。SE-GoS 把图变成**可变的 harness 状态**：它的确定性纯语义基底由执行证据更新，而它的节点描述更新是这一图演化框架的一个组件，而不是一个独立的文档扩展方法。SkillGraph 改变了策略与技能表示，因此不属于我们「冻结骨干」的结果集。

**表 1  SE-GoS 的定位。** Evolving：检索状态随执行而变。Training-free：不训练任何模型权重。LLM-prior-free：没有模型去判定哪些技能相关。Skill selection：在既有技能中选择，而不改写它们。SkillDAG 是最接近的一行，它与 SE-GoS 只在 LLM-prior-free 一项上不同（见第 4 节）。

| 方法 | 图基底 | 演化 | 免训练 | 免 LLM 先验 | 技能选择 |
|---|:---:|:---:|:---:|:---:|:---:|
| 向量检索（Karpukhin et al., 2020） | – | – | ✓ | ✓ | ✓ |
| GoS（Liu et al., 2026） | ✓ | – | ✓ | – | ✓ |
| SkillRouter（Zheng et al., 2026） | – | – | – | ✓ | ✓ |
| Voyager（Wang et al., 2023） | – | ✓ | ✓ | – | – |
| ProTeGi（Pryzant et al., 2023） | – | ✓ | ✓ | ✓ | – |
| SkillGraph（Li et al., 2026b） | ✓ | ✓ | – | ✓ | – |
| SkillDAG（Bai et al., 2026） | ✓ | ✓ | ✓ | – | ✓ |
| **SE-GoS（本文）** | **✓** | **✓** | **✓** | **✓** | **✓** |

### 2.2 经验累积、提示优化与测试时适配

另有一支工作已经在利用执行轨迹，但各自适配的对象不同。Voyager（Wang et al., 2023）从探索中累积技能库，其后续工作则蒸馏跨回合洞见、把失败转化为言语强化、合成新技能、或归纳可复用工作流（Zhao et al., 2024; Shinn et al., 2023; Zheng et al., 2025; Wang et al., 2025）；另一些工作从文档语料编译出技能目录并让 agent 浏览（Sun et al., 2026）。**这些系统改变的是技能库或 agent 的流程。**

提示优化改变的则是指令：ProTeGi（Pryzant et al., 2023）在语言中镜像梯度下降，TextGrad（Yuksekgonul et al., 2024）把同一原则形式化为文本制品上的自动微分。测试时训练（Sun et al., 2020）改变的是模型本身，让权重适配测试实例。

**SE-GoS 让这三个对象都不动，只重构检索所遍历的那张图**：它的节点更新借用了 ProTeGi 的机制，用于一个单轮、节点局部的变体，目标是「被用到但排名很低」的技能；但技能库、agent 的流程与模型权重全部维持原样。

### 2.3 定位

区分性的组合是结构化的：**在一张随执行轨迹演化的技能图上做依赖感知检索，且不训练模型、不对技能相关性施加 LLM 先验、不修改技能内容或检索代码。** 表 1 对比了几种代表性的技能选择与图演化范式；相邻的工具检索工作在 2.1 中讨论，但不是我们实验中的直接基线。

---

## 3 方法：SE-GoS

SE-GoS 让 GoS 的检索过程读取一个随执行反馈演化的基底（图 1）。该基底**无需改代码即可演化**，因为检索读取的是它的边权与节点级检索描述：重新加权、重新连边、或重写某个节点描述，都会改变被检索的内容。

冷启动图不是 GoS 的带类型图，因为**我们不假设存在构建其 workflow 与语义关系的那一趟 LLM 验证**。SE-GoS 从一张确定性的纯语义相似度图出发——没有 LLM 趟次、没有 embedding 服务——随后由执行来提供缺失的结构，用**观测到的经验**替代 GoS 的 **LLM 先验**。每个图节点都有自己的检索描述字段，从关联的技能记录初始化；节点描述更新只改这个**图局部字段**，不改源 `SKILL.md`、包元数据或已水合的技能内容。

### 3.1 预备知识

SE-GoS 建立在 Graph-of-Skills（GoS）的检索基底之上（Liu et al., 2026），此处按 GoS 的设计原样重述，不做修改。我们实验所用的配置在第 4 节报告。

**问题设定。** 令 $C = \{d_1, \dots, d_m\}$ 表示一个技能包的本地语料。遵循 GoS，每个技能被归一化为一条可执行记录，语料变成一张带类型的有向图

$$G = (V, E, w, \phi) \tag{1}$$

其中每个节点 $v \in V$ 是一个归一化技能，带有图局部的检索描述 $d_v$；每条边 $e \in E$ 连接两个技能；$w(e) \ge 0$ 是边权；$\phi(e) \in \mathcal{R}$ 从关系集中赋予一个边类型：

$$\mathcal{R} = \{\text{semantic}, \text{workflow}, \text{dependency}, \text{avoid}\} \tag{2}$$

**Semantic** 是我们基底起始所依赖的关系，它是一张确定性的 **token 重叠相似度图**，而不是 GoS 那种经 LLM 验证的语义边。**Workflow** 与 **dependency** 是 GoS 余下的导航关系：dependency 通过把生产者输出与消费者输入做匹配来确定性归纳，workflow 则通过一个在有限候选池上运行的稀疏 LLM 关系验证器获得（每节点验证预算 $k=8$，见附录 A.2）。因此 GoS 所构建的图携带**一个由 LLM 提供的、关于技能间结构的先验**，在任何 agent 运行之前就已离线构造好。GoS 的第四个导航关系 **alternative**，SE-GoS 不使用，因为「一个技能能否替代另一个」是关于一次**并未发生**的执行的主张（附录 B.3）。**Avoid** 是 SE-GoS 新增的关系：它标记在失败轨迹上被共用、而在成功轨迹上未被共用的一对技能，权重为零、永不被遍历，因此不增加扩散质量，只在执行包组装阶段影响检索（第 3.3 节）。

给定查询 $q$ 与上下文预算 $\tau$，检索返回一个有界、执行完整的包 $B(q) \subseteq V$。

**词法播种。** 我们使用 GoS 的词法播种评测条件，因此种子分布的第 $i$ 个分量为 $p_i \propto s_i^{\text{lexical}}(q)$，推理时不需要 embedding 服务。局部打分器在技能名称、能力、描述、领域标签、工具、输入/输出类型、示例任务与入口点上使用加权 token 重叠。

**反向感知的带类型扩散。** 令 $A_r$ 表示关系类型 $r \in \mathcal{R}$ 的加权邻接矩阵，其元素取自边权 $w(\cdot)$。对每种类型，GoS 构造一个行归一化的前向算子 $T_r^{\rightarrow}$ 与一个行归一化的反向算子 $T_r^{\leftarrow}$，并统一为

$$T = \text{RowNorm}(A^{\rightarrow} + A^{\leftarrow}) \tag{3}$$

其中 $A^{\rightarrow}_{uv}$ 累加从 $u$ 到 $v$ 的每条边的存储权重 $w(u \to v)$，而 $A^{\leftarrow}_{vu}$ 累加 $\gamma_{\phi(u,v)} w(u \to v)$。反向系数由关系类型固定；不使用单独的前向关系乘子。avoid 边权重为零，因此对 $T$ 没有任何贡献。检索随后运行反向感知的 Personalized PageRank 扩散（Page et al., 1999; Jeh and Widom, 2003; Yang et al., 2024）：

$$s^{(\ell+1)} = \alpha p + (1-\alpha) T^\top s^{(\ell)} \tag{4}$$

其中重启概率 $\alpha \in (0,1)$，使相关性从匹配到的种子向结构上重要的前置条件传播。

**有预算的水合（budgeted hydration）。** 词法字段命中在播种时进入；PPR 之后，技能按 $s^\star$ 排序。排名靠前的技能在单技能与全局上下文预算下被水合，产出有界的执行包。

### 3.2 经验信号收集

SE-GoS **消费的正是单次 GoS 评测已经产出的制品**，不需要额外运行。任务 $q_t$ 上的每次尝试 $t$ 产出一条轨迹

$$\mathcal{T}_t = \left(q_t,\ r_t,\ B_t,\ U_t,\ \text{tokens}_t\right) \tag{5}$$

其中 $r_t \in [0,1]$ 是验证器奖励，$B_t \subseteq V$ 是被检索到的包，$U_t$ 是 agent **实际使用**的技能集合——从轨迹的工具调用中，通过匹配已水合技能的本地源路径提取出来。$U_t$ 是无序的，用于共现证据；当 dependency 归纳需要时序时，我们另外保留首次使用序列 $U_t^{\text{ord}}$。$U_t$ 可以包含 $B_t$ 之外的技能（agent 即使检索没命中，也能通过浏览技能库发现一个技能），这正是节点更新所针对的情形。我们把一个演化窗口内的轨迹记为 $\mathcal{D} = \{\mathcal{T}_1, \dots, \mathcal{T}_T\}$。

三类更新沿三条互补的轴作用于检索基底（离散边集、连续边权、节点描述），因此没有任何一个更新会重写另一个的输出。

### 3.3 拓扑更新

拓扑更新通过归纳 workflow、dependency 与 avoid 关系来改变图的离散结构。它也能在**反复成功共用直接反驳失败侧证据**时撤回一条已存在的 avoid 边。单纯「未被使用」绝不删除边；语义边衰减属于边权更新。被归纳出的关系在权重与证据来源上都不同：

$$w(u \to v) = \begin{cases} \min\left(0.9,\ 0.6 + 0.05(c^r_{uv} - 1)\right), & r \in \{\text{workflow}, \text{dependency}\} \\ 0, & \text{avoid edges} \end{cases} \tag{6}$$

其中 $c^{\text{workflow}}_{uv}$ 统计见证了该对的**检索查询**数（所以一个含多个查询的任务可以贡献多于一次），而 $c^{\text{dependency}}_{uv}$ 统计见证该有序对的**不同任务轨迹**数。

**Workflow 边。** 若一个种子技能 $u$ 在某个成功尝试中因某个查询被检索到，而 agent 使用了**另一个**技能 $v$，这就构成一次查询级的行为共现。每个见证查询使 $c^{\text{workflow}}_{uv}$ 加一，因此一个含多个查询的任务可能贡献多于一次。轨迹并不能确立「检索到 $u$ 导致后来使用 $v$」。

**Dependency 边。** 当一个成功尝试先使用 $u$ 再使用 $v$，且 $u$ 的输出与 $v$ 的输入之间的 schema 重叠超过 GoS 离线所用的阈值（$\zeta = 0.6$）时，schema 预测了前置条件、轨迹确认了它。这要求轨迹记录技能顺序，而第 4 节的完整基准协议会记录。

**Avoid 边。** 一对技能在失败尝试中至少被共用 $\theta_{\text{avoid}}$ 次、且从未在成功尝试中共用，即为 avoid 边的证据。该信号基于**观测到的共用**，而不只是被一起装进检索包。我们强制一条保守的**无矛盾不变式**：一个已经拥有任何导航关系（包括语义边）的无序对，不会再被赋予 avoid 边。这会漏掉语义相似技能之间的有害配对，但避免在同一对上放置相互矛盾的信号。avoid 边权重为零、被排除在权重强化之外，只在执行包组装阶段起作用。若一个候选的 avoid 伙伴已被选中，该候选被丢弃，且**不从预排序 top-$N$ 列表之下回填**，所以最终包可能小于 $N$。已存在的 avoid 边只有在当前演化窗口内该对至少被共用出现在**两条不同的成功任务轨迹**中时才被撤回；单纯的未使用不构成撤回证据。该通道在基准上的产出见附录 B.4。

### 3.4 边权更新

该更新作用于连续边权，与 L1 在关系级拓扑改变上互补。

**第一，软剪枝。** 如果技能 $v$ 被至少 $\theta_{\text{obs}}$ 个不同训练任务浮现出来，却从未在任何训练轨迹中被使用，则每条进入 $v$ 的语义边被衰减一次：

$$w(u \to v) \leftarrow 0.5\, w(u \to v)$$

这是软剪枝：不删除任何边，也不施加下限。一个任务内的多个查询只计为一个「被浮现的任务」。

**第二，正向强化。** 对每次奖励为正（$r_t > 0$）的尝试 $t$，以及每个被使用的技能 $v \in U_t$，所有指向 $v$ 的既有非 avoid 边都被强化——无论其源是否被检索到：

$$w^{(t+1)}(u \to v) = w^{(t)}(u \to v) + \eta \cdot r_t \cdot \mathbb{I}[v \in U_t] \tag{7}$$

其中 $\eta > 0$ 是强化率，$r_t$ 按任务奖励缩放增量；失败尝试不贡献正向信用。该更新是对目标入边（非 avoid）的**全局**更新，不是对某个被检索源的因果归因。我们在此评测的单轮协议中直接报告这些原始累积权重。附录 B.3 推导了一个与静态先验的**置信度加权插值**，用于在多轮演化中保护已部署的图免受冷启动影响。

### 3.5 节点更新

该更新的目标是**被使用但浮现得很差**的技能：某个技能 $s$ 在一次失败尝试中被使用（$r_t < r_{\text{success}} = 0.9$），但在查询 $q$ 上的排名低于 $n_{\text{rank}}$（默认 3；缺失的技能排名最后）。

该更新改编自 ProTeGi（Pryzant et al., 2023），使用一个**单轮、节点局部**的文本梯度算子：一个 LLM 提出改写并做复述，随后**离线检索**选出能在这些「未命中查询」上最大程度改善目标节点排名的那个节点描述。令 $H_s(d)$ 计数 $s$ 出现在检索 top-$N$ 中的未命中查询数，$R_s(d)$ 累加它在这些查询上的 1-索引排名之和。被选中的节点描述为

$$d_s^\star = \arg\max_{d \in \text{Cands}(s)} \left(H_s(d),\ -R_s(d)\right)_{\text{lex}} \tag{8}$$

其中缺失的技能排名为 $N+1$。候选必须至少在一个未命中查询上把 $s$ 放进 $n_{\text{rank}}$ 以内。目标先最大化 $H_s(d)$，再最小化 $R_s(d)$；候选生成、并列处理与「不驱逐守卫」在附录 A.2 详述。候选选择只用离线检索，不需要额外的 agent 尝试。

**模型是观测轨迹上的算子，而不是关于技能相关性的先验。** 在失败任务上的使用不是真值相关标签：agent 可能选错了技能。因此该更新优化的是**与观测使用的一致性**，而不是**经过验证的因果有用性**；不驱逐守卫限制了连带的检索回退，但无法验证一个正向关联。所有组件都使用同一个以轨迹为条件的算子，使消融可归因于演化本身，而不是某个基线先验。

### 3.6 演化后图的检索

SE-GoS 每个演化窗口把图演化一次，随后对每个查询都在演化后的图 $G^{(\mathcal{T})}$、权重 $w^{(\mathcal{T})}$ 与描述 $d^\star$ 上执行词法播种、反向感知 PPR 与有预算水合来服务。因此排序是**经验感知**的：它依赖图结构、查询相关性，以及编码在权重中的历史有效性。演化是一个两阶段、完全离线的过程：附录 A.1 的算法 1（阶段 A：信号提取）与算法 2（阶段 B：离线更新应用）给出了细节，同一附录的算法 3 表明检索读取的是演化后的图。

---

## 4 实验

实验在 SkillsBench（Li et al., 2026a）与 ALFWorld dev 切分上进行。基线为：**Vanilla**（把全库载入上下文）、**向量检索**、**静态 GoS**，以及 **SkillDAG**（Bai et al., 2026）——最接近的自演化系统。我们报告三项研究：

- **表 2** 在三个骨干上比较全部五种方法：两个来自 GoS，一个是我们新增的近期高性价比模型。
- 两项后续研究仅在 SkillsBench 上运行（它仍有余量）；ALFWorld 在其中两个骨干上接近饱和，基于图的行已处在 80 高位到 90 低位（表 2）。
- **4.3 节**在 50 个任务上演化图、在不重叠的 37 个任务上度量，从而把**迁移**与**记忆**分开。
- **4.4 节**在已稳定的图上继续运行更多演化轮次。

### 4.1 实验设置

**基准与骨干。** 我们在 SkillsBench（Li et al., 2026a）上评测——这是 GoS 所用的基准（Liu et al., 2026）：真实世界技术任务配上精心整理的技能。我们使用完整的 87 任务集与已发布的 1,000 技能库，并额外在同一协议下运行 ALFWorld `valid_seen` 切分（Shridhar et al., 2020）作为跨域检查。这里的 ALFWorld 是域内的跨域评测；我们不主张 ALFWorld 留出迁移。表 2 覆盖三个骨干：两个是 GoS 报告的，第三个是 deepseek-v4-flash-0731——一个我们新增为主设置的近期高性价比 flash 模型。每个设置每任务运行两次尝试，在 GoS 环境与重试策略下最多 8 个并发 Docker 尝试。

对于我们的 SkillsBench 运行，验证器奖励是**收集到的单元测试用例中通过的比例**，从 Common Test Report Format（CTRF）输出计算；因此 $R$ 是每次尝试奖励在 $[0,1]$ 上的均值。这个分数式的局部指标不同于 SkillsBench 上游的「全部测试通过」二值奖励。由于每次尝试可以获得分数信用，池化均值不受限于 $1/174$ 的倍数。ALFWorld 奖励是二值成功，因此其 $R$ 是成功率。我们还报告每次尝试的平均输入 token 数（T）与仅 agent 的运行时间（S）。附录 C.1 记录了基准与骨干选择以及尝试记账。

**评测协议。** 自演化检索会**重新度量生成其经验的那些任务**。我们遵循 SkillDAG 在 SkillsBench 上的部署效用惯例：全部 87 个任务产生轨迹，三种更新运行一次，全部 87 个任务在演化后的图上被重新度量。这是「部署系统值得被度量」的协议，也把我们的完整基准单元格与已发布的 SkillsBench 数字放到同一基准线上。其代价是可能对已traced的任务产生记忆化，4.3 节直接度量了这一点。每个池化奖励都是在被计分的尝试上计算的：如果某次尝试在验证器能运行之前 harness 自身就失败了，它会被同时排除在分子与分母之外，而不是计为零分——这遵循最接近基线的记账惯例（Bai et al., 2026）。每个完整基准单元格都在其完整的 $87 \times 2 = 174$ 次计分尝试上度量。对于演化，信号解析器保留每个任务的**最后一次**尝试，得到 87 条按任务轨迹；默认不池化尝试。每个数字都是计分尝试上的均值。我们描述性地报告点估计，不对单个单元格做显著性检验；微小差异不应被解释为已确立的统计显著增益。在两个商用骨干区块中，Vanilla、Vector 与静态 GoS 是从 GoS 引用的历史值，而 SE-GoS 与 SkillDAG 是新鲜度量，因此可能的 API 版本漂移是这些跨时比较的局限。并发重跑与不确定性估计留待后续评测。

**配置与演化协议。** 主表的 GoS 基线使用原始带类型 GoS 图；它不同于 SE-GoS 的纯语义冷启动图。SE-GoS 使用词法播种与反向感知 PPR（top-$N=5$ / seed-$K=4$、每技能 1,800 字符 / 全局 9,000 字符预算），运行在官方 1,000 技能节点（863 条语义边）上的一张确定性 token 重叠 $k=1$ 图之上。其演化轨迹在这个纯语义基底上收集，L1—L3 按依赖顺序离线应用一次。组件消融在全部八个条件下都从同一张 SE-GoS 冷启动图出发，在该基底上隔离各更新；它不是从原始 GoS 带类型图初始化的。被归纳的关系是执行落地的（workflow 来自「检索→使用」共现，dependency 来自有序使用与 GoS I/O-schema 规则的匹配，avoid 来自失败共现），计数与结果一并报告。更多协议细节见附录 A.1。

### 4.2 主结果

在 deepseek-v4-flash-0731 上，原始 GoS 图得分 **52.4%**，而 Vanilla 为 46.2%、Vector 为 38.7%。**一轮 SE-GoS 演化达到 59.4%（相对 GoS +7.0）**，超过 SkillDAG（55.3%）与两个平铺基线，每次尝试 3.45M 输入 token（比 Vanilla 低 32%）。4.5 节的组件消融则从 SE-GoS 的纯语义冷启动图出发，在不测试「从原始带类型 GoS 图演化」的前提下隔离三种更新。在其他骨干上，SE-GoS 相对 GoS 在 minimax-m2.7 上提升 **+9.8**、在 gpt-5.2-codex 上提升 **+3.7**；增益在静态图得分最低处（18.7%）最大。SkillDAG（Bai et al., 2026）为其路由信号报告了同样的模式。

**表 2  主结果。** R：平均奖励（%）；T：每次尝试的平均输入 token（M）；S：仅 agent 运行时间（秒），保留一位小数。粗体 = 最优，下划线 = 每个模型区块内该指标列的次优；↑/↓ 表示越大/越小越好。SkillsBench 每单元格覆盖全部 $87 \times 2 = 174$ 次尝试；ALFWorld `valid_seen` 每区块覆盖全部 $140 \times 2 = 280$ 次尝试（第 4.1 节）。

| 模型 | 方法 | SkillsBench R ↑ | SkillsBench T ↓ | SkillsBench S ↓ | ALFWorld R ↑ | ALFWorld T ↓ | ALFWorld S ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| **deepseek-v4-flash-0731** | Vanilla | 46.2 | 5.06 | 771.4 | 80.4 | 1.81 | 85.1 |
| | Vector | 38.7 | 3.11 | 790.7 | 83.9 | 0.04 | 60.3 |
| | GoS | 52.4 | 3.67 | 843.8 | 88.2 | 0.07 | 65.2 |
| | SkillDAG | 55.3 | 3.62 | 862.9 | 90.4 | 0.06 | 66.8 |
| | **SE-GoS** | **59.4** | **3.45** | 883.7 | **91.1** | 0.07 | 63.2 |
| **minimax-m2.7** | Vanilla | 17.2 | 0.94 | 580.7 | 47.1 | 2.18 | 88.6 |
| | Vector | 10.4 | 0.85 | 552.9 | 50.7 | 0.07 | 73.4 |
| | GoS | 18.7 | 0.87 | 502.5 | 54.3 | 0.07 | 68.8 |
| | SkillDAG | 27.3 | 1.05 | 560.2 | 67.1 | 0.09 | 75.9 |
| | **SE-GoS** | **28.5** | **0.92** | 572.4 | **68.6** | 0.08 | 74.3 |
| **gpt-5.2-codex** | Vanilla | 27.4 | 3.19 | 686.8 | 89.3 | 1.44 | 83.3 |
| | Vector | 21.5 | 1.24 | 773.0 | 92.9 | 0.03 | 57.0 |
| | GoS | 34.4 | 1.38 | 715.6 | 93.6 | 0.05 | 64.7 |
| | SkillDAG | 36.8 | 1.65 | 780.4 | 93.6 | 0.05 | 64.2 |
| | **SE-GoS** | **38.1** | **1.56** | 749.1 | 93.6 | 0.05 | 62.3 |

### 4.3 对留出任务的泛化

**奖励增益在图上从未见过的任务上依然存在。** 为把泛化与记忆化分开，我们把任务切成 50 个训练任务与 37 个评测任务，二者不重叠但在八个技能域上分层（`evo_data/split.json`）。演化只在 50 个训练任务上运行。然后每个方法都在同样的 37 个评测任务上度量，在 $k=1$ 基底上各尝试两次（$n=74$，表 3）。

在留出任务上，SE-GoS 把静态 GoS 从 **52.9% 提升到 58.3%（+5.4 点）**，token 基本不变（每次尝试 3.30 → 3.19 M）、运行时间可比（631.4 → 650.8 秒）。因为边编码的是技能之间**跨任务的规律性**，而不是某条轨迹特有的东西，且评测任务与训练任务不重叠，该增益反映的是**可迁移的结构**而非被记住的轨迹。与完整基准一样，基于图的行位于平铺行之上，因此该排序在两种协议下都稳定。SkillDAG（Bai et al., 2026）没有发布留出 SkillsBench 数字（它唯一的留出结果在 ALFWorld 上），因此上表中的 SkillDAG 行是在该切分上实测的，不是引用的。

**表 3  37 任务留出切分上的对比**（$n=74$ 次尝试，全部计分；骨干：deepseek-v4-flash-0731）。粗体 = 最优，下划线 = 次优；每一行都在该切分上度量。

| 条件 | R ↑ | T ↓ | S ↓ |
|---|---:|---:|---:|
| Vanilla | 44.8 | 5.23 | 608.9 |
| Vector | 38.1 | 3.01 | 573.4 |
| GoS | 52.9 | 3.30 | 631.4 |
| SkillDAG（在训练集上演化） | 54.2 | 3.65 | 721.7 |
| **SE-GoS（在训练集上演化）** | **58.3** | **3.19** | 650.8 |

### 4.4 多轮演化有帮助吗？

**它帮一次，然后就停了。** 表 4 在已稳定的图上重跑全部三种更新，把上一轮的轨迹当作新经验，每轮重新度量全部 87 个任务（$n=174$；骨干：deepseek-v4-flash-0731）；第 0 轮是静态图，第 1 轮即表 2 的 SE-GoS 单元格。

**表 4  多轮演化**（每轮 $n=174$ 次尝试，全部计分；骨干：deepseek-v4-flash-0731）。粗体 = 最优 / 下划线 = 每个指标列的次优。

| 演化轮次 | R ↑ | T ↓ | S ↓ | 边数 | 节点编辑数 |
|---|---:|---:|---:|---:|---:|
| 0（静态） | 52.4 | 3.67 | 843.8 | 863 | – |
| **1** | **59.4** | 3.45 | 883.7 | 1,118 | **6** |
| 2 | 59.8 | 3.66 | **813.9** | 1,375 | 2 |
| 3 | 54.0 | 3.71 | 850.8 | 1,502 | 4 |

奖励在第 1 轮升到 59.4%，在第 2 轮基本持平（59.8%），随后在第 3 轮跌到 54.0%，同时边数从 1,118 增长到 1,502。token 成本也随之上漂，运行时间在第 2 轮最低（813.9 秒）。**第一轮之后归纳出的边不再值回它们自身的成本**，因此我们在部署时只应用一次更新，即正文的设置。

### 4.5 组件消融

全部八个因子条件都从同一张 SE-GoS 纯语义冷启动图出发，而不是主结果所用的原始带类型 GoS 图。边权更新具有最大的单组件增益（相对 50.8% 的对照 **+6.5 点**），其次是拓扑（**+3.3**）与节点描述（**+2.8**）。因子主效应为：边权 **+5.1 点**、拓扑 **+1.8**、节点描述 **+1.7**；留一法比较给出同样的排序。该消融在 SE-GoS 自己的冷启动基底上隔离三种更新；它不测试从原始 GoS 图初始化后的演化。更多协议细节见附录 C.1。

**表 5  从 SE-GoS 纯语义冷启动图出发的组件消融**（$k=1$，每单元格 $n=174$）。粗体 = 最优 / 下划线 = 每列次优。

| 方法 | R ↑ | T ↓ | S ↓ |
|---|---:|---:|---:|
| SE-GoS 冷启动 | 50.8 | 3.74 | 829.1 |
| + 拓扑 | 54.1 | 3.37 | 781.8 |
| + 边权 | 57.3 | 3.35 | 807.9 |
| + 节点 | 53.6 | 3.86 | 883.3 |
| + 拓扑 + 边权 | 58.8 | 3.66 | 799.4 |
| + 拓扑 + 节点 | 55.8 | **3.17** | 844.5 |
| + 边权 + 节点 | 59.1 | 3.43 | **771.5** |
| **+ 拓扑 + 边权 + 节点（SE-GoS）** | **59.4** | 3.45 | 883.7 |

把节点更新加到「拓扑 + 边权」上，把奖励从 58.8% 提到 59.4%；这 0.6 点的差异是描述性的，交互效应未做显著性检验。

---

## 5 结论

SE-GoS 把**检索图当作离线维护的 harness 状态**，从而让执行经验变得可复用，同时保持检索流水线、骨干与源技能包固定不变。在已评测的设置中，一轮演化提升了奖励，并迁移到留出的 SkillsBench 任务上。组件消融在纯语义冷启动图上识别出**边权适配是最大的单独立贡献者**，而重复更新并不带来一致增益。与在线图编辑方法不同，SE-GoS 把**经验收集与图维护分离**，因此更新可以在影响后续检索之前被检视；它也因此不会在一次部署运行内立即适配。这把 SE-GoS 定位为静态结构化检索的**轨迹驱动补充**，而不是一个模型训练流程。我们的证据限于已评测的基准、库规模与骨干；扩展到显著更大的库与更广的模型家族仍有待测试。

---

## 附录 A  方法与实现细节

### A.1 算法

演化是离线的，分两阶段运行，与代码一致：阶段 A（算法 1）扫描收集到的轨迹并累积执行信号。阶段 B（算法 2）按依赖顺序把三种更新应用到图上。推理（算法 3）在演化后的图上运行 GoS 检索过程。

**算法 1  SE-GoS 演化（离线），阶段 A：从轨迹提取执行信号。**

```
Require: 轨迹 D = {T_t}_{t=1..T}，成功阈值 r_success = 0.9，schema 阈值 ζ，
         阈值 θ_obs, θ_avoid，撤回阈值 θ_retract = 2，节点阈值 n_rank
 1: 初始化查询级计数 c_workflow_uv、任务级计数 c_dependency_uv、c_failed_uv、c_success_uv、
    被浮现任务指示 z_t(v)、以及每技能查询映射 Q_s ← {s ↦ ∅ : s ∈ V}
 2: for t = 1, ..., T do
 3:   for 任务 t 记录的所有查询 q do
 4:     记录 z_t(v) = 1 当且仅当 v 出现在任务 t 至少一个查询的检索 top-N 中
 5:     if r_t ≥ r_success then
 6:       for q 的所有词法种子 u、被使用的 v ∈ U_t，u ≠ v do
 7:         c_workflow_uv ← c_workflow_uv + 1
 8:       end for
 9:     end if
10:   end for
11:   for U_t^ord 中所有有序使用对「u 先于 v」，且 schema(u, v) ≥ ζ、r_t ≥ r_success do
12:     c_dependency_uv ← c_dependency_uv + 1
13:   end for
14:   for 所有尝试 t、所有对 {u, v} ⊆ U_t do
15:     c_failed_uv ← c_failed_uv + I[r_t < r_success]；c_success_uv ← c_success_uv + I[r_t ≥ r_success]
16:   end for
17:   for 所有失败尝试 t、t 的查询 q、以及 s ∈ U_t 且 rank(s | q) > n_rank do
18:     Q_s ← Q_s ∪ {q}
19:   end for
20: end for
21: return 信号计数 (c_workflow, c_dependency, c_failed, c_success, Q_s)
```

**算法 2  SE-GoS 演化（离线），阶段 B：应用拓扑、边与节点更新。**

```
Require: 静态图 G_0 = (V, E_0, w_0, φ)，阶段 A 信号计数，
         超参数 η, θ_obs, θ_avoid, θ_retract = 2, n_rank, p
 1: E ← E_0；w ← w_0            // 从静态图出发
 2: // (B.1) 拓扑更新：归纳 workflow / dependency / avoid 边
 3: for 所有 c_workflow_uv ≥ 1 的对 (u, v) do
 4:   E ← E ∪ {(u, v)}，类型 workflow，权重 w_workflow(u → v)
 5: end for
 6: for 所有 c_dependency_uv ≥ 1 的有序对 (u, v) do
 7:   E ← E ∪ {(u, v)}，类型 dependency，权重 w_dependency(u → v)
 8: end for
 9: for 所有 c_failed_uv ≥ θ_avoid 且 c_success_uv = 0 的对 (u, v) do
10:   E ← E ∪ {(u, v)}，类型 avoid，权重 0
11: end for
12: for 所有已存在的 avoid 边 (u, v) 且 c_success_{u,v} ≥ θ_retract do
13:   E ← E \ {(u, v)}
14: end for
15: // (B.2) L2 软衰减：每个不同任务最多贡献一次
16: for 所有满足 Σ_t z_t(v) ≥ θ_obs 且 Σ_t I[v ∈ U_t] = 0 的 v do
17:   w(u → v) ← 0.5 w(u → v) 对所有语义边 u → v；保留边、不设下限
18: end for
19: // (B.3) L2 边强化（式 7）；排除 avoid 边
20: for 满足 r_t > 0 的 t do
21:   for 所有被使用的 v ∈ U_t、所有边 (u, v) ∈ E 且 φ(u, v) ≠ avoid do
22:     w(u → v) ← w(u → v) + η · r_t
23:   end for
24: end for
25: // (B.4) 节点更新（单轮；不驱逐守卫开启）
26: for 所有 Q_s ≠ ∅ 的 s do
27:   d_s* ← argmax_lex_{d ∈ Cands(s)} (H_s(d), -R_s(d))，受 top-K 不驱逐守卫约束；精确并列保留首个候选（式 8）
28: end for
29: return 演化后的图 G = (V, E, w, φ) 与描述 {d_s*}
```

**算法 3  SE-GoS 检索（推理）。**

```
Require: 查询 q，演化后的图 G = (V, E, w, φ)，演化后的描述 {d_s*}，预算 τ
1: 用演化后的描述计算词法种子得分上的种子分布 p
2: 从演化后的权重 w 构建转移算子 T（式 3）
3: 运行反向感知 PPR 至收敛，s*（式 4）
4: 按 s* 排序技能并水合有界的包
5: return 有界执行包 B(q)
```

### A.2 超参数

SE-GoS 按设计使用一张确定性的纯语义冷启动图。GoS 在具备离线 LLM 验证趟次时可以构造额外的带类型关系，但 SE-GoS 省略该先验，以便 workflow、dependency 与 avoid 关系可归因于执行轨迹。检索使用词法播种，不需要 embedding 服务。

表 6 列出 SE-GoS 的超参数与默认值。检索侧超参数（PPR 重启、关系权重、预算）是 harness 默认值，在所有基准与库规模上保持固定，从而使任何相对静态基线的差异都可归因于演化。

**表 6  SE-GoS 超参数；所有实验中使用的默认值。**

| 超参数 | 取值 | 作用 |
|---|---|---|
| PPR 重启 α | 0.2 | 传送概率（式 4）。 |
| 反向权重 γ_r | dependency 1.0、workflow 0.5、semantic 0.2 | 反向遍历强度（式 3）。 |
| 词法播种 | 名称、能力、描述、标签、工具、I/O、示例、入口点上的加权 token 重叠 | 种子得分 $p_i \propto s_i^{\text{lexical}}$；不用 embedding。 |
| top-N / seed-K / 预算 | 5 / 4 / 1,800 + 9,000 字符 | 执行包组装。 |
| 强化率 η | 0.1 | Hebbian 步长（式 7）。 |
| 归纳权重 | $0.6 + 0.05(c^{\text{workflow}}_{uv} - 1)$，上限 0.9 | workflow 边权；计数是**查询级**的（第 3.3 节）。 |
| 观测阈值 θ_obs | 2 个不同任务 | 对从未被使用的头节点做衰减前的浮现次数；一个任务内的多个查询只计一次。 |
| 语义衰减因子 | 0.5 | 对入向语义权重做一次性 L2 缩放；不删边、不设下限。 |
| 复述数量 p | 2 | 每个被编辑描述的复述变体数。 |
| 节点更新阈值 n_rank | 3 | 被使用的技能若排名劣于此值就被针对。 |
| 节点更新未命中来源 | 失败（默认） | 来自奖励 < r_success 的尝试的查询。 |
| 成功阈值 r_success | 0.9 | 拓扑/节点未命中过滤的成功切点。 |
| avoid 阈值 θ_avoid | 1 | 构成 avoid 边的失败共现次数（且无成功）。 |
| avoid 撤回阈值 θ_retract | 2 个不同成功任务 | 撤回既有 avoid 边所需的成功共用（L1）。 |
| dependency 阈值 ζ | 0.6 | dep 认证的 I/O schema 重叠。 |
| 不驱逐守卫（节点更新） | 开（默认） | 在所有已记录查询上，保留任何已记录训练尝试中使用过的 top-K 技能。 |
| 描述编辑预算 | ≤ 50 tokens | 描述编辑的上限。 |

### A.3 轨迹提取

被使用技能集合 $U_t$ 从轨迹中提取：扫描 agent 的工具调用（shell、文件读取、代码执行调用），查找对执行包 $B_t$ 中返回的已水合技能源路径的引用。目录名通过技能记录的源路径字段映射到归一化技能节点。$U_t$ 作为**集合**用于共用统计；dependency 归纳另外使用记录下来的首次使用顺序。零奖励尝试贡献到失败尝试的 avoid 证据与 L2 从未使用衰减统计中。部分奖励尝试按其奖励成比例地贡献正向权重（式 7）。

### A.4 节点更新提示词

对每个受影响的技能，节点更新发出三次 LLM 调用：一个**批评者**看到当前描述与所有未命中查询；一个**编辑者**提出一次改写；一个**复述者**提出 $p=2$ 个变体。离线评估器重跑与推理时相同的词法播种与 PPR 检索。它选出最大化命中数、再最小化排名和的候选，只提交至少在一个未命中查询上把技能放进 top-$n_{\text{rank}}$ 的候选，并强制执行不驱逐守卫：在所有已记录的训练查询上，任何在已记录训练尝试中被使用过、且当前出现在该查询 top-$K$ 中的技能都必须留在那里。精确得分并列时保留首个生成的候选。不涉及任何 agent 运行。

---

## 附录 B  附加结果与诊断

### B.1 定性分析

演化增量本身是可检视的。在单轮演化中，拓扑更新产出执行落地的关系：查询级 workflow 共现、有序使用与 GoS I/O-schema 规则吻合处的 dependency 边、以及失败尝试共用产生的 avoid 边。L1 更新只在至少两条不同成功任务轨迹共用该对时才撤回一条先前的 avoid 关系。L2 把入向语义权重减半，针对被至少两个不同任务浮现却从未被使用的技能；它保留这些边且不设下限。它还会在正奖励尝试上强化每条指向被使用目标的既有非 avoid 入边。节点更新为那些被使用但排名低于节点更新阈值的节点修改图局部的检索描述（第 3 节）。结果表中的报告计数来自已评测的那次运行；更新后的方法设置将被单独重新度量。增量记录新增与撤回的边以及权重变化，可以逐边检视。

### B.2 配置理由

本附录给出正文（第 4 节）简述的两项配置选择背后的完整论证。

**为何使用 token 重叠语义基底。** GoS 从 embedding kNN 索引构建其语义邻居；SE-GoS 的语义边则改由签名 token 的 Jaccard 重叠计算。该计算是确定性且无模型的，因此基础图由原始文本构建、无需 embedding 服务，并且在描述编辑之后仍可重算——这正是语义边演化的间接路径（第 3 节）。对 87 个任务查询在两种构造上的离线重放显示，就我们关心的量（agent 后来使用的技能是否被浮现）而言二者检索等价：官方 embedding-kNN 基底与 token 重叠基底的 hit@5 都是 70/73（0.959），平均最优排名都是 1.19；而 token 重叠图的度分布更均匀（在已发布的 $k=1$ 基底上最大度为 98，对比 embedding-kNN 基底的 484），因此 PPR 更不容易发生**枢纽崩塌**。基于 embedding 的边还会把图绑死在一个预计算索引上，一旦描述变化就无法扩展——而我们瞄准的部署并不携带 embedding 服务。

**为何没有带类型的 {dependency, workflow, semantic, alternative} 边集。** 重建一个带类型边集需要在由每技能 I/O 元数据构成的候选池上跑一趟 LLM 验证，而 SE-GoS 瞄准的部署不假设这一点。这是设计选择而非局限：GoS 的候选池有一个词法通道与一个 I/O 索引通道，都不需要 embedding 服务，因此带类型图是可以在无 embedding 的情况下构造的，而 SE-GoS 的贡献是**改为从执行中获得结构**。因此我们的静态图只包含语义边，这恰好是 SE-GoS 瞄准的设置，而缺失的结构随后由执行反馈提供。

**为何只用词法播种。** 我们使用 GoS 的 SkillsBench 评测 harness 所提供的词法播种 + 反向 PPR 条件。它不需要 embedding 服务，并在静态图与演化图之间保持播种与传播配置固定；因此任何差异都源于演化后的图字段，而不是被改变的检索条件。

### B.3 设计理由（完整论证）

**免训练、确定性、可审计。** 除打分之外，演化图的唯一消费者是执行包组装——当该通道被触发时它会丢弃「共同加载」的 avoid 对（第 3.3 节）。其他每个更新都纯粹通过图的权重、边与描述作用于检索器。演化后的图是否同时降低实际消耗的输入 token，在第 4 节评测。合起来看，**边权是成功执行的一份压缩、非参数化记录，随技能库一起流通并被多个 agent 共享**。

**先验 vs 算子。** 先验是证据存在之前就装入的信念：GoS 的关系验证器与 SkillDAG 的成对分类器都从文档判定相关性，没有见过任何执行。算子把证据变成更新，且可以是模型：节点更新的批评者与编辑者作用于一个**确实使用过该技能的查询**和**确实把它排得太低的检索证据**，且没有候选描述会被提交，除非它可证明地提升了该技能在此类查询上的排名。如果结构通道携带了 LLM 先验，那么 $2^3$ 因子设计就无法把「演化带来的增益」与「该先验带来的增益」分开，因为基线本身已经包含它。

**为何拓扑撤回是有选择的、而衰减是软的。** L1 只撤回 avoid 边，且只在至少两条不同成功任务轨迹后来共用该对时。这是对该关系失败侧定义的直接反证；单纯未使用不是。L2 用**减半而不是删除**来处理更弱的证据：对反复浮现却从未被使用的技能，把入向语义权重减半。保留边维护了稀疏基底的连通性，并为未来的证据留下强化路径；不需要任意权重下限。这把关系级拓扑改变（归纳与有证据支撑的 avoid 撤回）与连续的语义权衰减分离开。GoS 在图维护与去重期间也会移除一些边，SkillDAG 则允许 agent 显式提出移除/重定类型；二者都不等同于「仅因在有限执行窗口内未被观测到就删边」（Liu et al., 2026; Bai et al., 2026）。

**过拟合与部署窗口。** 经验感知的更新可能过拟合到已traced的任务。4.4 节的多轮曲线显示重复更新在第 2 轮平台化、在第 3 轮反转。一种解读是：后续轮次消费的是在演化图上产生的轨迹，因此它们新增的边编码的是**上一轮的排名**而不是新的执行证据。生产部署可以按窗口运行演化，保留拓扑与节点更新所需的窗口级统计。我们直接度量了单轮与多轮两种机制（4.4 节），除此之外不刻画窗口化部署。

**置信度加权插值（部署保障）。** 在长期部署中，演化会重复很多轮而每条边的证据计数依然很小，此时新加入或极少被观测的边不应立即主导技能图。因此我们把演化权重与图构造时设定的静态先验 $w_0(e)$ 混合：

$$w(e) = \left(1 - \lambda_c(e)\right) w_0(e) + \lambda_c(e) \tilde{w}(e) \tag{9}$$

$$\lambda_c(e) = \frac{n_e}{n_e + n_0} \tag{10}$$

其中 $\tilde{w}(e)$ 是原始累积权重，$n_e$ 是边 $e$ 的信息性尝试数，$\lambda_c(e)$ 是带先验强度 $n_0$ 的置信权重。该插值是**部署保障**，并未在已评测的单轮实现中被实例化；使用它的部署必须在标定时指定 $n_0$。对没有或极少观测的边，$\lambda_c(e) \approx 0$，检索行为接近静态先验。随着证据累积，图越来越由经验驱动。在报告的单轮协议中，直接使用原始累积权重，该插值未被启用。

**为何图结构更新优于无图适配。** 一个无图基线用每个技能自己的经验分（成功率或平均奖励）来加权它，把技能当作彼此独立。SE-GoS 改为更新**边**：当技能 $u$ 导向 $v$ 的一次成功使用，未来每一个检索到 $u$ 的查询都获得一条通往 $v$ 的路径——这是一种**技能到技能的迁移**，而缺少任何相关性概念的逐技能基线无法表达。因此承载增益的是**图**，而不只是经验信号。

**完备性与更新顺序。** 一张技能图有四个组件，$G = (V, E, w, \phi)$（式 1）。三种更新恰好作用于其中三个可变组件，而节点集 $V$ 固定（SE-GoS 从不创建或废弃技能）。在一轮内，更新按依赖顺序运行：拓扑第一，边权第二（作为已定型边集的精修），节点更新最后（因为种子得分由描述计算）。在我们的纯词法配置中，被修订的描述直接进入下一次种子 token 重叠，没有重新索引步骤。

**为何执行归纳的是 workflow、dependency 与 avoid，而不是 alternative。** 拓扑更新产出 GoS 四种关系中的三种——这是「执行能识别什么」的边界，而不是「机制接受什么」的边界，因为转移算子是按关系标签查表分派的。Workflow 在查询级被见证：每个记录查询的词法种子与该成功任务上使用的技能配对；一个任务内的多个查询可能多次见证同一个有序对。这是共现证据，不是「检索 $u$ 导致使用 $v$」的证明。Dependency 使用首次使用顺序与 GoS 的 I/O-schema 规则。Avoid 基于失败尝试中**实际被共用**的技能（而不是包里被加载的每一个技能），成功共用作为反证。**Alternative 仍是反事实的，不被归纳。** 冷启动语义图保持原位，L2 只对反复浮现、从未被使用的头节点衰减语义权重。该更新不发出任何 LLM 调用。在无 LLM 先验的情况下恢复 alternative 仍属未来工作。

**为何 dependency 关系被归纳却在此处未触发。** Dependency 是三条规则中最严格的，值得说明其代价。一条 dependency 边需要：一次成功尝试（奖励 ≥ 0.9）、两个技能被按序使用、以及生产者输出与消费者输入之间至少 $\zeta = 0.6$ 的 I/O-schema 重叠。在 $k=1$ 的完整基准轨迹上，前两个条件从 87 次尝试中的 22 次成功尝试留下 **68 个有序对**。这些对中只有 **26 对**两侧都带 I/O 字段，而它们达到的最大重叠是 **0.500**，低于 $\zeta$。**因此没有 dependency 边被归纳出来**，本文报告的结构增益来自该更新新增的 workflow 边（avoid 边不携带扩散质量，只在组装时剪枝），再加上边权与描述更新。

**约束不在轨迹而在技能库**：已发布的 1,000 技能库中，只有 332 个技能带 inputs、337 个带 outputs，所以大约三分之二的库根本无法参与 schema 匹配。这也界定了「从执行获得结构」这一主张的边界，我们倾向于**明确画出这条线**而不是任其被推断。共现结构在轨迹中是可观测的（「先检索 $u$ 再使用 $v$」被直接见证，一起失败的一对也同样），这就是 workflow 与 avoid 都能触发的原因。**机制不可观测**：$u$ 产出 $v$ 所消费的制品这件事在轨迹中不留痕迹——轨迹只显示 $u$ 在前，而顺序本身无法把「前置条件」与「惯例」分开。GoS 通过从技能文档读取机制来解决这一点。我们保留它的规则与阈值，因此在文档沉默之处，该关系就保持未被归纳。

**我们没有为得到边而降低 $\zeta$。** 在 $\zeta = 0.5$ 时会有八对合格，但该阈值是 GoS 的，为了造出几条边而移动它，在这个样本量上不是我们能辩护的主张。有两条路径可以让该关系活起来：从技能内容恢复 I/O 字段，或者改从轨迹中挖掘 writer→reader 数据流而不是读 schema。我们探测了第二条：在 87 条任务轨迹上它产出 12 个候选对，schema 通道对其无一印证，而反复出现的那些对原来是单个任务内的**兄弟调用**而非前置条件。二者都仍属未来工作。

### B.4 avoid 通道触发到什么程度

在默认 $\theta_{\text{avoid}} = 1$ 下，更新提出 51 个「仅失败」共现；无矛盾不变式扣下 24 个，留下 **27 条 avoid 边**。avoid 边的扩散权重为零：它们在执行包组装阶段改变共同加载，而不改变 PPR 相关性得分。

---

## 附录 C  实验协议与可复现性

### C.1 基准、骨干与记账细节

**为何默认骨干是 flash 模型。** 更小、更便宜的骨干把更多任务难度留给 harness 去解决，而这正是检索图改进最可见的机制，也是注重成本的部署会运行的配置。

**任务划分。** 87 个任务是被划分、从不被下采样：每个任务在每种机制中都被使用，4.1 节为每种机制说明所报奖励平均在哪个子集上。对 ALFWorld，我们使用完整的官方 `valid_seen` 切分共 140 个 episode，不做下采样。这与 GoS 报告的完整 140 episode ALFWorld 评测、以及 SkillDAG 的 140 episode `valid_seen` 评测一致；SkillDAG 另外为其在线编辑训练阶段使用 420 个 episode。因此表 2 中的 $140 \times 2$ 计数意味着在完整 `valid_seen` 切分的每个 episode 上做两次尝试，而不是为对齐 SkillsBench 的 87 个任务而重采样。

**尝试记账。** 每个单元格都在其完整的 $87 \times 2 = 174$ 次尝试预算上度量。对于演化，解析器为每个任务保留最后一次尝试，因此三种更新都看到 87 条按任务轨迹。已发布代码在 `SEGOS_MERGE_ATTEMPTS=1` 时可以池化尝试，但该选项对所报告结果是关闭的。

**SkillsBench 奖励。** 对每个生成的任务副本，harness 运行上游 pytest 套件并记录一份 CTRF 报告。我们的局部验证器奖励是「被标记为 passed 的收集到的测试用例数」除以「收集到的总数」；failed、skipped、pending 与其他状态仍留在分母中且不计为通过。这个包装只改变奖励聚合，不改变任务指令或测试用例；源任务包保持不变。分数式奖励是本文所做 SkillsBench 运行所用的分数，而已发布的基线条目保持其来源报告的数值。

**Agent harness。** 三个骨干都由同一个 Codex-CLI agent harness 驱动，模型区块之间唯一不同的组件就是这个包装。

**$2^3$ 设计。** 增量从轨迹计算一次，并组合成一个八单元格的 $2^3$ 设计（静态加七个演化单元格），在 4.5 节报告。在一轮内，更新按依赖顺序运行：拓扑第一、然后边权、然后节点描述，理由见附录 B.3。

### C.2 与自演化基线的协议对比

SkillDAG（Bai et al., 2026）——最接近的同期自演化技能图系统——在域内评测 SkillsBench：图在执行期间被在线编辑（在 episode 时刻做一对「提议边/编辑边」），奖励在 agent 与演化图**在同一批任务上协同工作**时度量，并用同一批查询的冷启动 vs 编辑后重放，在任何下游执行之前隔离检索机制（Ret@K/MRR）。它的泛化主张依赖一个 ALFWorld 训练/测试切分：420 个域内训练 episode 开启编辑，140 个留出测试 episode 在冷启动图与训练产出的图上都被评测。它的冷启动图也依赖 LLM（HyDE 风格的 e_needs embedding 加上一个 LLM 成对分类器），而它自己的前提是：任何冷启动图在执行反馈到来之前必然是不完整的。SE-GoS 共享这一前提但移除了 LLM 依赖：它从一张确定性的纯语义相似度图出发，用固定规则重建缺失的执行结构。SkillGraph-RL（Li et al., 2026b）——基于训练的替代方案——同样在域内域（NQ、HotpotQA）上训练，并在不重叠的留出/未见域上评测。

我们的 SkillsBench 评测遵循 SkillDAG 的部署效用惯例（全部 87 个任务产生轨迹、全部 87 个被重新度量），因此头条数字与它的域内数字直接可比。由于 SE-GoS 离线批量演化一次，用同一批后来被计分的查询拟合出的更新可能反映**记忆化**而不是可迁移结构。我们通过另外报告一个留出评测（图在一个任务子集上演化、在不重叠的另一个上度量，4.3 节）来把两种主张分开。我们还借用 SkillDAG 的「冷启动 vs 编辑后」思路作为补充性的**检索召回诊断**：比较演化图是否比静态图更频繁地浮现出 agent 实际使用的技能。该诊断与演化结果一并报告，而不作为头条主张使用。

### C.3 基准保真度审计

我们的任务包源自上游 SkillsBench 仓库（Li et al., 2026a），取其 schema 迁移之前的那一刻快照（commit `d75b2187`，2026-06-14），即 v1.1 的 `task.toml` 布局，早于任务被重打包为原生 `task.md` frontmatter。把我们的 87 个任务包与该快照逐文件比较：

- `instruction.md`（给 agent 的提示）：87 个中 **0 个不同**；
- `tests/`（奖励验证器，包括 `test.sh`、`test_outputs.py`、`score_outputs.py`、`build.sh`）：87 个中 **0 个不同**；
- `task.toml`（超时、CPU/内存/存储限制、网络策略）：87 个中 **0 个不同**。

因此决定任务难度与奖励的三个组件与上游 v1.1 **逐字节相同**：没有任何指令、验证阈值、超时或资源设置被放松，所以 SE-GoS 与已发布基线之间的差距不能归因于被削弱的任务配置。

与该快照的唯一差异在于七个任务的 Docker 构建层，且都是不改变任务逻辑或验证器的本地适配：

- 四个任务带一个 `predownload/` 目录（`seismic-phase-picking`、`earthquake-phase-association`、`fix-druid-loophole-cve`、`python-scala-translation`）。上游 Dockerfile 在构建时抓取同样的制品：seisbench 模型权重（带重试）、Apache Druid 0.20.0 tarball 加浅层源码克隆、以及 Scala 2.13.12 发行版。我们的构建因为出口网关封锁了那些主机而从本地缓存复制。产出的镜像等价。
- `fix-build-google-auto` 删除了从 bugswarm 基础镜像继承来的未使用 Oracle JDK，以避免许可合规告警。
- 两个 web 任务（`fix-visual-stability`、`react-performance-debugging`）把 `next@14.2.10` 固定，而上游是 `14.0.4`/`14.2.0`。这是唯一真正的依赖版本差异。它不触碰验证器。若将来要求镜像的精确可复现，把这两个包回退到上游固定版本并重新度量就是一个两任务的检查。

另有一个 oracle 脚本（`pptx-reference-formatting/solution/solve.sh`）只在一条错误消息字符串上不同。**Oracle 从不决定奖励。**

---

## 附录 D  范围与局限

四条约束界定了上述主张。

1. **单轮头条数字。** 重复更新在第 2 轮平台化（59.8%）、在第 3 轮反转（54.0%，4.4 节），因此演化后的图只在单轮之后被报告，协议没有触及更细粒度的奖励信号或更长的时间跨度。反转界定的是所报告的机制范围，而不是更新本身：第一轮之后归纳出的边不再值回自身成本，附录 B.3 给出了我们提出的机制。
2. **被使用集合的提取。** 权重与拓扑更新读取从工具调用恢复出的被使用技能集合 $U_t$，因此间接的技能使用可能低估证据。该规则偏向遗漏：未被恢复的使用贡献不了证据，而不是贡献一条错的证据——这削弱更新而不是污染它。
3. **评测范围。** 我们在 1,000 技能规模上评测 SkillsBench，并在表 2 的三个模型家族下评测 ALFWorld dev 切分，因此这些数字界定的是 SE-GoS 在这些设置与骨干上达到的水平；ALFWorld 在那里接近饱和，这就是两项后续研究只在 SkillsBench 上运行的原因。我们不对其他骨干、也不对 200/500/2,000 技能规模作任何主张。
4. **冷启动与收敛。** 置信度加权插值（式 9）保护低证据的边，但冷启动与长时程收敛只被部分刻画，因为我们只度量到第 2、3 轮就停止了。为我们所用这类技能库恢复 I/O 字段、使 dependency 关系能够触发，仍属未来工作。

---

## 参考文献（节选）

- Agent Skills. *Agent skills*, 2026. https://github.com/agentskills/agentskills. 规范与文档仓库，访问于 2026-04-01。
- Tong Bai, Zhenglin Wan, Pengfei Zhou, Xingrui Yu, Yang You, and Ivor W. Tsang. *SkillDAG: Self-evolving typed skill graphs for LLM skill selection at scale.* arXiv:2606.03056, 2026.
- Darren Edge, et al. *From local to global: A graph RAG approach to query-focused summarization.* arXiv:2404.16130, 2024.
- Taher H. Haveliwala. *Topic-sensitive PageRank.* WWW '02, pp. 517–526, 2002. doi:10.1145/511446.511513.
- Glen Jeh and Jennifer Widom. *Scaling personalized web search.* WWW, pp. 271–279, 2003.
- Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, and Yu Su. *HippoRAG: Neurobiologically inspired long-term memory for large language models.* arXiv:2405.14831, 2024.
- Vladimir Karpukhin, et al. *Dense passage retrieval for open-domain question answering.* EMNLP 2020, pp. 6769–6781. doi:10.18653/v1/2020.emnlp-main.550.
- Patrick Lewis, et al. *Retrieval-augmented generation for knowledge-intensive NLP tasks.* NeurIPS 33:9459–9474, 2020.
- Minghao Li, et al. *API-Bank: A comprehensive benchmark for tool-augmented LLMs.* EMNLP 2023, pp. 3102–3116.
- Xiangyi Li, et al. *SkillsBench: Benchmarking how well agent skills work across diverse tasks.* arXiv:2602.12670, 2026a.
- Xiaoyuan Li, Moxin Li, Keqin Bao, Yubo Ma, Wenjie Wang, Dayiheng Liu, and Fuli Feng. *SkillGraph: Skill-augmented reinforcement learning for agents via evolving skill graphs.* arXiv:2605.12039, 2026b.
- Jianghao Lin, et al. *MassTool: A multi-task search-based tool retrieval framework for large language models.* arXiv:2507.00487, 2025.
- Dawei Liu, Zongxia Li, Hongyang Du, Xiyang Wu, Shihang Gui, Yongbei Kuang, and Lichao Sun. *Graph-of-Skills: Dependency-aware structural retrieval for massive agent skills.* arXiv:2604.05333, 2026.
- Nelson F. Liu, et al. *Lost in the middle: How language models use long contexts.* TACL, 12:157–173, 2024a. doi:10.1162/tacl_a_00638.
- Xukun Liu, et al. *ToolNet: Connecting large language models with massive tools via tool graph.* arXiv:2403.00839, 2024b.
- Zhaoyang Liu, et al. *ControlLLM: Augment language models with tools by searching on graphs.* ECCV, pp. 89–105. Springer, 2024c.
- Xuan Lu, Haohang Huang, Rui Meng, Yaohui Jin, Wenjun Zeng, and Xiaoyu Shen. *Tools are under-documented: Simple document expansion boosts tool retrieval.* ICLR, 2026.
- Grégoire Mialon, et al. *Augmented language models: A survey.* TMLR, 2023.
- Lawrence Page, Sergey Brin, Rajeev Motwani, and Terry Winograd. *The PageRank citation ranking: Bringing order to the web.* Stanford InfoLab, 1999.
- Shishir G. Patil, Tianjun Zhang, Xin Wang, and Joseph E. Gonzalez. *Gorilla: Large language model connected with massive APIs.* arXiv:2305.15334, 2023.
- Reid Pryzant, Dan Iter, Jerry Li, Yin Tat Lee, Chenguang Zhu, and Michael Zeng. *Automatic prompt optimization with "gradient descent" and beam search.* EMNLP 2023, pp. 7957–7968.
- Yujia Qin, et al. *ToolLLM: Facilitating large language models to master 16000+ real-world APIs.* ICLR, 2024.
- Changle Qu, et al. *Towards completeness-oriented tool retrieval for large language models.* CIKM, 2024.
- Timo Schick, et al. *Toolformer: Language models can teach themselves to use tools.* NeurIPS 36, 2023.
- Zhengliang Shi, et al. *Retrieval models aren't tool-savvy: Benchmarking tool retrieval for large language models.* Findings of ACL 2025, pp. 24497–24524. doi:10.18653/v1/2025.findings-acl.1258.
- Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. *Reflexion: Language agents with verbal reinforcement learning.* arXiv:2303.11366, 2023.
- Mohit Shridhar, et al. *ALFWorld: Aligning text and embodied environments for interactive learning.* arXiv:2010.03768, 2020.
- Yiqun Sun, Pengfei Wei, and Lawrence B. Hsieh. *Corpus2Skill: Distilling enterprise knowledge into navigable agent skills for QA and RAG.* Findings of EMNLP 2026. arXiv:2604.14572.
- Yu Sun, et al. *Test-time training with self-supervision for generalization under distribution shifts.* ICML, pp. 9229–9248, 2020.
- Guanzhi Wang, et al. *Voyager: An open-ended embodied agent with large language models.* arXiv:2305.16291, 2023.
- Zora Zhiruo Wang, Jiayuan Mao, Daniel Fried, and Graham Neubig. *Agent workflow memory.* ICML, vol. 267, pp. 63897–63911. PMLR, 2025.
- Qiantong Xu, et al. *On the tool manipulation capability of open-source large language models.* arXiv:2305.16504, 2023.
- Mingji Yang, Hanzhi Wang, Zhewei Wei, Sibo Wang, and Ji-Rong Wen. *Efficient algorithms for personalized PageRank computation: A survey.* IEEE TKDE, 36(9):4582–4602, 2024. doi:10.1109/TKDE.2024.3376000.
- Lifan Yuan, et al. *CRAFT: Customizing LLMs by creating and retrieving from specialized toolsets.* ICLR, 2024.
- Mert Yuksekgonul, et al. *TextGrad: Automatic "differentiation" via text.* arXiv:2406.07496, 2024.
- Andrew Zhao, et al. *ExpeL: LLM agents are experiential learners.* AAAI, vol. 38, pp. 19632–19642, 2024.
- Boyuan Zheng, et al. *SkillWeaver: Web agents can self-improve by discovering and honing skills.* arXiv:2504.07079, 2025.
- YanZhao Zheng, et al. *SkillRouter: Skill routing for LLM agents at scale.* arXiv:2603.22455, 2026.
- Yuanhang Zheng, et al. *ToolRerank: Adaptive and hierarchy-aware reranking for tool retrieval.* LREC-COLING, pp. 16263–16273, 2024.

---

## 图片与文件索引

| 图片 | 对应原文 | 说明 |
|---|---|---|
| `../images/SEGoS/01-figure1-overview-results.png` | Figure 1 | SE-GoS 概览与 SkillsBench 结果：(a) 离线轨迹驱动地更新图拓扑、边权与节点描述，虚线箭头表示可选的多轮演化；(b) deepseek-v4-flash-0731 在 SkillsBench 上的奖励柱状对比（GoS / Vanilla / Vector / SkillDAG / SE-GoS），虚线标出第 0 轮的 GoS 与第 1—3 轮的 SE-GoS。 |
| `../images/SEGoS/02-skillbench-bars.png` | Figure 1(b) 细节 | SkillsBench 奖励柱状图细节。 |

> 注：本文档与 `Externalization_2604.08224_全文详细翻译.md`、`SkillShadowing_2605.24050_全文详细翻译.md`、`ASSAY_2606.15390_全文详细翻译.md`、`Ratchet_2605.22148_全文详细翻译.md`、`HarnessCL_2608.19013_全文详细翻译.md`、`Recuris_2608.24876_全文详细翻译.md`、`MA-Memory_2603.10062_全文详细翻译.md` 同属第 8 篇《经验、技能与记忆的外部化》的配套译文。
