# Archived MSM server source: static review

ZIP hash verified. No server code executed or republished.

Java source files: 155
Archive size: 15170251 bytes

## Game-system method names

### BreedingLookup.java

init, add, getBreedingResult, getMonsterBreedWeightContribution, getDatabaseBreedingComboResult, findTotalProbability, probabilityWithTorches

### GameStateHandler.java

handleClientRequest, getPromotions, deleteComposerTemplate, saveComposerTemplate, saveComposerTrack, dailyLoginBuyback, diamondsRequiredToComplete, updateDisplayName, redeemCode, transferCode, adminGetCodes, serverQuestEvent, buyEgg, transferEgg, sellEgg, adminHatchNonEgg, hatchEgg, hatchingSpeedUp, feedMonster, muteMonster, flipMonster, moveMonster, sellMonster, collectSpecialFromMonster, collectFromMonster, nameMonster, tribalFeedMonster, adminNameMonster, adminBoxActivateMonster, adminFinishedEdit, boxActivateMonster, boxPurchaseFillCost, adminBoxPurchaseFill, boxPurchaseFill, boxAddEgg, boxAddUnderlingEgg, adminBoxMonsterToggle, boxAddMonster, adminBoxToggleMonster, sendMonsterHome, deleteParentData, deleteAssociatedGoldMonster, testBreeding, adminQASelectBreedEgg, breedMonsters, finishBreeding, breedingSpeedUp, processAdminNeighborChangeMsg, processAdminMultiNeighborChangeMsg, processMultiNeighborChangeMsg, generateMonsterHappinessUpdate, updateMonsterHappiness, calculateHappiness, triggerNeighborQuest, adminChangeUserHappiness, buyIsland, changeIsland, adminPlaceOnGoldIsland, placeOnGoldIsland, saveIslandWarpSpeed, placeOnTribal, adminSwapTribalMonster, islandHasTribalMonster, playerInOtherTribe, cancelTribeInvite, declineAllTribeInvites, cancelTribeRequest, sendTribeRequest, sendTribeInvite, joinTribe, leaveTribeRequest, kickTribeRequest, updateTribeName, updateIslandName, refreshTribeRequests, getRequests, buyStructure, addHappyTreeEffects, moveStructure, sellStructure

### MSMAdminCatchUnreleasedAccount.java

cancelSchedule, run, clearUnreleasedAcccount

### MSMExtension.java

initGameSettings, CurrentDBTime, getInstance, getScratchOffs, isDevServer, scratchOffPrizeSupportedByServerVer, init, sendVersionError, adminCreatePlayerByBBBID, updateLastLogin, checkQuestDataForErrors, isAValidQuest, createPlayerByBBBID, createPlayerByID, createPlayerWithUserRecord, initializePlayerQuestData, initializePlayerAchievementData, initializePlayerGroupsFromUserGroupsTable, initializeAdvertisementGroup, initializePlayerScratchTicketData, initializePlayerIslands, initializePlayerAds, initializePlayerMusic, setupPlayerScratchData, setupPlayerPromotions, initializePlayerScientificRevenue, loadPlayerIslandData, loadPlayerTribalIslandData, createPlayerIsland, createTribalIsland, joinTribalIsland, sendPlayerState, sendQuests, sendErrorResponse, sendAdminMessage, savePlayer, savePlayerQuests, savePlayerIsland, destroy, loadAndCacheStaticData, processUnclaimedPurchases, addScientificRevenueUserTag, updateScientificRevenueUserTags, updateTapjoyUserTags, processUncollectedOfferRewards, sendGameSettings, logMessage, loadGameSettings, send, updateSocialUsers

### MSMServerEventHandler.java

handleLoginData, userJoinZone, CreateNewPlayer, CreateNewBbbIdDbEntry, CreateNewPlayerDbEntry, initializeNewPlayerGroups, initializeFirstIsland, initializeEmptyQuests, addUserToInitialGroupsTable, selectTutorialGroupForNewUser, selectNoAdvertisementGroupForNewUser, selectScientificRevenueGroupForNewUser, selectAdvertisement2018GroupForNewUser, addUserToGroupTable, userHasNewerDataThanClientVersion, getClientLastUpdateVersion, userLogin, userLogout, userDisconnect, userReconnectSuccess, userReconnectTry, send

