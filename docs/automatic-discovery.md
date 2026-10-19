# Automatic playlist discovery

The two-hour production build already refreshes its configured public playlists,
national targeted source lists, Philadelphia sources, public seed candidates and
IPTV-org issue signals. Newly encountered candidates for missing/unstable channels
enter the ordinary safety, identity, health, burn-in, decoder and selection gates.
GitHub-wide code search remains disabled because it hit sustained secondary rate
limits. Playlist scraping does not depend on an active ChatGPT conversation.

The `playlist-scrub` job adds a persistent view of changes across **all original
111 identities**, including potential backups for currently healthy channels.
It scans configured M3U lists plus maintained additional public research playlist documents,
deduplicates repeated exact channel/URL/header combinations, and distinguishes:

- Known candidates from the current production attempt or prior scrub inventory.
- New candidates since a retained trusted inventory.
- An initial inventory when historical evidence is unavailable.
- Previously unseen provider hostnames, which do **not** prove independent media
  ownership or delivery origins.

Sources use explicit playlist IDs and configured ID aliases; West variants,
unrelated FAST/foreign networks and wrong affiliates are excluded. Credential
paths, authentication headers, configured kill switches and exact playback
quarantines are applied before storing or probing candidates. Unsafe media URLs
are counted without being copied into the evidence artifact.

After each production attempt the scrub checks up to three unseen, queued
candidates with a segment-aware HLS probe and the existing normal direct-media
FFmpeg/repeat detector. Missing channels and newly observed hosts take priority.
The queue persists across runs, and current-build candidates are not redundantly
probed. This is initial media triage: it does not perform full promotion burn-in,
confirm programming identity, grant local exceptions, change source priority,
write production configuration, or count as a release-qualified recovery.
Ordinary builder discovery continues to reconsider its configured sources on
subsequent builds. Healthy-channel backup leads can be reviewed from the scrub.

## Execution and evidence

The job uses the existing `7 */2 * * *` production schedule. It starts **after**
`build` and `deploy`, even if either was blocked, and never gates Pages. It has
read-only repository/Actions permissions, a 20-minute timeout and advisory failure
behavior. It does not create another two-hour timer or enable GitHub code search.

Open a production Actions run and read **Playlist scrub (advisory)** in its job
summary. Download its **playlist-scrub** artifact for:

| File | Contents |
|---|---|
| `playlist-scrub.json` | Source success/errors, candidate novelty, provenance and bounded probe results |
| `playlist-scrub.md` | Compact counts and limitations |
| `playlist-scrub-state.json` | Persistent seen URLs and queued/completed media triage |

The next scrub restores the newest retained artifact from this repository's
default-branch production workflow, including runs whose deployment guard failed.
PR runs cannot supply state. Artifact history is retained for 14 days; inventory
is bounded to 5,000 recently observed entries. If prior state is missing,
expired, corrupt or inaccessible, the report says so and creates an initial
inventory rather than claiming that every old stream is newly discovered.
Incomplete source reads never establish a removal or wipe earlier observations.

## What still benefits from research

The scrub finds changes **inside the configured sources**. Finding entirely new
projects, player APIs or independently operated media origins still requires
targeted research and source review. A newly found playlist or hostname often
recycles the same upstream media. Identity, actual programming and resilience
must be established before considering a new feed a recovered channel or backup.

To reproduce without GitHub API history:

```sh
python assemble_build.py
python playlist_scrub.py --baseline-dir site/diagnostics --probe-limit 0 --out scrub-results
python playlist_scrub.py --baseline-dir site/diagnostics --previous scrub-results/playlist-scrub-state.json --probe-limit 0 --out scrub-replay
```

The CLI performs public metadata reads; `--probe-limit 0` skips media triage.
No API token is sent to playlist or media hosts. GitHub authentication is used
only to read trusted prior artifacts, with bearer credentials stripped on the
artifact download redirect.

## Twenty-link search target

