# RESEARCH_LOG

ArXiv 论文研究工作日志。每条记录格式：论文发表日期 + 标题 + 作者 + 链接 + 相关性说明。

---

### [2026-01-08] Beyond Static Summarization: Proactive Memory Extraction for LLM Agents
- **Authors**: Chengyuan Yang, Zequn Sun, Wei Wei, Wei Hu
- **Link**: https://arxiv.org/abs/2601.04463
- **Summary**: 提出 ProMem，把记忆抽取从「一次性摘要」改造为「初始抽取 → 语义匹配补全 → 自我提问验证」的三段回路，论证依据是认知神经科学的循环加工理论（RPT）。在 HaluMem 上把记忆完整性从 41%—43% 抬到 81.37%（v2），LongMemEval-S 72.12%、LoCoMo 77.56%。EMNLP 2026 Findings。**注意 v2（2026-09-01）大幅改写实验章节**：v1 中 ProMem 是完整性与 QA 双料第一，v2 中这两项第一归新增基线 MemOS（84.81 / 67.23），ProMem 改为「记忆准确率 94.68 与 F1 87.52 最高、平衡最好」。本仓库译文基于 v1，文末已加 v2 附录。

### [2026-02-13] Learning to Remember: End-to-End Training of Memory Agents for Long-Context Reasoning (UMA)
- **Authors**: Kehao Zhang, Shangtong Gui, Sheng Yang, Wei Chen（理想汽车）, Yang Feng（通讯，中科院计算所 / 中国科学院大学）
- **Link**: https://arxiv.org/abs/2602.18493
- **Summary**: 统一记忆智能体 UMA：把记忆操作（CRUD）与问答统一在单一策略内做端到端强化学习，用任务分层 GRPO 让下游问答结果反向监督记忆写入。自建 Ledger-QA 连续状态追踪基准；13 个数据集平均 77.36%（MemAlpha 64.50%）。消融显示放弃端到端（分两阶段训练）会掉 11 个百分点。EMNLP 2026 Main。定位为 ProMem 的「可学习后继」——把手工设计的写入回路升级为可学习策略。代码：https://github.com/ictnlp/unified-memory-agent

### [2026-03-16] Selective Memory for Artificial Intelligence: Write-Time Gating with Hierarchical Archiving
- **Authors**: Oliver Zahn, Simran Chana
- **Link**: https://arxiv.org/abs/2603.15994
- **Summary**: SGW-HA，「写时门控 + 分层归档」。用三个写时可见的信号（来源声誉、新颖性、来源可靠性）算复合显著性分数，超阈值进活跃存储、低于阈值进冷归档而非丢弃；门控不访问 oracle。合成对抗基准上未门控 13.3% → 门控 100%；干扰比 8:1 时读时过滤（Self-RAG）崩溃到 0% 而写时门控保持 100%。核心论断：**取代创造的是层级，而不是替换**。实验规模小（50 个对象），作者自述为机制演示而非效应量估计。

### [2026-07-17] LazyMem: Retrieve Broadly, Construct Selectively for Efficient Long-Term Agent Memory
- **Authors**: Jing Yu, Yibo Zhao, Jiaming Zhang, Xiang Li（华东师范大学数据科学与工程学院）
- **Link**: https://arxiv.org/abs/2607.22690（v2 2026-07-28）
- **Summary**: 「先检索后构造」路线。写入时原样存储、零处理；查询时宽泛检索出高召回池，再由一个经 SFT + GRPO 训练的 4B 记忆处理模型在重叠并行窗口上做 Keep/Drop 与查询条件压缩。LongMemEval 上 LLM 评判 0.85，仅用 213 个记忆 token（比 RAG Top50 少 68.7×）；LoCoMo 零样本 0.68；32B 变体 0.93。**是 Selective Memory「写时压缩优于读时过滤」的正面反例**。其反面边界：唯一输给 oracle 的题型是基于用户历史的推荐（SSP 0.50 vs 0.67），说明持久用户画像仍需写入时维护。代码：https://github.com/allacnobug/LazyMem

