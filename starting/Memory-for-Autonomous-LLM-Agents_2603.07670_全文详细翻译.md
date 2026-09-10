# Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers —— 全文中文翻译

> **论文元数据**
>
> - **英文标题**：Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers
> - **中文标题**：自主 LLM 智能体的记忆：机制、评估与新兴前沿
> - **作者**：Pengfei Du
> - **arXiv**：[2603.07670](https://arxiv.org/abs/2603.07670)（固定翻译版本：v1，2026-03-08）
> - **篇幅**：15 页；HTML 结构统计为 2 个 figure 容器、3 个 table 元素
> - **翻译说明**：依据 arXiv HTML 与 PDF 对照进行分块翻译，并人工校订章节标题、摘要、核心术语、表格和结论；章节层级、公式、图注和正文引用均保留。参考文献保留英文原样，不逐条翻译。

---

###### 摘要（Abstract）

大语言模型（LLM）智能体越来越多地工作在这样的环境中：单个上下文窗口远不足以容纳已经发生的事情、智能体学到的内容，以及不应再次犯下的错误。记忆，即跨交互持久化、组织并选择性召回信息的能力，正是把无状态文本生成器变成真正自适应智能体的关键。

本综述系统梳理了现代 LLM 智能体中记忆的设计、实现和评估方法，覆盖 2022 年至 2026 年初的研究。作者将智能体记忆形式化为一个与感知和行动紧密耦合的“写入-管理-读取”循环，并提出由时间范围、表示载体和控制策略构成的三维分类法。论文深入讨论五类机制：上下文驻留压缩、检索增强存储、反思式自我改进、分层虚拟上下文，以及策略学习式管理。

在评估方面，论文追踪了从静态召回测试转向多会话智能体任务的变化，并分析四个揭示现有系统顽固短板的新基准。论文还考察个人助理、编码智能体、开放世界游戏、科学推理和多智能体协作等记忆具有决定性作用的应用，同时讨论写入过滤、矛盾处理、延迟预算和隐私治理等工程问题。最后，论文提出持续整合、因果驱动检索、可信反思、学习式遗忘，以及多模态和具身记忆等开放挑战。

关键词：大语言模型智能体；智能体记忆；长期记忆；检索增强生成；持续适应；智能体评估

## 1. 引言（Introduction）

大语言模型的规模扩展催生了一类新的自主软件智能体：它们能够感知环境、围绕目标推理、使用工具，并在较长时间跨度内采取行动 [Brown et al., 2020；Achiam et al., 2023；Touvron et al., 2023]。
这些智能体与普通聊天机器人的差别不只是模型更大，更重要的是人们期望它们能够“从经验中学习”。
编码助理应该记住某个 API 并不稳定；游戏智能体应该知道自己已经掌握了哪些合成配方；个人日程助理也不应该反复询问用户的生日。
所有这些都需要记忆。

### 1.1 没有记忆会出什么问题

想象一个调试助手在一个大型代码库上工作一周的会话。
如果没有记忆，每个星期一早上它都会重新发现目录布局，重新读取相同的 README，并且最糟糕的是重试周五导致构建崩溃的确切修复。
为相同的智能体配备一个适度的记忆模块和动态变化：它到达时已经知道热点，跳过死胡同，并逐渐提取特定于项目的启发式方法。

这不是边际进步；而是进步。这是质的变化。
记忆将无状态的 LLM 转换为 *自我进化* 智能体 [Zhang et al., 2024b]，它可以 (i) 积累事实知识和用户偏好，(ii) 开发基于先前经验的行为模式，(iii) 避免重复代价高昂的错误， (iv) 通过互动不断改进。

### 1.2 神经记忆简史

为神经网络提供外部存储的雄心可以追溯到十多年前。
Memory Networks [Weston 等人，2015] 及其端到端变体 [Sukhbaatar 等人，2015] 引入了对外部插槽的可区分读写访问以进行问答。
神经图灵机 [ Graves et al., 2014 ] 和可微分神经计算机 [ Graves et al., 2016 ] 进一步推进，支持通过记忆矩阵进行基于内容和基于位置的寻址。
Memorizing Transformers [ Wu et al., 2022 ] 和 Recurrent Memory Transformers [ Bulatov et al., 2022 ] 后来将显式记忆层直接集成到 Transformer 主干中。

专注于检索的并行线程。
RAG [Lewis et al., 2020] 将预训练的生成器与密集文档检索器结合起来，而 RETRO [Borgeaud et al., 2022] 表明，在推理时从*万亿*token语料库中提取可以在参数数量的一小部分匹配更大的模型。
这些系统证明了一个关键点：外部知识存储可以在生成过程中动态查询，而无需重新训练。

从检索增强 *型号* 到记忆增强型 *智能体* 的飞跃发生得很快。
ReAct [Yao et al., 2022] 将推理轨迹与环境行为交织在一起，产生可解释的轨迹，兼作短视界记忆。
Reflexion [Shinn et al., 2023] 更进一步，在任务尝试后存储口头自我批评——本质上是给智能体一份事后日志。
然后是生成式智能体论文 [Park et al., 2023]，其模拟的 25 个角色城镇证明，一个简单的观察-反思-规划循环可以产生数月的连贯社会行为。
自 2023 年以来，设计空间呈爆炸式增长：受操作系统启发的分层虚拟记忆 [Packer 等人，2024]、Minecraft 中不断增长的技能库[Wang 等人，2023a]、SQL 数据库作为符号记忆 [Hu 等人，2023] ]，以及最近通过强化学习端到端学习的记忆管理 [Yu et al., 2026]。

### 1.3 为什么还需要一篇综述？

几项广泛的智能体综述已经存在[Xi et al., 2023, Wang et al., 2024a]，以及Zhang et al., 2024a]。 [Zhang et al., 2024b] 于 2024 年发表了一篇记忆-focused 综述。
然而，自那时以来，情况发生了很大变化。
2025-2026 年贡献浪潮——智能体式记忆 [ Yu et al., 2026 ]、MemBench [ Tan et al., 2025 ]、MemoryAgentBench [ Hu et al., 2025 ]、 MemoryArena [He et al., 2026]—引入了学习型记忆控制、更丰富的评估维度以及将记忆与操作紧密结合的智能体式基准。

本综述重点关注 *记忆模块* 并提出三个问题：

1. RQ1

LLM 智能体中的记忆应该如何分解和形式化呢？
2. RQ2

存在哪些机制，它们会带来哪些权衡？
3. RQ3

当最终考验的是下游智能体性能时，应该如何评估记忆？

贡献。
我们将智能体记忆形式化为 POMDP-style 智能体循环中的写入-管理-读取循环（第 2 节），提出统一不同设计的三维分类法（第 3 节），通过具体系统比较提供深入的机制审查（第 4 节），综述基准以及实用指标堆栈（第 5 节），地图应用其中记忆是区分因素（第 6 节），讨论工程现实和架构模式（第 7 节），相对于先前综述的位置（第 8 节），并绘制开放研究方向（第 9 节）。

## 2. 问题形式化与设计目标

### 2.1 从记忆视角看智能体循环

在每个离散步骤 $t$ 中，智能体接收输入 $x\_{t}$（用户消息、传感器读数或工具返回值），并且必须产生操作 $a\_{t}$。
在这两个事件之间，它会查阅其累积的记忆。
我们写：

| | $\displaystyle a_{t}$ | $\displaystyle=\pi_{\theta}\!\bigl(x_{t},\;\mathcal{R}(M_{t},x_{t}),\;g_{t}\bigr),$ | | (1) |
| --- | --- | --- | --- | --- |
| | $\displaystyle M_{t+1}$ | $\displaystyle=\mathcal{U}\!\bigl(M_{t},x_{t},a_{t},o_{t},r_{t}\bigr),$ | | (2) |

其中 $\pi\_{\theta}$ 是策略（通常是提示或部分微调的 LLM），$\mathcal{R}$ 从记忆读取，$\mathcal{U}$ 写入并管理记忆， $g\_{t}$ 编码主动目标，$o\_{t}$ 是环境反馈，$r\_{t}$ 是任何类似奖励的信号。

有两个方面值得强调。
首先，$\mathcal{U}$“不是”简单的附加操作。
在设计良好的系统中，它会进行总结、删除重复、确定优先级、解决矛盾，并在适当的时候进行删除。
其次，$\pi\_{\theta}$ 和 $(\mathcal{R},\mathcal{U})$ 形成反馈循环：智能体的决策决定写入内容，而写入内容决定未来的决策。
这种递归依赖性使得记忆既强大又脆弱——一次错误的写入可能会污染下游许多步骤的存储。

### 2.2 与 POMDP 的联系

正式来说，上面的设置是一个部分可观察的马尔可夫决策过程。
记忆 $M\_{t}$ 扮演着智能体的“信念状态”的角色：历史的内部总结，代表了世界不可观察的真实状态。
经典的 POMDP 求解器通过贝叶斯过滤更新信念； LLM 智能体通过自然语言压缩、向量索引或结构化存储做类似的事情，尽管更混乱。

这个类比澄清了一个重要的点：智能体记忆不仅仅是一个数据库查找问题。
它是关于维护交互历史的“足够的统计数据”，以进行良好的操作选择，并受到硬计算和存储预算的影响。

### 2.3 五个设计目标及其张力

在我们审查的系统中，记忆机构沿五个轴拉动：

