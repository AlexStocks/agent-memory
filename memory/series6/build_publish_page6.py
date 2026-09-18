#!/usr/bin/env python3
"""从 第6篇_模板.html 生成两个产物。

1. 第6篇_公众号正文.html —— 可直贴的正文：图片位置替换为占位框（不是 {{IMG:}} 字面量），
   在浏览器打开全选复制即可粘进公众号，再按占位框提示逐张插图。
2. 第6篇_发布版_带复制按钮.html —— 本地预览页：渲染真实图片供预览，
   复制到剪贴板时把 <img> 换成同样的占位框，避免把 file:// 地址粘进公众号（微信抓不到会裂图）。

与第 4、5 篇同一套路。
"""
import base64
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "第6篇_模板.html"          # 含 {{IMG:key}} 的源模板
BODY = HERE / "第6篇_公众号正文.html"        # 产物 1：可直贴正文
OUT = HERE / "第6篇_发布版_带复制按钮.html"   # 产物 2：预览页

# 占位符 key -> (显示用图片路径, 占位框标题, 占位框副标题)
IMG_MAP = {
    "img1": ("publish_images/图1_再获取成本.png", "图 1", "压缩后的再获取成本：完成度没掉，检索调用翻了三倍"),
    "img2": ("publish_images/图2_事件级扩展.png", "图 2", "查询时沿事件线索扩展：补回缺失的支撑证据"),
}

article = TEMPLATE.read_text(encoding="utf-8")


def ph_box(label: str, sub: str, fname: str = "") -> str:
    """占位框。与发布页复制时所用的 PH_BOX 保持像素级一致，两条路径观感统一。"""
    extra = (
        f'<p style="margin:6px 0 0;font-size:12px;color:#B0B8C6;line-height:1.6;">'
        f"待插入文件：{fname}</p>"
        if fname
        else ""
    )
    return (
        '<section style="border:1px dashed #B9C4D4;border-radius:8px;background:#F7F9FC;'
        'padding:22px 16px;margin:6px 0;text-align:center;">'
        '<p style="margin:0 0 4px;font-size:14px;font-weight:600;color:#46536B;line-height:1.6;">'
        f"【{label} · 在此处插入图片】</p>"
        f'<p style="margin:0;font-size:12px;color:#8A94A6;line-height:1.6;">{sub}</p>'
        f"{extra}</section>"
    )


def data_uri(path: str) -> str:
    """把图片内嵌为 data URI，保证页面脱离目录也能正常显示。"""
    p = HERE / path
    mime = "image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(p.read_bytes()).decode("ascii"))


def to_preview(m: re.Match) -> str:
    key = m.group(1)
    path, label, sub = IMG_MAP[key]
    return (
        f'src="{data_uri(path)}" data-ph="{label}" data-ph-sub="{sub}" '
        f'alt="{label} {sub}"'
    )


def to_body(m: re.Match) -> str:
    """把整个 <section><img …></section> 换成占位框，避免产出 <section><section> 非法嵌套。"""
    key = m.group(1)
    path, label, sub = IMG_MAP[key]
    return ph_box(label, sub, Path(path).name)


# 产物 1：可直贴正文。img 外层是 <section style="text-align:center;">，整块替换。
body_html, n_body = re.subn(
    r'<section style="text-align:center;"><img src="\{\{IMG:([a-z0-9-]+)\}\}"[^>]*></section>',
    to_body,
    article,
)
assert "{{IMG:" not in body_html, "正文仍有未替换的占位符"
BODY.write_text(body_html, encoding="utf-8")

