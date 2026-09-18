#!/usr/bin/env python3
"""把 第6篇_公众号正文.md 转成含 {{IMG:key}} 的 第6篇_模板.html。

md 是唯一可编辑源；本脚本负责把它渲染成公众号用的内联样式 HTML，
再由 build_publish_page6.py 生成「可直贴正文」与「发布预览页」。

支持的 md 语法：# / ## NN · 标题 / ### 小节 / 段落 / - 与 1. 列表 /
表格 / > 引用框 / ``` 代码块 / **粗** / *斜* / `行内码` / > 【图 N · 待插入】图位。
图位按出现顺序映射为 {{IMG:img1}}、{{IMG:img2}}…（与 build_publish_page6.py 的 IMG_MAP 对应）。
"""
import io
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "第6篇_公众号正文.md"
OUT = HERE.parent / "第6篇_模板.html"

WRAP = ('<section style="font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\','
        "\'Hiragino Sans GB\',\'Microsoft YaHei\',sans-serif;font-size:15px;line-height:1.8;"
        'color:rgb(55,65,81);letter-spacing:0.5px;text-align:justify;padding:0 10px;">')
P = ('<p style="margin:0 0 20px;font-size:15px;line-height:1.8;color:rgb(55,65,81);'
     'letter-spacing:0.5px;text-align:justify;">')
RUNIN = ('<p style="font-size:15px;font-weight:800;color:rgb(28,25,23);margin:28px 0 14px;'
         'padding-left:10px;border-left:3px solid rgb(220,38,38);line-height:1.4;'
         'letter-spacing:0.5px;">')
QUOTE = ('<section style="border-left:4px solid rgb(214,211,209);padding:14px 20px;'
         'margin:0 0 24px;background:rgb(250,250,250);">')
QP = '<p style="margin:0 0 8px;font-size:14px;line-height:1.85;color:rgb(55,65,81);text-align:justify;">'
PRE = ('<pre style="background:rgb(247,249,252);border:1px solid #E1E6EE;border-radius:8px;'
       'padding:14px 16px;margin:0 0 24px;font-size:13px;line-height:1.75;overflow-x:auto;'
       'color:rgb(55,65,81);font-family:Menlo,Consolas,monospace;">')
UL = ('<ul style="box-sizing:border-box;margin:0.8em 0;padding-left:25px;color:rgb(51,51,51);'
      'font-size:15px;font-weight:400;letter-spacing:normal;line-height:1.8;list-style-type:disc;">')
OL = ('<ol style="box-sizing:border-box;margin:0.8em 0;padding-left:30px;color:rgb(51,51,51);'
      'font-size:15px;font-weight:400;letter-spacing:normal;line-height:1.8;">')
TABLE = '<section style="margin-bottom:24px;overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;">'
TH = ('<th style="background:rgb(220,38,38);color:rgb(255,255,255);font-weight:700;'
      'padding:8px 12px;text-align:left;">')
TD = ('<td style="padding:8px 12px;border-bottom:1px solid rgb(254,226,226);color:rgb(55,65,81);">')
TD_ALT = ('<td style="padding:8px 12px;border-bottom:1px solid rgb(254,226,226);'
          'color:rgb(55,65,81);background:rgb(254,242,242);">')


def inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`",
                  r'<code style="background:rgb(240,243,248);padding:1px 5px;border-radius:4px;'
                  r'font-size:13px;color:rgb(44,74,124);">\1</code>', text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    return text


def render_table(rows: list[str]) -> str:
    cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    out = [TABLE, "<thead><tr>" + "".join(TH + inline(c) + "</th>" for c in cells) + "</tr></thead><tbody>"]
    for i, row in enumerate(rows[2:]):
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        td = TD if i % 2 == 0 else TD_ALT
        out.append("<tr>" + "".join(td + inline(c) + "</td>" for c in cells) + "</tr>")
    out.append("</tbody></table></section>")
    return "".join(out)


def section_header(num: str, label: str, title: str) -> str:
    badge = (f'<span style="display:inline-block;background:rgb(220,38,38);color:rgb(255,255,255);'
             f'font-size:18px;font-weight:900;padding:4px 14px;border-radius:6px;margin-right:14px;'
             f'line-height:1.3;">{num}</span>')
    label_html = (f'<p style="font-size:10px;color:rgb(220,38,38);font-weight:700;letter-spacing:3px;'
                  f'margin:0 0 2px;text-transform:uppercase;">{label}</p>' if label else "")
    return (
        '<section style="margin-top:48px;margin-bottom:28px;padding:0 10px;">'
        '<section style="display:flex;align-items:center;justify-content:space-between;'
        'margin-bottom:20px;padding-bottom:14px;border-bottom:3px solid rgb(220,38,38);">'
        '<section style="display:flex;align-items:center;">' + badge +
        f'<section>{label_html}<h3 style="font-size:18px;font-weight:800;color:rgb(28,25,23);'
        f'margin:0;letter-spacing:0.5px;line-height:1.4;">{inline(title)}</h3></section>'
        '</section></section>'
    )


def main():
    lines = SRC.read_text(encoding="utf-8").split("\n")
    out, i, fig_no, open_section = [], 0, 0, False
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):  # 代码块
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i].replace("&", "&amp;").replace("<", "&lt;"))
                i += 1
            i += 1
            out.append(PRE + "\n".join(buf) + "</pre>")
            continue

        if stripped.startswith("|"):  # 表格
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            out.append(render_table(rows))
            continue

        m = re.match(r"^## (\d{2}) · (.+)$", stripped)  # 编号大节
        if m:
            if open_section:
                out.append("</section>")
            label = ""
            if i + 1 < len(lines) and re.match(r"^\*[^*]+\*$", lines[i + 1].strip()):
                label = lines[i + 1].strip().strip("*")
                i += 1
            out.append(section_header(m.group(1), label, m.group(2)))
            open_section = True
            i += 1
            continue

        if stripped.startswith("## "):  # 无编号大节（参考文档）
            if open_section:
                out.append("</section>")
            out.append('<section style="margin-top:48px;margin-bottom:28px;padding:0 10px;">'
                       '<h3 style="margin:0 0 15px;padding:0;font-weight:bold;color:#000;'
                       f'font-size:20px;">{inline(stripped[3:])}</h3>')
            open_section = True
            i += 1
            continue

        if stripped.startswith("# "):  # 文章标题
            out.append('<p style="font-size:21px;font-weight:800;color:rgb(28,25,23);'
                       f'margin:0 0 24px;line-height:1.5;letter-spacing:0.5px;">{inline(stripped[2:])}</p>')
            i += 1
            continue

        if stripped.startswith("### "):  # run-in 小标题
            out.append(RUNIN + inline(stripped[4:]) + "</p>")
            i += 1
            continue

        if stripped.startswith("> "):  # 引用框 / 图位
            buf = []
            while i < len(lines) and (lines[i].strip().startswith(">") or not lines[i].strip()):
                if not lines[i].strip():
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                        buf.append("")
                        i += 1
                        continue
                    break
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            text = "\n".join(buf).strip()
            fm = re.match(r"【图 (\d+) · 待插入】(.+)", text.split("\n")[0])
            if fm:  # 图位 -> {{IMG:}}
                fig_no += 1
                sub = fm.group(2)
                out.append('<section style="text-align:center;">'
                           f'<img src="{{{{IMG:img{fig_no}}}}}" data-ph-sub="{sub}" '
                           f'style="max-width:100%;" alt="{sub}"></section>')
            else:
                paras = [p for p in text.split("\n") if p.strip()]
                out.append(QUOTE + "".join(QP + inline(p) + "</p>" for p in paras) + "</section>")
            continue

        if re.match(r"^[-*] ", stripped):  # 无序列表
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i].strip()):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append(UL + "".join(f'<li style="margin-bottom:6px;">{inline(x)}</li>' for x in items) + "</ul>")
            continue

        if re.match(r"^\d+\. ", stripped):  # 有序列表
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                items.append(re.sub(r"^\d+\. ", "", lines[i].strip()))
                i += 1
            out.append(OL + "".join(f'<li style="margin-bottom:6px;">{inline(x)}</li>' for x in items) + "</ol>")
            continue

        out.append(P + inline(stripped) + "</p>")
        i += 1

    if open_section:
        out.append("</section>")

    html = WRAP + "\n" + "\n".join(out) + "\n</section>\n"
    OUT.write_text(html, encoding="utf-8")
    print(f"已生成 {OUT.name}: {len(html)} 字符")
    print("大节数:", len(re.findall(r'margin-top:48px', html)),
          "| run-in:", len(re.findall(r'border-left:3px solid rgb\(220,38,38\)', html)),
          "| 表格:", html.count("<table"),
          "| 图位:", len(re.findall(r'\{\{IMG:', html)))


if __name__ == "__main__":
    main()
