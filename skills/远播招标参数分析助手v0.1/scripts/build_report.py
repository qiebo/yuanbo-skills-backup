#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render a 标书拆解 report JSON into a self-contained HTML file.

Usage:
    python build_report.py <report.json> <output.html>

The CSS is embedded (copied from the reference sample reports) so the
output opens standalone in any browser and prints cleanly.
"""
import sys
import json
import html
import os

CSS = """
  :root{
    --bg:#f4f7fa;
    --card:#ffffff;
    --ink:#1f2937;
    --muted:#64748b;
    --line:#e2e8f0;
    --primary:#0e7490;
    --primary-soft:#e0f2f5;
    --accent:#0d9488;
    --warn:#dc2626;
    --warn-soft:#fef2f2;
    --amber:#b45309;
    --amber-soft:#fffbeb;
    --green:#15803d;
    --green-soft:#f0fdf4;
    --blue:#1d4ed8;
    --blue-soft:#eff6ff;
    --shadow:0 1px 3px rgba(15,23,42,.08),0 1px 2px rgba(15,23,42,.04);
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    background:var(--bg);color:var(--ink);line-height:1.65;font-size:15px;
  }
  header.top{
    position:sticky;top:0;z-index:50;background:rgba(255,255,255,.92);
    backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
  }
  .top-inner{max-width:1180px;margin:0 auto;padding:10px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
  .brand{font-weight:700;font-size:15px;color:var(--primary);white-space:nowrap;}
  .top nav{display:flex;gap:6px;flex-wrap:wrap;margin-left:auto;}
  .top nav a{
    text-decoration:none;color:var(--muted);font-size:13px;padding:6px 11px;border-radius:8px;transition:.15s;
  }
  .top nav a:hover{background:var(--primary-soft);color:var(--primary);}
  .hero{max-width:1180px;margin:28px auto 0;padding:0 24px;}
  .hero-card{
    background:linear-gradient(135deg,#0e7490 0%,#0d9488 100%);
    border-radius:18px;padding:30px 34px;color:#fff;box-shadow:0 10px 30px rgba(14,116,144,.25);
  }
  .hero-card .tag{display:inline-block;background:rgba(255,255,255,.18);padding:3px 12px;border-radius:999px;font-size:12px;letter-spacing:.5px;}
  .hero-card h1{margin:14px 0 6px;font-size:24px;line-height:1.35;}
  .hero-card .sub{opacity:.9;font-size:14px;}
  .hero-meta{display:flex;gap:26px;flex-wrap:wrap;margin-top:18px;}
  .hero-meta div{font-size:13px;opacity:.95;}
  .hero-meta b{display:block;font-size:18px;font-weight:700;margin-top:2px;}
  .wrap{max-width:1180px;margin:26px auto 60px;padding:0 24px;display:grid;grid-template-columns:1fr;gap:26px;}
  section.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 26px;box-shadow:var(--shadow);}
  .sec-head{display:flex;align-items:center;gap:12px;margin:0 0 16px;padding-bottom:12px;border-bottom:2px solid var(--primary-soft);}
  .sec-head .num{background:var(--primary);color:#fff;width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex:0 0 auto;}
  .sec-head h2{margin:0;font-size:18px;}
  .sec-head .hint{margin-left:auto;font-size:12px;color:var(--muted);}
  .facts{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px;}
  .fact{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
  .fact .k{font-size:12px;color:var(--muted);}
  .fact .v{font-size:15px;font-weight:600;margin-top:3px;word-break:break-word;}
  .fact .v.red{color:var(--warn);}
  .fact .v.green{color:var(--green);}
  .fact .v.blue{color:var(--blue);}
  .timeline{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;}
  .tl{border-left:3px solid var(--primary);background:var(--bg);border-radius:0 10px 10px 0;padding:12px 16px;}
  .tl .date{font-weight:700;color:var(--primary);font-size:14px;}
  .tl .ev{font-size:13px;color:var(--ink);margin-top:2px;}
  .tl .note{font-size:12px;color:var(--muted);margin-top:3px;}
  table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:6px;}
  th,td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top;}
  th{background:var(--primary-soft);color:#0c4a55;font-weight:600;}
  tbody tr:nth-child(even){background:#fafcfe;}
  .tbl-scroll{overflow-x:auto;}
  .callout{border-radius:10px;padding:14px 16px;margin:14px 0;font-size:14px;}
  .callout.warn{background:var(--warn-soft);border:1px solid #fecaca;color:#991b1b;}
  .callout.amber{background:var(--amber-soft);border:1px solid #fde68a;color:#92400e;}
  .callout.green{background:var(--green-soft);border:1px solid #bbf7d0;color:#166534;}
  .callout.blue{background:var(--blue-soft);border:1px solid #bfdbfe;color:#1e40af;}
  .callout b{font-weight:700;}
  ul.clean{margin:8px 0;padding-left:20px;}
  ul.clean li{margin:6px 0;}
  .pill{display:inline-block;background:var(--primary-soft);color:var(--primary);font-size:12px;font-weight:600;padding:1px 9px;border-radius:999px;margin:1px 4px 1px 0;}
  .pill.star{background:var(--amber-soft);color:var(--amber);}
  .pill.red{background:var(--warn-soft);color:var(--warn);}
  .pill.green{background:var(--green-soft);color:var(--green);}
  .pill.blue{background:var(--blue-soft);color:var(--blue);}
  .pill.amber{background:var(--amber-soft);color:var(--amber);}
  .score-row{display:flex;align-items:center;gap:14px;padding:10px 0;border-bottom:1px dashed var(--line);}
  .score-row:last-child{border-bottom:none;}
  .score-name{width:200px;flex:0 0 auto;font-weight:600;}
  .score-bar{flex:1;height:10px;background:var(--bg);border-radius:6px;overflow:hidden;}
  .score-bar i{display:block;height:100%;background:linear-gradient(90deg,#0e7490,#0d9488);}
  .score-pts{width:90px;text-align:right;font-weight:700;color:var(--primary);}
  .formula{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-family:"Cascadia Code",Consolas,monospace;font-size:14px;color:#0c4a55;}
  .cat-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;}
  .cat-list a{display:block;text-decoration:none;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;color:var(--ink);transition:.15s;}
  .cat-list a:hover{border-color:var(--primary);background:var(--primary-soft);color:var(--primary);}
  .cat-list a .t{font-weight:600;font-size:14px;}
  .cat-list a .d{font-size:12px;color:var(--muted);margin-top:2px;}
  footer{max-width:1180px;margin:0 auto 50px;padding:0 24px;color:var(--muted);font-size:12.5px;}
  .foot-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 22px;}
  @media(max-width:640px){
    .hero-card{padding:22px;}
    .hero-card h1{font-size:20px;}
    .score-name{width:130px;}
  }
"""

NAV_LABELS = {
    "info": "基本信息",
    "time": "时间节点",
    "reject": "废标条款",
    "qual": "资格条件",
    "score": "评分办法",
    "demand": "采购需求",
    "files": "响应文件",
    "tips": "解读技巧",
    "strategy": "得分策略",
    "pit": "避坑清单",
    "techmat": "技术证明",
}


def esc(s):
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def render_block(b):
    t = b.get("type")
    if t == "facts":
        items = "".join(
            '<div class="fact"><div class="k">{k}</div><div class="v {tone}">{v}</div></div>'.format(
                k=esc(f.get("k")), v=esc(f.get("v")),
                tone=esc(f.get("tone", ""))
            ) for f in b.get("fields", [])
        )
        return '<div class="facts">' + items + "</div>"
    if t == "table":
        cap = b.get("caption")
        cap_html = '<p style="margin:6px 0 0;color:var(--muted);font-size:13px">{c}</p>'.format(c=cap) if cap else ""
        head = "".join("<th>{h}</th>".format(h=esc(h)) for h in b.get("headers", []))
        rows = ""
        for r in b.get("rows", []):
            cells = "".join("<td>{c}</td>".format(c=esc(c)) for c in r)
            rows += "<tr>" + cells + "</tr>"
        return ('<div class="tbl-scroll"><table><thead><tr>{head}</tr></thead>'
                '<tbody>{rows}</tbody></table></div>{cap}').format(head=head, rows=rows, cap=cap_html)
    if t == "callout":
        lvl = b.get("level", "blue")
        return '<div class="callout {lvl}">{txt}</div>'.format(lvl=esc(lvl), txt=b.get("text", ""))
    if t == "list":
        items = ""
        for it in b.get("items", []):
            pill = it.get("pill")
            pill_html = '<span class="pill {pc}">{pt}</span>'.format(pc=esc(pill.get("cls", "")), pt=esc(pill.get("text", ""))) if pill else ""
            items += "<li>{txt}{pill}</li>".format(txt=it.get("text", ""), pill=pill_html)
        return '<ul class="clean">' + items + "</ul>"
    if t == "text":
        return '<div style="margin-top:6px">{txt}</div>'.format(txt=b.get("text", ""))
    if t == "scorebars":
        rows = ""
        for it in b.get("items", []):
            rows += ('<div class="score-row"><div class="score-name">{n}</div>'
                     '<div class="score-bar"><i style="width:{p}%"></i></div>'
                     '<div class="score-pts">{pts}</div></div>').format(
                n=esc(it.get("name")), p=esc(it.get("pct", 0)), pts=esc(it.get("pts")))
        return rows
    if t == "timeline":
        items = ""
        for it in b.get("items", []):
            items += ('<div class="tl"><div class="date">{d}</div>'
                      '<div class="ev">{e}</div><div class="note">{n}</div></div>').format(
                d=esc(it.get("date")), e=esc(it.get("ev")), n=esc(it.get("note", "")))
        return '<div class="timeline">' + items + "</div>"
    return ""


def render_section(sec):
    blocks = "".join(render_block(b) for b in sec.get("blocks", []))
    return ('<section class="card" id="{id}">'
            '<div class="sec-head"><span class="num">{num}</span>'
            '<h2>{title}</h2><span class="hint">{hint}</span></div>'
            '{blocks}</section>').format(
        id=esc(sec.get("id")), num=esc(sec.get("num")),
        title=esc(sec.get("title")), hint=esc(sec.get("hint", "")),
        blocks=blocks)


def render_techmat(tm):
    head = "<th>参数条款（★/▲）</th><th>对应证明材料</th><th>来源（章节/条款）</th>"
    rows = ""
    for r in tm:
        rows += ("<tr><td>{c}</td><td>{m}</td><td>{s}</td></tr>").format(
            c=esc(r.get("clause")), m=esc(r.get("material")), s=esc(r.get("source")))
    table = ('<div class="callout warn"><b>📌 技术参数响应证明材料（规则七）：</b>'
             '以下条款招标文件明确要求提供佐证材料，须在响应文件中逐条对应、标记来源，'
             '避免遗漏导致扣分或无效响应。</div>'
             '<div class="tbl-scroll"><table><thead><tr>{head}</tr></thead>'
             '<tbody>{rows}</tbody></table></div>').format(head=head, rows=rows)
    return ('<section class="card" id="techmat">'
            '<div class="sec-head"><span class="num">⚙</span>'
            '<h2>技术参数响应证明材料汇总表（规则七）</h2>'
            '<span class="hint">来自招标文件技术参数响应要求</span></div>'
            '{body}</section>').format(body=table)


def build(data):
    meta = data.get("meta", {})
    sections = data.get("sections", [])
    techmat = data.get("tech_materials")

    # nav (sections + optional techmat)
    nav_links = ""
    for s in sections:
        sid = esc(s.get("id"))
        slab = esc(NAV_LABELS.get(s.get("id"), s.get("id")))
        nav_links += '<a href="#{0}">{1}</a>'.format(sid, slab)
    if techmat:
        nav_links += '<a href="#techmat">技术证明</a>'

    # hero
    facts_extra = meta.get("facts_extra", [])
    hero_meta = ""
    for f in facts_extra:
        hero_meta += "<div>{0}<b>{1}</b></div>".format(esc(f.get("k")), esc(f.get("v")))
    hero = ('<div class="hero"><div class="hero-card">'
             '<span class="tag">{tag}</span>'
             '<h1>{name}</h1>'
             '<div class="sub">{sub}</div>'
             '<div class="hero-meta">{meta}</div>'
             '</div></div>').format(
        tag=esc(meta.get("hero_tag", "招标文件 · 拆解分析")),
        name=esc(meta.get("project_name", "")),
        sub=esc(meta.get("hero_sub", "")),
        meta=hero_meta
    )

    # sections html
    sec_html = ""
    for s in sections:
        sec_html += render_section(s)
    if techmat:
        sec_html += render_techmat(techmat)

    source_note = esc(data.get("source_note", ""))

    html_doc = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>标书拆解报告 · {title}</title>
<style>{css}</style>
</head>
<body>
<header class="top">
  <div class="top-inner">
    <span class="brand">📑 标书拆解报告</span>
    <nav>{nav}</nav>
  </div>
</header>
{hero}
<div class="wrap">
{sections}
</div>
<footer>
  <div class="foot-card">{source}</div>
</footer>
</body>
</html>
""".format(title=esc(meta.get("project_name", "")), css=CSS,
           nav=nav_links, hero=hero, sections=sec_html, source=source_note)
    return html_doc


def main():
    if len(sys.argv) < 3:
        print("Usage: python build_report.py <report.json> <output.html>")
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    doc = build(data)
    os.makedirs(os.path.dirname(os.path.abspath(outp)), exist_ok=True)
    with open(outp, "w", encoding="utf-8") as f:
        f.write(doc)
    print("Rendered -> {out} ({n} bytes, {s} sections)".format(
        out=outp, n=len(doc), s=len(data.get("sections", []))))


if __name__ == "__main__":
    main()
