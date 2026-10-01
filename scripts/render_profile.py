"""Render a compact profile with bounded images and no viewport-based layouts."""

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSET_NAMES = {
    "profile": "profile-software",
    "activity": "github-activity",
    "languages": "language-overview",
}
PROFILE_LANGUAGES = ("Swift", "Python", "C#", "TypeScript", "JavaScript", "C++")
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


def portrait(x, y, height=354, animated=True, light=False, width=370):
    theme = "light" if light else "dark"
    portrait_ink = "#53616d" if light else "#c3ccd5"
    rows = (ASSETS / f"portrait-{theme}.txt").read_text().splitlines()
    grid_width = max(map(len, rows)) * 4.05
    grid_height = len(rows) * 7.8
    scale = min(width / grid_width, height / grid_height)
    x += (width - grid_width * scale) / 2
    y += (height - grid_height * scale) / 2
    reveal_width = grid_width + 2
    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.5f})" aria-hidden="true">']
    for i, row in enumerate(rows):
        if not row:
            continue
        attrs = ""
        if animated:
            delay = 1.55 * i / max(1, len(rows) - 1)
            timing = f'values="0;0;{reveal_width:.2f}" keyTimes="0;{delay/(delay+.45):.4f};1"' if i else f'from="0" to="{reveal_width:.2f}"'
            out.append(f'<clipPath id="r{i}"><rect x="-1" y="{i*7.8-7.1:.2f}" width="{reveal_width:.2f}" height="8.1"><animate attributeName="width" {timing} begin="0s" dur="{delay+.45:.2f}s" fill="freeze"/></rect></clipPath>')
            attrs = f'clip-path="url(#r{i})"'
        out.append(f'<g {attrs}>')
        positions = " ".join(f"{column*4.05:.2f}" for column in range(len(row)))
        out.append(text(positions, f"{i*7.8:.2f}", row, 6.7, portrait_ink, 400, 'xml:space="preserve"'))
        out.append('</g>')
    return "".join(out) + '</g>'


def hero(palette, animated=True):
    out = [portrait(16, 15, 354, animated, palette == PALETTES["light"]),
           text(414, 76, "~/byrm-tsn", 12, "accent"),
           text(410, 130, "Bayram Tosun", 33, weight=650),
           text(414, 175, "Software development", 17),
           text(414, 201, "Swift · Python · C#", 14),
           text(414, 247, "BSc + MSc Computer Science", 12, "muted"),
           text(414, 269, "London, UK", 12, "muted"),
           text(414, 324, "> always curious", 12, "accent")]
    animation = '<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.4s" calcMode="discrete" repeatCount="indefinite"/>' if animated else ""
    out.append(f'<text x="537" y="324" fill="accent" font-size="12">_{animation}</text>')
    return document(760, 384, "Bayram Tosun — software development", "".join(out), palette,
                    "Animated ASCII portrait from my photograph, including my shoulders and upper chest, with the background excluded. Software development with Swift, Python and C#. Computer Science BSc and MSc graduate in London.")


def language_rows(languages):
    ranked = sorted(languages.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(n for _, n in ranked[5:]))]
    return ranked


def activity_card(palette, data):
    out = [text(18, 27, "GITHUB ACTIVITY", 12, "accent", 600)]
    metrics = [("Repositories", data["repositories"]), ("Stars earned", data["stars"]),
               ("Followers", data["followers"]), ("Contributions / yr", data["contributions"])]
    for i, (label, value) in enumerate(metrics):
        x, y = 18 + (i % 2) * 150, 71 + (i // 2) * 57
        out += [text(x, y, f"{value:,}", 27, weight=600), text(x, y + 20, label, 12, "muted")]
    return document(310, 166, "GitHub activity", "".join(out), palette,
                    f"{data['repositories']} public repositories, {data['stars']} stars earned, {data['followers']} followers, and {data['contributions']} contributions visible on the public calendar in 365 days. Updated {data['updated']}.")


def language_card(palette):
    out = [text(18, 27, "LANGUAGES I USE", 12, "accent", 600)]
    for i, name in enumerate(PROFILE_LANGUAGES):
        x, y = 18 + (i % 2) * 150, 69 + (i // 2) * 38
        out.append(text(x, y, name, 16, weight=500))
    return document(310, 166, "Languages I use", "".join(out), palette,
                    "Selected languages in my work: " + ", ".join(PROFILE_LANGUAGES) + ".")


def picture(kind, animated=False):
    # Theme/motion sources share one geometry. Never serve a tall mobile image
    # or use percentage widths: some README rendering paths can upscale them.
    asset = ASSET_NAMES[kind]
    sources = []
    if animated:
        sources += [('(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)', f'{asset}-dark-still.svg'),
                    ('(prefers-reduced-motion: reduce)', f'{asset}-light-still.svg')]
    sources.append(('(prefers-color-scheme: dark)', f'{asset}-dark.svg'))
    alts = {
        "profile": "Bayram Tosun. An animated ASCII portrait. Software development with Swift, Python and C#. BSc and MSc Computer Science, London.",
        "activity": "GitHub activity: repositories, stars, followers, and contributions. Scope and text summary below.",
        "languages": "Languages I use: " + ", ".join(PROFILE_LANGUAGES) + ".",
    }
    width = 800 if kind == "profile" else 310
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

Computer Science **BSc & MSc graduate** in **London**. I build software with **Swift, Python and C#**, with interests across backend systems, web development and machine learning. Away from code, I'm usually behind a camera.

<p align="center">
  <b>Tools I work with</b><br><br>
  <img src="https://skillicons.dev/icons?i=swift,py,cs,ts,js,cpp,c,django,react,html,css,postgres,mysql,pytorch,tensorflow,docker,git,linux,gcp&amp;perline=10&amp;theme=dark" width="460" alt="Swift, Python, C#, TypeScript, JavaScript, C++, C, Django, React, HTML, CSS, PostgreSQL, MySQL, PyTorch, TensorFlow, Docker, Git, Linux, Google Cloud">
</p>

<!-- BEGIN AUTO:stats -->
<p align="center">
{picture("activity")}
{picture("languages")}
</p>

<details>
<summary>About these numbers</summary>

Updated **{data['updated']}**. **{data['repositories']} public repositories**, **{data['stars']} stars earned** on owned non-fork repositories, **{data['followers']} followers**, and **{data['contributions']} contributions** visible on my public calendar over the last 365 days.

**Repository language shares:** {languages}

The activity figures and repository language shares use public GitHub data. Language shares count code bytes in non-fork repositories, not proficiency or my complete body of work. The **Languages I use** card lists a selection from my broader toolkit. Stats refresh daily through [GitHub Actions](https://github.com/byrm-tsn/byrm-tsn/actions/workflows/refresh-profile.yml).

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
            name = f"{ASSET_NAMES['profile']}-{theme}" + ("" if animated else "-still") + ".svg"
            (ASSETS / name).write_text(hero(palette, animated))
        (ASSETS / f"{ASSET_NAMES['activity']}-{theme}.svg").write_text(activity_card(palette, data))
        (ASSETS / f"{ASSET_NAMES['languages']}-{theme}.svg").write_text(language_card(palette))
    target = ROOT / "README.md"
    generated = readme(data)
    target.write_text(generated if "--full" in sys.argv else update_stats_block(target.read_text(), generated))
    print("Rendered compact profile, 4 portrait assets, and 4 statistics assets.")


if __name__ == "__main__":
    main()
