#!/usr/bin/env python3
"""
重建第06篇 7 篇论文的源料（/tmp 断电即丢，本脚本用于在新机器上复现）。
Windows 适配版：urllib 抓取（沙箱内 curl 不可用）、自包含转换器
（原依赖 skill `arxiv-fulltext-cn-translation` 的 arxiv_html_convert.py，
本机无该 skill，此处用 bs4 重写等价逻辑）。

产出（每篇一个子目录）：
    <root>/<arxiv_id>/paper.html    arXiv 官方 HTML 版原文
    <root>/<arxiv_id>/text2.txt     剥标签后的正文，含 [[IMG:FIGn]] / [[TABLE:TABn]] 占位标记
    <root>/<arxiv_id>/index2.json   图表清单（kind/id/caption/src）

用法：
    python fetch_arxiv_sources.py [输出根目录，默认 D:/tmp/arxiv7]

注意：export.arxiv.org 对并发请求会限流，本脚本串行 + 重试 + sleep。
"""
import json
import os
import re
import sys
import time
import urllib.request

from bs4 import BeautifulSoup, NavigableString, Tag

# (arxiv_id, 版本) —— 版本号与 HANDOFF 4.1 中已下载插图对应的版本一致
PAPERS = [
    ("2608.21230", "v1"),  # UtilityUnderAttack  S 级（补 PART2）
    ("2607.17545", "v2"),  # RetainOrConsolidate S 级
    ("2609.08279", "v1"),  # EvictionDestroys    S 级（译文已完成，源料备查）
    ("2608.13334", "v1"),  # RippleMem           A 级
    ("2608.01742", "v2"),  # MemSIF              A 级
    ("2608.16370", "v1"),  # CompressionCost     A 级
    ("2608.28978", "v1"),  # SelectiveForgetting A 级
]

UA = {"User-Agent": "Mozilla/5.0 (research translation tool; contact: local)"}


def fetch(url, dst, tries=4):
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) > 20000:
                with open(dst, "wb") as f:
                    f.write(data)
                return len(data)
            print(f"    第{attempt}次 body 过小({len(data)})，重试…")
        except Exception as e:
            print(f"    第{attempt}次失败: {e}")
        time.sleep(5)
    return 0


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def replace_math(soup):
    """LaTeXML 的 <math alttext=...> 含 LaTeX annotation 双份渲染，统一换成单一 $alttext$。"""
    for m in soup.find_all("math"):
        alt = clean(m.get("alttext", ""))
        m.replace_with(f"${alt}$" if alt else "")


def collect_figures(soup):
    """把顶层 figure 换成 [[IMG:FIGn]] / [[TABLE:TABn]] 标记，返回图表清单。"""
    items, fi, ti = [], 0, 0
    for fig in soup.find_all("figure"):
        if fig.find_parent("figure"):  # 嵌套 figure 只处理最外层
            continue
        classes = " ".join(fig.get("class") or [])
        img = fig.find("img")
        has_img = img is not None or fig.find(class_="ltx_graphics") is not None
        is_table = "ltx_table" in classes and not has_img
        cap = fig.find("figcaption")
        cap_text = clean(cap.get_text(" ", strip=True)) if cap else ""
        src = (img.get("src", "") if img else "") or ""
        if is_table:
            ti += 1
            kind, fid = "table", f"TAB{ti}"
        else:
            fi += 1
            kind, fid = "figure", f"FIG{fi}"
        items.append({"kind": kind, "id": fid, "caption": cap_text, "src": src})
        marker = soup.new_tag("p")
        marker.string = f"[[{kind.upper()}:{fid}]]"
        fig.replace_with(marker)
    return items


def render(node, out):
    """把剩余 DOM 摊平成 markdown 风格文本（保留标题层级、段落、列表、pre）。"""
    for child in node.children:
        if isinstance(child, NavigableString):
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name
        if name in ("h1", "h2", "h3", "h4"):
            txt = clean(child.get_text(" ", strip=True))
            if txt:
                out.append("#" * int(name[1]) + " " + txt)
        elif name in ("h5", "h6"):  # LaTeXML 的 run-in 标题 / Abstract 等，降为粗体行
            txt = clean(child.get_text(" ", strip=True))
            if txt:
                out.append("**" + txt + "**")
        elif name == "p":
            txt = clean(child.get_text(" ", strip=True))
            if txt:
                out.append(txt)
        elif name == "pre":
            txt = child.get_text("\n", strip=True)
            if txt:
                out.append("```\n" + txt + "\n```")
        elif name in ("ul", "ol"):
            for li in child.find_all("li", recursive=False):
                txt = clean(li.get_text(" ", strip=True))
                if txt:
                    out.append(("- " if name == "ul" else "1. ") + txt)
        elif name == "table":  # 未包在 figure 里的散表：按行摊平
            for tr in child.find_all("tr"):
                cells = [clean(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
                cells = [c for c in cells if c]
                if cells:
                    out.append(" | ".join(cells))
        elif name in ("section", "div", "main", "article", "body", "aside",
                      "blockquote", "header", "footer", "span", "figure"):
            render(child, out)
        # 其余标签（svg、math 残壳等）忽略


def convert(html_path, out_dir):
    html = open(html_path, encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "noscript"]):
        t.decompose()
    body = soup.body or soup
    replace_math(body)
    items = collect_figures(body)
    out = []
    render(body, out)
    text = "\n\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    with open(os.path.join(out_dir, "text2.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    with open(os.path.join(out_dir, "index2.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    return len(text), items


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "D:/tmp/arxiv7"
    os.makedirs(root, exist_ok=True)
    for arxiv_id, ver in PAPERS:
        d = os.path.join(root, arxiv_id)
        os.makedirs(d, exist_ok=True)
        html_path = os.path.join(d, "paper.html")
        print(arxiv_id, f"({ver})")
        if os.path.exists(html_path) and os.path.getsize(html_path) > 20000:
            print("    HTML 已存在，跳过抓取")
        else:
            url = f"https://arxiv.org/html/{arxiv_id}{ver}"
            size = fetch(url, html_path)
            if not size:  # 版本号不存在则退回无版本 URL
                print(f"    {ver} 抓取失败，退回无版本 URL")
                size = fetch(f"https://arxiv.org/html/{arxiv_id}", html_path)
            print(f"    抓取 size={size}")
            if not size:
                print("    !! 抓取失败，稍后重跑本脚本")
                continue
        chars, items = convert(html_path, d)
        n_f = sum(1 for i in items if i["kind"] == "figure")
        n_t = sum(1 for i in items if i["kind"] == "table")
        print(f"    转换: text2.txt={chars} 字符, 图{n_f} 表{n_t}")
        time.sleep(3)
    print("\n完成。下一步：按 HANDOFF.md 派发译文。")


if __name__ == "__main__":
    main()
