# Agent Memory 领域的一些经典论文、项目和行业实践

## 第 0 步 · 建立心智模型

1. **CoALA — Cognitive Architectures for Language Agents**（Princeton, arXiv:2309.02427）

算是 agent memory 的"奠基性框架之作”。整个领域现在通用的记忆词汇表就出自这篇：**working / episodic / semantic / procedural** 四类记忆 + action space + 决策循环。先读它，后面所有系统你都能归位（PC 的 Memory≈semantic、Handoff≈episodic、Skill/Experience≈procedural）。

文章原文在 https://arxiv.org/abs/2309.02427 ，AI 翻译的中文版  https://github.com/AlexStocks/agent-memroy/blob/main/starting/CoALA_%E5%85%A8%E6%96%87%E8%AF%A6%E7%BB%86%E7%BF%BB%E8%AF%91.md 。

2. **A Survey on the Memory Mechanism of LLM based Agents**（arXiv:2404.13501）
   
该领域**第一篇系统性综述**：记忆分类、读写机制、评估基准（LoCoMo/LongMemEval/DMR）一次讲清，适合当"地图"反复翻。

原文在 https://arxiv.org/abs/2404.13501 ，AI 翻译的中文版 https://github.com/AlexStocks/agent-memroy/blob/main/starting/LLM-Agent-Memory-Survey-2404.13501-%E5%85%A8%E6%96%87%E4%B8%AD%E6%96%87%E7%BF%BB%E8%AF%91.md 。

## 第 1 步 · 三大奠基论文

