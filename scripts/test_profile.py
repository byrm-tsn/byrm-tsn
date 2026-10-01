import unittest
from unittest.mock import patch
from datetime import date, timedelta
from xml.etree import ElementTree as ET

from fetch_stats import Calendar, collect
from render_profile import PALETTES, hero, language_rows, activity_card, language_card, update_stats_block


class ProfileTests(unittest.TestCase):
    def calendar(self, end):
        parser = Calendar()
        for i in range(365):
            day = (end - timedelta(days=i)).isoformat()
            parser.feed(f'<td id="day-{i}" data-date="{day}"></td>')
        # Tooltip order need not match cell order; commas must parse as integers.
        for i in reversed(range(365)):
            count = "1,234 contributions" if i == 0 else "No contributions"
            parser.feed(f'<tool-tip for="day-{i}">{count} on October 1st.</tool-tip>')
        return parser

    def test_calendar_joins_ids_and_handles_leap_day(self):
        end = date(2024, 3, 1)
        days = self.calendar(end).days(end)
        self.assertEqual(len(days), 365)
        self.assertIn("2024-02-29", days)
        self.assertEqual(sum(days.values()), 1234)

    def test_missing_count_does_not_silently_become_zero(self):
        end = date(2026, 10, 1)
        parser = self.calendar(end)
        del parser.counts["day-20"]
        with self.assertRaises(ValueError):
            parser.days(end)

    def test_incomplete_calendar_is_rejected(self):
        with self.assertRaises(ValueError):
            Calendar().days(date(2026, 10, 1))

    def test_grouping_preserves_language_totals(self):
        languages = {f"language-{i}": i for i in range(1, 12)}
        grouped = language_rows(languages)
        self.assertEqual(len(grouped), 6)
        self.assertEqual(sum(n for _, n in grouped), sum(languages.values()))
        self.assertEqual(language_rows({}), [])

    def test_refresh_preserves_personal_copy(self):
        existing = 'My edited bio\n<!-- BEGIN AUTO:stats -->old<!-- END AUTO:stats -->\nMy links'
        generated = 'default bio<!-- BEGIN AUTO:stats -->new<!-- END AUTO:stats -->default links'
        self.assertEqual(update_stats_block(existing, generated), existing.replace('>old<', '>new<'))
        with self.assertRaises(ValueError):
            update_stats_block('No markers', generated)

    def test_public_refresh_preserves_dated_account_total(self):
        # A visibility change can increase the public subset without changing
        # the account total. Do not add public growth to a stale private count.
        for public_count in (4, 5):
            repos = [dict(private=False, owner=dict(login='byrm-tsn'), fork=True)
                     for _ in range(public_count)]
            with patch('fetch_stats.api', side_effect=[dict(followers=8), repos]), \
                 patch('fetch_stats.get', return_value=''), \
                 patch.object(Calendar, 'days', return_value={}), \
                 patch('pathlib.Path.read_text', return_value='{"count":6,"verified":"2026-09-20"}'):
                data = collect()
            self.assertEqual(data['repositories'], 6)
            self.assertEqual(data['repositories_verified'], '2026-09-20')
            self.assertEqual(data['public_repositories'], public_count)

    def test_all_svg_variants_and_empty_languages(self):
        data = dict(updated='2026-10-01', repositories=0, repositories_verified='2026-10-01', stars=0, followers=0, contributions=0, languages={})
        for palette in PALETTES.values():
            ET.fromstring(activity_card(palette, data))
            ET.fromstring(language_card(palette))
            for animated in (False, True):
                root = ET.fromstring(hero(palette, animated))
                animations = root.findall('.//{http://www.w3.org/2000/svg}animate')
                self.assertEqual(bool(animations), animated)


if __name__ == '__main__':
    unittest.main()
