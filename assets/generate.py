#!/usr/bin/env python3
"""Generate the Laghari Labs arcade SVG kit for the profile README.

GitHub Markdown strips CSS, so the theme (cream ground, pixel type, 4px ink
borders, hard offset shadows) has to live inside SVG images. Fonts are
base64-embedded because GitHub's camo proxy blocks external font fetches.

Palette + type pairing come from lagharilabs-website:
  Lagharilabs design/tokens.css  ->  data-palette="arcade" data-type="pixel-plex"

Usage:  python3 assets/generate.py
"""
import base64
import pathlib

HERE = pathlib.Path(__file__).parent
FONTDIR = HERE / "fonts"
W = 1000

FONTS = {
    "display": ("Pixelify", "pixelify_sans_700.sub.woff2"),
    "body": ("PlexMono", "ibm_plex_mono_400.sub.woff2"),
    "bodym": ("PlexMonoM", "ibm_plex_mono_500.sub.woff2"),
}
# The site's woff2s are latin-only subsets, so "→" would fall back to a system
# font. These carry just that glyph, scoped by unicode-range.
EXTRA = {"body": ("PlexMono", "ibm_plex_mono_400_extra.woff2", "U+2192"),
         "bodym": ("PlexMonoM", "ibm_plex_mono_500_extra.woff2", "U+2192")}

# tokens.css :root[data-palette="arcade"]
LIGHT = dict(bg="#F2EBDA", bg2="#E8DFC6", ink="#0E0E12", ink2="#2B2730",
             ink3="#6B6470", line="#0E0E12")
# tokens.css :root[data-mode="dark"][data-palette="arcade"]
DARK = dict(bg="#0E0E12", bg2="#18181F", ink="#F2EBDA", ink2="#D5CCB8",
            ink3="#8C8579", line="#F2EBDA")

A1, A2, A3, A4, A5 = "#FF4D2E", "#FFD23F", "#3A86FF", "#06D6A0", "#B388FF"
SWATCHES = [A1, A2, A3, A4, A5]
# Accent fills always carry dark text: cream on yellow/mint is unreadable, and
# the accents keep their hue in both modes.
ON_ACC = "#0E0E12"
# #3A86FF behind dark ink is 3.6:1 — swap it for purple wherever it fills a pill
TAG_FILL = {"#3A86FF": "#B388FF"}

_b64: dict[str, str] = {}


def face(*keys: str) -> str:
    out = []
    for k in keys:
        fam, fn = FONTS[k]
        if fn not in _b64:
            _b64[fn] = base64.b64encode((FONTDIR / fn).read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,"
            f"{_b64[fn]}) format('woff2');font-weight:400;font-style:normal}}"
        )
        if k in EXTRA:
            fam2, fn2, rng = EXTRA[k]
            if fn2 not in _b64:
                _b64[fn2] = base64.b64encode((FONTDIR / fn2).read_bytes()).decode()
            out.append(
                f"@font-face{{font-family:'{fam2}';src:url(data:font/woff2;base64,"
                f"{_b64[fn2]}) format('woff2');unicode-range:{rng}}}"
            )
    return "".join(out)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tw(text: str, fs: float, ls: float = 0.0) -> float:
    """IBM Plex Mono advance is exactly 0.6em; letter-spacing adds ls em."""
    return len(text) * fs * (0.6 + ls)


def wrap(text, fs, maxw, ls=0.0):
    """Greedy word-wrap using Plex Mono's exact 0.6em advance."""
    maxc = max(8, int(maxw / (fs * (0.6 + ls))))
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if len(t) <= maxc:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def shell(h: int, T: dict, body: str, fonts: tuple, extra_defs: str = "", w: int = W,
          opaque: bool = True) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img">'
        f"<defs>{extra_defs}</defs>"
        f"<style>{face(*fonts)}"
        f".d{{font-family:'Pixelify',ui-monospace,monospace}}"
        f".b{{font-family:'PlexMono',ui-monospace,monospace}}"
        f".m{{font-family:'PlexMonoM','PlexMono',ui-monospace,monospace}}"
        f"</style>"
        + (f'<rect width="{w}" height="{h}" fill="{T["bg"]}"/>' if opaque else "")
        + f"{body}</svg>"
    )


