#!/usr/bin/env python3
"""Regenerate sitemap.xml from what's actually on disk.

Includes: root, /privacy, /support, /learn/ hub, and every learn/<tactic>.html.
The /share/ pages are deliberately EXCLUDED: they are redirect shims for social
link previews (they meta-refresh to the app), so telling Google to index them
just produces "Page with redirect" reports. Run after gen_tactic_pages.py.
"""
import datetime
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://ctrl-alt.app'

def pages_in(subdir):
    d = os.path.join(ROOT, subdir)
    if not os.path.isdir(d):
        return []
    # index.html is the section hub; it is listed separately as /<subdir>/.
    return sorted(f'{BASE}/{subdir}/{f[:-5]}' for f in os.listdir(d)
                  if f.endswith('.html') and f != 'index.html')

def main():
    today = datetime.date.today().isoformat()
    urls = [(f'{BASE}/', '1.0'), (f'{BASE}/privacy', '0.5'), (f'{BASE}/support', '0.5')]
    if os.path.isfile(os.path.join(ROOT, 'learn', 'index.html')):
        urls.append((f'{BASE}/learn/', '0.9'))
    urls += [(u, '0.8') for u in pages_in('learn')]

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pr in urls:
        out.append(f'  <url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{pr}</priority></url>')
    out.append('</urlset>')

    with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as fh:
        fh.write('\n'.join(out) + '\n')
    print(f'sitemap.xml: {len(urls)} URLs')

if __name__ == '__main__':
    main()