Each run aims for **20 previously unseen stream URLs** for the original111
channels, using `--new-link-target 20`. Reads proceed in batches of four and stop
when the target is met, every distinct available playlist has been read, or the
600-second (10-minute) search budget expires. A batch can yield more than20; all discoveries
are retained. Re-reading an unchanged playlist cannot produce genuinely new links.
The report gives the target, distinct new URL count and exact stopping reason.
Mirrors, header changes and the same URL under several IDs count only once.
An initial inventory does not count as new discoveries. Source lists are capped
at128 distinct documents. Missing history is reported honestly.

This target concerns discovery, not20 playable streams or automatic additions.
The three-candidate media triage budget and all production QA remain unchanged.
Additional research catalogs are not automatically added to production sources.

## Discovery follow-through

The summary also reports retained candidates still awaiting a probe and leads that
passed both HLS and decoder triage. These counts include saved leads even when a
playlist disappears. Decoder-passing leads remain unapproved: full burn-in,
programme identity, stability and guarded staging are still required. Source
errors include HTTP status codes without publishing exception text or headers.

The obsolete date-specific epg-pw mirror was removed after its daily filename
expired; the same project's maintained `output/all_merged.m3u` stays configured.
# Automatic provider discovery

The post-build scrub now also searches public GitHub repositories for additional
playlist catalogs (`--discover-providers`). It rotates six search queries and five
result pages, inspects up to six unfamiliar repositories per run, and retains up
to two M3U documents from each. Archived/private repositories, forks, configured
repositories, oversized files and non-playlist code are excluded. Repository
contents are parsed as data; no third-party programs are downloaded or executed.

The trusted production scrub artifact retains discovered catalogs, inspected
repository revisions and the search cursor. Upstream changes or seven days allow
reinspection. Up to twelve retained catalogs rotate into the front of each scrub,
before the configured sources, so target-based early stopping cannot always
exclude the new catalogs. A failed search preserves retained catalogs, reports the
failure, and still scans known lists. Missing prior artifacts are reported using
the existing initial-inventory behavior, not claimed as fresh stream discoveries.

Provider searching gets at most 120 seconds of the existing shared 600-second
search/playlist budget; the scrub job retains its 20-minute timeout. Requests have
bounded response sizes and timeouts. API rate/access failures stop discovery
without blocking deployment. The two-hour schedule, 86-channel guard, protected
channel identities and all playback/release gates are unchanged.

The summary distinguishes repositories inspected, new **candidate playlist
documents**, new distinct stream URLs, and new media hostnames. A repository or
M3U file can contain mirrors, empty lists, foreign channels or player manifests;
finding one is not proof of a new provider family or independent origin. Exact-ID,
credential, quarantine and kill-switch filters still apply before media triage.
Up to three eligible unseen candidates get the existing segment/decoder probes.
Discovery never edits production configuration or approves a source. Burn-in,
sustained playback, exact programming review and guarded staging remain required.


### Discovery eligibility and HGTV priority (2026-10-19)

Public discovery now includes WPSG and NBC Sports Philadelphia Plus. Finding a
candidate does not establish full-linear programming or playback. Private/OTA
connectors remain available, but these channels no longer skip public searches.

Research accepts public signed/session query URLs unchanged and does not reject
DASH solely because its extension is `.mpd`. The scrub inspects DASH manifests:
ContentProtection holds the candidate without decoding; clear DASH gets the normal
bounded research decoder attempts. A pass remains advisory and cannot publish a
stream or bypass production segment, burn-in, Primary, identity or access checks.
Static signed links must still satisfy expiry checks. Account query credentials,
email/userinfo paths, recognizable Xtream account paths, device MAC/serial links,
quarantine and exact kill switches remain excluded. `/live/`, `/play/` and
`/api/stream/` prefixes alone no longer establish embedded credentials.

Deployment and release readiness retain the 86-channel floor and now require
HGTV. Disney Channel, History and National Geographic remain curated channels,
but no longer individually block deployment. Playback QA and the two-hour cron
are unchanged.
