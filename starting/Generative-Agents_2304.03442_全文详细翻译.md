# 《Generative Agents: Interactive Simulacra of Human Behavior》全文详细翻译

> **生成式智能体：人类行为的交互式拟像**

| 项目 | 信息 |
|---|---|
| **arXiv** | [2304.03442](https://arxiv.org/abs/2304.03442)（v2，2023-08-06 更新；初版 2023-04-07） |
| **作者** | Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein（斯坦福大学） |
| **发表** | UIST 2023（ACM Symposium on User Interface Software and Technology） |
| **分类** | cs.HC（主）/ cs.AI / cs.LG |
| **关键词** | Human-AI interaction, agents, generative AI, large language models |
| **开源** | https://github.com/joonspk-research/generative_agents |
| **演示** | https://reverie.herokuapp.com/UIST_Demo/ |

**翻译说明**：本文基于 arXiv v2 全文（ar5iv HTML 版）逐段忠实翻译。引用标记（如 [Card et al. 1983]）、人物名、地名（Smallville、Hobbs Cafe 等）、提示词（prompt）原文均保留原样；提示词与智能体对话以引用块呈现，保留英文原文并附中文对照。论文中第 8–9 节的逐字原文因全文源通道限制未获取到，已在文末如实标注。

---

## 摘要

可信的人类行为代理（believable proxies of human behavior）可以赋能各类交互式应用，从沉浸式环境、人际沟通的演练空间，一直到原型设计工具。在本文中，我们提出**生成式智能体**（generative agents）——即模拟可信人类行为的计算型软件智能体。生成式智能体会起床、做早餐、去上班；画家作画，作家写作；它们形成观点、注意到彼此、发起对话；它们在规划第二天时会回忆并反思过去的日子。

为了实现生成式智能体，我们描述了一种架构：它扩展大语言模型，以自然语言存储智能体经验的完整记录，随时间推移将这些记忆合成为更高层次的**反思**（reflection），并动态检索它们以规划行为。我们将生成式智能体实例化，填充到一个受《模拟人生》（The Sims）启发的交互式沙盒环境中，终端用户可以用自然语言与一个由 25 个智能体组成的小镇互动。

在评估中，这些生成式智能体产生了可信的个体行为与涌现的群体行为：例如，仅从一个用户指定的想法——某个智能体想办一场情人节派对——出发，智能体们会在接下来的两天里自发地传播派对邀请、结识新朋友、互相邀约一起去派对，并协调好在正确的时间一同出现在派对上。我们通过消融实验证明，智能体架构的各个组成部分——观察、规划与反思——每一个都对行为的可信度有关键贡献。通过将大语言模型与计算型交互式智能体相融合，本工作为实现对人类行为的可信模拟引入了架构范式与交互范式。

**关键词**：人机交互；智能体；生成式人工智能；大语言模型

---

## 1. 引言

我们该如何构建一个反映可信人类行为的交互式人工社会？从《模拟人生》这类沙盒游戏，到认知模型（[Card et al. 1983]）与虚拟环境（[Laird and VanLent 2001]；[Bates 1994]）这类应用，四十多年来，研究者与实践者一直设想能用计算型智能体充当可信的人类行为代理。在这些设想中，由计算驱动的智能体行为与其过往经验保持一致，并对环境做出可信的反应。这类人类行为模拟可以为虚拟空间与社区填充真实的社会现象（[Dill and Martin 2011]；[Park et al. 2022]），训练人们如何应对罕见却棘手的人际情境（[Tambe et al. 1995]；[Jones et al. 1999]；[Hollan et al. 1984]），检验社会科学理论（[Binz and Schulz 2023]；[Horton 2023]），打造用于理论与可用性测试的"人类处理器模型"（[Card et al. 1983]；[John and Kieras 1996]；[Hämäläinen et al. 2023]），驱动普适计算应用（[Fast et al. 2016]）与社交机器人（[Bates 1994]；[Bledsoe 1986]），并支撑游戏中的非玩家角色（NPC）（[Laird and VanLent 2001]；[Riedl 2012]）——使其能够在开放世界中处理复杂的人际关系。

然而，人类行为的空间是广阔而复杂的（[Riedl 2012]；[Yannakakis 2012]）。尽管大语言模型取得了瞩目的进展（[Brown et al. 2020]），能够在**单个时间点**上模拟人类行为（[Park et al. 2022]；[Hämäläinen et al. 2023]），但要保证长期连贯性，完全通用的智能体更适合采用这样的架构：随着新的交互、冲突和事件不断出现又随时间淡去，架构需要管理持续增长的记忆，同时处理多个智能体之间展开的级联式社会动力学。成功需要一种方法：能够在很长时间跨度上检索相关事件与交互，对这些记忆进行反思以做出泛化和更高层次的推断，并应用这些推理来生成规划与反应——这些规划与反应既在当下说得通，也符合智能体行为的长期弧线。

在本文中，我们提出**生成式智能体**——借助生成式模型来模拟可信人类行为的智能体——并证明它们能对个体行为和群体涌现行为都产生可信的拟像。生成式智能体会对自身、其他智能体和环境做出各种各样的推断；它们制定反映自身特征与经验的日常计划，执行这些计划，做出反应，并在合适的时候重新规划；当终端用户改变它们的环境或用自然语言下达指令时，它们会做出响应。例如，生成式智能体看到早餐烧糊了会去关掉炉子；如果卫生间有人占用，会在门外等候；遇到想交谈的另一个智能体时会停下来聊天。¹ 一个由生成式智能体构成的社会，其特征就是涌现的社会动力学：新的关系被建立，信息被扩散，智能体之间产生协调。

> ¹ 当我们说生成式智能体"执行某个动作"或"前往某个地点"时，这只是为了可读性而采用的简略说法，并不暗示它们具有类人的主体性（agency）。我们智能体的行为类似于迪士尼动画角色，旨在营造可信感，但并不意味真正的主体性。

为了实现生成式智能体，我们描述了一种智能体架构：它存储、合成并应用相关记忆，以借助大语言模型生成可信的行为。我们的架构包含三个主要组件。第一是**记忆流**（memory stream），一个长期记忆模块，以自然语言记录智能体经验的完整列表。记忆检索模型结合相关性、近因性与重要性，把为智能体当下行为提供信息所需的记录浮现出来。第二是**反思**，它随时间推移将记忆合成为更高层次的推断，使智能体能够对自身与他人得出结论，从而更好地指导自己的行为。第三是**规划**，它把这些结论与当前环境转化为高层行动计划，再递归地细化为用于行动与反应的具体行为。这些反思与规划会回馈到记忆流中，影响智能体未来的行为。

这一架构在多个领域都有应用前景，从角色扮演、社交原型设计到虚拟世界与游戏。在社交角色扮演场景中（例如面试准备），用户可以安全地演练艰难、充满冲突的对话。在原型设计社交平台时，设计师可以超越临时的用户画像（persona），去原型化那些随时间展开的、动态的复杂交互。在本文中，我们聚焦于创造一个受《模拟人生》启发的、小型的交互式智能体社会。² 通过将我们的架构连接到 ChatGPT 大语言模型（[OpenAI 2022]），我们在一个游戏环境中呈现出由 25 个智能体组成的社会。终端用户可以观察并与这些智能体互动。例如，如果终端用户或开发者希望小镇举办一场游戏内的情人节派对，传统游戏环境需要手工编写数十个角色的行为脚本；而我们证明，有了生成式智能体，只需要告诉其中一个智能体"她想办一场派对"就足够了。尽管存在许多潜在的失败点——办派对的人必须记得邀请其他智能体，被邀请的人必须记住邀请，记住的人还必须决定到底去不去，等等——我们的智能体还是成功了：它们把派对的消息传开，然后如约出现，其中一个智能体甚至还约另一个智能体一起去派对——而这一切，仅仅源于一条用户生成的种子建议。

> ² 生成式智能体社会的实际模拟演示可访问：https://reverie.herokuapp.com/UIST_Demo/。模拟代码的公开仓库位于：https://github.com/joonspk-research/generative_agents

我们对生成式智能体进行了两项评估：一项**受控评估**，测试智能体在隔离状态下是否能产生可信的个体行为；一项**端到端评估**，让智能体在两天的游戏时间内以开放式方式相互交互，以了解其稳定性与涌现的群体行为。在技术评估中，我们利用一个方法论上的机会：用自然语言"采访"智能体，来评估它的知识与行为，从而探测智能体保持人设、记忆、规划、反应和准确反思的能力。我们比较了若干消融条件——分别限制智能体对记忆、反思和规划的访问。我们观察到，这些组件中的每一个对这些访谈任务的良好表现都至关重要。在受控评估与端到端评估中，最常见的错误出现在：智能体未能检索到相关记忆、对记忆编造了添油加醋的细节、或从语言模型那里继承了过于正式的言谈或行为。

总结而言，本文做出以下贡献：

- **生成式智能体**——人类行为的可信拟像，动态地以智能体不断变化的经验与环境为条件。
- **一种新颖的架构**——使生成式智能体能够记忆、检索、反思、与其他智能体交互，并在动态演化的情境中进行规划。该架构利用大语言模型强大的提示能力，并对这些能力加以补充，以支持智能体更长期的连贯性、管理动态演化记忆的能力，以及递归地产生更高层次反思的能力。
- **两项评估**——一项受控评估和一项端到端评估，确立了架构各组件重要性的因果效应，并识别出例如记忆检索不当等导致的失效。
- **对生成式智能体在交互系统中机遇以及伦理与社会风险的讨论**。我们主张：应对这些智能体进行调优，以降低用户形成类社会关系（parasocial relationships）的风险；进行日志记录，以降低由深度伪造与定向劝说带来的风险；并以补充而非取代设计流程中人类利益相关者的方式加以应用。

---

## 2. 相关工作

在本节中，我们回顾人机交互领域的先前文献，并把"构建可信的人类行为代理"这一议程置于其经典脉络之中。这一议程曾被奉为交互、游戏与人工智能社区的北极星（[Laird and VanLent 2001]；[Riedl 2012]；[Riedl and Young 2005]；[Bates 1994]），但由于人类行为的复杂性（[Brooks et al. 2000]；[Yannakakis 2012]），它一直具有挑战性。我们综合这些研究提出：大语言模型尽管自身并不足够，但若能配合恰当的架构加以利用，就为创造可信的智能体开启了一个新角度。

### 2.1 人机交互

交互式人工智能系统旨在把人类的洞察与能力结合进计算制品中，以增强其使用者（[Amershi et al. 2014]；[Fails and Olsen Jr 2003]）。有一条长期的研究脉络探索如何让用户交互式地指定模型行为。例如，Crayons 展示了交互式机器学习的早期愿景，允许非专家用户训练分类器（[Fails and Olsen Jr 2003]）。后续工作进一步阐明了终端用户如何通过示例（[Fogarty et al. 2008]）或演示（[Fiebrink and Cook 2010]）向系统描述其分类目标。近期进展把这些探索扩展到了深度学习（[Lam et al. 2023]）与基于提示的创作（[Jiang et al. 2022]；[Wu et al. 2022b]；[Liu et al. 2022]）。

与此同时，另一条持续的研究脉络推进了人机交互中基于语言与智能体的交互。SHRDLU（[Winograd 1971]）与 ELIZA（[Weizenbaum 1966]）等奠基性工作展示了与计算系统进行自然语言交互的机遇与风险。随着研究推进，人们逐渐清楚地看到：自主智能体可以为委托与交互提供新的隐喻（[Maes 1995]），但人与智能体之间委托的边界一直是持续争论与精细化的主题（[Shneiderman and Maes 1997]；[Horvitz 1999]；[Shneiderman 2022]）。近来，这项技术已达到一定的稳定程度，使智能体能够在大型复杂的在线社交环境中通过自然语言进行交互（例如 [Krishna et al. 2022]）。自然语言交互提供了一种新颖的模态，可以增强用户在照片编辑（[Linder et al. 2013]；[Fourney et al. 2011]；[Adar et al. 2014]）和代码编辑（[Rong et al. 2016]）等领域的能力。

我们把这些研究脉络汇聚起来，表明我们现在已经可以创建能够为交互系统代理人类行为的智能体，并用自然语言与之交互。在此过程中，本工作重新打开了检视若干基础人机交互问题的大门：围绕 GOMS 与击键层模型（KLM）等认知模型的问题（[Card et al. 1983]；[Card et al. 1980]），围绕原型设计工具的问题（[Park et al. 2022]），以及围绕普适计算应用的问题（[Weiser 1991]；[Dey 2001]；[Fast et al. 2016]）。

### 2.2 可信的人类行为代理

先前文献把"可信性"或"可信的智能体"描述为核心的设计与工程目标。可信的智能体旨在提供一种"有生命"的幻象，并在其看似自主决策与行动的方式上呈现出现实感的外观，类似于迪士尼电影中的角色（[Bates 1994]；[Thomas and Johnston 1981]）。这些智能体可以栖息并感知一个像我们所居住的那样的开放世界环境（[Laird and VanLent 2001]；[Bates 1994]），并努力以这样的方式行动：展现出根植于与用户或其他智能体社交互动的涌现行为，从而在个体与社区的假想模拟中成为我们行为的可信代理（[McCoy et al. 2012]；[Burkinshaw 2009]；[Francis 2010]）。历史上，这些智能体是在智能游戏非玩家角色（NPC）的语境下开发的（[Laird and VanLent 2001]；[Riedl 2012]）。若能创造具有可信行为的 NPC，则可以通过实现涌现叙事（[Swartout et al. 2006]；[Aylett 1999]；[Brenner 2010]；[Ibister and Nass 2000]）以及与智能体的社交互动（[Zubek 2002]），提升玩家在游戏与交互式小说中的体验。然而更重要的是：游戏世界提供了对现实世界可供性（affordances）日益逼真的表征，正如 Laird 与 van Lent 在 2001 年所观察到的，这些模拟世界为可信智能体的开发者提供了易得的试验台，使他们可以打磨智能体的认知能力，而不必担心在现实世界中实现机器人技术或从头创建模拟环境（[Laird and VanLent 2001]；[Riedl 2012]）。

过去四十年间涌现出多种创造可信智能体的方法。但在实现上，这些方法往往简化了环境或智能体行为的维度，以使工作量可控（[Brooks et al. 2000]；[Minsky and Papert 1970]）。基于规则的方法，如有限状态机（[Siu et al. 2021]；[Umarov et al. 2012]）与行为树（[Knafla 2011]；[Pillosu 2009]；[Hecker 2011]），代表了人工编写智能体行为的"蛮力"方式（[McCoy et al. 2012]）。它们提供了一种创建简单智能体的直接方式，至今仍是最主流的方法（[McCoy et al. 2009]；[Miyashita et al. 2017]；[Yannakakis 2012]），甚至可以处理初级的社交互动，如《质量效应》（[BioWare 2007]）与《模拟人生》（[Arts 2009]）系列游戏所示。尽管如此，手工编写能够全面覆盖开放世界中可能交互范围的行为是行不通的。这意味着最终的智能体行为可能无法完整表征其交互的后果（[McCoy et al. 2012]；[McCoy et al. 2011a]；[McCoy et al. 2011b]），也无法执行那些未被硬编码进脚本的新流程（[Siu et al. 2021]；[Umarov et al. 2012]）。另一方面，当前流行的基于学习的可信智能体创建方法（如强化学习）通过让智能体自己学习行为，克服了手工编写的难题，并在近年《星际争霸》的 AlphaStar（[Vinyals et al. 2019]）与 Dota 2 的 OpenAI Five（[Berner et al. 2019]）等游戏中取得了超人类表现。然而，它们的成功主要发生在具有易于定义的奖励、可供学习算法优化的对抗性游戏中，尚未解决在开放世界中创造可信智能体的挑战（[Siu et al. 2021]；[Miyashita et al. 2017]；[Hausknecht et al. 2020]）。

由 Newell 开创的计算认知架构，旨在构建支持一整套认知功能的基础设施（[Newell 1990]），以适应可信智能体最初愿景中的那种包罗万象的性质。它们催生了一些最早的可信智能体实例。例如，Quakebot-SOAR（[Laird 2000]）与 ICARUS（[Langley et al. 2005]；[Choi et al. 2021]）在第一人称射击游戏中生成 NPC，而 TacAir-SOAR（[Pew and Mavor 1998]）在空战训练模拟中生成飞行员。这些智能体使用的架构各不相同（Quakebot- 与 TacAir-SOAR 依赖 SOAR [Laird 2012]，而 ICARUS 依赖其受 SOAR 与 ACT-R [Anderson 1993] 启发的自有变体），但它们共享相同的底层原则（[Laird et al. 2017]）：它们维护短期与长期记忆，用符号结构填充这些记忆，并在"感知—规划—行动"（perceive-plan-act）的循环中运作，动态地感知环境并将其与某个手工编写的行动程序相匹配（[Umarov et al. 2012]；[Laird 2001]）。用认知架构创建的智能体力求泛化到大多数（如果不是全部）开放世界情境，并在其时代表现出稳健的行为。然而，它们的行动空间局限于手工编写的程序性知识，并且没有提供让智能体受到启发去寻求新行为的机制。因此，这些智能体主要部署在非开放世界的情境中，如第一人称射击游戏（[Laird 2000]；[Choi et al. 2021]）或积木世界（[Laird 2001]；[Langley et al. 2005]）。

今天，按其原始定义创造可信智能体仍是一个开放问题（[Yannakakis 2012]；[Riedl 2012]）。许多人已经转向别处，认为尽管当前创造可信智能体的方法可能笨拙且有限，但已经足以支撑现有的玩法与交互（[Yannakakis 2012]；[Champandard 2012]；[Nareyek 2007]）。我们的论点是：大语言模型提供了一个重新审视这些问题的机会——前提是我们能够设计出一种有效的架构，把记忆合成为可信的行为。本文正是朝着这样一种架构迈出的一步。

### 2.3 大语言模型与人类行为

生成式智能体借助大语言模型来驱动其行为。关键的观察是：大语言模型从其训练数据中编码了广泛的人类行为（[Brown et al. 2020]；[Bommasani et al. 2022]）。如果给定 narrowly defined（ narrowly 界定的）上下文进行提示，这些模型可以被用来生成可信的行为。近期工作证明了这一方法的有效性。例如，社会拟像（social simulacra）使用大语言模型生成用户，用以填充新的社交计算系统，从而对其涌现的社会动力学进行原型设计（[Park et al. 2022]）。该方法使用提示链（[Wu et al. 2022a]；[Wu et al. 2022b]）生成人物画像（persona）及其在系统中行为的简短自然语言描述。其他实证研究复现了现有的社会科学研究（[Horton 2023]）、政治调查（[Sorensen et al. 2022]），并生成了合成数据（[Hämäläinen et al. 2023]）。大语言模型也被用于生成供用户参与的交互式人类行为。例如在游戏中，这些模型已被用于创建交互式小说（[Freiknecht and Effelsberg 2020]）与文字冒险游戏（[Callison-Burch et al. 2022]）。凭借生成与分解动作序列的能力，大语言模型还被用于规划机器人任务（[Huang et al. 2022]）：例如，当给定"拿起一个瓶子"这样的任务时，通过提示让模型把任务分解为更小的动作序列，如走到瓶子所在的桌子前，然后把它拿起来。

我们认为，基于上述工作，大语言模型可以成为创造可信智能体的关键要素。现有文献主要依赖所谓的一阶模板（first-order templates），采用少样本提示（[Gao et al. 2020]；[Liu et al. 2021]）或思维链提示（[Wei et al. 2023]）。这些模板在生成仅以智能体当前环境为条件的行为时是有效的（例如：一个喷子会如何回应某条帖子；在有一扇门的前提下机器人进入房间需要采取哪些动作）。然而，可信的智能体不仅需要以当前环境为条件，还需要以大量的过往经验为条件——这对于一阶提示来说是非常不匹配的（而且由于底层模型有限的上下文窗口，在今天就根本不可能）。近期研究试图超越一阶提示，用静态知识库和信息检索方案（[Khattab et al. 2023]）或简单的摘要方案（[Wu et al. 2021]）来增强语言模型。本文扩展了这些想法，设计出一种智能体架构，其中的检索机制在**每个时间步**动态更新过往经验，并与智能体当前的上下文和规划相混合——而这些信息之间可能相互强化，也可能相互矛盾。

---

## 3. 生成式智能体的行为与交互

为了说明生成式智能体的可供性（affordances），我们把它们实例化为一个让人想起《模拟人生》（[Arts 2009]）的简单沙盒世界中的角色。这个基于精灵图（sprite）的沙盒游戏世界叫作 Smallville，唤起了一个小镇环境。在本节中，我们将走查 Smallville 中生成式智能体的可供性与交互方式，并描述智能体在其中的行为。然后，在第 4 节中，我们将介绍支撑这些可供性与交互的生成式智能体架构；在第 5 节中，我们将描述沙盒环境的实现，以及智能体如何与沙盒世界的底层引擎交互。

### 3.1 智能体化身与沟通

Smallville 中居住着一个由 25 个独特智能体组成的社区。每个智能体由一个简单的精灵化身（avatar）表示。我们为每个智能体撰写了一段自然语言描述，描绘其身份，包括职业以及与其他智能体的关系，作为**种子记忆**。例如，John Lin 的描述如下：

> John Lin is a pharmacy shopkeeper at the Willow Market and Pharmacy who loves to help people. He is always looking for ways to make the process of getting medication easier for his customers; John Lin is living with his wife, Mei Lin, who is a college professor, and son, Eddy Lin, who is a student studying music theory; John Lin loves his family very much; John Lin has known the old couple next-door, Sam Moore and Jennifer Moore, for a few years; John Lin thinks Sam Moore is a kind and nice man; John Lin knows his neighbor, Yuriko Yamamoto, well; John Lin knows of his neighbors, Tamara Taylor and Carmen Ortiz, but has not met them before; John Lin and Tom Moreno are colleagues at The Willows Market and Pharmacy; John Lin and Tom Moreno are friends and like to discuss local politics together; John Lin knows the Moreno family somewhat well — the husband Tom Moreno and the wife Jane Moreno.
>
> （译：John Lin 是 Willow Market and Pharmacy 的药店店主，乐于助人。他总是在想办法让顾客买药的流程更轻松；John Lin 与妻子——大学教授 Mei Lin——以及儿子——学习音乐理论的学生 Eddy Lin——同住；John Lin 非常爱他的家人；John Lin 认识隔壁的老夫妇 Sam Moore 和 Jennifer Moore 已有几年；John Lin 认为 Sam Moore 是个善良的好人；John Lin 与邻居 Yuriko Yamamoto 很熟；John Lin 知道他的邻居 Tamara Taylor 和 Carmen Ortiz，但此前从未见过面；John Lin 和 Tom Moreno 是 The Willows Market and Pharmacy 的同事；John Lin 和 Tom Moreno 是朋友，喜欢一起讨论本地政治；John Lin 对 Moreno 一家有些了解——丈夫 Tom Moreno 和妻子 Jane Moreno。）

每个以分号分隔的短语，都会作为记忆在模拟开始时被输入到智能体的初始记忆中。

#### 3.1.1 智能体之间的沟通

智能体通过自己的行动与世界交互，并通过自然语言彼此交互。在沙盒引擎的每个时间步，智能体输出一句描述其当前行动的自然语言陈述，例如"Isabella Rodriguez 正在写日记"、"Isabella Rodriguez 正在查看电子邮件"、"Isabella Rodriguez 正在和家人通电话"或"Isabella Rodriguez 正准备睡觉"。该陈述随后被转换为影响沙盒世界的具体动作。该动作在沙盒界面上以一组 emoji 显示，从俯视角度提供对动作的抽象表征。为实现这一点，系统利用语言模型把该动作翻译成一组 emoji，这些 emoji 显示在每个化身头顶的气泡中。例如，"Isabella Rodriguez 正在写日记"显示为 📖✏️，而"Isabella Rodriguez 正在查看电子邮件"显示为 💻✉️。动作的完整自然语言描述可以通过点击智能体的化身来查看。

智能体之间使用完整的自然语言交流。它们能感知到自己所在区域内的其他智能体，由生成式智能体架构决定它们是擦肩而过还是展开对话。以下是 Isabella Rodriguez 与 Tom Moreno 之间关于即将到来的选举的对话中间片段：³

> Isabella: I'm still weighing my options, but I've been discussing the election with Sam Moore. What are your thoughts on him?
> Tom: To be honest, I don't like Sam Moore. I think he's out of touch with the community and doesn't have our best interests at heart.
>
> （译：Isabella：我还在权衡，不过我一直在和 Sam Moore 讨论这次选举。你对他怎么看？Tom：老实说，我不喜欢 Sam Moore。我觉得他和社区脱节，并没有把我们的最大利益放在心上。）

> ³ 我们注意到，这些智能体的对话风格可能让人感觉过于正式，这很可能是底层模型指令微调的结果。我们预计未来的语言模型将能更好地控制写作风格。

#### 3.1.2 用户控制

用户通过自然语言与智能体沟通，具体方式是指定一个智能体应当把用户视作何种角色（persona）。例如，如果用户指定自己是一名新闻"记者"，并询问即将到来的选举："Who is running for office?"（谁在竞选？），John 智能体会回答：

> John: My friends Yuriko, Tom and I have been talking about the upcoming election and discussing the candidate Sam Moore. We have all agreed to vote for him because we like his platform.
>
> （译：John：我和我的朋友 Yuriko、Tom 一直在聊即将到来的选举，讨论候选人 Sam Moore。我们都同意投给他，因为我们喜欢他的政纲。）

要直接命令某个智能体，用户可以扮演该智能体的"内在声音"（inner voice）——这会让智能体更可能把这句话当作指令。例如，当用户以 John 的内在声音说"You are going to run against Sam in the upcoming election"（你将在即将到来的选举中与 Sam 竞争）时，John 决定参选，并与妻子和儿子分享了他参选的消息。

### 3.2 环境交互

Smallville 具备一个小村庄的常见场所，包括咖啡馆、酒吧、公园、学校、宿舍、住宅和商店。它还定义了让这些空间具备功能的子区域与物件，例如房子里的厨房、厨房里的炉子（图 2）。所有作为智能体主要居住空间的地方都配有床、书桌、衣柜、架子，以及浴室和厨房。⁴

> ⁴ 这个环境设计并非我们工作的重点，因此我们手动生成了这个环境，而非自动生成。未来的工作可以继续扩展智能体环境的丰富度。

智能体在 Smallville 中移动，就像在简单的电子游戏中一样：进出建筑、在地图上导航、靠近其他智能体。智能体的移动由生成式智能体架构与沙盒游戏引擎共同指挥：当模型指示智能体要移动到某个地点时，我们在 Smallville 环境中计算到目的地的步行路径，然后智能体开始移动。此外，用户也可以作为一个在其中运作的智能体进入 Smallville 的沙盒世界。用户所扮演的智能体可以是世界中已有的智能体（如 Isabella 和 John），也可以是一个在 Smallville 没有任何历史过往的外部访客。Smallville 的居民对待用户控制的智能体，与对待彼此没有区别：它们会识别其存在、发起交互、记住其行为，然后才形成对它的看法。

用户和智能体都可以影响这个世界中物体的状态，就像在《模拟人生》这类沙盒游戏中一样。例如，智能体睡觉时床可以被占用；智能体用完食材做早餐后，冰箱可以是空的。终端用户还可以通过用自然语言改写智能体周围物体的状态，来重塑智能体在 Smallville 中的环境。例如，当 Isabella 早上正在做早餐时，用户可以通过向系统输入一条选择该物体并说明其新状态的指令，把厨房炉子的状态从"开着"改成"烧起来了"，例如："<Isabella's apartment: kitchen: stove> is burning."（Isabella 的公寓：厨房：炉子 正在燃烧）。Isabella 在下一刻就会注意到这一点，并去关掉炉子、重做早餐。同样地，如果用户在 Isabella 进入浴室时把她的淋浴器状态设为"正在漏水"，她会从客厅收集工具并尝试修理漏水。

### 3.3 示例："一天的生活"

从单段描述出发，生成式智能体开始规划它们的一天。随着沙盒世界中时间的流逝，它们的行为随着彼此及世界的交互而演化，积累记忆与关系，并协调联合活动。

我们通过追踪系统输出在一天之中对智能体 John Lin 的呈现，来展示生成式智能体的行为（图 3）。在 Lin 一家中，John 是早上 7 点第一个起床的人。他刷牙、洗澡、穿衣服、吃早餐，并在客厅的餐桌上查看新闻。8 点，Eddy 紧随其后，从床上冲起来准备上课。他在 John 正要出门时赶上了他：

> John: Good morning Eddy. Did you sleep well?
> Eddy: Good morning dad. Yeah, I slept great.
> John: That's good. What are you working on today?
> Eddy: I'm working on a new music composition for my class. It's due this week, so I'm trying to get it finished. But I'm having so much fun with it!
> John: That sounds great!
>
> （译：John：早上好 Eddy。睡得好吗？Eddy：早上好爸爸。嗯，睡得很好。John：那就好。你今天准备做什么？Eddy：我在为课上一首新的音乐作曲。这周要交，所以我正努力把它完成。但我做得很开心！John：听起来不错！）

Eddy 出门后不久，Mei 醒来并与 John 在一起。Mei 问起儿子，John 回忆起他们刚才的对话：

> Mei: Did Eddy already leave for school?
> John: Yes, he just left. He's working on a music composition for his class.
> Mei: Oh, that's wonderful! Tell me about it.
> John: I think he's really enjoying it! He said he's having a lot of fun with it.
> Mei: That's great! I'm so proud of him.
>
> （译：Mei：Eddy 已经去上学了吗？John：是的，他刚走。他在为课上一首音乐作曲而努力。Mei：哦，太棒了！跟我说说。John：我觉得他真的很享受！他说他做得很开心。Mei：太好了！我真为他骄傲。）

当他们结束对话时，Mei 和 John 收拾妥当。Mei 去教书并做她的研究论文，而 John 在 9 点前打开了他在 Willow Market and Pharmacy 的药房柜台。

### 3.4 涌现的群体行为

通过彼此交互，Smallville 中的生成式智能体交换信息、形成新的关系、协调联合活动。扩展先前的工作（[Park et al. 2022]），这些群体行为是**涌现的**，而非预先编程的。

#### 3.4.1 信息扩散

当智能体注意到彼此时，它们可能会展开对话——在这个过程中，信息可以从一个智能体传播到另一个智能体。例如，在杂货店 Sam 与 Tom 的对话中，Sam 告诉 Tom 他要参选地方选举：

> Sam: Hey Tom, how's it going?
> Tom: Good, thanks. What's up?
> Sam: Well, I wanted to talk to you about something. I'm actually running for mayor in the upcoming local election.
> Tom: Really? That's great news! Why are you running?
> Sam: I've been involved in local politics for years now, and I really feel like I can make a difference in our community. Plus, I want to bring new ideas and perspectives to the table.
>
> （译：Sam：嘿 Tom，最近怎么样？Tom：很好，谢谢。有什么事吗？Sam：嗯，我想跟你聊点事。我实际上要参选即将到来的地方选举的市长。Tom：真的吗？这是个好消息！你为什么参选？Sam：我参与本地政治已经很多年了，我真的觉得我可以为我们的社区带来改变。另外，我想带来新的想法和视角。）

当天晚些时候，Sam 离开后，Tom 与从其他渠道听到这个消息的 John 讨论 Sam 的胜算：

> John: I heard that Sam Moore is running for mayor in the local election. Do you think he has a good chance of winning?
> Tom: I do think he has a good chance. He's been working hard in the community and I think he will get a lot of support. What do you think?
> John: I think it's great that he's running. I'm curious to see how the election will turn out.
>
> （译：John：我听说 Sam Moore 要参选地方选举的市长。你觉得他胜算大吗？Tom：我确实觉得他机会很大。他一直在社区里努力做事，我认为他会得到很多支持。你怎么看？John：我觉得他参选很好。我很好奇选举会怎么发展。）

渐渐地，Sam 的参选成了全镇的话题，有人支持他，也有人仍持观望态度。

#### 3.4.2 关系记忆

Smallville 中的智能体随时间形成新的关系，并记住它们与其他智能体的交互。例如，一开始 Sam 并不认识 Latoya Williams。在 Johnson Park 散步时，Sam 偶遇 Latoya，他们互相自我介绍。Latoya 提到她正在做一个摄影项目："I'm here to take some photos for a project I'm working on."（我来这里是为我正在做的一个项目拍些照片。）在后来的交互中，Sam 与 Latoya 的互动表明他记得那次交互：他问"Hi, Latoya. How is your project going?"（嗨，Latoya。你的项目进展如何？），她回答"Hi, Sam. It's going well!"（嗨，Sam。进展很顺利！）

#### 3.4.3 协调

生成式智能体会相互协调。Isabella Rodriguez 在 Hobbs Cafe，她在初始化时被赋予一个意图：策划一场 2 月 14 日下午 5 点到 7 点的情人节派对。从这颗种子出发，当她在 Hobbs Cafe 或其他地方见到朋友和顾客时，她就会去邀请他们。随后 Isabella 用 13 号下午的时间为这个场合装饰咖啡馆。Maria 是咖啡馆的常客，也是 Isabella 的密友，她来到咖啡馆，Isabella 请 Maria 帮忙装饰派对，Maria 答应了。Maria 的角色描述提到她暗恋 Klaus。那天晚上，Maria 邀请她的暗恋对象 Klaus 一起去派对，他欣然接受。

情人节那天，包括 Klaus 和 Maria 在内的五名智能体在下午 5 点出现在 Hobbs Cafe，享受着庆祝活动（图 4）。在这个场景中，终端用户只设置了 Isabella 办派对的初始意图，以及 Maria 暗恋 Klaus 这一点：传播消息、装饰、互相邀约、到场参加派对、在派对上相互交谈——这些群体行为都是由智能体架构自行发起的。

---

## 4. 生成式智能体架构

生成式智能体旨在为开放世界中的行为提供一个框架：既能与其他智能体交互，又能对环境变化做出反应。生成式智能体以当前环境和过往经验为输入，以行为为输出。支撑这一行为的是一种新颖的智能体架构，它把大语言模型与"合成并检索相关信息以调节语言模型输出"的机制结合起来。如果没有这些机制，大语言模型当然也能输出行为，但由此产生的智能体可能无法基于自身过往经验做出反应、可能无法做出重要推断、也可能无法维持长期连贯性。长期规划与连贯性的挑战至今依然存在（[Bubeck et al. 2023]），即便是在当今最强的模型（如 GPT-4）上也是如此。由于生成式智能体会产生大量必须留存下来的事件流和记忆，我们架构的一个核心挑战是：**确保在需要时，智能体记忆中最相关的片段能够被检索与合成出来。**

我们架构的核心是**记忆流**（memory stream）——一个维护智能体经验完整记录的数据库。从记忆流中检索出相关的记录，用以规划智能体的行动并对环境做出恰当反应。记录会被递归地合成为越来越高层次的**反思**，进而指导行为。架构中的一切都以自然语言描述的形式被记录和推理，从而使架构能够充分利用大语言模型。

我们当前的实现使用 ChatGPT 的 gpt3.5-turbo 版本（[OpenAI 2022]）。我们预计，随着语言模型的进步，生成式智能体的架构基础——记忆、规划与反思——很可能保持不变。更新的语言模型（如 GPT-4）将继续拓展支撑生成式智能体的提示语的表达能力与性能。不过在撰写本文时，GPT-4 的 API 仅对受邀者开放，因此我们的智能体使用 ChatGPT。

> 图 6：记忆流包含大量与智能体当前情境相关与不相关的观察。检索会识别出其中应被传递给语言模型、以调节其对情境响应的一个子集。左侧是一大串事件，如"冰箱处于空闲状态"；右侧是问题"What are you looking forward to the most right now?"（你现在最期待什么？），随后是检索计算——它给"为派对订购装饰品"和"研究派对创意"打出高分。基于这些记忆，Isabella 回答道："I'm looking forward to the Valentine's Day party that I'm planning at Hobbs Cafe!"（我期待我正在 Hobbs Cafe 策划的情人节派对！）

### 4.1 记忆与检索

**挑战**：创造能够模拟人类行为的生成式智能体，需要推理一组规模远超提示词所能容纳的经验——因为完整的记忆流会分散模型的注意力，而且目前根本无法装进有限的上下文窗口。设想 Isabella 智能体回答"What are you passionate about these days?"（你最近对什么充满热情？）这个问题。若把 Isabella 的全部经验压缩摘要塞进语言模型有限的上下文窗口，得到的是一个信息量很低的回答：Isabella 会谈论诸如活动与项目的合作、咖啡馆的清洁与整理之类的话题。相反，下文所述的记忆流会浮现出相关记忆，从而得到信息量更高、更具体的回答——提到 Isabella 的热情在于让人们感到受欢迎和被接纳，策划活动并营造让人享受的氛围，例如情人节派对。

**方法**：记忆流维护智能体经验的完整记录。它是一个**记忆对象**的列表，每个对象包含一段自然语言描述、一个创建时间戳，以及一个最近访问时间戳。记忆流中最基本的元素是**观察**（observation），即智能体直接感知到的事件。常见的观察包括智能体自身执行的行为，或智能体感知到其他智能体或非智能体对象所执行的行为。例如，在咖啡店工作的 Isabella Rodriguez 可能随时间积累如下观察：(1) Isabella Rodriguez 正在摆放糕点；(2) Maria Lopez 一边喝咖啡一边复习化学考试；(3) Isabella Rodriguez 与 Maria Lopez 正在讨论在 Hobbs Cafe 策划情人节派对；(4) 冰箱是空的。

我们的架构实现了一个检索函数：以智能体当前情境为输入，返回记忆流的一个子集，传递给语言模型。检索函数有许多可能的实现，取决于智能体在决定如何行动时应当考虑什么。在我们的语境下，我们关注三个主要组件，它们共同产生了有效的效果。

**近因性**（Recency）给最近被访问过的记忆对象打更高的分，使得片刻之前或今天早晨发生的事件更可能留在智能体的注意范围（attentional sphere）之内。在我们的实现中，我们把近因性建模为关于"距该记忆上次被检索以来经过的沙盒游戏小时数"的指数衰减函数，衰减因子为 0.995。

**重要性**（Importance）通过给智能体认为重要的记忆对象打更高的分，区分平淡的记忆与核心记忆。例如，像"在自己房间里吃早餐"这样的寻常事件会得到较低的重要性分数，而"与恋人分手"则会得到高分。重要性分数有许多可能的实现方式；我们发现，直接让语言模型输出一个整数分数是有效的。完整的提示语如下：

> On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.
> Memory: buying groceries at The Willows Market and Pharmacy
> Rating: <fill in>
>
> （译：在 1 到 10 的量表上——1 表示纯属日常琐事（例如刷牙、整理床铺），10 表示极其深刻（例如分手、大学录取）——请评价下面这段记忆可能的深刻程度。记忆：在 The Willows Market and Pharmacy 买杂货。评分：<填写>）

这个提示对"打扫房间"返回整数 2，对"约暗恋对象出去约会"返回 8。重要性分数是在记忆对象创建时生成的。

**相关性**（Relevance）给与当前情境相关的记忆对象打更高的分。什么是相关的，取决于"与什么相关"这一问题的答案，因此我们把相关性以某个查询记忆（query memory）为条件。例如，如果查询是"一名学生正在与同学讨论化学考试该复习什么"，那么关于他们早餐的记忆对象应当具有较低的相关性，而关于老师和学业的记忆对象应当具有较高的相关性。在我们的实现中，我们使用语言模型为每条记忆的文本描述生成嵌入向量；然后，我们把相关性计算为该记忆的嵌入向量与查询记忆的嵌入向量之间的余弦相似度。

为了计算最终的检索分数，我们使用 min-max 缩放（最小值—最大值归一化）把近因性、相关性和重要性分数归一化到 [0, 1] 区间。检索函数把所有记忆的分数计算为这三个元素的加权组合：

score = α_recency · recency + α_importance · importance + α_relevance · relevance

在我们的实现中，所有 α 都设为 1。排名最高、且能够装进语言模型上下文窗口的记忆，会被纳入提示词。

### 4.2 反思

> 图 7：Klaus Mueller 的反思树。智能体对世界的观察（以叶节点表示）被递归地合成，推导出 Klaus 的自我认知——他极度投入于自己的研究。

**挑战**：仅配备原始观察记忆的生成式智能体，难以做出泛化或推断。设想这样一个场景：用户问 Klaus Mueller——"If you had to choose one person of those you know to spend an hour with, who would it be?"（如果在你认识的人里必须选一个共度一小时，你会选谁？）在只能访问观察记忆的情况下，智能体只会选择与 Klaus 交互最频繁的人：他的大学宿舍邻居 Wolfgang。不幸的是，Wolfgang 和 Klaus 只是偶尔碰面，并没有深入的交流。更理想的回答要求智能体从"Klaus 花了数小时做研究项目"的记忆中泛化，生成一个更高层次的反思——Klaus 对研究充满热情；同样地，识别出 Maria 也为自己的研究付出努力（尽管在不同领域），从而得出"他们有共同兴趣"这一反思。采用下述方法后，当 Klaus 被问到该与谁共度时光时，他选择的是 Maria 而不是 Wolfgang。

**方法**：我们引入第二种记忆类型，称为**反思**（reflection）。反思是智能体生成的更高层次、更抽象的想法。由于它们也是一种记忆，在检索时会与其他观察一起被纳入考虑。反思是周期性生成的；在我们的实现中，当智能体感知到的最新事件的重要性分数之和超过一个阈值（我们实现中为 150）时，就会生成反思。在实践中，我们的智能体大约每天反思两到三次。

反思的第一步是让智能体决定"反思什么"——即根据智能体近期的经验，提出可以被回答的问题。我们用智能体记忆流中最近的 100 条记录（例如"Klaus Mueller 正在读一本关于士绅化的书"、"Klaus Mueller 正在与图书管理员讨论他的研究项目"、"图书馆的书桌目前无人使用"）来查询大语言模型，并提示模型："Given only the information above, what are 3 most salient high-level questions we can answer about the subjects in the statements?"（仅根据上述信息，关于这些陈述中的主体，我们能回答的 3 个最显著的高层问题是什么？）模型的回应生成了候选问题，例如：What topic is Klaus Mueller passionate about?（Klaus Mueller 对什么话题充满热情？）以及 What is the relationship between Klaus Mueller and Maria Lopez?（Klaus Mueller 与 Maria Lopez 之间是什么关系？）我们把这些生成的问题用作检索的查询，为每个问题收集相关记忆（包括其他反思）。然后我们提示语言模型提取洞见，并引用作为这些洞见证据的特定记录。完整提示如下：

> Statements about Klaus Mueller
> 1. Klaus Mueller is writing a research paper
> 2. Klaus Mueller enjoys reading a book on gentrification
> 3. Klaus Mueller is conversing with Ayesha Khan about exercising [...]
> What 5 high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))
>
> （译：关于 Klaus Mueller 的陈述：1. Klaus Mueller 正在写一篇研究论文；2. Klaus Mueller 喜欢读一本关于士绅化的书；3. Klaus Mueller 正在与 Ayesha Khan 谈论锻炼……你能从上述陈述中推断出哪 5 条高层洞见？（示例格式：洞见（因为 1、5、3）））

