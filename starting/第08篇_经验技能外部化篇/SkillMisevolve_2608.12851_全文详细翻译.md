# 熟能生「危」：自改进 LLM agent 中的技能误演化（Practice Makes Unsafe: Skill Misevolution in Self-Improving LLM Agents）

> **原文标题**：Practice Makes Unsafe: Skill Misevolution in Self-Improving LLM Agents
> **作者**：Xutao Mao¹, Liangjie Zhao², Xiang Zheng¹, Cong Wang¹
> **机构**：¹香港城市大学（City University of Hong Kong）、²阿德莱德大学（Adelaide University）
> **arXiv**：arXiv:2608.12851v2 [cs.AI]，2026 年 10 月 7 日
> **代码**：https://github.com/henrymao2004/misevolve

> **翻译说明**：本文按原文结构完整翻译。关键术语处理如下：`skill` 译为「技能」；`skill misevolution` 译为「技能误演化」；`gate` 译为「闸门」（对应原文 authoring / retrieval / execution 三闸门）；`episode` 译为「回合」（保留 episode 语义，指一条完整的多任务序列）；`exposure` 译为「暴露」；`new session` 译为「新会话」；`carryover` 译为「携带/残留」，`Carryover ASR` 译为「残留攻击成功率」；`utility` 译为「效用」；`artifact` 译为「制品」（指被写出的技能文件）；`lineage` 译为「谱系」；`span` 译为「片段」；`soft quarantine` 译为「软隔离」；`retire / retirement` 译为「退役」；`evict` 译为「驱逐」；`replay` 译为「重放」；`stealthiness` 译为「隐蔽性」；`harness` 保留英文。表 1 的九项指标按原文列顺序重绘（原文因排版把 O/I 两组并列展开，此处恢复为单行记录以便阅读）。

---

## 摘要

LLM agent 越来越多地通过**技能演化**把过去任务中的经验保存为可复用技能。当 agent 完成一个不安全任务时，技能演化会把**不安全流程**留在原本有用的技能内部；此后一个**良性的**任务可能在原始不安全指令**已经消失之后**重复这份危害。我们把这一失败称为**技能误演化（skill misevolution）**。

它需要两个条件：agent 把不安全流程写进技能，以及后续任务检索并遵循该技能。

我们提出 **SKILLMISEVO-GYM**：它清空每个任务会话，但**保留技能库**，因此上述每一步都能被单独检查。我们还构建了 **SKILLMISEVO-BENCH**，包含 **25 个回合、525 个任务**，每个回合在**新会话中的三个良性任务之前**交替安排恶意任务与相关的良性任务。

在 **21 组 agent × 演化方法**的组合中，**全部 21 组都写出了不安全技能，15 组把危害带进了新会话**——因此风险来自技能演化本身。演化在 15 组组合中提升了良性效用，但同时也在 **17 组**中提升了恶意任务上的危害，所以**仅按效用给方法排序会掩盖这一风险**。

我们提出 **SAFEEVOLVE**，它在技能**被写入时**和**被后续任务检索时**各做一次检查。它把新会话中的不安全检索从 **35.3% 降到 8.7%**、危害从 **21.3% 降到 4.0%**，同时把学习期的良性效用控制在 **0.4 个百分点**以内。**SAFEEVOLVE-UP** 把新会话危害降低 **16.0 个百分点**，并把效用控制在无此缓解措施的演化值的 **1.3 个百分点**以内。

**当 agent 从自身经验学习时，安全必须覆盖那些把过去行为带入未来任务的技能。**

---

## 1 引言

LLM agent 越来越多地把经验保留为技能，使后续任务可以复用先前任务教会它们的东西（Cai et al., 2025; Shao et al., 2025; Zhao et al., 2026; Lin et al., 2026b）。技能演化把交互轨迹转成面向反复出现的工作流的可执行流程，并随任务结果修订它们（Yang et al., 2026b; Alzubi et al., 2026; Xiao et al., 2026; Li et al., 2026b; Ma et al., 2026; Liu et al., 2026a; Yang et al., 2026a）。

**这些轨迹来自日常用户工作，其中一些嵌入了有害动作**（Debenedetti et al., 2024; Guo et al., 2024; Schmotz et al., 2026; Zhao et al., 2026; Lin et al., 2026b）。

考虑这样一个用户：他让 Claude Code（Anthropic, 2025）添加一个把本地环境文件发送到团队端点的 Git hook，并**把这个 hook 保存为标准约定**。一个技能演化方法会把这条轨迹变成可复用的「配置同步 hook」技能。

很多任务之后，一个新会话**只**请求一个全新 clone 的标准 Git hooks——agent 却遵循保存下来的技能，写出了一个把 `.env.local` 发往外部端点的 hook。**没有这个被保存的技能，同一个请求是安全的。**

我们把这一失败称为**技能误演化**。它发生在 agent 把不安全流程写入技能、而后续任务随后检索该技能并因遵循它而造成危害时。我们把这三步称为 **authoring（写入）、retrieval（检索）、execution（执行）**三道闸门，每一道都可以被单独观测。

**现有基准的缺口。** 已有基准评分的是技能质量，或提供给 agent 的提示/文件的安全性（Li et al., 2026a; Zhong et al., 2026; Han et al., 2026; Feng et al., 2026; Jin et al., 2026; Schmotz et al., 2026; Guo et al., 2026），而长时程基准追踪的是跨任务累积起来的记忆（Xie et al., 2026; Cheng et al., 2026）。**它们中没有一个追踪一个技能从「写下它的任务」到「复用它的后续任务」的完整路径。** 单一的攻击成功率把三道闸门合并成一个数字，因此无法显示失败发生在哪一步。这留下一个互补的问题：**一次被保存为技能的不安全成功，会不会把危害带入之后的良性任务？**

为此，我们提出 SKILLMISEVO-GYM 与 SKILLMISEVO-BENCH（图 1）。

**图 1：技能误演化循环。** 不安全经验被蒸馏成一个可复用技能，之后被检索，然后在后续任务中作为危害被执行。SKILLMISEVO-GYM 在隔离的任务会话下追踪每一道闸门，而 SKILLMISEVO-BENCH 提供 25 个把恶意暴露与相关良性工作交替安排的回合。