- 效用 – 记忆是否确实改善了任务结果？
- 效率 – 每单位效用的token、延迟和存储成本是多少？
- 适应性——系统能否在不进行全面重新训练的情况下根据交互反馈逐步更新？
- 忠实性——召回的信息是否准确且最新？陈旧的或幻觉的召回可能比根本没有召回更糟糕。
- 治理 – 系统是否尊重隐私、支持删除请求并遵守组织政策？

这些目标朝着相反的方向发展。
最大化实用性会诱使您存储所有内容，这会导致存储膨胀并造成治理难题。
积极的压缩提高了效率，但默默地放弃了一个罕见的事实，而三周后事实证明这一事实至关重要。
任何真正的部署都必须谨慎地进行这些权衡，并且“正确的”平衡点会随着应用的变化而变化。
医疗分诊智能体错过的过敏记录可能会危及生命，其运作的忠实性-效率边界与休闲食谱推荐器截然不同。
理解这些张力不仅仅是学术上的——它直接影响架构选择，正如我们在后续章节中讨论的那样。

### 2.4 记忆作为差异化因素：实证视角

记忆设计的实际重要性也许可以通过最新系统报告的消融结果得到最好的说明。
在生成式智能体实验中 [Park et al., 2023]，移除反射组件导致智能体行为从连贯的多日计划退化为 48 个模拟小时内的重复性、上下文无关的响应。
Voyager [Wang et al., 2023a] 没有技能库，在技术树里程碑速度上损失了 15.3$\times$——技能库*就是*性能。
在 MemoryArena [He et al., 2026] 中，将活动的记忆智能体替换为仅长上下文基线，使相互依赖的多会话任务的任务完成率从 80% 以上下降到大约 45%。

这些数字强调了一个反复出现的主题：“有记忆”和“没有记忆”之间的差距通常大于不同 LLM 主干之间的差距。
投资记忆架构可以产生与模型扩展相媲美或超过的回报。

## 3. 智能体记忆的统一分类法

认知科学家长期以来区分了人脑中的多个记忆系统 [Atkinson 和 Shiffrin, 1968, Tulving, 1972, Baddeley, 2000, Squire, 2004]。
智能体设计师常常无意识地反映了这种结构。
我们沿着三个正交维度组织空间。

### 3.1 时间范围

工作记忆。
当前上下文窗口内部的任何内容都构成了智能体的工作记忆。
Baddeley 的中央执行程序加缓冲区模型 [Baddeley, 2000] 映射得很清楚：LLM 是执行程序，上下文窗口是缓冲区，两者共享相同的瓶颈 - 有限的容量。

情节记忆。
具体经历的记录：单独的工具调用、对话轮流、环境观察。
在生成式智能体世界中 [Park et al., 2023]，每个观察结果（“伊莎贝拉下午 3 点看到克劳斯在公园里画画”）都会以时间戳、重要性得分以及后来的检索的嵌入形式出现在情景流中。

语义记忆。
抽象的、脱离情境的知识。
像“用户在 1 月 5 日、1 月 12 日和 2 月 1 日更正了日期格式”这样的情节事实可以合并到语义记录“用户更喜欢 DD/MM/YYYY”。
这种整合很少是自动的；大多数当前系统需要明确的提示或启发式触发器。

程序记忆。
可重用的技能和可执行的计划。
Voyager 的技能库 [Wang et al., 2023a] 是最明显的例子：每个经过验证的 Minecraft 例程都存储为可运行的 JavaScript，通过自然语言描述进行索引，并为新颖的任务动态组合。

在实践中，大多数智能体至少混合了其中的两种。
困难的问题是“转换策略”：情节记录何时升级到语义状态，以及语义事实何时实例化回工作记忆以执行特定任务？

为了说明相互作用，请考虑客户支持智能体处理退货。
每个返回请求构成一个情节记录。
在处理数百个类似请求后，智能体可能会将模式合并为语义规则：“7 天内收到损坏物品的客户有资格获得快速更换。”
当新请求到达时，该语义规则将与当前案例的具体情节细节一起加载到工作记忆中。
如果智能体还存储了用于处理退货的脚本（程序记忆），则四个记忆类型形成一个完整的推理堆栈：过程说*如何*，语义记忆说*政策是什么*，情节记忆说*发生了什么*，以及工作记忆保存实时推理上下文。

这种四层集成是我们的愿望；大多数当前系统仅很好地实现了两层，并通过粗略的启发式处理层之间的转换。
整合步骤（情节变成语义知识）尤其得不到满足：它通常需要明确的开发人员规则或定期的 LLM-driven 总结，这两者都很脆弱且难以验证。

### 3.2 表示载体

记忆的物理存储方式限制了智能体可以有效地利用它执行的操作。

上下文驻留文本——摘要、草稿本、思想链痕迹[Wei et al., 2022]——是最简单的基质。
完全透明、零基础设施，但容量受到严格限制。

向量索引存储将记录编码为密集嵌入并支持近似最近邻搜索[Karpukhin et al., 2020, Johnson et al., 2021]。
它们可以优雅地扩展到数百万条记录，但会失去结构化关系：您可以问“什么是最相似的？”但不是“什么导致了什么？”

结构化存储——SQL 数据库[Hu et al., 2023]、键值映射、知识图[Ji et al., 2022]——保留关系结构并支持复杂查询（“过去 7 天内涉及服务 X 的所有 API 故障”），但代价是前期架构设计。

可执行存储库——代码库、工具定义、计划模板[Wang et al., 2023a]——让智能体直接调用存储的技能，避开重新生成及其引入的错误。

混合商店是生产中的常态。
例如，MemGPT [Packer et al., 2024] 在可搜索召回数据库和向量索引存档上分层了一个上下文窗口“主记忆”——每一层都有不同的访问模式和逐出规则。

### 3.3 控制策略

也许最重要且讨论最少的维度是“谁决定”存储什么、检索什么以及丢弃什么。

启发式控制硬编码规则：top-$k$ 检索，总结每个$n$轮次，过期记录早于$d$天。
可预测、易于调试，但对上下文视而不见。

提示自我控制将记忆操作公开为工具调用，并让 LLM 决定何时调用它们。
MemGPT 的核心 \_记忆\_append 和存档 \_记忆\_search 是典型示例 [Packer et al., 2024]。
这里的质量取决于 LLM 的指令跟踪能力以及记忆 API 在系统提示中的记录情况。

学习控制将记忆操作视为端到端优化的策略操作。
智能体式记忆 [Yu et al., 2026] 通过具有逐步 GRPO 的三阶段 RL 管道将存储、检索、更新、总结和丢弃作为可调用工具进行训练。
回报是巨大的——学习策略发现非显而易见的策略，例如在上下文完整之前进行先发制人的总结——但培训成本也是如此。

### 3.4 代表性系统概览

表 1 按时间线绘制了关键系统和基准。

表 1：记忆的代表性系统和 LLM 智能体的基准（2020-2026 年）。

| 系统 | 年份 | 记忆类别 | 区别特征 |
| --- | --- | --- | --- |
| RAG [ Lewis et al., 2020 ] | 2020 | 非参数检索 | 首先将 seq2seq 生成器与密集文档检索器结合起来在NeurIPS 2020。|
| RETRO [ Borgeaud et al., 2022 ] | 2022 | 检索规模 | 从 2 万亿token检索的块语料库； 7.5B-parameter 模型在 10/16 基准测试中与 175B Jurassic-1 竞争。 |
| ReAct [ Yao et al., 2022 ] | 2022 | 轨迹轨迹 | 推理与行动轨迹兼作短视界工作记忆； ALFWorld 的绝对增益为 34%。 |
| 反思 [ Shinn et al., 2023 ] | 2023 | 反思性片段 | 口头自我批评，存储为情节记忆； HumanEval 上的通过率为 91%@1（对比 GPT-4 基线为 80%）。 |
| 生成智能体 [ Park et al., 2023 ] | 2023 | 情景+反思 | 25 个模拟角色通过观察-反思-规划周期自主组织情人节派对。 |
| Voyager [ Wang et al., 2023a ] | 2023 | 程序技能库 | 3.3 $\times$ 更多独特项目和 15.3 $\times$ 比之前的 Minecraft 智能体更快的技术树进展。 |
| LongMem [ Wang et al., 2023b ] | 2023 | 长格式外部 | 冻结骨干网 + 剩余侧网络； 记忆银行规模扩大至 65k token。 |
| ChatDB [ Hu et al., 2023 ] | 2023 | 结构化符号 | SQL 数据库为智能体记忆；支持INSERT/SELECT交互记录精准查询。 |
| ExpeL [Zhao et al., 2024] | 2024 | 体验式学习 | 从轨迹比较中系统地提取成功/失败的“经验法则”。 |
| MemGPT [ Packer et al., 2024 ] | 2024 | 跨主上下文的分层虚拟 | OS-inspired 分页，回想一下DB，以及档案向量存储。 |
| MemoryBank [Zhong et al., 2024] | 2024 | 长期遗忘 | 艾宾浩斯曲线衰减应用于聊天机器人记忆；发表于 AAAI 2024。|
| LoCoMo [ Maharana et al., 2024 ] | 2024 | 基准 | 最多 35 个会话，300+ 回合，每次对话 9k–16k token；人类还遥遥领先。 |
| MemBench [ Tan et al., 2025 ] | 2025 | 基准 | 区分事实与反映记忆；参与与观察模式； ACL 2025 年综述结果。 |
| MemoryAgentBench [ Hu et al., 2025 ] | 2025 | 基准 | 测试四种认知能力；当前的系统还没有掌握这四种能力。 |
| 智能体式记忆 [ Yu et al., 2026 ] | 2026 | 统一 STM/LTM 政策| 记忆操作通过逐步 GRPO 训练为 RL 操作；在五个基准测试中优于所有记忆增强型基准。 |
| MemoryArena [ He et al., 2026 ] | 2026 | 基准 | 四个域中的多会话相互依赖的任务；接近饱和的 LoCoMo 模型在此下降至 40-60%。 |

