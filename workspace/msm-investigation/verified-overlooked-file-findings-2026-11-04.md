# MSM lost-file investigation — verified new findings (2026-11-04)

## What was actually achieved

The previous server ZIP was found by the human user, not by the assistant. This new round searched for **actual original game assets/archives**, not origin attribution of the earlier ZIP. New/overlooked to **our investigation** is not the same as previously unknown to all fans.

**Best newly verified discovery:** A publicly preserved 2014 PlayStation Vita copy of My Singing Monsters includes its own complete SQLite game-data database `msm.db`; within it, monster record **#30 / entity #93** is still a five-bed **unimplemented five-Natural-element placeholder**, with names **`NEW ABCDE 1`, `NEW ABCDE 2`**, *empty genes field*, **15 breeding-result rows**, **zero breeding-parent rows** and **zero island-monster placements**. The separately preserved 2012 SQL dump had the same #30 and entity #93, with genes `ABCDE`, 15 positive breeding-result rows and no island placement. The 2014 port therefore preserves a later data-state for the same placeholder; there is no evidence that the missing Natural Quint had artwork, audio or animations, and code/game records could have been carried forward from a shared database rather than independently invented. This is unusually convincing **unfinished content scaffolding**, not proof of a completed monster.

**Real platform image evidence:** `https://archive.org/details/msm-ps-vita-game-files` has a 71,805,852 byte ZIP, SHA-1 `4d4bdbb3c4d90aad6743dda8e55dd2ed95605ff8`, which we downloaded temporarily, validated, and inspected read-only.
- 1,566 files, including 298 PS Vita `.vag` music clips, 251 PNG, 93 PVR, 8 `worldXX.mid`, 29 WAV and 5 MP3.
- `sce_sys/param.sfo` says `TITLE_ID=PCSE00459`, `CONTENT_ID=UP2128-PCSE00459_00-MYSINGINGMONSTER`, `APP_VER=01.00`, `VERSION=01.02`, and development tool metadata `c_date=20140626,sdk_ver=03150000`. This tool's date is **June 26, 2014** (not the date of any specific monster design), preceding the documented August 12 2014 PS Vita release.
- `msm.db` is a genuine 299,008 byte SQLite 3 database containing 22 first-party gameplay tables (no player/account tables). It has **71 monster records**, 8 island definitions, 161 island-monster assignments, **1,200** breeding-combination rows, 296 entity records, 224 quests and 201 structures.
- Its eight islands include the original five Natural islands plus Gold, Ethereal and Shugabush; the Gold Island gene list `ABCDE` is a set of island elements, **not evidence of a Gold Island quint**.

## Regional Monster Choir builds — actual packages recovered and compared

`https://archive.org/details/Msmapks` carries both of these:
- **Chinese Monster Choir** `Monsterchoirchina.uc.apk`: **113,810,411 bytes**, SHA-1 `e5dad967088db4318616f26b642d81080b31931f`. Android package `com.yodo1.MySingingMonsters.uc`, `versionName=1.5.0`, `versionCode=151`. 2,661 archive entries, 876 PNG, 92 PVR, 303 OGG, 713 XML, 505 BIN. This is a preserved build with actual graphic/audio/data assets.
- **Korean Monster Choir** `MONSTERCHOIRSOUTHKORIEA.apk`: **51,720,835 bytes**, SHA-1 `2e41a71fdc59be8d4904316adee168c686367e6e`. Android package `com.yodo1.msm.kr`, `versionName=1.0.9`, `versionCode=13`. 2,565 archive entries, 696 PNG, 300 OGG, 717 XML, 698 BIN. An identically hashed APK is also separately posted at `https://archive.org/details/Monsterchoir_20231012`; it is **one duplicate, not two unique packages**.

Compare of first-party `assets/gfx/monsters`, `assets/audio/music`, `assets/xml_resources` and `assets/xml_bin` pathsets:
- **1,037 shared relative filenames**.
- **312 paths appear only in the Chinese package**; **332 only in the Korean**.
- Unique audio paths include `assets/audio/music/metronome08.mid` (Korean only), and eight `assets/audio/music/beats_*.mp3` files (Chinese only).
- This does **not** prove those audio files were unused or scrapped; they are verified region/version differences. Korean `_kor` monster XML-BIN names and Chinese localized sprites require more semantic comparison before declaring a new species.
- The separate public `https://archive.org/details/monster_choir_korean_sprites` collection supplies 2026-archived Korean CDN PNGs not necessarily in an APK; they were already published and should be used for differences, not claimed newly invented.

## Early Android preservation search

