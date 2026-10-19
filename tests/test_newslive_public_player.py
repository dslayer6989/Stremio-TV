import datetime as dt
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import build

PAGE = 'https://www.newslive.com/business/cnbc-live-free.html'
SOURCE = {'url': PAGE, 'tvg_id': 'CNBC.us', 'format': 'public-player-page'}


def url(**changes):
    expires = int(dt.datetime.now(dt.timezone.utc).timestamp()) + 20000
    base = f'https://stream.livenewsplay.com:9555/hls/cnbcsd/index.m3u8?token=public-example&expires={expires}&sig=public-signature'
    return changes.get('value', base)


def html(value):
    return 'const streamURL = ' + json.dumps(value).replace('/', '\\/') + ';'


class NewsLivePublicPlayerTests(unittest.TestCase):
    def test_preserves_public_signature_and_normal_player_headers(self):
        value = url()
        entries = build._parse_public_player_page(html(value), SOURCE)
        self.assertEqual(len(entries), 1)
        row = entries[0]
        self.assertEqual(row['url'], value)
        self.assertEqual(row['headers']['Referer'], PAGE)
        self.assertEqual(row['source_type'], 'public-third-party-player')
        self.assertNotIn('local_verified_override', row)
        self.assertNotIn('official', row['source_type'])

    def test_expiring_and_malformed_values_fail_closed(self):
        value = url().split('?')[0] + '?expires=1'
        self.assertEqual(build._parse_public_player_page(html(value), SOURCE), [])
        self.assertEqual(build._parse_public_player_page('const streamURL = getToken();', SOURCE), [])
        self.assertEqual(build._parse_public_player_page('const streamURL = "invalid";', SOURCE), [])

    def test_other_hosts_channels_and_credentials_are_rejected(self):
        for value in [url().replace('stream.livenewsplay.com', 'attacker.example'),
                      url().replace('https://', 'http://'),
                      url().replace('/cnbcsd/', '/cnn/'),
                      url().replace('https://', 'https://user:password@')]:
            self.assertEqual(build._parse_public_player_page(html(value), SOURCE), [])
        for source in [{**SOURCE, 'url': 'https://attacker.example/player'},
                       {**SOURCE, 'tvg_id': 'CNBCWorld.us'}]:
            self.assertEqual(build._parse_public_player_page(html(url()), source), [])

    def test_enters_normal_targeted_pipeline_without_override(self):
        config = json.loads(Path('config.json').read_text())
        config['discovery']['targeted_source_families']['sources'] = [SOURCE]
        with patch.object(build, '_target_ids_for_source_hunt', return_value=['CNBC.us']), \
             patch.object(build, '_fetch_public_text', return_value=(html(url()), PAGE)):
            entries, rows, targets = build.discover_targeted_source_families(config, [])
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]['targeted_scan'])
        self.assertFalse(entries[0].get('local_verified_override', False))
        self.assertEqual(targets, ['CNBC.us'])
        self.assertEqual(rows[-1]['candidates_found'], 1)
