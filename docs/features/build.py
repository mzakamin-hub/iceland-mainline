#!/usr/bin/env python3
# Generate docs/FEATURES.md and docs/features/feature-matrix.html from features-data.py.
# Usage: python3 docs/features/build.py   (from anywhere; paths are relative to this file)
import html
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("features_data", os.path.join(HERE, "features-data.py"))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)

ORDER = ["ok", "part", "todo", "out"]
LABEL = {"ok": "Working", "part": "In progress", "todo": "Not started", "out": "Not planned"}
ICON = {"ok": "✅", "part": "🟡", "todo": "⬜", "out": "❌"}


def counts(rows):
    return {s: sum(1 for r in rows if r[1] == s) for s in ORDER}


def total_counts():
    t = {s: 0 for s in ORDER}
    for _, rows in D.G:
        for s, n in counts(rows).items():
            t[s] += n
    return t


def bar(c, cls="bar", titles=True):
    label = ", ".join(f"{c[s]} {LABEL[s].lower()}" for s in ORDER)
    segs = "".join(
        f'<span class="seg {s}" style="flex:{c[s]}"' + (f' title="{LABEL[s]}: {c[s]}"' if titles else "") + "></span>"
        for s in ORDER if c[s]
    )
    return f'<div class="{cls}" role="img" aria-label="{label}">{segs}</div>'


def look(r):
    return r[3] if len(r) > 3 else ""


# The 4th field ("next") holds items that start with one of these prefixes; several items are separated by "; ".
NEXT_KINDS = [("Fixing", "fix", "Fixing now"), ("Owner check", "own", "Owner checks"),
              ("Add", "add", "Can be added"), ("Tune", "tune", "Can be tuned")]
NEXT_RE = re.compile(r"(?:^|;\s+)(?:(Fixing|Owner check|Add|Tune):|(Nothing)\b)\s*")


def next_items(text):
    """Split a next field into [(kind, text)]; text without a known prefix becomes one item of kind ''."""
    hits = list(NEXT_RE.finditer(text or ""))
    if not hits:
        return [("", text.strip())] if (text or "").strip() else []
    items = []
    if hits[0].start() > 0:
        items.append(("", text[:hits[0].start()].strip()))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        body = text[m.end():end].strip().rstrip(";").strip()
        if m.group(1):
            items.append((m.group(1), body))
        elif body:  # "Nothing" followed by a remark
            items.append(("", body))
    return items


def next_summary():
    """{kind: [(group, feature, text)]} in the order of the matrix."""
    s = {k: [] for k, _, _ in NEXT_KINDS}
    for gname, rows in D.G:
        for r in rows:
            for kind, body in next_items(look(r)):
                if kind in s:
                    s[kind].append((gname, r[0], body))
    return s


def build_md():
    t = total_counts()
    n = sum(t.values())
    ns = next_summary()
    out = ["# OnePlus Pad 4 mainline: feature matrix", "",
           f"Status {D.DATE} ({D.STATUS_MD}). Everything is tested by RAM boot; nothing is installed on the tablet yet.",
           "Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.",
           f"Totals: {t['ok']} working, {t['part']} in progress, {t['todo']} not started, {t['out']} not planned ({n}).",
           "Next steps: " + ", ".join(f"{len(ns[k])} {title.lower()}" for k, _, title in NEXT_KINDS)
           + " (listed at the end).",
           ""]
    for name, rows in D.G:
        c = counts(rows)
        out += [f"## {name} ({c['ok']}/{len(rows)} working)", "", "| Feature | Status | Notes | Next (fixing / add / tune / owner check) |", "|---|---|---|---|"]
        out += [f"| {r[0]} | {ICON[r[1]]} {LABEL[r[1]]} | {r[2]} | {look(r)} |" for r in rows]
        out.append("")
    out += ["## Next steps", ""]
    for kind, _, title in NEXT_KINDS:
        out += [f"### {title} ({len(ns[kind])})", ""]
        out += [f"- **{feat}** ({g}): {body}" for g, feat, body in ns[kind]] or ["- none"]
        out.append("")
    return "\n".join(out)


def next_html(text):
    """The next field with a coloured tag in front of each item."""
    e = html.escape
    parts = []
    for kind, body in next_items(text):
        cls = {k: c for k, c, _ in NEXT_KINDS}.get(kind)
        parts.append((f'<span class="tag {cls}">{e(kind)}</span> ' if cls else "") + e(body))
    if not parts and (text or "").strip():
        return f'<span class="tag none">Nothing</span>'
    return "<br>".join(parts)