## 4. 核心记忆机制

我们现在详细研究每个机制系列，将讨论建立在具体的系统设计及其经验权衡的基础上。

### 4.1 上下文驻留记忆与压缩

给出智能体记忆最直接的方法是在提示中保留相关信息。
系统消息、最近的对话轮次、便笺——LLM 在每次通话中“看到”的所有内容都与工作记忆一样，具有完美的窗口内调用功能。

当历史超出了窗口范围时，麻烦就开始了。
已经出现了几种压缩策略：
(i) *滑动窗口*保留 $n$ 最近的转弯并放弃其余的；
(ii) *滚动摘要*，定期将较旧的历史压缩为较短的概要；
(iii) *按轮流、会话和主题粒度进行操作的分层摘要；
(iv) *任务条件压缩*，其中当前查询决定历史记录的哪些部分保留完整细节。
Self-Controlled 记忆系统 [Liang et al., 2023] 将这一决定交给智能体本身，让它选择哪些片段值得逐字保留而不是积极压缩。

上下文驻留记忆是透明的且无需基础设施，但它具有众所周知的病态：*摘要漂移*。
每次压缩都会默默地丢弃低频细节。
经过足够多的传递后，智能体“记住”一个经过净化的、通用的历史版本——正是那种在边缘情况下失败的记忆。
将上下文窗口扩展到 100k+ token [Chen et al., 2023] 会延迟问题，但无法消除它，并且较长的上下文会导致注意力成本呈二次方增加。

为了具体说明这一点：考虑一个每天处理 50 次用户交互的智能体。
经过一周的滚动总结，原始的 350 回合历史记录已被压缩了至少三个总结周期。
从第一天开始的一条罕见但关键的指令（例如，“永远不要直接调用生产数据库”）可能会在第一次压缩中幸存下来，但正是那种低频、高重要性的细节，往往会在第三次压缩时消失。
然后，智能体继续调用生产数据库，结果可预测。

这不是假设的故障模式；而是假设的故障模式。它反映了部署的长期运行的聊天机器人和编码助手中报告的问题。
含义很明确：对于任何预计运行多个会话的智能体，应使用以完全保真度保存原始记录的外部存储来补充（不是替换，而是补充）上下文驻留的记忆。

上下文驻留记忆的一个不太明显但同样重要的限制是*注意力稀释*。
即使在足够大的窗口内，LLM 的注意力机制也必须在所有token之间分配容量。
随着注入更多的记忆内容，模型专注于任何单个片段的能力会下降——“迷失在中间”文献中根据经验记录了这种现象，其中位于长上下文中心的信息比开头或结尾的信息更不可靠。
这表明简单地增大窗口并不是一个完整的解决方案。 智能体还必须“管理”进入窗口的内容，这让我们回到了对检索和过滤机制的基本需求。

### 4.2 检索增强记忆存储

RAG [Lewis et al., 2020] 证明，将生成器与非参数检索索引配对可以在知识密集型任务上产生强大的结果。
在智能体设置中，商店中填充的不是百科全书文章，而是“活生生的交互记录”：工具调用日志、环境观察、用户更正、部分计划和口头反思。

索引粒度。
细粒度索引（单个工具调用或单个句子）可以提供精确的召回，但可以将多步骤推理分割成无意义的碎片。
粗粒度索引（完整会话或长段落）保留了上下文，但将信号淹没在噪音中。
实用的最佳点是多粒度索引，检索器自适应地选择正确的数据来源。
通过学习编码器实现的密集通道检索 [Karpukhin 等人，2020]，通常由 FAISS-style 近似最近邻搜索支持[Johnson 等人，2021]，仍然是默认实现，通常通过稀疏 BM25 和元数据过滤器（时间戳、工具类型、任务标签）进行增强。

查询表述。
许多系统都忽略了一个微妙之处：智能体的立即输入 $x\_{t}$ 通常是一个糟糕的检索查询。
用户询问“为什么会崩溃？”需要智能体检索两个会话前的崩溃日志，而不是语义上最相似的句子。
策略包括 LLM-reformulated 查询、具有结果融合的多查询扇出以及使用当前子目标作为附加检索信号。
Self-RAG [Asai 等人，2024] 更进一步，教导模型决定“是否”检索是有保证的——一个简单的门，可以大大减少不必要的延迟。

规模。
RETRO [ Borgeaud et al., 2022 ] 和对万亿token数据存储的后续工作 [ Raad et al., 2024 ] 表明检索记忆可以扩展到多年的交互历史，而无需架构更改。
瓶颈决定性地从存储转移到“相关性”：确保返回最“有用”（而不仅仅是最“相似”）的记录。

读写记忆。
RET-LLM [Sun et al., 2024] 通过让智能体在存储时写入结构化三元组，同时通过自然语言查询它们，将自由格式检索和结构化存储联系起来。
这是一个务实的妥协：写入时的模式，读取时的灵活性。

### 4.3 反思式与自我改进记忆

Reflexion [Shinn et al., 2023] 引入了一个看似简单的想法：任务失败后，让智能体编写自然语言事后分析，然后将其添加到下一次尝试的提示中。
没有梯度更新，没有奖励模型——只是一个自我批评的文本文件。
结果令人震惊：HumanEval 的通过率@1 为 91%，而没有反射的 GPT-4 的通过率为 80%。

生成式智能体 [Park et al., 2023] 构建了更丰富的管道。
原始观察结果以情景流的形式积累。
智能体会定期对相关观察结果进行聚类，并综合高阶*反射*，例如，“Klaus 一直独自吃饭，似乎很孤僻。”
检索通过新近度（指数衰减）、相关性（嵌入相似性）和重要性（自我评估的整数）的加权组合对记忆进行评分。
这种多信号评分比纯余弦相似性有了很大的改进，并且在以后的设计中仍然具有影响力。

ExpeL [Zhao et al., 2024] 通过系统地对比成功和失败的轨迹、提取有区别的“经验法则”并将其存储为可重用的启发式方法，进一步推动了这一范式。
Think-in-记忆 [Liu et al., 2024a] 将检索与推理分开：智能体首先召回，然后在生成响应之前对召回的内容执行专门的思考步骤。

反思性记忆的核心风险是“自我强化错误”。
如果智能体错误地得出“API X 总是返回参数 Y 的错误”的结论，它将永远避免该调用路径，永远不会收集证据来推翻错误的信念。
过度概括是同级风险：在一种情况下吸取的教训盲目地应用于另一种情况。
质量门——置信度分数、与其他记忆的矛盾检查、定期过期——是必要的，但仍然不发达。

随着规模的扩大，问题变得更加严重。
短暂的智能体中的一次错误反射造成的损害有限；同样的错误反映持续存在于长期运行的生产智能体中，可能会在数周内影响数千个下游决策，这可能是灾难性的。
反射型记忆故障模式的严重性与智能体的使用寿命成正比，这使得它在最需要记忆的设置中特别危险。

最近的工作中探索的一种缓解策略是“反射指令落地”：要求智能体为其生成的每个反射引用特定的情景证据。
如果“API X 不可靠”的反映必须指向三个具体的故障实例，则智能体不太可能生成毫无根据的概括。
这并不能完全解决问题——引用的证据本身可能不具有代表性——但它提供了可供人类操作员审查的可审计线索。

### 4.4 分层记忆与虚拟上下文管理

MemGPT [Packer et al., 2024] 借用了操作系统设计者几十年前完善的一个想法：虚拟记忆。
OS 通过在 RAM 和磁盘之间透明地分页数据，为每个进程提供了巨大、连续的记忆的错觉。
MemGPT 对 LLM 的上下文窗口执行相同的操作：

- 主上下文（RAM）：活动窗口持有系统提示、最近消息和当前相关记录。
- 召回存储（磁盘）：所有过去消息的可搜索数据库。
- 档案存储（冷存储）：文档和长期知识的向量索引存储。

智能体通过调用记忆管理“函数”（archive\_记忆\_search、core\_记忆\_append 等）在层之间移动数据。
中断机制将每个用户消息或定时器事件的控制权传递给智能体，使其在响应之前执行多个内部记忆操作。

JARVIS-1 [Wang et al., 2024b] 将分层原则扩展到多模式设置，为视觉观察、文本计划和可执行技能提供单独的存储。
语言认知架构智能体 [ Sumers et al., 2024 ] 提出了一个通用的蓝图，其中工作存储、情景存储、语义存储和程序存储通过中央执行程序（LLM）进行交互，直接呼应了 Baddeley 的模型 [Baddeley, 2000]。

分层记忆的致命弱点是*编排*。
分页错误的内容会浪费宝贵的上下文标记；存档过于激进，您会造成“记忆失明”——智能体根本不知道关键事实存在于冷存储中的某个位置。
这种张力激发了下一个机制系列。

