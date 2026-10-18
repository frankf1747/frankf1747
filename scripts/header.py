"""Builds assets/header-light.svg and assets/header-dark.svg.

The cover is the portfolio's link-preview card (lib/og-card.tsx in the
Portfolio repo) brought to life: the field of mono characters keeps
flickering, and every couple of seconds a kitchen call (SO WHAT?, TASTE
IT, MORE CHILI) surfaces out of the noise in the accent colour. The
headline decodes letter by letter once, like the site's nav.

GitHub shows a README image through <img>, which allows CSS animation but
no external fonts, so each face is subset to the characters used and
embedded as base64. Every animation only hides something for a moment, so
a renderer that runs no CSS animation still shows a finished card.

Run: python3 scripts/header.py   (needs fonttools and brotli)
"""

import base64
import io
import random
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"

PAPER, INK, ACCENT = "#f5f3ec", "#262048", "#f2247a"
THEMES = {
    "light": {"ground": PAPER, "mark": ACCENT, "text": INK, "field": 0.15},
    "dark": {"ground": INK, "mark": ACCENT, "text": PAPER, "field": 0.18},
}

W, H = 1200, 556
X = 70
KICKER = "DATA & PRODUCT  ·  LOS ANGELES"
HEADLINE = ["I COOK THINGS", "UNTIL THEY'RE WELL DONE."]
SUB = "Products, insights and dishes, all from my own recipes."
CTA = "FRANKFU.ME  →"

# What surfaces from the field, in order, one every SLOT seconds. Each word
# owns its own row so no two ever claim the same cell.
WORDS = [(1, "SO WHAT?"), (3, "TASTE IT"), (5, "MORE CHILI"), (2, "RECOOK"), (4, "SHIP IT"), (0, "SERVED")]
SLOT = 2.2
GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/;:,."
SCRAMBLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#/"

COLS, ROWS, CW, CH = 26, 6, 25.5, 38
FX, FY = W - COLS * CW + 6, 52


def embed(file, text):
    font = TTFont(FONTS / file)
    opts = Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    sub = Subsetter(opts)
    sub.populate(text=text)
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def advances(file, text, size):
    font = TTFont(FONTS / file)
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    return [font["hmtx"][cmap[ord(c)]][0] / upm * size for c in text]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def field(theme, rand):
    cycle = round(SLOT * len(WORDS), 2)
    words = {}
    for i, (row, word) in enumerate(WORDS):
        start = COLS - 1 - len(word)
        for j, ch in enumerate(word):
            words[(row, start + j)] = (round(i * SLOT + j * 0.07, 2), ch)

    out = []
    for r in range(ROWS):
        for c in range(COLS):
            t = max(0.0, min(1.0, (c / (COLS - 1)) * 1.5 - 0.35 - (r / ROWS) * 0.15))
            op = round(t * theme["field"], 3)
            x, y = FX + c * CW + CW / 2, FY + r * CH
            word = words.get((r, c))
            if op < 0.01 and not word:
                continue
            glyphs = [GLYPHS[int(rand.random() * len(GLYPHS))] for _ in range(3)]

            # Noise: about a third of the cells keep cycling through three glyphs.
            noise = [f'<text x="{x:.1f}" y="{y}">{esc(glyphs[0])}</text>']
            if rand.random() < 0.38:
                dur = round(1.4 + rand.random() * 2.6, 2)
                lag = rand.random() * dur
                noise = [
                    f'<text class="cy{" h" if k else ""}" x="{x:.1f}" y="{y}" '
                    f'style="animation-duration:{dur}s;animation-delay:-{round(lag + k * dur / 3, 2)}s">{esc(g)}</text>'
                    for k, g in enumerate(glyphs)
                ]
            noise = f'<g opacity="{op}">{"".join(noise)}</g>'
            if word:
                # The noise steps aside while the word holds this cell.
                d, ch = word
                timing = f"animation-delay:{d}s;animation-duration:{cycle}s"
                out.append(f'<g class="hide" style="{timing}">{noise}</g>')
                if ch != " ":
                    out.append(f'<text class="w" x="{x:.1f}" y="{y}" style="{timing}">{esc(ch)}</text>')
            else:
                out.append(noise)
    return "\n    ".join(out), cycle