def build_html():
    t = total_counts()
    n = sum(t.values())
    e = html.escape
    total_label = ", ".join(f"{t[s]} {LABEL[s].lower()}" for s in ORDER) + f" of {n}"
    total_bar = (f'<div class="total" role="img" aria-label="{total_label}">'
                 + "".join(f'<span class="seg {s}" style="flex:{t[s]}"></span>' for s in ORDER if t[s]) + "</div>")
    chips = "".join(
        f'<button class="chip {s}" data-f="{s}" aria-pressed="false"><span class="dot {s}"></span>{LABEL[s]} <b>{t[s]}</b></button>'
        for s in ORDER)
    groups = []
    for name, rows in D.G:
        c = counts(rows)
        trs = "".join(
            f'<tr data-s="{r[1]}"><td class="f">{e(r[0])}</td><td><span class="pill {r[1]}">{LABEL[r[1]]}</span></td><td class="n">{e(r[2])}</td><td class="l">{next_html(look(r))}</td></tr>'
            for r in rows)
        groups.append(
            f'<section class="grp"><header><h2>{e(name)}</h2><span class="cnt">{c["ok"]}/{len(rows)} working</span></header>\n'
            f'{bar(c)}\n'
            f'<div class="tw"><table><thead><tr><th>Feature</th><th>Status</th><th>Notes</th><th>Next</th></tr></thead><tbody>{trs}</tbody></table></div></section>')
    ns = next_summary()
    lists = "".join(
        f'<details class="nx"{" open" if cls == "fix" else ""}><summary><span class="tag {cls}">{e(kind)}</span> {e(title)} <b>{len(ns[kind])}</b></summary>'
        + "<ul>" + "".join(f'<li><b>{e(feat)}</b> <span class="g">{e(g)}</span>: {e(body)}</li>' for g, feat, body in ns[kind]) + "</ul></details>"
        for kind, cls, title in NEXT_KINDS)
    nextsec = f'<section class="grp next"><header><h2>Next steps</h2><span class="cnt">{sum(len(v) for v in ns.values())} items</span></header>{lists}</section>'
    return HTML_HEAD + f"""<div class="wrap">
  <div class="top">
    <div class="eyebrow">OnePlus Pad 4 · SM8850P “iceland” · mainline Linux + Fedora 44</div>
    <h1>Pad 4 feature matrix</h1>
    <p class="sub">{e(D.STATUS_HTML)}</p>
    {total_bar}
    <div class="chips" role="group" aria-label="Filter by status">{chips}</div>
  </div>
  {nextsec}
  {"".join(groups)}
  <footer>{n} features in {len(D.G)} groups. Tap a status to show only those rows; tap it again to show all. Source: docs/FEATURES.md in iceland-mainline.</footer>
</div>
""" + HTML_TAIL