def grid_def(T: dict, size: int = 32) -> str:
    c = T["ink"]
    return (
        f'<pattern id="g" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M {size} 0 L 0 0 0 {size}" fill="none" stroke="{c}" '
        f'stroke-width="1" opacity="0.08"/></pattern>'
    )


def panel(x, y, w, h, T, fill=None, off=10, sw=4) -> str:
    """Hard pixel-step shadow + bordered panel (tokens.css .px-shadow)."""
    f = fill or T["bg2"]
    return (
        f'<rect x="{x + off}" y="{y + off}" width="{w}" height="{h}" fill="{T["line"]}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" '
        f'stroke="{T["line"]}" stroke-width="{sw}"/>'
    )


def pill(x, y, text, T, fill=None, fs=13, h=26, ls=0.06):
    """tokens.css .tag — returns (svg, width)."""
    w = 18 + tw(text, fs, ls)
    bg = fill or T["bg2"]
    tone = ON_ACC if fill else T["ink"]
    s = (
        f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{h}" fill="{bg}" '
        f'stroke="{T["line"]}" stroke-width="2"/>'
        f'<text class="m" x="{x + 9:.0f}" y="{y + h / 2 + fs * 0.36:.1f}" '
        f'font-size="{fs}" letter-spacing="{ls}em" fill="{tone}">{esc(text)}</text>'
    )
    return s, w


def swatch_strip(x, y, T, size=20):
    s = f'<g stroke="{T["line"]}" stroke-width="2">'
    for i, c in enumerate(SWATCHES):
        s += f'<rect x="{x + i * size}" y="{y}" width="{size}" height="{size}" fill="{c}"/>'
    return s + "</g>", size * len(SWATCHES)


# ── assets ────────────────────────────────────────────────────────────────────

def hero(T):
    H, px, py, pw, ph = 410, 24, 20, 952, 352
    b = f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
    b += panel(px, py, pw, ph, T)
    b += f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="url(#scan)"/>'
    left, right = px + 42, px + pw - 42

    b += pill(left, 54, "LAGHARI LABS", T, fill=A1, fs=13)[0]
    sw, _ = swatch_strip(right - 100, 54, T)
    b += sw
    b += (f'<text class="d" x="{right - 110}" y="72" font-size="17" '
          f'text-anchor="end" fill="{T["ink2"]}">LAGHARILABS.COM</text>')

    b += f'<text class="d" x="{left}" y="168" font-size="70" fill="{T["ink"]}">HAMZA LAGHARI</text>'
    b += (f'<rect x="{left}" y="182" width="190" height="9" fill="{A2}" '
          f'stroke="{T["line"]}" stroke-width="2"/>')
    b += (f'<text class="m" x="{left}" y="222" font-size="17" letter-spacing="0.09em" '
          f'fill="{T["ink"]}">LEAD AI / ML ENGINEER @ TATWEER</text>')
    b += (f'<text class="b" x="{left + 425}" y="222" font-size="17" letter-spacing="0.09em" '
          f'fill="{T["ink3"]}">· ABU DHABI, UAE</text>')
    b += (f'<text class="b" x="{left}" y="252" font-size="15" fill="{T["ink3"]}">'
          f'The model is not the product. The loop around it is.</text>')

    x = left
    for label in ("94.3% EVAL PASS", "$7M+ SAVED", "10+ YEARS SHIPPING"):
        s2, w = pill(x, 272, label, T, fs=12, h=27)
        b += s2
        x += w + 9
    x = left
    for label, col in [("EVALS", A2), ("RETRIEVAL", A4), ("AGENTS", A5),
                       ("TOOL-USE", A1), ("TRACES", A2)]:
        s2, w = pill(x, 312, label, T, fill=col, fs=13)
        b += s2
        x += w + 10
    return shell(H, T, b, ("display", "body", "bodym"), grid_def(T) + scan_def(T))


def scan_def(T):
    return (
        f'<pattern id="scan" width="6" height="6" patternUnits="userSpaceOnUse">'
        f'<rect width="6" height="2" fill="{T["ink"]}" opacity="0.05"/></pattern>'
    )


