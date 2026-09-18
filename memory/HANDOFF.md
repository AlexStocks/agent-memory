# HANDOFF — 第06篇《有界召回篇》同期论文中文翻译（7 篇）

> 生成时间：2026-09-18 19:10（断电断网前）
> 交接原因：本机十分钟后停电断网。进度 **2/7**，源料在 `/tmp` 已随断电丢失，需按下方「恢复步骤」重建。

---

## 一、任务是什么

把 `memory/series6/第6篇_同期论文核查_2026-09-18.md` 里评级为 **S 级 3 篇 + A 级 4 篇**的 2026 年同主题论文，做**带图带表的全文中文翻译**，落到：

```
/Users/alex/test/github/agent-memory/starting/第06篇_有界召回篇/
```

- 论文清单：`2608.21230`（S）、`2607.17545`（S）、`2609.08279`（S）、`2608.13334`（A）、`2608.01742`（A）、`2608.16370`（A）、`2608.28978`（A）
- **风格基准**（照它的标题层级 / 图注三件套 / 表格写法 / 语言风格）：
  `starting/第05篇_写入机制篇/Beyond-Static-Summarization_2601.04463_全文详细翻译.md`
- 使用的 skill：`arxiv-fulltext-cn-translation`

---

## 二、当前进度

### 已完成（1/7 真正完成 + 1/7 半成品，均已提交入库）

| 译文文件 | 论文 | 体量 | 校验状态 |
|---|---|---|---|
| `EvictionDestroys_2609.08279_全文详细翻译.md` | What Eviction Destroys | 46 KB | ✅ **PASS**（图 2 张全引、表题 1、无残留） |
| `UtilityUnderAttack_2608.21230_全文详细翻译.md` | Utility Under Attack: Agent Memory Poisoning and the Limits of Content Screening and Provenance Ranking | 30 KB | ⚠️ **FAIL — 只写了第一段** |

> **`UtilityUnderAttack` 是半成品，接手后第一件事是补完它**，校验实测：
> - `<!-- PART2 -->` 哨兵**未替换**（文件在第一段末尾就断了）
> - 4 张插图**只引用了 1 张**（缺 Figure 1/3/4）
> - 表题行计数 **0**（Table 1 + 附录 T2–T6 全部未落）
> - 换句话说：摘要 + 前半正文有了，**后半正文、全部表格、3 张图、参考文献都还没有**。
>   `/tmp` 源料已丢，需先按第三节重建，再用 Edit 把 `<!-- PART2 -->` 替换为后半段。

### 待完成（6/7 篇）

| arXiv ID | 短名（图床目录） | 论文主题 | 图数 | 性质 |
|---|---|---|---|---|
| `2608.21230` | `UtilityUnderAttack` | 记忆投毒 / 溯源加权失效（**补 PART2**） | 4（已引 1） | 🔧 半成品补完 |
| `2607.17545` | `RetainOrConsolidate` | Retain or Consolidate?（预算依赖的记忆整合算子选择，方法名 OAS） | 2 | 🆕 全新翻译 |
| `2608.13334` | `RippleMem` | 事件级记忆图 + 查询时在线联想补全 | 4 | 🆕 全新翻译 |
| `2608.01742` | `MemSIF` | TSM / DUM 两类错配，结构化交互记忆 + 双轨事实记忆 | 10 | 🆕 全新翻译 |
| `2608.16370` | `CompressionCost` | 压缩抬高再获取成本（完成度未降但检索调用激增） | 6 | 🆕 全新翻译 |
| `2608.28978` | `SelectiveForgetting` | 图记忆在 LongMemEval 匹配预算下未赢扁平基线 | 1 | 🆕 全新翻译 |

**插图已全部下载并提交**，在 `starting/images/<短名>/`，**不要重新下载**。

---

## 三、恢复步骤（在新机器上照做）

```bash
cd /Users/alex/test/github/agent-memory
git pull

# 1) 重建 /tmp 源料（HTML + text2.txt + index2.json），约 2-3 分钟
python3 memory/series6/tools/fetch_arxiv_sources.py

# 2) 派发 5 个翻译子任务（prompt 模板见第四节）

# 3) 每篇写完立即校验
cd starting/第06篇_有界召回篇
python3 ../../memory/series6/tools/check_trans.py <译文文件名>
```

> `fetch_arxiv_sources.py` 依赖 skill `arxiv-fulltext-cn-translation` 自带的
> `scripts/arxiv_html_convert.py`。若新机器没装该 skill，先加载一次 `arxiv-fulltext-cn-translation`。
> 图片**不在**该脚本范围内（已在仓库里）。

---

## 四、派发 prompt 模板（照填即可）

