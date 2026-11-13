#!/usr/bin/env python3
"""Builds copilot/index.html and copilot/downloads/ from the Copilot Kit folder.
Run: python3 -I copilot/build.py   (standard library only)"""
import json, re, shutil
from html import escape
from pathlib import Path

KIT = Path("/Users/mylesparslow/Desktop/ClaudeStuff/copilot-kit")
OUT = Path(__file__).resolve().parent
LIMIT = 8000


def e(s):
    return escape(s, quote=True)


# ---------- minimal Markdown -> HTML (everything escaped first) ----------
def inline(s):
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    def link(m):
        text, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://")):
            return '<a href="%s" target="_blank" rel="noopener">%s</a>' % (url, text)
        return text  # relative kit files are not on the site
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    return s


def md(text):
    lines = text.replace("\r", "").split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.lstrip().startswith("```"):
            buf, i = [], i + 1
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append('<pre class="code">%s</pre>' % e("\n".join(buf)))
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            lvl = min(len(m.group(1)) + 2, 6)  # keep page hierarchy: # -> h3
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
        elif re.match(r"^\s*(-{3,}|\*{3,})\s*$", ln):
            out.append("<hr>")
            i += 1
        elif ln.lstrip().startswith("|"):
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
            html = '<div class="tw"><table>'
            for k, r in enumerate(rows):
                tag = "th" if k == 0 else "td"
                html += "<tr>" + "".join("<%s>%s</%s>" % (tag, inline(c), tag) for c in r) + "</tr>"
            out.append(html + "</table></div>")
        elif ln.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % "<br>".join(inline(b) for b in buf))
        elif re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.", ln))
            items = []
            while i < n and lines[i].strip():
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if mm and len(mm.group(1)) < 2:
                    items.append([mm.group(3)])
                elif items:
                    items[-1].append(lines[i].strip())
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            html = "<%s>" % tag
            for it in items:
                body, extra = it[0], it[1:]
                html += "<li>" + inline(body)
                for x in extra:
                    if x.startswith(">"):
                        html += "<blockquote><p>%s</p></blockquote>" % inline(x.lstrip("> "))
                    else:
                        html += " " + inline(x)
                html += "</li>"
            out.append(html + "</%s>" % tag)
        else:
            buf = []
            while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|>|\||\s*-{3,}\s*$|\s*```)", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            if not buf:  # safety: never loop forever
                buf = [lines[i].strip()]
                i += 1
            out.append("<p>%s</p>" % "<br>".join(inline(b) for b in buf))
    return "\n".join(out)


def sections(readme):
    """Split a README on '## ' headings -> {heading: body}."""
    parts = re.split(r"^## +", readme, flags=re.M)
    return {p.split("\n", 1)[0].strip(): (p.split("\n", 1)[1] if "\n" in p else "") for p in parts[1:]}


def read(p):
    return Path(p).read_text(encoding="utf-8")


# ---------- load ----------
kit = json.loads(read(KIT / "kit.json"))
prompts = json.loads(read(KIT / "prompts" / "prompts.json"))
roles = []
for p in prompts:
    if p["role"] not in roles:
        roles.append(p["role"])

dl = OUT / "downloads"
dl.mkdir(exist_ok=True)
shutil.copyfile(KIT / "dist" / "copilot-kit.zip", dl / "copilot-kit.zip")

NOTE = "Sample run: these instructions run by Claude Haiku on an invented document. Copilot's wording will differ."


def agent_dialog(a):
    slug, name = a["slug"], a["name"]
    d = KIT / "agents" / slug
    secs = sections(read(d / "README.md"))
    tabs = []  # (id, label, html)
    if slug == "client-prep":
        about = re.sub(r"^# .*\n", "", read(d / "README.md"), count=1)
        about = re.split(r"^## What it will NOT do", about, flags=re.M)[0]
        tabs.append(("about", "About", md(about)))
    else:
        sin = read(d / "sample-input.md")
        sout = read(KIT / "samples" / (slug + "-output.md"))
        tabs.append(("sample", "Sample run",
            '<p class="note">%s</p><div class="pair"><section><h4>Sample input</h4><div class="doc">%s</div></section>'
            '<section><h4>Haiku output</h4><div class="doc">%s</div></section></div>' % (e(NOTE), md(sin), md(sout))))
        ins = read(d / "instructions.txt").strip("\n")
        tabs.append(("instr", "Instructions",
            '<p class="meta"><span>%s of %s characters</span> <button type="button" class="tbtn" data-copy-from="ins-%s">Copy instructions</button></p>'
            '<pre class="ins" id="ins-%s" tabindex="0">%s</pre>' % (format(len(ins), ","), format(LIMIT, ","), slug, slug, e(ins))))
        st = json.loads(read(d / "starters.json"))
        rows = "".join('<li><div><strong>%s</strong><p>%s</p></div><button type="button" class="tbtn" data-copy="%s" aria-label="Copy starter: %s">Copy</button></li>'
                       % (e(s["title"]), e(s["text"]), e(s["text"]), e(s["title"])) for s in st)
        tabs.append(("starters", "Starters", "<p>Add these as conversation starters. Replace the [BRACKETS] with your own text.</p><ul class=\"rows\">%s</ul>" % rows))
    tabs.append(("wont", "Won't do", "<ul>%s</ul><p>A person makes the call; the agent prepares the work.</p>" % "".join("<li>%s</li>" % e(x) for x in a["does_not"])))
    if slug == "client-prep":
        body = md(secs["Two install routes"]) + "<h4>Approval</h4>" + md(secs["Approval note"])
        body = "<p>Client Prep needs a live data source, so it is built in Copilot Studio or the Agents Toolkit. It is not a no-code Agent Builder agent.</p>" + body
        body += '<p class="links"><a href="/legal/#firmfacts">See Firm Facts</a></p>'
    else:
        body = md(secs["Set it up (Agent Builder, about five minutes, no code)"])
        pkg = "%s-appPackage.zip" % slug
        shutil.copyfile(KIT / "dist" / pkg, dl / pkg)
        body += ('<h4>For IT</h4><p>Microsoft 365 Agents Toolkit package, for sideloading or deploying the same agent. Install only with IT and risk approval.</p>'
                 '<p class="links"><a href="/copilot/downloads/%s" download>Download %s package (.zip)</a></p>') % (pkg, e(name))
    tabs.append(("install", "Install", body))

    tl = "".join('<button type="button" role="tab" id="t-%s-%s" aria-controls="p-%s-%s" aria-selected="%s" tabindex="%s">%s</button>'
                 % (slug, t[0], slug, t[0], "true" if k == 0 else "false", "0" if k == 0 else "-1", e(t[1])) for k, t in enumerate(tabs))
    tp = "".join('<div role="tabpanel" id="p-%s-%s" aria-labelledby="t-%s-%s" class="tp"%s>%s</div>'
                 % (slug, t[0], slug, t[0], "" if k == 0 else " hidden", t[2]) for k, t in enumerate(tabs))
    return ('<dialog class="cp-dlg" id="d-%s" aria-labelledby="dh-%s"><div class="dlg-h"><div><h3 id="dh-%s">%s</h3><p>%s</p></div>'
            '<button type="button" class="tbtn" data-close>Close</button></div><div class="tabs" role="tablist" aria-label="%s">%s</div>%s</dialog>'
            % (slug, slug, slug, e(name), e(a["tagline"]), e(name + " details"), tl, tp))


AREA_ORDER = ["Firm operations", "Litigation", "Appellate", "Government", "Government investigations", "Construction",
              "Real estate", "Land use", "Environmental", "Labor & employment", "Employee benefits", "Senior housing & care",
              "Health care", "Privacy & data", "Intellectual property", "Insurance recovery", "Family wealth"]
areas = [x for x in AREA_ORDER if any(a["area"] == x for a in kit["agents"])]
areas += sorted({a["area"] for a in kit["agents"]} - set(areas))  # any area not in the list goes last
cards, dialogs = "", ""
for ar in areas:
    items = ""
    for a in kit["agents"]:
        if a["area"] != ar:
            continue
        items += ('<li><button type="button" class="card" data-open="d-%s"><span class="card__n">%s</span><span class="card__t">%s</span>'
                  '<span class="card__m"><b>Who</b> %s</span><span class="card__m"><b>Where</b> %s</span><span class="card__go">Open details &rarr;</span></button></li>'
                  % (a["slug"], e(a["name"]), e(a["tagline"]), e(a["who"]), e(a["where"])))
    n_ar = sum(1 for a in kit["agents"] if a["area"] == ar)
    cards += ('<div class="area" data-area="%s"><h3 class="area__h">%s <i>%d</i></h3><ul class="grid">%s</ul></div>'
              % (e(ar), e(ar), n_ar, items))
for a in kit["agents"]:
    dialogs += agent_dialog(a)

# ---------- labs: the code-backed integrations ----------
LAB_ORDER = ["matter-api", "lex-mcp", "wall-connector", "brief-bench", "defined-terms-addin", "platform-agents", "evals"]
LAB_DEMO = {"lex-mcp": ["demo/transcript.md"], "matter-api": ["demo/transcript.md"],
            "wall-connector": ["demo/access-proof.md", "demo/sync-log.md"], "brief-bench": ["demo/report.md"],
            "defined-terms-addin": ["demo/findings.md"], "evals": ["demo/summary.md"],
            "platform-agents": ["demo/validator-all-labs.md", "demo/matter-pulse-haiku.md", "demo/privilege-log-builder-run.txt"]}
SKIP = {"node_modules", ".venv", "cache", "out", "dist", "results", "__pycache__", ".pytest_cache", "_build", ".DS_Store"}
LABS = KIT / "labs"
labs = [json.loads(read(LABS / s / "lab.json")) for s in LAB_ORDER if (LABS / s / "lab.json").exists()]


def zip_lab(slug):
    import zipfile
    dest = dl / ("lab-%s.zip" % slug)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted((LABS / slug).rglob("*")):
            rel = p.relative_to(LABS / slug)
            if not p.is_file() or set(rel.parts) & SKIP:
                continue
            if p.name.startswith(".env") and p.name != ".env.example":
                continue  # never ship real env files
            z.write(p, "%s/%s" % (slug, rel.as_posix()))
    return dest.stat().st_size


def lab_dialog(L):
    slug = L["slug"]
    ul = lambda xs: "<ul>%s</ul>" % "".join("<li>%s</li>" % inline(x) for x in xs)
    tabs = [("what", "What it shows", ul(L["what_it_shows"]) + "<h4>Built with</h4>" + ul(L["stack"]))]
    demo = ""
    for f in LAB_DEMO.get(slug, []):
        p = LABS / slug / f
        if p.exists() and p.stat().st_size > 200:
            body = '<pre class="code">%s</pre>' % e(read(p)) if p.suffix == ".txt" else md(read(p))
            demo += '<div class="doc demo">%s</div>' % body
    if demo:
        tabs.append(("demo", "Real run", '<p class="note">Output saved from actually running the code on invented data.</p>' + demo))
    if L.get("agents"):
        tabs.append(("agents", "Agents", '<ul class="rows">%s</ul>' % "".join(
            "<li><div><strong>%s</strong><p>%s</p></div></li>" % (e(a["name"]), e(a["tagline"])) for a in L["agents"])))
    tabs.append(("proof", "Checked", "<h4>Verified here</h4>" + ul(L["verified"]) + "<h4>Not verified</h4>" + ul(L["not_verified"])))
    kb = max(1, zip_lab(slug) // 1024)
    tabs.append(("src", "Source", '<p>Run it yourself:</p><pre class="code">%s</pre><p class="links"><a href="/copilot/downloads/lab-%s.zip" download>Download the source (.zip, %s KB)</a></p>'
                 % (e(L["run"]), slug, format(kb, ","))))
    tl = "".join('<button type="button" role="tab" id="t-%s-%s" aria-controls="p-%s-%s" aria-selected="%s" tabindex="%s">%s</button>'
                 % (slug, t[0], slug, t[0], "true" if k == 0 else "false", "0" if k == 0 else "-1", e(t[1])) for k, t in enumerate(tabs))
    tp = "".join('<div role="tabpanel" id="p-%s-%s" aria-labelledby="t-%s-%s" class="tp"%s>%s</div>'
                 % (slug, t[0], slug, t[0], "" if k == 0 else " hidden", t[2]) for k, t in enumerate(tabs))
    return ('<dialog class="cp-dlg" id="d-lab-%s" aria-labelledby="dh-%s"><div class="dlg-h"><div><h3 id="dh-%s">%s</h3><p>%s</p></div>'
            '<button type="button" class="tbtn" data-close>Close</button></div><div class="tabs" role="tablist" aria-label="%s">%s</div>%s</dialog>'
            % (slug, slug, slug, e(L["name"]), e(L["tagline"]), e(L["name"] + " details"), tl, tp))


lab_cards = "".join(
    '<li><button type="button" class="card" data-open="d-lab-%s"><span class="card__n">%s</span><span class="card__t">%s</span>'
    '<span class="card__m"><b>Kind</b> %s</span><span class="card__m"><b>Agents</b> %s</span><span class="card__go">Open details &rarr;</span></button></li>'
    % (L["slug"], e(L["name"]), e(L["tagline"]), e(L["kind"]),
       e(", ".join(a["name"] for a in L.get("agents", [])) or "None. It tests the other agents.")) for L in labs)
lab_dialogs = "".join(lab_dialog(L) for L in labs)

achips = '<button type="button" class="chip2" data-area-f="all" aria-pressed="true">All <i>%d</i></button>' % len(kit["agents"])
for ar in areas:
    achips += '<button type="button" class="chip2" data-area-f="%s" aria-pressed="false">%s <i>%d</i></button>' % (
        e(ar), e(ar), sum(1 for a in kit["agents"] if a["area"] == ar))

chips = '<button type="button" class="chip2" data-role="all" aria-pressed="true">All <i>%d</i></button>' % len(prompts)
for r in roles:
    chips += '<button type="button" class="chip2" data-role="%s" aria-pressed="false">%s <i>%d</i></button>' % (
        e(r), e(r), sum(1 for p in prompts if p["role"] == r))
prows = "".join(
    '<li class="pr" data-role="%s"><div class="pr__b"><p class="pr__h"><strong>%s</strong> <span class="app">%s</span></p>'
    '<p class="pr__t">%s</p><p class="pr__w"><b>Why:</b> %s</p></div>'
    '<button type="button" class="tbtn" data-copy="%s" aria-label="Copy prompt: %s">Copy</button></li>'
    % (e(p["role"]), e(p["title"]), e(p["app"]), e(p["prompt"]), e(p["why"]), e(p["prompt"]), e(p["title"])) for p in prompts)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#fbfaf7">
<title>Copilot Kit — Myles Parslow</title>
<meta name="description" content="Agents and prompts that law-firm staff can set up in Microsoft 365 Copilot themselves, built on an invented firm.">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&display=swap">
<script>document.documentElement.className+=" js"</script>
<link rel="stylesheet" href="/assets/site/i.css">
<style>
.cp{--c:#0019a8;--f:#ffffff;max-width:1100px;margin:0 auto;padding:clamp(20px,4vw,48px) var(--gut) 56px}
.cp *{min-width:0}
.cp h2{font-weight:800;font-size:clamp(24px,3vw,34px);line-height:1.1;margin-bottom:10px}
.cp h3{font-weight:800;font-size:20px;line-height:1.2}
.cp h4{font-weight:800;font-size:16px;margin:18px 0 6px}
.cp p{max-width:46em}
.cp .back{display:inline-block;font-weight:600;font-size:15px;margin-bottom:18px}
.cp .eyebrow{display:inline-block;background:var(--c);color:var(--f);font-weight:800;font-size:14px;padding:4px 12px 3px;border-radius:999px;margin-bottom:12px}
.cp h1{font-weight:800;font-size:clamp(40px,8vw,76px);line-height:1;letter-spacing:-.01em}
.cp .lede{font-size:19px;margin-top:14px}
.cp .cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.cp .btn{display:inline-block;padding:11px 18px 9px;border-radius:999px;border:2px solid var(--ink);background:var(--ink);color:var(--white);font-weight:800;font-size:16px;text-decoration:none}
.cp .btn.alt{background:var(--white);color:var(--ink)}
.cp .btn:hover{background:var(--c);border-color:var(--c);color:var(--f)}
.cp section.s{margin-top:clamp(36px,6vw,64px)}
.cp .how{list-style:none;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;counter-reset:h}
.cp .how li{border:2px solid var(--ink);background:var(--white);padding:14px 16px;counter-increment:h}
.cp .how li::before{content:counter(h);display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--c);color:var(--f);font-weight:800;margin-bottom:8px;padding-top:2px}
.cp .how b{display:block;margin-bottom:2px}
.cp .honest{margin-top:14px;padding:10px 14px;border-left:6px solid var(--c);background:var(--soft)}
.cp .area{margin-top:22px}
.cp .area__h{font-size:15px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:var(--mute);margin-bottom:8px}
.cp .area__h i{font-style:normal;margin-left:4px}
.cp .grid{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.cp .card{all:unset;box-sizing:border-box;display:flex;flex-direction:column;gap:8px;height:100%;width:100%;padding:16px;border:2px solid var(--ink);background:var(--white);cursor:pointer;font:400 15px/1.45 var(--ff)}
.cp .card:hover{border-color:var(--c);box-shadow:5px 5px 0 var(--c)}
.cp .card:focus-visible{outline:3px solid var(--ink);outline-offset:3px}
.cp .card__n{font-weight:800;font-size:20px;line-height:1.15}
.cp .card__t{font-size:16px}
.cp .card__m{color:var(--mute);font-size:14px}
.cp .card__m b{color:var(--ink)}
.cp .card__go{margin-top:auto;padding-top:6px;font-weight:800;color:var(--c)}
.cp .chipbar{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.cp .chip2{font:600 15px/1 var(--ff);padding:9px 14px 7px;border:2px solid var(--ink);border-radius:999px;background:var(--white);color:var(--ink);cursor:pointer}
.cp .chip2 i{font-style:normal;color:var(--mute);margin-left:4px}
.cp .chip2[aria-pressed="true"]{background:var(--c);border-color:var(--c);color:var(--f)}
.cp .chip2[aria-pressed="true"] i{color:var(--f)}
.cp .plist,.cp .rows{list-style:none;padding:0;display:grid;gap:10px}
.cp .pr,.cp .rows li{display:flex;gap:14px;align-items:flex-start;justify-content:space-between;border:2px solid var(--rule);background:var(--white);padding:12px 14px}
.cp .pr__b{flex:1}
.cp .pr__h{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.cp .app{font-size:13px;font-weight:800;padding:2px 9px 1px;border-radius:999px;background:var(--c);color:var(--f)}
.cp .pr__t{margin-top:4px}
.cp .pr__w{margin-top:4px;color:var(--mute);font-size:15px}
.cp .pr__w b{color:var(--ink)}
.cp .rows li p{margin-top:2px}
.cp .tbtn{flex:none}
.cp .dim{color:var(--mute);font-size:15px;margin-top:10px}
.cp dialog{border:3px solid var(--ink);padding:0;background:var(--paper);color:var(--ink);width:min(1000px,calc(100vw - 24px));max-height:calc(100vh - 24px);font:400 16px/1.5 var(--ff)}
.cp dialog::backdrop{background:rgba(22,22,26,.6)}
.cp dialog[open]{display:block;overflow:auto}
.cp .dlg-h{display:flex;gap:12px;justify-content:space-between;align-items:flex-start;padding:16px 18px;border-bottom:2px solid var(--ink);position:sticky;top:0;background:var(--paper);z-index:2}
.cp .dlg-h p{color:var(--mute);margin-top:2px}
.cp .tabs{display:flex;flex-wrap:wrap;gap:6px;padding:12px 18px 0}
.cp .tabs button{font:600 15px/1 var(--ff);padding:9px 14px 7px;border:2px solid var(--ink);border-bottom:0;border-radius:10px 10px 0 0;background:var(--white);color:var(--ink);cursor:pointer}
.cp .tabs button[aria-selected="true"]{background:var(--c);border-color:var(--c);color:var(--f)}
.cp .tp{padding:16px 18px 22px;border-top:2px solid var(--ink)}
.cp .tp ul,.cp .tp ol{padding-left:22px;display:grid;gap:4px;margin:8px 0}
.cp .tp .rows{padding-left:0}
.cp .tp blockquote{margin:8px 0;padding:6px 12px;border-left:4px solid var(--c);background:var(--soft)}
.cp .tp code{font-size:.92em;background:var(--soft);padding:1px 4px}
.cp .tp hr{border:0;border-top:2px solid var(--rule);margin:12px 0}
.cp .tp .links a{display:inline-block;margin-top:6px;padding:10px 16px 8px;border-radius:999px;border:2px solid var(--ink);background:var(--c);color:var(--f);font-weight:800;text-decoration:none}
.cp .tp .links a::after{content:none}
.cp .note{font-weight:600;margin-bottom:12px}
.cp .pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px;align-items:start}
.cp .doc{border:2px solid var(--rule);background:var(--white);padding:12px 14px;max-height:520px;overflow:auto;font-size:15px}
.cp .doc>*+*{margin-top:8px}
.cp .doc h3,.cp .doc h4,.cp .doc h5{font-size:16px;margin:10px 0 4px}
.cp .tw{overflow-x:auto}
.cp table{border-collapse:collapse;font-size:14px;min-width:640px}
.cp td{min-width:9em}
.cp th,.cp td{border:1px solid var(--rule);padding:5px 8px;text-align:left;vertical-align:top}
.cp th{background:var(--soft)}
.cp .meta{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px;color:var(--mute);font-weight:600}
.cp pre.ins{margin:0;padding:12px 14px;border:2px solid var(--rule);background:var(--white);max-height:460px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 ui-monospace,Menlo,Consolas,monospace}
.cp pre.code{margin:6px 0;padding:10px 12px;border:2px solid var(--rule);background:var(--soft);max-height:360px;overflow:auto;white-space:pre;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace}
.cp .doc.demo{max-height:none}
.cp .doc.demo+.doc.demo{margin-top:14px}
.cp .stat{font-size:14px;color:var(--mute);margin-left:8px}
@media (max-width:760px){
 .cp .how{grid-template-columns:minmax(0,1fr)}
 .cp .pair{grid-template-columns:minmax(0,1fr)}
 .cp .pr,.cp .rows li{flex-direction:column;gap:10px}
 .cp dialog{width:calc(100vw - 16px)}
 .cp .tabs{padding:10px 12px 0}.cp .tp,.cp .dlg-h{padding-left:12px;padding-right:12px}
}
</style>
<script src="/assets/site/styles.js" data-v="i" defer></script>
</head>
<body class="room room-legal">
<a class="skip" href="#main">Skip to the content</a>
<header class="bar" id="bar"><nav class="bar__in" aria-label="Lines"><a class="home" href="/"><svg class="ico" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path d="M3 11.5 12 4l9 7.5M5.5 10v10h13V10M10 20v-6h4v6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg><span>Home</span></a><ul class="chips"><li><a class="chip is-cur" href="/legal/" style="--c:#0019a8;--f:#ffffff" aria-current="page" title="Back to the Legal line"><b aria-hidden="true">L</b><span>Legal</span></a></li><li><a class="chip" href="/business/" style="--c:#00843d;--f:#ffffff"><b aria-hidden="true">B</b><span>Business</span></a></li><li><a class="chip" href="/creative/" style="--c:#e32017;--f:#ffffff"><b aria-hidden="true">C</b><span>Creative</span></a></li><li><a class="chip" href="/design/" style="--c:#ffd300;--f:#16161a"><b aria-hidden="true">D</b><span>Design</span></a></li><li><a class="chip" href="/research/" style="--c:#9b0058;--f:#ffffff"><b aria-hidden="true">R</b><span>Research</span></a></li></ul><p class="yah" id="yah"><span class="yah__l">You are here</span> <a id="yah-a" href="#top" style="--c:#0019a8">Copilot Kit</a></p></nav></header>
<main id="main" class="cp">
<header id="top">
<a class="back" href="/legal/#copilotkit">&larr; Back to the Legal line</a><br>
<span class="eyebrow">Legal line &middot; Copilot integrations</span>
<h1>Copilot Kit</h1>
<p class="lede">Agents and prompts that law-firm staff can set up in Microsoft 365 Copilot themselves, built on an invented firm. %%NAGENTS%% agents across %%NAREAS%% practice areas, and %%NPROMPTS%% prompts.</p>
<div class="cta"><a class="btn" href="/copilot/downloads/copilot-kit.zip" download>Download the kit (.zip)</a><a class="btn alt" href="#labs">See the labs</a><a class="btn alt" href="#prompts">Jump to the prompt library</a></div>
</header>

<section class="s" aria-labelledby="h-how">
<h2 id="h-how">How it works</h2>
<ol class="how">
<li><b>Paste the instructions</b>Copy an agent's instructions into Copilot's agent builder.</li>
<li><b>Add the documents</b>Add the client's documents, or just paste them into the chat.</li>
<li><b>A person decides</b>The agent drafts and flags. A person makes the call.</li>
</ol>
<p class="honest">Built and tested with Claude on invented documents; not yet run inside a firm's Copilot tenant. Install only with IT and risk approval.</p>
</section>

<section class="s" aria-labelledby="h-agents">
<h2 id="h-agents">The agents</h2>
<p>%%NAGENTS%% agents across %%NAREAS%% practice areas. Open one to see a sample run, its instructions, starters, limits and install steps.</p>
<div class="chipbar" role="group" aria-label="Filter agents by practice area">%%ACHIPS%%</div>
<div id="agrid">%%CARDS%%</div>
%%DIALOGS%%
</section>

<section class="s" id="labs" aria-labelledby="h-labs">
<h2 id="h-labs">Labs: the code underneath</h2>
<p>The agents above need no code. These go further: a tool server, an API with ethical walls, a search connector, a custom engine agent, a Word add-in, newer Copilot agent features, and a test harness that checks every agent's safety rules. Each one ran for real on invented data; open one to see the saved run and exactly what was and was not verified.</p>
<ul class="grid">%%LABCARDS%%</ul>
%%LABDIALOGS%%
</section>

<section class="s" id="prompts" aria-labelledby="h-prompts">
<h2 id="h-prompts">Prompt library</h2>
<p>%%NPROMPTS%% prompts, by role. Save any of these to Copilot Prompt Gallery and share them with your team.</p>
<div class="chipbar" role="group" aria-label="Filter prompts by role">%%CHIPS%%</div>
<ul class="plist" id="plist">%%PROMPTS%%</ul>
</section>
</main>
<footer class="foot" id="contact"><p class="foot__row" style="margin-top:0"><a href="/legal/#copilotkit">&larr; Back to the Legal line</a> <a href="#top">Back to top &uarr;</a> <a href="mailto:mzpprojects1@gmail.com">mzpprojects1@gmail.com</a> <button type="button" class="tbtn" data-copy="mzpprojects1@gmail.com">Copy address</button></p><p class="foot__sign">All clients, people and documents are invented. Myles Parslow &middot; Made with AI</p></footer>
<script>
(function(){
var q=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
function copy(t,btn){
 var done=function(ok){var o=btn.getAttribute('data-l')||btn.textContent;btn.setAttribute('data-l',o);btn.textContent=ok?'Copied':'Press Ctrl+C';setTimeout(function(){btn.textContent=o},1600)};
 var fb=function(){try{var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.cssText='position:fixed;opacity:0';document.body.appendChild(a);a.select();var ok=document.execCommand('copy');document.body.removeChild(a);done(ok)}catch(e){done(false)}};
 try{if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){done(true)},fb)}else fb()}catch(e){fb()}
}
document.addEventListener('click',function(ev){
 var b=ev.target.closest('button');if(!b)return;
 if(b.hasAttribute('data-copy')){copy(b.getAttribute('data-copy'),b)}
 else if(b.hasAttribute('data-copy-from')){copy(document.getElementById(b.getAttribute('data-copy-from')).textContent,b)}
 else if(b.hasAttribute('data-open')){var d=document.getElementById(b.getAttribute('data-open'));if(d.showModal)d.showModal();else d.setAttribute('open','')}
 else if(b.hasAttribute('data-close')){var d2=b.closest('dialog');if(d2.close)d2.close();else d2.removeAttribute('open')}
 else if(b.getAttribute('role')==='tab'){selTab(b)}
 else if(b.hasAttribute('data-role')){
  var r=b.getAttribute('data-role');
  q('.chip2',b.parentNode).forEach(function(c){c.setAttribute('aria-pressed',c===b?'true':'false')});
  q('#plist .pr').forEach(function(p){p.hidden=!(r==='all'||p.getAttribute('data-role')===r)});
 }
 else if(b.hasAttribute('data-area-f')){
  var f=b.getAttribute('data-area-f');
  q('.chip2',b.parentNode).forEach(function(c){c.setAttribute('aria-pressed',c===b?'true':'false')});
  q('#agrid .area').forEach(function(g){g.hidden=!(f==='all'||g.getAttribute('data-area')===f)});
 }
});
q('dialog').forEach(function(d){d.addEventListener('click',function(ev){if(ev.target===d&&d.close)d.close()})});
function selTab(t){
 var list=t.parentNode;
 q('[role=tab]',list).forEach(function(x){var on=x===t;x.setAttribute('aria-selected',on);x.tabIndex=on?0:-1;document.getElementById(x.getAttribute('aria-controls')).hidden=!on});
 t.focus();
}
q('[role=tablist]').forEach(function(l){l.addEventListener('keydown',function(ev){
 var t=q('[role=tab]',l),i=t.indexOf(document.activeElement);if(i<0)return;
 if(ev.key==='ArrowRight'){selTab(t[(i+1)%t.length]);ev.preventDefault()}
 else if(ev.key==='ArrowLeft'){selTab(t[(i+t.length-1)%t.length]);ev.preventDefault()}
})});
})();
</script>
</body>
</html>
"""

page = (TEMPLATE.replace("%%NAGENTS%%", str(len(kit["agents"]))).replace("%%NAREAS%%", {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven",8:"eight",9:"nine"}.get(len(areas), str(len(areas)))).replace("%%ACHIPS%%", achips).replace("%%NPROMPTS%%", str(len(prompts)))
        .replace("%%LABCARDS%%", lab_cards).replace("%%LABDIALOGS%%", lab_dialogs)
        .replace("%%CARDS%%", cards).replace("%%DIALOGS%%", dialogs).replace("%%CHIPS%%", chips).replace("%%PROMPTS%%", prows))
(OUT / "index.html").write_text(page, encoding="utf-8")
print("wrote index.html (%d bytes), %d agents, %d prompts" % (len(page), len(kit["agents"]), len(prompts)))