值得注意的是，分层记忆中的编排失败往往是“无声的”。
与产生错误消息的崩溃的 API 调用不同，逐出错误记录的分页决策只会导致稍差的响应 - 没有例外，没有日志条目，没有明显的信号表明出现了问题。
随着时间的推移，这些无声的失败会变得更加复杂。
诊断它们需要详细的记忆操作日志和回顾性分析——这是当前很少有系统进行的工程投资，但这对于生产级部署至关重要。

### 4.5 策略学习式记忆管理

启发式和提示自我控制并未针对智能体的最终任务进行优化。
$k$-nearest-neighbor 检索器不知道检索到的记录是否真正有帮助；固定的摘要时间表并不关心被压缩的材料是否重要。

智能体式记忆 (AgeMem) [Yu et al., 2026] 通过将五个记忆操作（存储、检索、更新、总结、丢弃）视为智能体策略中的可调用工具，然后通过强化学习优化整个管道来解决此问题。
培训分三个阶段进行：记忆演示的监督预热、带有结果奖励的任务级 RL，以及最后为单个记忆操作提供更密集的信用分配的步骤级 GRPO。
在五个长时程基准测试中，AgeMem 始终优于强基线，并且学习的策略呈现出非显而易见的策略：在上下文填充之前主动总结中间结果，并有选择地丢弃语义上与现有记录相似但不添加新信息的记录。

公开的担忧依然存在。
RL 长期培训的成本很高。
习得性遗忘可能会删除对安全至关重要的信息。
针对一项任务分配训练的策略可能无法转移。
而且很难解释“为什么”智能体选择特定的记忆操作——可解释性落后于能力。

### 4.6 参数记忆与基于权重的适应

上述所有内容都将记忆视为模型权重的外部。
另一种系列通过微调或适配器模块将记忆“内部”嵌入到参数中。
MemLLM [ Modarressi et al., 2024 ] 微调 LLM 以与显式读写记忆模块交互，紧密耦合参数和非参数知识。
检索和生成的联合训练 [Zhong et al., 2022] 比冷冻猎犬基线产生更好的记忆利用率。

参数化记忆提供无缝集成——模型只是“了解”事物。
但它很难审计（用户的生日到底存储在权重中的哪里？），很难删除（机器取消学习仍然不成熟），并且更新成本昂贵（每个新事实都需要微调）。
由于这些原因，大多数部署的智能体都倾向于非参数、可检查的存储。

## 5. 评估：从召回到智能体效用

### 5.1 为什么经典检索指标不够

Precision@$k$ 和 nDCG 告诉您是否检索到了正确的文档。
他们没有透露智能体是否正确使用了该文档，或者检索它是否值得延迟。
智能体记忆评估必须联合评估*记忆质量*和*决策质量*，以及经典 IR 完全忽略的问题：陈旧、矛盾、遗忘质量和治理合规性。

### 5.2 新一代基准版图

最近的四个基准将评估推向互补的方向。

LoCoMo [Maharana et al., 2024] 测试非常长期的会话记忆：最多 35 个会话，300 多个回合，每个会话 9k-16k token。
三个评估任务——事实QA、事件总结和对话生成——探讨不同的记忆需求。
总体结果是：即使是 RAG-augmented LLM 也远远落后于人类，尤其是在时间和因果动态方面。

MemBench [ Tan et al., 2025 ] 将“事实”与“反思”记忆区分开来，并在“参与”和“观察”模式下分别进行测试。
指标涵盖三个维度：有效性（准确性）、效率（记忆操作的数量）和容量（随着记忆存储的增长，性能下降）。

MemoryAgentBench [Hu et al., 2025] 以认知科学评估为基础，探讨四种能力：准确的检索、测试时学习、长期理解和选择性遗忘。
长上下文数据集被重新格式化为增量多轮交互，以模拟实际积累。
当前的系统还没有掌握所有四种能力；大多数人在选择性遗忘方面明显失败。

MemoryArena [He et al., 2026] 将记忆评估嵌入到完整的智能体式任务中——网络导航、偏好约束规划、渐进信息搜索和顺序形式推理——其中后续子任务取决于智能体从早期子任务中学到的内容。
最引人注目的发现：在 LoCoMo 上得分近乎完美的模型在 MemoryArena 上下降到 40-60%，暴露了被动召回和主动、决策相关的记忆使用之间的巨大差距。

### 5.3 基准比较

表 2 总结了这四个基准的设计差异。

表 2：近期智能体记忆基准测试的功能比较。

| 基准 | 年份 | 多会话 | 多轮 | 智能体式任务 | 遗忘| 多模态 |
| --- | --- | --- | --- | --- | --- | --- |
| LoCoMo | 2024 | ✓ | ✓ | – | – | ✓ |
| MemBench | 2025 | – | ✓ | – | – | – |
| MemoryAgentBench | 2025 | – | ✓ | – | ✓ | – |
| MemoryArena | 2026 | ✓ | ✓ | ✓ | – | – |

### 5.4 一套实用的指标栈

部署需要比任何单一基准提供的更多细微差别。
我们提出一个四层评估堆栈：

第 1 层——任务有效性：
成功率、事实正确性、计划完成率。

第 2 层 —记忆质量：
检索记录的精确度/召回率、矛盾率、陈旧性分布、任务相关事实的覆盖范围。

第 3 层——效率：
每个记忆操作的延迟、记忆内容消耗的提示token、每步检索调用、存储随时间的增长。

第 4 层——治理：
隐私泄露率、删除合规性、访问范围违规。

消融研究应该隔离写入策略、检索策略和压缩模块，将增益归因于特定组件而不是整个管道。

### 5.5 跨基准的共同启示

汇总这四项评估的结果，可以发现一些突出的模式。

长上下文不是记忆。
尽管上下文窗口扩展到 200k token[Chen et al., 2023]，但在需要选择性检索和主动管理的任务上，长上下文模型始终表现不佳专门构建的记忆系统。
MemoryArena 的表现最为明显：被动召回王牌很差记忆智能体。

RAG 有帮助，但与人类的差距很大。
RAG-based 智能体全面击败了纯长上下文基线，但主要瓶颈不再是存储，而是*检索质量*。
智能体通常会显示看似合理但陈旧或偏离主题的记录 [Maharana 等人，2024 年]。

没有人能够很好地评价遗忘。
只有 MemoryAgentBench 显式测试选择性遗忘。
然而，在任何长期运行的部署中，无法丢弃过时的信息会逐渐损害检索的精度。

跨会话一致性尚未得到充分探索。
大多数基准测试都会衡量会话内的性能。
MemoryArena 的多会话设计表明，在间隔几小时或几天的会话中保持一致的知识和行为是一个独特的挑战，而且基本上尚未解决。

参数与非参数之间的差距是真实存在的。
具有参数记忆（微调权重）和非参数记忆（外部存储）的系统显示不同的故障概况。
参数化记忆擅长无缝知识集成，但在定向删除和审计方面失败。
非参数记忆支持检查和治理，但可能会让人感觉“被束缚”——智能体有时会忽略检索到的记录或不一致地使用它们。
这两种方法之间的最佳平衡以及如何有效地将它们结合起来仍然是一个悬而未决的实证问题。

评估必须包括成本。
记忆系统的准确度提高了 5%，但延迟和存储成本却增加了三倍，但在实践中可能并不能算是一种改进。
目前的基准都没有系统地报告效率指标和有效性，因此很难评估报告的收益是“免费”还是以巨大的运营费用获得。
未来的评估应该要求至少报告token消耗和延迟开销以及准确度数字。

## 6. 记忆在哪些场景决定智能体成败

记忆并非一律重要。
一次性翻译工具几乎不需要它；一个为期一个月的项目合作者如果没有它就无法运作。
下面我们检查记忆是差异化因素的领域。

### 6.1 个人助理与对话智能体

私人助理忘记你的饮食限制或每次会话都重新询问你的时区，这充其量只是烦人的。
MemoryBank [Zhong et al., 2024] 通过艾宾浩斯遗忘曲线建模记忆衰减[Ebbinghaus, 1885]：经常访问的、高度重要的记忆会得到强化，而被忽视的记忆会逐渐消失。
MemGPT [Packer et al., 2024] 演示了具有不断发展的用户模型的多会话聊天。
该领域的核心张力是“个性化但不超越”——智能体必须记住足够多的信息才能真正提供帮助，而不会泄露用户认为私密或忘记的信息。

### 6.2 软件工程智能体

编码智能体有助于跨可能包含数百万行代码库的生成、调试、审查和项目管理[Qian 等人，2024 年，Hong 等人，2024 年]。
记忆的要求非常严格：保留架构决策、跟踪错误报告历史、记住代码风格首选项以及维护经过验证的解决方案库。
ChatDev [Qian et al., 2024] 为角色扮演智能体（CEO、CTO、程序员、测试人员）配备共享记忆，以保持项目在各个开发阶段的一致性。
MetaGPT [Hong et al., 2024] 将这个共享的记忆构建为标准化文档——PRDs、设计规范、代码模块——持续存在并不断发展。

这里的独特挑战是“结构规模”：记忆系统必须索引和检索可能跨越数千个文件而不仅仅是对话的代码库的相关部分。

### 6.3 开放世界游戏智能体

