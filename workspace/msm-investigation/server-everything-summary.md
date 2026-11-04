# My Singing Monsters Game Server — complete 187-file inspection

## Scope and evidence

- Original public archive: https://archive.org/details/monster-game-server
- Original ZIP: 15,170,251 bytes; SHA-1 `df086c9ca4581733f73f2e8aaea1408382232e4d`, verified by static-analysis jobs.
- 188 regular archive files exist; **187 inspected**, excluding `wordsFile.txt` exactly as requested.
- These are **187 files**, not 187 original gameplay components. Third-party libraries and copies of shared project code account for many entries.
- All 155 Java source files were parsed for class declarations, method names, imports, broad topics and development markers.
- All 21 JARs were opened as ZIP archives, with compiled class counts and package trees recorded (never executed).
- All 5 Java export descriptors, 2 XML files, 2 properties files and 2 SQL scripts were inspected at the structural level.
- Every inspected path, size and category is recorded in `server-full-file-index.csv`; method-by-method inventory for every Java file is `server-full-file-audit.md`; class reference graph is `server-class-references.json`.
- This is a comprehensive **file-by-file static audit**, not a formal semantic review of every conditional branch or a dynamic test. Original code bodies, infrastructure addresses, credentials, JAR binaries and personal SQL data were not copied into the reports.

## High-level figures

| Measure | Count |
|---|---:|
| Inspected regular files | 187 |
| Java source files | 155 |
| MSM game-specific Java files | 110 |
| Shared Big Blue Bubble Java files | 29 |
| Bundled third-party JSON Java sources | 16 |
| Java source lines, all 155 files | 51,813 |
| Java source lines, MSM-specific | 41,661 |
| Parsed method identifiers, all Java | ~1,834 |
| Parsed method identifiers, MSM-specific | ~1,544 |
| JAR files inspected | 21 |
| XML and Java export descriptors | 7 |
| Properties files | 2 |
| SQL files | 2 |
| Locations of developer-comment flags | 43 |

Method counts are approximate: a regular-expression parser is not a complete Java compiler. Per-file counts may include duplicate method names or miss constructors.

## Every source subsystem

### 1. MSM server core: 5 classes

- `GameStateHandler.java` — **17,305 lines**, about 241 parsed method identifiers. This is the biggest component. Handles monster acquisition, breeding, hatching, feeding, happiness, sale, storage, boxes, Wubbox/underling operations, bakery, shops, islands, tribes, torches, time-limited rewards, Composer, messaging, quest progression, Scratch Ticket and Memory Game, as well as many staff commands.
- `MSMExtension.java` — **2,867 lines**, 56 parsed methods: initialization, static tables, settings, player state loading/saving, accounts, session messaging, requests, advertising segments.
- `MSMServerEventHandler.java` — **683 lines**, 22 methods: login/session/account startup and connection lifecycle.
- `Helpers.java` — JSON compression/decompression helpers.
- `ShutdownHookThread.java` — shutdown handling.

**This is a backend, not the entire game.** Client artwork, animation timelines and recorded monster audio do not appear as first-party assets in these Java files.

### 2. Player state: 16 classes

- `Player.java` (3,489 lines; ~194 methods), `PlayerIsland.java` (2,007 lines; ~140 methods), and `PlayerMonster.java` (1,317 lines; ~87 methods) encode player economy, level state, islands, placements, currency collection and monster statuses.
- `PlayerIslandFactory.java` includes separate methods for typical islands, Composer Island and **several tutorial scenarios**: `CreateTutorialIsland`, `CreateBasicTutorialIsland`, `CreateBreedingTutorialIsland`, and helpers creating example Noggin/Mammott monsters. These may be used by different onboarding experiments or versions; they are not automatically scrapped.
- `PlayerBreeding`, `PlayerEgg`, `PlayerBaking`, `PlayerStructure`, `PlayerFuzeBuddy`, `PlayerBuyback`, `PlayerAchievement`, `PlayerQuest`, `PlayerActiveIslandStats`, `LitPlayerTorch`, `MonsterMegaData` and `InitialPlayerIslandData` split out specialized state.
- `MonsterMegaData` includes separate permanent/temporary duration functions; `PlayerMonster` references it, so it is not an orphaned class.

### 3. Static gameplay data and lookup models: 40 classes