每篇派一个 `general-purpose` 子 agent，把下表的值填进模板。**关键：不要把未核实的数字写进 prompt**，只给定位提示，并要求「以原文为准，不符时按原文来」。

```
你要把一篇 arXiv 论文的 HTML 全文翻译成中文 markdown，要求「全文 + 原论文插图 + 完整数据表格」。

论文：arXiv:<ID>《<英文标题>》

源文件已准备好，直接用，不要重新联网抓取：
- HTML 原文：/tmp/arxiv7/<ID>/paper.html
- 已剥标签的正文（含 [[IMG:xx]] / [[TABLE:xx]] 占位标记）：/tmp/arxiv7/<ID>/text2.txt
- 图表清单 + 完整图注（JSON，字段 kind/id/caption/src）：/tmp/arxiv7/<ID>/index2.json

先读一遍风格基准，照它的标题层级、图注三件套、表格写法与语言风格来写：
/Users/alex/test/github/agent-memory/starting/第05篇_写入机制篇/Beyond-Static-Summarization_2601.04463_全文详细翻译.md

输出文件（只写这一个）：
/Users/alex/test/github/agent-memory/starting/第06篇_有界召回篇/<短名>_<ID>_全文详细翻译.md

插图已下载完毕，不要重新下载。目录 starting/images/<短名>/，引用统一写 `../images/<短名>/<文件名>`。
可用文件与图号对应（图号请以 index2.json 的 caption 复核）：
<此处贴该篇的图号映射表>

每张图必须写三件套：
<!-- 原图：https://arxiv.org/html/<ID><ver>/<原始 src 文件名> -->
![图 N：<中文说明，把图里的关键结论写进去>](../images/<短名>/<文件>)

> **图 N（原文 Figure N）**：<英文原图注>
> （<原图注中文翻译>）

标题层级约定（严格遵守）：`# 英文标题` → `## 中文标题` → `## 摘要` → `## N. 标题`（编号后跟英文句点）
→ `### N.M 子节` → `#### run-in 段落标题`。run-in 段落标题恒用 h4。不得出现 h5/h6。
表格：标准 markdown 表，数值全量照抄不得省略；表题单独一行 `**表 N：<中文表题>**`；表下脚注也要译。
公式：原文 MathML+LaTeX 双份，剥标签后有重复串；译文统一用 LaTeX 重排（$...$ 或 $$...$$）；
数学环境外不得出现裸反斜杠命令。
写作纪律：全文翻译（摘要 + 全部正文小节 + 全部附录，参考文献保留编号不译条目）；
数字必须从 text2.txt 取，不得凭印象；术语首次出现中英对照；不得增补原文没有的结论。
分两段写：先 Write 写第一段（文件头 + 元信息 + 翻译说明 + 摘要 + 前半正文）末尾留 `<!-- PART2 -->`，
再 Edit 把哨兵替换为后半段。一次写完整篇会超输出上限。
文件头两个 blockquote：`> **论文元信息**`（编号/链接/版本日期/分类/作者/方法名/复现地址）与
`> **翻译说明**`（覆盖范围、插图张数、路径说明、PDF 裁剪位图需注明）。
写完自检：python3 memory/series6/tools/check_trans.py <译文文件名>
硬标准：图片引用缺失 0、占位符残留 0、PART 哨兵残留 0、数学环境外裸 LaTeX 0、结论 PASS。
汇报 ≤200 字：路径、覆盖范围与文字量、图数、表数、自检结论。
```

### 4.1 各篇图号映射（填进模板用）

**`2607.17545` RetainOrConsolidate**（HTML 版本号 `v2`）
- `01-figure_overview.png` ← Figure 1（OAS 工作流：何时整合、用哪个算子）
- `02-fig_budget_crossover.png` ← Figure 2（整合算子的预算交叉点）
- 表格多：`Sx4.T1`、`Sx4.T2`、`A2.T3`–`A2.T12`，附录预算敏感性表也要全译。

**`2608.13334` RippleMem**（`v1`）
- `01-motivation.png` ← Figure 1（长期记忆访问的失败模式）
- `02-method.png` ← Figure 2（RippleMem 框架总览）
- `03-ablation_locomo.png` ← Figure 3（LoCoMo 消融）
- `04-case1.png` ← Figure 4（LoCoMo 与 LongMemEval-S 案例）
- 表格多：`S4.T1`–`S4.T3`、`A1.T4`–`A1.T5`、`A2.T6`–`A2.T12`、`A4.T13`、`A5.T14`。
- 注意：`alg1` / `alg2` 是**算法块不是表格**，用代码块或有序列表逐行译出，保留算法标题与输入输出。

**`2608.01742` MemSIF**（`v2`）
- `01-fig1_empirical_motivation.png` ← Figure 1
- `02-MemSIF_method.png` ← Figure 2
- `03-backbone-generalization.png` ← Figure 3
- `04-ablation_linechart.png` ← Figure 4
- `05-scatter_combined.png` ← Figure 5
- `06-asv-chunk-sensitivity.png` ← Figure 6
- `07-sntd_trend.png` ← Figure 7
- `08-cdl-qad-scatter.png` ← Figure 8
- `09-case-study-1.png` ← Figure 9
- `10-case-study-2.png` ← Figure 10
- 表格极多（`S3.T1`–`S3.T3`、`S4.T4`、`A1.T5`–`A1.T11`、`A2.T12`–`A4.T15`、`A6.T16`–`A6.T18`），`A9.fig1`–`A9.fig7` 是图块需按内容分流。

**`2608.16370` CompressionCost**（`v1`）⚠️ **文件名与图号不同序，务必逐条核对**
- `01-fig1_draft.png` ← Figure 1（测量协议总览）
- `02-fig2_draft.png` ← Figure 2（压缩抬高再获取成本）
- `03-fig4_draft.png` ← **Figure 3**（两轴而非一轴）
- `04-fig5_retention.png` ← **Figure 4**（保留干预）
- `05-fig6_crossenv.png` ← **Figure 5**（外部环境边界）
- `06-fig3_draft.png` ← **Figure 6**（oracle 条件与交互预算）

**`2608.28978` SelectiveForgetting**（`v1`）
- `01-figure1-overview.png` ← Figure 1。**这张是 PDF 裁剪位图，无 HTML 源文件**，`<!-- 原图 -->` 注释写「（PDF 裁剪）」并注明来自 `https://arxiv.org/pdf/2608.28978`，且必须在「翻译说明」里注明。
- 该篇 index2.json 里 `S3.F1` 等图块被归为 `table`，按内容分流，别把图当表。
- 表格：`S4.T1`、`S4.T2`、`A1.T3`–`A1.T7`。