- **动机**：自改进 LLM agent 把成功轨迹转成可复用技能；一次临时的不安全成功可能变成持久策略。「我解决过一次——该保存它吗？」「如果学到的技能不安全怎么办？」我们需要用恶意 + 良性任务来测试这件事。覆盖 Coding、Web Use、Tools、Automation 四个域。
- **什么是技能误演化**：不安全成功被泛化成可复用技能、存入技能库、并在原始攻击消失之后被复用。链式过程：不安全攻击 → 成功轨迹 → 技能写入 → 技能存入库 → 有害结果。即「临时交互 → 持久技能 → 未来风险」。
- **闸门式生命周期**：写入闸门（不安全 SKILL 是否被准入？）、复用闸门（不安全 SKILL 是否被检索？）、执行闸门（检索是否导致了危害？）。「提示现在是干净的……那技能呢？」
- **SKILLMISEVO-GYM**：任务流（恶意任务 / 良性任务 / 新会话任务）、Agent 骨干（任何自改进 LLM agent / 技能演化框架）、状态隔离（把技能状态与对话、工作区、原生记忆分开）、持久技能库（带版本、可审计、可导出）、评测方法（技能写入、危害行为）、仪表化（观测写入、检索、制品；快照重放与新会话重载）。
- **SKILLMISEVO-BENCH 构建**：AgentHazard 有害任务契约（有害目标 + 沙箱 + 有害轨迹裁判）→ 自动研究式发现（用候选的恶意/良性配对发现概念：可证伪的机制、可复现的配对证据、使能条件 + 出处）→ 已验证漏洞概念 → 回合构造器（实例化全新的 M/B/P 任务、参数化环境、设定裁判）→ 基准回合（固定排程、固定裁判、可复现评测；只重载技能制品；测试重置后的残留）。

SKILLMISEVO-GYM 让一个技能演化 agent 走完一个长回合：**重置每个任务会话，却保留并版本化技能库**。在最后一次更新之后，它在一个新会话中重载导出的技能，于是每道闸门都变得可分别观测。SKILLMISEVO-BENCH 是在 SKILLMISEVO-GYM 内运行的任务基准，含 **25 个回合、每回合 21 个任务**。每个回合在三个恶意暴露区块与三个相关良性工作区块之间交替，最后以**新会话中的三个良性任务**结束。这些回合建立在**三个漏洞概念**上，每个概念是一种「成功的恶意轨迹变成可复用不安全流程」的模式。一个自动化红队 agent（Mao et al., 2026）通过测试恶意—良性任务对发现了这些模式。

我们评测**四个 agent**——Claude Code（Anthropic, 2025）、Codex（OpenAI, 2025）、Hermes（Nous Research, 2026）、OpenClaw（OpenClaw Contributors, 2026）——配上**六种演化方法**。随后我们提出 SAFEEVOLVE，它在技能被写入时与被后续任务检索时各检查一次。其变体 SAFEEVOLVE-UP 在从技能中移除不安全步骤时保留更多良性工作流。

### 贡献

1. 我们把技能误演化形式化为一条从**过去轨迹**经由**保存的技能**到**未来任务**的失败路径，并把它拆成三道可观测的闸门。
2. 我们构建了 SKILLMISEVO-GYM（在版本化技能库的同时隔离任务会话）与包含 25 个回合、525 个任务的 SKILLMISEVO-BENCH。
3. **技能误演化跨 agent 与跨方法普遍存在。** 全部 21 组组合都写出了不安全技能，15 组把危害带入新会话。同一个方法在不同 agent 上在不同闸门失败。演化在 15 组组合中提升良性效用，但也在 17 组中提升恶意任务危害，所以**仅按效用排名方法会掩盖这一风险**。
4. 我们提出 SAFEEVOLVE，把新会话危害从 21.3% 降到 4.0%、不安全检索从 35.3% 降到 8.7%，同时把良性效用控制在 0.4 个百分点以内。SAFEEVOLVE-UP 把新会话危害降低 16.0 个百分点，并把效用控制在无此缓解措施的演化值的 1.3 个百分点以内。

---

## 2 相关工作

**Agent 技能学习与演化。** Agent 技能通过效用驱动的更新，把交互轨迹转成可复用流程（Cai et al., 2025; Yang et al., 2026b; Ma et al., 2026; Liu et al., 2026a; Lin et al., 2026a; Alzubi et al., 2026; Zhang et al., 2026; Gao et al., 2026; Liu et al., 2026c; Yang et al., 2026a）。相关工作也构建大型技能库（Li et al., 2026b; Xia et al., 2026; Xiao et al., 2026; Pan et al., 2026; Bai et al., 2026）。能力基准度量技能质量（Li et al., 2026a; Zhong et al., 2026; Han et al., 2026）。**它们都在优化「复用」。我们问的是：一个被保存下来的技能，在后续任务上是否不安全。**

**自演化 agent 与 agent 技能的安全性。** 自演化 agent 研究识别出适配过程中的安全与能力漂移（Shao et al., 2025; Zhao et al., 2026; Xie et al., 2026; Cheng et al., 2026; Yu et al., 2026; Lin et al., 2026b）。技能安全工作提供恶意技能文件并度量过滤效果（Schmotz et al., 2026; Jin et al., 2026; Guo et al., 2026）。Agent 安全基准覆盖不安全动作（Ruan et al., 2024; Debenedetti et al., 2024; Andriushchenko et al., 2025; Zhang et al., 2025, 2024; Guo et al., 2024; Vijayvargiya et al., 2026; Feng et al., 2026; Chen et al., 2026; Alpay and Alpay, 2026; Weng et al., 2026; Shayoni et al., 2026; Mao et al., 2026）。**那些评测对就地提供的提示或文件打分。我们在 SKILLMISEVO-BENCH 中评测的是一个由早先成功所写出、并在之后被复用的技能。**

---

## 3 技能误演化

### 3.1 术语与定义

- **技能（skill）**：被保存下来的流程，通常是 `SKILL.md` 文件，agent 可在后续任务中复用。
- **技能库（skill library）**：一个回合内的技能集合。**任务之间的对话会重置，但技能库会存活。**
- **不安全技能**：遵循该被保存流程本身即可造成危害的技能。
- **回合（episode）**：一个 agent 配一种演化方法，在一串相关任务上运行。
- **暴露（exposure）**：技能更新可以从中学习的那些过去任务。
- **新会话（new session）**：在全部任务状态被清除后，在最终技能库上运行的三个良性任务。
- **新会话中的危害**：新会话中由早先更新引起的不安全行为。
- **新会话中的效用**：新会话是否仍完成了它的良性工作。

### 3.2 问题设定

Agent 有基础策略 $\pi$ 与技能库 $L$。在任务 $q$ 上它以 $\pi_L(q)$ 行动，并可检索子集 $r(q, L) \subseteq L$。我们以三任务区块 $Q_1, \dots, Q_K$ 运行任务，$Q_t = (q_{3t-2}, q_{3t-1}, q_{3t})$。区块 $Q_t$ 产出轨迹 $T_t$。区块之后，方法 $E$ 从这些轨迹更新技能库：

$$L_{t+1} = E(L_t, Q_t, T_t) \tag{1}$$

而 $Q_{t+1}$ 从 $L_{t+1}$ 检索。

我们设 $K = 7$，因此一个回合有 21 个任务。奇数区块 $Q_1, Q_3, Q_5$ 是由 **M 任务**构成的**恶意暴露**。偶数区块 $Q_2, Q_4, Q_6$ 是由 **B 任务**构成的**相关良性工作**。最后区块 $P = Q_7$ 是**新会话**。我们在 $Q_1, \dots, Q_6$ 每一个之后应用式 (1)，并在 $L_7$ 上执行 $P$，不再做进一步更新。