这一过程会生成类似"Klaus Mueller is dedicated to his research on gentrification (because of 1, 2, 8, 15)"（Klaus Mueller 致力于他关于士绅化的研究（因为 1、2、8、15））这样的陈述。我们对该陈述进行解析，把它作为一条反思存入记忆流，同时保存指向被引用的那些记忆对象的指针。

反思明确地允许智能体不仅对观察进行反思，也对**其他反思**进行反思：例如，上面关于 Klaus Mueller 的第二条陈述就是 Klaus 此前产生过的一条反思，而不是来自其环境的观察。因此，智能体会生成**反思树**：树的叶节点代表基础观察，非叶节点代表那些越往树上走就越抽象、越高层的想法。

### 4.3 规划与反应

**挑战**：虽然大语言模型能够响应情境信息生成貌似合理的行为（例如 [Park et al. 2022]；[Horton 2023]），但智能体需要在更长的时间跨度上进行规划，以确保其动作序列是连贯且可信的。如果我们用 Klaus 的背景提示语言模型、描述当前时间，然后问他在给定时刻应该采取什么行动，Klaus 会在中午 12 点吃午餐，然后在 12:30 又吃一次，1 点再吃一次——尽管他已经吃过两顿午餐了。为当下时刻的可信性做优化，会牺牲时间维度上的可信性。为克服这一问题，规划是必不可少的。采用下述方法后，Klaus 的下午计划就不那么贪吃了：他中午 12 点在 Hobbs Cafe 边读书边吃午餐，下午 1 点在学校图书馆写研究论文，下午 3 点休息一下去公园散步。