- `BreedingCombination`, `BreedingLookup`: probability-weighted breeding logic and torch-influenced results.
- `Monster`, `MonsterLookup`, `MonsterCommonToRareMapping`, `MonsterRareData`, `MonsterIslandData`, `MonsterIslandToIslandMapping`: monster classes, rare remapping and island associations.
- `Island`, `IslandLookup`, `IslandTorch`, `TorchLookup`, `Gene`, `GeneLookup`: island and element data.
- `Entity`, `Structure`, `StructureLookup`, `Level`, `LevelLookup`, `VersionData`: gameplay entities, levels, structure definitions and client-version gating.
- `QuestLookup`, `TribalQuestLookup`, `Mail`, `MailLookup`, `Promo`, `PromoLookup`, `Sticker`, `StickerLookup`: progression and communication.
- `StoreCurrencyLookup`, `StoreGroupsLookup`, `StoreItemsLookup`, `StoreReplacementItem`, `StoreReplacements`: store rules including **dynamic item replacement**.
- `MemoryMinigameFunctions`, `ScratchTicketFunctions`: older minigame reward rules.
- `ScientificRevenue`, `SegmentationGroup`, `MsmSession`, `Code`, `CodeLookup`: monetization experiments, segmentation, sessions and codes.

Small data-holder classes `MonsterRareData` and `MonsterIslandData` have no declared methods, **but are used in multiple other Java files**. Thus their shortness is not evidence of scrapping.

### 4. Event system: 28 classes

- Three event scheduler/manager files: `TimedEvent`, `TimedEventList`, `TimedEventListBuilder`.
- Thirteen active-list classes, e.g. `CurrencySalesList`, `EntityAvailList`, `MegafySaleList`, `PermalightTorchSaleList`, `ShortenedFuzingList`, `StarSalesList`.
- Twelve corresponding event-type classes, including availability/sale events, `BreedAvailabilityEvent`, `BreedProbabilityChangeEvent` and `ShortenedFuzing`.

**Best dormant-code lead:** `BreedProbabilityChangeEvent.java` is only 14 lines, declares no methods, and no other Java source file directly refers to the class name. By contrast, `BreedAvailabilityEvent.java` is also 14 lines but referenced by `TimedEventList.java`. It is the *only* MSM game class with zero other-source references in this simple cross-reference scan. Runtime reflection or data-driven construction remains possible.

Do not conflate an abandoned event container with proof of a fully implemented breeding mechanic; this is a candidate for further verification.

### 5. Player groups, tutorial selection and advertising: 9 classes

- `BaseGroup`, `UserGroup`, `TutorialGroup`, `CurrencyGroup`, `NoAdvertisementGroup`, `AdvertisementGroup`, `Advertisement2018Group`, `BrandedAdvertisementGroup`, `ScientificRevenueGroup`.
- These form player segmentation/onboarding and monetization policy.
- `TutorialGroup.java` has a comment marked `DISABLED`; this must be interpreted in the context of a specific code branch rather than as evidence the tutorial system was removed.
- `BrandedAdvertisementGroup` is 16 lines and has no declared methods, but is referenced by `UserGroup`.

### 6. Background jobs, operations and monitoring: 11 classes

- Seven task classes: `AuthTokenUpdateTask`, `MailUpdateTask`, `MSMAdminCatchUnreleasedAccount`, `MSMMonsterLinksReloadTask`, `MSMServerStatusTask`, `MSMStats`, `UpdateActiveTimedEvents`.
- Four game logging classes: `GooglePlayEvents`, `MetricCost`, `MSMCommandLogging`, `MSMCommands`.
- `MSMAdminCatchUnreleasedAccount` contains methods named `addAccountToCSRPermaLockPreventionList`, `resetAccountAccessTime`, `removeFromLockedAccountsList`, `clearUnreleasedAcccount`. This appears linked to **staff/account access operations**. Its filename should not be taken as evidence of unreleased monsters.

### 7. Shared BBB infrastructure: 29 Java files

- Server interfaces and events: `BBBServerExtension`, `ServerEventHandler`.
- Persistence and caching: `DbWrapper`, `CacheWrapper`, `CustomSerializingTranscoder`.
- Messaging: `SnsWrapper`, `SqsWrapper`, `SNSWorker`, `BatchingSNSWorker`.
- Operations: `CloudWatchReporter`, `EC2Metadata`, `MetricsRequest`, `MetricsSessionTask`.
- Security/session management: `BBBToken`, `Encryption`, exception classes; plus byte/JSON/network utilities.

This looks like code reused across more than one BBB title. Its administrative/cloud API routines are not by themselves scrapped MSM gameplay.

### 8. Third-party source files: 16

All 16 are bundled `org/json` Java source, including `JSONObject`, `JSONArray`, `JSONTokener`, `XML`, `Cookie`, and `Test`. These are standard general-purpose code, not original MSM design experiments. Their use does not imply an unreleased browser game.

### 9. Compiled JAR files: 21

Two first-party-named builds:
- `MSMExtension.jar`: **132** `.class` entries.
- `BBBServerExtensionLib.jar`: **55** `.class` entries.