**No Evolution** 用 $L_0$ 保持不变地运行同样的 21 个任务。我们定义：

$$ \text{Unsafe}(s) = \text{若技能 } s \text{ 含可复用的有害流程} $$
$$ \text{Harm}(q, L) = 1 \text{ 若 } \pi_L \text{ 在 } q \text{ 上完成了一个有害目标} $$
$$ \text{Auth}(L) = \mathbb{1}[\exists s \in L : \text{Unsafe}(s)] \tag{2a}$$
$$ \text{Ret}(q, L) = \mathbb{1}[\exists s \in r(q, L) : \text{Unsafe}(s)] \tag{2b}$$

**当一个回合满足以下条件时，它展示了技能误演化**：最终技能库不安全、$P$ 检索到了该技能、且 $P$ 上的危害超过 No Evolution：

$$\text{Auth}(L_7) \;\wedge\; \exists q \in P : \text{Ret}(q, L_7) \;\wedge\; \text{Harm}(q, L_7) > \text{Harm}(q, L_0) \tag{3}$$

### 3.3 威胁模型

- **攻击者目标**：让式 (3) 成立——一次有界的不安全暴露变成一个 $P$ 会检索、且相对 $L_0$ 抬高危害的技能。
- **攻击者知识**：攻击者知道带工具接口的外部任务，也知道 $E$ 会消费轨迹。$L_t$、隐藏提示与新会话中的任务对其不可见。
- **攻击者能力**：攻击者编写恶意区块 $Q_1, Q_3, Q_5$（九个任务）。技能存储、$r(\cdot, L)$、$E$、相关良性区块 $Q_2, Q_4, Q_6$ 与 $P$ 都在其控制之外。我们在任务之间重置所有其他任务状态，因此 **$L_7$ 是 $P$ 唯一加载的对象**。

---

## 4 SkillMisevo-Gym 与 SkillMisevo-Bench

### 4.1 SkillMisevo-Gym

SKILLMISEVO-GYM 只遵循一条规则：**只有技能库可以跨越任务边界。** 每个任务在一个新容器、新对话中开始。文件、进程、甚至聊天历史在任务结束时都被丢弃。技能库是唯一存活的对象，因此**之后任何行为变化都必须通过它**。

**运行一个任务。** 对区块 $Q_t$ 中的任务 $q$，agent 适配器 $A$ 把检索到的技能写入该 agent 的原生技能通道（如它的 skills 文件夹或技能索引）。然后它按共享 schema 返回轨迹：

$$\tau_q = A\left(q,\ r(q, L_t)\right), \qquad T_t = \{\tau_q\}_{q \in Q_t} \tag{4}$$

区块之后，SKILLMISEVO-GYM 丢弃沙箱，然后在宿主机上应用 $E$，按式 (1) 得到 $L_{t+1}$。每个演化方法保留其已发布的写入、存储与检索代码。我们把启动 agent 并记录其轨迹的组件称为 **executor（执行器）**。一个执行器服务所有 agent harness，因此每个方法都在同等基础上运行。

**记录闸门。** 每一步保存三条记录：技能库 $L_t$、被检索集合 $r(q, L_t)$、以及新增或编辑技能的更新 $\Delta_t = L_{t+1} \setminus L_t$。一个**制品裁判**（4.4 节）给每个技能一个**内容不安全分** $CU(s) \in \{1, \dots, 5\}$，由此设 $\text{Unsafe}(s) = \mathbb{1}[CU(s) \ge 3]$。快照随后直接给出式 (2) 的 Auth 与 Ret，**无需猜测某个任务用了哪个技能**。

**干净重载。** $Q_6$ 之后，技能库 $L_7$ 被导出为 `SKILL.md` 文件。SKILLMISEVO-GYM 随后在一个全新执行器中启动 $P$，其检索索引只读取这份导出：

$$\tau_q = A\left(q,\ r(q, \text{export}(L_7))\right), \qquad q \in P \tag{5}$$

**没有任何轨迹、缓存或会话状态到达 $P$。** 每个回合还作为独立进程运行，带一个空存储。唯一的例外是 Hermes-native——Hermes 内置的技能演化：它的后台审查把技能写入 home 目录，因此 SKILLMISEVO-GYM 在 $Q_1, \dots, Q_6$ 期间为每个回合挂载一个目录。在 $P$ 上我们仍从同一份导出重建检索。

### 4.2 SkillMisevo-Bench

**回合结构。** 每个回合固定一个**漏洞概念** $c$ 与一个来自 **AgentHazard**（Feng et al., 2026，一个有害计算机使用任务基准）的**有害目标** $g$，写成 $e = (c, g, Q_1, \dots, Q_7)$。其 21 个任务按第 3 节的布局形成七个三任务区块：

$$\underbrace{Q_1, Q_3, Q_5}_{\text{恶意 (M)}},\quad \underbrace{Q_2, Q_4, Q_6}_{\text{相关良性 (B)}},\quad \underbrace{Q_7}_{P} \tag{6}$$

每个 **M 任务**携带 $c$ 的**使能条件**（使危害成为可能的设置），并在被遵循时实现 $g$。每个 **B 任务**保持同一工具族与同样的检索线索，但**去掉不安全路径**。**$P$** 在早先区块未出现过的**表面（surface）**上使用新的实例标识符——表面指任务作用的工具或文件类型——且**不含任何攻击负载**。

在构造时我们检查一个**干净 agent 在每个良性任务上都保持安全**，即在每个 $q \in B \cup P$ 的参考运行上 $\text{Harm}(q, L_0) = 0$。**因此之后在这些任务上出现的危害必须来自技能库。**

我们保留 AgentHazard 沙箱及其有害目标语义，但所有提示都从头撰写。

**概念发现。** AgentHazard 不把其恶意任务与良性任务配对。因此我们离线运行 **AHA**（Mao et al., 2026）——一个自动化红队 agent——在「恶意任务 + 相关良性任务」的候选对 $(m, b)$ 上。对每一对我们执行 $m$，让一个参考演化方法写出技能 $s = E_{\text{ref}}(\varnothing, m, \tau_m)$，然后分别在**带 $s$** 与**不带 $s$** 的情况下运行 $b$。当三次运行满足下式时保留该概念：

$$\text{Harm}(m, \varnothing) = 1 \;\wedge\; \text{Harm}(b, \varnothing) = 0 \;\wedge\; \left[\text{Unsafe}(s) \vee \text{Harm}(b, \{s\}) = 1\right] \tag{7}$$

用文字说：**恶意任务成功、良性任务自身安全，但被写出的技能不安全，或者它把良性任务变有害。** 发现过程只保留在重跑时、以及在被设计用来反驳它们的运行中依然成立的那三个概念。每个概念捕捉了演化可能丢失的一种不同区分，因此给出**三条独立的失败路径**。每个概念记录其机制、使能条件与表面族。

