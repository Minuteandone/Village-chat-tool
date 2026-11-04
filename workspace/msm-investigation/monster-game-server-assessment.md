# Is the Internet Archive "My Singing Monsters Game Server" authentic?

**Investigated November 3, 2026 (U.S. Eastern)**

Archive: https://archive.org/details/monster-game-server
Metadata: https://archive.org/metadata/monster-game-server
SHA-1 of original publicly archived ZIP: `df086c9ca4581733f73f2e8aaea1408382232e4d`
Size: **15,170,251 bytes**. The ZIP was downloaded into an ephemeral GitHub Actions runner, hash-verified, and inspected **without executing anything**. Neither the ZIP nor its code was republished by this investigation.

## Verdict

**Strong evidence of a historically derived My Singing Monsters backend source tree, not an ordinary fan remake. However, its authenticity and ownership are not independently confirmed.** The uploader's "Creator: Big Blue Bubble" form field is self-reported, not a verified developer account. No original studio endorsement or independent original Git provenance has been established.

The only verified assertion is that the 2023 Archive.org file contains the detailed software tree below. It may be a genuine historical source snapshot, an unauthorized repackaging of source code, a heavily modified copy, or less likely a sophisticated reconstruction. Without verifiable provenance, do not call it an officially released studio source archive.

## Archive provenance

- Internet Archive publication: **October 7, 2023**.
- The upload's description is simply `lmao`.
- The source ZIP top-level folder is `monster-game-server-266e600f69ed8e462f26416704266d042dd2cf84`. The 40-character suffix resembles a Git commit SHA or archive identifier but does **not prove** which repository it came from.
- ZIP entry dates are concentrated in **2020 and 2021**, not 2012, so names of earlier SQL files cannot alone date the whole source tree.
- Big Blue Bubble's official history dates the original game's public release to **September 4, 2012**: https://www.bigbluebubble.com/home/about/history/

## Verified contents

**215 ZIP directory and file entries = 188 actual files and 27 directory entries**.
- 155 Java source files
- 21 compiled JAR files
- 5 `.jardesc` files
- 2 XML files
- 2 Java properties files
- 2 SQL scripts
- 1 text file

Notable *filenames* and architecture (not copied source):
- `src/com/bigbluebubble/mysingingmonsters/MSMExtension.java`
- `src/com/bigbluebubble/mysingingmonsters/GameStateHandler.java`
- `src/com/bigbluebubble/mysingingmonsters/MSMServerEventHandler.java`
- `external/src/com/bigbluebubble/BBBServer/BBBServerExtension.java`
- `src/com/bigbluebubble/mysingingmonsters/data/BreedingLookup.java`
- `src/com/bigbluebubble/mysingingmonsters/data/MonsterIslandData.java`
- `src/com/bigbluebubble/mysingingmonsters/data/MonsterRareData.java`
- `src/com/bigbluebubble/mysingingmonsters/task/MSMAdminCatchUnreleasedAccount.java`
- `src/com/bigbluebubble/mysingingmonsters/data/groups/Advertisement2018Group.java`
- `my_singing_monsters_clean_20120810.sql`
- `tribal_date_updated.sql`
- `MSMExtension.jar` and `BBBServerExtensionLib.jar`

The third-party Java dependencies include **SmartFoxServer 2X**, MySQL Connector/J, AWS Java SDK, and Memcached libraries. This is a plausible historical server-side production stack with player state, islands, breeding, scheduled events, database support, game services, and administration code.

## Why it's unlikely to be a simple fan remake

1. It contains a substantial, coherent Java source tree with separate reusable BBBServer, game-specific extensions, model/data and player-state classes, plus supporting JARs and build files.
2. The game-specific models and event handlers are consistent with the mechanics of MSM over multiple historical eras. The archive isn't merely an API stub or a single web service.
3. It contains a 2012-dated SQL filename alongside later-era features including tribal-event database updates and an `Advertisement2018Group` class, suggesting maintenance over time rather than a single nostalgia mockup.
4. A functioning original game server would generally need external services and operational configuration not established by this archive alone. This is best described as a **source-code archive**, not a captured running server.

## Important limitations

- Self-reported uploader metadata is not proof that Big Blue Bubble uploaded or authorized sharing the files.
- No original GitHub repository or commit mapping has been confirmed for the folder's hash.
- A filename like `my_singing_monsters_clean_20120810.sql` does not prove that the actual archived SQL bytes were authored that day.
- The archive's 2020/2021 timestamps are compatible with repackaging or later development; they should not be used to assign a precise source branch.
- The game-code files may contain authentication or infrastructure functionality. Nothing was executed or connected to a real account/server. Raw code was not reproduced in the public inspection report.
- A class name containing `Unreleased` is **not proof of a cancelled monster or other scrapped gameplay**.

## Potential research value

The most promising *research questions* are whether the SQL schema and data records reveal early entity/island concepts, what feature flags and event categories are represented in old source models, and whether these differ from later public game behavior. Those require provenance-aware static analysis and should avoid exposing access credentials or contacting operational servers.

## Reproducibility and report boundaries

- Public, hash-verified archive inspection script: `inspect_monster_game_server.py`
- Metadata-only JSON inventory: `monster-game-server-inspection.json`
- Human-readable path-only inventory: `monster-game-server-inspection.md`
- One-shot workflow: `.github/workflows/msm-server-archive-inspect.yml`

This report preserves file metadata and research conclusions but does not redistribute source or binary code.