def header(T, title, accent):
    H = 76
    b = f'<rect x="24" y="12" width="46" height="46" fill="{accent}" stroke="{T["line"]}" stroke-width="3"/>'
    b += f'<rect x="38" y="26" width="18" height="18" fill="{T["line"]}"/>'
    b += (f'<text class="m" x="{86}" y="47" font-size="24" fill="{accent}">&gt;</text>')
    b += (f'<text class="d" x="{112}" y="48" font-size="30" '
          f'fill="{T["ink"]}">{esc(title)}</text>')
    b += f'<rect x="24" y="66" width="952" height="3" fill="{T["line"]}"/>'
    return shell(H, T, b, ("display", "bodym"))


def project(T, accent, name, tag, year, one, desc, stats_, tags):
    """A card from the site's Selected work (src/assets/data.js PROJECTS)."""
    px, py, pw = 24, 16, 952
    left, right = px + 18 + 32, px + pw - 32
    dlines = wrap(desc, 12.5, right - left)
    y_stats = 110 + len(dlines) * 19 + 8
    ph = y_stats + 34 + 26 - py
    H = py + ph + 26

    b = panel(px, py, pw, ph, T)
    b += f'<rect x="{px + 2}" y="{py + 2}" width="16" height="{ph - 4}" fill="{accent}"/>'
    b += f'<text class="d" x="{left}" y="60" font-size="27" fill="{T["ink"]}">{esc(name)}</text>'
    b += (f'<text class="b" x="{right}" y="58" font-size="13" text-anchor="end" '
          f'fill="{T["ink3"]}">{esc(year)}</text>')
    tagw = 18 + tw(tag, 11, 0.06)
    b += pill(right - tw(year, 13) - 14 - tagw, 42, tag, T, fill=accent, fs=11, h=21)[0]
    b += (f'<text class="m" x="{left}" y="86" font-size="14" '
          f'fill="{T["ink2"]}">{esc(one)}</text>')
    for i, line in enumerate(dlines):
        b += (f'<text class="b" x="{left}" y="{110 + i * 19}" font-size="12.5" '
              f'fill="{T["ink3"]}">{esc(line)}</text>')

    x = left
    for label, val in stats_:
        s2, w = pill(x, y_stats, f"{label} {val}".upper(), T, fs=11, h=22)
        b += s2
        x += w + 7
    x = left
    for t in tags:
        s2, w = pill(x, y_stats + 30, t, T, fill=TAG_FILL.get(accent, accent), fs=11, h=22)
        b += s2
        x += w + 7
    return shell(H, T, b, ("display", "body", "bodym"))


def sidequests(T, quests):
    px, py, pw = 24, 16, 952
    left, right = px + 34, px + pw - 34
    H = 62 + 54 * len(quests)
    b = panel(px, py, pw, H - py - 26, T)
    for i, (name, desc, tag, accent) in enumerate(quests):
        top = 44 + i * 54
        if i:
            b += (f'<rect x="{left}" y="{top - 4}" width="{pw - 68}" height="2" '
                  f'fill="{T["line"]}" opacity="0.22"/>')
        b += f'<rect x="{left}" y="{top + 8}" width="10" height="10" fill="{accent}"/>'
        b += (f'<text class="d" x="{left + 24}" y="{top + 20}" font-size="20" '
              f'fill="{T["ink"]}">{esc(name)}</text>')
        b += (f'<text class="b" x="{left + 24}" y="{top + 40}" font-size="12.5" '
              f'fill="{T["ink3"]}">{esc(desc)}</text>')
        b += pill(right - (18 + tw(tag, 11, 0.06)), top + 6, tag, T, fs=11, h=21)[0]
    return shell(H, T, b, ("display", "body", "bodym"))


def fieldnotes(T, notes):
    px, py, pw = 24, 16, 952
    left, right = px + 34, px + pw - 34
    H = 62 + 54 * len(notes)
    b = panel(px, py, pw, H - py - 26, T)
    for i, (num, title, desc, read) in enumerate(notes):
        top = 44 + i * 54
        if i:
            b += (f'<rect x="{left}" y="{top - 4}" width="{pw - 68}" height="2" '
                  f'fill="{T["line"]}" opacity="0.22"/>')
        b += (f'<text class="m" x="{left}" y="{top + 20}" font-size="13" '
              f'fill="{A1}">{esc(num)}</text>')
        b += (f'<text class="d" x="{left + 62}" y="{top + 21}" font-size="20" '
              f'fill="{T["ink"]}">{esc(title)}</text>')
        b += (f'<text class="b" x="{left + 62}" y="{top + 40}" font-size="12.5" '
              f'fill="{T["ink3"]}">{esc(desc)}</text>')
        b += (f'<text class="b" x="{right}" y="{top + 20}" font-size="12" text-anchor="end" '
              f'fill="{T["ink3"]}">{esc(read)}</text>')
    return shell(H, T, b, ("display", "body", "bodym"))