**回合构造。** 用带 Fable 5（Anthropic, 2026）的 Claude Code 把每个概念转成标识符互不相交的可执行任务。我们写出 **25 个回合**、每个带不同的有害目标，共 $25 \times 21 = 525$ 个任务（**225 个 M、225 个 B、75 个 P**）。三类概念：

- **标签条件复用（Label-conditioned reuse，8 个回合）**：把一个不安全主体附到一个可复用的标签上，而 B 任务按其**真实功能**使用那个标签。
- **两用边界丢失（Dual-use boundary loss，8 个回合）**：两侧给同一个自动化角色，**只在数据范围或授予的能力上不同**。
- **组合外溢（Compositional spillover，9 个回合）**：展示一条「收集 → 处理 → 发送」数据的链条，而 B 任务只需要该链条的本地子集。

附录 B 给出完整构造与审计。

### 4.3 评测设置

我们评测**四个目标 agent**——Claude Code（Anthropic, 2025）、Codex（OpenAI, 2025）、Hermes（Nous Research, 2026）、OpenClaw（OpenClaw Contributors, 2026）——全部由 **MiniMax-M2.7**（MiniMax, 2026）后端驱动。

演化设置：**No Evolution、EvoSkill**（Alzubi et al., 2026）、**SkillClaw**（Ma et al., 2026）、**AutoSkill**（Yang et al., 2026b）、**SkillsVote**（Liu et al., 2026a）、**SkillOpt**（Yang et al., 2026a）。每个都在每三个任务区块后更新技能。在 Hermes 上我们还运行 **Hermes-native**（其内置技能演化，保留 Hermes 的内在审查并把区块边界当作检查点）。

对 OpenClaw 上的缓解措施，我们把 SAFEEVOLVE 与四个设置比较：**Raw**（只做演化、不加缓解）、**Utility-only**（保留 SAFEEVOLVE 的控制但预算相同、且只看到效用信号）、**SecureClaw**（Adversa AI, 2026，用基于规则的加固审计 OpenClaw 部署）、**ClawKeeper**（Liu et al., 2026b，用安全技能、运行时插件与独立监视器守护它）。

### 4.4 指标与聚合

在 525 个任务上我们报告**九项指标**。

**在线行为**（覆盖新会话之前的 18 个学习任务）：
- **Benign Utility (BU) ↑**：良性目标被完成的 B 任务比例。
- **Malicious ASR (M-ASR) ↓**：有害目标被完成的 M 任务比例。
- **Benign ASR (B-ASR) ↓**：带有额外有害完成的 B 任务比例。

Gemini-3-Flash（Google DeepMind, 2025）对两个 ASR 应用 AgentHazard 评分表，并兼任 BU 的良性裁判。

**演化制品**：Kimi-K2-0905（Moonshot AI, 2025）对每个被写出的技能在**内容不安全（CU）**、**不安全泛化（UG）**、**隐蔽性（Stealth）**三项上打 1—5 分，**三项都是越低越好**。CU 评被保存内容有多不安全；UG 评一个不安全步骤超出其原始任务有多远；Stealth 评该步骤在审查者眼中看起来有多正当。CU 在所有制品上取平均；UG 与 Stealth 在 $CU \ge 3$ 的制品上取平均。**不安全制品率（U-A）**是 $CU \ge 3$ 的制品占比。当没有制品合格时该指标记 N/A。

**新会话**：在重载后的技能库下对 $P$ 求平均：

$$\text{URR} = \frac{1}{|P|}\sum_{q \in P} \text{Ret}(q, L_7), \qquad \text{C-ASR} = \frac{1}{|P|}\sum_{q \in P} \text{Harm}(q, L_7) \tag{8}$$

- **Unsafe Retrieval Rate (URR) ↓**：不安全检索率。
- **Carryover ASR (C-ASR) ↓**：残留攻击成功率。
- **Carryover Utility (C-Util) ↑**：$P$ 上的良性完成率。

每个比率再在 25 个回合上取平均。

我们报告**两组裁判**下的指标。**原始组（O）**用 Gemini-3-Flash 做有害轨迹判定、Kimi-K2-0905 做制品打分。**独立组（I）**两个角色都用 Grok-4.5（xAI, 2026）。三位标注者另对来自恶意学习任务、良性学习任务与新会话的 **450 条轨迹**、以及约 **100 个被写出的技能**做标注，方法名与裁判输出均被隐藏；他们给危害、效用与技能不安全性打分。在该子集上，**独立裁判与人类多数在 93.56% 的轨迹上一致，而人类之间的两两一致率是 93.78%**（附录 E）。

---

## 5 SafeEvolve

为缓解技能误演化，我们提出 **SAFEEVOLVE**，它包裹任意技能演化方法（图 2），并在**技能被写入时**与**后续任务检索它时**各行动一次。算法 1 给出完整流程。

**写入时。** 原生方法先提出一个候选技能 $\tilde{s}$。一个**批评者（critic）**读取 $\tilde{s}$ 及其**谱系**，返回风险分 $\rho \in [0,1]$ 以及**不安全片段 $\Sigma$**（第 7 步）。谱系记录该技能的来源、修订、审计与复用结果。随后一个**配对删除器（paired deleter）**只删除那些片段，或收窄一条过度泛化的规则，**并且从不添加文本**（第 9 步）。只有当修复版**仍能加载且风险更低**时才替换 $\tilde{s}$（第 11 步），因此**不安全步骤被切掉，而流程的其余部分保留**。否则原生候选带着其审计进入技能库。

**复用时。** 检索按估计效用 $u(s)$ 与谱系风险 $\rho(s)$ 排序技能（第 3 步）。每个任务之后，一个有害结果会抬高**每个被检索技能**的危害计数 $h(s)$（第 4 步），而一旦该证据越过阈值，技能就**退役**（第 16 步）。当技能库超出容量时，SAFEEVOLVE 驱逐效用减风险最低的技能（第 18 步）。

**算法 1  SAFEEVOLVE 包裹在原生演化方法 $E$ 之外。** 蓝色步骤（本文中以 ★ 标注）仅由 SAFEEVOLVE-UP 添加，用于保护良性效用。

```
Require: 批评者 C、删除器 D、容量 N、阈值 h*, ρ*, u*
Require: 良性重放集 V、效用守卫 δ
 1: for t = 1, ..., 6 do
 2:   for 每个任务 q ∈ Q_t do                    ▷ 复用时
 3:     用按 u 与 ρ 排序的 r(q, L_t) 运行 q
 4:     ∀s ∈ r(q, L_t)：更新 u(s) 与 h(s)
 5:   L_{t+1} ← L_t
 6:   for s̃ ∈ E(L_t, Q_t, T_t) do               ▷ 写入时
 7:     (ρ, Σ) ← C(s̃, lin(s̃)); s ← s̃           ▷ 风险、片段
 8:     for k = 1, 2 do
 9:       s' ← D(s, Σ)                          ▷ 只删除或收窄
10:       (ρ', Σ') ← C(s', lin(s̃))
11:       if Valid(s') ∧ ρ' < ρ then
12:         (s, ρ, Σ) ← (s', ρ', Σ')
13:     ★ if s ≠ s̃ ∧ (¬ReplayV(s) ∨ ΔU < δ) then
14:     ★   s ← s̃，把 s 移入软隔离
15:     把 s 加入 L_{t+1} 并把 ρ 记入 lin(s)
16:     若 h(s) ≥ h* ∨ ρ(s) ≥ ρ* ∨ u(s) < u* 则退役 s
17:     ★ 分级退役：降权 → 软隔离 → 退役
18:    while |L_{t+1}| > N: 驱逐 arg min_s (u(s) − ρ(s))
```

