"""Build the TreasuryEase site: a landing page plus each pack's browser app.

Usage:  python tools/build_site.py [output-dir]      (default: public)

GitHub Pages publishes the output folder. In GitHub Actions the repository URL is
read from GITHUB_REPOSITORY; CI_PROJECT_URL also works. It makes the Source and Docs
links point at the repository.
"""

import html
import json
import os
import shutil
import sys
from pathlib import Path

from _packs import ROOT, load_pack, pack_dirs

STATUS_LABEL = {"available": "Available", "beta": "Beta", "idea": "Planned"}


def e(value):
    return html.escape(str(value), quote=True)


def card(meta, repo, has_app, has_shot):
    pid = meta["id"]
    shot = (
        f'<a class="shot" href="packs/{e(pid)}/" tabindex="-1" aria-hidden="true"><img src="packs/{e(pid)}/screenshot.png" alt="" loading="lazy"></a>'
        if has_shot
        else ""
    )
    tags = "".join(f'<li>{e(t)}</li>' for t in meta.get("tags", []))
    links = []
    if has_app:
        links.append(f'<a class="btn pri" href="packs/{e(pid)}/">Open app</a>')
    if repo:
        links.append(f'<a class="btn" href="{e(repo)}/blob/main/packs/{e(pid)}/README.md">Docs</a>')
        links.append(f'<a class="btn" href="{e(repo)}/tree/main/packs/{e(pid)}">Source</a>')
    return f"""
    <article class="card">
      {shot}
      <div class="body">
        <div class="top"><h3>{e(meta['name'])}</h3><span class="chip {e(meta['status'])}">{STATUS_LABEL.get(meta['status'], meta['status'])}</span></div>
        <p>{e(meta['summary'])}</p>
        <ul class="tags">{tags}</ul>
        <div class="links">{''.join(links)}</div>
      </div>
    </article>"""