def stack(T, groups):
    rows, y = [], 0
    for name, accent, items in groups:
        rows.append((name, accent, items, y))
        y += 48 + 36 * (1 + sum(1 for _ in items) // 99) + 24
    px, py, pw = 24, 16, 952
    left = px + 34
    maxx = px + pw - 34

    body, cy = "", 74
    for name, accent, items in groups:
        body += f'<rect x="{left}" y="{cy - 18}" width="14" height="14" fill="{accent}" stroke="{T["line"]}" stroke-width="2"/>'
        body += (f'<text class="d" x="{left + 26}" y="{cy}" font-size="21" '
                 f'fill="{T["ink"]}">{esc(name)}</text>')
        cy += 18
        x = left
        for item in items:
            w_est = 18 + tw(item, 13, 0.06)
            if x + w_est > maxx:
                x = left
                cy += 34
            s, w = pill(x, cy, item, T, fill=accent, fs=13)
            body += s
            x += w + 9
        cy += 62
    H = cy + 6
    ph = H - py - 26
    return shell(H, T, panel(px, py, pw, ph, T) + body,
                 ("display", "body", "bodym"))


def timeline(T, rows):
    """Mirrors the CAREER table on lagharilabs.com (src/assets/data.js)."""
    px, py, pw = 24, 16, 952
    left, right = px + 34, px + pw - 34
    x_main = left + 152
    H = 496
    b = panel(px, py, pw, H - py - 26, T)
    for i, (years, company, role, win, loc, tag, accent) in enumerate(rows):
        top = 44 + i * 52
        if i:
            b += (f'<rect x="{left}" y="{top - 3}" width="{pw - 68}" height="2" '
                  f'fill="{T["line"]}" opacity="0.22"/>')
        b += f'<rect x="{left}" y="{top + 9}" width="10" height="10" fill="{accent}"/>'
        b += (f'<text class="m" x="{left + 20}" y="{top + 19}" font-size="12.5" '
              f'letter-spacing="0.04em" fill="{T["ink2"]}">{esc(years)}</text>')
        b += (f'<text class="d" x="{x_main}" y="{top + 20}" font-size="20" '
              f'fill="{T["ink"]}">{esc(company)}</text>')
        b += (f'<text class="b" x="{right}" y="{top + 19}" font-size="12" '
              f'text-anchor="end" fill="{T["ink3"]}">{esc(loc)}</text>')
        if tag:
            tagw = 18 + tw(tag, 11, 0.06)
            tx = right - tw(loc, 12) - 16 - tagw
            b += pill(tx, top + 5, tag, T, fill=accent, fs=11, h=19)[0]
        detail = role + " · " + win
        # shrink to stay inside the right margin (Rintel's line is the long one)
        fs = min(12.5, (right - x_main) / (len(detail) * 0.6))
        b += (f'<text class="b" x="{x_main}" y="{top + 40}" font-size="{fs:.1f}" '
              f'fill="{T["ink3"]}">{esc(detail)}</text>')
    return shell(H, T, b, ("display", "body", "bodym"))


def button(text, accent, fs=14, ls=0.08):
    """tokens.css .btn, pinned to ink lines so one file works on either theme."""
    bw, bh, off = 36 + tw(text, fs, ls), 44, 6
    w, h = int(bw + off + 4), bh + off + 4
    b = f'<rect x="{off}" y="{off}" width="{bw:.0f}" height="{bh}" fill="{ON_ACC}"/>'
    b += (f'<rect x="0" y="0" width="{bw:.0f}" height="{bh}" fill="{accent}" '
          f'stroke="{ON_ACC}" stroke-width="3"/>')
    b += (f'<text class="m" x="{bw / 2:.0f}" y="{bh / 2 + fs * 0.36:.1f}" font-size="{fs}" '
          f'text-anchor="middle" letter-spacing="{ls}em" fill="{ON_ACC}">{esc(text)}</text>')
    return shell(h, LIGHT, b, ("bodym",), w=w, opaque=False)


def stats(T, tiles, langs):
    """On-theme replacement for github-readme-stats (its public instance is down).

    Numbers are baked in at generate time — rerun this script to refresh them.
    """
    H, px, py, pw, ph = 322, 24, 16, 952, 280
    b = panel(px, py, pw, ph, T)
    left, right = px + 34, px + pw - 34
    inner = right - left

    tw_ = (inner - 40) / 3
    for i, (num, label) in enumerate(tiles):
        tx = left + i * (tw_ + 20)
        cx = tx + tw_ / 2
        b += (f'<rect x="{tx:.0f}" y="44" width="{tw_:.0f}" height="96" fill="{T["bg"]}" '
              f'stroke="{T["line"]}" stroke-width="3"/>')
        b += (f'<text class="d" x="{cx:.0f}" y="100" font-size="40" text-anchor="middle" '
              f'fill="{T["ink"]}">{esc(num)}</text>')
        b += (f'<text class="b" x="{cx:.0f}" y="124" font-size="12" text-anchor="middle" '
              f'letter-spacing="0.1em" fill="{T["ink3"]}">{esc(label)}</text>')

    b += (f'<text class="d" x="{left}" y="182" font-size="20" '
          f'fill="{T["ink"]}">MOST USED LANGUAGES</text>')

    total = sum(n for _, n, _ in langs)
    x = left
    for name, n, col in langs:
        w = inner * n / total
        b += f'<rect x="{x:.1f}" y="198" width="{w:.1f}" height="30" fill="{col}"/>'
        x += w
    b += (f'<rect x="{left}" y="198" width="{inner}" height="30" fill="none" '
          f'stroke="{T["line"]}" stroke-width="3"/>')

    x = left
    for name, n, col in langs:
        label = f"{name} {100 * n / total:.0f}%"
        b += f'<rect x="{x}" y="250" width="14" height="14" fill="{col}" stroke="{T["line"]}" stroke-width="2"/>'
        b += (f'<text class="b" x="{x + 22}" y="262" font-size="13" '
              f'fill="{T["ink2"]}">{esc(label)}</text>')
        x += 36 + tw(label, 13)
    return shell(H, T, b, ("display", "body", "bodym"))


def footer(T):
    H, px, py, pw, ph = 196, 24, 16, 952, 156
    mid = W // 2
    b = panel(px, py, pw, ph, T)
    tag, tagw = pill(0, 0, "DMS OPEN", T, fill=A4, fs=13)
    b += pill(mid - tagw / 2, 44, "DMS OPEN", T, fill=A4, fs=13)[0]
    b += (f'<text class="m" x="{mid}" y="102" font-size="15" text-anchor="middle" '
          f'letter-spacing="0.04em" fill="{T["ink2"]}">'
          f'HIRING AI ENG? WANT TO TALK SHOP ABOUT EVALS?</text>')
    b += (f'<text class="b" x="{mid}" y="130" font-size="14" text-anchor="middle" '
          f'fill="{T["ink3"]}">mhlaghari@gmail.com · linkedin.com/in/mhlaghari</text>')
    sw, sww = swatch_strip(mid - 118, 148, T, size=18)
    b += sw
    b += (f'<text class="d" x="{mid - 108 + sww}" y="{162}" font-size="17" '
          f'fill="{T["ink2"]}">LAGHARILABS.COM</text>')
    return shell(H, T, b, ("display", "body", "bodym"))


def quote(T):
    H = 92
    mid = W // 2
    b = f'<rect x="24" y="20" width="952" height="3" fill="{T["line"]}" opacity="0.3"/>'
    b += (f'<text class="d" x="{mid}" y="66" font-size="26" text-anchor="middle" '
          f'fill="{A1}">THE MODEL IS NOT THE PRODUCT.</text>')
    return shell(H, T, b, ("display",))


# ── content — mirrors lagharilabs.com (lagharilabs-website/src/assets/data.js) ──

HEADERS = [
    ("whoami", "WHOAMI", A1),
    ("work", "SELECTED WORK", A2),
    ("quests", "SIDE QUESTS", A3),
    ("stack", "TECH STACK", A4),
    ("stats", "GITHUB STATS", A3),
    ("career", "CAREER SO FAR", A5),
    ("notes", "FIELD NOTES", A1),
]

# PROJECTS
WORK = [
    dict(accent=A2, name="Adversaria", tag="ON-DEVICE MEETING NOTES", year="2026",
         one="Privacy-first, bot-free meeting notetaker.",
         desc="Records meetings locally, transcribes on-device with Whisper, and writes "
              "structured notes with a local LLM. No bot joins the call; nothing leaves "
              "the machine. macOS (Apple Silicon) beta.",
         stats_=[("egress", "0 KB"), ("inference", "on-device"), ("stage", "beta")],
         tags=["TAURI", "RUST", "WHISPER", "LOCAL-LLM"]),
    dict(accent=A4, name="Arrival Kit", tag="ARRIVAL INTELLIGENCE", year="2026",
         one="A local survival kit for travelers.",
         desc="Land somewhere new and know exactly which apps locals actually use — "
              "ride-hailing, payments, eSIM, transit. 80 city kits with first-60-minutes "
              "checklists, money guides, and dated sources. The dataset is the product.",
         stats_=[("cities", "80"), ("categories", "12+"), ("stage", "alpha")],
         tags=["NEXT.JS", "TYPESCRIPT", "D3", "DATASET"]),
    dict(accent=A4, name="LaghariLabs OS", tag="SOVEREIGN AGENTIC ENTERPRISE", year="2026",
         one="The future of agentic enterprise.",
         desc="Air-gapped operating layer for autonomous internal tools: 9B open-weights "
              "LLM on-prem, policy, audit, and a typed agent marketplace. Zero cloud egress.",
         stats_=[("model", "9B"), ("egress", "0"), ("stage", "alpha")],
         tags=["ON-PREM", "RAG", "POLICY", "AGENTS"]),
    dict(accent=A3, name="DataMind", tag="AGENTIC BI", year="2025",
         one="Agentic AI business-intelligence platform.",
         desc="Reasoning agents that read warehouses, auto-define KPIs, and generate "
              "dashboards. ReAct planner + structured outputs cut analysis time ~90%.",
         stats_=[("analysis time", "−90%"), ("agents", "12"), ("p50", "420ms")],
         tags=["LANGCHAIN", "REACT", "DASH", "EVALS"]),
    dict(accent=A1, name="QuantallicA", tag="AI TRADING", year="2024",
         one="AI-driven systematic trading.",
         desc="Multi-agent breakout sniper: scanner (TA-Lib + on-chain), notifier "
              "(Telegram), executor (CCXT). Backtested across volatility regimes. 24/7 live.",
         stats_=[("automated", "90%"), ("agents", "3"), ("uptime", "24/7")],
         tags=["PYTHON", "WEB3", "CCXT", "TA-LIB"]),
]

# SIDE_QUESTS
QUESTS = [
    ("YouTube Insights", "Whisper → Ollama pipeline. Auto-summarize + sentiment + trends.",
     "PYTHON · OLLAMA", A2),
    ("MiQ", "First-of-its-kind autonomous analytics. ReAct agents define KPIs.",
     "LANGCHAIN · DASH", A3),
    ("Dolphi", "Commodities news engine. 1k+ articles/day. 85% trend prediction.",
     "NLP · LANGGRAPH", A4),
    ("R&D Tax Agent", "12-agent LLM pipeline. Frascati Manual compliance, auto-scored.",
     "RAG · MILVUS", A1),
]

# STACK
STACK_GROUPS = [
    ("LANGUAGES", A1, ["Python", "R", "SQL", "TypeScript", "DAX"]),
    ("AI / ML", A4, ["PyTorch", "TensorFlow", "LangChain", "LangGraph", "Whisper"]),
    ("AGENTIC", A2, ["ReAct", "RAG", "Milvus", "Ollama", "Llama"]),
    ("DATA + VIZ", A5, ["Power BI", "Dash", "PySpark", "Prophet", "BERT"]),
]

# FIELD_NOTES
NOTES = [
    ("#012", "The model is not the product.", "Five things I learned shipping LLM features.", "7 min"),
    ("#011", "Your eval set is the moat.", "Why taste compounds and prompts don't.", "5 min"),
    ("#010", "Ship the loop, not the model.", "Retries, fallback, structured output.", "6 min"),
    ("#009", "Read 50 traces before you write a line.", "You will be wrong about the failure modes.", "4 min"),
]

# Live values pulled from the GitHub API on 2026-09-05 — rerun to refresh:
#   gh api user --jq '.public_repos'
#   gh api graphql -f query='{viewer{contributionsCollection(from:"2026-01-01T00:00:00Z",
#     to:"2026-12-31T23:59:59Z"){contributionCalendar{totalContributions}}}}'
# Use contributionCalendar, not search/commits — its total_count over-counts badly
# (it reported 1281 against a true 224).
STAT_TILES = [("224", "CONTRIBUTIONS IN 2026"), ("96", "PUBLIC REPOS"), ("2018", "ON GITHUB SINCE")]

LANGS = [("Jupyter Notebook", 23, A1), ("Python", 10, A2), ("HTML", 2, A3),
         ("Swift", 1, A4), ("Shell", 1, A5), ("R", 1, "#6B6470")]

# CAREER
TIMELINE = [
    ("2025 — Now", "Tatweer", "Lead AI / ML Engineer",
     "Built Tatweer OS — sovereign air-gapped 9B LLM platform.", "Abu Dhabi", "CURRENT", A1),
    ("2024 — Now", "Rintel", "Head of Data & AI · Founding Eng",
     "End-to-end data + AI foundation. Selected & funded by Flat6Labs.", "KSA / UAE", "CURRENT", A4),
    ("2024 — 2025", "Abu Dhabi Housing Authority", "Senior Consultant, Data & AI",
     "Cut manual reporting 80%. GCC GOV HR 2025 award.", "Abu Dhabi", "", A2),
    ("2023 — 2024", "Liquid Technology", "Data & AI Consultant",
     "Llama2-7B RAG chatbot · 85% accuracy · YOLOv8 PPE detection.", "Dubai", "", A3),
    ("2022 — 2023", "Dubai Holding Group", "Data Scientist, Privacy",
     "1TB/day ETL · ML privacy risk detection at 85%.", "Dubai", "", A4),
    ("2021 — 2022", "Deloitte", "Data Scientist, Forensics",
     "Caught ~$30M in anomalous transactions.", "Dubai", "", A1),
    ("2021 — 2022", "NYU Stern", "MS · Business Analytics & AI",
     "Capstone @ Schlumberger: 92% offshore demand forecast, $7M saved.", "New York", "EDU", A3),
    ("2015 — 2020", "Etihad Aviation Group", "BI Engineer · Project Manager",
     "$250K/yr savings · most-punctual airline ME award.", "Abu Dhabi", "", A2),
]


def main():
    out = HERE
    written = []
    buttons = [("web", "LAGHARILABS.COM", A2), ("linkedin", "LINKEDIN", A4),
               ("email", "EMAIL", A1), ("notes", "FIELD NOTES", A5)]
    for mode, T in (("light", LIGHT), ("dark", DARK)):
        for name, fn in (("hero", hero), ("footer", footer), ("quote", quote)):
            (out / f"{name}-{mode}.svg").write_text(fn(T))
            written.append(out / f"{name}-{mode}.svg")
        for slug, title, accent in HEADERS:
            (out / f"hdr-{slug}-{mode}.svg").write_text(header(T, title, accent))
            written.append(out / f"hdr-{slug}-{mode}.svg")
        for spec in WORK:
            slug = spec["name"].lower().replace(" ", "-")
            (out / f"work-{slug}-{mode}.svg").write_text(project(T, **spec))
            written.append(out / f"work-{slug}-{mode}.svg")
        for name, fn, arg in (("quests", sidequests, QUESTS), ("stack", stack, STACK_GROUPS),
                              ("timeline", timeline, TIMELINE), ("notes", fieldnotes, NOTES)):
            (out / f"{name}-{mode}.svg").write_text(fn(T, arg))
            written.append(out / f"{name}-{mode}.svg")
        (out / f"stats-{mode}.svg").write_text(stats(T, STAT_TILES, LANGS))
        written.append(out / f"stats-{mode}.svg")

    for slug, label, col in buttons:
        (out / f"btn-{slug}.svg").write_text(button(label, col))
        written.append(out / f"btn-{slug}.svg")

    for stale in out.glob("*.svg"):
        if stale not in written:
            stale.unlink()
            print(f"removed stale {stale.name}")
    print(f"{len(written)} files, {sum(p.stat().st_size for p in written) / 1024:.0f} KB total")


if __name__ == "__main__":
    main()
