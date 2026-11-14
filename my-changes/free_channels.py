"""Add extra free channels to the allow-list so the lineup is as big as possible.

Called by localize.py on every sync. The builder only publishes channels whose
exact ID is on the allow-list in config.json, so this script finds more IDs worth
adding and writes them in. Every added channel still goes through all of the
builder's normal checks (stream probing, decoder QA, identity, logos).

A channel is added only when ALL of these are true:
  * its ID comes from the IPTV-org or Free-TV playlists and isn't already allowed,
  * the playlist doesn't flag it as geo-blocked or not 24/7,
  * the program guide has an EXACT match (same name, or same station call sign),
    so a channel never shows another channel's schedule.

If anything can't be downloaded the script changes nothing and the sync carries on.
"""
import gzip
import re
import urllib.request
import xml.etree.ElementTree as ET

MAX_ADDED = 300
CATEGORY_MORE = "More Channels"
CATEGORY_LOCALS = "Other Local Stations"
NEW_CATALOGS = [
    {"id": "more", "name": "More Free Channels", "category": CATEGORY_MORE},
    {"id": "otherlocals", "name": "Other Local Stations", "category": CATEGORY_LOCALS},
]
PLAYLIST_FAMILIES = {"iptv-org", "free-tv"}
SKIP_FLAGS = ("geo-blocked", "not 24/7")
VARIANT_SUFFIXES = {"sd", "hd", "uhd", "fhd", "east", "west", "eastern", "western"}
FILLER_WORDS = ("network", "channel", "tv", "television")


def fetch(url: str, timeout: int = 120) -> urllib.request.addinfourl:
    request = urllib.request.Request(url, headers={"User-Agent": "stremio-tv-localize/1.0"})
    return urllib.request.urlopen(request, timeout=timeout)


def canonical_key(tvg_id: str) -> str:
    """Same idea as the builder: Foo.us@SD and Foo.us are one channel."""
    tvg_id = (tvg_id or "").strip()
    if "@" in tvg_id:
        base, suffix = tvg_id.rsplit("@", 1)
        if re.sub(r"[^a-z0-9]+", "", suffix.lower()) in VARIANT_SUFFIXES:
            return base.lower()
    return tvg_id.lower()