---

## 五、不可改动的约定

1. **图片是单一图床**：`starting/images/<短名>/`，不随篇拆分。子目录里的 md 用 `../images/...` 相对路径；`starting/` 根目录的 md 用 `images/...`。
2. **图注三件套**：`<!-- 原图：URL -->` + `![图 N：说明](相对路径)` + `> **图 N（原文 Figure N）**：英文原注` / `> （中文翻译）`。缺一不可（校验会数）。
3. **标题层级**：h1 英文标题 → h2 中文标题 → h2 摘要 → h2 `N. 标题` → h3 `N.M` → h4 run-in。**不得出现 h5/h6**。
4. **分两段写**，`<!-- PART2 -->` 哨兵，写完必须替换掉。
5. **全文翻译**，附录和表格数值全量，不概括。

---

## 六、已知坑（踩过的）

| 坑 | 现象 | 处理 |
|---|---|---|
| arXiv 并发限流 | 图片下载返回非 200 / 空体，但不是 URL 错 | 串行 + `sleep 2~4` + 4 次重试；脚本已处理 |
| GitHub HTTPS push | `error: RPC failed; HTTP 400 curl 56` | 改用 `git push ssh://git@ssh.github.com:443/AlexStocks/agent-memory.git main`（本次即靠它成功） |
| 远端有他人提交 | push 被 rejected（本次远端被 force update 过） | `git pull --rebase origin main` 后再推 |
| HTML 里部分图无独立图像文件 | 图被包成 `<figure>` 且内部是排版元素 | 从论文 PDF 裁剪（`pymupdf`，按图注向上聚簇、取最大间隙切分，避开上一节正文），裁完**肉眼核验** |
| MathML + LaTeX 双份渲染 | 剥标签后出现 `Mi n i tM_{init}` 这类重复串 | 统一用 LaTeX 重排 |
| `mv` 被沙箱 shim 拦截 | 仓库内移动文件报 "No such file" 且行为不可预期 | 用 `cp` 逐文件核对，别用 `mv` |

---

## 七、收尾动作（5 篇译完后）

1. 7 篇全跑一遍 `check_trans.py`，确认全部 PASS。
2. 写一篇 `第06篇_同期论文译文总结.md`（对齐 `第05篇_写入机制篇/五篇跟踪论文总结.md` 的格式）。
3. 检查 `memory/RESEARCH_LOG.md` 是否需要补第 6 篇相关条目的译文链接。
4. 把 5 篇译文 + 总结提交推送（走 SSH-443 通道）。
5. 若后续要把第 1–4 篇也按篇建目录归档，**先确认没有外部链接引用**（公众号旧文的 GitHub 链接指向 `starting/` 根目录）。