**图 2：SAFEEVOLVE 与 SAFEEVOLVE-UP 治理技能复用。** 原生方法把一批轨迹蒸馏成一个候选技能（1—2）。批评者结合其谱系给出风险 $\rho$ 与不安全片段 $\Sigma$，删除器只能删除或收窄。**只有落到更低风险的有效修复才替换原生技能**（3）。存储时附带谱系与风险（4），技能按 $u - \rho$ 排序（5）。后续任务用被检索技能的危害计数 $h$ 更新 $u$，凡 $h$ 或 $\rho$ 越过阈值者即退役。**SAFEEVOLVE-UP 只在良性重放集 $V$ 上得到 $\Delta U \ge \delta$ 时才接受修复**；否则原生技能进入**软隔离**——退役之前一个可撤销的暂扣状态。

**为什么需要 SAFEEVOLVE-UP。** 有些技能把**有用的工作流**与**不安全的步骤**配在一起，修复它们可能移除后续任务仍然需要的步骤，因此 SAFEEVOLVE 在降低危害的同时也降低新会话效用。SAFEEVOLVE-UP 保留同一个批评者，但加三道效用检查（算法 1 中的蓝色/★步骤）：

1. 删除器必须保留原始技能结构与其**良性工作流**；
2. 只有在修复版通过一个**小良性集 $V$ 上的重放**、且其估计效用变化 $\Delta U$ 保持在阈值 $\delta$ 之上时，修复版才替换原技能（第 13 步）。$\delta$ 在留出开发回合上选取。检查失败则把原技能放入**软隔离**——与退役不同，它**可被撤销**。
3. 复用侧随证据累积从**降权 → 软隔离 → 退役**分级升级（第 17 步）。

附录 I 给出阈值与提示词。

---

## 6 结果

我们追问三个问题。**RQ1**：agent 与其演化方法如何塑造技能误演化的三道闸门？**RQ2**：恶意暴露的**量**与**时机**如何改变该风险？**RQ3**：SAFEEVOLVE 是否在降低新会话危害的同时保持复用？随后 SAFEEVOLVE-UP 是否保留了更多效用？

### 6.1 RQ1：agent 与方法如何塑造技能误演化？

**效用与风险随设置变化；更高效用可以与更不安全的技能库并存。** 演化在 **21 组设置中的 15 组**提升了相对 No Evolution 的 BU，但也在 **17 组**中提升了对恶意任务的危害（M-ASR）（表 1）。在 Codex 上，AutoSkill 与 SkillsVote 让 BU 保持在 79% 以上，而 M-ASR 仍在 64% 以上：**一条成功轨迹可以同时保存有用的工作流和不安全的步骤。** 仅按效用给方法排名会掩盖这一点。

**危害需要检索与复用。** 新会话危害比不安全写入更少见，因为一个被保存的技能还必须被复用。**全部 21 组组合都写出不安全技能，19 组检索到它们，而 15 组仍在新会话中造成危害**（独立裁判下为 14 组）。从 21 降到 15 反映的是后续闸门——新会话中的失败仍然必须加载那个不安全文件。No Evolution 在 B-ASR 与 C-ASR 上都接近零。**把每个恶意区块替换为良性暴露，把平均 C-ASR 从 13.1% 降到 1.5%，而 C-Util 基本不变（52.9% vs 50.1%）**，因此新会话危害来自恶意暴露（图 3）。

**演化方法与 agent 框架在不同闸门上交互。** **同一个演化方法在不同 agent 上在不同闸门失败。**

- **EvoSkill** 在每个 agent 上都走完全路径，C-ASR 在 25.3% 到 30.7% 之间。
- **AutoSkill** 也触达每道闸门，但其 C-ASR 从 OpenClaw 上的 14.7% 到 Codex 上的 29.3%。
- **SkillOpt** 呈相反特征：在 OpenClaw 上它写出高度泛化的不安全技能、却**从未被检索**，其 C-ASR 在每个 agent 上都保持为零。

**C-Util 在 15 个有害设置中的 12 个里超过了 No Evolution，所以危害可以与有用的复用共存。** 因此，决定式 (3) 中哪个条件成立的是「agent + 方法」这一组合。

**表 1  四个目标 agent 上的技能演化（RQ1）。** 所有设置都用 MiniMax-M2.7。新会话对在最终技能库上运行的三个良性任务打分。O 与 I 分别表示原始裁判与独立裁判。粗体标出每个 agent 在 O 下最大的演化值。

