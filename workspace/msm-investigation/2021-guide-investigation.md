# Historical MSM 2021 Windows archives and 2019 Official Guide DLC: verified results
Investigation completed: November 3, 2026 (America/New_York).
Source artifacts and reproducible code are alongside this report in the GitHub workspace.

## A. Both 2021 Windows archives were retrieved successfully

The independently hosted public archive at https://debugging.games/Windows exposes two My Singing Monsters 11 MB compressed `.7z` files. Both were actually downloaded to a temporary, non-persisted GitHub Actions runner and inspected with `7z l -slt`; no executable was run.

### April 21, 2021 — manifest 4651787433336000098
- Downloaded: **11,135,464 bytes**, SHA-256 `ec0f5c7c5bdf79eacacb9dd37f72b771ce83c17f4c69bd3395eb3fc5ca1af162`
- Contains `MySingingMonsters.exe` (5,780,480 bytes), `MySingingMonsters.iobj` (72,721,676), `MySingingMonsters.ipdb` (13,301,936), `MySingingMonsters.exp` (2,833), `MySingingMonsters.lib` (5,658), and `MySingingMonsters.exe.metagen` (8,527).

### May 18, 2021 — manifest 2046132612292651817
- Downloaded: **11,127,240 bytes**, SHA-256 `f698d0a8f02b1b1751505a8210c85a14e50ff4b2308cba3c4bf19e06e0ad6ef2`
- Contains `MySingingMonsters.exe` (5,782,016), `MySingingMonsters.iobj` (72,729,955), `MySingingMonsters.ipdb` (13,303,504), `MySingingMonsters.exp` (2,833), and `MySingingMonsters.lib` (5,658).
- No `.exe.metagen` entry.

**Caution:** These are compiled executable and incremental linker/debug artifacts, not complete content archives. Internal archived file timestamps are in December **2022** despite the archives' Steam-manifest labels specifying 2021. Their exact chronological provenance is unconfirmed. No 2021 private staging/development build was accessed.

## B. 2019 Official Guide bundles downloaded and actually inspected
Original public archive metadata: https://archive.org/metadata/msm_official_guide_dlcs
Preserved item: https://archive.org/details/msm_official_guide_dlcs

A GitHub Actions runner successfully downloaded and SHA-1-verified selected small original Unity bundles from version-labelled directories **1280**, **1383**, and **1428**. UnityPy parsed `data.unity3d`, `master.unity3d`, and the available `localization.unity3d`, `static_data.unity3d`, and `Server` bundles. Original asset binaries were not committed or redistributed; extracted object metadata was saved as `deep_archive_results.json` and `guide_catalog_diff.json`.

- Version 1280 `AllData`: 170 MSM1 monster records; 61 DoF monster records; 17 MSM1 islands.
- Version 1383 `AllData`: 256 MSM1 monster records; 68 DoF monster records; 20 MSM1 islands.
- Version 1428 `AllData`: 259 MSM1 monster records; 68 DoF monster records; 20 MSM1 islands.
- 1383 -> 1428 added exactly three MSM1 monster records:
  - `MONSTERRARE_BN` (entity 868), consistent with **Rare Flowah** (released Oct 4, 2019).
  - `MONSTER_BC_EPIC` (entity 610), **Epic Shrubb** (Oct 9, 2019).
  - `MONSTER_ACDE_EPIC` (entity 628), **Epic Riff** (Oct 23, 2019).
- 1383 -> 1428 also removed six records for old generic `OBSTACLE_ROCK_*` and `OBSTACLE_TREE_*` structures from the guide's `AllData` listing.
- A noteworthy inconsistency: `dlc/1428 (...)/android/master.unity3d` `GlobalLookupData.version` is **1427**, while its directory is numbered **1428**. The other two versions' embedded version numbers match their directory labels. Do not assume this identifies an additional retrievable `1427` release.
- `Server` is not a plaintext host-configuration document: it is a UnityFS asset bundle containing an `AssetBundleManifest`.

The three new monster records were **already released in the main game by October 23, 2019**. This evidence supports the Guide's update lag, not new cancelled monsters. Historical timeline: https://mysingingmonsters.fandom.com/wiki/History/2019

## C. How might the archived 1428 version have been discovered?

**A concrete older asset-server address was found.** A GameBanana tutorial documenting Official Guide rig extraction publishes the exact URL:
`http://dlc.bbbgame.net/companion_app/dlc/1044/android/msm1.unity3d`
Source: https://gamebanana.com/tuts/15603

This establishes that at least one numbered Official Guide DLC asset URL was publicly documented, with path structure:
`/companion_app/dlc/<numeric-version>/<android-or-ios>/<bundle-name>`

A second narrow test used the **HTTPS** version of this documented host, requesting at most a 128-byte range:
1. `1044/android/msm1.unity3d`: **HTTP 206 Partial Content**, `Content-Range: bytes 0-127/51934616`, begins with `UnityFS`. So this original static file path is **still publicly accessible today** (at least for a 128-byte test).
2. `1428/android/Server`: **HTTP 403 Forbidden**. No further requests to that version were attempted; the hypothetical 1427 file was not tested.

Test run: https://github.com/Minuteandone/Village-chat-tool/actions/runs/41748666124

**Provenance limits:** Deambird23 linked the Internet Archive collection and identified version 1428 as unreleased in a February 2026 Spriters Resource comment (https://www.spriters-resource.com/mobile/mysingingmonstersdawnoffire/asset/524667/). There is no public account in the checked sources of **how** they discovered 1428, when they downloaded it, or whether a different server/mirror was involved. Public numbering makes educated discovery plausible, but guessing is not proof.

## D. What has and has not been recovered

**Recovered:** two public 2021 Windows .7z packages to temporary runner storage and their exact contents/hashes; small old Guide Unity asset bundles from archived versions 1280, 1383 and 1428; actual serialized monster metadata and change lists; a working historical official CDN URL for version 1044.

**Not recovered:** complete 2021 game content archives, private Steam branch builds, the currently forbidden 1428 original CDN file, or any new scrapped monster confirmed by these records.

Detailed reproducible reports:
- `deep_archive_results.json` and `deep_archive_results.md`
- `guide_catalog_diff.json` and `guide_catalog_diff.md`
- `deep_archive_probe.py` and `guide_catalog_diff.py`
- Actions workflows `.github/workflows/msm-deep-inspect.yml`, `.github/workflows/msm-catalog-diff.yml`, `.github/workflows/msm-legacy-cdn-check.yml`

The original game binaries were not copied into the public report or ZIP.
