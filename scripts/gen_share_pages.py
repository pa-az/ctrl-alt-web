#!/usr/bin/env python3
"""Generates static share pages (share/<platform-id>.html) from
platform_data.json so shared deep links get rich social previews, then
redirect into the app. Rerun after editing platform_data.json:
    python3 scripts/gen_share_pages.py
"""
import json, html, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
platforms = json.loads((root / "platform_data.json").read_text())
features = {f["id"]: f["title"] for f in json.loads((root / "feature_data.json").read_text())}
outdir = root / "share"
outdir.mkdir(exist_ok=True)

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{name} on Ctrl+Alt: Manipulation Level {level}</title>
  <meta name="description" content="{desc}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ctrl+Alt">
  <meta property="og:title" content="{name}: Manipulation Level {level}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="https://ctrl-alt.app/share/{pid}">
  <meta property="og:image" content="https://ctrl-alt.app/share/cards/{pid}.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{name}: Manipulation Level {level}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="https://ctrl-alt.app/share/cards/{pid}.png">
  <meta http-equiv="refresh" content="0; url=/?platform={pid}">
  <script>location.replace('/?platform={pid}');</script>
</head>
<body>
  <p>Opening <a href="/?platform={pid}">{name} on Ctrl+Alt</a>&hellip;</p>
</body>
</html>
"""

for p in platforms:
    # Respectful "white hat" platforms are not part of the threat share set.
    if p.get("respectful"):
        continue
    tactics = [features.get(t, t) for t in p["tacticIds"]]
    desc = html.escape(
        f"{p['name']} uses {len(tactics)} documented manipulation tactics: "
        + ", ".join(tactics[:4])
        + ("," if len(tactics) > 4 else ".")
        + (" and more." if len(tactics) > 4 else "")
        + " See the full breakdown on Ctrl+Alt.", quote=True)
    page = TEMPLATE.format(
        pid=p["id"], name=html.escape(p["name"], quote=True),
        level=html.escape(p["manipulationPercentage"], quote=True), desc=desc)
    (outdir / f"{p['id']}.html").write_text(page)
    print("wrote share/%s.html" % p["id"])
print(f"{len(platforms)} share pages generated")
