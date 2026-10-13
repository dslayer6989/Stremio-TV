# Channel logo verification — 2026-10-13

## Scope
PR #95 is **logo metadata only**. It must not modify stream selection, playback, EPG, channel ordering, or source recovery.

## Inventory
- 116 distinct configured curated channel IDs (includes configured channels that may not be published in the current build).
- 110 IDs have explicit `channel_metadata.logo` overrides on this branch.
- All TV-logo collection paths in those overrides exist in the upstream Git tree.
- GitHub PR unit test check passed for commit `21ea16fdc3164bd01d9b4daf20ea56e3d5266a21`.
- A semantic comparison of `config.json` against `main`, stripping the `logo` property, showed no non-logo changes.

## Remaining without an explicit override
- `WHYY.us`: exact local public-media station branding required.
- `WPHL.us`: current PHL17/PHL CW station identity needs visual confirmation.
- `MSNBC.us`: avoid assigning the newer MS NOW brand blindly when both IDs exist.
- `NBCSportsPhiladelphia.us`: current Philadelphia-specific logo needed.
- `NBCSportsPhiladelphiaPlus.us`: separate Plus-specific logo needed; do not substitute main network logo.
- `HallmarkMoviesMore.us`: distinct Movies & More artwork, not Hallmark Movies Now unless proven identical.

These six **may have usable upstream playlist logos**; lack of an override is not proof of a generated fallback.

## Merge gate (not yet satisfied)
1. Run the actual build on the PR branch and inspect its generated per-channel logo report, including `status=normalized` vs `fallback` for all actually published channels.
2. Verify images render correctly, represent the exact channel/feed, and use current branding; specifically check the six unresolved IDs and any build fallback.
3. Require zero generic fallback icons across the published catalog, passing PR CI, and a metadata-only diff before merge.
4. After merge, confirm the GitHub Pages deploy succeeds and compare published logo-report counts and Stremio metadata.

**Decision:** Hold PR #95 as draft until this evidence is present. A passing unit test alone does not prove zero fallback icons or correct branding.
