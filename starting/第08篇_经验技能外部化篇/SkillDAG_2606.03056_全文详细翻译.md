# SkillDAG：面向大规模 LLM 技能选择的自演化带类型技能图（SkillDAG: Self-Evolving Typed Skill Graphs for LLM Skill Selection at Scale）

> **原文标题**：SkillDAG: Self-Evolving Typed Skill Graphs for LLM Skill Selection at Scale
> **作者**：Tong Bai¹\*, Zhenglin Wan²\*, Pengfei Zhou², Xingrui Yu³‡, Yang You², Ivor W. Tsang³
> **机构**：¹复旦大学（Fudan University）、²新加坡国立大学（National University of Singapore）、³CFAR, A\*STAR
> **通讯**：yu_xingrui@a-star.edu.sg（‡ 通讯作者，\* 共同一作）
> **arXiv**：arXiv:2606.03056v2 [cs.AI]，2026 年 7 月 2 日（正文标注日期 2026-06-01）
> **代码与数据**：https://github.com/Ericbai06/SkillDAG

> **翻译说明**：本文按原文结构完整翻译。关键术语处理如下：`skill` 译为「技能」；`typed graph` 译为「带类型图」；`agent-callable` 译为「agent 可调用」；`propose-then-commit` 译为「先提议后提交」；`propose-edge / edit-edge` 保留英文（接口名）；`acyclicity / non-contradiction / append-only reversibility` 译为「无环性 / 无矛盾性 / 仅追加可回滚」；`cold-start constructor` 译为「冷启动构造器」；`two-view embedding` 译为「双视角嵌入」；`bundle` 译为「包」；`harness` 保留英文；五种边类型 `depends_on / specializes / composes_with / similar_to / conflicts_with` 保留英文原样（首次出现时给出中文释义）。表 1、表 2、图 4 的数字按原文完整保留。

---

## 摘要

随着 LLM agent 采用大型技能库，**选出正确的子集变成了一个结构性问题，而不是相似度匹配问题**：技能之间**相互依赖、冲突、特化或重复**——这一结构对全量枚举与嵌入相似度**都是不可见的**。

我们提出 **SkillDAG**，它把技能间关系建模为一张**带类型的有向图**，并把它作为一个**推理期、agent 可调用的结构化检索接口**暴露给 LLM agent——在**执行过程中被查询与演化**，而不是被固化进一条固定的检索流水线。每次 `search` 返回**向量匹配、带类型边邻居与冲突信号**，而一个**先提议后提交（propose-then-commit）协议**让 agent 能登记**有执行证据支撑的边**，使图**跨回合累积结构**。

在 MiniMax-M2.7 下的 ALFWorld 与 SkillsBench 上，SkillDAG 达到 **67.1% 成功率与 27.3% 奖励**，超过已报告最强的 Graph-of-Skills 基线 **+12.8 与 +8.6 个百分点**；该优势**可迁移到 gpt-5.2-codex**，且在匹配查询下 SkillsBench 的内在 **Ret@K 从 65.5 升到 78.2**。这些增益可归因于**可隔离的机制**：

1. **候选排序在候选池扩大 10 倍时依然稳健**，而一条固定的「播种—扩散」流水线会退化；
2. **集合单调的在线编辑扩大了真值召回率，且不驱逐先前的命中**。

**图 1  SkillDAG 的每回合工作流。** Agent 发出 `search` 得到一个三字段响应（`matches`、`neighbors`、`conflicts`），调用 `show` 取任何技能正文，在环境中行动，并可通过 `propose-edge` / `edit-edge` 这一对接口提交一条**有证据支撑的图编辑**。每次提交都通过**无环性与无矛盾性检查**，并有一个**仅追加日志**支持回滚；更新后的图馈入后续的 `search` 调用。**决定加载什么的是 LLM，而不是某个图排序策略。**

---

## 1 引言

LLM agent 越来越多地依赖外部技能库来扩展模型权重中的程序化知识之外的能力。**一个技能是一个自包含的包**：一个唯一标识符、一段说明它何时适用的自然语言描述、以及一段 agent 在被调用时运行的指令或代码正文，通常还带辅助脚本与前置条件说明 [Liu et al., 2026]。Voyager [Wang et al., 2023a]、JARVIS-1 [Wang et al., 2023b] 与 ToolLLM [Qin et al., 2024] 报告了一旦 agent 配备精选技能集合就能获得大幅增益。**当集合增长到数千条时，瓶颈从「撰写」转移到「技能选择」**：该加载哪个子集无法仅凭名称或嵌入决定，而对大型工具集合的检索本身就是 LLM agent 一个可度量的失败模式 [Shi et al., 2025]。

**实践中主导的两种策略：**

- **拼接整个技能库**：只在小规模可行——token 成本线性增长，描述会在过载提示中丢失 [Liu et al., 2024a]。
- **平铺检索**：改把任务嵌入，按余弦相似度 [Karpukhin et al., 2020, Reimers and Gurevych, 2019] 或 BM25 [Robertson and Zaragoza, 2009] 拼接 top-$K$ 技能。

**二者都掩盖了技能库的关系结构**：排名最高的匹配命名了任务，而**功能上必需的前置条件（解析器、转换器或环境准备工具）被悄悄省略**；类似的缺口还来自**共选时相互干扰的技能、浪费上下文预算的近重复项、以及只有联合起来才能提供一个单独都无法提供的能力的技能对**。精选可以在小规模掩盖这些失败，但**其成本随技能库增长**。

