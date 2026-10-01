# Maintaining this profile

The portrait consists of positioned text characters derived from Bayram's public
GitHub avatar, tightly cropped to his head with the background excluded. The text
grid accounts for the character cell aspect ratio to preserve facial proportions.
SVG is the container, not an illustration of the subject. Its reveal
takes about two seconds; only the small prompt cursor continues blinking. Explicit
still assets are selected for reduced-motion visitors. There are separate phone
layouts and light/dark character densities.

## Personal edits

Edit `README.md` normally outside `BEGIN AUTO:stats` / `END AUTO:stats`.
The daily refresh changes only that block and the generated assets. It refuses to
overwrite the README if the markers are missing.

## Regeneration

Python 3.12, standard library only:

```sh
python scripts/fetch_stats.py
python scripts/render_profile.py
python -m unittest discover -s scripts -p 'test_*.py'
```

`GH_TOKEN` is optional locally and is passed to api.github.com only. In Actions,
the built-in repository token is used; no personal token or external server is
required. All repository requests explicitly exclude private repositories.
Calendar data is requested without authentication to match a public visitor.
A failed fetch leaves the previous published data intact.

Public repositories include forks; stars and language bytes count owned public
non-fork repositories. Contributions cover the last 365 UTC dates and use the
counts shown by GitHub's public calendar, including any anonymized private counts
the profile owner has chosen to make public. Language shares are not proficiency.

To recreate the ASCII source, install Pillow in a local environment and run:

```sh
python scripts/make_portrait.py /path/to/github-avatar.jpg
python scripts/render_profile.py
```

The crop and silhouette in `make_portrait.py` are fitted to the current avatar;
adjust them for a different photograph. Daily Actions runs do not need Pillow.
`render_profile.py --full` rebuilds the entire README from its template and will
replace personal README edits; use it only intentionally.

The refresh is scheduled daily at 06:23 UTC and can be run manually under Actions.
GitHub may delay scheduled runs or disable schedules on inactive repositories.
See [GitHub's schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

Technology icons are served by [Skill Icons](https://github.com/tandpfun/skill-icons).
The profile view counter is served by [GitHub Profile Views Counter](https://github.com/antonkomarev/github-profile-views-counter).