def alnum(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def parse_playlist(text: str) -> list[tuple[str, str]]:
    """Return (tvg_id, clean name) for entries that carry an ID and aren't flagged."""
    rows = []
    for line in text.splitlines():
        if not line.startswith("#EXTINF"):
            continue
        match = re.search(r'tvg-id="([^"]+)"', line)
        # US channels only: a name like "Discovery Channel" must not pull in the
        # Italian or UK feed and hand it the US guide.
        if not match or not re.search(r"\.us(?:@|$)", match.group(1)):
            continue
        raw_name = line.rsplit(",", 1)[-1].strip()
        if any(flag in raw_name.lower() for flag in SKIP_FLAGS) or "Ⓖ" in raw_name:  # Ⓖ = geo-blocked
            continue
        name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", raw_name)
        name = re.sub(r"[Ⓐ-ⓩ]", "", name).strip()
        rows.append((match.group(1).strip(), name))
    return rows


def guide_ids(url: str) -> set[str]:
    """Channel IDs in the XMLTV guide. They come before the programmes, so stop early."""
    ids = set()
    with fetch(url, timeout=180) as response, gzip.GzipFile(fileobj=response) as stream:
        for _event, element in ET.iterparse(stream):
            if element.tag == "channel":
                ids.add(element.get("id"))
            elif element.tag == "programme":
                break
            element.clear()
    return ids


def callsign(value: str) -> str:
    value = re.sub(r"(?:TV|DT\d*|LD|CD|LP|HD)$", "", value.upper())
    return value


def build_guide_index(ids: set[str]) -> dict:
    index: dict = {"_cable": {}}
    for guide_id in ids:
        if guide_id.endswith(".us_locals1"):
            station = callsign(guide_id.split("-", 1)[0])
            index[station] = guide_id
            continue
        stem = re.sub(r"\.us2?$", "", guide_id)
        tokens = [t for t in stem.split(".") if alnum(t) not in VARIANT_SUFFIXES]
        base = alnum("".join(tokens))
        forms = {base}
        for word in FILLER_WORDS:
            if base.endswith(word) and len(base) > len(word) + 2:
                forms.add(base[: -len(word)])
            forms.add(base + word)
        for form in forms:
            index["_cable"].setdefault(form, []).append(guide_id)
    return index


def pick(index: dict, tvg_id: str, name: str) -> tuple[str, bool] | None:
    local = re.match(r"^[A-Za-z]+\.us@([A-Za-z0-9]+)$", tvg_id)
    if local and alnum(local.group(1)) not in VARIANT_SUFFIXES:
        guide_id = index.get(callsign(local.group(1)))
        return (guide_id, True) if guide_id else None
    wanted = alnum(name)
    candidates = index["_cable"].get(wanted, []) if wanted else []
    if len(set(candidates)) == 1:  # ambiguous names are skipped, never guessed
        return candidates[0], False
    return None


def add_free_channels(config: dict, aliases: dict) -> int:
    try:
        sources = (config.get("sources") or {}).get("playlists", [])
        index = build_guide_index(guide_ids(config["sources"]["epg"]))
        pool: dict[str, tuple[str, str]] = {}
        for source in sources:
            if source.get("family") not in PLAYLIST_FAMILIES:
                continue
            try:
                with fetch(source["url"]) as response:
                    text = response.read().decode("utf-8", errors="ignore")
            except Exception as error:  # one bad playlist must not stop the rest
                print(f"free channels: skipped {source.get('name')}: {error}")
                continue
            for tvg_id, name in parse_playlist(text):
                pool.setdefault(canonical_key(tvg_id), (tvg_id, name))
    except Exception as error:
        print(f"free channels: nothing added this time ({error})")
        return 0

    curation = config["curation"]
    allowed = {canonical_key(p) for key in ("philly_allow", "national_allow")
               for p in curation.get(key, []) if "." in p}
    allowed |= {canonical_key(p) for p in (curation.get("canonical_id_aliases") or {})}
    metadata = config.setdefault("channel_metadata", {})
    by_tvg = aliases.setdefault("by_tvg_id", {})

    # The same channel can appear under a second ID (TheWeatherChannel.us@SD vs
    # WeatherChannel.us). Skip anything whose name matches a channel already allowed.
    def name_key(text: str) -> str:
        text = alnum(text)
        return text[3:] if text.startswith("the") and len(text) > 6 else text

    def is_station_id(tvg_id: str) -> bool:  # ABC.us@WATMTV is one station, not "ABC"
        return "@" in tvg_id and canonical_key(tvg_id) == tvg_id.lower()

    have_names = {name_key(re.sub(r"\.us.*$", "", p)) for key in ("philly_allow", "national_allow")
                  for p in curation.get(key, []) if "." in p and not is_station_id(p)}
    have_names |= {name_key(row.get("name", "")) for row in metadata.values()}

    added = []
    for key in sorted(pool):
        if key in allowed:
            continue
        tvg_id, name = pool[key]
        id_name = name_key(re.sub(r"\.us.*$", "", tvg_id))
        if name_key(name) in have_names or (not is_station_id(tvg_id) and id_name in have_names):
            continue
        found = pick(index, tvg_id, name)
        if not found:
            continue
        guide_id, is_local = found
        have_names.add(name_key(name))
        added.append((tvg_id, name, guide_id, is_local))
    # Cable-style channels first, then out-of-market local stations.
    added.sort(key=lambda row: (row[3], row[1].lower()))
    added = added[:MAX_ADDED]

    for tvg_id, name, guide_id, is_local in added:
        curation["national_allow"].append(tvg_id)
        by_tvg[tvg_id] = guide_id
        if tvg_id not in metadata:
            metadata[tvg_id] = {
                "name": name,
                "category": CATEGORY_LOCALS if is_local else CATEGORY_MORE,
                "service_type": "Local broadcast" if is_local else "Free channel",
            }

    existing = {c.get("id") for c in config.get("catalogs", [])}
    for catalog in NEW_CATALOGS:
        if catalog["id"] not in existing:
            config.setdefault("catalogs", []).append(dict(catalog))
    return len(added)