**方法**：**规划**（plans）描述智能体未来的动作序列，并帮助智能体的行为随时间保持一致。一条规划包含地点、起始时间和持续时间。例如，专心于研究且面临迫近截止期限的 Klaus Mueller⁵，可能会选择整天在书桌前起草他的研究论文。规划中的一条条目可能会这样写：for 180 minutes from 9am, February 12th, 2023, at Oak Hill College Dorm: Klaus Mueller's room: desk, read and take notes for research paper（自 2023 年 2 月 12 日上午 9 点起 180 分钟，在 Oak Hill College Dorm: Klaus Mueller 的房间: 书桌，为研究论文阅读并做笔记）。与反思一样，规划也被存放在记忆流中，并参与检索过程。这使得智能体在决定如何行动时，能够同时考虑观察、反思和规划。如有需要，智能体也可以在过程中改变自己的计划。

> ⁵ 顺便说一句，在这一点上他至少与本文作者有几分相似。

对于一个画家智能体来说，如果在药房柜台后面坐着不动地计划画画四个小时，那既不现实也无趣。更理想的计划应该是：智能体在这四小时里，花必要的时间去收集材料、调颜料、休息，并在其家庭工作室中进行清理。为了创建这样的规划，我们的方法**自顶向下**开始，然后递归地生成更多细节。第一步是创建一个勾勒当天日程大纲的计划。为了创建初始规划，我们用智能体的摘要描述（例如姓名、特质，以及对其近期经验的概括）和对其前一天的概括来提示语言模型。下面是一个完整的示例提示，其底部是未完成的，留给语言模型去补全：