**已有工作建模了技能间结构，但止步于让 LLM 直接在其上推理。** SkillNet [Liang et al., 2026] 构建了一张 50 万技能的图，用于平台组织而非运行时路由。Graph of Skills [GoS; Liu et al., 2026] 在推理期于一张带类型技能图上运行 Personalized PageRank [Haveliwala, 2003, Page et al., 1999]，在 SkillsBench 与 ALFWorld 上报告了增益，**但它通过一条固定的「播种—扩散—重排」流水线计算包，并交给 agent 不透明的上下文**：它无法询问「为什么选了这个技能」、无法撤回一次噪声检索、也无法记录一条离线流水线漏掉的关系。XSkill [Jiang et al., 2026] 与 CUA-Skill [Chen et al., 2026] 分别处理技能获取与技能执行，而非技能间关系。

我们提出 **SkillDAG**，建立在**反向的设计选择**之上：**不是把图当作固定检索算法的基底，而是把图作为推理期、agent 可调用的结构化检索接口暴露给 LLM**，与 agent 已经用于执行的工具处于同等地位。**由 LLM——而不是某个图排序策略——决定结构证据应如何影响执行**；而图反过来通过**有证据支撑的 agent 编辑**跨回合累积结构知识。

### 贡献

1. 我们识别出**大规模技能库上的平铺检索会悄悄省略结构上必需的技能，并拼接冗余或相互干扰的技能**——这是一个仅靠相似度匹配看不见的失败模式。
2. 我们提出 **SkillDAG**，一个 **agent 可调用的结构化检索接口**，通过 `search`/`show`/`propose-edge`/`edit-edge` 把一张带类型技能关系图暴露给 LLM，**用一个由 agent 直接推理的结构证据来取代固定的图排序策略**。
3. 我们设计了一个**在线「先提议后提交」编辑协议**，受**三条结构不变式**约束（**无环性、无矛盾性、仅追加可回滚**），使图能从**单个回合的证据**中增长；并配以一个**双视角冷启动构造器**，用于恢复平铺自相似度会漏掉的**跨功能技能对**。
4. 在 MiniMax-M2.7 与 gpt-5.2-codex 下的 ALFWorld [Shridhar et al., 2021] 与 SkillsBench [Liu et al., 2026] 上，SkillDAG 达到 **67.1%/93.6% ALFWorld 成功率**与 **27.3%/36.8% SkillsBench 奖励**，内在 **Ret@K 为 78.2**，并在**技能池扩大 10 倍**的情况下保持稳定。

---

## 2 相关工作

**技能与工具库。** LLM agent 被外部能力增强，这些能力以工具 [Patil et al., 2024, Qin et al., 2024, Schick et al., 2023]、技能 [Wang et al., 2023a,b]、代码动作 [Liang et al., 2023, Wang et al., 2024b] 或接地的原语 [Ahn et al., 2022, Huang et al., 2022] 的形式暴露。随着技能库规模化，**瓶颈从撰写转向选择**：ToolkenGPT [Hao et al., 2023] 学习每工具嵌入，AnyTool [Du et al., 2024] 加入分层 API 检索器，CRAFT [Yuan et al., 2024] 创建并检索专门工具集，库学习方法把轨迹压缩成有文档的可复用代码 [Grand et al., 2024]。SkillNet [Liang et al., 2026] 把 50 万+ 技能组织成一张供开发者导航的图，CUA-Skill [Chen et al., 2026] 把技能建模为可执行 DAG，GraSP [Xia et al., 2026] 为任务内排序加入 DAG 修复；**它们都没有在运行时把技能间结构暴露给 agent**，因此在技能库增长时，平铺选择仍然会漏掉前置条件与冲突。

**技能检索与结构化 RAG。** 除平铺 top-$K$ RAG [Lewis et al., 2020] 之外，近期工作注入了结构：GraphRAG [Edge et al., 2024] 为离线摘要索引一张社区图，HuggingGPT [Shen et al., 2023] 在平铺目录上通过任务分解组合模型，HippoRAG [Gutiérrez et al., 2024] 通过 KG 记忆上的 Personalized PageRank 检索，LightRAG [Guo et al., 2025] 维护一个增量更新的图索引，GeAR [Shen et al., 2025] 执行 agent 驱动的图扩展。就工具而言，Re-Invoke [Chen et al., 2024] 为免样本检索改写查询，ToolGen [Wang et al., 2025] 通过工具 token 把查找折叠进生成。

**Graph of Skills [GoS; Liu et al., 2026] 是最接近的基线**：它离线构建一张带类型技能图，并通过反向感知 Personalized PageRank 检索出一个包，作为**不透明文本**拼进上下文。**SkillDAG 反转了两个选择**：

1. **图是一个 agent 可调用的结构化检索接口，而不是某个固定检索器的基底**；
2. **它的边在执行期间可被编辑，而不是在构造时被冻结**。

**自演化 agent。** ReAct [Yao et al., 2023b] 交错推理 [Wei et al., 2022] 与动作，并由审慎搜索 [Yao et al., 2023a] 扩展；Reflexion [Shinn et al., 2023] 与 Self-Refine [Madaan et al., 2023] 加入言语自我纠正；ExpeL [Zhao et al., 2024]、AutoAct [Qiao et al., 2024] 与 Agent-Pro [Zhang et al., 2024] 把经验蒸馏成可复用洞见或策略。更接近技能累积的：Agent Workflow Memory [Wang et al., 2024c] 在线归纳可复用工作流，ICAL [Sarch et al., 2024] 与 STE [Wang et al., 2024a] 把轨迹抽象成记忆，AutoGuide [Fu et al., 2024] 检索状态条件化指南，OS-Copilot [Wu et al., 2024] 在工具丰富的 OS 中累积技能；综述把这些统称为**非参数自演化** [Gao et al., 2025]。Generative Agents [Park et al., 2023] 与 MemGPT [Packer et al., 2023] 管理自由文本记忆，XSkill [Jiang et al., 2026] 更新单个技能。近期系统也**外化或压缩 agent 执行上下文**：AgentOCR 把交互历史渲染成紧凑的视觉记忆 [Feng et al., 2026]，CaveAgent 把持久运行时当作中心状态存储并集成运行时技能管理 [Ran et al., 2026]，文献 [Zhang et al., 2026] 支持现代 agent 系统的轻量部署。在具身场景中，多记忆框架类似地为长时程交互组织空间、时间、情景与语义经验 [Lei et al., 2026]。**我们的 propose-edge/edit-edge 机制改为变更一张由所有未来 agent 共享的带类型关系结构，从而实现精确、可审计的更新。**