### [2026-07-26] When Does Memory Help? A Cost-Aware Evaluation of Long-Term Memory in Tool-Using LLM Agents (MERIT)
- **Authors**: Shweta Mishra, Shashank Mishra（Independent Research）
- **Link**: https://arxiv.org/abs/2609.05441
- **Summary**: 指出主流记忆评测（LoCoMo / LongMemEval / BEAM）测的是「能否回答长对话问题」，而非「被记住的事实有没有改变 agent 行为」。构建三个领域的分幕工具调用基准（含难度阶梯、自动泄漏检查、受控记忆损坏、token 与美元全计量），23,440 个计分幕、$42.57。**核心结果：在「事实被更新」档上，写时更新式记忆（结构化事实库、LLM 摘要）稳定 0.70—1.00，而嵌入检索跨模型不可预测地崩到 0.30—0.95（种子间最大差距 0.45），混合方案不如其「较好的那一半」。** 新失败面：agent 会忽略已正确检索到的事实（忽略率 0.45）、陈旧记忆危害、以及「记忆来源怀疑」（Opus 4.8 在全重放控制格上拒绝据记忆行动）。**「检索正确 ≠ 行动正确」的最强第三方证据。** 代码：https://github.com/smshweta/merit-bench

### [2026-09-02] MemoryLACE: Memory Lifecycle-Aware Consolidation and Evidence Retrieval
- **Authors**: Meriem Yacoubi, Pia Schmidt, Nenad Petrovic, Ahmed Frikha, Martin Kirchhoff, Alois Knoll（慕尼黑工业大学 / inovex GmbH / Cerebras Systems）
- **Link**: https://arxiv.org/abs/2609.03201
- **Summary**: MemLACE，位于「扁平文本记忆」与「完备结构化记忆」之间的轻量中间路线：保留原子的自然语言记忆与溯源，用稀疏局部关系（合并 / 取代 / 矛盾）显式建模证据生命周期；检索时沿关系扩展出「当前—历史—支持—冲突」证据单元。BEAM 100K 同主干最优（4B 45.4 / 9B 51.9），运行时比反思式基线 Hindsight 降 66.6%（2.99×）；StructMemEval 状态追踪 100%、树结构 100%（Mem-Agent 57% / 50%）。消融：生命周期扩展 −5.16、时间感知 −4.97，两者不可互换。结论：**长期记忆的主要挑战不是更丰富的全局结构，而是保留证据随时间的演化方式。** 边界：计数类 0%、推荐类 8.33%。

### [2026-09-08] Revoked but Still Authoritative: An Empirical Study of Revocation Enforcement in Agent-Memory Systems
- **Authors**: Yi Ting Shen, Kentaroh Toyoda, Alex Leung（Vulcan Research, AIFT，新加坡）
- **Link**: https://arxiv.org/abs/2609.08258
- **Summary**: 首次实测「软撤销」（把被矛盾的事实标记为失效并保留，即 Selective Memory 的「归档而非删除」）在检索时是否真被执行。五个主流系统（Graphiti、Zep、mem0、langmem、cognee）× 9 场景 × 9 模型 × 6 种防御条件。**结论：没有任何系统默认强制执行撤销**；两款把已撤销记录 81/81 返回且每次排在替代项之上，导致 agent 在 43.1%（699/1,620）的试验中采取不安全动作。三种失效形态：撤销未记录 / 记录但对调用方隐瞒 / 记录可见但检索时不执行。**关键补充：仅提示词加固几乎无效（43.1% → 37.2%），存储级过滤才彻底消除（0/1,620）；失效点在检索而非存储（同一数据只改一个检索标志，81 个单元中 39 个从安全翻成不安全且从未反向）；与模型能力无相关性（九款 15.0%—60.0%，最抗的是最快的非推理模型）。** 给「归档而非删除」补上必备条件：归档之后必须在检索层加一道有效性闸门。代码：https://github.com/VulcanLab/Memory-Rebirth-Attack

---

## 第 6 篇《有界召回篇》同期论文核查（2026-09-18）

> 核查报告全表见 `memory/series6/第6篇_同期论文核查_2026-09-18.md`。以下为 S / A 级论文的正式归档条目。

