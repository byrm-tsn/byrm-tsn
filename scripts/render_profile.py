"""Render a compact profile with bounded images and no viewport-based layouts."""

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PROFILE_ASSET = "profile-portrait"
PALETTES = {
    "dark": {"bg": "#11161c", "fg": "#e5e9ee", "muted": "#a0acb9", "line": "#303943", "accent": "#d9ac70", "ink": "#c3ccd5"},
    "light": {"bg": "#f6f5f1", "fg": "#242b32", "muted": "#56616b", "line": "#d8dcd9", "accent": "#885821", "ink": "#45515d"},
}
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',monospace"


def text(x, y, value, size=14, color="fg", weight=400, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" {extra}>{escape(str(value))}</text>'


def document(width, height, title, body, palette, description=""):
    for key, color in palette.items():
        body = body.replace(f'fill="{key}"', f'fill="{color}"').replace(f'stroke="{key}"', f'stroke="{color}"')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<rect width="{width}" height="{height}" rx="8" fill="{palette['bg']}"/>
<g font-family="{MONO}">{body}</g>
</svg>\n'''


def portrait(x, y, height=224, animated=True, light=False):
    theme = "light" if light else "dark"
    rows = (ASSETS / f"portrait-{theme}.txt").read_text().splitlines()
    scale = height / (len(rows) * 6.94)
    reveal_width = max(map(len, rows)) * 4.05 + 2
    out = [f'<g transform="translate({x} {y}) scale({scale:.5f})" aria-hidden="true">']
    for i, row in enumerate(rows):
        if not row:
            continue
        positions = " ".join(f"{n*4.05:.2f}" for n in range(len(row)))
        attrs = 'xml:space="preserve"'
        if animated:
            delay = i * .019
            timing = f'values="0;0;{reveal_width:.2f}" keyTimes="0;{delay/(delay+.45):.4f};1"' if i else f'from="0" to="{reveal_width:.2f}"'
            out.append(f'<clipPath id="r{i}"><rect x="-1" y="{i*6.94-6.8:.2f}" width="{reveal_width:.2f}" height="7.6"><animate attributeName="width" {timing} begin="0s" dur="{delay+.45:.2f}s" fill="freeze"/></rect></clipPath>')
            attrs += f' clip-path="url(#r{i})"'
        out.append(text(positions, f"{i*6.94:.2f}", row, 6.7, "ink", 500, attrs))
    return "".join(out) + '</g>'


def hero(palette, animated=True):
    out = [portrait(20, 15, 224, animated, palette == PALETTES["light"]),
           text(188, 43, "~/byrm-tsn", 12, "accent"),
           text(184, 94, "Bayram Tosun", 38, weight=650),
           text(188, 132, "Backend development", 17),
           text(188, 157, "Machine learning", 17),
           text(188, 191, "BSc + MSc Computer Science · London", 12, "muted"),
           text(188, 224, "> always curious", 12, "accent")]
    animation = '<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.4s" calcMode="discrete" repeatCount="indefinite"/>' if animated else ""
    out.append(f'<text x="311" y="224" fill="accent" font-size="12">_{animation}</text>')
    return document(640, 248, "Bayram Tosun — backend development and machine learning", "".join(out), palette,
                    "Animated half-body ASCII portrait from my photograph, with sunglasses, scarf and jacket, and the background excluded. Computer Science BSc and MSc graduate in London.")


def language_rows(languages):
    ranked = sorted(languages.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(n for _, n in ranked[5:]))]
    return ranked


def activity_card(palette, data):
    out = [text(18, 27, "PUBLIC ACTIVITY", 12, "accent", 600)]
    metrics = [("Repositories", data["repositories"]), ("Stars earned", data["stars"]),
               ("Followers", data["followers"]), ("Contributions / yr", data["contributions"])]
    for i, (label, value) in enumerate(metrics):
        x, y = 18 + (i % 2) * 150, 71 + (i // 2) * 57
        out += [text(x, y, f"{value:,}", 27, weight=600), text(x, y + 20, label, 12, "muted")]
    return document(310, 166, "Public GitHub activity", "".join(out), palette,
                    f"{data['repositories']} public repositories, {data['stars']} stars earned, {data['followers']} followers, and {data['contributions']} contributions visible on the public calendar in 365 days. Updated {data['updated']}.")


def language_card(palette, data):
    out = [text(18, 27, "LANGUAGES IN PUBLIC CODE", 12, "accent", 600)]
    ranked = language_rows(data["languages"])
    total = sum(data["languages"].values())
    shades = [palette["accent"], palette["fg"], palette["ink"], palette["muted"], "#a68fa8", "#839784"]
    pos = 18
    for i, (name, n) in enumerate(ranked):
        width = 274 * n / total
        out.append(f'<rect x="{pos:.3f}" y="42" width="{width:.3f}" height="6" fill="{shades[i]}"/>')
        pos += width
        y = 69 + 16.5 * i
        out += [text(18, y, "●", 8, shades[i]), text(33, y, name, 12),
                text(292, y, f"{100*n/total:.1f}%", 12, "muted", extra='text-anchor="end"')]
    if not ranked:
        out.append(text(18, 85, "No public language data yet.", 12, "muted"))
    return document(310, 166, "Languages in public repositories", "".join(out), palette,
                    "Code byte shares in owned public non-fork repositories. These are not proficiency ratings.")


def picture(kind, animated=False):
    # Theme/motion sources share one geometry. Never serve a tall mobile image
    # or use percentage widths: some README rendering paths can upscale them.
    asset = PROFILE_ASSET if kind == "profile" else kind
    sources = []
    if animated:
        sources += [('(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)', f'{asset}-dark-still.svg'),
                    ('(prefers-reduced-motion: reduce)', f'{asset}-light-still.svg')]
    sources.append(('(prefers-color-scheme: dark)', f'{asset}-dark.svg'))
    alts = {
        "profile": "Bayram Tosun. An animated ASCII portrait with my body included and the background removed. Backend development and machine learning. BSc and MSc Computer Science, London.",
        "activity": "Public repositories, stars, followers, and contributions. Text summary below.",
        "languages": "Language shares in my public code. Text summary below.",
    }
    width = 720 if kind == "profile" else 310
    return '<picture>\n' + ''.join(f'  <source media="{media}" srcset="./assets/{file}">\n' for media, file in sources) + f'  <img src="./assets/{asset}-light.svg" width="{width}" alt="{alts[kind]}">\n</picture>'


def readme(data):
    languages = ", ".join(f"{name} {100*n/sum(data['languages'].values()):.1f}%" for name, n in language_rows(data["languages"])) or "No public language data yet."
    return f'''<p align="center">
{picture("profile", animated=True)}
</p>

<p align="center">
  <a href="https://bayramtosun.dev">Website</a> ·
  <a href="mailto:bayramtosun@outlook.com">Email</a> ·
  <a href="https://linkedin.com/in/bayram-tosun-a19217102">LinkedIn</a> ·
  <a href="https://instagram.com/bayram.jpeg">Photography</a> ·
  <a href="https://medium.com/@bayramtosun">Medium</a> ·
  <a href="https://x.com/9byrmtsn">X</a>
</p>

Computer Science **BSc & MSc graduate** in **London**, building backend software and exploring machine learning. Away from code, I'm usually behind a camera.

<p align="center">
  <b>Tools I work with</b><br><br>
  <img src="https://skillicons.dev/icons?i=py,cs,swift,ts,js,cpp,c,django,react,html,css,postgres,mysql,pytorch,tensorflow,docker,git,linux,gcp&amp;perline=10&amp;theme=dark" width="460" alt="Python, C#, Swift, TypeScript, JavaScript, C++, C, Django, React, HTML, CSS, PostgreSQL, MySQL, PyTorch, TensorFlow, Docker, Git, Linux, Google Cloud">
</p>

<!-- BEGIN AUTO:stats -->
<p align="center">
{picture("activity")}
{picture("languages")}
</p>

<details>
<summary>About these numbers</summary>

Updated **{data['updated']}**. **{data['repositories']} public repositories**, **{data['stars']} stars earned** on owned non-fork repositories, **{data['followers']} followers**, and **{data['contributions']} contributions** visible on my public calendar over the last 365 days.

**Language shares:** {languages}

These measure code bytes in my public, non-fork repositories, not proficiency. Refreshed daily through [GitHub Actions](https://github.com/byrm-tsn/byrm-tsn/actions/workflows/refresh-profile.yml).

</details>
<!-- END AUTO:stats -->

<p align="center">
  <a href="https://www.buymeacoffee.com/bayramtosun"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="140" alt="Buy me a coffee"></a>
  &nbsp;
  <img src="https://komarev.com/ghpvc/?username=byrm-tsn&amp;label=Profile+views&amp;color=80705b&amp;style=flat-square" alt="Profile views">
</p>
'''


def update_stats_block(existing, generated):
    pattern = r"<!-- BEGIN AUTO:stats -->.*?<!-- END AUTO:stats -->"
    block = re.search(pattern, generated, flags=re.S).group(0)
    if re.search(pattern, existing, flags=re.S):
        return re.sub(pattern, lambda _: block, existing, flags=re.S)
    raise ValueError("README statistics markers are missing; refusing to overwrite personal edits")


def main():
    data = json.loads((ASSETS / "stats.json").read_text())
    for theme, palette in PALETTES.items():
        for animated in (False, True):
            name = f"{PROFILE_ASSET}-{theme}" + ("" if animated else "-still") + ".svg"
            (ASSETS / name).write_text(hero(palette, animated))
        (ASSETS / f"activity-{theme}.svg").write_text(activity_card(palette, data))
        (ASSETS / f"languages-{theme}.svg").write_text(language_card(palette, data))
    target = ROOT / "README.md"
    generated = readme(data)
    target.write_text(generated if "--full" in sys.argv else update_stats_block(target.read_text(), generated))
    print("Rendered compact profile, 4 portrait assets, and 4 statistics assets.")


if __name__ == "__main__":
    main()
