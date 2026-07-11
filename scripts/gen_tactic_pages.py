#!/usr/bin/env python3
"""Generate static SEO pages for every tactic in feature_data.json.

Output: learn/<tactic_id>.html — real, content-full HTML (unlike the /share
pages, which are instant redirects for social previews and are invisible to
search). Each page cross-links related tactics (same category) and the
platforms that use it, giving crawlers a dense internal link graph.

Rerun after editing feature_data.json or platform_data.json:
    python3 scripts/gen_tactic_pages.py && python3 scripts/gen_sitemap.py
"""
import json
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'learn')
BASE = 'https://ctrl-alt.app'

def category_label(enum_name: str) -> str:
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', enum_name).split()
    fixed = [w.upper() if w.lower() == 'ai' else w.capitalize() for w in words]
    return ' '.join(fixed)

def section(title, body_html):
    return f'''
  <section>
    <h2>{title}</h2>
    {body_html}
  </section>'''

def main():
    features = json.load(open(os.path.join(ROOT, 'feature_data.json')))
    platforms = json.load(open(os.path.join(ROOT, 'platform_data.json')))
    os.makedirs(OUT, exist_ok=True)

    by_category = {}
    for f in features:
        by_category.setdefault(f['category'], []).append(f)

    used_by = {}
    for p in platforms:
        for tid in p.get('tacticIds', []):
            used_by.setdefault(tid, []).append(p)

    css = '''
    :root { color-scheme: light dark; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
           background: #ffffff; color: #1a1a1a; line-height: 1.65; }
    @media (prefers-color-scheme: dark) { body { background: #0e0e12; color: #f4f3ee; } a { color: #ff8a65; } }
    main { max-width: 720px; margin: 0 auto; padding: 24px 20px 64px; }
    header { max-width: 720px; margin: 0 auto; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
    .wordmark { font-weight: 800; letter-spacing: -0.5px; text-decoration: none; color: inherit; font-size: 20px; }
    .wordmark span { color: #e8654a; }
    .badge { display: inline-block; font-size: 13px; padding: 4px 12px; border-radius: 16px;
             background: rgba(232,101,74,0.12); color: #e8654a; font-weight: 600; margin-bottom: 8px; }
    h1 { font-size: 32px; line-height: 1.2; margin: 4px 0 8px; }
    h2 { font-size: 19px; margin: 28px 0 8px; }
    p { margin: 0 0 12px; }
    .lead { font-size: 18px; }
    .fix { border-left: 3px solid #e8654a; padding: 2px 0 2px 16px; }
    .stat-src { font-size: 14px; opacity: 0.75; }
    .pills { display: flex; flex-wrap: wrap; gap: 8px; padding: 0; list-style: none; margin: 8px 0 0; }
    .pills a { display: inline-block; font-size: 14px; padding: 6px 14px; border-radius: 18px;
               border: 1px solid rgba(128,128,128,0.35); text-decoration: none; color: inherit; }
    .pills a:hover { border-color: #e8654a; }
    .cta { display: inline-block; margin-top: 28px; background: #e8654a; color: #fff; text-decoration: none;
           padding: 12px 24px; border-radius: 12px; font-weight: 700; }
    footer { max-width: 720px; margin: 0 auto; padding: 20px; font-size: 13px; opacity: 0.7; display: flex; gap: 16px; }
    footer a { color: inherit; }
    a { color: #d84315; }
    '''

    for f in features:
        fid = f['id']
        title = f['title']
        cat = category_label(f['category'])
        explanation = html.escape(f.get('explanation', ''))
        origin = html.escape(f.get('origin', ''))
        loop = html.escape(f.get('psychologicalLoop', ''))
        fix = html.escape(f.get('fix', ''))
        stat = html.escape(f.get('stat') or '')
        citation = html.escape(f.get('citation') or '')
        citation_url = f.get('citationUrl') or ''
        url = f'{BASE}/learn/{fid}'
        meta_desc = html.escape((f.get('explanation', '')[:150] + '…') if len(f.get('explanation', '')) > 150 else f.get('explanation', ''))

        body_sections = []
        if origin:
            body_sections.append(section('Where it comes from', f'<p>{origin}</p>'))
        if loop:
            body_sections.append(section('How it hooks you', f'<p>{loop}</p>'))
        if stat:
            src = ''
            if citation and citation_url:
                src = f'<p class="stat-src">Source: <a href="{html.escape(citation_url)}" rel="noopener">{citation}</a></p>'
            elif citation:
                src = f'<p class="stat-src">Source: {citation}</p>'
            body_sections.append(section('What the research shows', f'<p>{stat}</p>{src}'))
        if fix:
            body_sections.append(section('How to resist it', f'<div class="fix"><p>{fix}</p></div>'))

        users = used_by.get(fid, [])
        if users:
            pills = ''.join(
                f'<li><a href="/share/{html.escape(p["id"])}">{html.escape(p["name"])}</a></li>'
                for p in sorted(users, key=lambda p: p['name'])
            )
            body_sections.append(section('Where you&rsquo;ll run into it', f'<ul class="pills">{pills}</ul>'))

        related = [r for r in by_category.get(f['category'], []) if r['id'] != fid][:6]
        if related:
            pills = ''.join(
                f'<li><a href="/learn/{html.escape(r["id"])}">{html.escape(r["title"])}</a></li>'
                for r in related
            )
            body_sections.append(section(f'More {html.escape(cat.lower())} tactics', f'<ul class="pills">{pills}</ul>'))

        ld = json.dumps({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"What is {title}?",
            "description": f.get('explanation', ''),
            "url": url,
            "publisher": {"@type": "Organization", "name": "Ctrl+Alt", "url": BASE},
        })

        page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>What is {html.escape(title)}? How this {html.escape(cat.lower())} tactic works | Ctrl+Alt</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="/favicon.png">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Ctrl+Alt">
  <meta property="og:title" content="What is {html.escape(title)}?">
  <meta property="og:description" content="{meta_desc}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{BASE}/icons/Icon-512.png">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{ld}</script>
  <style>{css}</style>