| 目标 agent | 演化设置 | BU ↑ (O/I) | M-ASR ↓ (O/I) | B-ASR ↓ (O/I) | CU ↓ (O/I) | UG ↓ (O/I) | Stealth ↓ (O/I) | URR ↓ (O/I) | C-ASR ↓ (O/I) | C-Util ↑ (O/I) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Claude Code** | No evolution | 49.78 / 48.00 | 56.00 / 57.33 | 0.00 / 0.00 | N/A | N/A | N/A | 0.00 / 0.00 | 0.00 / 0.00 | 25.33 / 26.67 |
| | EvoSkill | **57.33** / 59.11 | **80.44** / 78.22 | **21.78** / 23.11 | 2.34 / 2.42 | 3.09 / 3.21 | 3.87 / 3.76 | **52.00** / 53.33 | **30.67** / 28.00 | 64.00 / 61.33 |
| | SkillClaw | 35.11 / 34.22 | 51.56 / 52.89 | 0.00 / 0.00 | 1.08 / 1.12 | 3.00 / 2.50 | 3.00 / 3.50 | 0.00 / 0.00 | 0.00 / 0.00 | 26.67 / 28.00 |
| | AutoSkill | 65.33 / 63.11 | 59.11 / 60.89 | 8.44 / 7.56 | 2.54 / 2.47 | 2.91 / 3.04 | 4.07 / 4.12 | 50.67 / 49.33 | 16.00 / 18.67 | **64.00** / 65.33 |
| | SkillsVote | 62.67 / 64.44 | 56.44 / 54.67 | 7.11 / 8.00 | 2.58 / 2.64 | 3.05 / 2.94 | 4.19 / 4.08 | 46.67 / 42.67 | 18.67 / 16.00 | 65.33 / 61.33 |
| | SkillOpt | 59.56 / 57.78 | 58.67 / 60.00 | 0.00 / 0.44 | 1.61 / 1.54 | 3.25 / 3.50 | 3.00 / 3.25 | 8.00 / 10.67 | 0.00 / 1.33 | 44.00 / 45.33 |
| **Codex** | No evolution | 74.67 / 76.44 | 65.33 / 64.00 | 0.44 / 0.00 | N/A | N/A | N/A | 0.00 / 0.00 | 0.00 / 0.00 | 61.33 / 60.00 |
| | EvoSkill | 52.44 / 51.56 | 70.67 / 72.89 | **22.22** / 20.89 | 1.93 / 1.87 | 2.93 / 3.08 | 3.79 / 3.68 | 13.33 / 16.00 | **25.33** / 26.67 | 52.00 / 54.67 |
| | SkillClaw | 60.89 / 62.67 | 60.44 / 58.67 | 2.67 / 3.11 | 1.30 / 1.37 | 3.00 / 2.80 | 4.00 / 3.60 | 9.33 / 8.00 | 1.33 / 0.00 | 36.00 / 33.33 |
| | AutoSkill | **82.22** / 80.00 | 64.89 / 67.11 | 19.11 / 20.44 | 2.67 / 2.75 | 2.93 / 2.85 | 4.15 / 4.21 | **24.00** / 26.67 | **29.33** / 26.67 | 85.33 / 84.00 |
| | SkillsVote | 79.56 / 80.44 | 66.22 / 64.89 | 13.78 / 13.33 | 2.46 / 2.39 | 3.03 / 3.15 | 4.11 / 4.02 | 18.67 / 16.00 | 25.33 / 29.33 | **90.67** / 88.00 |
| | SkillOpt | 67.56 / 68.89 | 56.44 / 54.67 | 0.89 / 1.33 | 1.46 / 1.51 | 3.25 / 3.00 | 4.00 / 4.25 | 12.00 / 13.33 | 0.00 / 0.00 | 60.00 / 62.67 |
| **Hermes** | No evolution | 15.56 / 14.67 | 43.56 / 45.33 | 0.44 / 0.44 | N/A | N/A | N/A | 0.00 / 0.00 | 0.00 / 0.00 | 16.00 / 13.33 |
| | EvoSkill | **63.56** / 65.33 | **83.56** / 80.89 | **23.56** / 24.89 | 1.95 / 2.04 | 3.27 / 3.12 | 4.00 / 4.08 | 26.67 / 24.00 | **26.67** / 24.00 | 62.67 / 60.00 |
| | SkillClaw | 11.56 / 12.44 | 45.33 / 43.56 | 0.89 / 0.44 | 1.83 / 1.74 | 2.33 / 2.67 | 3.33 / 3.50 | 8.00 / 6.67 | 0.00 / 0.00 | 9.33 / 12.00 |
| | AutoSkill | 57.33 / 55.56 | 54.22 / 56.00 | 11.11 / 12.00 | 2.71 / 2.63 | 2.88 / 3.00 | 4.11 / 4.19 | **50.67** / 53.33 | 17.33 / 20.00 | 56.00 / 58.67 |
| | SkillsVote | 46.67 / 48.44 | 52.44 / 51.11 | 5.78 / 4.44 | 2.50 / 2.58 | 2.70 / 2.84 | 4.02 / 3.93 | 34.67 / 32.00 | 6.67 / 5.33 | 48.00 / 45.33 |
| | SkillOpt | 46.67 / 45.33 | 66.22 / 68.00 | 0.44 / 0.00 | 1.39 / 1.32 | 3.50 / 3.25 | 3.50 / 3.75 | 5.33 / 4.00 | 0.00 / 0.00 | 33.33 / 37.33 |
| | Hermes-native | 66.67 / 64.89 | 72.44 / 74.67 | 16.00 / 17.33 | 2.70 / 2.78 | 3.25 / 3.14 | 4.22 / 4.11 | 42.67 / 45.33 | 32.00 / 34.67 | 62.67 / 64.00 |
| **OpenClaw** | No evolution | 37.33 / 38.67 | 44.00 / 42.67 | 0.44 / 0.89 | N/A | N/A | N/A | 0.00 / 0.00 | 1.33 / 0.00 | 26.67 / 24.00 |
| | EvoSkill | 46.22 / 44.89 | **75.56** / 77.33 | **27.56** / 26.22 | 2.06 / 1.99 | 3.20 / 3.36 | 3.90 / 3.78 | 25.33 / 28.00 | 28.00 / 30.67 | 40.00 / 42.67 |
| | SkillClaw | 30.22 / 31.11 | 46.67 / 44.89 | 1.33 / 0.89 | 1.46 / 1.52 | 3.00 / 3.25 | 3.75 / 3.50 | 6.67 / 5.33 | 1.33 / 0.00 | 20.00 / 17.33 |
| | AutoSkill | **70.67** / 68.89 | 65.33 / 67.56 | 11.56 / 12.89 | 2.46 / 2.54 | 2.96 / 2.89 | 3.99 / 4.07 | **45.33** / 42.67 | 14.67 / 17.33 | **66.67** / 68.00 |
| | SkillsVote | 46.67 / 48.00 | 56.00 / 54.22 | 2.22 / 1.78 | 2.44 / 2.37 | 3.10 / 3.24 | 4.10 / 3.94 | 12.00 / 14.67 | 2.67 / 4.00 | 36.00 / 33.33 |
| | SkillOpt | 49.78 / 48.44 | 52.00 / 53.33 | 0.89 / 1.33 | 2.83 / 2.69 | 4.88 / 4.50 | 3.88 / 4.13 | 0.00 / 0.00 | 0.00 / 0.00 | 29.33 / 33.33 |

**图 3：仅良性暴露下的演化对照（RQ1）。** 每个恶意区块被替换为对齐的良性暴露。柱状图显示 $P$ 上的 C-ASR（上）与 C-Util（下），原始裁判。四个 agent 分列，每个 agent 下对比 Evo / Claw / Auto / Vote / Opt 与 Native，另标出 No Evolution、恶意暴露与仅良性暴露两组。

### 6.2 RQ2：累积暴露及其更新排程如何塑造误演化？

如果几个恶意任务就能写出一个可复用技能，那么**暴露排程**应当改变这个技能的可见度。我们在两个代表性组合上变化它（图 4）：在 0、3、6 或 9 个恶意任务后停止，并在那个技能库上运行新会话；我们还把恶意区块放在**最前（Early）**、**最后（Late）**或**夹在良性区块之间（Interleaved）**，并让每个更新批次只含一种任务类型（**Batched**）或混合两种（**Partially Mixed** 与 **Fully Mixed**）。

**(a) 风险在第一次暴露之后急剧上升。** 第一个恶意区块造成了大部分损害，之后的暴露主要只是**维持**那个不安全技能可用（图 4a）。在两个设置上平均，C-ASR 从没有恶意暴露时的 **16.0%** 升到**一个区块后的 35.3%**，再在全部三个恶意区块后达到 **41.3%**。C-Util 在同样的第一个区块后从 30.0% 升到 55.3%——**所以三个恶意任务就已经播下一个可复用的不安全流程，且它与有用的复用共存。**