**Agent 基准。** 我们在 ALFWorld [Shridhar et al., 2021] 与 SkillsBench [Liu et al., 2026] 上评测，这处于一个横跨跨域任务 [Liu et al., 2024b]、网页环境 [Zhou et al., 2024]、通用助手 [Mialon et al., 2024]、桌面/OS 控制 [Xie et al., 2024]、API 丰富应用 [Trivedi et al., 2024]、工具-代{理}-用户对话 [Yao et al., 2024] 与函数调用 [Patil et al., 2025] 的版图之中。它们都共享驱动 SkillDAG 的那个压力点：**在不断增长的能力表面上的检索，本身就是一个可度量的失败模式** [Shi et al., 2025]。

---

## 3 方法

### 3.1 概览

SkillDAG 从一个简单的反转出发：**带类型图并不隐藏在固定检索流水线内部，而是作为一个 agent 可调用的接口被暴露出来**，LLM 可以在执行期间查询、检视与修订它。这使**图结构成为 agent 决策上下文的一个显式部分**，而不是一个不透明的排序启发式。

带类型关系图给本来平铺的技能库赋予了**可操作的结构**：

- **前置条件边与特化边**组织可复用的递进路径；
- **组合边与相似边**浮现相邻技能；
- **冲突边**标记 agent 应当避免的组合。

`search`/`show` 接口把该结构变成动作：以**独立证据通道**的形式返回语义匹配、带类型邻居与冲突，同时**只在需要时加载完整技能正文**。

为了在任何回合运行之前初始化这样的结构，**冷启动构造器从两个互补视角连接技能**：**一个技能做什么（what a skill does）**与**它需要什么（what it needs）**。然而静态结构不可避免地不完整，因此**在线协议让 agent 在无环性、无矛盾性与仅追加可回滚三条约束下提议并提交有执行证据支撑的编辑**，防止图漂移成不连贯。

**图 3  冷启动构造。** 读取技能库 → 以两个视角嵌入每个技能（$e_{\text{self}}$ 表示它做什么，$e_{\text{needs}}$ 表示它需要什么）→ 施加自适应余弦阈值 → 运行一个 LLM 成对分类器 → 物化初始图。**`conflicts_with` 被保留给在线协议，因为共同使用造成的危害无法仅从静态文本推断。**

### 3.2 技能关系图定义

在默认检索基线（按自描述相似度排名技能并拼接 top-$K$）下，**前置条件、替代项与冲突会坍缩到同一个余弦分数上**：一个硬前置条件与一个可互换的替代项都会作为「高余弦邻居」浮现，**尽管加载前者解锁任务，而加载后者浪费上下文并稀释 agent 的注意力**。

为防止这种坍缩，我们**把关系类型本身提升为 agent 可见语义的一部分**，因此 LLM 依据**它看到的是哪一类关系**而非仅仅两个技能看起来有多相似来行动。

我们把这个原则实例化为一张带类型图。令技能库是技能包的有限集合 $C = \{s_1, \dots, s_n\}$，其中 $s_i$ 也是唯一标识符；图 $G = (V, E, \tau)$ 有 $V = C$，而类型函数 $\tau$ 给每条边赋予以下**五种操作化指定的类型**之一：

| 边类型 | 含义 |
|---|---|
| `depends_on(A, B)` | $A$ 需要前置条件 $B$。 |
| `specializes(D, A)` | $D$ 是更窄的变体，**优先于** $A$。 |
| `composes_with` | 协同共用。 |
| `similar_to` | 功能冗余（**选一个**）。 |
| `conflicts_with` | 不应共选的技能对。 |

**两条操作约束使这张带类型图可作为面向 agent 的接口使用：**

**(1) 冲突是剪枝信号，而非导航边。** 我们**刻意把 `conflicts_with` 排除在遍历之外**，因为导航一条冲突边会主动破坏检索——它会浮现那些 LLM 已被告知要避免的技能。四种正向类型会被检索接口遍历，而 `conflicts_with` 只用于排除共选（3.3 节）。

**(2) 骨架上的无环性。** 我们把 `depends_on` 与 `specializes` 保留为有向骨架，**其无环性赋予了 SkillDAG 这个名字**；该不变式在提交时强制（3.5 节）。

**图 2** 展示了一个跑完后的 ALFWorld 图的**六节点子图**，它使用了全部五种带类型关系：冷启动的 `specializes`/`similar_to` 边，加上 agent 登记的 `depends_on`，以及同一对技能上后来的 `conflicts_with`。

### 3.3 Agent 可调用的结构化检索接口

给边加上类型之后，我们必须决定**如何在推理期把图暴露给 agent**。**已有图检索器的默认做法是把带类型结构再坍缩回一个排好序的包**，但这样做会**抵消 3.2 节的工作**——恰恰把我们构建这张图所要保留的那些区分**藏起来不给 LLM 看**。

