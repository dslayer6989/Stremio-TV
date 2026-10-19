"""Switch Stremio TV's local channels from Philadelphia to the Altoona, PA area.

Runs automatically from .github/workflows/keep-updated.yml after every update
from the original project. It only changes values in config.json.
"""
import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config.json"

# Johnstown-Altoona-State College stations first, then nearby stations that
# currently have free public streams (they fill the CBS gap).
LOCAL_IDS = [
    "NBC.us@WJACTV",         # NBC 6 WJAC, Johnstown
    "CBS.us@WTAJTV",         # CBS 10 WTAJ, Altoona
    "ABC.us@WATMTV",         # ABC 23 WATM, Altoona
    "Fox.us@WWCPTV",         # FOX 8 WWCP, Johnstown
    "PBS.us@WPSUTV",         # WPSU PBS, State College
    "TheCWPlus.us@WJACTV",   # CW on WJAC
    "MNT.us@WHVLLD",         # MyNetworkTV, State College
    "WJAC.us", "WTAJ.us", "WATM.us", "WWCP.us", "WPSU.us",
    "WHPDT1.us",             # CBS 21 WHP, Harrisburg (nearby)
    "CBSNewsPittsburgh.us",  # CBS News Pittsburgh 24/7 (nearby)
]

LOCAL_FAVORITES = ["WJAC", "NBC 6", "WTAJ", "CBS 10", "WATM", "ABC 23",
                   "WWCP", "FOX 8", "WPSU", "CBS 21"]
PHILLY_FAVORITES = {"WPVI", "6ABC", "NBC 10", "KYW", "CBS 3", "WTXF",
                    "FOX 29", "WPHL", "WHYY", "NBC Sports Philadelphia"}

NAMES = {
    "NBC.us@WJACTV": "NBC 6 / WJAC",
    "CBS.us@WTAJTV": "CBS 10 / WTAJ",
    "ABC.us@WATMTV": "ABC 23 / WATM",
    "Fox.us@WWCPTV": "FOX 8 / WWCP",
    "PBS.us@WPSUTV": "WPSU PBS",
    "WHPDT1.us": "CBS 21 / WHP (Harrisburg)",
    "CBSNewsPittsburgh.us": "CBS News Pittsburgh",
}


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))

    config["curation"]["philly_allow"] = list(LOCAL_IDS)

    hunt = (config.get("discovery") or {}).get("philly_local_sources")
    if isinstance(hunt, dict):
        hunt["target_ids"] = list(LOCAL_IDS)
        if "priority_target_ids" in hunt:
            hunt["priority_target_ids"] = list(LOCAL_IDS)
        if "secondary_target_ids" in hunt:
            hunt["secondary_target_ids"] = []
        hunt["official_pages"] = []  # these are Philadelphia station websites

    for catalog in config.get("catalogs", []):
        if catalog.get("id") == "philly":
            catalog["name"] = "Altoona Locals"  # keep "category" as-is; the build relies on it

    for source in (config.get("sources") or {}).get("playlists", []):
        if "cities/usphl.m3u" in source.get("url", ""):
            source["name"] = "IPTV-org Johnstown"
            source["url"] = "https://iptv-org.github.io/iptv/cities/usjst.m3u"

    favorites = [f for f in config.get("favorites", []) if f not in PHILLY_FAVORITES]
    config["favorites"] = LOCAL_FAVORITES + [f for f in favorites if f not in LOCAL_FAVORITES]

    metadata = config.setdefault("channel_metadata", {})
    for channel_id, name in NAMES.items():
        metadata[channel_id] = {"name": name, "category": "Other", "service_type": "Local broadcast"}

    config["addon"]["description"] = (
        "Live TV with a program guide: national channels plus Altoona, PA area locals."
    )

    CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Localized for Altoona: {len(LOCAL_IDS)} local channel IDs")


if __name__ == "__main__":
    main()
