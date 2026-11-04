# My Singing Monsters public server and asset investigation — November 3, 2026

## Scope and method
- Invoked the owner's `/work` GitHub Actions environment in `Minuteandone/Village-chat-tool`, issue #3.
- Tested a documented historical, official-looking Big Blue Bubble DLC manifest at `https://dlc2.bbbgame.net/my_singing_monsters_pc/dlc/4.2.1/r40831-zfUKpLse/files.json`; the actual response to the `/work web download` request was **HTTP 403**. No attempt was made to evade access controls.
- Retrieved the complete public Git tree for `Next-Private-Server/Resources` at `7d7be80226848c683cf5b28b1dac3045a75ac6c4` and ran `scan_assets.py` offline in the owner workspace.

## Audited contents
- **10,862 files** (the Git tree lists 10,901 total entries including directories; `truncated=false`).
- **2,643** music audio files matching `.ogg` or `.mid` under `audio/music`.
- **38** `world*.mid` files.
- **3** filenames explicitly containing a separated `test` token; **3** containing `placeholder`; **3** with a separated `admin` token.
- **0** filenames explicitly marked `unused`, `beta`, `prototype`, `deprecated`, or `scrapped` by the scan's strict filename rules. This does not imply that all the files are used.

## Concrete findings (verified by reading the underlying XML)
1. **Dish-Harmonizer test monster selector:** `split_asset_pack/menu_templates/template_dish_harmonizer_test_monster_select_entry.xml` invokes `dishHarmonizer:testDishHarmonizingMonsterSelect(...)`. It is paired with `split_asset_pack/menus/dish_harmonizer_test_monster_select.xml`. **Classification:** development/test interface still present in a public asset pack; no evidence of cancelled gameplay.
2. **Test egg selection menu:** `split_asset_pack/menus/test_select_egg.xml` is a full menu layout whose XML initiates a `BREED_SELECT` context. **Classification:** test-related UI remnant; runtime usage unverified.
3. **Placeholder ghost:** `split_asset_pack/xml_resources/placeholder_ghost_sheet.xml` defines MAJ and MIN placeholder images in 2×2, 3×3 and 4×4 sizes. There is also `xml_bin/placeholder_ghost.bin`. **Classification:** placeholder graphics descriptor confirmed. It is **not** evidence by itself of a cancelled ghost monster.
4. **Generic placeholder sign sheet:** `split_asset_pack/xml_resources/placeholder_sign_sheet.xml` lists signs for `attunement`, `evolve`, `fugue`, `synthesizer`, and `training`, plus three placeholder sign sizes. **Classification:** leftover/generic UI imagery; not necessarily scrapped.
5. **Admin quest-completion UI:** `split_asset_pack/menu_templates/template_admin_goalcontrols.xml` has a button labeled `AdminComplete` and invokes `game.adminCompleteQuest(...)`. The pack also contains `menus/admin_store.xml` and `xml_bin/contextbar_admin_def.bin`. **Classification:** developer/admin interface resources, not evidence of ordinary-user access or abandoned features.

## Evidence links
- Repository: https://github.com/Next-Private-Server/Resources
- Test selector: https://github.com/Next-Private-Server/Resources/blob/main/split_asset_pack/menu_templates/template_dish_harmonizer_test_monster_select_entry.xml
- Test egg menu: https://github.com/Next-Private-Server/Resources/blob/main/split_asset_pack/menus/test_select_egg.xml
- Ghost placeholder descriptor: https://github.com/Next-Private-Server/Resources/blob/main/split_asset_pack/xml_resources/placeholder_ghost_sheet.xml
- Sign placeholder descriptor: https://github.com/Next-Private-Server/Resources/blob/main/split_asset_pack/xml_resources/placeholder_sign_sheet.xml
- Admin controls: https://github.com/Next-Private-Server/Resources/blob/main/split_asset_pack/menu_templates/template_admin_goalcontrols.xml
- SteamDB historical Steam client diffs: https://steamdb.info/patchnotes/26216944/
- Source of archived official manifest URL: https://t.me/s/msmprivate/98

## Limits and next steps
The public resource repository is a snapshot, not a complete history of all builds. Without tracing runtime references or comparing historical versions, filenames and leftover XML cannot prove that something was scrapped or unreleased. The archival manifest responded 403. Future research should prioritize legally/publicly available historical builds and version-to-version comparisons, not protected server endpoints. Any unknown IDs must be cross-checked with release history before being called cut content.
