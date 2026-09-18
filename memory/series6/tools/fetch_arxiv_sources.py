#!/usr/bin/env python3
"""
重建第06篇 7 篇论文的源料（/tmp 断电即丢，本脚本用于在新机器上复现）。

用法：
    python3 memory/series6/tools/fetch_arxiv_sources.py [输出根目录，默认 /tmp/arxiv7]

产出（每篇一个子目录）：
    <root>/<arxiv_id>/paper.html    arXiv 官方 HTML 版原文
    <root>/<arxiv_id>/text2.txt     剥标签后的正文，含 [[IMG:xx]] / [[TABLE:xx]] 占位标记
    <root>/<arxiv_id>/index2.json   图表清单（kind/id/caption/src）

依赖：
    - 转换脚本来自 skill `arxiv-fulltext-cn-translation`：
      ~/.workbuddy/skills/arxiv-fulltext-cn-translation/scripts/arxiv_html_convert.py
      若新机器没有该 skill，先 `Skill` 加载一次 arxiv-fulltext-cn-translation 即可安装。
    - 图片**不需要**重新下载，已在仓库 starting/images/ 下（见 HANDOFF.md）。

注意：export.arxiv.org 对并发请求会限流（返回非 200 或空体），本脚本已加串行 + 重试。
"""
import os
import re
import subprocess
import sys
import time

IDS = [
    "2608.21230",  # UtilityUnderAttack  S 级
    "2607.17545",  # RetainOrConsolidate S 级
    "2609.08279",  # EvictionDestroys    S 级
    "2608.13334",  # RippleMem           A 级
    "2608.01742",  # MemSIF              A 级
    "2608.16370",  # CompressionCost     A 级
    "2608.28978",  # SelectiveForgetting A 级
]

CONVERT = os.path.expanduser(
    "~/.workbuddy/skills/arxiv-fulltext-cn-translation/scripts/arxiv_html_convert.py"
)


def fetch_html(arxiv_id, dst, tries=5):
    url = "https://export.arxiv.org/html/%s" % arxiv_id
    for attempt in range(tries):
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "90", "-w", "%{http_code}",
             "-o", dst, url],
            capture_output=True, text=True,
        )
        code = r.stdout.strip()
        if code == "200" and os.path.exists(dst) and os.path.getsize(dst) > 20000:
            return code, os.path.getsize(dst)
        time.sleep(5)
    return code, (os.path.getsize(dst) if os.path.exists(dst) else 0)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "/tmp/arxiv7"
    if not os.path.exists(CONVERT):
        sys.exit("找不到转换脚本：%s\n请先加载 skill arxiv-fulltext-cn-translation" % CONVERT)

    for arxiv_id in IDS:
        d = os.path.join(root, arxiv_id)
        os.makedirs(d, exist_ok=True)
        html = os.path.join(d, "paper.html")

        if os.path.exists(html) and os.path.getsize(html) > 20000:
            print("%-12s HTML 已存在，跳过抓取" % arxiv_id)
        else:
            code, size = fetch_html(arxiv_id, html)
            print("%-12s 抓取 http=%s size=%d" % (arxiv_id, code, size))
            if code != "200":
                print("            !! 抓取失败，稍后重跑本脚本")
                continue

        r = subprocess.run(
            [sys.executable, CONVERT, html, d],
            capture_output=True, text=True,
        )
        tail = (r.stdout or "").strip().split("\n")[-3:]
        txt = os.path.join(d, "text2.txt")
        idx = os.path.join(d, "index2.json")
        print("            转换: text2.txt=%s index2.json=%s | %s" % (
            os.path.getsize(txt) if os.path.exists(txt) else "MISS",
            os.path.getsize(idx) if os.path.exists(idx) else "MISS",
            " / ".join(tail),
        ))
        time.sleep(3)

    print("\n完成。下一步：按 HANDOFF.md 派发译文。")


if __name__ == "__main__":
    main()