Minecraft 和类似的沙盒之所以成为流行的测试平台，正是因为它们需要长时程规划和组合技能的重用。
Voyager [Wang 等人，2023a] 表明，不断增长的技能库可以实现终身学习：3.3$\times$ 比之前的智能体拥有更多独特的项目，15.3$\times$ 的里程碑进度更快。
JARVIS-1 [Wang et al., 2024b] 通过跨视觉观察和文本计划的多模态记忆扩展了这一点。
《Minecraft 中的幽灵》[ Zhu et al., 2023 ] 使用基于文本的知识和记忆来实现通用的开放世界智能体。

关键的挑战是*组合技能的重用*：智能体不仅必须召回个人技能，还必须创造性地将它们链接起来以解决新问题。

### 6.4 科学推理与发现

科学智能体必须跟踪假设、记录实验结果、消化文献并随着证据的积累修正信念。
记忆在这里充当假设分类账和证据累积器。
独特的挑战是*不确定性感知记忆*：智能体不仅必须维护事实，还必须维护置信水平，并在新数据到达时正确更新它们——大多数当前的记忆系统处理得很差或根本不处理。

### 6.5 多智能体协作

当多个智能体一起工作时，记忆成为一个协调机制。
AutoGen [ Wu et al., 2023 ] 让智能体通过共享上下文构建彼此的贡献。
CAMEL [Li et al., 2024] 探索了必须记住先前协议和协作历史的角色感知交流智能体。
Pro智能体 [Zhang et al., 2024a] 建立积极主动的团队成员，根据过去互动的记忆预测需求。

两个挑战占主导地位：*共享与私有记忆边界*——什么应该对谁可见？——以及*并发写入下的一致性*——当两个智能体同时更新共享记忆时会发生什么？
当前的多智能体框架以两种方式之一处理共享的记忆：要么共享所有记忆（简单但泄漏私人信息），要么每个智能体维护自己的存储，没有 cross-智能体访问（隔离但阻止知识传输）。
这两个极端都不能令人满意。
有原则的中间立场将在共享的记忆基底上定义基于角色的访问控制，允许项目经理智能体看到来自开发人员智能体的高级摘要，而无需访问原始代码差异。
适用于自然语言记录的数据库式访问控制列表是一种自然但未经探索的解决方案。

### 6.6 工具使用与 API 编排

使用工具智能体 [Schick et al., 2024] 与 APIs、数据库和 Web 服务交互。
记忆必须跟踪存在哪些工具、如何调用它们、上次工作的参数以及哪些调用序列已被验证。
智能体Bench [Liu et al., 2023] 在八个环境中评估智能体；失去命令历史记录的智能体在多步骤任务中表现出急剧的性能下降。
DERA [Nair et al., 2023] 使用对话转向记忆迭代地细化工具使用策略。

此设置特有的实际危险是*架构漂移*：当 API 更新其界面时，存储的使用模式将变得无效。
对存储的工具使用记录的版本跟踪和模式验证至关重要，但很少实施。
在快速发展的 API 生态系统中，不处理架构漂移的工具使用记忆系统将积累越来越多的无效记录，从而逐渐降低智能体重用过去经验的能力。

这里更广泛的一点是，工具使用记忆不仅仅是存储“有效的内容”；它是关于维护一个动态的、版本化的工具功能目录，该目录会随着外部世界的变化而优雅地降级。
这与依赖管理的软件工程概念相关：就像构建系统必须跟踪库版本一样，使用智能体的工具必须跟踪其记忆存储中的 API 版本。

### 6.7 跨领域记忆迁移

一个新兴方向是跨域传输记忆，例如，将在 Python 中学到的调试启发式方法重用于 Java，或者将一个用户的时间管理策略应用于另一个用户。
思想之树 [Yao et al., 2024] 提供了一个有意识地解决问题的框架，可以从跨域程序记忆中受益。
悬而未决的问题是如何识别哪些记忆是概括性的，哪些是无可救药的特定情境记忆。

### 6.8 小结：不同记忆类型最重要的场景

应用综述揭示了一个清晰的模式：不同的领域强调不同的记忆类型。
个人助理最依赖语义记忆（用户偏好和配置文件）。
软件工程智能体严重依赖于程序记忆（经过验证的代码模式和架构决策）。
游戏智能体需要情节和程序记忆的紧密结合（$+$发生了什么该怎么办）。
科学智能体要求语义记忆具有明确的不确定性跟踪。
多智能体系统添加了一个协调层，目前 single-智能体记忆设计无法很好地处理该层。

现有系统还没有同时对所有这些配置文件提供强大的支持，这表明智能体记忆的下一个飞跃可能来自更加模块化、可插拔的架构，其中记忆组件可以根据部署进行组合和配置，而不是融入整体设计。

## 7. 工程现实

### 7.1 写入路径

逐字存储每个交互是很诱人的，而且几乎总是错误的。
噪音（闲聊、多余的确认、重复的问候）会降低检索的精度。
精心设计的写入路径包括：
*过滤*以拒绝低信号记录，
*规范化*标准化日期、名称和数量，
*重复数据删除*合并重叠条目，
*优先评分*按任务相关性和新颖性对记录进行排名，
和*元数据标记*（时间戳、来源、任务标签、置信度）以支持下游结构化查询。

最佳过滤阈值是特定于应用的。
医疗智能体不能承受假阴性（缺少药物过敏提及）；一个休闲的聊天助手可以容忍它们。
在这两个极端之间存在着一个范围：企业客户支持机器人通常优先考虑对合同承诺的高召回率，但接受对随意偏好的较低召回率，而财务咨询智能体要求对监管披露进行近乎完美的召回，但可以忘记非正式的闲聊。
写入路径设计应通过风险分析来告知，该风险分析将记忆故障模式映射到目标域中的下游后果。

### 7.2 读取路径

并非每个步骤都需要检索，也不是每个检索都需要完整的管道。
实际的读取路径优化包括：
两阶段检索（快速 BM25 或元数据过滤器 $\rightarrow$ 较慢的交叉编码器重新排序），
检索-or-not 门控 [Asai 等人，2024]，
token预算，动态分配记忆和当前任务之间的上下文空间，
以及用于高频记录（例如用户偏好）的缓存层。

### 7.3 陈旧、矛盾与漂移

如果私人助理按照旧地址向用户的前伴侣发送生日贺卡，不仅没有帮助，而且有害。
长期存在的记忆存储会积累陈旧的记录，并且如果没有明确的机制，智能体无法区分 2024 年地址和 2022 年地址。

稳健的系统需要*临时版本控制*（首选最新记录）、*源归因*（用户语句 $>$ 智能体推理）、*矛盾检测*（标记冲突以解决问题）和*定期合并*（合并重复项并淘汰陈旧条目的计划扫描）。

### 7.4 延迟与成本

用户期望简单查询的亚秒级响应。
检索管道可以轻松增加 200–500ms。
常见的缓解措施：异步写入（延迟存储直到响应之后）、渐进式检索（在检索并行运行时开始生成）和动态路由（对于直接请求跳过检索，仅在模糊性较高时才使用完整管道）。

徐等人。 [Xu et al., 2024]表明，在中等长度的上下文中检索一些高度相关的段落通常会击败纯长上下文和纯检索方法——这是调整延迟与质量之间权衡的有用指南。

### 7.5 隐私、合规与删除

智能体记忆可以隐藏敏感数据：健康详细信息、财务记录、私人对话。
部署必须提供静态和传输中的加密、每用户访问范围、自动 PII 编辑、可配置的保留策略以及从每个层删除数据的可审核删除（包括向量索引条目和备份快照）。

当记忆泄漏到微调权重中时，外部删除是不够的。
机器取消学习 [ Bourtoule et al., 2021 , Liu et al., 2024b ] 是唯一的途径，而且距离生产就绪还很远。
智能体记忆治理与机器遗忘的交叉点是一个紧迫的开放问题。

### 7.6 三种架构模式

在实践中，智能体记忆系统分为三种重复模式：

模式 A：整体上下文。
所有记忆都位于提示符内。
零基础设施、完全透明，但容量有限且容易出现汇总漂移。
适用于短期智能体或快速原型制作。

模式 B：上下文 + 检索存储。
工作记忆中的上下文窗口；外部向量或结构化存储中的长期记录。
检索管道每一步都会注入相关记录。
这是当今大多数智能体生产背后的主力模式：编码助理、客户服务机器人、企业副驾驶。
工程负担是可控的；主要挑战是检索质量。

模式 C：具有学习控制的分层记忆。
多层——上下文、结构化DB、向量存储、冷存档——由学习或提示的控制器管理。
MemGPT [Packer 等人，2024] 和 AgeMem [Yu 等人，2026] 就是范例。
这种模式提供了最大的空间，但需要最复杂的工程和培训。

我们的建议：从模式 B 开始，彻底检测它，只有当经验数据表明学习控制能有效改善您的目标工作量时，才转向模式 C。

### 7.7 可观测性与调试

记忆系统是出了名的难以调试。
当智能体给出错误答案时，问题出在检索（出现错误记录）、写入路径（从未存储相关信息）、压缩（摘要过程中丢失细节），还是LLM对正确检索内容的推理中？

生产部署受益于全面的记忆操作日志记录：每次写入、读取、更新和删除都应记录时间戳、触发上下文以及涉及的记录。
重放工具允许开发人员使用修改后的记忆内容重新运行失败的交互，这对于根本原因分析非常有价值。
一些团队发现，一个简单的“记忆 diff”（显示两个对话轮之间记忆存储中发生的变化）比传统日志分析提供了更多的诊断价值。

