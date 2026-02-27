#!/usr/bin/env python3
"""读取 章节/*.md 生成 dist/index.html"""
import os, re, glob, html as htmlmod

DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTER_DIR = os.path.join(DIR, "章节")
OUTPUT = os.path.join(DIR, "dist", "index.html")

def md_to_html(md_text):
    """简单 markdown -> HTML 转换"""
    lines = md_text.strip().split("\n")
    parts = []
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        # 标题
        if line.startswith("# "):
            parts.append(f"<h1>{process_inline(line[2:])}</h1>")
        elif line == "——" or line == "---" or line == "——":
            parts.append("<hr>")
        else:
            text = process_inline(line)
            # 判断是否需要缩进：以 ** 开头的系统提示、分隔线等不缩进
            if text.startswith("<strong>【") or text.startswith("**"):
                parts.append(f'<p class="ni">{text}</p>')
            else:
                parts.append(f"<p>{text}</p>")
    return "\n".join(parts)

def process_inline(text):
    """处理行内 markdown：**bold**"""
    text = htmlmod.escape(text)
    # 还原被转义的 markdown bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text

def parse_chapter_file(filepath):
    """解析章节文件，返回 (title, html_content)"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 去掉 "下章预告" 段落
    content = re.sub(r'\n下章预告：.*$', '', content, flags=re.DOTALL)

    # 提取标题
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    if title_match:
        full_title = title_match.group(1)
        # 从 "第XXX章 标题" 提取短标题
        short_match = re.match(r'第\d+章\s+(.+)', full_title)
        short_title = short_match.group(1) if short_match else full_title
    else:
        short_title = os.path.basename(filepath).replace(".md", "")
        full_title = short_title

    html_content = md_to_html(content)
    return short_title, html_content

def get_chapter_files():
    """获取排序后的章节文件列表"""
    files = glob.glob(os.path.join(CHAPTER_DIR, "第*章_*.md"))
    files.sort()
    return files

def build():
    files = get_chapter_files()
    if not files:
        print("没有找到章节文件！")
        return

    chapters = []
    for f in files:
        short_title, html_content = parse_chapter_file(f)
        # 提取章节号
        basename = os.path.basename(f)
        num_match = re.search(r'第(\d+)章', basename)
        num = num_match.group(1) if num_match else "?"
        chapters.append({
            "num": num,
            "title": short_title,
            "html": html_content,
        })

    total = len(chapters)

    # 生成侧栏项
    sidebar_items = []
    for i, ch in enumerate(chapters):
        sidebar_items.append(
            f'    <div class="chapter-item" data-ch="{i}">'
            f'<span class="num">{ch["num"]}</span>'
            f'<span>{htmlmod.escape(ch["title"])}</span></div>'
        )

    # 生成隐藏内容
    hidden_divs = []
    for i, ch in enumerate(chapters):
        hidden_divs.append(
            f'<div class="ch-data" id="ch-{i}" data-title="{htmlmod.escape(ch["title"])}">\n'
            f'{ch["html"]}\n</div>'
        )

    html = TEMPLATE.replace("{{SIDEBAR_ITEMS}}", "\n".join(sidebar_items))
    html = html.replace("{{HIDDEN_CHAPTERS}}", "\n\n".join(hidden_divs))
    html = html.replace("{{TOTAL_CH}}", str(total))

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"生成 {total} 章 -> {OUTPUT}")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>重生2008：记忆贩卖者</title>
<style>
  :root {
    --bg: #f5f0e8;
    --text: #2c2416;
    --sidebar-bg: #ede6d8;
    --sidebar-hover: #ddd4c2;
    --sidebar-active: #c9bfad;
    --accent: #8b6914;
    --border: #d4cbb8;
    --reading-width: 700px;
  }
  [data-theme="dark"] {
    --bg: #1a1a1a;
    --text: #d4c9b8;
    --sidebar-bg: #222222;
    --sidebar-hover: #2d2d2d;
    --sidebar-active: #383838;
    --accent: #c4973a;
    --border: #333;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: "Songti SC", "Noto Serif SC", "Source Han Serif CN", serif;
    background: var(--bg);
    color: var(--text);
    transition: background 0.3s, color 0.3s;
    overflow: hidden;
    height: 100vh;
  }
  .sidebar {
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 260px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    z-index: 10;
    transition: transform 0.3s ease, background 0.3s;
  }
  .sidebar.collapsed { transform: translateX(-260px); }
  .sidebar-header {
    padding: 24px 20px 16px;
    border-bottom: 1px solid var(--border);
  }
  .sidebar-header h1 {
    font-size: 20px;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: 2px;
  }
  .sidebar-header .subtitle {
    font-size: 12px;
    color: var(--text);
    opacity: 0.5;
    margin-top: 4px;
  }
  .chapter-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
  }
  .chapter-list::-webkit-scrollbar { width: 4px; }
  .chapter-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
  .chapter-item {
    padding: 10px 20px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .chapter-item:hover { background: var(--sidebar-hover); }
  .chapter-item.active { background: var(--sidebar-active); font-weight: 600; }
  .chapter-item .num {
    font-size: 11px;
    opacity: 0.4;
    min-width: 24px;
  }
  .main {
    margin-left: 260px;
    height: 100vh;
    display: flex;
    flex-direction: column;
    transition: margin-left 0.3s ease;
  }
  .main.expanded { margin-left: 0; }
  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    flex-shrink: 0;
  }
  .toolbar-left, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .toolbar button {
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    transition: background 0.15s;
  }
  .toolbar button:hover { background: var(--sidebar-hover); }
  .toolbar .chapter-title {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
  }
  .font-size-control {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    opacity: 0.7;
  }
  .font-size-control button {
    width: 28px;
    height: 28px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }
  .reading-area {
    flex: 1;
    overflow-y: auto;
    scroll-behavior: smooth;
  }
  .reading-area::-webkit-scrollbar { width: 6px; }
  .reading-area::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  .content {
    max-width: var(--reading-width);
    margin: 0 auto;
    padding: 40px 24px 80px;
    line-height: 2;
    font-size: 18px;
  }
  .content h1 {
    text-align: center;
    font-size: 24px;
    margin-bottom: 32px;
    letter-spacing: 2px;
    color: var(--accent);
  }
  .content p {
    text-indent: 2em;
    margin-bottom: 0.6em;
  }
  .content p.ni { text-indent: 0; }
  .content hr {
    border: none;
    height: 1px;
    background: var(--border);
    margin: 28px 0;
  }
  .content strong {
    color: var(--accent);
    font-weight: 600;
  }
  .chapter-nav {
    display: flex;
    justify-content: center;
    gap: 16px;
    padding: 32px 0;
    margin-top: 20px;
    border-top: 1px solid var(--border);
  }
  .chapter-nav button {
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 28px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-family: inherit;
    transition: background 0.15s;
  }
  .chapter-nav button:hover { background: var(--sidebar-hover); }
  .chapter-nav button:disabled { opacity: 0.3; cursor: default; }
  .progress-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--border);
    z-index: 100;
  }
  .progress-bar .fill {
    height: 100%;
    background: var(--accent);
    width: 0;
    transition: width 0.15s;
  }
  .ch-data { display: none; }
  @media (max-width: 768px) {
    .sidebar { width: 240px; transform: translateX(-240px); }
    .sidebar.open { transform: translateX(0); }
    .main { margin-left: 0 !important; }
    .content { padding: 24px 16px 60px; }
    .overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.3);
      z-index: 5;
    }
    .overlay.show { display: block; }
  }
</style>
</head>
<body>

<div class="progress-bar"><div class="fill" id="progressFill"></div></div>
<div class="overlay" id="overlay"></div>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h1>重生2008</h1>
    <div class="subtitle">记忆贩卖者</div>
  </div>
  <div class="chapter-list" id="chapterList">
{{SIDEBAR_ITEMS}}
  </div>
</aside>

<main class="main" id="main">
  <div class="toolbar">
    <div class="toolbar-left">
      <button id="toggleSidebar" title="切换目录">&#9776;</button>
      <span class="chapter-title" id="toolbarTitle"></span>
    </div>
    <div class="toolbar-right">
      <div class="font-size-control">
        <button id="fontDec">&minus;</button>
        <span id="fontLabel">18</span>
        <button id="fontInc">+</button>
      </div>
      <button id="themeToggle" title="切换主题">&#127769;</button>
    </div>
  </div>
  <div class="reading-area" id="readingArea">
    <div class="content" id="content">
      <div id="welcomeScreen" style="text-align:center;padding:100px 0;opacity:0.4;">
        <p style="text-indent:0;font-size:42px;letter-spacing:6px;color:var(--accent);">重生2008</p>
        <p style="text-indent:0;font-size:18px;margin-top:8px;letter-spacing:4px;opacity:0.6;">记忆贩卖者</p>
        <p style="text-indent:0;margin-top:24px;">&larr; 请从目录选择章节开始阅读</p>
      </div>
    </div>
  </div>
</main>

<!-- 章节内容 -->
{{HIDDEN_CHAPTERS}}

<script>
var totalCh = {{TOTAL_CH}};
var currentCh = -1;
var fontSize = 18;
var isDark = false;

document.querySelectorAll('.chapter-item').forEach(function(el) {
  el.addEventListener('click', function() {
    loadChapter(parseInt(this.getAttribute('data-ch')));
  });
});

function loadChapter(idx) {
  currentCh = idx;
  var src = document.getElementById('ch-' + idx);
  var contentEl = document.getElementById('content');
  var welcome = document.getElementById('welcomeScreen');
  if (welcome) welcome.style.display = 'none';

  var html = src.innerHTML;
  html += '<div class="chapter-nav">';
  if (idx > 0) {
    html += '<button onclick="loadChapter(' + (idx - 1) + ')">上一章</button>';
  } else {
    html += '<button disabled>上一章</button>';
  }
  if (idx < totalCh - 1) {
    html += '<button onclick="loadChapter(' + (idx + 1) + ')">下一章</button>';
  } else {
    html += '<button disabled>下一章</button>';
  }
  html += '</div>';

  contentEl.innerHTML = html;
  contentEl.style.fontSize = fontSize + 'px';
  document.getElementById('toolbarTitle').textContent = src.getAttribute('data-title');

  document.querySelectorAll('.chapter-item').forEach(function(el, i) {
    el.classList.toggle('active', i === idx);
  });

  document.getElementById('readingArea').scrollTop = 0;

  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('show');
  }
}

document.getElementById('toggleSidebar').addEventListener('click', function() {
  var sb = document.getElementById('sidebar');
  var ov = document.getElementById('overlay');
  var mn = document.getElementById('main');
  if (window.innerWidth <= 768) {
    sb.classList.toggle('open');
    ov.classList.toggle('show');
  } else {
    sb.classList.toggle('collapsed');
    mn.classList.toggle('expanded');
  }
});

document.getElementById('overlay').addEventListener('click', function() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('show');
});

document.getElementById('fontInc').addEventListener('click', function() {
  if (fontSize < 28) { fontSize += 2; applyFont(); }
});
document.getElementById('fontDec').addEventListener('click', function() {
  if (fontSize > 14) { fontSize -= 2; applyFont(); }
});
function applyFont() {
  document.getElementById('content').style.fontSize = fontSize + 'px';
  document.getElementById('fontLabel').textContent = fontSize;
}

document.getElementById('themeToggle').addEventListener('click', function() {
  isDark = !isDark;
  document.body.setAttribute('data-theme', isDark ? 'dark' : '');
  this.textContent = isDark ? '\u2600\uFE0F' : '\uD83C\uDF19';
});

document.getElementById('readingArea').addEventListener('scroll', function() {
  var el = this;
  var pct = el.scrollTop / (el.scrollHeight - el.clientHeight) * 100;
  document.getElementById('progressFill').style.width = Math.min(100, pct) + '%';
});
</script>
</body>
</html>'''

if __name__ == "__main__":
    build()
