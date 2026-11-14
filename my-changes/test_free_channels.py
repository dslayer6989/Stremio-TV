"""Offline checks for free_channels.py. Run: python3 -m unittest my-changes/test_free_channels.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import free_channels as fc

GUIDE = {
    "KAAL-DT.us_locals1", "KERO-DT.us_locals1",
    "3ABN.Kids.Network.us2", "Golf.Channel.HD.us2", "Weather.Nation.TV.HD.us2",
    "Game.Show.Network.HD.us2", "Court.TV.us2", "Comet.us2", "Comet.us",
}


class FreeChannelMatching(unittest.TestCase):
    def setUp(self):
        self.index = fc.build_guide_index(GUIDE)

    def test_local_station_needs_exact_callsign(self):
        self.assertEqual(fc.pick(self.index, "ABC.us@KAAL", "ABC KAAL"), ("KAAL-DT.us_locals1", True))
        self.assertEqual(fc.pick(self.index, "ABC.us@KEROTV", "ABC KERO-TV"), ("KERO-DT.us_locals1", True))
        self.assertIsNone(fc.pick(self.index, "ABC.us@KXYZ", "ABC KXYZ"))

    def test_cable_channel_needs_exact_name(self):
        self.assertEqual(fc.pick(self.index, "CourtTV.us@SD", "Court TV"), ("Court.TV.us2", False))
        self.assertEqual(fc.pick(self.index, "3ABNKids.us@SD", "3ABN Kids"), ("3ABN.Kids.Network.us2", False))

    def test_lookalikes_do_not_get_another_channels_guide(self):
        self.assertIsNone(fc.pick(self.index, "30AGolfKingdom.us@SD", "30A Golf Kingdom"))
        self.assertIsNone(fc.pick(self.index, "30ALionelNation.us@SD", "30A Lionel Nation"))
        self.assertIsNone(fc.pick(self.index, "30ATheBeachShow.us@SD", "30A The Beach Show"))

    def test_ambiguous_guide_name_is_skipped(self):
        index = fc.build_guide_index({"Comet.us2", "Comet.HD.us2"})
        self.assertIsNone(fc.pick(index, "Comet.us@SD", "Comet"))

    def test_playlist_flags_and_variants(self):
        text = (
            '#EXTINF:-1 tvg-id="Comet.us@SD",Comet (720p)\nhttp://x/a.m3u8\n'
            '#EXTINF:-1 tvg-id="Bad.us@SD",Bad (1080p) [Geo-blocked]\nhttp://x/b.m3u8\n'
            '#EXTINF:-1 tvg-id="Odd.us@SD",Odd [Not 24/7]\nhttp://x/c.m3u8\n'
            '#EXTINF:-1,No Id\nhttp://x/d.m3u8\n'
        )
        self.assertEqual(fc.parse_playlist(text), [("Comet.us@SD", "Comet")])

    def test_non_us_and_geo_flagged_entries_are_skipped(self):
        text = (
            '#EXTINF:-1 tvg-id="Discovery.Channel.it",Discovery Channel\nhttp://x/a.m3u8\n'
            '#EXTINF:-1 tvg-id="Blaze.uk",Blaze Ⓖ\nhttp://x/b.m3u8\n'
            '#EXTINF:-1 tvg-id="Fuse.us@East",Fuse Ⓢ\nhttp://x/c.m3u8\n'
        )
        self.assertEqual(fc.parse_playlist(text), [("Fuse.us@East", "Fuse")])
        self.assertEqual(fc.canonical_key("Comet.us@SD"), fc.canonical_key("Comet.us"))
        self.assertNotEqual(fc.canonical_key("ABC.us@KAAL"), fc.canonical_key("ABC.us"))


if __name__ == "__main__":
    unittest.main()
