#!/usr/bin/env python3
# 用法: python3 /tmp/check_trans.py <译文文件名>
# 在 /Users/alex/test/github/agent-memory/starting/第06篇_有界召回篇 下执行
import os, re, sys

f = sys.argv[1]
base = os.path.dirname(os.path.abspath(f)) or "."
t = open(f, encoding="utf-8").read()

imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", t)
missing = [p for p in imgs if not os.path.exists(os.path.join(base, p))]

print("文件:", f)
print("总字数(含标记):", len(t))
print("图片引用:", len(imgs), "| 缺失:", len(missing), missing)
print("占位符残留:", re.findall(r"\[\[(?:IMG|TABLE)[^\]]*\]\]", t))
print("分段哨兵残留:", re.findall(r"<!--\s*PART\d+\s*-->", t))

bad = []
for i, ln in enumerate(t.split("\n"), 1):
    s = re.sub(r"\$\$.*?\$\$", "", ln)
    s = re.sub(r"\$[^$]*\$", "", s)
    if "\\" in s:
        bad.append((i, s[:100]))
print("数学环境外裸 LaTeX:", len(bad), bad[:6])

print("h5/h6:", [l for l in t.split("\n") if re.match(r"^#{5,6} ", l)][:5])
print("图注三件套计数:", len(re.findall(r">\s*\*\*图\s*\d+（(?:原文|arXiv HTML 版)\s*Figure", t)))
print("表题行计数:", len(re.findall(r"^\*\*表\s*\d+", t, re.M)))
print("原图注释计数:", len(re.findall(r"<!--\s*原图", t)))
print("元信息/翻译说明:", ("论文元信息" in t), ("翻译说明" in t))

ok = (len(missing) == 0
      and not re.findall(r"\[\[(?:IMG|TABLE)[^\]]*\]\]", t)
      and not re.findall(r"<!--\s*PART\d+\s*-->", t)
      and len(bad) == 0
      and not [l for l in t.split("\n") if re.match(r"^#{5,6} ", l)])
print("结论:", "PASS" if ok else "FAIL")
