// 用 jsdom 实测发布页的「复制到公众号」路径：验证复制出的 HTML
// 不含 <img>、含 5 个占位框、无 {{IMG:}} 字面量、无非法 <p><section> 嵌套、标签平衡。
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const FILE = path.join(__dirname, "第6篇_发布版_带复制按钮.html");
const html = fs.readFileSync(FILE, "utf8");

let captured = null;
let capturedText = null;

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  beforeParse(window) {
    window.ClipboardItem = function (items) { this.items = items; };
    Object.defineProperty(window.navigator, "clipboard", {
      value: {
        write: (arr) => {
          const item = arr[0];
          const blob = item.items["text/html"];
          captured = blob;
          return Promise.resolve();
        },
        writeText: (t) => { capturedText = t; return Promise.resolve(); },
      },
      configurable: true,
    });
  },
});

setTimeout(async () => {
  const btn = dom.window.document.getElementById("copyRich");
  if (!btn) { console.log("✗ 找不到 #copyRich 按钮"); process.exit(1); }
  btn.dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true }));

  await new Promise((r) => setTimeout(r, 300));

  if (!captured) { console.log("✗ 未捕获到剪贴板 HTML"); process.exit(1); }
  const out = await captured.text();

  const count = (re) => (out.match(re) || []).length;
  const bal = (tag) => [count(new RegExp(`<${tag}[\\s>]`, "g")), count(new RegExp(`</${tag}>`, "g"))];

  console.log("复制出的 HTML 长度:", out.length);
  console.log("  <img> 残留        :", count(/<img\b/g), "(应为 0)");
  console.log("  占位框            :", count(/在此处插入图片/g), "(应为 5)");
  console.log("  {{IMG: 字面量     :", count(/\{\{IMG:/g), "(应为 0)");
  console.log("  data:image 残留   :", count(/data:image/g), "(应为 0)");
  console.log("  非法 <p><section> :", count(/<p[^>]*><section/g), "(应为 0)");
  for (const t of ["p", "section", "table", "tr", "td", "div"]) {
    const [o, c] = bal(t);
    console.log(`  <${t}> 开/闭       : ${o}/${c} ${o === c ? "✓" : "✗ 不平衡"}`);
  }
  console.log("  纯文本长度        :", capturedText ? capturedText.length : "(未走纯文本分支)");

  const pass =
    count(/<img\b/g) === 0 &&
    count(/在此处插入图片/g) === 5 &&
    count(/\{\{IMG:/g) === 0 &&
    count(/data:image/g) === 0 &&
    count(/<p[^>]*><section/g) === 0 &&
    ["p", "section", "table", "tr", "td", "div"].every((t) => bal(t)[0] === bal(t)[1]);
  console.log(pass ? "\n✓ 复制路径通过" : "\n✗ 复制路径有问题");
  process.exit(pass ? 0 : 1);
}, 1200);
