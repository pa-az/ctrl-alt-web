#!/usr/bin/env python3
"""Validate the site's indexing signals before a web push.

Exists because Search Console failures surface ~7-10 days after the deploy that
caused them, long after anyone remembers what changed. These checks are the
invariants the current canonical model depends on:

  1. index.html is the SPA shell. It carries the ONLY sitewide canonical
     (https://ctrl-alt.app/). Every ?platform= / ?tactic= deep link serves this
     same shell, so they all consolidate to the homepage.
  2. learn/<slug>.html pages are real content and self-canonicalize to their own
     clean URL. A learn page pointing at any other URL removes it from the index.
  3. share/<id>.html are redirect shims for social previews. They must be
     noindex and must NOT carry a canonical: Google treats noindex + canonical
     as contradictory signals and may resolve it either way.
  4. Every sitemap URL resolves to a file on disk, and every indexable page on
     disk is in the sitemap.

Run from anywhere:  python3 scripts/check_seo.py
Exits non-zero on any failure so it can gate a push.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://ctrl-alt.app'

# The Google Search Console verification file is a bare token page, not content.
SITEMAP_EXEMPT = {'google63aad6237c9561a7.html'}

failures: list[str] = []
checks_run = 0


def fail(msg: str) -> None:
    failures.append(msg)


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding='utf-8', errors='replace') as fh:
        return fh.read()


def canonicals(html: str) -> list[str]:
    return re.findall(
        r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html, re.I)


def has_noindex(html: str) -> bool:
    for tag in re.findall(r'<meta[^>]+>', html, re.I):
        if re.search(r'name=["\']robots["\']', tag, re.I) and 'noindex' in tag.lower():
            return True
    return False


def clean_url(relpath: str) -> str:
    """Map a file on disk to the URL Vercel serves it at (cleanUrls: true)."""
    p = relpath[:-5] if relpath.endswith('.html') else relpath
    if p == 'index':
        return f'{BASE}/'
    if p.endswith('/index'):
        return f'{BASE}/{p[:-5]}'
    return f'{BASE}/{p}'


def check_shell() -> None:
    """index.html: exactly one canonical, pointing at the homepage."""
    global checks_run
    checks_run += 1
    html = read('index.html')
    found = canonicals(html)
    if len(found) != 1:
        fail(f'index.html has {len(found)} canonical tags, expected exactly 1: {found}')
        return
    if found[0] != f'{BASE}/':
        fail(f'index.html canonical is {found[0]!r}, expected {BASE + "/"!r}. '
             'The shell must consolidate every query-param deep link to the homepage.')
    og = re.search(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']',
                   html, re.I)
    if og and og.group(1) != found[0]:
        fail(f'index.html og:url {og.group(1)!r} disagrees with canonical {found[0]!r}.')


def check_learn_pages() -> None:
    """Every learn page must self-canonicalize to its own clean URL."""
    global checks_run
    pages = sorted(glob.glob(os.path.join(ROOT, 'learn', '*.html')))
    if not pages:
        fail('no learn/*.html pages found; did gen_tactic_pages.py run?')
        return
    for path in pages:
        checks_run += 1
        rel = os.path.relpath(path, ROOT)
        html = read(rel)
        found = canonicals(html)
        expected = clean_url(rel)
        if len(found) != 1:
            fail(f'{rel} has {len(found)} canonical tags, expected exactly 1.')
            continue
        if found[0] != expected:
            fail(f'{rel} canonicals to {found[0]!r} but should self-canonicalize '
                 f'to {expected!r}. A learn page pointing elsewhere is dropped '
                 'from the index.')
        if has_noindex(html):
            fail(f'{rel} is noindex; learn pages are the organic-traffic surface '
                 'and must stay indexable.')


def check_share_shims() -> None:
    """Share shims must be noindex and must not carry a canonical."""
    global checks_run
    for path in sorted(glob.glob(os.path.join(ROOT, 'share', '*.html'))):
        checks_run += 1
        rel = os.path.relpath(path, ROOT)
        html = read(rel)
        if not has_noindex(html):
            fail(f'{rel} is missing <meta name="robots" content="noindex, follow">. '
                 'Indexable redirect shims produce "Page with redirect" reports.')
        found = canonicals(html)
        if found:
            fail(f'{rel} carries a canonical ({found[0]!r}). Do not combine '
                 'noindex with rel=canonical: Google calls these contradictory '
                 'and may honour either one.')


def check_sitemap() -> None:
    """Sitemap URLs must resolve to files, and indexable files must be listed."""
    global checks_run
    checks_run += 1
    sitemap = read('sitemap.xml')
    listed = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    if not listed:
        fail('sitemap.xml lists no URLs.')
        return

    for url in listed:
        path = url[len(BASE):] if url.startswith(BASE) else url
        if path in ('', '/'):
            target = 'index.html'
        elif path.endswith('/'):
            target = path.lstrip('/') + 'index.html'
        else:
            target = path.lstrip('/') + '.html'
        if not os.path.isfile(os.path.join(ROOT, target)):
            fail(f'sitemap lists {url} but {target} does not exist. Google will '
                 'crawl it, 404, and report it as an error.')

    listed_set = set(listed)
    on_disk = (glob.glob(os.path.join(ROOT, '*.html'))
               + glob.glob(os.path.join(ROOT, 'learn', '*.html'))
               + glob.glob(os.path.join(ROOT, 'share', '*.html')))
    for path in sorted(on_disk):
        rel = os.path.relpath(path, ROOT)
        if os.path.basename(rel) in SITEMAP_EXEMPT:
            continue
        html = read(rel)
        if has_noindex(html):
            continue
        if clean_url(rel) not in listed_set:
            fail(f'{rel} is indexable but missing from sitemap.xml '
                 f'(expected {clean_url(rel)}). Run scripts/gen_sitemap.py.')


def main() -> int:
    check_shell()
    check_learn_pages()
    check_share_shims()
    check_sitemap()

    if failures:
        print(f'SEO check FAILED ({len(failures)} problem(s)):\n')
        for msg in failures:
            print(f'  - {msg}')
        print('\nFix these before pushing; Search Console will not report them '
              'for another week or so.')
        return 1
    print(f'SEO check passed ({checks_run} pages/checks validated).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