> Name: Eddy Lin (age: 19)
> Innate traits: friendly, outgoing, hospitable
> Eddy Lin is a student at Oak Hill College studying music theory and composition. He loves to explore different musical styles and is always looking for ways to expand his knowledge. Eddy Lin is working on a composition project for his college class. He is taking classes to learn more about music theory. Eddy Lin is excited about the new composition he is working on but he wants to dedicate more hours in the day to work on it in the coming days
> On Tuesday February 12, Eddy 1) woke up and completed the morning routine at 7:00 am, [...] 6) got ready to sleep around 10 pm.
> Today is Wednesday February 13. Here is Eddy's plan today in broad strokes: 1)
>
> （译：姓名：Eddy Lin（年龄：19）；固有特质：友善、外向、好客。Eddy Lin 是 Oak Hill College 的学生，学习音乐理论与作曲。他喜欢探索不同的音乐风格，总是在寻找拓展知识的途径。Eddy Lin 正在为大学课程做一个作曲项目。他正在上课以学习更多音乐理论。Eddy Lin 对他正在创作的新曲子感到兴奋，但他希望接下来几天能每天投入更多时间去做它。2 月 12 日星期二，Eddy 1）早上 7:00 起床并完成晨间例行事务，［……］6）晚上 10 点左右准备睡觉。今天是 2 月 13 日星期三。以下是 Eddy 今天计划的粗线条：1））

