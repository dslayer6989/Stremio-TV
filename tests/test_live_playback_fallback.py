import copy
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote, unquote

import build


class LivePlaybackFallbackTests(unittest.TestCase):
    def setUp(self):
        self.channel = {
            "id": "stremiotv_test", "name": "Test TV", "epg_matched": True,
            "logo": "https://example.test/logo.png",
            "streams": [{"url": "https://example.test/live.m3u8"}],
        }
        self.programmes = [{
            "id": "stremiotv_test:epg:2099-01-01T12:00:00Z",
            "title": "Future programme", "released": "2099-01-01T12:00:00Z",
            "startTime": "2099-01-01T12:00:00Z",
            "endTime": "2099-01-01T13:00:00Z",
        }]

    def test_live_navigation_is_distinct_from_parent_without_auto_redirect(self):
        preview = build.channel_preview(self.channel)
        detail = build.channel_meta(self.channel, self.programmes, live_fallback=True)
        for meta in (preview, detail):
            self.assertNotIn("defaultVideoId", meta["behaviorHints"])
            self.assertTrue(meta["behaviorHints"]["isLive"])
        self.assertEqual(detail["videos"][0]["id"], "stremiotv_test:0:0")
        self.assertNotEqual(detail["videos"][0]["id"], detail["id"])

    def test_generated_episode_route_serves_same_options_as_native_channel(self):
        detail = build.channel_meta(self.channel, self.programmes, live_fallback=True)
        payload = {
            "streams": [{"url": "https://example.test/live.m3u8", "name": "Primary",
                         "behaviorHints": {"notWebReady": True, "proxyHeaders": {
                             "request": {"Referer": "https://example.test/player"}}}},
                        {"url": "https://backup.test/live.m3u8", "name": "Backup 1"}],
            "stremioTvBuild": {"build_id": "test"}, "cacheMaxAge": 300,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build.write_channel_stream_resources(root, self.channel, payload)
            # Client links percent-encode ':'; the decoded static resource path
            # must exist for the ID actually selected from channel metadata.
            selected = unquote(quote(detail["videos"][0]["id"], safe=""))
            episode = json.loads((root / "stream" / "tv" / f"{selected}.json").read_text())
            native = json.loads((root / "stream" / "tv" / f"{detail['id']}.json").read_text())
            self.assertEqual(episode, payload)
            self.assertEqual(native, episode)
            self.assertEqual(len(list((root / "stream" / "tv").iterdir())), 2)

    def test_live_entry_is_available_without_claiming_a_scheduled_programme(self):
        detail = build.channel_meta(self.channel, self.programmes, live_fallback=True)
        live = detail["videos"][0]
        self.assertEqual(live["title"], "Watch live")
        self.assertEqual(live["season"], 0)
        self.assertEqual(live["episode"], 0)
        self.assertTrue(live["available"])
        self.assertEqual(live["released"], "1970-01-01T00:00:00Z")
        self.assertIn("not recordings", live["overview"])
        for field in ("startTime", "endTime", "streams"):
            self.assertNotIn(field, live)

    def test_published_metadata_and_routes_preserve_identical_selected_options(self):
        payload = {
            "streams": [{"url": "https://example.test/live.m3u8", "name": "Primary",
                         "behaviorHints": {"notWebReady": True, "proxyHeaders": {
                             "request": {"Referer": "https://example.test/player"}}},
                         "stremioTvBuild": {"build_id": "test"}},
                        {"url": "https://backup.test/live.m3u8", "name": "Backup 1"}],
            "stremioTvBuild": {"build_id": "test"}, "cacheMaxAge": 60,
        }
        original = copy.deepcopy((self.channel, self.programmes, payload))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build.write_channel_playback_resources(root, self.channel, self.programmes, payload)
            detail = json.loads((root / "meta/tv/stremiotv_test.json").read_text())
            live = detail["meta"]["videos"][0]
            # A client that consumes inline streams needs no second HTTP lookup.
            self.assertEqual(live["streams"], payload["streams"])
            self.assertEqual(detail["meta"]["videos"][2:], self.programmes)
            self.assertTrue(detail["meta"]["behaviorHints"]["hasScheduledVideos"])
            for video_id in (self.channel["id"], live["id"]):
                route = json.loads((root / "stream/tv" / f"{video_id}.json").read_text())
                self.assertEqual(route, payload)
                self.assertEqual(live["streams"], route["streams"])
            # A live client may select the parent channel, not the episode ID.
            # Resolve inline streams using the same ID match as Stremio core.
            for selected_id in (self.channel["id"], live["id"]):
                selected = next(v for v in detail["meta"]["videos"] if v["id"] == selected_id)
                self.assertEqual(selected["streams"], payload["streams"])
        self.assertEqual((self.channel, self.programmes, payload), original)

    def test_empty_options_do_not_publish_an_exclusive_empty_inline_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            detail = build.write_channel_playback_resources(
                Path(tmp), self.channel, [], {"streams": []},
            )
            for video in detail["videos"]:
                self.assertNotIn("streams", video)

    def test_plain_channel_selection_has_no_season_or_episode_or_redirect(self):
        detail = build.channel_meta(
            self.channel, self.programmes, live_fallback=True,
            live_streams=[{"url": "https://example.test/live.m3u8"}],
        )
        selected = next(v for v in detail["videos"] if v["id"] == detail["id"])
        self.assertEqual(selected["title"], self.channel["name"])
        self.assertTrue(selected["streams"])
        self.assertTrue(selected["available"])
        for field in ("season", "episode", "startTime", "endTime"):
            self.assertNotIn(field, selected)
        self.assertNotIn("defaultVideoId", detail["behaviorHints"])
        self.assertEqual(len({v["id"] for v in detail["videos"]}), len(detail["videos"]))

    def test_native_guide_never_inlines_live_options_into_programmes(self):
        detail = build.channel_meta(
            self.channel, self.programmes,
            live_streams=[{"url": "https://example.test/live.m3u8"}],
        )
        self.assertEqual(detail["videos"], self.programmes)
        self.assertTrue(all("streams" not in p for p in detail["videos"]))

    def test_native_guide_and_future_programmes_are_unchanged(self):
        original = copy.deepcopy((self.channel, self.programmes))
        guide = build.channel_meta(self.channel, self.programmes)
        detail = build.channel_meta(self.channel, self.programmes, live_fallback=True)
        self.assertEqual(guide["videos"], self.programmes)
        self.assertEqual(detail["videos"][2:], self.programmes)
        self.assertTrue(guide["behaviorHints"]["hasScheduledVideos"])
        self.assertTrue(detail["behaviorHints"]["hasScheduledVideos"])
        self.assertNotIn("available", detail["videos"][2])
        self.assertEqual((self.channel, self.programmes), original)

    def test_channel_without_epg_still_has_live_playback(self):
        self.channel["epg_matched"] = False
        self.channel.pop("logo")
        detail = build.channel_meta(self.channel, [], live_fallback=True)
        self.assertEqual(len(detail["videos"]), 2)
        self.assertNotIn("hasScheduledVideos", detail["behaviorHints"])
        self.assertNotIn("thumbnail", detail["videos"][0])


if __name__ == "__main__":
    unittest.main()
