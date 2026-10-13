# Legacy source recovery audit — HBO Movies and Cinemax Classics (2026-10-12)

**Decision: no stream promotion.** Evidence supports a channel-name migration for both, but not a newly authorized, healthy, independent media origin. Research only; existing stream policies, manually verified exceptions and kill switches remain unchanged.

## Identity reconciliation — confirmed

| Current curated ID | Legacy network name / historical `tvg-id` | Source of naming |
| --- | --- | --- |
| `HBOMovies.us` (East as applicable) | HBO Zone / `HBOZone.us@East` | HBO renamed HBO Zone to HBO Movies on Sept 4, 2025; see [Cord Cutters News](https://cordcuttersnews.com/hbo-max-updates-its-linear-channel-names/) and [GTA pay-TV lineup notice](https://www.gta.net/product-announcements). |
| `CinemaxClassics.us` (East as applicable) | 5StarMax / `5StarMax.us@East` | Same September 2025 rebrand; see [TheWrap](https://www.thewrap.com/hbo-max-renames-linear-channels-rebrand/) and [GTA pay-TV lineup notice](https://www.gta.net/product-announcements). |

These are **historical identity aliases for research**, not automatic permission to turn an old labeled stream into the new channel. Full East/West identity, real live schedule, and source provenance still require confirmation. iptv-org's [guide channel map](https://github.com/iptv-org/epg) still contains old identifiers, which is a useful guide lookup key but **not** playback or currently aired content proof.

## Concrete public source matches found

Current [iptv-org US source playlist](https://github.com/iptv-org/iptv/blob/master/streams/us.m3u) labels both under the **new** names but retains their **old** URL path stems.

| Target | Public playlist entry / provenance | Project QA and independence | Result |
| --- | --- | --- | --- |
| HBO Movies (East) | `HBOMovies.us@East`, source `http://23.237.104.106:8080/USA_HBO_ZONE/index.m3u8` | Existing widely reused host; no independent origin provenance or successful FFmpeg decode established for this exact entry. iptv-org [issue #50560](https://github.com/iptv-org/iptv/issues/50560) earlier had a rejected **channel-ID validation** check; this is not a decoder success or failure. | **Research only: not qualified.** |
| Cinemax Classics (East) | `CinemaxClassics.us@East`, source `http://23.237.104.106:8080/USA_5STARMAX/index.m3u8` | **Already exact-URL quarantined** in `config.json → curation.stream_quarantine`: full decoded-primary scan and 30-second focused retry both timed out with **zero decoded frames** on Sept 25, 2026. | **Do not restore, test-list or promote unchanged.** |

Both entries share `23.237.104.106`, a high-blast-radius provider entry host that previously appeared across **26 published channels** in the repo's [upstream concentration report](v080-identity-host-backup-2026-10-12.md). This does **not** constitute two independent sources. Variants of `/tracks-v1a1/mono.m3u8` on the same host are not fresh provider origins.

Additional old HBO Zone playlists show `fl*.moveonjoy.com/HBO_ZONE`, TVPass web player, or TheTVApp web watch pages (example [older indexed playlist](https://github.com/gogetta69/TMDB-To-VOD-Playlist/blob/main/channels/m3u_formatted.dat)). Those are relays/aggregator or browser viewing leads, not authenticated evidence that an original broadcaster permits direct anonymous HLS for the exact current full-linear channel. Subscriber-path Xtream/M3U feeds, DRM player sessions, source copying and browser redirects are not admissible sources.

## Why no new Stremio Local Test candidate was created

1. An old name mapping was **proved**, not a newly licensed video origin.
2. Cinemax Classics' exact known URL is **quarantined** following repeatable zero-frame failures.
3. HBO Movies' new `tvg-id` entry is on a known shared host, without confirmed provenance, current decoder QA, or live full-linear schedule verification.
4. Neither an IPTV-org listing nor a generic `#EXTM3U` response proves playable progressing media or redistribution rights.
5. The project deliberately rejects embedded credentials, paid-session extraction, DRM circumvention, and proxy/restreaming.

No direct network media request/FFmpeg test on these unapproved third-party sources was performed during this **origin-first** review. The earlier Cinemax QA failures are historical project results, not re-tested live status.

## Safe next engineering path

- Retain the name pairs in **research identity hints only**. Do not alter production `canonical_id_aliases`, `manual_sources.json` or source selection in response to source-list titles.
- Ask network/license distributors for a directly permitted HLS source or separately approved **user-private** integration. HBO Max live Channels/entitled TV subscriptions are legitimate ways to watch but **not public addon HLS feeds**.
- Upon finding an *independent authorized origin*, confirm actual HBO Movies / Cinemax Classics East linear schedule and ownership/CDN lineage, then run full HLS advancement and 60s+ FFmpeg decoder/repeat-stall checks on an isolated research runner.
- Preserve the Cinemax exact-URL quarantine. Only a genuine new upstream URL with passing QA and authorization can qualify for a Local Test or production candidate.

**GitHub status at review:** [PR #83 merged](https://github.com/sondog001-cyber/Stremio-TV/pull/83) as `df89affd` (all-24 access audit and research-only media preflight). Last successful prior full deployment [#38328228372](https://github.com/sondog001-cyber/Stremio-TV/actions/runs/38328228372) was green; the new post-merge deployment [#38334699875](https://github.com/sondog001-cyber/Stremio-TV/actions/runs/38334699875) was still in progress when inspected. The last documented published count remains 87/111 until the newer run's artifacts establish otherwise.

**Changes resulting from this review:** One markdown research document; **zero** source/config/playlist/build/kill-switch changes, **zero** restored or promoted feeds.