def headline(rand, size):
    out, cursor = [], (0, 0)
    for li, line in enumerate(HEADLINE):
        y = 328 + li * size * 0.92
        adv = advances("archivo-condensed-900.woff", line, size)
        x = X
        for i, (c, a) in enumerate(zip(line, adv)):
            cx = x + a / 2
            x += a
            if c == " ":
                continue
            n = li * 15 + i
            frames = 3 + (i % 3)
            for k in range(frames):
                g = SCRAMBLE[int(rand.random() * len(SCRAMBLE))]
                out.append(
                    f'<text class="hd s" x="{cx:.1f}" y="{y:.0f}" '
                    f'style="animation-delay:{120 + n * 28 + k * 50}ms">{g}</text>'
                )
            out.append(
                f'<text class="hd f" x="{cx:.1f}" y="{y:.0f}" '
                f'style="animation-delay:{120 + n * 28 + frames * 50}ms">{esc(c)}</text>'
            )
        cursor = (x + 10, y)
    return "\n    ".join(out), cursor


def fit():
    for size in range(116, 60, -2):
        if max(sum(advances("archivo-condensed-900.woff", l, size)) for l in HEADLINE) <= 1000:
            return size
    return 60


def build(key):
    theme = THEMES[key]
    rand = random.Random("frankf1747")
    size = fit()
    words = "".join(w for _, w in WORDS)
    fonts = (
        f'@font-face{{font-family:D;src:url(data:font/woff2;base64,{embed("archivo-condensed-900.woff", "".join(HEADLINE) + SCRAMBLE)}) format("woff2")}}'
        f'@font-face{{font-family:B;src:url(data:font/woff2;base64,{embed("archivo-500.woff", SUB)}) format("woff2")}}'
        f'@font-face{{font-family:M;src:url(data:font/woff2;base64,{embed("plex-mono-500.woff", GLYPHS + KICKER + CTA + words)}) format("woff2")}}'
    )
    grid, cycle = field(theme, rand)
    head, (cx, cy) = headline(rand, size)
    win = round(SLOT * 0.8 / cycle * 100, 2)  # share of the cycle a word stays up
    css = f"""{fonts}
text{{font:500 27px M;text-anchor:middle;fill:{theme["text"]}}}
.cy{{animation:cy 3s step-end infinite}}
.h{{opacity:0}}
.w{{fill:{theme["mark"]};opacity:0;animation:word linear infinite}}
.hide{{animation:hide linear infinite}}
.hd{{font:900 {size}px D;fill:{theme["mark"]}}}
.s{{opacity:0;animation:frame 50ms linear 1}}
.f{{animation:hold 1ms linear backwards}}
.k{{font:500 17px M;letter-spacing:.06em;text-anchor:start}}
.cta{{fill:{theme["mark"]};text-anchor:end}}
.p{{font:500 30px B;text-anchor:start}}
.cur{{fill:{theme["text"]};animation:blink 1.1s step-end infinite}}
@keyframes cy{{0%{{opacity:1}}33.33%{{opacity:0}}}}
@keyframes word{{0%{{opacity:0}}0.4%{{opacity:1}}{win}%{{opacity:1}}{win + 0.4}%,100%{{opacity:0}}}}
@keyframes hide{{0%{{opacity:1}}0.4%{{opacity:0}}{win}%{{opacity:0}}{win + 0.4}%,100%{{opacity:1}}}}
@keyframes frame{{from,to{{opacity:1}}}}
@keyframes hold{{from,to{{opacity:0}}}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.s,.w,.h{{display:none}}}}"""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="I cook things until they're well done. Products, insights and dishes, all from my own recipes.">
  <style>{css}</style>
  <rect width="{W}" height="{H}" rx="14" fill="{theme["ground"]}"/>
  <g>
    {grid}
  </g>
  <text class="k" x="{X + 4}" y="74">{esc(KICKER)}</text>
  <rect x="{X + 4}" y="88" width="34" height="3" fill="{theme["mark"]}"/>
  <g>
    {head}
  </g>
  <rect class="cur" x="{cx:.0f}" y="{cy - size * 0.7:.0f}" width="{size * 0.3:.0f}" height="{size * 0.7:.0f}"/>
  <text class="p" x="{X + 4}" y="{H - 50}">{esc(SUB)}</text>
  <text class="k cta" x="{W - X}" y="{H - 50}">{esc(CTA)}</text>
</svg>
"""
    (ROOT / "assets" / f"header-{key}.svg").write_text(svg)
    print(key, f"{len(svg) // 1024} KB, headline {size}px, cycle {cycle}s")


if __name__ == "__main__":
    for k in THEMES:
        build(k)