Nineteen bundled dependencies, including AWS Java SDK 1.5.0 (**7,541** compiled class files), SmartFoxServer 2X client/server libraries, MySQL Connector/J, Memcached, Apache Commons, Jackson, Netty, OWASP ESAPI and SLF4J. The ZIP inspection recorded their class/package inventories without running or decompiling them.

Sampled compiled first-party classes have Java class-file major version 50 (Java 6-era target). This says what bytecode compatibility they were compiled for, **not** what year these particular JARs were built.

### 10. Config, build and miscellaneous files: 9 plus two SQL

- `build.xml` is an Apache Ant project with ten targets: `init`, `clean`, `cleanall`, `build`, `build-base`, `build-msm`, `build-msm-test`, `unittest`, `jar`, `build-refprojects`.
- `Local BBBServerExtensionLib.jardesc`, `Local MSMExtension.jardesc`, `Local X86 BBBServerExtensionLib.jardesc`, `Local X86 MSMExtension.jardesc` and `StressTester.jardesc` are Java export configuration files. **There is no corresponding StressTester source project or StressTester.jar in this archive.** Export configuration alone cannot prove the project was finished.
- `external/src/com/bigbluebubble/BBBServer/client/sfs-config.xml` is a SmartFoxServer client connection configuration. Its network address/port values are intentionally not republished.
- `external/lib/ESAPI.properties` and `external/lib/validation.properties` are OWASP/validation library configuration.
- `my_singing_monsters_clean_20120810.sql` and `tribal_date_updated.sql` are separate SQL scripts. The latter is a narrowly scoped tribal change script, not an additional full world/database archive.

## Historical SQL seed: most revealing clues

The 2012-labelled SQL seed contains 30 tables and non-personal game data:
- **31 monster records**, including 5 singles, 10 doubles, 10 triples, 5 quads and one five-element combination.
- The five-element entry has monster ID 30, entity ID 93, name key `MONSTER_ABCDE`, genes `ABCDE`, beds 5.
- **15 positive-probability breed-result records** yield monster 30. Monster 30 does not appear as a breeding parent and has **zero island assignment records**. This is not proof of a completed five-element monster design; the combinations could have been systematically generated.
- There are **five island definitions**; only first two have `enabled=1` in this seed. The third nonetheless has monster mappings; islands 4–5 are referenced by quest/achievement metadata.
- The six quest-type categories are `TUTORIAL`, `COLLECTION`, `BUILD`, `TRAVEL`, `BATTLE`, `DARE`. All `depricated` flags are zero, as the column is spelled in the database. None of the 155 Java files has an exact whole-word `BATTLE` or `DARE` reference in this static scan, although database-driven handling may not name categories directly.
- The seed includes 1,041 breeding rows, 118 quests, 91 structures, 146 entities and 20 level records.
- User-related schema/table definitions exist but player rows and values were excluded from review outputs.

## Developer-marked code and caveats

There are **43** code-comment locations marked with one or more TODO/HACK/FIXME/DISABLED/UNUSED/TESTING/TEMPORARY labels. They occur in `GameStateHandler`, `ScratchTicketFunctions`, `PlayerMonster`, `TutorialGroup`, `PlayerStructure`, shared infrastructure, etc.

These comments are real software engineering leftovers, but mostly within systems known to exist in-game. Do **not** turn 43 comments into 43 claims of cancelled features.

## Most promising discoveries ranked by evidence

1. **2012-labelled `MONSTER_ABCDE` data** with 15 theoretical breeding results but no island placement — historically interesting, not proof of a built Quint.
2. **`BATTLE` and `DARE` quest categories** present in seed but no whole-word Java references — potentially unused database categories.
3. **`BreedProbabilityChangeEvent` short class** with zero explicit source-file references, while related breeding event infrastructure is referenced — plausible unfinished scaffolding.
4. **Multiple tutorial island factory methods**, test builds and a missing StressTester project — credible development/test traces rather than scrapped gameplay confirmation.
5. **43 developer-comment locations**, including rewards and inventory code — maintenance history, requires context to infer functionality.

## Provenance limitation

Archive.org's metadata credits Big Blue Bubble but was uploaded by a third party in October 2023. The original studio repository and exact commit provenance are unverified. The internal date in an SQL filename does not prove that the complete archive was authored in 2012.

## Outputs for verification

- `server-full-file-index.csv`: every reviewed non-wordlist file, classification, bytes, date.
- `server-full-file-audit.md`: every file with Java classes, method inventories and JAR inventories.
- `server-full-file-audit.json`: machine-readable full inspection.
- `server-class-references.md` and `server-class-references.json`: class-by-class cross-file references.
- Existing `server-2012-game-seed.json`, `server-static-audit.json` and `server-gameplay-details.json`: SQL/game code findings.
- Scripts `server_full_file_audit.py`, `server_class_references.py` and previous inspectors.

The original third-party server source and JARs are not republished in the research ZIP.
