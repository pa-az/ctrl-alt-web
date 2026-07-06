#!/usr/bin/env python3
"""Generates 1200x630 social preview cards (share/cards/<id>.png) styled
like the app's dark theme. Rerun after editing platform_data.json:
    python3 scripts/gen_share_cards.py && python3 scripts/gen_share_pages.py
"""
import json, pathlib
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(__file__).resolve().parent.parent
platforms = json.loads((root / "platform_data.json").read_text())
features = {f["id"]: f["title"] for f in json.loads((root / "feature_data.json").read_text())}
outdir = root / "share" / "cards"
outdir.mkdir(parents=True, exist_ok=True)

BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
def font(path, size): return ImageFont.truetype(path, size)

BG, SURFACE, BORDER = "#141414", "#1E1E1E", "#3A3A3A"
TEXT, MUTED = "#EDEDED", "#8F8F8F"

def threat(raw):
    s = raw.strip().lower()
    digits = "".join(ch for ch in s if ch.isdigit())
    if "%" in s and digits:
        score = int(digits) / 100.0
        value = f"{int(digits)}%"
        is_pct = True
    else:
        score = 0.95 if "severe" in s else 0.85 if "high" in s else 0.6 if "moderate" in s else 0.4 if "low" in s else 0.7
        value, is_pct = None, False
    if score >= 0.90: color, tier = "#FF5B5B", "SEVERE"
    elif score >= 0.80: color, tier = "#FF8A4C", "HIGH"
    elif score >= 0.70: color, tier = "#FFB13D", "ELEVATED"
    else: color, tier = "#F2CD4C", "MODERATE"
    label = f"{tier} · {value}" if is_pct else tier
    return score, color, label

def text_w(d, t, f): 
    b = d.textbbox((0, 0), t, font=f); return b[2] - b[0]

def eye(d, cx, cy, w):
    h = w * 0.62
    pts_top = [(cx - w/2 + (w) * t, 0) for t in []]
    def quad(p0, pc, p1, n=24):
        return [((1-t)**2*p0[0] + 2*(1-t)*t*pc[0] + t**2*p1[0],
                 (1-t)**2*p0[1] + 2*(1-t)*t*pc[1] + t**2*p1[1]) for t in [i/n for i in range(n+1)]]
    L, R = (cx - w/2, cy), (cx + w/2, cy)
    top = quad(L, (cx, cy - h), R)
    bot = quad(R, (cx, cy + h), L)
    d.line(top + bot + [top[0]], fill="#FF6B6B", width=6, joint="curve")
    r = w * 0.16
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#F0B429")
    r2 = r * 0.42
    d.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=BG)

for p in platforms:
    score, color, label = threat(p["manipulationPercentage"])
    img = Image.new("RGB", (1200, 630), BG)
    d = ImageDraw.Draw(img)
    M = 64

    # Header: eye + wordmark
    eye(d, M + 34, 86, 64)
    d.text((M + 84, 72), "CTRL+ALT", font=font(BOLD, 28), fill=MUTED)

    # Platform name (shrink to fit)
    name = p["name"]
    size = 96
    while text_w(d, name, font(BOLD, size)) > 1200 - 2*M and size > 44:
        size -= 4
    d.text((M, 150), name, font=font(BOLD, size), fill=TEXT)

    # Threat pill
    pf = font(BOLD, 34)
    pw = text_w(d, label, pf) + 56
    py = 170 + size + 18
    d.rounded_rectangle([M, py, M+pw, py+62], radius=31, outline=color, width=3)
    d.ellipse([M+24, py+25, M+36, py+37], fill=color)
    d.text((M+48, py+13), label, font=pf, fill=color)

    # Meter
    my = py + 100
    d.rounded_rectangle([M, my, 1200-M, my+16], radius=8, fill="#2B2B2B")
    d.rounded_rectangle([M, my, M + max(60, int((1200-2*M)*score)), my+16], radius=8, fill=color)
    d.text((M, my+30), "MANIPULATION LEVEL", font=font(BOLD, 20), fill=MUTED)
    tcount = f"{len(p['tacticIds'])} TACTICS DOCUMENTED"
    d.text((1200-M-text_w(d, tcount, font(BOLD, 20)), my+30), tcount, font=font(BOLD, 20), fill=MUTED)

    # Tactic chips
    cf = font(REG, 26)
    x, y = M, my + 86
    shown = 0
    for tid in p["tacticIds"]:
        t = features.get(tid)
        if not t: continue
        w = text_w(d, t, cf) + 44
        if x + w > 1200 - M:
            break
        d.rounded_rectangle([x, y, x+w, y+52], radius=26, fill=SURFACE, outline=BORDER, width=2)
        d.text((x+22, y+11), t, font=cf, fill="#D9D9D9")
        x += w + 14
        shown += 1
    rest = len([t for t in p["tacticIds"] if t in features]) - shown
    if rest > 0:
        t = f"+{rest} more"
        w = text_w(d, t, cf) + 44
        if x + w <= 1200 - M:
            d.rounded_rectangle([x, y, x+w, y+52], radius=26, outline=BORDER, width=2)
            d.text((x+22, y+11), t, font=cf, fill=MUTED)

    # Footer
    d.text((M, 630-58), "ctrl-alt.app", font=font(BOLD, 26), fill="#FF6B6B")
    tag = "See how apps manipulate you"
    d.text((1200-M-text_w(d, tag, font(REG, 24)), 630-56), tag, font=font(REG, 24), fill=MUTED)

    img.save(outdir / f"{p['id']}.png", optimize=True)
print(f"{len(platforms)} cards written to share/cards/")