### [2026-08-21] Utility Under Attack: Agent Memory Poisoning and the Limits of Content Screening and Provenance Ranking
- **Authors**: Arulnidhi Karunanidhi
- **Link**: https://arxiv.org/abs/2608.21230
- **译文**: `starting/第06篇_有界召回篇/UtilityUnderAttack_2608.21230_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: 与 WMT 同日发表，正面对上 P-1 的投毒实验。用朴素措辞（无指令、无触发器、无检索器优化）的假陈述投毒 **1.2%** 的 LongMemEval 语料，准确率 0.850 → 0.300。四阶段写时筛查对间接 prompt injection 有 0.832 recall、只误标 1.5% 含触发词的良性文本，但 **360 条投毒记忆一条都没拒掉（0/360）**。溯源加权：出厂权重与不设防统计不可区分（p=0.80）；强权重只能靠排斥不可信内容换效用（混合溯源语料 0.3167 → 0.7000），但当答案证据本身不可信时，证据召回掉到 0、准确率 0.0417。结论：**加性溯源惩罚没有可用工作点，应改为检索侧的有界占用约束（bounded occupancy）**。给 P-1「AF 压到 0.965 但未归零」提供了结构性解释。边界：单作者；投毒为朴素虚假陈述，不能外推为「内容筛查对对抗性投毒无效」。

### [2026-07-20] Retain or Consolidate? Budget-Dependent Operator Selection for Language Agent Memory
- **Authors**: Qingcan Kang, Mingyang Liu, Shixiong Kai 等 8 人
- **Link**: https://arxiv.org/abs/2607.17545（v2）
- **译文**: `starting/第06篇_有界召回篇/RetainOrConsolidate_2607.17545_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: 把「记忆该不该压」从启发式打分升级为**预算依赖的算子选择**：保留 vs 整合，整合再选 Merge / Abstract / Rewrite。核心理论是把每个算子的效用分解为对「保留会漏掉的证据」的 coverage effect 与对「已经装得下的原始证据」的**带符号** replacement effect，两者的平衡解释了为何偏好动作随相对预算压力翻转。实现为 OAS，从预生成特征估计动作效用并做 held-out 危害校准。LongMemEval 紧凑预算下整合带来最高 **+48% 绝对准确率**，松预算下保留更优；LoCoMo 在更小预算复现同一 crossover（与其证据更短一致）；需要压缩时跨笔记抽象与合并普遍优于局部重写。**是对 P-1 固定系数（0.75 / 0.30）的直接否定：不存在全局最优策略。**

### [2026-09-08] What Eviction Destroys: A Restore-Counterfactual Audit of Forgetting in Agent Memory
- **Authors**: Chen Shen
- **Link**: https://arxiv.org/abs/2609.08279
- **译文**: `starting/第06篇_有界召回篇/EvictionDestroys_2609.08279_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: 提出 **restore counterfactual**——逐题配对干预，把该题的 gold evidence 在读取时重新装回上下文并重跑同一 reader；结合正确性变化与「驱逐后证据是否仍在」把每个可答错题分为可恢复 / 不可逆 / 残余三类。在 LongMemEval-S 上评 FIFO / random / 冗余感知 / LLM 重要性四种驱逐策略 × 3 预算 × 2 检索口径。**80k 预算 top-k 检索下，被恢复纠正的错误里不可逆占比 0.67—0.73（LLM 重要性 0.60）；8k 预算下四种策略全部达到 1.00。** 另指出预算-准确率结果在检索口径不同时不可直接比较。**给第 6 篇 6.4 节「证据下限」提供量化刻度：压缩真正不可逆的比例是有方法可测的。** 边界：单作者；匹配准确率分析分辨率 1.2—6 pp，「未检测到差异」≠「无差异」。

### [2026-08-13] RippleMem: From Isolated Retrieval to Associative Recollection for Long-Term Agent Memory
- **Authors**: Jingbo Ji, Lingyi Li, Xilong Cheng 等 7 人
- **Link**: https://arxiv.org/abs/2608.13334
- **译文**: `starting/第06篇_有界召回篇/RippleMem_2608.13334_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: **StructMem 的正面竞品**，痛点陈述几乎一致：全上下文要噪声搜索、扁平检索返回孤立不完整记录、图记忆构建贵且压掉丰富事件语境。RippleMem 把交互历史存成 cue-rich episodic memory units 并组织为事件中心图，查询时先用混合线索召回 anchors，再沿语义与结构关联**扩展补全缺失证据**——已被召回的记忆既是答案上下文也是补全线索。LoCoMo 与 LongMemEval-S 上整体最优，LLM-as-Judge 准确率 LoCoMo +3.95%、LongMemEval-S 最多 +11.87%，**图构建成本降约 30×**。与 P-2 的关键差异：StructMem 的跨事件整合是离线周期性批处理、种子选择对查询是盲的；RippleMem 是查询时在线联想补全。

