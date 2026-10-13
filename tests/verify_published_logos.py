"""Fail the logo gate if the actual generated published catalog uses placeholder logos."""
import json
from pathlib import Path

root = Path("site")
report_path = root / "diagnostics" / "logo-normalization.json"
channels_path = root / "diagnostics" / "channels.json"
if not report_path.is_file():
    raise SystemExit(f"Missing actual build logo report: {report_path}")
report = json.loads(report_path.read_text(encoding="utf-8"))
rows = report.get("channels", [])
if not report.get("enabled") or not rows:
    raise SystemExit("Logo normalization report missing, empty or disabled")
summary = report.get("summary", {})
fallbacks = [r for r in rows if r.get("status") != "normalized"]
print(f"Published logo report: {summary}; non-normalized rows: {len(fallbacks)}")
for row in fallbacks:
    print(f"  {row.get('tvg_id')} | {row.get('name')} | {row.get('status')} | {row.get('error')}")
if fallbacks:
    raise SystemExit(f"BLOCK MERGE: {len(fallbacks)} published channels lack normalized logos")
if not channels_path.is_file():
    raise SystemExit("Missing published channel diagnostics; cannot verify catalog alignment")
published = json.loads(channels_path.read_text(encoding="utf-8"))
if isinstance(published, list) and len(published) != len(rows):
    raise SystemExit(f"Published channel/report mismatch: {len(published)} vs {len(rows)}")
print("PASS: zero generic fallback logos in the generated channel catalog")