### MemoryMinigameFunctions.java

canPlayMemoryMinigame, getMemoryMinigameUserData

### Monster.java

specialCollectionRate, getNames, generateRandomMonsterName, getGenes, setTimeToFillSec, getTimeToFillSec, isSeasonalMonster, isDipster, getCompleteData, isBoxMonsterType, getBoxRequirements, initGoldBoxMonsterRequirements, isLegendaryMonster, isGoldUpgradeMonster, isEtherealMonster, getGoldBoxMonsterRequirements, getGoldRareBoxMonsterRequirements, getLikes, getDislikes, getLevel, getMonsterID, coinRate, etherealRate, beds, upgradesTo, getLinkTitle, getLinkAddress, setLinkTitle, setLinkAddress, setLastUpdated, isValidMonsterForVersionFromId, isTrackedUncommon

### MonsterLookup.java

init, add, get, getFromEntityId, iterator

### MonsterRareData.java



### PlayerEgg.java

initFromSFSObject, getData, toSFSObject, toString, getID, getType, getParentID, setParentID, getStructureID, getPreviousName, getPrevPermaMega, getTimeRemaining, getInitialTimeRemaining, finishHatchingNow, getCompletionTime, getStartTime, reduceHatchingTimeByVideo

### PlayerFuzeBuddy.java

initStaticData, initFromSFSObject, getData, toSFSObject, toString, getStructureID, getTimeRemaining, getInitialTimeRemaining, finishNow, getCompletionTime, getStartTime, getCreate, getR, getY, getB, reduceFuzingTimeByVideo

### PlayerIsland.java

toString, initFromSFSObject, toSFSObject, soldMonsterTypes, initStructures, initMonsters, initTribalRequests, initTribalIslandData, initTribalQuests, addChiefData, getTribalIslandData, getTribalRequests, initMonstersFromJson, initSoldMonstersFromJson, initStructuresFromJson, initEggs, initBreeding, initBaking, initFuzeBuddies, initTorches, fixMonsterLevels, checkForInvalidData, initBuyback, initLastBred, setLastPlayerLevel, setGiMappings, getIslandMonsterData, getIslandStructureData, getIslandVolatileData, getName, getID, getUser, getType, getIndex, getTribalID, getDateCreated, getLikes, getDislikes, getWarpSpeed, setWarpSpeed, isGoldIsland, isRegularIsland, isShugaIsland, isEtherealIsland, isTribalIsland, isUnderlingIsland, isComposerIsland, isCelestialIsland, isFireIsland, getMonsters, getMonsterByID, changeMonsterID, addMonster, removeMonster, addToSoldMonsters, getStructures, getStructureByID, addStructure, removeStructure, hasMax, hasHappinessTree, hasStructure, numStructuresOfEntTypeOnIsland, getNextStructureId, getMonsterBaseBuildTimeForIsland, getBreeding, getBreedings, getBreedCompletionTimeForIsland, testBreed, getAvailableEmptyBreedingStructure, getBusyBreedingStructure, startNewBreed, makeNewBreeding, getBreedResult, setBreeding, removeBreeding, breedingFull, finishBreeding, getEgg, getEggs

### PlayerMonster.java