The dated Russian 4PDA thread:
https://4pda.to/forum/index.php?showtopic=389382
- Post #18, May 15, 2013: old **Android 1.1.6** `My Singing Monsters-17.apk`, listed 26.84 MiB.
- Post #83, Apr 24, 2014: old **Android 1.2.7** `com.bigbluebubble.singingmonsters.full-1.2.7.apk`, listed 46.76 MiB.
- Both are still mentioned by the historical thread's version index. However file bytes were **not recovered**, and we did **not** verify these precise APK versions. Do not conflate with the archived **iOS** 1.2.7 IPA.

`https://archive.org/details/com.bigbluebubble.singingmonsters.full` contains many preserved early **Android** APKs including 1.2.0, 1.2.4, 1.2.5, 1.2.9 and 1.3.x, but not the sought 1.1.6/1.2.7. This catalog can support version-to-version comparison.
`https://archive.org/details/1.4.3_202310` preserves numerous historical **iOS** 1.x IPAs, including 1.2.7, which is not a recovery of Android 1.2.7.
`https://archive.org/details/Msmapks` contains several copies of the APKs above as well as a bit-identical copy of the already-investigated `monster-game-server.zip` (SHA-1 `df086c9... `); the duplicate isn't an independent new server source.

## Historical server-data XML time series — 62 snapshots

`https://archive.org/details/msm_dat_files` holds 2,712 original/derived archive entries and game-data files grouped under **62 dated snapshots** from July 22, 2021 to April 8, 2026. Public original-file metadata was scanned only; no direct live server interaction.

- Found **32** distinct XML data basenames.
- Archive-file SHA-1 changes indicate gameplay-data updates between dates (for example, 10 changed snapshots from 2021-07-22 to 2022-07-31).
- Some file categories first appear in available snapshots in 2023 (flip-board data etc.), 2025 (attuner, ethereal islet, titansoul and more), and 2026 (clubbox/card data).
- `attuner_gene_data.xml` and `battle_campaign_data.xml` vanish from the uploader's dated snapshots after May 5, 2025, **reappear on Dec 25, 2025**. This could reflect missing archive selection and must *not* automatically be called cut systems.
- None of 32 names appears only in one snapshot; none is permanently absent from the latest snapshot. Do not claim unambiguously cut XML files.
- This remains a particularly strong source for future **content-level** comparisons, not merely file counts.

## Steam depot history and removed content

Public SteamDB data for content depot 1419171 supports change evidence:
- https://steamdb.info/depot/1419171/manifests/
- https://steamdb.info/patchnotes/24978233/ (Sept 2, 2026 update 5.7.0)
- https://steamdb.info/patchnotes/26216944/ (Oct 28, 2026 update 5.7.4)

On Oct 28 2026 (build 26216944), SteamDB's indexed file changes explicitly show **11 removed paths**, including 5 `data/xml_bin/club01_act05-..._C.bin` files and event/multipack graphics. On Sept 2 2026 (build 24978233), hundreds of changes included removal of older sticker image and costume assets while introducing newer content. These are verifiable previous files that *disappeared from subsequent depot manifests*, but **most plausibly normal event/asset cleanup**, not evidence of a canceled monster. New assets like `world32.mid` are a regular island song sequence, not evidence of scrapped music.
- Indexed SteamDB changes are more detailed than the JavaScript-first interactive page visible in a basic reader. Do not claim every historical patch was exhaustively checked.

## Verification and reproducibility files

- `msm-expanded-public-catalog.json` — large internet archive search for public MSM material.
- `msm-public-candidate-file-details.json` — real archive files and SHA-1 data, 18 prioritized items.
- `msm-candidate-static-verified-contents.json` — checksum-verified contents of Vita/Chinese, initial Korean download issue.
- `msm-choir-apk-content-comparison.json` — checksum and `aapt`-verified Chinese/Korean build identities and changed pathsets.
- `msm-vita-metadata-deep.json` — actual Vita SFO and SQLite table summary.
- `msm-vita-2014-game-db-metadata.json` — game-data rows/columns, monster #30 references and islands.
- `msm-dated-server-data-file-diff.json` — all 62 snapshot names and hash-change evidence.
- Every JSON report has a corresponding Python static research script, and new GitHub Actions workflows used temporary runners to download binaries. No source APK, Vita executable, account data or copyrighted assets were committed or redistributed in reports.

**Key conclusion:** The Vita five-element monster placeholder persistence across 2012 and 2014 *is* a substantive new historical-game-data result, beyond simply finding an archive listing. Regional Monster Choir file-level differences are independently authenticated. We did **not** find authenticated Android 1.1.6 or Android 1.2.7 binaries in this round.
