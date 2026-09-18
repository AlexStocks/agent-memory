#!/usr/bin/env python3
"""把 第6篇_模板.html 导出为 markdown 版（第6篇_公众号正文.md）。

模板 markup 规整（同一套内联样式），按样式特征分派：
- 编号大节（badge span + h3）        -> ## 01 · 标题
- run-in 小标题（p, font-weight:800） -> ### 标题
- 引用框（border-left:4px solid …）  -> > 行
- 图片占位（{{IMG:key}}）            -> > 【图 N · 待插入】（文件名从 build_publish_page6.py 的 IMG_MAP 解析）
- 表格                              -> markdown 表
- <strong>/<em>                     -> **…** / *…*
"""
import io
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "第6篇_模板.html"
OUT = HERE.parent / "第6篇_公众号正文.md"
BUILDER = HERE.parent / "build_publish_page6.py"

# 从构建脚本解析 IMG_MAP：key -> (文件, 图号, 副标题)
builder_src = BUILDER.read_text(encoding="utf-8")
IMG_MAP = {
    m.group(1): (m.group(2), m.group(3), m.group(4))
    for m in re.finditer(r'"(img\d)":\s*\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', builder_src)
}


def inline(el) -> str:
    """递归拼接行内文本，strong -> **x**，em -> *x*。"""
    out = []
    for node in el.children:
        if isinstance(node, NavigableString):
            out.append(str(node))
        elif node.name in ("strong", "b"):
            inner = inline(node).strip()
            if inner:
                out.append(f"**{inner}**")
        elif node.name in ("em", "i"):
            inner = inline(node).strip()
            if inner:
                out.append(f"*{inner}*")
        elif node.name == "br":
            out.append(" ")
        else:
            out.append(inline(node))
    text = "".join(out)
    return re.sub(r"\s+", " ", text).strip()


def render_table(el) -> list[str]:
    lines = []
    headers = [inline(th) for th in el.find_all("th")]
    if headers:
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "---|" * len(headers))
    for tr in el.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells = [inline(td).replace("|", "／") for td in tds]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def render_block(node) -> list[str]:
    """把一个块级节点转成 markdown 行列表。"""
    if isinstance(node, NavigableString):
        return []
    if not isinstance(node, Tag):
        return []
    style = node.get("style", "")
    name = node.name

    if name == "p":
        text = inline(node)
        if not text:
            return []
        if "font-weight:800" in style and "border-left" in style:  # run-in 小标题
            return ["", "### " + text, ""]
        if text.startswith("图："):  # 图注
            return ["", "*" + text + "*", ""]
        return ["", text, ""]

    if name in ("h3", "h4"):
        text = inline(node)
        if text == "参考文档":
            return ["", "## " + text, ""]
        return ["", "### " + text, ""]

    if name in ("ul", "ol"):
        lines = [""]
        for i, li in enumerate(node.find_all("li", recursive=False), 1):
            bullet = "- " if name == "ul" else f"{i}. "
            lines.append(bullet + inline(li))
        lines.append("")
        return lines

    if name == "table":
        return [""] + render_table(node) + [""]

    if name == "section":
        if "{{IMG:" in str(node) and node.find("img"):  # 图片占位
            img = node.find("img")
            m = re.search(r"\{\{IMG:(img\d)\}\}", img.get("src", ""))
            if m and m.group(1) in IMG_MAP:
                fname, label, sub = IMG_MAP[m.group(1)]
                return ["", f"> 【{label} · 待插入】{sub}", f"> （文件：`{fname}`）", ""]
            return ["", "> 【图片 · 待插入】", ""]
        if "border-left:4px solid" in style and "rgb(214,211,209)" in style:  # 引用框
            lines = [""]
            for p in node.find_all("p"):
                if inline(p):
                    lines.append("> " + inline(p))
            lines.append("")
            return lines
        lines = []
        for child in node.children:
            lines.extend(render_block(child))
        return lines

    # 其余容器（div 等）递归
    lines = []
    for child in node.children:
        lines.extend(render_block(child))
    return lines


def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    out = ["# Agent Memory 技术综述：有界召回篇", ""]

    wrapper = soup.find("section")  # 全文包裹层
    for child in wrapper.children:
        if not isinstance(child, Tag):
            continue
        badge = child.find("span", string=re.compile(r"^\d{2}$")) if child.name == "section" else None
        if badge and child.find("h3"):  # 编号大节
            label_p = badge.find_parent("section").find("p")
            label = inline(label_p) if label_p else ""
            title = inline(child.find("h3"))
            out.append("")
            out.append(f"## {badge.get_text(strip=True)} · {title}")
            if label:
                out.append(f"*{label}*")
            out.append("")
            header_inner = badge.find_parent("section")
            header_top = header_inner
            while header_top.parent is not child:
                header_top = header_top.parent
            for sub in child.children:
                if sub is header_top:
                    continue
                out.extend(render_block(sub))
        else:
            out.extend(render_block(child))

    md = "\n".join(out)
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    io.open(OUT, "w", encoding="utf-8").write(md)
    print(f"已生成 {OUT.name}: {len(md)} 字符, {md.count(chr(10))} 行")
    print("大节数:", len(re.findall(r"^## \d", md, re.M)), "| 小节数:", len(re.findall(r"^### ", md, re.M)),
          "| 表格数:", md.count("|---"))


if __name__ == "__main__":
    main()
