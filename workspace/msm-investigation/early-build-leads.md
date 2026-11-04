# Targeted MSM early-build discovery (public metadata only)

Research date: 2026-11-03 (America/New_York)

This is an **evidence-led guessing experiment**, not a scan of private servers. The target list below consists of exact build identifiers that are **already indexed publicly**. There is no bruteforcing, guessed credential use, or access-control circumvention.

## Exact leads worth further archival comparison

| Game | Date (UTC) | Build ID | SteamDB label | Evidence |
|---|---|---:|---|---|
| My Singing Monsters (PC) | 2021-06-03 | 6806184 | Staging; not observed on public branch | https://steamdb.info/patchnotes/6806184/ |
| My Singing Monsters (PC) | 2021-06-16 | 6880526 | Staging; not observed on public branch | https://steamdb.info/patchnotes/6880526/ |
| My Singing Monsters (PC) | 2024-06-03 | 14585054 | Development; not observed on public branch | https://steamdb.info/patchnotes/14585054/ |
| My Singing Monsters (PC) | 2024-06-06 | 14625798 | Development; not observed on public branch | https://steamdb.info/patchnotes/14625798/ |
| My Singing Monsters (PC) | 2024-10-14 | 16030952 | Development; not observed on public branch | https://steamdb.info/patchnotes/16030952/ |
| My Singing Monsters (PC) | 2024-10-15 | 16045795 | Development; not observed on public branch | https://steamdb.info/patchnotes/16045795/ |
| My Singing Monsters (PC) | 2024-10-16 | 16059775 | Development; not observed on public branch | https://steamdb.info/patchnotes/16059775/ |
| My Singing Monsters (PC) | 2025-01-02 | 16891951 | Development; not observed on public branch | https://steamdb.info/patchnotes/16891951/ |
| My Singing Monsters Playground | 2021-09-14 (manifest creation) | 7602409 (associated Steam build) | Preview depot 1722769; SteamDB saw the manifest on 2021-11-04 | https://steamdb.info/depot/1722769/ |

## Notable differences and interpretation

- The main game's PC Steam release was 2021-03-24, so 2021 staging records are *post-launch staging builds*, not evidence of a 2012 pre-release prototype.
- SteamDB's sentence **"This build has not been seen in a public branch"** is an observation about its tracking and must not be interpreted as "scrapped gameplay" or "never released any of these assets." Some listed updates were officially announced.
- `My Singing Monsters Playground Preview` is a different game from the original `My Singing Monsters`, and its preview depot is **not** proof of a cut monster in the main game.
- That preview depot contains a catalog of 1,556 entries. SteamDB says its filenames are encrypted, making direct comparison to today's files impossible from SteamDB's displayed metadata alone.
- The original game's depot (1419171) has a public set of historical manifests listed here: https://steamdb.info/depot/1419171/ . Historical public manifests are a stronger starting point than requesting guessed private CDN paths.
- A 2026 SteamDB app page explicitly indicated `privatebranches: 1`; that is not sufficient to determine the private branch name, contents, purpose, or access rights.

## Future hypotheses, prioritized

1. **Strong evidence, no guesses needed:** compare *publicly released* historical depot manifests (e.g. 2025 vs 2026) for assets that disappear or retain obsolete names. Validate whether removal is just ordinary housekeeping.
2. **Promising, metadata-only:** look for public patch metadata about staging/development builds, especially those preceding public releases. These records can tell us *when* to investigate, not what their files contain.
3. **Separate spinoff investigation:** compare the archived Playground Preview depot metadata to ordinary released Playground assets. But encrypted preview filename entries prevent trustworthy detailed inference from the currently available index.
4. **Low-priority conjecture:** use expected filename schemes to infer candidates offline, then search publicly indexed archives. No need to generate many direct requests to any Big Blue Bubble server.

## Request discipline

- No enumeration of unpublished CDN paths.
- No repeated requests to hosts returning HTTP 401/403.
- No use of guessed credentials, tokens, Steam beta passwords, or private repository access.
- Stop treating an entry as a candidate once it proves to be ordinary released content.
