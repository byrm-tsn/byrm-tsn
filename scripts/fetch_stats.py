"""Fetch only public profile data; leave published files intact on failure."""

import json
import os
import re
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = "byrm-tsn"


def get(url, api=False):
    headers = {"User-Agent": "byrm-tsn-profile", "Accept": "text/html"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        token = os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=30) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def api(path):
    return json.loads(get("https://api.github.com/" + path, api=True))


class Calendar(HTMLParser):
    """Join public calendar cells to their accessible tooltip counts."""

    def __init__(self):
        super().__init__()
        self.dates = {}
        self.counts = {}
        self.current = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "id" in attrs:
            self.dates[attrs["id"]] = attrs["data-date"]
        if tag == "tool-tip":
            self.current = attrs.get("for")
            self.parts = []

    def handle_data(self, data):
        if self.current:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.current:
            match = re.match(r"\s*(No|[\d,]+) contributions? on ", "".join(self.parts))
            if match:
                self.counts[self.current] = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            self.current = None

    def days(self, end):
        start = end - timedelta(days=364)
        result = {}
        for key, day in self.dates.items():
            if start <= date.fromisoformat(day) <= end:
                if key not in self.counts:
                    raise ValueError("Public contribution calendar is missing a count")
                result[day] = self.counts[key]
        if len(result) != 365:
            raise ValueError(f"Expected 365 public calendar days, got {len(result)}")
        return dict(sorted(result.items()))


def collect():
    today = datetime.now(timezone.utc).date()
    user = api(f"users/{USER}")
    repos = []
    page = 1
    while True:
        batch = api(f"users/{USER}/repos?type=owner&per_page=100&page={page}")
        repos.extend(r for r in batch if not r["private"] and r["owner"]["login"].lower() == USER)
        if len(batch) < 100:
            break
        page += 1
    originals = [r for r in repos if not r["fork"]]
    languages = Counter()
    for repo in originals:
        # Never send credentials to URLs taken from a response.
        languages.update(api(f"repos/{USER}/{repo['name']}/languages"))
    calendar = Calendar()
    # Deliberately unauthenticated, matching what a public visitor can see.
    calendar.feed(get(f"https://github.com/users/{USER}/contributions"))
    days = calendar.days(today)
    return {
        "updated": today.isoformat(),
        "repositories": len(repos),
        "stars": sum(r["stargazers_count"] for r in originals),
        "followers": user["followers"],
        "contributions": sum(days.values()),
        "activity": days,
        "languages": dict(sorted(languages.items(), key=lambda item: (-item[1], item[0]))),
    }


if __name__ == "__main__":
    data = collect()
    target = ROOT / "assets" / "stats.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(target)
    print(f"Updated public stats for {USER}: {data['updated']}")
