# Built-in live playback fallback

Observed on sideloaded iOS Stremio 2.0.8 b23 / core 0.6.5: scheduled
programmes appear as ordinary episodes, including Upcoming labels, and the
selected programme has no playback options. Production serves the NFL Network
channel stream resource (HTTP 200) but not its EPG programme ID (HTTP 404).
We do not have a device request trace, so the exact client failure is unproven.

## Change

- Channel catalog previews and metadata omit `defaultVideoId` so clients open
  channel details without an automatic redirect back to the same identity.
- Channel detail metadata includes an explicit, untimed `Watch live` video
  using a distinct `{channelId}:0:0` ID. Its historical `released` value avoids an Upcoming gate;
  it describes live playback, not an actual historical broadcast.
- Following a failed device test of the untimed entry, the live video explicitly
  declares `season: 0` and `episode: 0` for clients requiring series coordinates.
  The builder publishes both `/stream/tv/{channelId}.json` and
  `/stream/tv/{channelId}:0:0.json` with identical feed options, headers, ordering,
  cache hints and build identity. Both production and local-test channels use
  the same resource writer. Timed guide programmes keep their original metadata.
- Date-filtered EPG catalogs retain only their original timed programmes.
  Detail metadata retains the timed programmes and native scheduling hint.
- The untimed Watch live video also includes `streams` using the exact serialized
  options served by both stream endpoints. This is the SDK's documented inline
  video playback path, avoiding a second addon stream lookup for clients that
  consume it. Only already selected production/local-test feed options are used;
  headers, order, source labels and build identity remain identical.
- No timed programme-ID aliases, catch-up claims, alternate
  addon, new upstream requests, or source-selection changes are introduced.

This is a persistent compatibility path, not automatic detection of a failed
player: static GitHub Pages cannot inspect a client version or playback result.
Native guide clients continue using the channel stream resource. Legacy clients
select Watch live in channel details using the distinct episode stream resource.

## October 27 device evidence

The user confirmed the Season 0/Episode 0 entry is visible on FOX 29. Tapping it
briefly animates/loading appears, then returns to the same details screen.
The previous implementation reused the parent ID for the live video and set
that same ID as `defaultVideoId`. This suggests navigation re-entry, but the
screenshots do not establish the exact request sequence or prove the cause.
The distinct episode ID and removal of the automatic redirect address that
ambiguity. Actual device validation remains required after publication.

The next device test reached stream selection but displayed "No addons were
able to provide streams" on both FOX 29 and HGTV. Direct HTTP checks of native
and episode endpoints returned 200 and nonempty streams (FOX 29: one; HGTV:
three), including percent-encoded episode IDs. The production manifest supports
type tv and the stremiotv_ ID prefix. These checks do not establish the phone's
actual request path, cached addon manifest, or HTTP response. Inline Watch live
streams are an additional compatibility attempt, not a confirmed root-cause fix.
The SDK documents inline streams as exclusive for that video; our retained
stream endpoints continue to support clients using resource lookup. Timed EPG
programmes never receive inline live streams.

## Validation and limitations

Focused tests cover distinct channel/video identity without an auto redirect,
generated episode resource lookup and exact payload parity, explicit available live
entry, unchanged future/timed programmes and date-filtered guide behavior,
input immutability, and channels without EPG or artwork. Existing native EPG
generated-output tests remain applicable. Normal PR validation must pass the
real-build logo audit and protected-channel deployment guard before merge.

The fallback does not fix incompatible codecs, upstream outages, or any mobile
transport/header restriction. Device compatibility remains unconfirmed until
tested in the reported iOS build. Restart/refresh the existing addon after the
new build publishes; reinstalling the app is not part of this change.

Protocol references:
- https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/epg.md
- https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/api/responses/meta.md
- https://github.com/Stremio/stremio-core/blob/master/src/deep_links/mod.rs

The core master implementation is supporting design evidence, not proof of
the exact behavior of the installed core 0.6.5 binary.
