#!/usr/bin/env python3
"""第 2 轮三篇译文强校验（对齐 arxiv-fulltext-cn-translation skill 第 6 步）。

判读标准：
  - 图片引用缺失数必须为 0
  - 占位符残留（[[IMG:...]] / [[TABLE:...]] / <!-- PARTn -->）必须为 0
  - 数学环境外的裸 LaTeX 必须为 0
"""

from __future__ import annotations

import os
import re
import sys

BASE = "/Users/alex/test/github/agent-memroy/starting"
FILES = [
    "Weighted-Memory-Tree_2608.20631_全文详细翻译.md",
    "StructMem_2604.21748_全文详细翻译.md",
    "Memento_2604.09852_全文详细翻译.md",
]


def check(fname: str) -> bool:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"\n### {fname}\n  ✗ 文件不存在")
        return False

    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    ok = True
    print(f"\n### {fname}  ({len(text.encode('utf-8'))} bytes, {text.count(chr(10)) + 1} 行)")

    # 1) 图片引用与文件存在性
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    miss = [p for p in imgs if not os.path.exists(os.path.join(BASE, p))]
    print(f"  图片引用 {len(imgs)} 张，缺失 {len(miss)} {miss if miss else ''}")
    if miss:
        ok = False

    # 2) 占位符残留
    leftovers = re.findall(r"\[\[(?:IMG|TABLE)[^\]]*\]\]", text)
    sentinels = re.findall(r"<!--\s*PART\d+\s*-->", text)
    print(f"  图表占位符残留 {len(leftovers)} {leftovers if leftovers else ''}")
    print(f"  分段哨兵残留 {len(sentinels)} {sentinels if sentinels else ''}")
    if leftovers or sentinels:
        ok = False

    # 3) 数学环境外的裸 LaTeX
    bad: list[tuple[int, str]] = []
    for i, line in enumerate(text.split("\n"), 1):
        s = re.sub(r"\$\$.*?\$\$", "", line)
        s = re.sub(r"\$[^$]*\$", "", s)
        if "\\" in s:
            bad.append((i, s[:120]))
    print(f"  数学环境外裸 LaTeX {len(bad)}")
    for ln, frag in bad[:10]:
        print(f"    L{ln}: {frag}")
    if bad:
        ok = False

    # 4) 结构抽查：文件头 + 图注三件套
    head_ok = text.startswith("# ") and "> **论文元信息**" in text[:1200]
    print(f"  文件头（英文标题 + 论文元信息）{'OK' if head_ok else '异常'}")
    # 图注三件套。图号口径允许两种：'原文 Figure N'（与 PDF 一致）
    # 或 'arXiv HTML 版 Figure N'（PDF/HTML 图号有偏移时，需在翻译说明中交代）
    cap = len(re.findall(r"> \*\*图 \d+（(?:原文|arXiv HTML 版) Figure", text))
    print(f"  图注三件套（原文 Figure 引用）{cap} 处")
    if not head_ok:
        ok = False

    print(f"  结论: {'✓ 通过' if ok else '✗ 未通过'}")
    return ok


def main() -> int:
    results = [check(f) for f in FILES]
    print("\n" + "=" * 48)
    print(f"合计 {sum(results)}/{len(FILES)} 篇通过")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