因此我们把 `search`（图 1）设计为一个 **agent 可调用的接口**，它把**语义匹配、带类型邻居与冲突**作为**三个独立证据通道**返回，供 LLM 独立推理。

一次 `search(q, K, D)` 调用返回三个字段，每个回答一个 LLM 否则必须单独提出的问题：

| 字段 | 回答的问题 | 内容 |
|---|---|---|
| **`matches`** | 「什么与 $q$ 主题上接近？」 | 按查询–节点嵌入余弦排名的 top-$K$ 技能 [Karpukhin et al., 2020]。 |
| **`neighbors`** | 「带类型图附着在这些匹配上的是什么？」 | 在**四种可遍历边类型**上做深度 $D$ 的有界广度优先遍历所到达的技能。 |
| **`conflicts`** | 「我不应该与它们共载什么？」 | 与任何匹配相邻的一跳 `conflicts_with` 边。 |

**我们选择把这些通道分开，而不是融合成单一分数**，因为这种分解给了 agent 三项排序后的包无法提供的能力：

1. **它可以在上下文预算紧张时丢弃整个字段**（例如上下文稀缺时跳过 `neighbors`）；
2. **它可以自主安排 `search` 调用的时机**（例如在部分进展之后重新查询）；
3. **它可以留下一条记录「为何每个技能被选中或排除」的推理轨迹。**

### 3.4 冷启动图构造

3.3 节的接口假设图已经存在；现在我们描述它**在 agent 首次运行之前**是如何被首次填充的。

显然的选择（嵌入每个技能的自描述并连接最近邻）有一个我们专门要修复的失败模式：**应当被连接的技能往往描述的是不同的动作，其中一方提供另一方所需的东西。** 例如一个**降温技能**与一个**拿起技能**的自描述互不相交，然而降温技能需要由拿起技能产生的「手中持有对象」。**仅靠自描述相似度会系统性地漏掉这类跨功能对**，因此我们设计了一个**双视角嵌入策略**，在从静态 `SKILL.md` 文本初始化图的同时，**显式恢复这些桥接**。

与单视角检索的关键区别是**第二个嵌入**。对每个技能 $v$：

- $e_{\text{self}}(v)$ 捕捉**一个技能做什么**（标识符、描述、正文预览）；
- $e_{\text{needs}}(v)$ 捕捉**它需要什么**：一个 LLM 想象若干调用任务，并把共享的前置条件汇总成一句话（HyDE 风格 [Gao et al., 2023]），然后嵌入该摘要。

$e_{\text{self}}$ 浮现主题邻居，$e_{\text{needs}}$ 浮现功能桥接；**只要任一排名超过自适应余弦阈值，候选对就出现**。随后一个 LLM 分类器 [Zheng et al., 2023] 赋四种静态类型之一或不分类型。

**我们出于操作上的必要性把 `conflicts_with` 保留给在线协议（3.5 节）**：冲突按定义是「共用会可预期地降低成功率」的技能对，**而该证据在执行被观测到之前根本不存在。再多的静态阅读也恢复不了它。**

### 3.5 在线图演化

即便一张构造良好的冷启动图也**必然不完整**。按刚才的论证，它**根本不可能包含 `conflicts_with` 边**；更广泛地说，许多有用的关系只在执行期间出现：一个冷启动 LLM 未预料到的前置条件、一个只有在两个技能被一起加载时才可观测的干扰对、一次近似失误之后对已有关系的精化。

为弥合这一缺口，我们**把图构造变成 agency 的在线组成部分，而不是离线预处理**：图 1 的每回合循环包含 `propose-edge`/`edit-edge` 这一对，**agent 以与环境行动相同的节奏提交有证据支撑的编辑**。

**我们把编辑拆成两次调用**，使提交始终是一个**审慎的行为**，而不是执行的副作用：

- **`propose-edge`** 执行一次**演练**：它预览改动，并浮现同一技能对已有的边与历史，使 agent 能推理是否提交。
- **`edit-edge`** 随后用一个**自然语言理由与支撑性执行轨迹**提交改动；同一次调用可以**新增、删除或重设**一条已有边的类型，**给 agent 一条对陈旧或错误关系的显式撤回路径**。

我们**刻意只以 agent 自己的推理来把守提交**，而不是下游投票阈值或人类策展人，**以便单个执行回合就足够**，图以 **agent 速度而非策展速度**演化。图 2 中重复出现的那一对技能说明了为什么预览要浮现「配对历史」：一个后来的 `conflicts_with` 决定必须与**同一对技能上更早的 `depends_on` 证据**放在一起评估。

**仅以 agent 推理把守提交会抬高「单次污染」的风险**，我们用**三条每次提交都必须通过的结构不变式**来限制它；这些不变式的选择目的是**限制一次坏编辑的爆炸半径，而不去二次猜测 agent 的语义判断**：

| 不变式 | 内容 | 为何是结构性的 |
|---|---|---|
| **无环性（acyclicity）** | 一次会闭合骨架环的 `depends_on`/`specializes` 提交被拒绝 | 循环的前置条件链会让 agent 在「每个都要求下一个」的技能之间打转，使 3.2 节声明的 DAG 属性失效。 |
| **无矛盾性（non-contradiction）** | 一对技能不能同时携带 `conflicts_with` 与一条正向浮现边 | 防止导航信号与剪枝信号相互抵消。 |
| **可回滚性（reversibility）** | 一个仅追加的历史日志支持按新近度回滚 | 使一次伪编辑**有界且可恢复**。 |

**这些不变式按设计是结构性的而非语义性的**：它们**保留 LLM 对每条边含义的权威**，同时防止图漂移成不连贯。

---

## 4 实验

