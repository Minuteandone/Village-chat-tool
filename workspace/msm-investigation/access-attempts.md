# Direct build access checks — 2026-11-03 (US Eastern)

## Result: Playground Preview depot was NOT anonymously downloadable

- Game: My Singing Monsters Playground (Steam AppID `1722760`).
- Target depot: `1722769`, named **My Singing Monsters Playground Preview**.
- Target manifest: `3349315166870153103`, dated 2021-09-14 in SteamDB.
- Source for IDs: https://steamdb.info/depot/1722769/
- Public test: official SteamCMD installed on a clean GitHub Actions Ubuntu runner; `+login anonymous`; one `+download_depot 1722760 1722769 3349315166870153103` request with 80-second timeout.
- Exact outcome: SteamCMD connected anonymously and reported **`Depot download failed : missing license for depot (No subscription)`**. SteamCMD process exited with code `14`.
- Run evidence: https://github.com/Minuteandone/Village-chat-tool/actions/runs/41745545835
- GitHub owner-issue reply in issue #3: https://github.com/Minuteandone/Village-chat-tool/issues/3
- Security: no Steam credentials, beta passwords, private branches or bypasses used; no game files uploaded, committed, or shared.

The command reached Steam's authenticated/anonymous client protocol rather than merely fetching SteamDB. Denial means **this anonymous account has no depot license**; it does NOT establish that every authorized Steam account lacks one, or that the files have been deleted.

## Additional checks

1. `/work web get https://steamdb.info/depot/1722769/manifests/`: workspace runner returned **HTTP 403**. The ordinary public web view is readable and shows the file count and metadata, but names are encrypted.
2. Smaller Internet Archive search for an exact `My Singing Monsters Playground` title: **0 items** returned in that query. A narrow search result is NOT proof that no independently archived copy exists anywhere.
3. Exact string `3349315166870153103` in public GitHub indexed code: **0 matches** returned from this search.
4. Known 2021 staging and 2024 development **build IDs** in SteamDB reveal metadata but not a corresponding accessible **manifest ID** for each private build. These were **not tested as binary depot downloads**; build ID and manifest ID are different identifiers.

## Next constructive approach

Compare existing publicly available main-game Steam depot manifests from released versions, inspect developer test remnants in public archives, and contact legitimate archivists or build owners if they choose to share allowed historical material. Do not automate guesses against restricted depots or probe credentials.