### [2026-08-03] MemSIF: From Structured Interactions to Dual-Track Fact Memory for LLM Agents
- **Authors**: YuFei Luo, Xiucheng Xu, Zhen Yang
- **Link**: https://arxiv.org/abs/2608.01742（v2）
- **译文**: `starting/第06篇_有界召回篇/MemSIF_2608.01742_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: 命名两种长期交互中的失配：**TSM（Temporal-Structural Misalignment，时间邻近不能可靠对齐主题或事件级相关性）**与 **DUM（Delayed Utility Manifestation，写时显著性不能可靠预测未来查询效用）**。DUM 同时打在 P-1 写时打分与 P-2 写时结构上——若写时信号预测不了未来效用，两侧都要打折。解法：Structured Interaction Memory（Topical Segments 保留局部主题连贯 + Event Trajectories 维持跨时事件连续）+ Dual-Track Fact Memory（CoreFact 写时按 schema 固化稳定信息；ActiveFact 按需生成，被多源支持且反复被查询才提升为复用）。LoCoMo 与 LongMemEval-S × 5 基座全部取得最高 Total ACC，比最强基线高 2.29%—8.79%（LoCoMo）/ 2.87%—6.15%（LongMemEval-S）。代码：https://github.com/luoyufeihaha/MemSIF

### [2026-08-17] What Does Context Compression Cost an Agent? Interaction Costs Unrevealed by Task-Completion Metrics
- **Authors**: Shuyu Liu
- **Link**: https://arxiv.org/abs/2608.16370
- **译文**: `starting/第06篇_有界召回篇/CompressionCost_2608.16370_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: **明确引用 Memento（P-3）**。用有界时程（固定 24 轮）工具调用 agent 的受控运行时协议测量「再获取成本」：压缩会让 agent 被迫重新获取被丢弃的状态，而完成度可能统计上毫无变化。六个模型-场景对照中检索调用**全部上升**且几乎解释了全部新增交互，五组通过 Holm 校正；预设 5× 压缩点上完成度变化均不显著；GPT-5.5 最典型：完成度 80% → 85%（p=1.0）而检索从 21.0 涨到 63.9 次（p=.002）。保留干预进一步分离状态数量/类型/内容有效性：用语义无关内容替换保留状态使检索 +57%（p<.001）而完成度无显著变化。ALFWorld 上滑窗压缩没有检索激增，说明该特征是环境依赖的。**结论：P-3 报的 7.4 / 15.3 个百分点只是压缩代价的下界。** 边界：单作者。

### [2026-08-29] Selective Forgetting: A Graph-Based Memory Framework for Long-Term LLM Agents
- **Authors**: Theo Rusu, Sourena Khanzadeh, Manar Alalfi
- **Link**: https://arxiv.org/abs/2608.28978
- **译文**: `starting/第06篇_有界召回篇/SelectiveForgetting_2608.28978_全文详细翻译.md`（2026-09-18 完成带图带表的全文翻译，check_trans 校验 PASS）
- **Summary**: 直接检验「图记忆是否比扁平检索更强」这一假设。框架把每轮对话抽成带类型节点与属性边，用两跳子图答题，并周期性剪掉「新近度 + 访问频次 + 度中心性 + 时间」加权得分低的节点。**LongMemEval 上，在匹配的候选生成预算（5 个检索根）下，图未超过扁平向量基线**：token F1 0.417 vs 0.468，500 题配对 bootstrap Δ=-0.050（95% CI [-0.085,-0.016]）；差距最大在「需回忆某条助手原话」类，judged correctness 从 0.911 掉到 0.607——把 turn 拆成实体丢掉了这些题依赖的表层形式。**但遗忘模块是成功的**：对 27,021 节点的持久图剪掉 9.8% 节点 / 9.5% 字节，token F1 不变（+0.001，CI [-0.015,+0.016]），judged correctness 仅降 1.6 点（损失上界 3.8 点）。作者自述：单抽取器单基准，结论刻画该抽取式流水线而非图结构记忆整体。代码：https://github.com/skhanzad/Selective-Amnesia

---

### 第 6 篇核查中值得关注的其余同期论文（一行式）