我们的评测追问四个关于接口设计**何时、为何**奏效的引导性问题：

1. 我们先在**端任务奖励**上把 SkillDAG 与全库提示、向量检索和 GoS 对比——这是「agent 可调用图访问确实胜过主导基线」的最强指标。
2. 随后**把相同的查询重放进两个检索器**，隔离出「在任何下游执行之前就已经可见」的那部分增益。
3. 对比 MiniMax-M2.7 与 gpt-5.2-codex，展示**该效应如何随骨干推理强度变化**。
4. 最后用一个 **10 倍技能池扩张**与一个 **ALFWorld 训练/测试切分**，度量**检索是否在规模上保持稳健，以及在线编辑能否迁移到留出回合**。

### 4.1 实验设置

**基准。** 我们在 Liu et al. [2026] 所用的两个基准上评测，它们检验大规模技能选择的不同侧面。

- **ALFWorld** [Shridhar et al., 2021]：一个基于文本的具身环境，其六种任务类型（拾取并放置、在光下检查、清洁并放置、加热并放置、降温并放置、拾取两件并放置）需要组合导航、操作与状态变更行为；我们运行 **140 回合的 `valid_seen` 切分**，配一个 **37 技能的程序化技能库**。
- **SkillsBench** [Liu et al., 2026]：87 个容器化代码生成任务，按单元测试通过比例计分，以**四种技能池规模（200/500/1000/2000 个 `SKILL.md` 文档）**发布，因此可以在池增长时研究检索质量。

**基线。** 我们对比 Liu et al. [2026] 的三个基线：

| 基线 | 说明 |
|---|---|
| **Vanilla Skills** | 把整个技能库放进提示，并通过 ReAct [Yao et al., 2023b] 行动（召回上界与上下文成本参照）。 |
| **Vector Skills** | 拼接 top-$K$ 嵌入余弦匹配，**不使用任何图结构**。 |
| **Graph of Skills (GoS)** | 通过混合语义—词法播种加带类型图上的反向感知 Personalized PageRank 检索出一个包，在 token 预算下重排，然后拼接进提示。 |
| **SkillDAG（本文）** | 把图暴露为 agent 可调用的结构化检索接口：agent 在执行期间发出 `search`/`show`/`propose-edge`/`edit-edge`，依据三字段搜索响应行动，并在护栏检查下提交有证据支撑的边。 |

**模型与评测。** 我们报告每回合奖励 $R$（%）；对 ALFWorld，$R$ 等于成功率。Vanilla/Vector/GoS 的 $R$ 行（MiniMax-M2.7 与 gpt-5.2-codex 两者）**引自 Liu et al. [2026] 表 1，未在本地重跑**；SkillDAG 的 $R$ 行是我们自己在相同基准、骨干、任务数据与技能池上的运行，**但不是与基线配对的同种子重跑**。内在检索列由我们在**相同输入**上计算：SkillDAG agent 在其 87 任务运行期间实际发出的 `search` 查询，由各流水线在 **scale-1000 池**上评测（$n=140$ ALFWorld 回合、$n=87$ SkillsBench 任务）。

### 4.2 主结果

表 1 报告两个基准、两个骨干上的任务奖励与内在检索。

**SkillDAG 在 MiniMax-M2.7 下改善最多**：ALFWorld **54.3 → 67.1（+12.8）**、SkillsBench **18.7 → 27.3（+8.6）**；而在 gpt-5.2-codex 下 ALFWorld **打平于 93.6%**、SkillsBench 收窄为 **34.4 → 36.8（+2.4）**。**「路由辅助」的签名在骨干无法越过一个糟糕的包进行推理时很大，而一旦它能，该签名就消失。**

**内在 SkillsBench 检索**在同样的 MiniMax 查询分布上也优于 GoS：**Ret@K 65.5 → 78.2、Ret@1 50.6 → 66.7、MRR 57.3 → 71.3**，这**在任何 agent 侧执行之前**就隔离出一条检索流水线的增益；在嵌入与查询固定的情况下，**SkillDAG 基于带类型图节点嵌入的 `matches` 字段余弦，比 GoS 的 HNSW [Malkov and Yashunin, 2020] 播种 + PPR [Page et al., 1999] 扩散排序得更准**。

在 gpt-5.2-codex 上，SkillDAG 在 ALFWorld 与 GoS 打平（93.6%），在 SkillsBench 上仍是最优（36.8%），并在 codex 轨迹查询上得到 **75.9/70.1/73.0 的 Ret@5/Ret@1/MRR**。

**表 1  主结果。** $R$ = 奖励（%）；ALFWorld 的 $R$ = 成功率。SkillsBench 的 $R$ 为 1000 技能规模。Ret@K / Ret@1 / MRR（↑）为内在检索指标。Vanilla/Vector/GoS 的 $R$ 引自 Liu et al. [2026] 表 1；SkillDAG 的 $R$ 来自我们自己的运行。每列最优加粗。

| 模型 | 方法 | SkillsBench R↑ | SkillsBench Ret@K↑ | SkillsBench Ret@1↑ | SkillsBench MRR↑ | ALFWorld R↑ | ALFWorld Ret@K↑ | ALFWorld Ret@1↑ | ALFWorld MRR↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **MiniMax-M2.7** | Vanilla Skills | 17.2 | – | – | – | 47.1 | – | – | – |
| | Vector Skills | 10.4 | 10.8 | 3.6 | 5.8 | 50.7 | 68.6 | 37.9 | 49.2 |
| | GoS | 18.7 | 65.5 | 50.6 | 57.3 | 54.3 | 86.4 | 56.4 | 67.9 |
| | **SkillDAG** | **27.3** | **78.2** | **66.7** | **71.3** | **67.1** | **92.1** | 57.9 | **71.1** |
| **gpt-5.2-codex** | Vanilla Skills | 27.4 | – | – | – | 89.3 | – | – | – |
| | Vector Skills | 21.5 | 10.8 | 3.6 | 5.8 | 92.9 | 68.6 | 37.9 | 49.2 |
| | GoS | 34.4 | 65.5 | 50.6 | 57.3 | **93.6** | 86.4 | 56.4 | 67.9 |
| | **SkillDAG** | **36.8** | **75.9** | **70.1** | **73.0** | **93.6** | 85.1 | **60.4** | **69.6** |