HTML_HEAD = """<title>Pad 4 Feature Matrix</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Layout: one column of functional groups; each group = header, stacked status bar, table. Summary chips on top filter rows. */
:root {
  --bg:#f3f5f8; --panel:#ffffff; --fg:#17202b; --muted:#5a6675; --line:#dde2ea; --accent:#2a4fc9;
  --ok:#1f8a4c; --ok-bg:#e3f4ea; --part:#b86e00; --part-bg:#fbefd9; --todo:#6b7684; --todo-bg:#eceff3; --out:#9a3b3b; --out-bg:#f6e3e3;
  --display:"Archivo","Arial Narrow",system-ui,sans-serif; --body:"Source Sans 3",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"JetBrains Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg:#0f141b; --panel:#161d27; --fg:#e6ebf2; --muted:#98a4b3; --line:#27313e; --accent:#7f9cff;
  --ok:#5fd08e; --ok-bg:#16301f; --part:#f0b25a; --part-bg:#352813; --todo:#a3adba; --todo-bg:#232b36; --out:#ee8d8d; --out-bg:#3a1f22; color-scheme:dark } }
:root[data-theme="dark"] {
  --bg:#0f141b; --panel:#161d27; --fg:#e6ebf2; --muted:#98a4b3; --line:#27313e; --accent:#7f9cff;
  --ok:#5fd08e; --ok-bg:#16301f; --part:#f0b25a; --part-bg:#352813; --todo:#a3adba; --todo-bg:#232b36; --out:#ee8d8d; --out-bg:#3a1f22; color-scheme:dark }
body { background:var(--bg); color:var(--fg); font-family:var(--body); font-size:15px; line-height:1.45; }
.wrap { max-width:1280px; margin:0 auto; padding-inline:16px; padding-block:28px 48px; display:grid; gap:22px; }
.top { display:grid; gap:10px; }
.eyebrow { font-family:var(--mono); font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }
h1 { font-family:var(--display); font-stretch:80%; font-weight:800; font-size:clamp(28px,5vw,40px); line-height:1.05; margin:0; text-wrap:balance; }
.sub { color:var(--muted); max-width:70ch; margin:0; }
.total { display:flex; height:14px; border-radius:7px; overflow:hidden; background:var(--line); }
.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip { font:inherit; font-size:14px; display:inline-flex; align-items:center; gap:7px; padding:6px 12px; border-radius:999px; border:1px solid var(--line); background:var(--panel); color:var(--fg); cursor:pointer; }
.chip b { font-family:var(--mono); font-weight:500; font-variant-numeric:tabular-nums; }
.chip[aria-pressed="true"] { border-color:var(--accent); box-shadow:0 0 0 1px var(--accent) inset; }
.chip:focus-visible, button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.dot { width:9px; height:9px; border-radius:50%; }
.dot.ok,.seg.ok { background:var(--ok); } .dot.part,.seg.part { background:var(--part); } .dot.todo,.seg.todo { background:var(--todo); } .dot.out,.seg.out { background:var(--out); }
.grp { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:16px; display:grid; gap:10px; min-width:0; }
.grp header { display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap; }
h2 { font-family:var(--display); font-stretch:85%; font-weight:700; font-size:20px; margin:0; }
.cnt { font-family:var(--mono); font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums; }
.bar { display:flex; height:8px; border-radius:4px; overflow:hidden; background:var(--line); gap:2px; }
.seg { min-width:6px; }
.tw { overflow-x:auto; min-width:0; }
table { width:100%; border-collapse:collapse; }
th { text-align:left; font-size:12px; font-weight:600; letter-spacing:.05em; text-transform:uppercase; color:var(--muted); padding:6px 8px; border-bottom:1px solid var(--line); }
td { padding:8px; border-bottom:1px solid var(--line); vertical-align:top; }
tr:last-child td { border-bottom:0; }
td.f { font-weight:600; min-width:14ch; }
td.n { color:var(--muted); min-width:18ch; }
td.l { font-size:13.5px; min-width:26ch; }
td.l:not(:empty) { border-left:3px solid var(--accent); }
.pill { display:inline-block; white-space:nowrap; font-size:12.5px; font-weight:600; padding:2px 9px; border-radius:999px; }
.pill.ok { color:var(--ok); background:var(--ok-bg); } .pill.part { color:var(--part); background:var(--part-bg); }
.pill.todo { color:var(--todo); background:var(--todo-bg); } .pill.out { color:var(--out); background:var(--out-bg); }
.grp.empty { display:none; }
.tag { display:inline-block; white-space:nowrap; font-size:11.5px; font-weight:600; letter-spacing:.02em; padding:1px 7px; border-radius:4px; margin-right:2px; }
.tag.fix { color:var(--out); background:var(--out-bg); } .tag.own { color:var(--accent); background:var(--todo-bg); }
.tag.add { color:var(--ok); background:var(--ok-bg); } .tag.tune { color:var(--part); background:var(--part-bg); } .tag.none { color:var(--todo); background:var(--todo-bg); }
.nx { border-top:1px solid var(--line); padding:8px 0 4px; }
.nx summary { cursor:pointer; font-weight:600; }
.nx summary b { font-family:var(--mono); font-weight:500; color:var(--muted); }
.nx ul { margin:8px 0 4px; padding-left:20px; display:grid; gap:4px; }
.nx li .g { color:var(--muted); font-size:13px; }
footer { color:var(--muted); font-size:13px; }
@media (max-width:560px) { th:nth-child(n+3) { display:none; } td.n, td.l { display:block; padding-top:0; border-bottom:0; } tr { display:grid; grid-template-columns:1fr auto; border-bottom:1px solid var(--line); } td { border-bottom:0; } td.n, td.l { grid-column:1 / -1; } td.l:empty { display:none; } td.l:not(:empty) { margin:0 8px 8px; padding-left:8px; } }
</style>
"""

HTML_TAIL = """<script>
(function(){
  var active=null, chips=[].slice.call(document.querySelectorAll('.chip'));
  function apply(){
    chips.forEach(function(c){ c.setAttribute('aria-pressed', String(c.dataset.f===active)); });
    [].forEach.call(document.querySelectorAll('.grp:not(.next)'), function(g){
      var any=false;
      [].forEach.call(g.querySelectorAll('tbody tr'), function(r){ var show=!active||r.dataset.s===active; r.hidden=!show; if(show) any=true; });
      g.classList.toggle('empty', !any);
    });
  }
  chips.forEach(function(c){ c.addEventListener('click', function(){ active = active===c.dataset.f ? null : c.dataset.f; apply(); }); });
})();
</script>
"""

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(HERE))
    with open(os.path.join(root, "docs", "FEATURES.md"), "w", encoding="utf-8") as f:
        f.write(build_md())
    with open(os.path.join(HERE, "feature-matrix.html"), "w", encoding="utf-8") as f:
        f.write(build_html())
    t = total_counts()
    print(f"FEATURES.md + feature-matrix.html: {t['ok']} working, {t['part']} in progress, {t['todo']} not started, {t['out']} not planned ({sum(t.values())})")
    ns = next_summary()
    print("next: " + ", ".join(f"{k} {len(ns[k])}" for k, _, _ in NEXT_KINDS))
