"""Discovery eligibility must not grant production approval or relax access gates."""
import datetime as dt
import json
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

import build
import playlist_scrub as scrub
from research import fresh_origin_discovery as fresh


class DiscoveryEligibilityTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(Path('config.json').read_text())
        self.now = dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc)

    def test_both_former_private_only_channels_enter_public_target_selection(self):
        ids = ['WPSG.us', 'NBCSportsPhiladelphiaPlus.us']
        self.assertFalse(build._private_connector_only_ids(self.config))
        self.assertFalse(fresh.PRIVATE_IDS)
        for channel in ids:
            self.assertEqual(fresh.exact_target(
                {'tvg_id': channel, 'name': channel}, ids)[0], channel)

    def test_public_path_and_signed_session_links_survive_without_modification(self):
        for url in [
            'https://cdn.example.com/live/us/hgtv/master.m3u8',
            'https://cdn.example.com/play/region/hgtv/master.m3u8',
            'https://cdn.example.com/api/stream/us/hgtv/master.mpd',
            'https://cdn.example.com/hgtv.mpd?token=public&sessionid=public-session&expires=9999999999',
        ]:
            with self.subTest(url=url):
                entry = {'tvg_id': 'HGTV.us', 'url': url, 'headers': {}}
                self.assertTrue(scrub.safe_entry(entry, self.config, self.now))
                self.assertEqual(entry['url'], url)

    def test_explicit_credentials_and_xtream_paths_remain_excluded(self):
        for url in [
            'https://user:password@example.com/master.mpd',
            'https://example.com/live/user/password/123.m3u8',
            'https://example.com/api/stream/user@example.com/123/hgtv.mpd',
            'https://example.com/hgtv.mpd?username=user&password=password',
        ]:
            with self.subTest(url=url):
                self.assertFalse(scrub.safe_entry(
                    {'tvg_id': 'HGTV.us', 'url': url, 'headers': {}}, self.config, self.now))

    def dash_probe(self, manifest, decoder_status='ok'):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = 'https://cdn.example.com/hgtv.mpd'
        response.read.return_value = manifest.encode()
        opener = MagicMock()
        opener.open.return_value = response
        decoder = {'status': decoder_status}
        with patch.object(scrub.urllib.request, 'build_opener', return_value=opener), \
             patch.object(scrub.build, '_validate_direct_media_survival', return_value=decoder) as decode:
            result = scrub.probe_research_candidate(
                {'url': 'https://cdn.example.com/hgtv.mpd?token=public', 'headers': {}}, self.config)
        return result, decode.call_count

    def test_clear_dash_reaches_decoder_and_does_not_convert_failures_to_success(self):
        manifest = '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="dynamic"><Period/></MPD>'
        result, calls = self.dash_probe(manifest)
        self.assertEqual(calls, 1)
        self.assertEqual(result[0]['status'], 'ok')
        result, calls = self.dash_probe(manifest, 'failed')
        self.assertEqual(calls, 1)
        self.assertEqual(result[0]['status'], 'failed')

    def test_protected_or_invalid_dash_never_reaches_decoder(self):
        for manifest in [
            '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011"><Period><ContentProtection/></Period></MPD>',
            '<html>login required</html>',
            'not XML',
        ]:
            with self.subTest(manifest=manifest):
                result, calls = self.dash_probe(manifest)
                self.assertEqual(calls, 0)
                self.assertEqual(result[0]['status'], 'failed')

    def test_dash_triage_remains_unapproved_even_after_decoder_pass(self):
        row = {'url': 'https://cdn.example.com/hgtv.mpd', 'headers': {},
               'tvg_id': 'HGTV.us', 'new_provider_host': True, 'first_seen': '',
               'key': 'test', 'needs_probe': True}
        with patch.object(scrub, 'probe_research_candidate', return_value=(
                {'status': 'ok'}, {'status': 'ok'})):
            scrub.triage([row], self.config, 1, set())
        self.assertFalse(row['probe']['production_approved'])
        self.assertFalse(row['probe']['burn_in_completed'])