研究论文中很少讨论这种可观测性基础设施，但它的缺失是令人印象深刻的演示阶段记忆系统无法过渡到可靠的生产部署的主要原因之一。

除了调试之外，记忆可观察性还支持*持续改进*。
通过分析记忆操作中的模式（最常检索哪些类型的记录、哪些类型的记录被写入但从不读取、哪些检索查询始终返回空结果），团队可以识别瓶颈并随着时间的推移校准其记忆系统。
这种反馈循环在数据库工程（查询性能监控、索引优化）中是标准的，但在智能体记忆实践中几乎完全不存在。
借用这些技术，即使是简化形式，也将显着提高已部署的记忆增强型智能体的可靠性。

一个相关的问题是*记忆行为的回归测试*。
当记忆系统更新时（例如，为向量存储部署新的嵌入模型），对检索质量的影响是不可预测的，而且可能是微妙的。
如果没有一套回归测试来验证代表性场景下的预期记忆行为，则对记忆子系统的更改将成为未跟踪风险的来源。
构建这样的测试套件需要“应该为哪些查询检索哪些记忆”的真实注释，这是一项可以在系统稳定性方面带来回报的投资。

## 8. 与既有综述的定位比较

习等人。 [ Xi 等人，2023 ] 和 Wang 等人。 [ Wang et al., 2024a] 提供了广泛的智能体综述，其中记忆是众多模块之一。
张等人。 [Zhang et al., 2024b] 特别关注记忆并围绕写-管理-读操作组织他们的审查；我们的工作更新了 2025-2026 年系统（AgeMem、MemBench、MemoryAgentBench、MemoryArena）的覆盖范围，添加了以 POMDP 为基础的公式，并将讨论扩展到应用、工程模式和治理。

高等人。 [Gao等，2024]对RAG进行了全面综述，但其范围是检索——代管道，而不是智能体-specific、记忆的需求。
苏默斯等人。 [ Sumers et al., 2024 ] 提出了语言智能体的认知架构蓝图；我们的分类法是互补的，共享认知科学术语，但将分析扩展到代表性基质和控制政策。

经常提出的一个问题是，扩展上下文窗口（从早期 GPT 模型中的 4k 到今天的 200k+ [Chen et al., 2023]）是否会使外部记忆过时。
证据表明不。
较长的上下文会扩大工作记忆，但不提供持久的跨会话存储、结构化知识组织、来自几个月历史的选择性检索或删除和访问控制等治理机制。
此外，推理成本与上下文长度呈二次方关系，Xu 等人。 [Xu et al., 2024] 凭经验表明，通过有针对性的检索增强的适度上下文在许多任务上优于暴力长上下文。

## 9. 开放挑战

### 9.1 有原则的整合

当前的系统在囤积（储存所有东西，淹没在噪音中）和失忆（积极压缩，丢失罕见但重要的事实）之间摇摆。
神经科学提供了一个有启发性的模型：在睡眠期间，海马体会重播最近的经历，加强重要的痕迹并修剪其余的[Squire，2004]。
类似的“离线整合”流程（在空闲期间安排）可以提供原则上的平衡。
开放问题：如何在没有前瞻性的情况下估计记忆的重要性，如何检测何时需要整合，以及如何保证安全关键记录在整个过程中幸存下来。

一种值得探索的具体方法是“双缓冲区整合”，即新形成的记忆在试用期内驻留在“热”缓冲区中，只有在通过质量检查（重新验证、重复数据删除和重要性评分）后才会晋升为长期存储。
这反映了在生物记忆 [Squire, 2004] 中观察到的海马到新皮质的转移，其中新记忆最初是海马依赖性的，并通过反复重新激活逐渐变得独立。
在智能体系统中实现此功能需要定义试用期、升级标准以及升级发生前热缓冲区溢出时的回退行为。

### 9.2 具有因果依据的检索

语义相似性回答“这看起来像什么？”但不是“是什么造成了这个？”
当智能体调试系统故障时，相关的记忆可能在时间上远离当前错误消息并且在语义上与当前错误消息不同，但因果关系在上游。
混合语义相似性、时间排序、因果图遍历和反事实相关性的混合检索器在很大程度上仍未被探索。
构建它们需要将因果发现技术与记忆索引相结合——技术上具有挑战性，但对于复杂的推理任务来说可能具有变革性。

具体的起点是使用轻量级因果元数据层来增强标准向量索引。
当存储记忆记录时，智能体可以使用估计的*因果父项（促成该记录的早期记录或事件）对其进行注释。
在检索时间，系统将与标准相似性搜索一起遍历这些因果链接，显示语义上遥远但因果相关的记录。
这样的系统不需要执行完整的因果推理；即使是由 LLM 在写入时生成的近似因果注释，也可以显着改善检索的推理繁重任务，例如根本原因分析、反事实规划和多步调试。

### 9.3 可信反思

自我反省是一种强大的适应机制，但也可能会加深错误。
如果智能体错误地得出“接近 $A$ 总是失败”的结论，那么它永远不会再次测试接近 $A$——这是一个典型的确认偏差。
未来的系统需要外部验证（如果可用的话，根据真实情况检查反射）、不确定性量化（在没有确认证据的情况下随着时间的推移降低置信度）、对抗性探测（定期用反例挑战存储的信念）和过期策略（在设定的时间段后淘汰未经验证的反射）。

### 9.4 学会遗忘

遗忘不是错误，而是错误。它是一项对于稳健性、隐私性和效率来说至关重要的功能。
然而，当前的系统处理方式很粗糙：基于时间的硬性过期、存储限制驱逐，或者根本不处理。
研究问题是学习“选择性”遗忘策略，在安全和合规性约束下最大化长期效用。
当记忆通过上下文学习或微调影响模型行为时，与机器取消学习的联系[Bourtoule et al., 2021, Liu et al., 2024b]至关重要。

### 9.5 多模态与具身记忆

随着智能体进入机器人和混合现实领域，记忆必须融合文本、视觉、音频、本体感觉和工具状态。
JARVIS-1 [Wang et al., 2024b] 提供了 Minecraft 中的早期示例，但现实世界的具体设置添加了空间记忆、实时延迟约束以及跨模式检索的棘手问题 - 通过文本查询查找视觉记忆，或者反之亦然反之亦然。

### 9.6 多智能体记忆治理

多智能体系统提出了 single-智能体记忆从未遇到的问题：共享存储的访问控制、并发写入的共识协议以及不同专业化的智能体之间的知识传输机制。
当前的方法依赖于共享对话日志或文档存储；更复杂的设计——具有合并语义的分布式记忆、具有 per-智能体缓存的分层共享记忆——仍然处于开放状态。

### 9.7 迈向记忆高效架构

记忆增强型智能体很昂贵：大型上下文窗口、每步多个检索调用、不断增长的存储。
稀疏检索（每步激活一小部分存储）、压缩会话向量、Recurrent Memory Transformers 等记忆-native 架构 [Bulatov 等人，2022] 以及通过适配器注入的检索-free [Modarressi 等人，2024] 都指向更便宜的替代品，尽管尚未表现出强大的智能体级性能。

### 9.8 更深入地融合神经科学

目前的智能体记忆借用认知科学标签；更深入的参与可以产生更好的机制。
传播激活[Anderson，1983]——访问一个记忆素数相关激活——可以改进检索超越直接相似性。
记忆重新巩固理论——检索使记忆不稳定并易于修订——可以为更新机制提供信息。
艾宾浩斯曲线 [Ebbinghaus, 1885] 已在 MemoryBank [Zhong et al., 2024] 中使用，可以通过间隔重复进行扩展，以优化强化时间。

### 9.9 面向记忆管理的基础模型

长期愿景：*记忆控制的基础模型*，在不同的智能体任务中进行训练，以执行具有一般能力的写入、检索、总结、忘记和巩固操作 - 类似于指令调整的 LLM [Ouyang et al., 2022] 提供一般语言能力。
AgeMem [Yu et al., 2026] 通过学习记忆管理作为策略迈出了第一步，但真正与任务无关的记忆控制器的愿景仍未实现。

这样的基础模型需要处理各种分布的记忆挑战：短期会话跟踪、长期用户分析、高频工具使用日志记录、罕见但安全关键的信息保留以及存储预算耗尽时的优雅降级。
训练数据要求令人望而生畏——该模型需要接触数十个领域的数千条智能体轨迹，并带有记忆操作质量的真实标签。
综合生成此训练数据，也许通过先进的 LLM 回顾性注释历史痕迹中的哪些记忆操作是有用的或有害的，可以引导该过程。

### 9.10 标准化评估

该领域仍然缺乏社区标准的评估工具。
每个基准测试都使用自己的数据集、指标和协议，使得跨论文比较不可靠。
GLUE 式的智能体记忆共享排行榜（涵盖会话、智能体式和多会话轨道，以及来自我们四层堆栈的标准化指标）将大大加快进度并减少重复工作。

## 10. 结论

记忆已经从外围附加模块，转变为基于 LLM 的智能体最核心的工程与研究挑战之一。这个领域在很短时间内经历了三代演进：提示级压缩、检索增强外部存储，以及端到端学习的记忆策略。评估也同步从静态召回测试走向多会话智能体基准，开始真正暴露“记住一个事实”和“在行动中正确使用它”之间的差距。