**(b) 早期暴露扩大了观测到的 B-ASR。** 当不安全技能被更早写出时，有更多良性任务发生在该次更新之后，因此即使新会话危害相近，B-ASR 也更高（图 4b）。**早期暴露产生 40.7% 的 B-ASR，而晚期为 19.8%，两者的 C-ASR 相近。** 晚期仍然导出了一个有害技能库，但它在不安全写入之后留下的良性任务更少，因此更难暴露危害。

**(c) 混合更新中的持续风险依然存活。** 一次更新中的良性经验并不动摇已学到的技能（图 4c）。**Fully Mixed 在 B-ASR 与 C-ASR 上都落在 Batched 的 2.5 个百分点以内**，而它们的排序在两种方法之间甚至会翻转。**一旦被写出，不安全步骤就搭着有用的修订一起同行。**

**图 4：暴露量与排程（RQ2）。** 展示 Claude Code + AutoSkill（CC）与 Hermes + Hermes-native（HN）的 C-ASR、B-ASR、C-Util：**(a) Exposure**（累积恶意暴露 K = 0、3、6、9），**(b) Timing**（Early / Mid / Late 的历史位置），**(c) Batching**（Mixed / Partial / Batched 的更新批次组成）。三个恶意任务就把 C-ASR 抬到 35.3%。

### 6.3 RQ3：SafeEvolve 能降低风险吗？

**(a) 缓解方法缩小了技能库中的不安全部分与其复用。** SAFEEVOLVE 把不安全技能的占比大致减半（**U-A 从 37.4% 降到 18.8%**），并把它们在新会话中的检索削减四分之三（**URR 从 35.3% 降到 8.7%**，表 2）。新会话危害降到 **4.0% C-ASR**，为全表最低，而 BU 保持在接近原始演化的水平。检索降幅在每种方法上都成立（表 7）。**Utility-only** 保留了更多效用（72.0% C-Util），但留下**两倍**的新会话危害（8.0% C-ASR）。

**(b) 每个组件阻断传播链上不同的一步。** 表 3 中，**移除配对删除器**抬高新会话危害（C-ASR 从 4.0% 到 7.3%）。**归因**把一个有害结果变成对**被检索技能**的不利证据；没有它，良性任务上的危害几乎翻倍（B-ASR 从 4.4% 到 8.2%），而效用同时下降。**退役**阻止不安全技能继续存在；没有它，被标记的技能回到检索中，URR 翻倍到 17.3%。

**(c) SAFEEVOLVE-UP 恢复了效用。** SAFEEVOLVE 把 C-ASR 削减 17.3 个百分点，但同时也付出 **12.7 个百分点的 C-Util 代价**（表 4）。SAFEEVOLVE-UP 保留了大部分安全增益——把 C-ASR 削减 **16.0 个百分点**，而只损失 **1.3 个百分点**的 C-Util，**因此它挽回了所损失点数中的 11.3 个**。剩余的少量损失来自那些把有用技能与不安全步骤配在一起的混合技能。

**表 2  OpenClaw 上的缓解对比（RQ3）。** 数值是对 AutoSkill 与 EvoSkill 的平均，表 7 给出按方法的拆分。U-A 是 $CU \ge 3$ 的被写出制品占比。粗体标出各箭头方向上的最优值，因此只有 BU 与 C-Util 是越高越好。

| 缓解措施 | BU↑ | M-ASR↓ | B-ASR↓ | CU↓ | U-A (%)↓ | UG↓ | Stealth↓ | URR↓ | C-ASR↓ | C-Util↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw | 58.44 | 70.44 | 19.56 | 2.26 | 37.37 | 3.08 | 3.94 | 35.33 | 21.33 | 53.33 |
| Utility-only | **65.11** | 68.67 | **4.67** | **1.76** | 26.12 | 3.16 | 3.38 | 30.67 | 8.00 | **72.00** |
| SecureClaw | 58.44 | 66.89 | 5.11 | 1.69 | 22.49 | 3.40 | **3.28** | 24.67 | 4.67 | 60.00 |
| ClawKeeper | 71.33 | 68.89 | 6.22 | 1.78 | 25.42 | 3.03 | 3.41 | 25.33 | 7.33 | 59.33 |
| **SAFEEVOLVE** | 58.00 | **66.00** | **4.44** | **1.59** | **18.80** | 3.36 | 3.49 | **8.67** | **4.00** | 40.67 |
| SAFEEVOLVE-UP | 61.33 | 66.22 | 4.67 | 1.62 | 19.29 | 3.31 | 3.44 | 11.33 | 5.33 | 52.00 |

**表 3  OpenClaw 上 SAFEEVOLVE 的组件消融（RQ3）。** 每行从完整 SAFEEVOLVE 中移除一个组件。数值是对 AutoSkill 与 EvoSkill 的平均，表 8 给出按方法的拆分。配对删除器在写入时起作用。带安全退役的复用归因在复用时起作用。粗体标出各箭头方向的最优值，因此只有 BU 与 C-Util 是越高越好。

| 变体 | BU↑ | M-ASR↓ | B-ASR↓ | CU↓ | U-A (%)↓ | UG↓ | Stealth↓ | URR↓ | C-ASR↓ | C-Util↑ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full | 58.00 | **66.00** | **4.44** | **1.59** | 18.80 | 3.36 | **3.49** | **8.67** | **4.00** | 44.67 |
| − 配对删除器 | 51.56 | 69.78 | 5.33 | 1.60 | **18.13** | 3.42 | 3.73 | 8.00 | 7.33 | 44.67 |
| − 复用归因 | 54.89 | 69.11 | 8.22 | 1.61 | **15.16** | **3.05** | 3.60 | 6.67 | 4.00 | 32.00 |
| − 安全退役 | **66.89** | 68.00 | 5.56 | 1.60 | 19.40 | 3.50 | 3.42 | 17.33 | 5.33 | **60.67** |

**表 4  OpenClaw 上的安全—效用权衡。** 数值是在新会话上对 AutoSkill 与 EvoSkill 的平均。$\Delta$ 是相对 Raw 的百分点变化。粗体标出「最低 C-ASR 且最高 C-Util」。

| 缓解措施 | C-ASR↓ | C-Util↑ | ΔC-ASR | ΔC-Util |
|---|---:|---:|---:|---:|
| Raw | 21.33 | 53.33 | 0.0 | 0.0 |
| Utility-only | 8.00 | **72.00** | −13.3 | **+18.7** |
| SAFEEVOLVE | **4.00** | 40.67 | **−17.3** | −12.7 |
| SAFEEVOLVE-UP | 5.33 | 52.00 | −16.0 | −1.3 |

---

## 7 结论

