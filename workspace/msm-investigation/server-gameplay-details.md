# Historical MSM server: SQL game-data schema and development-marker context

Source: https://archive.org/download/monster-game-server/monster-game-server.zip

Code was not executed. Player tables and row data are not reproduced.

## my_singing_monsters_clean_20120810.sql

- ads_in_house: 7 columns, 1 seed records
- breeding_combinations: 6 columns, 1041 seed records
- entities: 16 columns, 146 seed records
- game_settings: 4 columns, 19 seed records
- island_monsters: 4 columns, 45 seed records
- island_structures: 4 columns, 15 seed records
- islands: 12 columns, 5 seed records
- level_xp: 4 columns, 20 seed records
- monster_levels: 7 columns, 465 seed records
- monsters: 8 columns, 31 seed records
- quest_types: 6 columns, 6 seed records
- quests: 12 columns, 118 seed records
- store_currency: 4 columns, 4 seed records
- store_groups: 5 columns, 3 seed records
- store_items: 17 columns, 18 seed records
- structure_levels: 5 columns, not counted seed records
- structures: 7 columns, 91 seed records
- user_apple_purchases: 9 columns, not counted seed records
- user_baking: 6 columns, not counted seed records
- user_breeding: 7 columns, 1 seed records
- user_contact_info: 4 columns, not counted seed records
- user_eggs: 5 columns, not counted seed records
- user_friends: 2 columns, not counted seed records
- user_inhouse_ads: 4 columns, not counted seed records
- user_islands: 5 columns, not counted seed records
- user_messages: 6 columns, not counted seed records
- user_monsters: 14 columns, not counted seed records
- user_quests: 6 columns, not counted seed records
- user_structures: 13 columns, not counted seed records
- users: 12 columns, not counted seed records

## tribal_date_updated.sql


## Development markers mapped to nearby methods

- BBBToken.java:55 in (class-level) (TODO)
- MigBase64.java:17 in (class-level) (TEMPORARY)
- MigBase64.java:19 in (class-level) (TEMPORARY)
- MigBase64.java:20 in (class-level) (TEMPORARY)
- MigBase64.java:30 in (class-level) (TEMPORARY)
- MigBase64.java:457 in encodeToString (TEMPORARY)
- TutorialGroup.java:44 in getGroupToAssign (DISABLED)
- ScratchTicketFunctions.java:181 in getScaledPrizeAmounts (TODO)
- ScratchTicketFunctions.java:184 in getScaledPrizeAmounts (TODO)
- GameStateHandler.java:2625 in hatchingSpeedUp (TODO)
- GameStateHandler.java:3006 in sellMonster (HACK)
- GameStateHandler.java:5018 in breedingSpeedUp (TODO)
- GameStateHandler.java:6303 in sendTribeRequest (TODO)
- GameStateHandler.java:7535 in putDecorationInStorage (TODO)
- GameStateHandler.java:7688 in removeDecorationFromStorage (TODO)
- GameStateHandler.java:9183 in structureSpeedUp (TODO)
- GameStateHandler.java:9440 in clearObstacleSpeedUp (TODO)
- GameStateHandler.java:9699 in bakingSpeedUp (TODO)
- GameStateHandler.java:10172 in fuzingSpeedUp (TODO)
- GameStateHandler.java:10810 in processUncollectedOfferRewards (TODO)
- GameStateHandler.java:10868 in processUncollectedGlobalAchRewards (TODO)
- GameStateHandler.java:10886 in processUncollectedGlobalAchRewards (TODO)
- GameStateHandler.java:10898 in processUncollectedGlobalAchRewards (TODO)
- GameStateHandler.java:16393 in getGeneDB (TODO)
- GameStateHandler.java:16454 in getTorchGfxDB (TODO)
- GameStateHandler.java:16559 in getMonsterDB (TODO)
- GameStateHandler.java:16648 in getStructureDB (TODO)
- GameStateHandler.java:16730 in getIslandDB (TODO)
- GameStateHandler.java:16784 in getLevelDB (TODO)
- GameStateHandler.java:16839 in getScratchOffsDB (TODO)
- GameStateHandler.java:16992 in getStoreDB (TODO)
- GameStateHandler.java:17068 in getStoreDBv2 (HACK)
- GameStateHandler.java:17093 in getStoreDBv2 (TODO)
- MSMExtension.java:2789 in send (HACK)
- MSMExtension.java:2795 in send (TODO)
- MSMServerEventHandler.java:667 in send (HACK)
- MSMServerEventHandler.java:678 in send (TODO)
- Player.java:1155 in toSFSObject (UNUSED)
- PlayerAchievement.java:95 in getUserQuest (HACK)
- PlayerIsland.java:1680 in canPlace (TODO)
- PlayerMonster.java:1169 in stashCurrency (HACK, TESTING)
- PlayerQuest.java:268 in getId (HACK)
- PlayerStructure.java:89 in initFromSFSObject (FIXME)

A marker or a strange method name does not itself indicate scrapped content.
