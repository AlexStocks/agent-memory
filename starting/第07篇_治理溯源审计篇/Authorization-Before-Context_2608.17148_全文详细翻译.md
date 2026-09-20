# Authorization Before Context：防止跨受众记忆泄露的模型中立边界

> 原文：*Authorization Before Context: A Model-Neutral Audience Boundary Against Cross-Audience Memory Leakage in Agentic Systems*
> arXiv：2608.17148v1，2026-08
> 证据说明：作者明确称评测是初步的合成数据结果。

## 摘要

个人 agent 可能同时服务 owner-private、1:1 和群聊。一个事实在私聊中被记录，之后如果只按相关性检索，就可能进入更大范围的对话。输出过滤太晚：模型已经看过未授权事实，事后删掉回答无法撤回这次暴露。

本文提出“先授权，再组装上下文”。每条记忆保存写入时的 audience；当前请求从通道元数据解析 viewer 集合。只有当当前所有 viewer 都属于原 audience 时，该记忆才允许进入 prompt。如果 viewer 集合不明确，系统回退到 public-only，并 fail closed。

## 1. 规则

设记忆条目的 audience 为 A，当前容器的 viewer 集合为 V(C)。条目只有在下式成立时才能进入上下文：

```text
V(C) ⊆ A
```

audience 是记录时参与者集合，不是 channel/thread 名字；同一组参与者在不同通道中仍然属于同一作用域。公共 audience 是一个保留值，表示所有人可见。

这个规则是单调的：当前 viewer 越多，能通过检查的窄 audience 条目不会变多。它不依赖模型类型，human viewer 和 agent viewer 用同一套成员关系检查。

## 2. 威胁模型

论文考虑三类风险：跨 audience 打听、通道参与者不明确导致过度共享、以及被植入一个 scope 的恶意记忆后来扩散到其他 scope。保护对象包括每次对话信息、由其派生的记忆、发送给模型的精确上下文、以及支撑授权的 audience/provenance 标签。

论文假设传输层能正确提供当前对话参与者，并不试图解决所有 prompt injection。它解决的是“即使记忆里有被植入的内容，也不能把它送给原 audience 之外的人”。

## 3. 实现边界

所有记忆可以放在一个共享、带 audience 标签的 store 中，recency buffer、摘要长期记忆和知识图都由同一个 audience decision 控制，但执行点可以不同：

- 当前 turn 的最近消息只在当前 scope 内回忆；
- 摘要长期存储把允许的 scope 直接带入查询，避免先取出再删除；
- 图检索在 hybrid search 后过滤，直接 entity lookup 在内部做检查，并对“不存在”和“存在但未授权”返回相同结果，防止存在性泄露；
- 不能按条目证明 audience 的聚合实体摘要直接 fail closed。

## 4. 评测

作者用固定种子的合成 Contextual-Integrity 数据生成 79 个场景，覆盖 owner-private、精确共享、跨通道、未知 viewer、混合不一致证据、对抗边界和 poisoning。

结果是：79 个场景中，禁止事实进入最终上下文为 0；授权决策与预期策略 79/79 一致；需要 fail-closed 的 16 个场景全部覆盖。一个不带 scope 的 baseline 会按定义把禁止事实带入上下文，用来表示需要消除的泄露上界。

论文还用不经过模型的 hermetic run 复现 0/79，说明度量发生在真实 context assembly path，而不是仅对模型输出做投影。作者报告了一个内部人工审核的 live regression fixture，但生产数据和全部过程并未公开。

## 5. 局限

证据是合成的、初步的，依赖传输层正确提供参与者集合。它不评估 action safety、audience widening、记忆事实质量，也不解决通用 prompt injection。规则只能保证未授权事实不进入上下文，不能保证已授权事实本身是真的。

## 6. 工程启示

访问控制的硬边界应该位于“记忆到上下文”的转换点。只要秘密已经进入模型上下文，输出过滤就没有机会撤回暴露。把 audience 固定在写入时、在每次组装时重新检查，并对不明确情况 fail closed，是比“让模型自己遵守隐私”更可审计的设计。