### 4.3 规模与编辑迁移消融

我们隔离主结果背后的两个效应：**agent 的在线编辑是否作为持久、召回安全的结构留存下来**，以及**带类型图检索器是否随技能池增长保持稳健**。

我们用两种方式度量在线编辑：一个 **ALFWorld 训练/测试切分**，测试**已提交的边能否迁移**；以及一个 **SkillsBench 冷启动 vs 编辑后的查询重放**，测试**一条被接受的边对检索召回做了什么**（表 2）。

**表 2  SkillsBench scale-1000 检索，重放来自 65 个任务的 316 条 `search` 查询，对照冷启动图与编辑后的图。**「Mean GT/q」是每查询检索到的真值技能平均数量（平均真值规模 2.52 技能/任务）。

| 图 | 边数 | Mean GT/q |
|---|---:|---:|
| 冷启动 | 2,359 | 1.915 |
| 编辑后（+27 条在线编辑） | 2,386 | **1.984** |

**(a) 已提交的边作为持久结构留存。** 一次 **420 回合的域内训练**运行累积编辑；随后在**禁用编辑**的情况下运行 test-initial（140 个留出回合，冷启动图）与 test-edited（同样的 140 个，但用训练产出的图）。在两个骨干上，训练与 test-initial 的差距都在 **2.1 个百分点以内**（MiniMax-M2.7：67.1/65.0/67.1%；gpt-5.2-codex：92.3/90.7/93.6%；图 4a）：**迁移在留出切分上成立，且 test-edited 恢复到训练的数字**，因此已提交的边**作为持久结构留存，而不是训练时的随机性**。

**(b) 在线编辑以集合单调的方式扩大真值召回。** 重放全部 316 条 scale-1000 查询，编辑后的图（+27 条单次观测提交）每查询检索到更多真值技能（**1.984 vs 1.915**；表 2），且**零条查询丢失任何真值检索**。这**按构造成立**：打分器取 `matches` 与 BFS 邻居的**未截断并集**，因此一条被接受的边**只能扩大被检索集合，绝不会驱逐冷启动图已经浮现过的真值技能**；**这是一个召回性质，不是上下文预算主张**。

**(c) SkillDAG 排序在技能池扩大 10 倍时保持稳健。** 在嵌入骨干固定的情况下，SkillDAG 仅靠 `matches` 余弦就在**每个技能池规模的每个检索指标上**胜过 GoS，**尽管不使用任何扩散步骤**：200 技能时 **+16.1/+17.2/+17.2**（Ret@5/Ret@1/MRR），2000 时 **+13.8/+16.1/+16.3**，在 500 时差距最窄（**+4.6/+6.9/+6.3**）——那里 GoS 的 PPR 拉力恰好与金标语目标对齐；在整个 10 倍池扩张中它只损失 **3.5 个 Ret@5 点（78.2 → 74.7）**，**稳健地扩展到更大的技能库**（图 4b）。这隔离出的是**离线检索流水线**，而不是 agent 在执行期间使用的**带类型边 `neighbors`/`conflicts` 字段**。

**图 4  稳健性实验。**

- **(a) ALFWorld 成功率（%）**，跨 Train（420 个域内回合，编辑开启）、Test-initial（140 个留出回合，在冷启动图上）、Test-edited（同样的 140 个，在训练产出的图上），两个骨干。MiniMax-M2.7：67.1 / 65.0 / 67.1；gpt-5.2-codex：92.3 / 90.7 / 93.6。
- **(b) 跨规模检索（SkillsBench）。** 同样的 87 条 SkillDAG 查询通过两个检索器，共享 `text-embedding-3-large`；SkillDAG 在每个规模上都排名高于 GoS，并在 10 倍扩张中保持平稳；scale-1000 与表 1 的 MiniMax 行一致。三条曲线：Ret@5（SkillDAG 78.2/78.2/78.2/74.7 vs GoS PPR 62.1/73.6/65.5/60.9）、Ret@1（67.8/67.8/66.7/58.6 vs 50.6/60.9/50.6/42.5）、MRR（72.3/72.1/71.3/65.6 vs 55.1/65.8/57.3/49.3）。

---

## 5 结论

SkillDAG 把一张带类型技能关系图暴露为 **agent 可调用的结构化检索接口**（`search`/`show`/`propose-edge`/`edit-edge`），而不是把它藏在某个固定的图排序策略里。**Agent 只加载它需要的带类型邻居与技能正文**，避免了「固定包检索器用勉强相关的技能淹没提示、进而污染下游推理」这一**上下文膨胀失败**。

相对 GoS，SkillDAG 提升了 MiniMax-M2.7 在 ALFWorld（**54.3 → 67.1**）与 SkillsBench（**18.7 → 27.3**）上的奖励，且 `matches` 字段检索**在每个技能池规模的每个指标上都胜出**——这支持了那条反转主张：**图作为路由决策的接口，比作为一个不透明的策略更为有效。**

## 局限