| 论文                            | 贡献一句话                                                   | 链接             |
| ------------------------------- | ------------------------------------------------------------ | ---------------- |
| **Generative Agents** (UIST'23) | 记忆流 memory stream + reflection 反思 + recency/importance/relevance 三级检索——几乎所有后续记忆设计的源头 | arXiv:2304.03442 |
| **MemGPT** (2023)               | "LLM 即 OS、上下文即 RAM、外存即磁盘"的虚拟上下文管理，agent 自己决定换页 | arXiv:2310.08560 |
| **Mem0** (ECAI'25)              | 生产级记忆流水线：抽取→更新(ADD/UPDATE/DELETE 工具调用)→检索，LoCoMo 上 token 省 90%+ | arXiv:2504.19413 |
| **Zep/Graphiti** (2025)         | **双时态知识图**：事实带 valid/expired 窗口，能答"上周二 agent 以为什么是真的" | arXiv:2501.13956 |
| **A-MEM** (NeurIPS'25)          | Zettelkasten 卡片盒：记忆动态建链+演化，不再只读             | arXiv:2502.12110 |

（附：2026 年有两篇新综述可做更新——Du et al. arXiv:2603.07670 和 "Rethinking Memory Mechanisms" arXiv:2602.06052，读完全部旧的再碰。）

### 1.1 Generative Agents（"斯坦福小镇"，arXiv:2304.03442）

**一句话定位**：把大语言模型接上"记忆流 + 反思 + 规划"三件套，25 个智能体在《模拟人生》式小镇里自发生活两天——首次证明这三个组件对"行为可信度"有**因果贡献**，而不只是让模型看起来更聪明。

AI 翻译的中文版 https://github.com/AlexStocks/agent-memroy/blob/main/starting/Generative-Agents_2304.03442_%E5%85%A8%E6%96%87%E8%AF%A6%E7%BB%86%E7%BF%BB%E8%AF%91.md 。

#### 1.1.1 要解决的核心问题

LLM 能在**单个时间点**生成像人的行为，但一放到长时间跨度和多个智能体交互中就崩：会重复吃三顿午餐、记不住昨天约了谁、行为缺乏长期弧线。论文认为根因不是模型不够强（连 GPT-4 也有这问题），而是**缺架构**：需要一个能管理持续增长记忆、并按需检索合成的框架。

#### 1.1.2 架构三件套

| 组件 | 设计要点 |
|---|---|
| **记忆流** | 自然语言存经验全量；每条含描述 + 创建时间 + 最近访问时间 |
| **检索** | `score = 近因性 + 重要性 + 相关性`（α 全为 1，min-max 归一化）。近因性：0.995 指数衰减；重要性：让 LLM 打 1–10 分（"打扫房间"=2，"约暗恋对象"=8）；相关性：嵌入余弦相似度 |
| **反思** | 取最近 100 条记忆 → LLM 提 3 个高层问题 → 用问题去检索（含已有反思）→ 生成带引用指针的洞见 → 形成**反思树**（叶=观察，非叶=逐级抽象的想法）。触发条件：近期事件重要性分之和 > 150，实践中每天约 2–3 次 |
| **规划** | 自顶向下递归分解：一天的 5–8 个粗块 → 小时级 → 5–15 分钟级；规划本身也写回记忆流并参与检索 |
| **反应 / 对话** | 每步判断"继续计划 or 反应"；反应时从该时刻重新生成规划；对话以双方对彼此的摘要记忆 + 对话历史为条件逐句生成 |

**关键类比**：反思不是"总结"，是**递归抽象**——反思可以对反思再反思，这才是 Maria 能推断出"该送 Wolfgang 音乐作曲相关礼物"的原因（纯观察记忆只会选"见面最多的人"）。

### 1.1.3 实验结果

- **受控评估**（100 名评估者排序，TrueSkill）：完整架构 μ=29.89 > 无反思 26.88 > 无反思无规划 25.64 > **人类众包 22.95** > 完全消融 21.21。与"代表先前工作"的完全消融条件相比 **Cohen's d = 8.16（八个标准差）**，Kruskal-Wallis H(4)=150.29, p<0.001。
- **端到端两天模拟**：Sam 参选消息扩散 4%→32%，派对消息 4%→52%（零用户干预）；关系网络密度 0.167→0.74；12 位受邀者中 5 位到场——全部从"Isabella 想办派对"这一条种子自然长出来。
- **三种失效模式**（7.2）：① 记忆变多后反而选错地点；② 难以用自然语言传达的物理规范导致误判（"宿舍浴室"被当成多人用、商店打烊后仍进店）；③ 检索不到 / 检索到碎片 → 幻觉式添油加醋。

### 1.2 MemGPT: Towards LLMs as Operating Systems（arXiv:2310.08560）

**一句话定位**：把操作系统的**虚拟内存分页**搬进 LLM——上下文窗口当主存、外部存储当磁盘，让 LLM **自己**通过函数调用做换页，从而在固定上下文下撑出"无限上下文"的假象。UC Berkeley 出品，项目后更名 Letta。

AI 翻译的中文版 https://github.com/AlexStocks/agent-memroy/blob/main/starting/MemGPT_2310.08560_%E5%85%A8%E6%96%87%E8%AF%A6%E7%BB%86%E7%BF%BB%E8%AF%91.md 。

#### 1.2.1 要解决的核心问题

不是"模型不够聪明"，而是**容量硬约束 + 扩展不划算**：自注意力让扩上下文成本二次方增长；即便扩了，Liu et al. 2023 也证明长上下文模型用不好中段信息（lost-in-the-middle）。所以论文走"**在固定上下文模型之上加一层内存管理**"的路线，而不是等更长的模型。

#### 1.2.2 架构

| 组件 | 设计要点 |
|---|---|
| **主上下文（三层）** | ① 系统指令（只读：控制流 + 存储层级说明 + 函数用法）② 工作上下文（固定大小读写块，存用户事实/偏好/人设）③ FIFO 队列（滚动消息 + **队首递归摘要**） |
| **外部上下文** | 召回存储（消息库，无限期保留）+ 归档存储（任意长文本对象 + 向量检索，PostgreSQL + pgvector + HNSW） |
| **内存压力机制** | 达 70% → 插系统告警，让 LLM 主动把重要信息写进工作上下文/归档；达 100% → 驱逐约 50% 消息并 **重生成递归摘要**（旧摘要 + 被驱逐消息） |
| **自我导向编辑** | 输出被解析成函数调用 → 执行 → **结果连同运行时错误反馈回处理器**（反馈回路）；系统提示里明确告诉 LLM token 限制 |
| **事件驱动控制流** | 用户消息 / 系统消息 / 用户交互 / **定时事件**都能触发推理（可无用户干预运行）；`request_heartbeat=true` → 函数链（多步检索）；不给 → yield 等下一个事件 |
| **分页检索** | 检索结果强制分页，防止溢出上下文窗口 |

**关键洞见**：内存管理不是"系统替模型做"，而是**交给模型自己做**——编译器式的自动换页换成了"LLM 自己决定什么时候存、存什么、什么时候继续翻页"。这也是它最大的脆弱点（见第 4 点）。

#### 1.2.3 实验结果

- **DMR 深度记忆检索（一致性）**：GPT-4 32.1% → **92.5%**；GPT-4 Turbo 35.3% → **93.4%**；GPT-3.5 38.7% → 66.9%（ROUGE-L 同步大涨）。注意基线拿到的是"过去五轮对话的摘要"，MemGPT 拿到的是完整历史但必须自己检索——**差距几乎全部来自"能否把对的记忆换进上下文"**。
- **嵌套 KV 多跳检索**：GPT-3.5 在 1 层嵌套就 0%（失效模式是直接把原始值返回）；GPT-4 / GPT-4 Turbo 在 3 层掉到 0%；**MemGPT + GPT-4 不受嵌套层数影响**。反常的是 MemGPT + GPT-4 Turbo 反而差于 + GPT-4——长上下文不是越强越好，函数调用策略才是瓶颈。
- **文档 QA**：固定上下文基线的准确率**上限被检索器性能锁死**（检索器没召回金标准文档就注定答错）；MemGPT 可多次调用检索器迭代翻页，性能不随文档数增加而退化。

#### 1.2.4 关键局限

① 性能**强依赖底层模型的函数调用能力**（GPT-3.5 上大幅掉点）；② MemGPT **经常在耗尽检索库之前就停止翻页**——理论上能翻完，实际上不等于会翻完；③ 仍受嵌入检索质量制约。

#### 1.2.5 与 PC 的关联

- 这是 **2404.13501 综述框架里"文本形式记忆 + 写入/管理/读取"的完整工程实现**：递归摘要 ≈ 管理操作里的"遗忘/合并"，归档/召回双库 ≈ 记忆来源的"跨试验信息 + 外部知识"，分页检索 ≈ 读取操作。
- 对照 PowerContext 六阶段闭环：**FIFO 队列 + 队列管理器 ≈ Capture/Flush**；**工作上下文 ≈ 常驻的有界召回区**；**归档存储向量检索 ≈ Search**；而 PC 的 **Source 证据链**恰好补上 MemGPT 没有的一环——它把消息无限期存进召回库，但反思/摘要过程**不带引用指针**（Generative Agents 的反思反而带 because of 1,2,8,15）。
- 对"有界召回"的直接启发：MemGPT 证明了**告警阈值（70%）+ 强制递归摘要**是个可用的工程范式，代价是摘要会丢信息；若换成"摘要保留 source 指针 + 原始消息可回溯"，就是 PC 相对 MemGPT 的差异化价值点。


## 第 2 步 · 四大开源实现

- **mem0ai/mem0**（~48-55K★，星最多）—— 三层 scope（user/session/agent）+ 向量+图混合存储，接入最广
- **getzep/graphiti**（~20-24K★）—— 双时态知识图引擎，时间推理最强，企业合规向
- **letta-ai/letta**（~21K★，原 MemGPT）—— Core/Recall/Archival 三层自编辑记忆，"sleep-time compute"
- **langchain-ai/langmem** —— 唯一把 **procedural memory**（agent 改自己指令）显式做出来的
- 加餐：**agiresearch/A-mem**（笔记网络）、Cognee（图原生）、Cloudflare Sessions（API 层 compaction overlay）

> 快速对比长文：wal.sh《Agent Memory Architectures: JITIR Against the Field》(2026) 把 Cloudflare/Letta/Zep/Mem0/A-MEM/LangMem 和 CLI agent 惯例**逐个拆解**，还点出一个和你正相关的视角——**value-oriented（事实只追加+失效，不原地改）vs place-oriented**——PC 的不可变 Revision 正是 value-oriented 路线。强烈推荐读。

## 第 3 步 · Context 侧

- **Anthropic《Effective context engineering for AI agents》**（2025-09）—— 现在讲 context 最权威的一篇：context rot、just-in-time context、subagent 隔离、预算思维
  → https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Anthropic cookbook：Memory vs Compaction vs Tool Clearing** —— 三种 context 手段怎么选
- **Anthropic《Building effective agents》**（2024-12）—— agent 设计总纲，记忆只是其中一节但定位很准

## 第 4 步 · 行业惯例层

现在的 CLI coding agent 用**约定即 schema**：`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`（项目指令）+ `~/.claude/.../memory/`（类型化长期记忆）+ `SKILL.md` + Codex `handoff`。2026 年 Anthropic 更把 memory tool 做进了 API（`/memories` 目录，官方 GA）。**PC 本质是把这套文件约定产品化为带审核的 Server 服务**——理解这层就理解了 PC 的生态位。
→ 论点长文：agentmarketcap《The Agent Memory Protocol Gap》(2026-04)：为什么至今没有"MCP for Memory"——scope 语义、事实演化、审核权这些正是缺口，PC 的 Scope/Revision/Review 恰好在补这些洞。

## 建议的实际切入动作

1. 先花 2 小时读 CoALA §4 + Generative Agents §4（记忆与反思），建立词汇表；
2. 再花半天把 Letta 和 Graphiti 两个 repo 的 README + 各自论文图各读一遍，对照 PC 的 docs/explanation 三篇，你会非常清楚地看到 PC 选了哪条路、避开了什么（自编辑 vs 审核、覆盖写 vs 不可变 revision）；
3. 用你熟悉的维度——`PreparedContext`=有界召回、`Review`=治理——反推其他系统对应概念，就能横向读懂整个生态。

要不要我**把 PC 与上面 3-4 个主流系统做一张逐概念对照表**（Memory/Handoff/召回/写入/审核/Scope 各维度），这样你一次看清 PC 和 Mem0/Letta/Zep 到底哪里同、哪里不同？