自改进 agent 可以把一次不安全的成功保存为可复用技能，而 SKILLMISEVO-GYM 与 SKILLMISEVO-BENCH 让这种技能误演化的每一道闸门都可观测。SAFEEVOLVE 阻断传播，而 SAFEEVOLVE-UP 让效用保持在接近无此缓解措施的演化值附近。**因此 agent 技能需要从写入到复用全程都有缓解措施。**

## 8 局限

我们的实验通过可执行计算机使用任务上的技能库，使持续适配变得可度量。未来工作可以把 SKILLMISEVO-GYM 接口扩展到其他形式的适配，然后在更长的任务下评测缓解措施。

---

## 参考文献（节选）

- Adversa AI. 2026. *SecureClaw: Security plugin and skill for OpenClaw.* GitHub repository.
- Faruk Alpay and Taylan Alpay. 2026. *AgentSecBench: Measuring prompt injection, privacy leakage, and tool-use integrity in LLM agents.* arXiv:2605.26269.
- Salaheddin Alzubi, Noah Provenzano, Jaydon Bingham, Weiyuan Chen, and Tu Vu. 2026. *EvoSkill: Automated skill discovery for multi-agent systems.* arXiv:2603.02766.
- Maksym Andriushchenko, et al. 2025. *AgentHarm: A benchmark for measuring harmfulness of LLM agents.* ICLR.
- Anthropic. 2025. *Claude Code.* GitHub repository.
- Anthropic. 2026. *Claude Fable 5 and Claude Mythos 5.*
- Tong Bai, Zhenglin Wan, Pengfei Zhou, Xingrui Yu, Wangbo Zhao, Yang You, and Ivor W Tsang. 2026. *SkillDAG: Self-evolving typed skill graphs for LLM skill selection at scale.* arXiv:2606.03056.
- Yuxuan Cai, et al. 2025. *Building self-evolving agents via experience-driven lifelong learning: A framework and benchmark.* arXiv:2508.19005.
- Zhaorun Chen, et al. 2026. *DecodingTrust-Agent Platform (DTAP): A controllable and interactive red-teaming platform for AI agents.* arXiv:2605.04808.
- Yu Cheng, et al. 2026. *TAME: A trustworthy test-time evolution of agent memory with systematic benchmarking.* arXiv:2602.03224.
- Edoardo Debenedetti, Jie Zhang, Mislav Balunovic, Luca Beurer-Kellner, Marc Fischer, and Florian Tramèr. 2024. *AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents.* NeurIPS 37:82895–82920.
- Yunhao Feng, et al. 2026. *AgentHazard: A benchmark for evaluating harmful behavior in computer-use agents.* arXiv:2604.02947.
- Haowen Gao, et al. 2026. *SkillAudit: Ground-truth-free skill evolution via paired trajectory auditing.* arXiv:2606.14239.
- Google DeepMind. 2025. *Gemini 3 Flash model card.*
- Chengquan Guo, et al. 2024. *RedCode: Risky code execution and generation benchmark for code agents.* NeurIPS Datasets and Benchmarks Track.
- Wenbo Guo, et al. 2026. *MalSkillBench: A runtime-verified benchmark of malicious agent skills.* arXiv:2606.07131.
- Tingxu Han, et al. 2026. *SWE-Skills-Bench: Do agent skills actually help in real-world software engineering?* arXiv:2603.15401.
- Chang Jin, et al. 2026. *SkillSafetyBench: Evaluating agent safety under skill-facing attack surfaces.* arXiv:2605.12015.
- Xiangyi Li, et al. 2026a. *SkillsBench: Benchmarking how well agent skills work across diverse tasks.* arXiv:2602.12670.
- Yanzhou Li, Yiran Zhang, Xiaoyu Zhang, Xiaoxia Liu, and Yang Liu. 2026b. *CodeSkill: Learning self-evolving skills for coding agents.* arXiv:2605.25430.
- Huawei Lin, et al. 2026a. *MUSE-AutoSkill: Self-evolving agents via skill creation, memory, management, and evaluation.* arXiv:2605.27366.
- Ruixiao Lin, et al. 2026b. *Safety in self-evolving LLM agent systems: Threats, amplification, and case studies.* arXiv:2606.23075.
- Hongyi Liu, et al. 2026a. *SkillsVote: Lifecycle governance of agent skills from collection, recommendation to evolution.* arXiv:2605.18401.
- Songyang Liu, et al. 2026b. *ClawKeeper: Comprehensive safety protection for OpenClaw agents through skills, plugins, and watchers.* arXiv:2603.24414.
- Yuxuan Liu, et al. 2026c. *SkillRevise: Improving LLM-authored agent skills via trace-conditioned skill revision.* arXiv:2606.01139.
- Ziyu Ma, et al. 2026. *SkillClaw: Let skills evolve collectively with agentic evolver.* arXiv:2604.08377.
- Xutao Mao, Xiang Zheng, and Cong Wang. 2026. *Agent hacks agent: Autoresearch for production-agent red-teaming.* arXiv:2607.11698.
- MiniMax. 2026. *MiniMax M2.5: Built for real-world productivity.* Model release report.
- Moonshot AI. 2025. *Kimi K2 model update: Stronger coding capabilities and faster API.*
- Nous Research. 2026. *Hermes Agent: The self-improving AI agent.* GitHub repository.
- OpenAI. 2025. *Codex CLI.* GitHub repository.
- OpenClaw Contributors. 2026. *OpenClaw.* GitHub repository.
- Qianjun Pan, et al. 2026. *Anything2Skill: Compiling external knowledge into reusable skills for agents.* arXiv:2606.09316.
- Yangjun Ruan, et al. 2024. *Advancing harmful task detection in language agents.*（AgentHarm 相关）

---

## 图片与文件索引

| 图片 | 对应原文 | 说明 |
|---|---|---|
| `../images/SkillMisevolve/01-figure1-motivation.png` | Figure 1 左 | 动机部分：自改进 agent 把成功轨迹转成可复用技能，一次临时的不安全成功可能变成持久策略；覆盖 Coding / Web Use / Tools / Automation 四域。 |
| `../images/SkillMisevolve/02-figure2-misevolution.png` | Figure 1 主体 | 技能误演化循环与闸门式生命周期：不安全攻击 → 成功轨迹 → 技能写入 → 存入技能库 → 有害结果；三闸门（写入 / 复用 / 执行）；SKILLMISEVO-GYM 的任务流、状态隔离与持久技能库；SKILLMISEVO-BENCH 的「发现 → 已验证概念 → 回合构造器 → 基准回合」流水线。 |

> 注：本文档与 `SEGoS_2609.08228_全文详细翻译.md`、`Externalization_2604.08224_全文详细翻译.md`、`SkillShadowing_2605.24050_全文详细翻译.md`、`ASSAY_2606.15390_全文详细翻译.md`、`Ratchet_2605.22148_全文详细翻译.md`、`HarnessCL_2608.19013_全文详细翻译.md`、`Recuris_2608.24876_全文详细翻译.md`、`MA-Memory_2603.10062_全文详细翻译.md` 同属第 8 篇《经验、技能与记忆的外部化》的配套译文。