| 日期 | 编号 | 标题 | 相关性 |
|---|---|---|---|
| 2026-06-14 | [2606.15903](https://arxiv.org/abs/2606.15903) | Control-Plane Placement Shapes Forgetting | 13 配置/385 对抗案例；**生产故障主要是遗忘故障，而现有基准只测召回**；发布 ForgetEval |
| 2026-06-18 | [2606.20047](https://arxiv.org/abs/2606.20047) | PACMS: Submodular Context Selection | 把「留谁」做成有理论保证的子模最大化，统一「对话轮 + 记忆条目 + 工具输出」为一个候选池 |
| 2026-06-23 | [2606.25115](https://arxiv.org/abs/2606.25115) | Forget to Improve: Budget-Curated Memory | **net-value-per-byte** 单一标尺统治 KEEP/SHARE/TRUST；端侧 2.7× 内存↓、注入成功率 0.75→0 |
| 2026-05-29 | [2607.22562](https://arxiv.org/abs/2607.22562) | SF-AMS: Strategic Forgetting for Structured Memory | 用**使用冗余度 + 时间信号**而非落选次数更新重要性；LoCoMo 多跳 +9.65 F1 |
| 2026-07-31 | [2607.29167](https://arxiv.org/abs/2607.29167) | Memory Provenance Laundering | **溯源洗白**：整合改写会把外部观察变成「看似用户历史」；脆弱整合记忆 ASR 达 1.000 |
| 2026-08-31 | [2608.30177](https://arxiv.org/abs/2608.30177) | Understanding Stage-Wise Utility-Risk Trade-offs | MemGauge：写入准入 / 管理策略 / 检索暴露三阶段分别扰动 × 11 LLM |
| 2026-08-12 | [2608.11775](https://arxiv.org/abs/2608.11775) | The Sleeping Agent: What Gist Compression Loses | gist 压缩的**任务类型交互**；时间题塌陷源于摘要丢日期，一句提示词把时间保留率 3.05%→62.39% |
| 2026-08-08 | [2608.07855](https://arxiv.org/abs/2608.07855) | CommitKV: Lifecycle-Aware KV Cache Compression | 区分**「暂时休眠」与「似乎已无用」**——P-1「落选 ≠ 无用」在 KV 层的同构 |
| 2026-08-16 | [2608.15797](https://arxiv.org/abs/2608.15797) | KV-Rescue | 驱逐损失是**信息缺口而非能力缺口**（oracle 回收 79%），B=64 下回收 87% |
| 2026-08-21 | [2608.21690](https://arxiv.org/abs/2608.21690) | Context as an Environment (Scroll) | append-only Event Log + 持久 Python kernel，驱逐 span 可精确回跳；LongMemEval_S 94.8%。**PC 最该对标的形态** |
| 2026-06-22 | [2606.23525](https://arxiv.org/abs/2606.23525) | Self-Compacting Language Model Agents | tool + 轻量 rubric，**免训练**让模型自己决定何时压；token 成本降 30—70% |
| 2026-06-29 | [2606.30005](https://arxiv.org/abs/2606.30005) | LLM Agents Are Latent Context Managers (VISTA) | 前沿模型**对自身上下文本体感觉盲**——对 P-3「模型自评语义边界」的前提性质疑 |
| 2026-06-13 | [2606.15405](https://arxiv.org/abs/2606.15405) | T-Mem: Memory That Anticipates, Not Archives | 区分 descriptive（共享表层特征）与 associative（仅潜在语义弧相连）两类可达性 |
| 2026-05-15 | [2605.15759](https://arxiv.org/abs/2605.15759) | DimMem: Dimensional Structuring | typed 原子自包含记忆单元；LoCoMo 81.43 / LongMemEval-S 78.20，per-query token −24% |
| 2026-08-17 | [2608.17053](https://arxiv.org/abs/2608.17053) | Memory Is Communication | 把记忆预算与通信预算放进同一可达域，定义 **remembering–signaling frontier** |
| 2026-04-17 | [2604.16548](https://arxiv.org/abs/2604.16548) | A Survey on Long-Term Memory Security | 记忆生命周期框架：6 阶段 × 4 目标，**第 7 篇（治理/溯源/审计）的现成骨架** |
| 2026-09-01 | [2609.00551](https://arxiv.org/abs/2609.00551) | EM²Mem: Event-Centric Multimodal Memory | 事件锚定多模态记忆，cite StructMem；来自 zjunlp/LightMem 家族 |
| 2026-05-27 | [2605.28773](https://arxiv.org/abs/2605.28773) | Rethinking Memory as Continuously Evolving Connectivity (FluxMem) | 记忆视为持续演化的异质图，三阶段拓扑精炼 |
| 2026-06-10 | [2606.11680](https://arxiv.org/abs/2606.11680) | HORMA: Organize then Retrieve | 文件系统式层级 + 摘要实体链接回原始轨迹；长对话 token ≤ 基线 22.17% |
| 2026-08-30 | [2608.29606](https://arxiv.org/abs/2608.29606) | Agent Zero Memory | provenance-aware 三套并行记忆，不选单一组织路线 |