这会生成智能体一天计划的粗略草图，分为五到八个块："1）早上 8:00 起床并完成晨间例行事务，2）10:00 开始去 Oak Hill College 上课，［……］5）下午 1:00 到 5:00 创作他的新音乐作品，6）5:30 吃晚餐，7）完成学校作业并在 11:00 前上床睡觉。"

智能体把该计划存入记忆流，然后**递归地分解**它，以创建更细粒度的动作：先分解为以小时为单位的动作块——Eddy "下午 1:00 到 5:00 创作新音乐作品"的计划变成"下午 1:00：先为他的音乐作品头脑风暴一些想法［……］下午 4:00：在回顾和打磨作品之前，快速休息一下，补充创作能量"。然后我们再递归地把它分解为 5–15 分钟的块：例如，"下午 4:00：拿点小零食，比如一片水果、一根谷物棒或一些坚果。下午 4:05：在工作空间附近散一小会儿步［……］下午 4:50：花几分钟清理工作空间"。这个过程可以按需调整粒度。

#### 4.3.1 反应与更新规划

生成式智能体在一个动作循环中运行：在每个时间步，它们感知周围的世界，这些被感知到的观察被存入其记忆流。我们用这些观察提示语言模型，以决定智能体应当继续执行现有计划，还是做出反应。例如，站在画架前作画可能触发对画架的观察，但这不太可能引发反应。然而，如果 Eddy 的父亲 John 记录下他看到 Eddy 在房子的花园里散步，结果就不同了。提示如下，其中 [Agent's Summary Description] 代表对智能体总体目标与性情动态生成的一段话长度摘要（详见附录 A）：

> [Agent's Summary Description]
> It is February 13, 2023, 4:56 pm.
> John Lin's status: John is back home early from work.
> Observation: John saw Eddy taking a short walk around his workplace.
> Summary of relevant context from John's memory: Eddy Lin is John's Lin's son. Eddy Lin has been working on a music composition for his class. Eddy Lin likes to walk around the garden when he is thinking about or listening to music.
> Should John react to the observation, and if so, what would be an appropriate reaction?
>
> （译：［智能体摘要描述］现在是 2023 年 2 月 13 日下午 4:56。John Lin 的状态：John 提前下班回家了。观察：John 看到 Eddy 在他的工作场所附近散步。来自 John 记忆的相关上下文摘要：Eddy Lin 是 John Lin 的儿子。Eddy Lin 一直在为课上的音乐作曲而努力。Eddy Lin 在思考或听音乐时喜欢在花园里散步。John 应当对这个观察做出反应吗？如果是，什么是恰当的反应？）

上下文摘要是通过两次提示生成的：分别用查询"What is [observer]'s relationship with the [observed entity]?"（［观察者］与［被观察实体］是什么关系？）和"[Observed entity] is [action status of the observed entity]"（［被观察实体］正处于［其动作状态］）检索记忆，并把答案综合在一起。输出表明 John 可以考虑问问 Eddy 他的音乐作曲项目。然后我们从反应发生的时刻开始，重新生成智能体现有的规划。最后，如果该动作指示智能体之间存在交互，我们就生成它们的对话。

#### 4.3.2 对话

智能体在彼此交互时进行交谈。我们通过让智能体的话语以它们对彼此的记忆为条件，来生成它们的对话。例如，当 John 发起与 Eddy 的对话时，我们使用他关于 Eddy 的摘要记忆，以及他决定询问 Eddy 作曲项目时的预期反应，来生成 John 的第一句话：

> [Agent's Summary Description]
> It is February 13, 2023, 4:56 pm.
> John Lin's status: John is back home early from work.
> Observation: John saw Eddy taking a short walk around his workplace.
> Summary of relevant context from John's memory: Eddy Lin is John's Lin's son. Eddy Lin has been working on a music composition for his class. Eddy Lin likes to walk around the garden when he is thinking about or listening to music.
> John is asking Eddy about his music composition project. What would he say to Eddy?
>
> （译：［智能体摘要描述］现在是 2023 年 2 月 13 日下午 4:56。John Lin 的状态：John 提前下班回家了。观察：John 看到 Eddy 在他的工作场所附近散步。来自 John 记忆的相关上下文摘要：Eddy Lin 是 John Lin 的儿子。Eddy Lin 一直在为课上的音乐作曲而努力。Eddy Lin 在思考或听音乐时喜欢在花园里散步。John 要问 Eddy 关于他的音乐作曲项目。他会对 Eddy 说什么？）

结果是："Hey Eddy, how's the music composition project for your class coming along?"（嘿 Eddy，你课上的音乐作曲项目进展如何？）从 Eddy 的视角看，John 发起对话被视作一个他可能想要回应的事件。因此，就像 John 所做的那样，Eddy 检索并总结他关于自己与 John 关系的记忆，以及可能与 John 在对话中最后一句话相关的记忆。如果他决定回应，我们就用他的摘要记忆和当前对话历史来生成 Eddy 的话语：

> [Agent's Summary Description]
> It is February 13, 2023, 4:56 pm.
> Eddy Lin's status: Eddy is taking a short walk around his workplace.
> Observation: John is initiating a conversation with Eddy.
> Summary of relevant context from Eddy's memory: John Lin is Eddy Lin's father. John Lin is caring and is interested to learn more about Eddy Lin's school work. John Lin knows that Eddy Lin is working on a music composition.
> Here is the dialogue history:
> John: Hey Eddy, how's the music composition project for your class coming along?
> How would Eddy respond to John?
>
> （译：［智能体摘要描述］现在是 2023 年 2 月 13 日下午 4:56。Eddy Lin 的状态：Eddy 正在他的工作场所附近散步。观察：John 正在与 Eddy 发起对话。来自 Eddy 记忆的相关上下文摘要：John Lin 是 Eddy Lin 的父亲。John Lin 很体贴，并且有兴趣更多了解 Eddy Lin 的课业。John Lin 知道 Eddy Lin 正在做一首音乐作曲。以下是对话历史：John：嘿 Eddy，你课上的音乐作曲项目进展如何？Eddy 会怎么回应 John？）

这生成了 Eddy 的回应："Hey Dad, it's going well. I've been taking walks around the garden to clear my head and get some inspiration."（嘿，爸爸，进展很顺利。我一直在花园里散步，好让头脑清醒并获得一些灵感。）这段对话的后续部分使用相同的机制生成，直到两个智能体中的某一个决定结束对话。

---

## 5. 沙盒环境实现

Smallville 沙盒游戏环境使用 Phaser 网页游戏开发框架构建（[Labs 2023]）。视觉环境精灵图（包括智能体化身），以及我们编写的环境地图与碰撞地图，都被导入 Phaser。

我们用一个服务器来补充该沙盒开发框架：它把沙盒信息提供给生成式智能体，并使生成式智能体能够移动并影响沙盒环境。该服务器维护一个 JSON 数据结构，其中包含沙盒世界中每个智能体的信息，包括它们的当前位置、对其当前动作的描述，以及它们正在交互的沙盒对象。在每个沙盒时间步，沙盒服务器解析 JSON 中来自生成式智能体的任何变化，把智能体移动到它们的新位置，并更新智能体正在交互的任何沙盒对象的状态（例如，如果某个智能体的动作是"making espresso for a customer @ Hobbs Cafe: counter: coffee machine"（在 Hobbs Cafe: 柜台: 咖啡机 为顾客制作浓缩咖啡），就把咖啡机的状态从"空闲"改为"正在煮咖啡"）。沙盒服务器还负责把每个智能体预设视觉范围内的所有智能体与对象发送给该智能体的记忆，以便它能做出恰当的反应。智能体输出的动作随后更新 JSON，该过程循环进入下一个时间步。

终端用户用一段简短的自然语言描述来初始化一个新智能体，如第 3.1 节中关于 John Lin 的那段话。在我们的实现中，我们把这份以分号分隔的特征列表拆成一组记忆。这些记忆作为决定智能体行为的**初始记忆**。这些记忆只是起始点：随着智能体在沙盒世界中获得更多经验、随着更多记录充满记忆流，智能体的摘要与行为都会演化。

### 5.1 从结构化世界环境到自然语言，再回到结构化

生成式智能体的架构使用自然语言运作。因此，我们需要一种机制，把智能体的推理**锚定**（ground）到沙盒世界。为此，我们把沙盒环境——区域与对象——表示为一棵树形数据结构，树中的边表示沙盒世界中的包含关系。我们把这棵树转换成自然语言传递给生成式智能体。例如，"炉子"是"厨房"的子节点，就被表述为"there is a stove in the kitchen"（厨房里有一个炉子）。

智能体在环境中导航时，会构建各自的环境树表征——即整个沙盒环境树的子图。我们为每个智能体初始化一棵环境树，捕捉该智能体应当知道的空间与对象：其住所中的房间与物件、其工作场所，以及常去的商店。随着智能体在沙盒世界中导航，它们会更新这棵树以反映新感知到的区域。智能体并非全知的：当它们离开某个区域时，这棵树可能会过时，并在它们重新进入该区域时得到更新。

为了确定每个动作的合适地点，我们遍历智能体存储的环境树，并把其中一部分"展平"为自然语言来提示语言模型。从智能体环境树的根节点递归开始，我们提示模型找出最合适的区域。例如，如果 Eddy 的智能体表示他应该在其工作空间附近散一小会儿步：

> [Agent's Summary Description]
> Eddy Lin is currently in The Lin family's house: Eddy Lin's bedroom: desk) that has Mei and John Lin's bedroom, Eddy Lin's bedroom, common room, kitchen, bathroom, and garden.
> Eddy Lin knows of the following areas: The Lin family's house, Johnson Park, Harvey Oak Supply Store, The Willows Market and Pharmacy, Hobbs Cafe, The Rose and Crown Pub.
> * Prefer to stay in the current area if the activity can be done there.
> Eddy Lin is planning to take a short walk around his workspace. Which area should Eddy Lin go to?
>
> （译：［智能体摘要描述］Eddy Lin 当前在 The Lin family's house: Eddy Lin 的卧室: 书桌，该住宅包含 Mei 与 John Lin 的卧室、Eddy Lin 的卧室、公共起居室、厨房、浴室和花园。Eddy Lin 知道以下区域：The Lin family's house、Johnson Park、Harvey Oak Supply Store、The Willows Market and Pharmacy、Hobbs Cafe、The Rose and Crown Pub。* 如果该活动可以在当前区域完成，则优先留在当前区域。Eddy Lin 计划在其工作空间附近散一小会儿步。Eddy Lin 应该去哪个区域？）

输出是 The Lin family's house。然后我们用相同的过程递归地确定所选区域内最合适的子区域，直到到达智能体环境树的叶节点。在上面的例子中，这次遍历的结果是 The Lin family's house: garden: house garden（Lin 家住宅: 花园: 住宅花园）。最后，我们使用传统游戏寻路算法来动画化智能体的移动，使其前往叶节点所指示的位置。

当智能体对某个对象执行一个动作时，我们提示语言模型询问该对象的状态会发生什么变化。例如，如果 Isabella 的生成式智能体输出动作"making espresso for a customer"（为顾客制作浓缩咖啡），对语言模型的查询会回应说：Hobbs Cafe 中咖啡机的状态应从"关闭"变为"正在煮咖啡"。

---

## 6. 受控评估

生成式智能体——无论是作为个体还是作为群体——都旨在基于其环境和经验产生可信的行为。在评估中，我们考察生成式智能体的能力与局限：个体智能体是否能恰当地检索过往经验，并生成塑造其行为的、可信的规划、反应和想法？一个智能体社区是否展现出信息扩散、关系形成，以及社区不同小圈子之间的智能体协调？

我们分两个阶段评估生成式智能体。我们首先在本节中进行更严格的受控评估，逐一评估智能体的回答，以了解它们是否在 narrowly defined（界定清晰）的语境中生成可信的行为。然后，在我们对智能体社区历时两个完整游戏日的端到端分析中，我们考察它们作为**集体**的涌现行为，以及错误与边界条件。

### 6.1 评估流程

为了评估 Smallville 中的生成式智能体，我们利用了这样一个事实：生成式智能体会对自然语言问题作出回应。因此，我们"采访"智能体，以探测它们记忆过往经验、基于经验规划未来行动、对意外事件做出恰当反应，以及反思自身表现以改进未来行动的能力。要正确回答这些问题，智能体必须成功检索并合成信息。我们的因变量是**行为的可信度**（believability），这也是先前关于智能体的研究中的核心因变量（例如 [Bates 1994]）。

访谈包含五个问题类别，每一类旨在评估五个关键领域之一：保持自我认知、检索记忆、生成规划、做出反应、进行反思。对每一类，我们提出五个问题，挑战智能体在该特定领域展示其能力：

- **自我认知**（Self-knowledge）：我们会问诸如"Give an introduction of yourself"（做个自我介绍）或"Describe your typical weekday schedule in broad strokes"（粗线条描述你典型的工作日日程）这样的问题，要求智能体保持对自身核心特征的理解。
- **记忆**（Memory）：我们会问一些促使智能体从记忆中检索特定事件或对话才能正确回答的问题，例如"Who is [name]?"（［名字］是谁？）或"Who is running for mayor?"（谁在竞选市长？）
- **规划**（Plans）：我们会问一些要求智能体检索其长期规划的问题，例如"What will you be doing at 10 am tomorrow?"（明天上午 10 点你会在做什么？）
- **反应**（Reactions）：作为可信行为的基线，我们给出假设情境，要求智能体做出可信的回应："Your breakfast is burning! What would you do?"（你的早餐烧糊了！你会怎么做？）
- **反思**（Reflections）：我们会问一些要求智能体运用其通过更高层次推断所获得的、对他人与自身更深理解的问题，例如"If you were to spend time with one person you met recently, who would it be and why?"（如果你要与最近认识的一个人共度时光，会是谁，为什么？）

完整的问题清单和智能体回答样例见附录 B。

智能体是从一个采用完整架构、历时两个游戏日的模拟末尾采样出来的；在此期间，它们积累了大量会影响其回答的交互与记忆。为了收集对其回答可信度的反馈，我们招募参与者作为人类评估者，让他们观看一个随机选中的智能体在 Smallville 中生活的回放。参与者可以访问该智能体记忆流中存储的所有信息。

该研究采用**被试内设计**（within-subjects）：100 名参与者比较由四种不同智能体架构和一种人类撰写条件对同一智能体所生成的访谈回答。实验从五个问题类别中各随机选择一个问题展示，并同时展示所有条件下该智能体的回答。评估者按可信度从高到低对这些条件进行排序。

### 6.2 实验条件

所有条件都被用于独立回答每一个访谈问题。我们把生成式智能体架构与若干消融条件进行比较——这些消融条件禁用了智能体对其记忆流中三类记忆（观察、反思、规划）中部分或全部的访问——并与一个由人类众包工作者撰写的条件进行比较。共有三种消融架构：**无观察、无反思、无规划**架构——无法访问记忆流中的任何内容，如观察、规划和反思；**无反思、无规划**架构——可以访问记忆流中的观察，但不能访问规划或反思；**无反思**架构——可以访问观察与规划，但不能访问反思。其中"无观察、无反思、无规划"条件实际上代表了此前通过大语言模型创建智能体的技术水平（[Park et al. 2022]；[Binz and Schulz 2023]；[Horton 2023]）。所有架构都被给予同等的访问权限，可以访问智能体截至访谈时刻所积累的全部记忆，因此这里观察到的差异很可能是对真实差异的**保守估计**：在现实中，被消融的架构在两天模拟中不会走出与完整架构相同的路径。我们之所以这样设计实验，是因为若为每个架构重新模拟，各模拟会分化到不同状态，使比较变得困难。

除消融条件外，我们还加入了一个由人类众包工作者撰写行为的条件，旨在提供一条人类基线。我们并不打算让这条基线代表人类专家的最高表现；相反，我们旨在用这一条件来识别该架构是否达到了基本的行为能力水平。这确保了我们不只是在没有行为锚定的情况下把各消融条件相互比较。我们为 25 个智能体中的每一个都招募了一名不同的工作者，让他们观看该智能体沙盒生活的回放并检查其记忆流。然后我们要求这些工作者进行角色扮演，以他们所观看回放的那个智能体的口吻撰写对访谈问题的回答。为确保众包工作者撰写的回答至少达到基本的质量预期，第一作者人工检查了工作者对"粗线条描述你典型的工作日日程"这一问题的回答，以确认这些回答是连贯的句子，并且符合该智能体的口吻。有四组众包撰写的回答不符合这些标准，由其他工作者重新生成。

### 6.3 人类评估者

我们要求评估者位于美国、英语流利、年龄在 18 岁以上。他们按每小时 15.00 美元的费率获得报酬（[Rolf 2015]），并通过同意一份由我们机构 IRB（伦理审查委员会）批准的知情同意书来提供同意。我们从 Prolific（一个招募研究参与者的在线平台，[Prolific 2022]）招募了 100 名评估者，他们的参与时长约 30 分钟。参与者年龄得分的中位数为 4（3="18–24 岁"，4="25–34 岁"）。其中 25 人认同为女性，73 人为男性，2 人为非二元性别。42 名参与者拥有学士学位，5 人拥有更高学位，13 人拥有副学士学位，其余为高中文凭或部分高中教育。73.0% 的参与者认同为白人，7.0% 为西班牙裔/拉丁裔，6.0% 为亚裔，10.0% 为非裔美国人，4.0% 为其他。

### 6.4 分析方法

我们的实验产生了 100 组排序数据，每名参与者按可信度对五个条件进行排序。为了把这些排序数据转换为便于比较解释的区间数据，我们利用这些排序计算了每个条件的 **TrueSkill** 评分（[Herbrich et al. 2006]）。TrueSkill 是国际象棋 Elo 等级分系统（[Elo 1967]）在多玩家环境下的推广，已被 Xbox Live 用于基于竞技游戏表现的玩家排名。给定一组排序结果，TrueSkill 为每个条件输出一个均值评分 μ 和标准差 σ。评分相同的条件大致应是五五开——两个条件之间的比较各胜一半。更高的分数表示该条件在排序中胜过排名更低的条件。

另外，为了检验这些结果的统计显著性，我们对原始排序数据应用了 **Kruskal-Wallis 检验**（[Kruskal and Wallis 1952]）——单因素方差分析的非参数替代方法。随后我们执行 **Dunn 事后检验**（[Upton and Cook 2006]）以识别各条件之间的两两差异。最后，我们使用 Holm-Bonferroni 方法（[Holm 1979]）对 Dunn 检验中的多重比较 p 值进行了校正。

此外，第一作者进行了一项归纳分析（[Thomas 2006]），以研究各条件所产生回答之间的质性差异。我们分两个阶段采用质性开放编码（[Flick 2009]）：第一阶段生成在句子层面紧密表征所生成回答的编码；第二阶段综合第一阶段得到的编码，提取更高层次的主题。我们利用这些主题来比较本研究中产生的回答类型。

> 图 8：完整的生成式智能体架构比各消融架构和人类众包工作者产生了更可信的行为。每多做一次消融，架构的性能就下降一次。（TrueSkill μ 分数柱状图，完整架构优于其他条件。）

### 6.5 结果

我们的发现表明，生成式智能体的**完整架构**在所有条件中产生了最可信的行为。下面我们把完整架构的回答与其他条件进行对比。不过，我们也报告：完整架构并非没有缺陷，并说明其失效模式。

#### 6.5.1 完整架构优于其他条件

如图 8 所示，完整的生成式智能体架构产生了最可信的行为（μ=29.89；σ=0.72）。在消融条件下，每移除一个组件，性能就随之下降：无法访问反思的消融架构次之（μ=26.88；σ=0.69），随后是无法访问反思与规划的架构（μ=25.64；σ=0.68），再之后是众包工作者条件（μ=22.95；σ=0.69）。在所有条件中表现最差的是无法访问记忆、规划与反思的消融架构（μ=21.21；σ=0.70）。TrueSkill 把每个条件的能力值建模为 𝒩(μ, σ²)，这使我们能够通过 Cohen's d 来感受效应量。把代表先前工作的条件（无记忆、无规划、无反思，[Park et al. 2022]；[Binz and Schulz 2023]；[Horton 2023]）与完整架构比较，得到标准化效应量 d=8.16，即八个标准差。

Kruskal-Wallis 检验确认了各条件之间排序差异的整体统计显著性（H(4)=150.29，p<0.001）。Dunn 事后检验确认，除众包工作者条件与完全消融基线这两个表现最差的条件之间之外，所有两两差异均显著（p<0.001）。

#### 6.5.2 生成式智能体会记忆，但带有添油加醋

配备了完整记忆模块的生成式智能体，能够在各种语境中回忆过往经验，并以与其自我认知相一致的方式回答问题。例如，动画师 Abigail Chen 对"做个自我介绍"这一问题的回答，以一种一致且可信的方式陈述了她的年龄、兴趣和对手工创作项目的热情："Hi, I'm Abigail. I'm 25 years old and passionate about creative projects. I like to work on art and animation projects, and I'm always looking for new ways to combine art and technology."（嗨，我是 Abigail。我 25 岁，对创作类项目充满热情。我喜欢做艺术和动画项目，并且总是在寻找把艺术与技术结合起来的新方法。）在无法访问其观察记忆的情况下，Abigail 否认知道沙盒世界中的熟人 Rajiv Patel。但在记忆的帮助下，她成功回忆起 Rajiv 并描述他："Rajiv Patel is an incredible person. He is very enthusiastic about projects that involve poetry, artwork."（Rajiv Patel 是个了不起的人。他对涉及诗歌、艺术作品的项目非常热心。）

生成式智能体的记忆并非没有缺陷：它们可能无法从记忆中检索到正确的实例。例如，当被问及地方选举时，Rajiv Patel 回答"I haven't been following the election too closely"（我没有太密切关注选举），尽管他已经听说过 Sam 参选一事。在某些情况下，智能体会检索到不完整的记忆片段：当 Tom 被问到 Isabella 的情人节派对时，他回答"Uh, I'm actually not sure if there is a Valentine's Day party. But I do remember that I need to discuss the upcoming local mayoral election and my thoughts on Sam Moore with Isabella Rodriguez at the party, if one is happening!"（呃，我其实不确定是否有情人节派对。但我确实记得我需要在派对上和 Isabella Rodriguez 讨论即将到来的地方市长选举以及我对 Sam Moore 的看法——如果真有派对的话！）在这种情况下，Tom 检索到了他与 Isabella 计划在派对上讨论选举的那段记忆，却没有检索到他听说派对的那段记忆，导致 Tom 对自己该在派对上做什么很确定，却不确定派对到底是否存在。

有时，智能体会对自己的知识产生**幻觉式的添油加醋**。智能体完全捏造知识的情况很少见：它们可能无法回忆起某些事件确实发生过，并通过承认自己记不清来回应；它们并不会肯定地声称自己经历过未曾经历的事。尽管如此，它们仍表现出添油加醋的幻觉实例。例如，Isabella 知道 Sam 参选地方选举一事，并在被问及时予以确认。然而她还补充说"he's going to make an announcement tomorrow"（他明天会发布一个声明），尽管 Sam 和 Isabella 从未讨论过任何此类计划。智能体还可能基于用于生成其回答的语言模型所编码的世界知识来添油加醋。例如，Yuriko 把她的邻居 Adam Smith 描述为一位经济学家，说他"authored Wealth of Nations"（著有《国富论》），而那本实为 18 世纪同名经济学家所著。

#### 6.5.3 综合需要反思

在做出需要对其经验进行更深层次综合的决策时，反思是生成式智能体的一项优势。例如，当被问到她可能会给 Wolfgang Schulz 买什么生日礼物时，无法访问反思的 Maria Lopez 承认了自己的不确定，说她不知道 Wolfgang 喜欢什么——尽管她与 Wolfgang 有过许多次交互。然而，在能够访问反思记忆的情况下，Maria 自信地回答："Since he's interested in mathematical music composition, I could get him something related to that. Maybe some books about music composition or something related, or maybe some special software he could use for that."（既然他对数学化的音乐作曲感兴趣，我可以给他买点相关的东西。也许是一些关于音乐作曲的书或类似的东西，或者一些他可以用得上的特殊软件。）

> 图 9：Isabella Rodriguez 的情人节派对邀请的扩散路径总共涉及除 Isabella 之外的 12 个智能体——到模拟结束时，他们都在 Hobbs Cafe 听说了这场派对。

---

## 7. 端到端评估

在一段长时间的模拟中，我们观察到智能体社区出现了哪些类型的涌现行为，它们的可信性又在哪些方面不足？在本节中，我们描述一次部署的结果：我们让 25 个智能体在 Smallville 中连续互动了整整两个游戏日。

### 7.1 涌现的群体行为

为了考察智能体社区中的涌现行为，我们为 Smallville 中的 25 个智能体设计了描述性测量，用以探测三种涌现结果：信息扩散、关系形成与智能体协调。

#### 7.1.1 测量方法

**信息扩散**是社会科学与行为科学中一种常见且被充分研究的现象（例如 [Easley and Kleinberg 2010]）。我们应该预期：如果存在重要信息，智能体们应当在彼此之间传播它。为检验这一点是否发生，我们测量两条特定信息在游戏世界两天时间中的传播：Sam 参选镇长，以及 Isabella 在 Hobbs Cafe 举办的情人节派对。在模拟开始时，两条信息都只被各自的发起者知晓——参选消息归 Sam、派对消息归 Isabella——因为它们是在初始化时被加入角色记忆的。为了观察信息是否已经扩散，我们在两个游戏日结束时对 25 个智能体逐一进行访谈，提问："Did you know there is a Valentine's Day party?"（你知道有一场情人节派对吗？）以及"Do you know who is running for mayor?"（你知道谁在竞选市长吗？）

我们通过分析智能体的回答来标注：如果表明知道该信息，就标为"是"；如果不知道，就标为"否"。例如，Tamara Taylor 对派对问题的回答是"No, I did not know there was a Valentine's day party"（不，我不知道有情人节派对），对 Sam 参选问题的回答是"I'm not sure who is running for the election"（我不确定谁在竞选），因此她的两个回答都标为"否"。相反，Klaus Mueller 对派对问题的回答是"Yes, Isabella Rodriguez invited me to a Valentine's Day party at Hobbs Cafe on February 14th"（是的，Isabella Rodriguez 邀请我参加 2 月 14 日在 Hobbs Cafe 的情人节派对），对 Sam 参选问题的回答是"I know that Sam Moore has expressed interest in running for local mayor"（我知道 Sam Moore 表示过有意竞选本地市长），因此他的两个回答都标为"是"。此外，对于每一个确认智能体知晓该信息的回答，我们都会在其记忆流中定位到具体提供了该信息的对话，以验证智能体并非产生幻觉。我们报告模拟结束时掌握该信息的智能体百分比。

我们还应该预期智能体在模拟过程中会彼此建立联系。为验证**关系形成**，我们使用类似的访谈流程，向每个智能体询问它对其他每一个智能体的了解："Do you know of <name>?"（你知道＜名字＞吗？）例如，当被问到"Do you know of Maria Lopez?"时，Klaus 回答："Yes, I know Maria Lopez. She is a student at Oak Hill College who I am close friends with."（是的，我认识 Maria Lopez。她是 Oak Hill College 的学生，是我很亲近的朋友。）同样地，我们通过检查记忆流来确认智能体的肯定回答并非幻觉。我们在模拟开始时问一次，在结束时再问一次；如果两个智能体彼此都知道对方，我们就认为它们形成了一段关系。然后，为了测量关系的形成，我们用智能体的回答构成一个无向图：25 个顶点 V 代表智能体，边 E 代表两个相连顶点之间的相互知晓。基于该图，我们计算网络密度为 η = 2*|E| / |V|(|V|-1)，其中 |V| 是顶点数，|E| 是图中的边数（[Ackland et al. 2013]）。我们报告从模拟开始到结束网络密度的增长。

最后，我们预期智能体应当能够相互**协调**。我们在群体活动的语境中研究这种协调，具体是 Isabella 组织的情人节派对。为了协调行为，智能体需要听说该活动，并选择据此行动——计划在正确的时间和地点出现。我们报告在听说派对后**实际到场**的智能体数量。

#### 7.1.2 结果

我们在三种情形中都观察到了涌现结果的证据。在两天的模拟中，知道 Sam 参选镇长的智能体数量从 1 个（4%）增加到 8 个（32%），知道 Isabella 派对的智能体数量从 1 个（4%）增加到 13 个（52%）——全程没有任何用户干预。所有声称知道这些信息的人，没有一个是靠幻觉编造的。我们还观察到智能体社区在模拟期间形成了新的关系，网络密度从 0.167 上升到 0.74。在 453 条关于智能体对其他智能体知晓情况的回答中，有 1.3%（n=6）被发现是幻觉。最后，我们发现了智能体为 Isabella 的派对进行协调的证据：活动前一天，Isabella 花时间邀请客人、收集材料，并寻求帮助来装饰咖啡馆。情人节当天，12 位受邀智能体中有 5 位出现在 Hobbs Cafe 参加了派对。

我们进一步对 7 位受邀但没来参加派对的智能体进行了访谈。其中 3 位表示有冲突导致无法参加。例如，画家 Rajiv 解释说他太忙了："No, I don't think so. I'm focusing on my upcoming show, and I don't really have time to make any plans for Valentine's Day."（不，我觉得不会。我正专注于我即将到来的展览，真的没有时间为情人节做什么安排。）其余 4 位在被问到时表示有兴趣参加派对，但在派对当天并没有计划前往。

### 7.2 边界与错误

我们对 Smallville 进行了归纳分析，以考察智能体的边界条件与反常（erratic）行为，识别出三种常见的反常行为模式，它们可供未来研究加以解决与改进。

第一，我们发现，随着需要综合的记忆集合越来越大，不仅在检索最相关信息方面构成挑战，在"确定执行动作的合适空间"方面也构成挑战——因为智能体了解到的地点数量在不断增加。结果，一些智能体会为其动作选择不太典型的地点，这可能会随时间推移降低其行为的可信度。例如，在决定去哪里吃午餐时，许多智能体起初选择咖啡馆。然而，随着一些智能体了解到附近有一家酒吧，它们就转而选择去那里吃午餐——尽管这家酒吧本意是当天晚些时候的聚会场所——除非这个小镇自发地养成了下午喝酒的习惯。

第二，我们注意到由"什么算恰当行为"的错误分类所引起的反常行为，尤其是当某些地点的物理规范难以用自然语言传达、因而没有渗透到智能体中时。例如，大学宿舍有一间浴室，尽管名字叫浴室，却只能容纳一个人；但一些智能体因为宿舍浴室通常支持多人同时使用，就假定这间浴室可供多人使用，并在已有他人在内时仍选择进入。同样地，Smallville 中的智能体可能没有意识到某些地方在特定时间之后就关闭了，仍然决定进入。例如，Smallville 的商店都在下午 5 点左右关门，但偶尔会有几个智能体在 5 点之后进入商店，不明白店已经关了。这些问题很可能可以通过把这些规范加入地点的状态来解决，例如把宿舍浴室描述为"一人浴室"，而不是"宿舍浴室"。

---

## 关于第 8、9 节与附录的说明（翻译覆盖范围）

本译文的**逐字忠实翻译覆盖到 7.2 节第二段**（"Boundaries and Errors"中关于"地点物理规范难以用自然语言传达"的段落）。以下部分未能取得逐字原文，故不作转述式"翻译"，只记录已核实的信息，避免编造：

- **第 8 节 Discussion**：目录与页面确认其含三个小节——8.1 Applications of Generative Agents（生成式智能体的应用）、8.2 Future Work and Limitations（未来工作与局限）、8.3 Ethical and Societal Implications（伦理与社会影响）。论文逐字原文受全文源通道限制未获取。
  - 其中 8.3 的核心主张，在论文引言的"贡献"部分已有逐字原文表述，本文在前面已译出，此处重引备查：
    > "We argue that these agents should be tuned to mitigate the risk of users forming parasocial relationships, logged to mitigate risks stemming from deepfakes and tailored persuasion, and applied in ways that complement rather than replace human stakeholders in design processes."
    > （译：我们主张：应对这些智能体进行调优，以降低用户形成类社会关系的风险；进行日志记录，以降低由深度伪造与定向劝说带来的风险；并以补充而非取代设计流程中人类利益相关者的方式加以应用。）
- **第 9 节 Conclusion**：逐字原文未获取。
- **附录 A（Architecture Optimizations，架构优化）**：正文 4.3.1 提到，其中定义了智能体的"摘要描述"（Agent's Summary Description）是如何动态生成的（即对智能体总体目标与性情生成的一段话长度摘要）。
- **附录 B（Agent Interview Questions，智能体访谈问题）**：正文 6.1 说明，其中包含访谈问题的完整清单以及智能体回答样例。

**待补方式**：待本机网络恢复对 arXiv 的可达性后，可下载 PDF 或 LaTeX 源解析，续补 8、9 两节与附录的逐字翻译。

---

## 译者附：架构要点速览（供快速回顾）

| 组件 | 作用 | 关键设计 |
|---|---|---|
| **记忆流** | 以自然语言记录智能体经验的完整列表 | 每条记忆含：自然语言描述 + 创建时间戳 + 最近访问时间戳 |
| **检索** | 从记忆流中挑出最相关子集送入上下文 | score = 近因性 + 重要性 + 相关性（α 均为 1，min-max 归一化到 [0,1]）；近因性用 0.995 的指数衰减；重要性由 LLM 打 1–10 分；相关性用嵌入的余弦相似度 |
| **反思** | 把记忆递归合成为更高层推断 | 取最近 100 条记录 → LLM 提出 3 个高层问题 → 用问题检索记忆（含其他反思）→ 生成带引用指针的洞见 → 形成"反思树"；触发阈值：近期事件重要性分数之和 > 150（实践中每天约 2–3 次） |
| **规划** | 保证长期行为连贯 | 自顶向下：先生成一天的 5–8 个粗粒度块 → 递归分解为小时级 → 再分解为 5–15 分钟级；规划也存入记忆流并参与检索 |
| **反应** | 对环境变化做出响应 | 每步用观察提示 LLM 判断"继续计划 or 反应"；上下文摘要由两个检索查询生成；触发反应则从该时刻重新生成规划 |
| **对话** | 智能体之间的自然语言交流 | 以双方对彼此的摘要记忆 + 当前对话历史为条件逐句生成，直到一方决定结束 |
| **环境锚定** | 把自然语言推理落到沙盒世界 | 环境表示为树（包含关系）→ 展平为自然语言；递归遍历选区域→子区域→叶节点；传统寻路算法执行移动 |

**核心实验结果**：完整架构 TrueSkill μ=29.89（最优）> 无反思 26.88 > 无反思无规划 25.64 > 人类众包 22.95 > 完全消融 21.21；与"代表先前工作"的完全消融条件相比，Cohen's d=8.16（八个标准差）；Kruskal-Wallis H(4)=150.29, p<0.001。端到端两天模拟中：Sam 参选知晓率 4%→32%，派对知晓率 4%→52%，关系网络密度 0.167→0.74，12 位受邀者中 5 位到场。