</head>
<body>
  <header>
    <a class="wordmark" href="/">C<span>+</span>rl<span>+</span>Al<span>+</span></a>
    <nav><a href="/learn/">All tactics</a> &nbsp;&middot;&nbsp; <a href="/">Open the app</a></nav>
  </header>
  <main>
    <span class="badge">{html.escape(cat)}</span>
    <h1>What is {html.escape(title)}?</h1>
    <p class="lead">{explanation}</p>
    {''.join(body_sections)}
    <a class="cta" href="/">Explore all {len(features)} tactics in the app</a>
  </main>
  <footer>
    <a href="/">Ctrl+Alt</a>
    <a href="/learn/">All tactics</a>
    <a href="/privacy">Privacy</a>
    <a href="/support">Support</a>
  </footer>
</body>
</html>
'''
        with open(os.path.join(OUT, f'{fid}.html'), 'w') as fh:
            fh.write(page)

    write_hub(features, by_category, css)
    print(f'Wrote {len(features)} pages + index to learn/')


def write_hub(features, by_category, css):
    """learn/index.html: the crawlable library hub. Groups every tactic by
    category so both humans and crawlers reach all pages from one URL."""
    url = f'{BASE}/learn/'
    n = len(features)
    desc = (f'A plain-language library of {n} documented dark patterns and '
            'manipulation tactics used by apps and platforms: what each one '
            'is, the psychology it exploits, and how to resist it.')

    sections = []
    for cat_key in sorted(by_category, key=lambda c: -len(by_category[c])):
        cat = category_label(cat_key)
        items = sorted(by_category[cat_key], key=lambda f: f['title'])
        pills = ''.join(
            f'<li><a href="/learn/{html.escape(f["id"])}">{html.escape(f["title"])}</a></li>'
            for f in items
        )
        sections.append(section(f'{html.escape(cat)} ({len(items)})',
                                f'<ul class="pills">{pills}</ul>'))

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "headline": f"The dark pattern library: {n} manipulation tactics explained",
        "description": desc,
        "url": url,
        "publisher": {"@type": "Organization", "name": "Ctrl+Alt", "url": BASE},
    })

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dark pattern library: {n} manipulation tactics explained | Ctrl+Alt</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="/favicon.png">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ctrl+Alt">
  <meta property="og:title" content="Dark pattern library: {n} manipulation tactics explained">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{BASE}/icons/Icon-512.png">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{ld}</script>
  <style>{css}</style>
</head>
<body>
  <header>
    <a class="wordmark" href="/">C<span>+</span>rl<span>+</span>Al<span>+</span></a>
    <a href="/">Open the app</a>
  </header>
  <main>
    <h1>The dark pattern library</h1>
    <p class="lead">{html.escape(desc)}</p>
    {''.join(sections)}
    <a class="cta" href="/">See how these tactics target you, in the app</a>
  </main>
  <footer>
    <a href="/">Ctrl+Alt</a>
    <a href="/privacy">Privacy</a>
    <a href="/support">Support</a>
  </footer>
</body>
</html>
'''
    with open(os.path.join(OUT, 'index.html'), 'w') as fh:
        fh.write(page)

if __name__ == '__main__':
    main()
