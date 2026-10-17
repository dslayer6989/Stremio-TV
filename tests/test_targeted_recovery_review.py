"""Regressions from actual October 15 candidate-selection and local-test evidence."""
import json
from pathlib import Path
import unittest

import build


class TargetedRecoveryReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(Path("config.json").read_text())

    def test_natgeo_hd_east_enters_curated_candidate_pool_without_merging_other_services(self):
        rows = build.parse_m3u(
            '#EXTM3U\n#EXTINF:-1 tvg-id="NationalGeographic.us@HDEast",National Geographic HD East\n'
            'http://example.test/natgeo/index.m3u8\n'
            '#EXTINF:-1 tvg-id="NationalGeographicLatinAmerica.us@Panregional",NatGeo Latin America\n'
            'http://example.test/natgeo-latam/index.m3u8\n'
            '#EXTINF:-1 tvg-id="Fox.us@WTXFTV",Fox 29\n'
            'http://example.test/fox29/index.m3u8\n',
            {"name": "IPTV-org US", "family": "iptv-org"},
        )
        mapped = build.canonicalize_approved_sources(rows, self.config)
        self.assertTrue(build.entry_matches_pattern(mapped[0], "NationalGeographic.us"))
        self.assertEqual(mapped[0]["source_tvg_id"], "NationalGeographic.us@HDEast")
        self.assertFalse(build.entry_matches_pattern(mapped[1], "NationalGeographic.us"))
        self.assertEqual(mapped[2]["tvg_id"], "Fox.us@WTXFTV")
        self.assertFalse(any(row.get("local_verified_override") for row in mapped))

    def test_user_failed_hallmark_endpoint_cannot_reappear_via_another_playlist(self):
        failed = "http://206.212.244.63/84/index.m3u8"
        rows = [
            {"tvg_id": "HallmarkChannel.us", "url": failed, "family": "shovo"},
            {"tvg_id": "HallmarkChannel.us@East", "url": failed, "family": "github-playlist"},
            {"tvg_id": "HallmarkChannel.us", "url": "https://example.test/other.m3u8"},
            {"tvg_id": "HallmarkMystery.us", "url": failed},
        ]
        kept, rejected = build.apply_stream_quarantine(rows, self.config)
        self.assertEqual(len(rejected), 2)
        self.assertEqual(kept, rows[2:])


if __name__ == "__main__":
    unittest.main()
