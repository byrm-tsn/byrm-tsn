"""Render a real text portrait and public statistics using stdlib only."""

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PALETTES = {
    "dark": {"bg": "#11161c", "fg": "#e5e9ee", "muted": "#a0acb9", "line": "#303943", "accent": "#d9ac70", "ink": "#bcc7d2"},
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
<rect width="{width}" height="{height}" rx="10" fill="{palette['bg']}"/>
<g font-family="{MONO}">{body}</g>
</svg>\n'''


def portrait(x, y, scale=1, animated=True, light=False):
    theme = "light" if light else "dark"
    rows = (ASSETS / f"portrait-{theme}.txt").read_text().splitlines()
    out = [f'<g transform="translate({x} {y}) scale({scale})" aria-hidden="true">']
    for i, row in enumerate(rows):
        if not row:
            continue
        positions = " ".join(f"{n*4.05:.2f}" for n in range(len(row)))
        attrs = 'xml:space="preserve"'
        if animated:
            delay = i * .03
            timing = f'values="0;0;310" keyTimes="0;{delay/(delay+.55):.4f};1"' if i else 'from="0" to="310"'
            out.append(f'<clipPath id="r{i}"><rect x="-1" y="{i*6.94-6.8:.2f}" width="310" height="7.6"><animate attributeName="width" {timing} begin="0s" dur="{delay+.55:.2f}s" fill="freeze"/></rect></clipPath>')
            # The default complete row remains readable if animation is unsupported.
            attrs += f' clip-path="url(#r{i})"'
        out.append(text(positions, f"{i*6.94:.2f}", row, 6.7, "ink", 500, attrs))
    out.append('</g>')
    return "".join(out)


def hero(palette, mobile=False, animated=True, compact=False):
    w, h = (400, 607) if mobile else ((600, 390) if compact else (900, 450))
    light = palette == PALETTES["light"]
    if mobile:
        out = [text(28, 34, "~/byrm-tsn", 13, "accent"), text(28, 79, "Bayram Tosun", 32, weight=650),
               text(28, 112, "Software. Learning. Curiosity.", 16), portrait(91, 147, .71, animated, light),
               text(28, 477, "Backend development · ML", 14), text(28, 508, "BSc + MSc Computer Science", 13, "muted"),
               text(28, 536, "London, UK", 13, "muted"), text(28, 578, "> always curious", 13, "accent")]
        cursor_x, cursor_y = 159, 578
    elif compact:
        out = [text(22, 32, "~/byrm-tsn", 14, "accent"), portrait(23, 72, .66, animated, light),
               text(265, 93, "Bayram Tosun", 32, weight=650), text(265, 128, "Software. Learning.", 17),
               text(265, 155, "Curiosity.", 17), text(265, 206, "Backend development", 17),
               text(265, 235, "Machine learning", 17), text(265, 281, "BSc + MSc", 16, "muted"),
               text(265, 307, "Computer Science", 16, "muted"), text(265, 340, "London, UK", 16, "muted"),
               text(22, 372, "> always curious", 13, "accent")]
        cursor_x, cursor_y = 153, 372
    else:
        out = [portrait(48, 37, .90, animated, light), text(390, 64, "~/byrm-tsn", 13, "accent"),
               text(386, 128, "Bayram Tosun", 46, weight=650), text(390, 172, "Software. Learning. Curiosity.", 20),
               text(390, 237, "Backend development", 17), text(390, 267, "Machine learning", 17),
               text(390, 317, "BSc + MSc Computer Science", 14, "muted"), text(390, 346, "London, UK", 14, "muted"),
               text(390, 400, "> always curious", 14, "accent")]
        cursor_x, cursor_y = 531, 400
    animation = '<animate attributeName="opacity" values="1;0;1" keyTimes="0;0.5;1" dur="1.4s" calcMode="discrete" repeatCount="indefinite"/>' if animated else ""
    out.append(f'<text x="{cursor_x}" y="{cursor_y}" fill="accent" font-size="14">_{animation}</text>')
    return document(w, h, "Bayram Tosun — software, learning, curiosity", "".join(out), palette,
                    "An ASCII portrait made from my GitHub photograph. Computer Science BSc and MSc graduate in London, interested in backend development and machine learning.")


def language_rows(languages):
    ranked = sorted(languages.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 6:
        ranked = ranked[:5] + [("Other", sum(n for _, n in ranked[5:]))]
    return ranked


def stats(palette, data, mobile=False, compact=False):
    if compact:
        out = [text(24, 30, "PUBLIC ACTIVITY", 14, "accent", 600)]
        for i, (label, value) in enumerate([("Repositories", data["repositories"]), ("Stars earned", data["stars"]), ("Followers", data["followers"]), ("Contributions¹", data["contributions"]) ]):
            x = 24 + 143*i
            out += [text(x, 80, f"{value:,}", 32, weight=600), text(x, 106, label, 13, "muted")]
        out += ['<path d="M24 133H576" stroke="line"/>', text(24, 166, "LANGUAGES IN PUBLIC CODE", 14, "accent", 600)]
        total = sum(data["languages"].values())
        ranked = language_rows(data["languages"])
        shades = [palette["accent"], palette["fg"], palette["ink"], palette["muted"], "#a68fa8", "#839784"]
        pos = 24
        for i, (name, n) in enumerate(ranked):
            width = 552 * n / total
            out.append(f'<rect x="{pos:.3f}" y="185" width="{width:.3f}" height="8" fill="{shades[i]}"/>')
            pos += width
            x, y = 24 + (i % 2) * 290, 228 + (i // 2) * 29
            out += [text(x, y, "●", 11, shades[i]), text(x+19, y, name, 15), text(x+260, y, f"{100*n/total:.1f}%", 15, "muted", extra='text-anchor="end"')]
        out.append(text(24, 326, f"Updated {data['updated']} · ¹last 365 days", 12, "muted"))
        return document(600, 348, "Bayram's public GitHub statistics", "".join(out), palette, "Public profile metrics and language shares. See the accessible text summary in the README.")
    w, h = (400, 530) if mobile else (900, 310)
    out = [text(28, 35, "PUBLIC ACTIVITY", 12, "accent", 600)]
    metrics = [("Repositories", data["repositories"]), ("Stars earned", data["stars"]),
               ("Followers", data["followers"]), ("Contributions / year", data["contributions"])]
    for i, (label, value) in enumerate(metrics):
        x, y = 28 + (i % 2) * 190, 85 + (i // 2) * 88
        out += [text(x, y, f"{value:,}", 32, weight=600), text(x, y + 24, label, 12, "muted")]
    lx, ly, lw = (28, 278, 344) if mobile else (468, 35, 404)
    out.append('<path d="M28 241H372" stroke="line"/>' if mobile else '<path d="M438 28V256" stroke="line"/>')
    out.append(text(lx, ly, "LANGUAGES IN PUBLIC CODE", 12, "accent", 600))
    ranked = language_rows(data["languages"])
    total = sum(data["languages"].values())
    shades = [palette["accent"], palette["fg"], palette["ink"], palette["muted"], "#a68fa8", "#839784"]
    pos = lx
    for i, (_, n) in enumerate(ranked):
        width = lw * n / total
        out.append(f'<rect x="{pos:.3f}" y="{ly+22}" width="{width:.3f}" height="8" fill="{shades[i]}"/>')
        pos += width
    if not ranked:
        out.append(text(lx, ly + 62, "No public language data yet.", 13, "muted"))
    for i, (name, n) in enumerate(ranked):
        y = ly + 63 + 26 * i
        out += [text(lx, y, "●", 10, shades[i]), text(lx + 20, y, name, 13),
                text(lx + lw, y, f"{100*n/total:.1f}%", 13, "muted", extra='text-anchor="end"')]
    out.append(text(28, h - 22, f"Updated {data['updated']} · public data", 11, "muted"))
    return document(w, h, "Bayram's public GitHub statistics", "".join(out), palette,
                    f"{data['repositories']} public repositories, {data['stars']} stars earned, {data['followers']} followers, and {data['contributions']} contributions visible on the public calendar over the last 365 days. Language shares measure bytes in owned public non-fork repositories.")


def picture(kind, animated=False):
    sources = []
    if animated:
        sources += [
            ('(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark) and (max-width: 600px)', f'{kind}-dark-mobile-still.svg'),
            ('(prefers-reduced-motion: reduce) and (max-width: 600px)', f'{kind}-light-mobile-still.svg'),
            ('(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark) and (max-width: 1100px)', f'{kind}-dark-compact-still.svg'),
            ('(prefers-reduced-motion: reduce) and (max-width: 1100px)', f'{kind}-light-compact-still.svg'),
            ('(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)', f'{kind}-dark-still.svg'),
            ('(prefers-reduced-motion: reduce)', f'{kind}-light-still.svg'),
        ]
    sources += [('(prefers-color-scheme: dark) and (max-width: 600px)', f'{kind}-dark-mobile.svg'),
                ('(max-width: 600px)', f'{kind}-light-mobile.svg'),
                ('(prefers-color-scheme: dark) and (max-width: 1100px)', f'{kind}-dark-compact.svg'),
                ('(max-width: 1100px)', f'{kind}-light-compact.svg'),
                ('(prefers-color-scheme: dark)', f'{kind}-dark.svg')]
    alt = "Bayram Tosun. An animated ASCII head portrait made from my photograph. Backend development and machine learning. Computer Science BSc and MSc, London." if kind == "head" else "Public GitHub activity and repository language shares. Accessible text is available below."
    return '<picture>\n' + ''.join(f'  <source media="{media}" srcset="./assets/{file}">\n' for media, file in sources) + f'  <img src="./assets/{kind}-light.svg" width="100%" alt="{alt}">\n</picture>'


def readme(data):
    languages = ", ".join(f"{name} {100*n/sum(data['languages'].values()):.1f}%" for name, n in language_rows(data["languages"])) or "No public language data yet."
    return f'''{picture("head", animated=True)}

<p align="center">
  <a href="https://bayramtosun.dev"><b>Website ↗</b></a> &nbsp; · &nbsp;
  <a href="mailto:bayramtosun@outlook.com"><b>Email ↗</b></a> &nbsp; · &nbsp;
  <a href="https://linkedin.com/in/bayram-tosun-a19217102"><b>LinkedIn ↗</b></a>
</p>

### A little about me

I build backend systems and explore machine learning. I enjoy turning ideas into practical software and understanding the logic underneath.

My background is in **Computer Science, at both BSc and MSc level**. My interests span backend engineering, computer vision, and cloud tooling. Away from code, I spend time with a camera — you can find that side of me at [@bayram.jpeg](https://instagram.com/bayram.jpeg).

### Tools I work with

**Languages**

<img src="https://skillicons.dev/icons?i=py,cs,swift,ts,js,cpp,c&amp;theme=dark" width="308" alt="Python, C#, Swift, TypeScript, JavaScript, C++, C">

**Web & data**

<img src="https://skillicons.dev/icons?i=django,react,html,css,postgres,mysql&amp;theme=dark" width="263" alt="Django, React, HTML, CSS, PostgreSQL, MySQL">

**Machine learning & infrastructure**

<img src="https://skillicons.dev/icons?i=pytorch,tensorflow,docker,git,linux,gcp&amp;theme=dark" width="263" alt="PyTorch, TensorFlow, Docker, Git, Linux, Google Cloud">

### On GitHub

<!-- BEGIN AUTO:stats -->
{picture("stats")}

<details>
<summary>About these numbers · accessible text</summary>

Updated **{data['updated']}**. **{data['repositories']} public repositories**, **{data['stars']} stars earned** on owned non-fork repositories, **{data['followers']} followers**, and **{data['contributions']} contributions** visible on my public calendar over the last 365 days.

**Language shares:** {languages}

Language shares measure code bytes in my public, non-fork repositories; they are not a measure of proficiency. The cards refresh daily through [GitHub Actions](https://github.com/byrm-tsn/byrm-tsn/actions/workflows/refresh-profile.yml).

</details>
<!-- END AUTO:stats -->

### Elsewhere

[Photography ↗](https://instagram.com/bayram.jpeg) &nbsp; · &nbsp; [Writing ↗](https://medium.com/@bayramtosun) &nbsp; · &nbsp; [X ↗](https://x.com/9byrmtsn) &nbsp; · &nbsp; [Buy me a coffee ↗](https://www.buymeacoffee.com/bayramtosun)

<sub>Find me at <a href="https://bayramtosun.dev">bayramtosun.dev</a> or say hello at <a href="mailto:bayramtosun@outlook.com">bayramtosun@outlook.com</a>.</sub>

<br><br>
<img src="https://komarev.com/ghpvc/?username=byrm-tsn&amp;label=Profile+views&amp;color=80705b&amp;style=flat-square" alt="Profile views">
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
        for mobile, compact in ((False, False), (True, False), (False, True)):
            suffix = theme + ("-mobile" if mobile else ("-compact" if compact else ""))
            for animated in (False, True):
                name = f"head-{suffix}" + ("" if animated else "-still") + ".svg"
                (ASSETS / name).write_text(hero(palette, mobile, animated, compact))
            (ASSETS / f"stats-{suffix}.svg").write_text(stats(palette, data, mobile, compact))
    target = ROOT / "README.md"
    generated = readme(data)
    target.write_text(generated if "--full" in sys.argv else update_stats_block(target.read_text(), generated))
    print("Rendered profile, 12 portrait assets, and 6 statistics assets.")


if __name__ == "__main__":
    main()