**先提议后提交协议是刻意由 agent 驱动的**：单个执行观测就足以让 agent 提交一条边，其界限是**结构性护栏**（无环性、无矛盾性、可回滚性）而非统计置信阈值（3.5 节）。聚合编辑效应已被报告（4.3 节），但**单次观测自演化的长时程行为仍是一个开放问题**，我们把它视为未来工作的方向。

---

## 参考文献（节选）

- Michael Ahn, et al. *Do as I can, not as I say: Grounding language in robotic affordances.* CoRL, 2022.
- Tianyi Chen, et al. *CUA-Skill: Develop skills for computer using agent.* arXiv:2601.21123, 2026.
- Yanfei Chen, et al. *Re-Invoke: Tool invocation rewriting for zero-shot tool retrieval.* Findings of EMNLP, 2024.
- Yu Du, Fangyun Wei, and Hongyang Zhang. *AnyTool: Self-reflective, hierarchical agents for large-scale API calls.* ICML, 2024.
- Darren Edge, et al. *From local to global: A graph RAG approach to query-focused summarization.* arXiv:2404.16130, 2024.
- Lang Feng, et al. *AgentOCR: Reimagining agent history via optical self-compression.* 2026. arXiv:2601.04786.
- Yao Fu, et al. *AutoGuide: Automated generation and selection of context-aware guidelines for large language model agents.* NeurIPS, 2024.
- Huan-ang Gao, et al. *A survey of self-evolving agents: What, when, how, and where to evolve on the path to artificial super intelligence.* arXiv:2507.21046, 2025.
- Luyu Gao, Xueguang Ma, Jimmy Lin, and Jamie Callan. *Precise zero-shot dense retrieval without relevance labels.* ACL, 2023.
- Gabriel Grand, et al. *LILO: Learning interpretable libraries by compressing and documenting code.* ICLR, 2024.
- Zirui Guo, et al. *LightRAG: Simple and fast retrieval-augmented generation.* Findings of EMNLP, 2025.
- Bernal Jiménez Gutiérrez, et al. *HippoRAG: Neurobiologically inspired long-term memory for large language models.* NeurIPS, 2024.
- Shibo Hao, et al. *ToolkenGPT: Augmenting frozen language models with massive tools via tool embeddings.* NeurIPS, 2023.
- Taher H. Haveliwala. *Topic-sensitive PageRank.* IEEE TKDE, 15(4):784–796, 2003.
- Wenlong Huang, et al. *Inner monologue: Embodied reasoning through planning with language models.* CoRL, 2022.
- Guanyu Jiang, Zhaochen Su, Xiaoye Qu, and Yi R. Fung. *XSkill: Continual learning from experience and skills in multimodal agents.* arXiv:2603.12056, 2026.
- Vladimir Karpukhin, et al. *Dense passage retrieval for open-domain question answering.* EMNLP, 2020.
- Mingcong Lei, et al. *RoboMemory: A brain-inspired multi-memory agentic framework for interactive environmental learning in physical embodied systems.* 2026. arXiv:2508.01415.
- Patrick Lewis, et al. *Retrieval-augmented generation for knowledge-intensive NLP tasks.* NeurIPS, 2020.
- Jacky Liang, et al. *Code as policies: Language model programs for embodied control.* ICRA, 2023.
- Yuan Liang, et al. *SkillNet: Create, evaluate, and connect AI skills.* arXiv:2603.04448, 2026.
- Dawei Liu, Zongxia Li, Hongyang Du, Xiyang Wu, Shihang Gui, Yongbei Kuang, and Lichao Sun. *Graph of Skills: Dependency-aware structural retrieval for massive agent skills.* arXiv:2604.05333, 2026.
- Nelson F. Liu, et al. *Lost in the middle: How language models use long contexts.* TACL, 12:157–173, 2024a.
- Xiao Liu, et al. *AgentBench: Evaluating LLMs as agents.* ICLR, 2024b.
- Aman Madaan, et al. *Self-Refine: Iterative refinement with self-feedback.* NeurIPS, 2023.
- Yu A. Malkov and Dmitry A. Yashunin. *Efficient and robust approximate nearest neighbor search using HNSW graphs.* IEEE TPAMI, 42(4):824–836, 2020. doi:10.1109/TPAMI.2018.2889473.
- Grégoire Mialon, et al. *GAIA: A benchmark for general AI assistants.* ICLR, 2024.
- Charles Packer, et al. *MemGPT: Towards LLMs as operating systems.* arXiv:2310.08560, 2023.
- Lawrence Page, Sergey Brin, Rajeev Motwani, and Terry Winograd. *The PageRank citation ranking: Bringing order to the web.* Stanford InfoLab, 1999.
- Joon Sung Park, et al. *Generative agents: Interactive simulacra of human behavior.* UIST, 2023.
- Shishir G. Patil, et al. *Gorilla: Large language model connected with massive APIs.* NeurIPS 37:126544–126565, 2024. doi:10.52202/079017-4020.
- Shishir G. Patil, et al. *The Berkeley Function Calling Leaderboard (BFCL).* ICML, 2025.
- Shuofei Qiao, et al. *AutoAct: Automatic agent learning from scratch for QA via self-planning.* ACL, 2024.
- Yujia Qin, et al. *ToolLLM: Facilitating large language models to master 16000+ real-world APIs.* ICLR, 2024.
- Maohao Ran, et al. *CaveAgent: Transforming LLMs into stateful runtime operators.* 2026. arXiv:2601.01569.
- Nils Reimers and Iryna Gurevych. *Sentence-BERT: Sentence embeddings using siamese BERT-networks.* EMNLP, 2019.
- Stephen Robertson and Hugo Zaragoza. *The probabilistic relevance framework: BM25 and beyond.* Foundations and Trends in IR, 3(4):333–389, 2009.
- Gabriel Sarch, et al. *VLM agents generate their own memories: Distilling experience into embodied programs of thought.* NeurIPS, 2024.
- Timo Schick, et al. *Toolformer: Language models can teach themselves to use tools.* NeurIPS, 2023.
- Yongliang Shen, et al. *HuggingGPT: Solving AI tasks with ChatGPT and its friends in Hugging Face.* NeurIPS, 2023.
- Zhili Shen, et al. *GeAR: Graph-enhanced agent for retrieval-augmented generation.* Findings of ACL, 2025.
- Zhengliang Shi, et al. *Retrieval models aren't tool-savvy: Benchmarking tool retrieval for large language models.* arXiv:2503.01763, 2025.
- Noah Shinn, et al. *Reflexion: Language agents with verbal reinforcement learning.* NeurIPS, 2023.
- Mohit Shridhar, et al. *ALFWorld: Aligning text and embodied environments for interactive learning.* ICLR, 2021.
- Harsh Trivedi, et al. *AppWorld: A controllable world of apps and people for benchmarking interactive coding agents.* ACL, 2024.
- Boshi Wang, et al. *LLMs in the imaginarium: Tool learning through simulated trial and error.* ACL, 2024a.
- Guanzhi Wang, et al. *Voyager: An open-ended embodied agent with large language models.* NeurIPS, 2023a.
- Renxi Wang, et al. *ToolGen: Unified tool retrieval and calling via generation.* ICLR, 2025.
- Xingyao Wang, et al. *Executable code actions elicit better LLM agents.* ICML, 2024b.
- Zhiruo Wang, Jiayuan Mao, Daniel Fried, and Graham Neubig. *Agent Workflow Memory.* arXiv:2409.07429, 2024c.
- Zihao Wang, et al. *JARVIS-1: Open-world multi-task agents with memory-augmented multimodal language models.* 2023b.
- Qingyun Wu, et al. *OS-Copilot: Towards generalist computer agents with self-improvement.* 2024.
- Tianbao Xie, et al. *OSWorld: Benchmarking multimodal agents for open-ended tasks in real computer environments.* 2024.
- Xiaohan Xia, et al. *GraSP: Graph-based skill planning.* 2026.
- Shunyu Yao, et al. *Tree of Thoughts: Deliberate problem solving with large language models.* NeurIPS, 2023a.
- Shunyu Yao, et al. *ReAct: Synergizing reasoning and acting in language models.* ICLR, 2023b.
- Shunyu Yao, et al. *τ-bench: A benchmark for tool-agent-user interaction in real-world domains.* 2024.
- Lifan Yuan, et al. *CRAFT: Customizing LLMs by creating and retrieving from specialized toolsets.* ICLR, 2024.
- Zhuosheng Zhang, et al. *Agent-Pro: Learning to evolve via policy-level reflection and optimization.* ACL, 2024.
- Ye Zhang, et al. 2026.（现代 agent 系统的轻量部署）
- Lianmin Zheng, et al. *Judging LLM-as-a-judge with MT-Bench and Chatbot Arena.* NeurIPS, 2023.
- Shuyan Zhou, et al. *WebArena: A realistic web environment for building autonomous agents.* ICLR, 2024.
- Jian Zhao, et al. *ExpeL: LLM agents are experiential learners.* AAAI, 2024.