本综述给出了以 POMDP 为基础的形式化、三轴分类法、机制分析、结构化基准比较、应用分析和工程实践框架。但最困难的问题仍未解决：如何在不发生灾难性信息损失的前提下整合记忆，如何按因果关系而非表面相似度检索，如何让反思不固化错误，以及如何安全地遗忘。

如果只能从这篇综述中带走一个结论，那就是：记忆值得获得与 LLM 本身同等程度的工程投入。团队往往用数月时间评测模型，却只用一个下午设计记忆架构。本文汇总的证据表明，扭转这种优先级，把记忆当作需要专门设计、测试和优化的一等系统组件，可能是今天构建智能体时杠杆最高的改进之一。

## 致谢

本手稿的目标是*高级智能系统*。
作者、资助和道德元数据应在提交前最终确定。

## 利益冲突

作者声明不存在利益冲突。

## 数据可用性声明

本研究未生成原始数据。
所有引用的作品均按引用方式公开提供。

## 参考文献（保留英文原文）

- Achiam et al. (2023)
  J. Achiam, S. Adler, S. Agarwal, L. Ahmad, I. Akkaya, F. L. Aleman, D. Almeida, J. Altenschmidt, S. Altman, S. Anadkat, et al.
  GPT-4 technical report.
  arXiv preprint arXiv:2303.08774.
  Cited by: §1.
- Anderson (1983)
  J. R. Anderson
  A spreading activation theory of memory.
  Journal of Verbal Learning and Verbal Behavior 22 (3), pp. 261–295.
  Cited by: §9.8.
- Asai et al. (2024)
  A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi
  Self-RAG: learning to retrieve, generate, and critique through self-reflection.
  arXiv preprint arXiv:2310.11511.
  Cited by: §4.2,
  §7.2.
- Atkinson and Shiffrin (1968)
  R. C. Atkinson and R. M. Shiffrin
  Human memory: a proposed system and its control processes.
  Psychology of Learning and Motivation 2, pp. 89–195.
  Cited by: §3.
- Baddeley (2000)
  A. Baddeley
  The episodic buffer: a new component of working memory?.
  Trends in Cognitive Sciences 4 (11), pp. 417–423.
  Cited by: §3.1,
  §3,
  §4.4.
- Borgeaud et al. (2022)
  S. Borgeaud, A. Mensch, J. Hoffmann, T. Cai, E. Rutherford, K. Millican, G. van den Driessche, J. Lespiau, B. Damoc, A. Clark, D. de Las Casas, et al.
  Improving language models by retrieving from trillions of tokens.
  In Proceedings of the 39th International Conference on Machine Learning (ICML),
  Cited by: §1.2,
  Table 1,
  §4.2.
- Bourtoule et al. (2021)
  L. Bourtoule, V. Chandrasekaran, C. A. Choquette-Choo, H. Brendel, M. Nasr, M. Hoover, B. Fung, D. Papadopoulos, C. Zhang, A. Travers, et al.
  Machine unlearning.
  IEEE Symposium on Security and Privacy.
  Cited by: §7.5,
  §9.4.
- Brown et al. (2020)
  T. Brown, B. Mann, N. Ryder, M. Subbiah, J. D. Kaplan, P. Dhariwal, A. Neelakantan, P. Shyam, G. Sastry, A. Askell, et al.
  Language models are few-shot learners.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §1.
- Bulatov et al. (2022)
  A. Bulatov, Y. Kuratov, and M. Burtsev
  Recurrent memory transformer.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §1.2,
  §9.7.
- Chen et al. (2023)
  S. Chen, S. Wong, L. Chen, and Y. Tian
  Extending context window of large language models via positional interpolation.
  arXiv preprint arXiv:2306.15595.
  Cited by: §4.1,
  §5.5,
  §8.
- Ebbinghaus (1885)
  H. Ebbinghaus
  Über das gedächtnis: untersuchungen zur experimentellen psychologie.
  Leipzig: Duncker & Humblot.
  Cited by: §6.1,
  §9.8.
- Gao et al. (2024)
  Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang
  Retrieval-augmented generation for large language models: a survey.
  arXiv preprint arXiv:2312.10997.
  Cited by: §8.
- Graves et al. (2014)
  A. Graves, G. Wayne, and I. Danihelka
  Neural turing machines.
  arXiv preprint arXiv:1410.5401.
  Cited by: §1.2.
- Graves et al. (2016)
  A. Graves, G. Wayne, M. Reynolds, T. Harley, I. Danihelka, A. Grabska-Barwińska, S. G. Colmenarejo, E. Grefenstette, T. Ramalho, J. Agapiou, et al.
  Hybrid computing using a neural network with dynamic external memory.
  Nature 538, pp. 471–476.
  Cited by: §1.2.
- He et al. (2026)
  Z. He, Y. Wang, C. Zhi, Y. Hu, T. Chen, L. Yin, Z. Chen, T. A. Wu, S. Ouyang, Z. Wang, J. Pei, J. McAuley, Y. Choi, and A. Pentland
  MemoryArena: benchmarking agent memory in interdependent multi-session agentic tasks.
  arXiv preprint arXiv:2602.16313.
  Cited by: §1.3,
  §2.4,
  Table 1,
  §5.2.
- Hong et al. (2024)
  S. Hong, M. Zhuge, J. Chen, X. Zheng, Y. Cheng, C. Zhang, J. Wang, Z. Wang, S. K. S. Yau, Z. Lin, et al.
  MetaGPT: meta programming for a multi-agent collaborative framework.
  arXiv preprint arXiv:2308.00352.
  Cited by: §6.2.
- Hu et al. (2023)
  C. Hu, J. Fu, C. Du, S. Luo, J. Zhao, and H. Zhao
  ChatDB: augmenting LLM with databases as their symbolic memory.
  arXiv preprint arXiv:2306.03901.
  Cited by: §1.2,
  §3.2,
  Table 1.
- Hu et al. (2025)
  Y. Hu, Y. Wang, and J. McAuley
  Evaluating memory in LLM agents via incremental multi-turn interactions.
  arXiv preprint arXiv:2507.05257.
  Cited by: §1.3,
  Table 1,
  §5.2.
- Ji et al. (2022)
  S. Ji, S. Pan, E. Cambria, P. Marttinen, and P. S. Yu
  A survey on knowledge graphs: representation, acquisition, and applications.
  IEEE Transactions on Neural Networks and Learning Systems 33 (2), pp. 494–514.
  Cited by: §3.2.
- Johnson et al. (2021)
  J. Johnson, M. Douze, and H. Jégou
  Billion-scale similarity search with GPUs.
  IEEE Transactions on Big Data 7 (3), pp. 535–547.
  Cited by: §3.2,
  §4.2.
- Karpukhin et al. (2020)
  V. Karpukhin, B. Oğuz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W. Yih
  Dense passage retrieval for open-domain question answering.
  arXiv preprint arXiv:2004.04906.
  Cited by: §3.2,
  §4.2.
- Lewis et al. (2020)
  P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela
  Retrieval-augmented generation for knowledge-intensive NLP tasks.
  In Advances in Neural Information Processing Systems (NeurIPS),
  Cited by: §1.2,
  Table 1,
  §4.2.
- Li et al. (2024)
  G. Li, H. A. A. K. Hammoud, H. Itani, D. Khizbullin, and B. Ghanem
  CAMEL: communicative agents for “mind” exploration of large language model society.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §6.5.
- Liang et al. (2023)
  X. Liang, B. Wang, H. Huang, S. Wu, P. Wu, L. Lu, Z. Ma, and Z. Li
  Unleashing infinite-length input capacity for large-scale language models with self-controlled memory system.
  arXiv preprint arXiv:2304.13343.
  Cited by: §4.1.
- Liu et al. (2024a)
  L. Liu, X. Yang, Y. Shen, B. Hu, Z. Zhang, J. Gu, and J. Zhou
  Think-in-memory: recalling and post-thinking enable LLM with long-term memory.
  arXiv preprint arXiv:2311.08719.
  Cited by: §4.3.
- Liu et al. (2023)
  X. Liu, H. Yu, H. Zhang, Y. Xu, X. Lei, H. Lai, Y. Gu, H. Ding, K. Men, K. Yang, et al.
  AgentBench: evaluating LLM as agents.
  arXiv preprint arXiv:2308.03688.
  Cited by: §6.6.
- Liu et al. (2024b)
  Z. Liu, G. Dou, Z. Tan, Y. Tian, and M. Jiang
  Towards safer large language models through machine unlearning.
  arXiv preprint arXiv:2402.10058.
  Cited by: §7.5,
  §9.4.
- Maharana et al. (2024)
  A. Maharana, D. Lee, S. Tulyakov, M. Bansal, F. Barbieri, and Y. Fang
  Evaluating very long-term conversational memory of LLM agents.
  arXiv preprint arXiv:2402.17753.
  Cited by: Table 1,
  §5.2,
  §5.5.
- Modarressi et al. (2024)
  A. Modarressi, A. Rizvi, M. Rezagholizadeh, and P. Poupart
  MemLLM: finetuning LLM to use an explicit read-write memory.
  arXiv preprint arXiv:2404.11672.
  Cited by: §4.6,
  §9.7.
- Nair et al. (2023)
  V. Nair, E. Schumacher, G. Tso, and A. Kannan
  DERA: enhancing large language model completions with dialog-enabled resolving agents.
  arXiv preprint arXiv:2303.17071.
  Cited by: §6.6.