# 产物 2：预览页
preview_html = re.sub(r'src="\{\{IMG:([a-z0-9-]+)\}\}"', to_preview, article)
assert "{{IMG:" not in preview_html, "仍有未替换的占位符"


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>第 6 篇《Agent Memory 技术综述：有界召回篇》· 复制用</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 0; background: #EDF0F4;
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  }
  .toolbar {
    position: sticky; top: 0; z-index: 99;
    background: #FFFFFF; border-bottom: 1px solid #E1E6EE;
    padding: 16px 20px; box-shadow: 0 2px 10px rgba(20,40,80,.06);
  }
  .toolbar-inner { max-width: 1040px; margin: 0 auto; }
  .toolbar h1 { margin: 0 0 4px; font-size: 17px; color: #1F2D3D; font-weight: 700; }
  .toolbar .sub { margin: 0 0 14px; font-size: 13px; color: #7A8496; line-height: 1.6; }
  .btns { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
  button {
    font-family: inherit; font-size: 14px; font-weight: 600;
    padding: 10px 22px; border-radius: 8px; border: none; cursor: pointer;
    transition: background .15s, transform .05s;
  }
  button:active { transform: translateY(1px); }
  #copyRich { background: #07C160; color: #fff; box-shadow: 0 2px 8px rgba(7,193,96,.28); }
  #copyRich:hover { background: #06AD56; }
  #copyPlain { background: #EEF1F6; color: #46536B; }
  #copyPlain:hover { background: #E2E7EF; }
  #status { font-size: 13px; font-weight: 600; margin-left: 4px; }
  .ok { color: #07A253; }
  .err { color: #C0392B; }

  .layout { max-width: 1040px; margin: 0 auto; padding: 24px 20px 80px;
            display: flex; gap: 28px; align-items: flex-start; }

  .side { width: 340px; flex: none; }
  .card { background: #fff; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;
          border: 1px solid #E4E9F0; }
  .card h2 { margin: 0 0 12px; font-size: 14px; color: #1F2D3D; font-weight: 700; }
  .steps { margin: 0; padding-left: 20px; font-size: 13px; line-height: 2; color: #5A6474; }
  .steps li { margin-bottom: 4px; }
  .steps code, .map code { background: #F0F3F8; padding: 1px 5px; border-radius: 4px;
                           font-size: 12px; color: #2C4A7C; }
  .map { width: 100%; border-collapse: collapse; font-size: 12.5px; }
  .map td { padding: 7px 0; border-bottom: 1px dashed #E4E9F0; color: #5A6474; vertical-align: top; }
  .map tr:last-child td { border-bottom: none; }
  .map td:first-child { color: #1F2D3D; font-weight: 600; width: 54px; white-space: nowrap; }
  .warn { background: #FFF8E8; border: 1px solid #F5E0B8; border-radius: 8px;
          padding: 11px 13px; font-size: 12.5px; line-height: 1.75; color: #7A5C1E; margin-top: 12px; }
  .warn strong { color: #A8741A; }

  .phone-wrap { flex: 1; display: flex; justify-content: center; }
  .phone { width: 414px; background: #fff; border-radius: 14px;
           border: 1px solid #DDE3EB; box-shadow: 0 6px 26px rgba(20,40,80,.10);
           overflow: hidden; }
  .phone-bar { background: #F7F9FC; border-bottom: 1px solid #E8EDF4; padding: 9px 14px;
               font-size: 12px; color: #8A94A6; }
  #article { padding: 20px 18px 34px; }
  #article img { max-width: 100% !important; }
</style>
</head>
<body>

<div class="toolbar">
  <div class="toolbar-inner">
    <h1>第 6 篇《Agent Memory 技术综述：有界召回篇》· 公众号发布版</h1>
    <p class="sub">点「复制到公众号」，然后到公众号编辑器里 <b>Cmd+V</b> 粘贴。样式会保留，图片位置留成占位框，由你手工插图。</p>
    <div class="btns">
      <button id="copyRich">复制到公众号</button>
      <button id="copyPlain">复制纯文本</button>
      <span id="status"></span>
    </div>
  </div>
</div>

<div class="layout">
  <div class="side">
    <div class="card">
      <h2>操作步骤</h2>
      <ol class="steps">
        <li>点上方 <b>复制到公众号</b></li>
        <li>打开公众号后台 → 新建图文 → 正文区 <b>Cmd+V</b></li>
        <li>逐个选中灰色占位框，点工具栏 <b>图片 → 从本地上传</b>，按右侧对照表选文件</li>
        <li>粘贴后检查：表格有没有挤、小标题分隔线是否正常</li>
      </ol>
    </div>
    <div class="card">
      <h2>图片对照表</h2>
      <table class="map">
        <tr><td>图 1</td><td>压缩后的再获取成本<br><code>图1_再获取成本.png</code><br>取自 CompressionCost Figure 2</td></tr>
        <tr><td>图 2</td><td>查询时事件级扩展<br><code>图2_事件级扩展.png</code><br>取自 RippleMem Figure 2</td></tr>
      </table>
      <p style="margin:10px 0 0;font-size:12px;line-height:1.7;color:#8A94A6;">
        文件在 <code>publish_images/</code>，已统一压到 1280px 宽以内。<br>
        旧版五张图（记忆树工作流 / 记忆投毒 / StructMem 结构 / 压缩锯齿 / KV 轨迹）随正文改版停用，仍留在目录里备用。
      </p>
      <div class="warn">
        <strong>图 2 的手机端风险</strong><br>
        该图英文小字密集（原图 2048px 宽，已压到 1280px），手机上只看得到结构；图注已引导读者看结论，细节留给原文。
      </div>
    </div>
    <div class="card">
      <h2>发布前还要配三处</h2>
      <p style="margin:0;font-size:12.5px;line-height:1.85;color:#5A6474;">
        · <b>标题</b> → <code>Agent Memory 技术综述：有界召回篇</code><br>
        · <b>阅读原文</b> → <code>github.com/AlexStocks/agent-memory</code><br>
        · <b>话题标签</b> → <code>#AgentMemory技术综述</code>（建议前五篇也补挂）<br>
        · <b>同期论文译文</b> → 仓库 <code>starting/第06篇_有界召回篇/</code>（S/A 级七篇，正文 5.4 节口播可提）
      </p>
    </div>
  </div>

  <div class="phone-wrap">
    <div class="phone">
      <div class="phone-bar">414px 宽 · 模拟手机阅读效果</div>
      <div id="article">
__ARTICLE__
      </div>
    </div>
  </div>
</div>

<script>
(function () {
  var PH_BOX = function (label, sub) {
    return '<section style="border:1px dashed #B9C4D4;border-radius:8px;background:#F7F9FC;' +
           'padding:22px 16px;margin:6px 0;text-align:center;">' +
           '<p style="margin:0 0 4px;font-size:14px;font-weight:600;color:#46536B;line-height:1.6;">' +
           '【' + label + ' · 在此处插入图片】</p>' +
           '<p style="margin:0;font-size:12px;color:#8A94A6;line-height:1.6;">' + sub + '</p>' +
           '</section>';
  };

  function buildHTML() {
    var clone = document.getElementById('article').cloneNode(true);
    Array.prototype.forEach.call(clone.querySelectorAll('img[data-ph]'), function (img) {
      var box = document.createElement('div');
      box.innerHTML = PH_BOX(img.getAttribute('data-ph'), img.getAttribute('data-ph-sub'));
      var ph = box.firstChild;
      var host = img.parentNode;
      // 图片外层是 <p> 或 <section>，若该容器只包这一张图就连同容器一起换掉，
      // 否则会产出 <p><section>…</section></p> 这种非法嵌套，微信解析会错乱。
      if (host && (host.tagName === 'P' || host.tagName === 'SECTION') && host.querySelectorAll('img').length === 1) {
        host.parentNode.replaceChild(ph, host);
      } else {
        host.replaceChild(ph, img);
      }
    });
    return clone.innerHTML;
  }

  // 少数环境（如无头 DOM）不实现 innerText，做一次兜底
  function articleText() {
    var el = document.getElementById('article');
    return el.innerText || el.textContent || '';
  }

  function setStatus(msg, cls) {
    var el = document.getElementById('status');
    el.textContent = msg;
    el.className = cls || '';
    if (cls === 'ok') setTimeout(function () { el.textContent = ''; }, 4000);
  }

  function legacyCopy(html, text) {
    var holder = document.createElement('div');
    holder.setAttribute('style', 'position:fixed;left:-99999px;top:0;white-space:normal;');
    holder.innerHTML = html;
    document.body.appendChild(holder);
    var range = document.createRange();
    range.selectNodeContents(holder);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    sel.removeAllRanges();
    document.body.removeChild(holder);
    return ok;
  }

  document.getElementById('copyRich').addEventListener('click', function () {
    var html = buildHTML();
    var text = articleText();
    if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
      var item = new ClipboardItem({
        'text/html': new Blob([html], { type: 'text/html' }),
        'text/plain': new Blob([text], { type: 'text/plain' })
      });
      navigator.clipboard.write([item]).then(function () {
        setStatus('已复制富文本，去公众号 Cmd+V 粘贴', 'ok');
      }).catch(function () {
        var ok2 = legacyCopy(html, text);
        setStatus(ok2 ? '已复制富文本，去公众号 Cmd+V 粘贴' : '复制失败，请改用「复制纯文本」', ok2 ? 'ok' : 'err');
      });
    } else {
      var ok = legacyCopy(html, text);
      setStatus(ok ? '已复制富文本，去公众号 Cmd+V 粘贴' : '复制失败，请手动全选正文复制', ok ? 'ok' : 'err');
    }
  });

  document.getElementById('copyPlain').addEventListener('click', function () {
    var text = articleText();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        setStatus('已复制纯文本（无格式）', 'ok');
      }).catch(function () {
        var ok2 = legacyCopy('', text);
        setStatus(ok2 ? '已复制纯文本' : '复制失败', ok2 ? 'ok' : 'err');
      });
    } else {
      var ok = legacyCopy('', text);
      setStatus(ok ? '已复制纯文本' : '复制失败', ok ? 'ok' : 'err');
    }
  });
})();
</script>
</body>
</html>
"""

OUT.write_text(PAGE.replace("__ARTICLE__", preview_html), encoding="utf-8")
print(f"已生成: {BODY.name}  ({BODY.stat().st_size/1024:.0f} KB, {n_body} 个图位占位框)")
print(f"已生成: {OUT.name}  ({OUT.stat().st_size/1024:.0f} KB)")
