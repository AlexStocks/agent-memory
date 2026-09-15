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