- Ouyang et al. (2022)
  L. Ouyang, J. Wu, X. Jiang, D. Almeida, C. L. Wainwright, P. Mishkin, C. Zhang, S. Agarwal, K. Slama, A. Ray, et al.
  Training language models to follow instructions with human feedback.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §9.9.
- Packer et al. (2024)
  C. Packer, S. Wooders, K. Lin, V. Fang, S. G. Patil, I. Stoica, and J. E. Gonzalez
  MemGPT: towards LLM as operating systems.
  arXiv preprint arXiv:2310.08560.
  Cited by: §1.2,
  §3.2,
  §3.3,
  Table 1,
  §4.4,
  §6.1,
  §7.6.
- Park et al. (2023)
  J. S. Park, J. C. O’Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein
  Generative agents: interactive simulacra of human behavior.
  In Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST),
  Cited by: §1.2,
  §2.4,
  §3.1,
  Table 1,
  §4.3.
- Qian et al. (2024)
  C. Qian, X. Cong, C. Yang, W. Chen, Y. Su, J. Xu, Z. Liu, and M. Sun
  ChatDev: communicative agents for software development.
  arXiv preprint arXiv:2307.07924.
  Cited by: §6.2.
- Raad et al. (2024)
  J. Raad, X. Li, P. West, and Y. Choi
  Scaling retrieval-based language models with a trillion-token datastore.
  arXiv preprint arXiv:2407.12854.
  Cited by: §4.2.
- Schick et al. (2024)
  T. Schick, J. Dwivedi-Yu, R. Dessì, R. Raileanu, M. Lomeli, L. Zettlemoyer, N. Cancedda, and T. Scialom
  Toolformer: language models can teach themselves to use tools.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §6.6.
- Shinn et al. (2023)
  N. Shinn, F. Cassano, E. Berman, A. Gopinath, K. Narasimhan, and S. Yao
  Reflexion: language agents with verbal reinforcement learning.
  arXiv preprint arXiv:2303.11366.
  Cited by: §1.2,
  Table 1,
  §4.3.
- Squire (2004)
  L. R. Squire
  Memory systems of the brain: a brief history and current perspective.
  Neurobiology of Learning and Memory 82 (3), pp. 171–177.
  Cited by: §3,
  §9.1,
  §9.1.
- Sukhbaatar et al. (2015)
  S. Sukhbaatar, A. Szlam, J. Weston, and R. Fergus
  End-to-end memory networks.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §1.2.
- Sumers et al. (2024)
  T. R. Sumers, S. Yao, K. Narasimhan, and T. L. Griffiths
  Cognitive architectures for language agents.
  Transactions on Machine Learning Research.
  Cited by: §4.4,
  §8.
- Sun et al. (2024)
  J. Sun, Z. Shi, S. Han, C. Gan, and Y. Du
  RET-LLM: towards a general read-write memory for large language models.
  arXiv preprint arXiv:2305.14322.
  Cited by: §4.2.
- Tan et al. (2025)
  H. Tan, Z. Zhang, C. Ma, X. Chen, Q. Dai, and Z. Dong
  MemBench: towards more comprehensive evaluation on the memory of LLM-based agents.
  arXiv preprint arXiv:2506.21605.
  Cited by: §1.3,
  Table 1,
  §5.2.
- Touvron et al. (2023)
  H. Touvron, T. Lavril, G. Izacard, X. Martinet, M. Lachaux, T. Lacroix, B. Rozière, N. Goyal, E. Hambro, F. Azhar, et al.
  LLaMA: open and efficient foundation language models.
  arXiv preprint arXiv:2302.13971.
  Cited by: §1.
- Tulving (1972)
  E. Tulving
  Episodic and semantic memory.
  Organization of Memory, pp. 381–403.
  Cited by: §3.
- Wang et al. (2023a)
  G. Wang, Y. Xie, Y. Jiang, A. Mandlekar, C. Xiao, Y. Zhu, L. Fan, and A. Anandkumar
  Voyager: an open-ended embodied agent with large language models.
  arXiv preprint arXiv:2305.16291.
  Cited by: §1.2,
  §2.4,
  §3.1,
  §3.2,
  Table 1,
  §6.3.
- Wang et al. (2024a)
  L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin, W. X. Zhao, Z. Wei, and J. Wen
  A survey on large language model based autonomous agents.
  Frontiers of Computer Science 18 (6), pp. 186345.
  Cited by: §1.3,
  §8.
- Wang et al. (2023b)
  W. Wang, L. Dong, H. Cheng, X. Liu, X. Yan, J. Gao, and F. Wei
  Augmenting language models with long-term memory.
  In Advances in Neural Information Processing Systems (NeurIPS),
  Cited by: Table 1.
- Wang et al. (2024b)
  Z. Wang, S. Cai, A. Liu, Y. Jin, J. Hou, B. Zhang, H. Lin, Z. He, Z. Zheng, Y. Yang, X. Ma, and Y. Liang
  JARVIS-1: open-world multi-task agents with memory-augmented multimodal language models.
  arXiv preprint arXiv:2311.05997.
  Cited by: §4.4,
  §6.3,
  §9.5.
- Wei et al. (2022)
  J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. V. Le, and D. Zhou
  Chain-of-thought prompting elicits reasoning in large language models.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §3.2.
- Weston et al. (2015)
  J. Weston, S. Chopra, and A. Bordes
  Memory networks.
  arXiv preprint arXiv:1410.3916.
  Cited by: §1.2.
- Wu et al. (2023)
  Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, J. Liu, et al.
  AutoGen: enabling next-gen LLM applications via multi-agent conversation.
  arXiv preprint arXiv:2308.08155.
  Cited by: §6.5.
- Wu et al. (2022)
  Y. Wu, M. N. Rabe, D. Hutchins, and C. Szegedy
  Memorizing transformers.
  arXiv preprint arXiv:2203.08913.
  Cited by: §1.2.
- Xi et al. (2023)
  Z. Xi, W. Chen, X. Guo, W. He, Y. Ding, B. Hong, M. Zhang, J. Wang, S. Jin, E. Zhou, et al.
  The rise and potential of large language model based agents: a survey.
  arXiv preprint arXiv:2309.07864.
  Cited by: §1.3,
  §8.
- Xu et al. (2024)
  P. Xu, W. Ping, X. Wu, L. McAfee, C. Zhu, Z. Liu, S. Subramanian, E. Bakhturina, M. Shoeybi, and B. Catanzaro
  Retrieval meets long context large language models.
  arXiv preprint arXiv:2310.03025.
  Cited by: §7.4,
  §8.
- Yao et al. (2024)
  S. Yao, D. Yu, J. Zhao, I. Shafran, T. L. Griffiths, Y. Cao, and K. Narasimhan
  Tree of thoughts: deliberate problem solving with large language models.
  Advances in Neural Information Processing Systems (NeurIPS).
  Cited by: §6.7.
- Yao et al. (2022)
  S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao
  ReAct: synergizing reasoning and acting in language models.
  arXiv preprint arXiv:2210.03629.
  Cited by: §1.2,
  Table 1.
- Yu et al. (2026)
  Y. Yu, L. Yao, Y. Xie, Q. Tan, J. Feng, Y. Li, and L. Wu
  Agentic memory: learning unified long-term and short-term memory management for large language model agents.
  arXiv preprint arXiv:2601.01885.
  Cited by: §1.2,
  §1.3,
  §3.3,
  Table 1,
  §4.5,
  §7.6,
  §9.9.
- Zhang et al. (2024a)
  C. Zhang, K. Yang, S. Du, X. Guo, Y. Chen, Y. Huang, H. Li, K. Zhu, Z. Zheng, H. Fan, J. Li, Y. Song, Y. Sun, and S. Hong
  ProAgent: building proactive cooperative agents with large language models.
  Proceedings of the AAAI Conference on Artificial Intelligence 38.
  Cited by: §6.5.
- Zhang et al. (2024b)
  Z. Zhang, X. Bo, C. Ma, R. Li, X. Chen, Q. Dai, J. Zhu, Z. Dong, and J. Wen
  A survey on the memory mechanism of large language model based agents.
  arXiv preprint arXiv:2404.13501.
  Cited by: §1.1,
  §1.3,
  §8.
- Zhao et al. (2024)
  A. Zhao, D. Huang, Q. Xu, M. Lin, Y. Liu, and G. Huang
  ExpeL: LLM agents are experiential learners.
  Proceedings of the AAAI Conference on Artificial Intelligence 38.
  Cited by: Table 1,
  §4.3.
- Zhong et al. (2022)
  W. Zhong, L. Guo, Q. Gao, H. Ye, and Y. Wang
  Training language models with memory augmentation.
  arXiv preprint arXiv:2205.12674.
  Cited by: §4.6.
- Zhong et al. (2024)
  W. Zhong, L. Guo, Q. Gao, H. Ye, and Y. Wang
  MemoryBank: enhancing large language models with long-term memory.
  Proceedings of the AAAI Conference on Artificial Intelligence 38.
  Cited by: Table 1,
  §6.1,
  §9.8.
- Zhu et al. (2023)
  X. Zhu, Y. Chen, H. Tian, C. Tao, W. Su, C. Yang, G. Huang, B. Li, L. Lu, X. Wang, Y. Qiao, Z. Zhang, and J. Dai
  Ghost in the minecraft: generally capable agents for open-world environments via large language models with text-based knowledge and memory.
  arXiv preprint arXiv:2305.17144.
  Cited by: §6.3.