---

## 图片与文件索引

| 图片 | 对应原文 | 说明 |
|---|---|---|
| `../images/SkillDAG/01-figure1-workflow.png` | Figure 1 | SkillDAG 的每回合工作流：`search` 返回三字段（`matches`/`neighbors`/`conflicts`）→ `show` 取技能正文 → 在环境中行动 → 通过 `propose-edge`/`edit-edge` 提交有证据支撑的图编辑 → 通过无环性与无矛盾性检查 + 仅追加日志支持回滚 → 更新后的图馈入后续 `search`。 |
| `../images/SkillDAG/02-figure2-subgraph.png` | Figure 2 | 跑完后的 ALFWorld 图的一个六节点子图，使用了全部五种带类型关系：冷启动的 `specializes`/`similar_to` 边，加上 agent 登记的 `depends_on`，以及同一对技能上后来的 `conflicts_with`。 |
| `../images/SkillDAG/03-figure3-coldstart.png` | Figure 3 | 冷启动构造流程：读取技能库 → 双视角嵌入（$e_{\text{self}}$ / $e_{\text{needs}}$）→ 自适应余弦阈值 → LLM 成对分类器 → 物化初始图。`conflicts_with` 保留给在线协议。 |
| `../images/SkillDAG/04-figure4-robustness.png` | Figure 4 | 稳健性实验：(a) ALFWorld 训练/测试切分成功率；(b) SkillsBench 跨规模检索（Ret@5 / Ret@1 / MRR，200/500/1000/2000 技能池，SkillDAG vs GoS PPR）。 |

> 注：本文档与 `SkillEvolBench_2605.24117_全文详细翻译.md`、`SkillMisevolve_2608.12851_全文详细翻译.md`、`SEGoS_2609.08228_全文详细翻译.md`、`Externalization_2604.08224_全文详细翻译.md`、`SkillShadowing_2605.24050_全文详细翻译.md`、`ASSAY_2606.15390_全文详细翻译.md`、`Ratchet_2605.22148_全文详细翻译.md`、`HarnessCL_2608.19013_全文详细翻译.md`、`Recuris_2608.24876_全文详细翻译.md`、`MA-Memory_2603.10062_全文详细翻译.md` 同属第 8 篇《经验、技能与记忆的外部化》的配套译文。