def idea(meta):
    tags = ", ".join(meta.get("tags", []))
    return f'<li><strong>{e(meta["name"])}</strong><span>{e(meta["summary"])}</span><small>{e(tags)}</small></li>'


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TreasuryEase</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* Layout idea: a quiet catalogue page. Header, one short statement, a grid of pack cards, then a plain list of what is planned. */
:root{
  --bg:#f3f5f7; --panel:#ffffff; --ink:#14202b; --muted:#5a6b7b; --line:#d9e0e6;
  --accent:#0b6e6e; --accent-ink:#ffffff; --soft:#e3f1f0; --head:#eef2f5;
  --ok:#1b7a43; --warn:#9a5b00;
  --font:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0e151b; --panel:#151e26; --ink:#e5ecf2; --muted:#93a3b2; --line:#25323d;
    --accent:#4cc2b8; --accent-ink:#04201d; --soft:#12302f; --head:#1b2630;
    --ok:#5fd08c; --warn:#e6a448; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0e151b; --panel:#151e26; --ink:#e5ecf2; --muted:#93a3b2; --line:#25323d;
  --accent:#4cc2b8; --accent-ink:#04201d; --soft:#12302f; --head:#1b2630;
  --ok:#5fd08c; --warn:#e6a448; color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font:15px/1.55 var(--font);-webkit-font-smoothing:antialiased}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line);background:var(--panel)}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-top:14px;padding-bottom:14px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none}
.mark{width:36px;height:36px;border-radius:9px;background:var(--accent);color:var(--accent-ink);display:grid;place-items:center}
.brand b{font-size:18px;font-weight:600;letter-spacing:-.01em}
nav{display:flex;gap:18px;font-size:14px}
nav a{color:var(--muted);text-decoration:none}
nav a:hover{color:var(--accent)}
.intro{padding:48px 0 28px;max-width:720px}
.intro h1{margin:0 0 12px;font-size:34px;line-height:1.15;letter-spacing:-.02em;font-weight:600;text-wrap:balance}
.intro p{margin:0;color:var(--muted);font-size:17px;max-width:62ch}
.points{display:flex;gap:10px 22px;flex-wrap:wrap;margin:22px 0 0;padding:0;list-style:none;font-size:14px}
.points li::before{content:"";display:inline-block;width:8px;height:8px;border-radius:2px;background:var(--accent);margin-right:8px}
h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600;margin:36px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;min-width:0}
.shot{display:block;border-bottom:1px solid var(--line);background:var(--head);aspect-ratio:16/9;overflow:hidden}
.shot img{width:100%;height:100%;object-fit:cover;object-position:left top;display:block}
.body{padding:16px;display:flex;flex-direction:column;gap:10px;flex:1}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.card h3{margin:0;font-size:17px;font-weight:600}
.card p{margin:0;color:var(--muted)}
.chip{font:500 11px/1 var(--mono);padding:4px 7px;border-radius:5px;border:1px solid var(--line);white-space:nowrap;color:var(--muted)}
.chip.available{color:var(--ok);border-color:var(--ok)}
.chip.beta{color:var(--warn);border-color:var(--warn)}
.tags{display:flex;gap:6px;flex-wrap:wrap;list-style:none;margin:0;padding:0}
.tags li{font:400 12px/1 var(--mono);padding:4px 7px;border-radius:5px;background:var(--head);color:var(--muted)}
.links{display:flex;gap:8px;flex-wrap:wrap;margin-top:auto;padding-top:6px}
.btn{border:1px solid var(--line);background:var(--panel);border-radius:8px;padding:7px 12px;font-weight:500;font-size:14px;text-decoration:none}
.btn:hover{border-color:var(--accent)}
.btn.pri{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.ideas{list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:12px;background:var(--panel);overflow:hidden}
.ideas li{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:4px 20px;padding:14px 16px;border-bottom:1px solid var(--line)}
.ideas li:last-child{border-bottom:0}
.ideas span{color:var(--muted)}
.ideas small{grid-column:2;font:400 12px var(--mono);color:var(--muted)}
.cta{margin:20px 0 0;color:var(--muted)}
.cta a{color:var(--accent)}
footer{margin-top:48px;border-top:1px solid var(--line);padding:24px 0 40px;color:var(--muted);font-size:13px}
footer p{margin:0 0 6px;max-width:80ch}
@media (max-width:640px){.ideas li{grid-template-columns:1fr}.ideas small{grid-column:1}.intro h1{font-size:28px}}
</style>
</head>
<body>
<header><div class="wrap">
  <a class="brand" href="./"><span class="mark" aria-hidden="true"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M4 12h10"/><path d="M4 17h6"/><path d="m16 15 2 2 4-4"/></svg></span><b>TreasuryEase</b></a>
  <nav>__NAV__</nav>
</div></header>
<main class="wrap">
  <section class="intro">
    <h1>Make treasury processing easy.</h1>
    <p>Small, open source automation packs for the repetitive work around treasury systems and bank files. Each pack does one job, runs on your own machine and ships with synthetic examples so you can try it in a minute.</p>
    <ul class="points"><li>Private: your files stay on your computer</li><li>Plain output: CSV and JSON</li><li>Tested, documented, MIT licensed</li></ul>
  </section>
  <h2>Packs</h2>
  <div class="grid">__CARDS__</div>
  <h2>On the roadmap</h2>
  <ul class="ideas">__IDEAS__</ul>
  <p class="cta">Missing something? __CTA__</p>
</main>
<footer><div class="wrap">
  <p>TreasuryEase is an independent open source project. ISO 20022, TWIST and other standard or product names belong to their owners and are used only to describe what the packs read or write. It is not affiliated with or endorsed by any standards body, bank or software vendor.</p>
  <p>Provided as is, without warranty. Check results against the source before relying on them. Example files are synthetic.</p>
</div></footer>
</body>
</html>
"""


def main(argv):
    out = Path(argv[1]) if len(argv) > 1 else ROOT / "public"
    repo = os.environ.get("CI_PROJECT_URL", "").rstrip("/")
    if not repo and os.environ.get("GITHUB_REPOSITORY"):
        repo = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ["GITHUB_REPOSITORY"]
    if out.exists():
        shutil.rmtree(out)
    (out / "packs").mkdir(parents=True)

    cards = []
    for pack in pack_dirs():
        meta = load_pack(pack)
        has_app = bool(meta.get("web")) and (pack / meta["web"] / "index.html").exists()
        has_shot = bool(meta.get("screenshot")) and (pack / meta["screenshot"]).exists()
        dest = out / "packs" / pack.name
        dest.mkdir(parents=True, exist_ok=True)
        if has_app:
            shutil.copytree(pack / meta["web"], dest, dirs_exist_ok=True)
        if has_shot:
            shutil.copy(pack / meta["screenshot"], dest / "screenshot.png")
        if not has_app and not has_shot:
            dest.rmdir()
        cards.append(card(meta, repo, has_app, has_shot))

    live = {load_pack(p)["id"] for p in pack_dirs()}
    ideas = [i for i in json.loads((ROOT / "catalog" / "planned.json").read_text(encoding="utf-8")) if i["id"] not in live]

    nav = f'<a href="{e(repo)}">Source</a><a href="{e(repo)}/blob/main/CONTRIBUTING.md">Contribute</a><a href="{e(repo)}/issues">Issues</a>' if repo else ""
    cta = f'<a href="{e(repo)}/issues/new">Suggest a pack or send an anonymised sample</a>.' if repo else "Open an issue in the repository."
    page = PAGE.replace("__NAV__", nav).replace("__CARDS__", "".join(cards)).replace("__IDEAS__", "".join(idea(i) for i in ideas)).replace("__CTA__", cta)
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"built {out} with {len(cards)} pack(s) and {len(ideas)} planned idea(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
