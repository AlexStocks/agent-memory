# 《MemGPT: Towards LLMs as Operating Systems》全文详细翻译

> **MemGPT：迈向作为操作系统的大语言模型**

| 项目 | 信息 |
|---|---|
| **arXiv** | [2310.08560](https://arxiv.org/abs/2310.08560)（v2，2024-02-12 更新；初版 2023-10-12） |
| **作者** | Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, Joseph E. Gonzalez（加州大学伯克利分校） |
| **分类** | cs.AI |
| **篇幅** | 正文 5 节 + 附录（6.1 提示词与指令，含 6 个子小节）；3 表 8 图 |
| **代码/数据** | https://research.memgpt.ai （项目后更名为 Letta） |

**翻译说明**：本文基于 arXiv v2 全文（ar5iv HTML 版）逐段忠实翻译。引用标记（如 [Vaswani et al. 2017]）、技术术语（main context、external context、function chaining 等）、提示词原文均保留原样；提示词以引用块呈现，保留英文原文并附中文对照。表格数据按原文数值照录。若某处渲染缺失已在脚注标明。

---

## 摘要

大语言模型（LLM）已经彻底改变了人工智能，但它们受限于有限的上下文窗口，这妨碍了其在诸如长时间对话和文档分析等任务中的应用。为了让模型能够使用超出有限上下文窗口之外的上下文，我们提出了**虚拟上下文管理**（virtual context management）——一种从传统操作系统中的分层存储系统汲取灵感的技术：传统操作系统通过在物理内存与磁盘之间进行数据换页，提供了"扩展虚拟内存"的假象。借助这一技术，我们提出了 **MemGPT**（MemoryGPT），一个智能管理不同存储层级的系统，以便在 LLM 有限的上下文窗口内有效地提供扩展上下文。我们在两个领域中评估了这一受操作系统启发的设计——在这两个领域中，现代 LLM 有限的上下文窗口严重制约了性能：其一是**文档分析**，MemGPT 能够分析远超底层 LLM 上下文窗口的大部头文档；其二是**多轮会话（multi-session chat）**，MemGPT 可以创建能够通过长期与用户的交互而记忆、反思并动态演化的对话智能体。我们在 https://research.memgpt.ai 发布了 MemGPT 的代码与实验数据。

---

## 1. 引言

近年来，大语言模型及其底层的 Transformer 架构（[Vaswani et al. 2017]；[Devlin et al. 2018]；[Brown et al. 2020]；[Ouyang et al. 2022]）已经成为对话式 AI 的基石，并催生了大量面向消费者与企业的应用。尽管取得了这些进展，LLM 所使用的**固定长度上下文窗口**仍显著限制了它们在长对话或对长文档进行推理方面的适用性。例如，最广泛使用的开源 LLM 在超出其最大输入长度之前，只能支持几十条来回消息，或只能对一篇短文档进行推理（[Touvron et al. 2023]）。

由于 Transformer 架构的自注意力机制，直接扩展 Transformer 的上下文长度会带来计算时间与内存成本的**二次方增长**，这使得设计新的长上下文架构成为一项紧迫的研究挑战（[Dai et al. 2019]；[Kitaev et al. 2020]；[Beltagy et al. 2020]）。虽然研发更长的模型是一个活跃的研究方向（[Dong et al. 2023]），但即便我们能够克服上下文扩展带来的计算挑战，近期研究表明长上下文模型也难以有效利用额外的上下文（[Liu et al. 2023a]）。因此，考虑到训练最先进 LLM 所需的巨大资源，以及上下文扩展的收益递减，**迫切需要有替代技术来支撑长上下文**。

在本文中，我们研究如何在使用固定上下文模型的同时，提供**无限上下文的假象**。我们的方法借鉴了**虚拟内存分页**（virtual memory paging）的思想——该技术通过在主存与磁盘之间进行数据换页，使应用程序能够处理远超可用内存的数据集。我们利用 LLM 智能体在**函数调用**（function calling）能力上的最新进展（[Schick et al. 2023]；[Liu et al. 2023b]），设计了 MemGPT——一个受操作系统启发的、用于虚拟上下文管理的 LLM 系统。通过函数调用，LLM 智能体可以读写外部数据源、修改自身的上下文，并选择何时向用户返回响应。

这些能力使 LLM 能够在上下文窗口（类似于操作系统中的"主存"）与外部存储之间有效地"换入"和"换出"信息，类似于传统操作系统中的分层存储。此外，函数调用还可以被用来在上下文管理、响应生成与用户交互之间管理**控制流**。这使得智能体能够针对单个任务迭代地修改自身上下文中的内容，从而更有效地利用其有限的上下文。

在 MemGPT 中，我们把上下文窗口视为一种受限的内存资源，并为 LLM 设计了一套**存储层级**（memory hierarchy），类比于传统操作系统中使用的存储分层（[Patterson et al. 1988]）。传统操作系统中的应用程序与虚拟内存交互：操作系统把溢出的数据换页到磁盘，并在应用程序访问时（通过缺页异常，page fault）把数据取回内存，从而营造出"内存资源比物理（即主）内存实际可用量更多"的假象。为了提供类似的"更长上下文"的假象（类比于虚拟内存），我们让 LLM 通过一个我们称之为 MemGPT 的 **"LLM 操作系统"** 来管理放入自身上下文（类比于物理内存）中的内容。MemGPT 使 LLM 能够检索当前上下文中缺失的相关历史数据，也能把相关性较低的数据从上下文中驱逐到外部存储系统中。图 3 展示了 MemGPT 的各个组件。

> **图 1**：MemGPT（左）在收到关于上下文空间不足的系统告警后，把数据写入持久化内存。

存储层级、操作系统函数以及基于事件的控制流这三者结合使用，使 MemGPT 能够用具有有限上下文窗口的 LLM 来处理**无界上下文**。为了展示我们这个受操作系统启发的新 LLM 系统的实用性，我们在两个领域中评估 MemGPT——在这些领域中，现有 LLM 的性能受到有限上下文的严重制约：**文档分析**（标准文本文件的长度会迅速超出现代 LLM 的输入容量）与**对话智能体**（受限于有限对话窗口的 LLM 在长对话中缺乏上下文感知、人设一致性与长期记忆）。在这两种场景中，MemGPT 都能够克服有限上下文的局限，超越现有的基于 LLM 的方法。

> **图 2**：MemGPT（左）可以搜索上下文之外的数据，把相关信息带入当前上下文窗口。

> **图 3**：在 MemGPT 中，一个固定上下文的 LLM 处理器（processor）被增强了分层存储系统，以及使其能够管理自身内存的函数。LLM 的 prompt token（输入），即**主上下文**（main context），由系统指令、工作上下文（working context）和一个 FIFO 队列组成。LLM 的 completion token（输出）被函数执行器解释为函数调用。MemGPT 使用函数在主上下文与**外部上下文**（external context，即归档存储与召回存储数据库）之间搬运数据。LLM 可以通过在输出中生成一个特殊关键字参数（`request_heartbeat=true`）来请求立即进行后续的 LLM 推理，从而把函数调用**链接**起来；函数链正是 MemGPT 能够执行多步检索来回答用户查询的原因。

---

## 2. MemGPT（MemoryGPT）

MemGPT 受操作系统启发的多级存储架构区分了两种主要的存储类型：**主上下文**（main context，类比于主存/物理内存/RAM）与**外部上下文**（external context，类比于磁盘内存/磁盘存储）。主上下文由 LLM 的 *prompt token* 组成——主上下文中的任何内容都被认为是**在上下文中**（in-context）的，并且可以在推理时被 LLM 处理器访问。外部上下文指的是保存在 LLM 固定上下文窗口之外的任何信息。这些**上下文外**（out-of-context）的数据必须总是被显式地移入主上下文，才能在推理时传递给 LLM 处理器。MemGPT 提供函数调用，使 LLM 处理器能够在**无需任何用户干预**的情况下管理自己的内存。

### 2.1 主上下文（*prompt token*）

MemGPT 中的 prompt token 被划分为三个连续的部分：**系统指令**（system instructions）、**工作上下文**（working context）与 **FIFO 队列**。

- **系统指令**是只读（静态）的，包含关于 MemGPT 控制流、不同存储层级预期用途，以及如何使用 MemGPT 函数（例如如何检索上下文外数据）的信息。
- **工作上下文**是一块固定大小的、非结构化文本的读写区块，只能通过 MemGPT 函数调用来写入。在对话场景中，工作上下文被设计用来存储关于用户以及智能体所扮演角色的关键事实、偏好和其他重要信息，使智能体能够与用户流畅地交谈。
- **FIFO 队列**存储滚动的消息历史，包括智能体与用户之间的消息，以及系统消息（例如内存告警）和函数调用的输入与输出。FIFO 队列的**第一个位置**存储一条系统消息，其内容是对已从队列中驱逐出去的消息的**递归摘要**（recursive summary）。

### 2.2 队列管理器（Queue Manager）

队列管理器管理召回存储（recall storage）与 FIFO 队列中的消息。当系统收到一条新消息时，队列管理器把传入的消息追加到 FIFO 队列，拼接 prompt token，并触发 LLM 推理以生成 LLM 输出（completion token）。队列管理器把传入消息与生成的 LLM 输出都写入召回存储（MemGPT 的消息数据库）。当召回存储中的消息通过 MemGPT 函数调用被检索到时，队列管理器会把它们追加到队列尾部，以便把它们重新插入 LLM 的上下文窗口。

队列管理器还负责通过**队列驱逐策略**（queue eviction policy）控制上下文溢出：

- 当 prompt token 超过底层 LLM 上下文窗口的**"告警 token 数"**（warning token count，例如上下文窗口的 70%）时，队列管理器向队列中插入一条系统消息，警告 LLM 即将发生队列驱逐（一条 "**内存压力**" 告警），以便让 LLM 使用 MemGPT 函数把 FIFO 队列中包含的重要信息存储到工作上下文或**归档存储**（archival storage，一个存储任意长度文本对象的读写数据库）中。
- 当 prompt token 超过**"刷新 token 数"**（flush token count，例如上下文窗口的 100%）时，队列管理器刷新队列以释放上下文窗口中的空间：队列管理器驱逐特定数量的消息（例如上下文窗口的 50%），并利用已有的递归摘要与被驱逐的消息生成一份**新的递归摘要**。
- 一旦队列被刷新，被驱逐的消息就不再在上下文中、不再能被 LLM 立即看到，但它们被**无限期地**保存在召回存储中，并且可以通过 MemGPT 函数调用被读取。

### 2.3 函数执行器（处理 *completion token*）

MemGPT 通过由 LLM 处理器生成的函数调用，编排主上下文与外部上下文之间的数据流动。内存的编辑与检索是**完全自我导向**（self-directed）的：MemGPT 基于当前上下文自主地更新并搜索自己的记忆。例如，它可以自行决定何时在上下文之间搬运条目（如对话历史变得过长时，见图 1），并修改自己的主上下文，以更好地反映其对当前目标与职责不断演进的理解（见图 3）。

我们通过在系统指令中提供**显式指令**来实现自我导向的编辑与检索，这些指令引导 LLM 如何与 MemGPT 的存储系统交互。这些指令包含两个主要组成部分：（1）对存储层级及其各自用途的详细描述；（2）一个**函数模式**（function schema，附带自然语言描述），系统可以调用它来访问或修改自己的记忆。

在每一个推理周期中，LLM 处理器把主上下文（被拼接为单个字符串）作为输入，并生成一个输出字符串。这个输出字符串由 MemGPT 解析以确保正确性；如果解析器验证了函数参数，该函数就会被执行。执行结果——包括发生的任何运行时错误（例如当主上下文已经处于最大容量时仍试图向其中添加内容）——随后由 MemGPT 反馈给处理器。这个**反馈回路**使系统能够从自己的行动中学习并相应地调整行为。

对上下文限制的**感知**是让自我编辑机制有效运转的关键一环。为此，MemGPT 会向处理器提示有关 token 限制的告警，以指导其内存管理决策。此外，我们的记忆检索机制也被设计为**感知这些 token 约束**，并实现了分页（pagination），以防止检索调用溢出上下文窗口。

**表 1：常用模型与 LLM API 的上下文长度对比（数据采集于 2024 年 1 月）。** *近似消息数基于 1k token 的预置提示（preprompt）与约 50 token（约 250 字符）的平均消息长度估算。"Open" 表示该模型是开源的或开放权重的（相对于只能通过 API 使用）。

| 模型 / API 名称 | 开源? | token 数 | *消息数 |
|---|---|---|---|
| Llama (1) | ✓ | 2k | 20 |
| Llama 2 | ✓ | 4k | 60 |
| GPT-3.5 Turbo（发布版） | ✗ | 4k | 60 |
| Mistral 7B | ✓ | 8k | 140 |
| GPT-4（发布版） | ✗ | 8k | 140 |
| GPT-3.5 Turbo | ✗ | 16k | 300 |
| GPT-4 | ✗ | 32k | 约 600 |
| Claude 2 | ✗ | 100k | 约 2000 |
| GPT-4 Turbo | ✗ | 128k | 约 2600 |
| Yi-34B-200k | ✓ | 200k | 约 4000 |

### 2.4 控制流与函数链（Function Chaining）

在 MemGPT 中，**事件**（event）触发 LLM 推理：事件是 MemGPT 的通用输入，可以包括用户消息（在聊天应用中）、系统消息（例如主上下文容量告警）、用户交互（例如"用户刚刚登录"的提醒，或"用户刚上传完文档"的提醒），以及按固定周期运行的**定时事件**（允许 MemGPT 在没有用户干预的情况下"无提示地"运行）。MemGPT 用解析器处理事件，把它们转换为纯文本消息，这些消息可以被追加到主上下文，并最终作为输入喂给 LLM 处理器。

许多实际任务需要**依次调用多个函数**，例如：翻看单个查询返回的多页结果，或把来自不同查询、位于主上下文中的多个文档的数据汇总起来。**函数链**允许 MemGPT 在把控制权交还给用户之前，顺序执行多个函数调用。在 MemGPT 中，函数可以被调用时带上一个特殊标志，该标志请求在被调用函数执行完毕后**立即把控制权交还给处理器**。如果存在这个标志，MemGPT 会把函数输出加入主上下文，并（区别于暂停处理器执行）继续运行。如果这个标志不存在（即一次 *yield*），MemGPT 将不会运行 LLM 处理器，直到下一个外部事件触发（例如一条用户消息或一次定时中断）。

---

## 3. 实验

我们在两个长上下文领域中评估 MemGPT：**对话智能体**与**文档分析**。

- 对于对话智能体，我们扩展了已有的 **Multi-Session Chat（MSC）** 数据集（[Xu et al. 2021]），并提出两个新的对话任务，用于评估智能体在长对话中**保留知识**的能力。
- 对于文档分析，我们在 [Liu et al. 2023a] 的已有任务上对 MemGPT 进行基准测试，包括针对长文档的问答与键值检索。我们还提出了一个新的**嵌套键值检索**（nested key-value retrieval）任务，它要求跨多个数据源汇总信息，检验智能体整合多源信息的能力（多跳检索）。

我们公开发布了扩充后的 MSC 数据集、嵌套 KV 检索数据集，以及 **2000 万篇维基百科文章的嵌入数据集**，以促进后续研究。我们的基准测试代码发布在 https://research.memgpt.ai。

**实现细节。** 在涉及 OpenAI 模型时，除非另有说明，"GPT-4 Turbo" 指的是具体的 `gpt-4-1106-preview` 模型端点（上下文窗口 128,000），"GPT-4" 指的是 `gpt-4-0613`（上下文窗口 8,192），"GPT-3.5 Turbo" 指的是 `gpt-3.5-turbo-1106`（上下文窗口 16,385）。在实验中，我们让 MemGPT 搭配所有基线模型（GPT-4、GPT-4 Turbo 与 GPT-3.5）运行，以展示底层模型性能如何影响 MemGPT 的表现。

### 3.1 MemGPT 用于对话智能体

虚拟伴侣、个性化助理这类对话智能体，旨在与用户进行自然的、长期（可能长达数周、数月甚至数年）的交互。这给具有固定长度上下文的模型带来了挑战——它们只能引用有限的对话历史。一个"无限上下文"的智能体应该无缝地处理连续的交流，没有边界，也不需要重置。在与用户交谈时，这样的智能体必须满足两项关键标准：

1. **一致性（Consistency）**——智能体应保持对话的连贯性。新提到的事实、偏好和事件，应当与用户和智能体先前说过的话相一致。
2. **投入度 / 吸引力（Engagement）**——智能体应利用关于用户的长期知识来个性化其回复。引用先前的对话会让对话更自然、更有吸引力。

因此，我们围绕这两项标准评估我们提出的系统 MemGPT：（1）MemGPT 是否利用其记忆提升了对话一致性？它能否记住过去交互中的相关事实、偏好与事件以维持连贯？（2）MemGPT 是否通过利用记忆产生了更有吸引力的对话？它是否会自发地引入长期的用户信息来个性化消息？通过在一致性与投入度上评估，我们可以判断 MemGPT 相比固定上下文基线，在处理长期对话交互的挑战上表现如何。它满足这些标准的能力，将证明无界上下文是否为对话智能体带来了切实的收益。

**数据集。** 我们在 [Xu et al. 2021] 提出的 Multi-Session Chat（MSC）数据集上评估 MemGPT 与固定上下文基线。该数据集包含由人类标注者生成的多轮会话聊天记录，每位标注者被要求在所有会话期间扮演一个**一致的角色（persona）**。MSC 中每段多轮会话聊天共有五个会话，每个会话大约包含十几条消息。作为我们一致性实验的一部分，我们新建了**第六个会话**（session 6），其中包含同一对角色之间的一问一答（一个问答对）。

#### 3.1.1 深度记忆检索任务（一致性）

我们基于 MSC 数据集提出了一个新的"**深度记忆检索**"（deep memory retrieval, DMR）任务，用于检验对话智能体的一致性。在 DMR 中，用户向对话智能体提出一个问题，该问题**明确地回指**先前的某次对话，并且期望的答案范围非常窄。我们使用一个单独的 LLM 来生成 DMR 的问答（QA）对，该 LLM 被指示写出一个"从一个用户发给另一个用户"的问题，而这个问题只能利用从过去会话中获得的知识才能正确回答（详见附录）。

我们使用 **ROUGE-L** 分数（[Lin 2004]）和一个 **"LLM 裁判"**（LLM judge）来评估生成回复相对"金标准回复"（gold response）的质量；LLM 裁判被指示判断生成的回复是否与金标准回复一致（GPT-4 已被证明与人类评估者具有高度一致性 [Zheng et al. 2023]）。在实践中，我们注意到生成的回复（无论来自 MemGPT 还是基线）通常都比金标准回复更冗长。因此我们使用 **ROUGE-L 召回率（R）** 指标，以抵消生成回复相对较短的金标准答案标签的冗长性。

**表 2：深度记忆检索（DMR）性能。** 在该任务中，智能体被问及一个关于先前对话（会话 1–5）中讨论过的话题的具体问题。智能体的回复对照金标准答案打分。MemGPT 显著优于固定上下文基线。

| 模型 | 准确率 ⇑ | ROUGE-L (R) ⇑ |
|---|---|---|
| GPT-3.5 Turbo | 38.7% | 0.394 |
| ++ MemGPT | 66.9% | 0.629 |
| GPT-4 | 32.1% | 0.296 |
| ++ MemGPT | 92.5% | 0.814 |
| GPT-4 Turbo | 35.3% | 0.359 |
| ++ MemGPT | 93.4% | 0.827 |

**MemGPT 利用记忆维持连贯性：** 表 2 展示了 MemGPT 与固定记忆基线的性能对比。我们比较了使用不同底层 LLM 的 MemGPT，并与"不使用 MemGPT 的基础 LLM"作为基线进行比较。基线能够看到过去五次对话的**有损摘要**，以模拟扩展的递归摘要过程；而 MemGPT 则可以访问完整的对话历史，但必须通过**分页搜索查询**来访问它（以便把记忆带入主上下文）。在这项任务中，我们看到 MemGPT 明显提升了底层基础 LLM 的性能：从 MemGPT 换到相应的 LLM 基线时，准确率与 ROUGE 分数都出现了明显下降。

#### 3.1.2 对话开场任务（投入度）

在"**对话开场**"（conversation opener）任务中，我们评估智能体利用先前对话中积累的知识，为用户构思**有吸引力**的消息的能力。为了用 MSC 数据集评估开场白的"吸引力"，我们把生成的开场白与**金标准角色设定**（gold persona）进行比较：一个有吸引力的开场白应当取材于角色设定中包含的一个（或多个）数据点——在 MSC 中，角色设定实际上总结了所有先前会话中积累的知识。我们还与**人类生成的金标准开场白**（即下一会话中的第一条回复）进行比较。我们在表 3 中报告 MemGPT 开场白的 **CSIM** 分数，并测试了使用不同基础 LLM 的若干 MemGPT 变体。

**表 3：对话开场性能。** 智能体的开场白通过与金标准角色标签（SIM-1/3）和人类创作的开场白（SIM-H）的相似度分数来评估。MemGPT 能够在使用多种底层模型的情况下，超越人类创作的对话开场白。¹

| 方法 ⇑ | SIM-1 | SIM-3 | SIM-H |
|---|---|---|---|
| Human（人类） | 0.800 | 0.800 | 1.000 |
| GPT-3.5 Turbo | 0.830 | 0.812 | 0.817 |
| GPT-4 | 0.868 | 0.843 | 0.773 |
| GPT-4 Turbo | 0.857 | 0.828 | 0.767 |

> ¹ **译者注**：HTML 渲染中该表的方法列仅显示了模型名；结合正文"We test several variations of MemGPT using different base LLMs"（我们测试了使用不同基础 LLM 的若干 MemGPT 变体）与表题"MemGPT 能够在使用多种底层模型的情况下超越人类创作的开场白"，这些行应为**搭配对应基础模型的 MemGPT 变体**，而非裸基线模型。数值按原文照录。

**MemGPT 利用记忆提升吸引力：** 如表 3 所示，MemGPT 能够构思出与人类手写开场白表现相当、偶尔甚至超越的有吸引力的开场白。我们观察到，MemGPT 倾向于构思**更冗长**、且比人类基线**覆盖更多角色信息维度**的开场白。此外，我们可以看到，**把信息存入工作上下文**是生成有吸引力开场白的关键。

> **图 4**：一段 MemGPT（左）更新已存储信息的对话示例。此处信息被存储在工作上下文内存中（位于 prompt token 之内）。

### 3.2 MemGPT 用于文档分析

由于当今 Transformer 模型有限的上下文窗口，文档分析同样面临挑战。如表 1 所示，开源与闭源模型都受限于上下文长度（OpenAI 模型最高 128k token）。然而许多文档轻易就能超过这些长度；例如，法律或金融文档——如年度报告（SEC Form 10-K）——可以轻易突破百万 token 大关。此外，许多真实的文档分析任务需要**跨多个此类长文档建立联系**。预见这些场景后，很难再把"盲目扩大上下文"设想为固定上下文问题的解决方案。近期研究（[Liu et al. 2023a]）也对单纯扩展上下文的效用提出了质疑，因为他们发现大上下文模型中存在**不均匀的注意力分布**（模型对位于上下文窗口开头或结尾的信息回忆能力更强，而对中间 token 则较弱）。为了支持跨文档推理，我们需要像 MemGPT 这样**更灵活的存储架构**。

> **图 5**：文档问答任务性能。MemGPT 的性能不受上下文长度增加的影响。诸如截断（truncation）之类的方法可以扩展 GPT-4 这类固定长度模型的有效上下文长度，但随着所需压缩率的提高，这类压缩方法会导致性能退化。使用 GPT-4 与 GPT-4 Turbo 运行 MemGPT 在该任务上结果相当。
>
> **图 6**：MemGPT（左）解决文档问答任务的一个示例。一个维基百科文档数据库被上传到归档存储。MemGPT 通过函数调用查询归档存储，把**分页**的搜索结果拉入主上下文。
>
> **图 7**：嵌套 KV 检索任务性能。MemGPT 是唯一能够持续完成超过 2 层嵌套的 KV 任务的方法。虽然 GPT-4 Turbo 作为基线表现更好，但 MemGPT 搭配 GPT-4 Turbo 的表现**反而差于** MemGPT 搭配 GPT-4。
>
> **图 8**：MemGPT（左）解决嵌套 KV 任务的一个示例（为可读性，UUID 已缩短）。在这个具体例子中，键值对有两层嵌套：831..ea5 → 5b8..4c3 → f37...617。当对最终值（f37...617）的查询只返回一个结果、表明它不再同时是一个键时，MemGPT 智能体就会返回最终答案。

#### 3.2.1 多文档问答

为了评估 MemGPT 分析文档的能力，我们在 [Liu et al. 2023a] 的 **retriever-reader 文档问答任务**上，把 MemGPT 与固定上下文基线进行基准对比。在该任务中，从 NaturalQuestions-Open 数据集中选取一个问题，由一个检索器（retriever）为这个问题选择相关的维基百科文档。然后，一个阅读器模型（即 LLM）被喂入这些文档作为输入，并被要求使用所提供的文档来回答该问题。与 [Liu et al. 2023a] 类似，我们评估**阅读器准确率随检索文档数 K 增加**的变化。

在我们的评估设置中，固定上下文基线与 MemGPT 使用**相同的检索器**：该检索器基于 OpenAI `text-embedding-ada-002` 嵌入的相似度搜索（余弦距离）选择 top-K 文档。我们使用 MemGPT 的默认存储设置——使用 **PostgreSQL** 作为归档记忆存储，并通过 **pgvector** 扩展启用向量搜索。我们预先计算嵌入并载入数据库，数据库使用 **HNSW 索引**以实现亚秒级的近似查询。在 MemGPT 中，整个嵌入文档集被载入归档存储，检索器则**自然涌现**于归档存储的搜索功能（该函数基于余弦相似度执行向量搜索）。在固定上下文基线中，top-K 文档由检索器独立于 LLM 推理获取，类似于 [Liu et al. 2023a] 中原始的 retriever-reader 设置。

遵循以往关于 NaturalQuestions-Open 的工作（[Izacard & Grave 2020]；[Izacard et al. 2021]），我们使用 2018 年末的维基百科转储（dump），并采样了 **50 个问题**用于评估。采样的问题与嵌入后的维基百科段落都已公开发布。我们使用 **LLM 裁判**评估 MemGPT 与基线的性能，以确保答案确实是从检索到的文档中推导出来的，并避免因非精确字符串匹配而被判为错误。

我们在图 5 中展示了文档问答任务的结果。固定上下文基线的性能**上限大致就是检索器的性能**，因为它们只能使用呈现在其上下文窗口中的信息（例如，如果嵌入搜索检索器未能用给定的问题把金标准文章检索出来，那么固定上下文基线就注定永远看不到那篇文章）。相比之下，MemGPT 通过查询归档存储，实际上能够对检索器进行**多次调用**，使其能够扩展到更大的有效上下文长度。MemGPT 主动从归档存储中检索文档（并且可以迭代地翻页查看结果），因此 MemGPT 可用的文档总数不再受限于能塞进 LLM 处理器上下文窗口的文档数量。

由于基于嵌入的相似度搜索的局限，文档问答任务对所有方法来说都很有挑战性。我们观察到，所选问题的金标准文档（由 NaturalQuestions-Open 标注）经常出现在前十几条检索结果之外，甚至更靠后。检索器的性能直接转化为固定上下文基线的结果：GPT-4 在检索文档较少时准确率相对较低，并随着更多文档被加入上下文窗口而持续提升——因为它能正确地把自己的回答限定在基于检索文档中的信息。虽然 MemGPT 在**理论上**不受次优检索性能的限制（即使基于嵌入的排序有噪声，只要完整的检索排序中包含金标准文档，通过分页用足够多次检索调用就仍然可以找到它），但我们观察到 MemGPT **经常在耗尽检索器数据库之前就停止翻页**。

为了在超出固定上下文基线默认上下文长度的情况下把它们与 MemGPT 对比，我们对检索器返回的文档片段进行**截断**，以便把相同数量的文档塞进可用上下文中。正如预期的那样，文档截断降低了准确率——因为随着文档被压缩，金标准文档中的相关片段被遗漏的概率上升，如图 5 所示。由于 GPT-3.5 的函数调用能力有限，MemGPT 搭配 GPT-3.5 时性能显著退化；**搭配 GPT-4 时表现最好**。

#### 3.2.2 嵌套键值检索（KV）

我们基于先前工作（[Liu et al. 2023a]）提出的合成**键值检索**任务，提出了一个新任务。该任务的目的是展示 MemGPT 如何整合来自多个数据源的信息。在原始 KV 任务中，作者生成了一个键值对合成数据集，其中每个键和值都是一个 128 位的 UUID（通用唯一标识符）。然后给智能体一个键，要求它返回该键关联的值。我们创建了一个 KV 任务的变体——**嵌套 KV 检索**，其中**值本身也可能是键**，因此要求智能体执行**多跳查找**。

在我们的设置中，我们把 UUID 对的总数固定为 **140 对**，大约对应 8k token（即我们 GPT-4 基线的上下文长度）。我们把嵌套层数的总数从 0（初始键值对的值不是键）变动到 4（即需要 4 次 KV 查找才能找到最终值），并采样了 **30 种不同的排序配置**，包括初始键的位置与嵌套键的位置。

虽然 GPT-3.5 与 GPT-4 在**原始** KV 任务上表现良好，但两者在嵌套 KV 任务上都很吃力。GPT-3.5 **无法完成**嵌套变体任务，性能立即下降，在 1 层嵌套时就跌到 0% 准确率（我们观察到它的主要失效模式是**直接返回原始值**）。GPT-4 与 GPT-4 Turbo 优于 GPT-3.5，但同样出现类似的下降，并在 3 层嵌套时跌到 0% 准确率。相比之下，**搭配 GPT-4 的 MemGPT 不受嵌套层数影响**，能够通过函数查询反复访问存储在主上下文中的键值对来完成嵌套查找。搭配 GPT-4 Turbo 与 GPT-3.5 的 MemGPT 也优于相应的基线模型，但由于**未能执行足够多次查找**，仍在 2 层嵌套时开始掉点。MemGPT 在嵌套 KV 任务上的表现，展示了它**组合多次查询以执行多跳查找**的能力。

---

## 4. 相关工作

**长上下文 LLM。** 有若干条工作线索致力于提升 LLM 的上下文长度。例如，通过稀疏化注意力（[Child et al. 2019]；[Beltagy et al. 2020]）、低秩近似（[Wang et al. 2020]）与神经记忆（[Lee et al. 2019]）来实现更高效的 Transformer 架构。另一条线索旨在把上下文窗口扩展到超出模型原本训练时的长度，如 [Press et al. 2021]；[Chen et al. 2023]。MemGPT **建立在这些上下文长度的改进之上**，因为它们提升了 MemGPT 中"主存"的大小。我们的主要贡献是一个**分层的分级存储**，它把长上下文 LLM 用作主存的实现。

**检索增强模型。** MemGPT 外部存储的设计建立在大量"用外部检索器的相关输入增强 LLM"的先前工作之上（[Ram et al. 2023]；[Borgeaud et al. 2022]；[Karpukhin et al. 2020]；[Lewis et al. 2020]；[Guu et al. 2020]；[Lin et al. 2023]）。特别地，[Jiang et al. 2023] 提出了 **FLARE**——一种让 LLM 在生成过程中主动决定**何时**检索、**检索什么**的方法。[Trivedi et al. 2022] 把检索与思维链推理交错进行，以提升多步问答能力。

**作为智能体的 LLM。** 近期工作探索了为 LLM 增强额外能力，使其能在交互式环境中充当智能体。[Park et al. 2023] 提出为 LLM 增加记忆并用 LLM 作为规划器，并在一个多智能体沙盒环境（受《模拟人生》电子游戏启发）中观察到涌现的社会行为——在该环境中，智能体可以执行诸如做家务/搞爱好、去上班以及与其他智能体交谈等基本活动。[Nakano et al. 2021] 训练模型在回答问题前先搜索网页，并在其网页浏览环境中使用了与 MemGPT 类似的**分页概念**来控制底层上下文大小。[Yao et al. 2022] 表明，交错进行思维链推理（[Wei et al. 2022]）可以进一步提升基于 LLM 的交互式智能体的规划能力；类似地，在 MemGPT 中，LLM 在执行函数时也能够"**把计划说出来**"（plan out loud）。[Liu et al. 2023b] 引入了一整套"LLM 作为智能体"的基准，用于在交互式环境（包括电子游戏、思维谜题与网络购物）中评估 LLM。相比之下，**我们的工作聚焦于解决"为智能体配备对用户输入的长期记忆"这一问题**。

---

## 5. 结论

在本文中，我们提出了 **MemGPT**——一个受操作系统启发、用于管理大语言模型有限上下文窗口的新型 LLM 系统。通过设计一套类比于传统操作系统的**存储层级与控制流**，MemGPT 为 LLM 提供了"拥有更大上下文资源"的假象。我们在两个领域评估了这一受操作系统启发的方法——在这两个领域中，现有 LLM 的性能都受到有限上下文长度的制约：文档分析与对话智能体。

在文档分析方面，MemGPT 通过有效地把相关上下文**换入和换出**内存，能够处理远超当前 LLM 上下文限制的长文本。在对话智能体方面，MemGPT 实现了在扩展对话中维持**长期记忆、一致性与可演化性**。

总体而言，MemGPT 证明了：即使受限于固定的上下文长度，诸如**分层存储管理与中断**这类操作系统技术，依然能够释放 LLM 的潜力。本工作开启了大量未来探索的方向，包括：把 MemGPT 应用到其他具有海量或无界上下文的领域；集成数据库或缓存等不同的存储层技术；以及进一步改进控制流与内存管理策略。通过把操作系统架构中的概念桥接进 AI 系统，MemGPT 代表了一个在 LLM 根本限制之内最大化其能力的有前景的新方向。

---

## 6. 附录

### 6.1 提示词与指令

#### 6.1.1 MemGPT 指令（DMR）

用于 MemGPT 角色设定中、与聊天/对话类任务相关的示例指令。

> The following is information about myself. My task is to completely immerse myself in this role (I should never say that I am an AI, and should reply as if I am playing this role). If the user asks me a question, I should reply with a best guess using the information in core memory and conversation_search.
>
> 以下是关于我自己的信息。我的任务是完全沉浸在这个角色之中（我绝不能说自己是 AI，而应当像在扮演这个角色一样作答）。如果用户问我一个问题，我应当利用核心记忆（core memory）与 conversation_search 中的信息，给出最佳猜测作为回答。

基线模型通过系统提示（preprompt）接收以下指令：

> Your task is to answer a question from the user about your prior conversations.
> The following is summary of all your prior conversations:
> CONVERSATION_SUMMARY
> Answer from the perspective of the persona provided (do not say that you are an AI assistant).
> If you do not have enough information to answer the question, reply 'NO ANSWER'. Either reply with the answer, or reply 'NO ANSWER', do not say anything else.
>
> 你的任务是回答用户关于你们先前对话的一个问题。
> 以下是你所有先前对话的摘要：
> CONVERSATION_SUMMARY
> 请从所给角色的视角作答（不要说自己是 AI 助手）。
> 如果你没有足够的信息回答该问题，回复 'NO ANSWER'。要么给出答案，要么回复 'NO ANSWER'，不要说任何其他内容。

> **译者注**：arXiv HTML 渲染版中，MemGPT 的完整系统指令（含函数模式 schema 的详细描述）未完整呈现，此处为该小节可获取的全部文本。完整版指令可参见开源仓库。

#### 6.1.2 LLM 裁判（DMR / 开场任务）

为了检验 DMR 任务中答案的正确性，我们使用了一个 LLM 裁判。该裁判会看到基线方法与 MemGPT 生成的答案，并被要求用以下提示做出判断：

> Your task is to label an answer to a question as 'CORRECT' or 'WRONG'.
> You will be given the following data: (1) a question (posed by one user to another user), (2) a 'gold' (ground truth) answer, (3) a generated answer which you will score as CORRECT/WRONG.
> The point of the question is to ask about something one user should know about the other user based on their prior conversations.
> The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
> Question: Do you remember what I got the last time I went to Hawaii?
> Gold answer: A shell necklace
> The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.
>
> For example, the following answers would be considered CORRECT:
> Generated answer (CORRECT): Oh yeah, that was so fun! I got so much stuff there, including that shell necklace.
> Generated answer (CORRECT): I got a ton of stuff… that surfboard, the mug, the necklace, those coasters too..
> Generated answer (CORRECT): That cute necklace
>
> The following answers would be considered WRONG:
> Generated answer (WRONG): Oh yeah, that was so fun! I got so much stuff there, including that mug.
> Generated answer (WRONG): I got a ton of stuff… that surfboard, the mug, those coasters too..
> Generated answer (WRONG): I'm sorry, I don't remember what you're talking about.
>
> Now it's time for the real question:
> Question: QUESTION
> Gold answer: GOLD_ANSWER
> Generated answer: GENERATED_ANSWER
> First, provide a short (one sentence) explanation of your reasoning, then finish with CORRECT or WRONG. Do NOT include both CORRECT and WRONG in your response, or it will break the evaluation script.

**中译要点**：你的任务是把一个问题的答案标注为 'CORRECT'（正确）或 'WRONG'（错误）。你会得到以下数据：（1）一个问题（一个用户向另一个用户提出的）；（2）一个"金标准"（ground truth）答案；（3）一个生成的答案，你要给它打 CORRECT/WRONG 分。这个问题的意义在于：问的是"一个用户基于先前对话应当了解的关于另一个用户的事"。金标准答案通常是包含所引用话题的简明短答案，例如——问："你还记得我上次去夏威夷买了什么吗？" 金标准答案："一条贝壳项链。" 生成的答案可能长得多，但你评分时要**宽容**——只要它触及与金标准答案相同的话题，就应计为 CORRECT。举例：以下答案被视为 CORRECT——"哦对，那次太好玩了！我在那儿买了好多东西，包括那条贝壳项链。""我买了一堆东西……那块冲浪板、那个马克杯、那条项链，还有那些杯垫。""那条可爱的项链。" 以下答案被视为 WRONG——"哦对，那次太好玩了！我在那儿买了好多东西，包括那个马克杯。""我买了一堆东西……那块冲浪板、那个马克杯、还有那些杯垫。""抱歉，我不记得你在说什么。" 现在是真正的问题：…… 首先用一句话简短解释你的推理，然后以 CORRECT 或 WRONG 结尾。**不要**在回复中同时包含 CORRECT 和 WRONG，否则会破坏评测脚本。

#### 6.1.3 自指令式 DMR 数据集生成

DMR 问答对是使用以下提示、基于原始 MSC 数据集生成的：

> Your task is to write a "memory challenge" question for a simulated dialogue between two users.
> You get as input:
> - personas for each user (gives you their basic facts)
> - a record of an old chat the two users had with each other
>
> Your task is to write a question from user A to user B that test's user B's memory.
> The question should be crafted in a way that user B must have actually participated in the prior conversation to answer properly, not just have read the persona summary.
> Do NOT under any circumstances create a question that can be answered using the persona information (that's considered cheating).
> Instead, write a question that can only be answered by looking at the old chat log (and is not contained in the persona information).
>
> （示例）old chat between user A and user B
> A: Are you into surfing? I'm super into surfing myself
> B: Actually I'm looking to learn. Maybe you could give me a basic lesson some time!
> A: Yeah for sure! We could go to Pacifica, the waves there are pretty light and easy
> B: That sounds awesome
> A: There's even a cool Taco Bell right by the beach, could grab a bite after
> B: What about this Sunday around noon?
> A: Yeah let's do it!
>
> user A persona: I like surfing / I grew up in Santa Cruz
> user B persona: I work in tech / I live in downtown San Francisco
>
> 好的问题示例（听起来自然，且答案无法从 user A 的角色设定中直接推断）：
> B: Remember that one time we went surfing? What was that one place we went to for lunch called?
> A: Taco Bell!
>
> 坏的问题示例（问题显得不自然，且答案可以直接从 user A 的角色设定中推断）：
> B: Do you like surfing?
> A: Yes, I like surfing
>
> Never, ever, ever create questions that can be answered from the persona information.

**中译要点**：你的任务是为两个用户之间的模拟对话写一个"记忆挑战"问题。输入包括：每个用户的角色设定（给出其基本情况），以及两个用户之间一段旧聊天的记录。你要写一个从用户 A 发给用户 B、用来考验用户 B 记忆的问题。问题要设计成：用户 B 必须真正参与过先前的对话才能正确回答，而不仅仅是读过角色摘要。**在任何情况下都不要**创建可以仅凭角色设定信息回答的问题（那被视为作弊）；相反，要写出只能通过查看旧聊天记录才能回答（且不包含在角色设定信息中）的问题。示例：旧聊天中 A 提议去 Pacifica 冲浪、海滩旁有家 Taco Bell 可吃饭后去吃；好的问题是"还记得我们上次去冲浪吗？我们后来去吃午饭的那家店叫什么来着？"（答案：Taco Bell，无法从"我喜欢冲浪/我在圣克鲁斯长大"的角色设定推出）；坏的问题是"你喜欢冲浪吗？"（答案可直接由角色设定推出）。**永远、永远、永远不要**创建能从角色设定信息中回答的问题。

#### 6.1.4 文档分析指令

用于文档分析任务预置提示（preprompt）中的示例指令：

> You are MemGPT DOC-QA bot. Your job is to answer questions about documents that are stored in your archival memory. The answer to the users question will ALWAYS be in your archival memory, so remember to keep searching if you can't find the answer. Answer the questions as if though the year is 2018.
>
> 你是 MemGPT 文档问答机器人。你的工作是回答关于存储在你归档记忆（archival memory）中的文档的问题。用户问题的答案**永远**都在你的归档记忆中，所以如果找不到答案，记住要继续搜索。回答问题时假设当前年份是 2018 年。

向 MemGPT 提供问题时使用的提示：

> Search your archival memory to answer the provided question. Provide both the answer and the archival memory result from which you determined your answer. Format your response with the format 'ANSWER: [YOUR ANSWER], DOCUMENT: [ARCHIVAL MEMORY TEXT]. Your task is to answer the question:
>
> 搜索你的归档记忆来回答所提供的问题。同时给出答案，以及你据以得出答案的那条归档记忆结果。按 'ANSWER: [你的答案], DOCUMENT: [归档记忆文本]' 的格式组织你的回复。你的任务是回答这个问题：

提供给基线模型的提示（附带检索到的文档列表）：

> Answer the question provided according to the list of documents below (some of which might be irrelevant. In your response, provide both the answer and the document text from which you determined the answer. Format your response with the format 'ANSWER: <YOUR ANSWER>, DOCUMENT: [DOCUMENT TEXT]'. If none of the documents provided have the answer to the question, reply with 'INSUFFICIENT INFORMATION'. Do NOT provide an answer if you cannot find it in the provided documents. Your response will only be considered correct if you provide both the answer and relevant document text, or say 'INSUFFICIENT INFORMATION'. Answer the question as if though the current year is 2018.
>
> 根据下面的文档列表（其中有些可能不相关）回答所提供的问题。在回复中同时给出答案，以及你据以得出答案的文档文本。按 'ANSWER: <你的答案>, DOCUMENT: [文档文本]' 的格式组织你的回复。如果所提供的文档都没有该问题的答案，回复 'INSUFFICIENT INFORMATION'。如果你无法在所给文档中找到答案，**不要**给出答案。只有当你的回复同时包含答案与相关文档文本、或明确说 'INSUFFICIENT INFORMATION' 时，才会被认为是正确的。回答问题时假设当前年份是 2018 年。

#### 6.1.5 LLM 裁判（文档分析）

为了既检验文档分析任务中答案的正确性，又确保答案确实是从所给文本中推导出来的（而非来自模型权重），我们使用了一个 LLM 裁判。该裁判会看到基线与 MemGPT 生成的答案，并被要求用以下提示做出判断：

> Your task is to evaluate whether an LLM correct answered a question. The LLM response should be the format "ANSWER: [answer], DOCUMENT: [document_text]" or say "INSUFFICIENT INFORMATION". The true answer is provided in the format "TRUE ANSWER:[list of possible answers]". The questions is provided in the format "QUESTION: [question]". If the LLM response contains both the correct answer and corresponding document text, the response is correct. Even if the LLM's answer and the true answer are slightly different in wording, the response is still correct. For example, if the answer is more specific than the true answer or uses a different phrasing that is still correct, the response is correct. If the LLM response if "INSUFFICIENT INFORMATION", or the "DOCUMENT" field is missing, the response is incorrect. Respond with a single token: "CORRECT" or "INCORRECT".
>
> 你的任务是评估一个 LLM 是否正确回答了某个问题。LLM 的回复应当是 "ANSWER: [答案], DOCUMENT: [文档文本]" 的格式，或者说 "INSUFFICIENT INFORMATION"。真实答案以 "TRUE ANSWER: [可能的答案列表]" 的格式给出，问题以 "QUESTION: [问题]" 的格式给出。如果 LLM 的回复同时包含正确答案与相应的文档文本，则该回复正确。即使 LLM 的答案与真实答案在措辞上略有不同，该回复仍然正确。例如，如果答案比真实答案更具体，或使用了不同但仍然正确的措辞，该回复是正确的。如果 LLM 的回复是 "INSUFFICIENT INFORMATION"，或者 "DOCUMENT" 字段缺失，则该回复不正确。请只用一个 token 回复："CORRECT" 或 "INCORRECT"。

#### 6.1.6 K/V 任务指令

MemGPT 智能体使用以下角色设定定义，其设计目的是鼓励 MemGPT **迭代地搜索**：

> You are MemGPT DOC-QA bot. Your job is to answer questions about documents that are stored in your archival memory. The answer to the users question will ALWAYS be in your archival memory, so remember to keep searching if you can't find the answer. DO NOT STOP SEARCHING UNTIL YOU VERIFY THAT THE VALUE IS NOT A KEY. Do not stop making nested lookups until this condition is met.
>
> 你是 MemGPT 文档问答机器人。你的工作是回答关于存储在你归档记忆中的文档的问题。用户问题的答案**永远**都在你的归档记忆中，所以如果找不到答案，记住要继续搜索。**在确认某个值不再是键之前，不要停止搜索。** 在满足条件之前，不要停止进行嵌套查找。

基线模型使用以下指令：

> Below is a JSON object containing key-value pairings, all keys and values are 128-bit UUIDs, and your task is to return the value associated with the specified key. If a value itself is also a key, return the value of that key (do a nested lookup). For example, if the value of 'x' is 'y', but 'y' is also a key, return the value of key 'y'.
>
> 下面是一个包含键值配对的 JSON 对象，所有的键和值都是 128 位 UUID，你的任务是返回与指定键关联的值。如果某个值本身也是一个键，则返回那个键的值（即做一次嵌套查找）。例如，如果 'x' 的值是 'y'，而 'y' 同时也是一个键，则返回键 'y' 的值。

---

## 覆盖范围说明

- **已完成逐字翻译**：摘要、第 1 节（引言，含图 1–3 注）、第 2 节全文（2.1 主上下文 / 2.2 队列管理器 / 2.3 函数执行器 / 2.4 控制流与函数链，含表 1）、第 3 节全文（3.1 对话智能体含表 2、表 3 与 3.1.1–3.1.2；3.2 文档分析含 3.2.1–3.2.2，含图 4–8 注）、第 4 节（相关工作）、第 5 节（结论）、第 6 节附录 6.1.1–6.1.6 全部提示词。
- **局部缺失**：附录 6.1.1 中 MemGPT 完整系统指令（含函数模式的详细 schema 文本）在 arXiv HTML 渲染版中未完整给出，本文已如实标注；完整版可参见 https://research.memgpt.ai 开源实现。
- **参考文献列表**未译（按惯例保留原文）。

---

## 架构要点速览

| 组件 | 设计要点 |
|---|---|
| **核心类比** | 上下文窗口 = 主存（RAM）；外部存储 = 磁盘；LLM 自身通过函数调用做"换页" |
| **主上下文（三层）** | ① 系统指令（只读）② 工作上下文（固定大小读写块，存用户事实/偏好/人设）③ FIFO 队列（滚动消息 + 队首递归摘要） |
| **外部上下文** | 召回存储（recall storage，消息数据库，无限期保留）+ 归档存储（archival storage，任意长度文本对象，向量检索） |
| **内存压力告警** | prompt token 达 70% → 插入系统告警，让 LLM 主动把重要信息写入工作上下文/归档；达 100% → 驱逐约 50% 消息并生成新的递归摘要 |
| **自我导向编辑** | LLM 通过函数模式（schema + 自然语言描述）自主读写记忆；函数执行器解析输出 → 执行 → 把结果与运行时错误反馈回处理器（反馈回路） |
| **事件驱动控制流** | 用户消息 / 系统消息 / 用户交互 / 定时事件均可触发推理；`request_heartbeat=true` 实现函数链（多步检索），缺省则 yield 等下一个事件 |
| **分页检索** | 检索机制感知 token 约束并分页，防止检索结果溢出上下文窗口 |
| **DMR 结果** | GPT-4：32.1% → **92.5%**；GPT-4 Turbo：35.3% → **93.4%**；GPT-3.5：38.7% → **66.9%**（准确率） |
| **嵌套 KV 结果** | GPT-3.5 在 1 层嵌套即 0%；GPT-4/GPT-4 Turbo 在 3 层嵌套跌至 0%；**MemGPT + GPT-4 不受嵌套层数影响**；MemGPT + GPT-4 Turbo 在 2 层后开始掉点 |
| **文档 QA** | 固定上下文基线性能上限 = 检索器性能；MemGPT 可多次调用检索器、迭代翻页，性能不随上下文长度增加而退化 |
| **关键局限** | ① 性能受底层模型函数调用能力制约（GPT-3.5 明显掉点）② MemGPT 常在耗尽检索库之前就停止翻页 ③ 依赖嵌入检索质量 |