GetRandom, CachedCollectionTypes, getCurrencyStrFromType, createMonsterSFS, startEggTimer, eggTimerStart, collectionOfDyingFetuses, resetEggTimer, clearRottenEggs, initDefaultValues, initFromSFSObject, toSFSObject, DebuggingIslandSet, toSFSObjectWithoutBoxData, getMegaSFS, toString, getName, getID, getType, getLastCollectedTime, getLevel, getParentID, getTimesFed, getCollectedCoins, getCollectedEth, getCollectedDiamonds, getCollectedFood, getCollectedStarpower, getXPosition, getYPosition, getVolume, getHappiness, getMuted, getFlip, levelUp, setLevel, getGoldIslandData, removeGoldIslandData, getParentIslandData, markForDeletion, inHotel, setID, setParentID, setPosition, setVolume, setHappiness, resetTimesFed, setName, toggleMute, toggleFlip, setFlip, feed, tribalFeed, setGoldIslandData, setParentIslandData, isInactiveBoxMonster, setBoxMonsterData, isPermaMega, megaEnable, isMega, isDailyMega, dailyMegaExpired, makeMega, getBoxMonsterPossessedEggs, getRemainingMonsterTypes, adminRemoveEgg, addEgg, hasNumOfEgg, numBoxReqsOfTypeReqd, getBoxRequirements, boxMonsterBuyPossessedEggsPrice, boxMonsterSellingPrice, hasAllRequiredEggs, needsEgg, activateBoxMonster, CurrentCollectionType, getRandomUnderlingCollectionMin, resetUnderlingCurrencyType, validCollectionType, validRandomTime

### PromoLookup.java

init, add, get

### QuestLookup.java

init, getDefaultTutorialQuests, getById, getByName, getValues

### ScratchTicketFunctions.java

initializeScratchOff, getScaledPrizeAmounts, scaleScratchReward, roundToHundreds, getAlternativeMonsterScratch, getPossibleRare

### ShortenedFuzingList.java

GetKey, makeEvent

### TribalQuestLookup.java

init, getValues

## SQL tables

### my_singing_monsters_clean_20120810.sql

ads_in_house, breeding_combinations, entities, game_settings, island_monsters, island_structures, islands, level_xp, monster_levels, monsters, quest_types, quests, store_currency, store_groups, store_items, structure_levels, structures, user_apple_purchases, user_baking, user_breeding, user_contact_info, user_eggs, user_friends, user_inhouse_ads, user_islands, user_messages, user_monsters, user_quests, user_structures, users

### tribal_date_updated.sql



## Development marker locations

- BBBToken.java:55 (TODO)
- MigBase64.java:17 (TEMPORARY)
- MigBase64.java:19 (TEMPORARY)
- MigBase64.java:20 (TEMPORARY)
- MigBase64.java:30 (TEMPORARY)
- MigBase64.java:457 (TEMPORARY)
- TutorialGroup.java:44 (DISABLED)
- ScratchTicketFunctions.java:181 (TODO)
- ScratchTicketFunctions.java:184 (TODO)
- GameStateHandler.java:2625 (TODO)
- GameStateHandler.java:3006 (HACK)
- GameStateHandler.java:5018 (TODO)
- GameStateHandler.java:6303 (TODO)
- GameStateHandler.java:7535 (TODO)
- GameStateHandler.java:7688 (TODO)
- GameStateHandler.java:9183 (TODO)
- GameStateHandler.java:9440 (TODO)
- GameStateHandler.java:9699 (TODO)
- GameStateHandler.java:10172 (TODO)
- GameStateHandler.java:10810 (TODO)
- GameStateHandler.java:10868 (TODO)
- GameStateHandler.java:10886 (TODO)
- GameStateHandler.java:10898 (TODO)
- GameStateHandler.java:16393 (TODO)
- GameStateHandler.java:16454 (TODO)
- GameStateHandler.java:16559 (TODO)
- GameStateHandler.java:16648 (TODO)
- GameStateHandler.java:16730 (TODO)
- GameStateHandler.java:16784 (TODO)
- GameStateHandler.java:16839 (TODO)
- GameStateHandler.java:16992 (TODO)
- GameStateHandler.java:17068 (HACK)
- GameStateHandler.java:17093 (TODO)
- MSMExtension.java:2789 (HACK)
- MSMExtension.java:2795 (TODO)
- MSMServerEventHandler.java:667 (HACK)
- MSMServerEventHandler.java:678 (TODO)
- Player.java:1155 (UNUSED)
- PlayerAchievement.java:95 (HACK)
- PlayerIsland.java:1680 (TODO)
- PlayerMonster.java:1169 (HACK, TESTING)
- PlayerQuest.java:268 (HACK)
- PlayerStructure.java:89 (FIXME)

These identifiers alone do not prove that a feature was cut or unfinished.
