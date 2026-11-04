# Full MSM game-class cross-reference analysis

Every MSM Java class is included; no code contents, player records or credentials are reproduced.

## Interesting classes

### BrandedAdvertisementGroup

Source lines: 16; parsed method names: ; referencing files: 1
References: UserGroup.java

### MonsterIslandData

Source lines: 14; parsed method names: ; referencing files: 3
References: MonsterIslandToIslandMapping.java, GameStateHandler.java, MSMExtension.java

### MonsterRareData

Source lines: 17; parsed method names: ; referencing files: 4
References: BreedingLookup.java, MonsterCommonToRareMapping.java, ScratchTicketFunctions.java, MSMExtension.java

### StoreReplacements

Source lines: 86; parsed method names: Initialize, addReplacementItem, currentlyReplacesAnotherStoreItem, getValueEntityId, getData; referencing files: 3
References: Entity.java, GameStateHandler.java, MSMExtension.java

### BreedAvailabilityEvent

Source lines: 14; parsed method names: ; referencing files: 1
References: TimedEventList.java

### BreedProbabilityChangeEvent

Source lines: 14; parsed method names: ; referencing files: 0
References: 

### TimedEventListBuilder

Source lines: 210; parsed method names: activeEventsInNext24Hours, addNewEventFromDb, doErrorCheckingOnTimedEvent, UpdateActiveTimedEvents, removeFinishedEvents, addNewlyActiveEvents, addToActiveEvents, UpdateCachedSFSArrayOfEvents; referencing files: 1
References: TimedEventList.java

### MonsterMegaData

Source lines: 148; parsed method names: initFromSFSObject, toSFSObject, isPermaMega, resetMega, resetTempMegaTime, megaExpired, enableMega, getData, toString; referencing files: 1
References: PlayerMonster.java

### PlayerIslandFactory

Source lines: 337; parsed method names: CreateIslandInitialStructures, CreateTutorialIsland, CreateBasicTutorialIsland, CreateBreedingTutorialIsland, CreateTypicalIsland, CreateComposerIsland, createCastle, createNursery, createBreedingStructure, createNoggin, createTutorialMammott, createComposerMammott, createMonster, createIslandObstacles, createStructure, createObstacle, createNoCompletionStructure; referencing files: 3
References: TutorialGroup.java, GameStateHandler.java, MSMExtension.java

### MSMAdminCatchUnreleasedAccount

Source lines: 135; parsed method names: addAccountToCSRPermaLockPreventionList, resetAccountAccessTime, cancelSchedule, run, removeFromLockedAccountsList, clearUnreleasedAcccount; referencing files: 1
References: MSMExtension.java

## All classes and cross-references

- BreedingCombination: 1 other Java source files; 6 parsed methods
- BreedingLookup: 2 other Java source files; 7 parsed methods
- Code: 4 other Java source files; 15 parsed methods
- CodeLookup: 2 other Java source files; 4 parsed methods
- Entity: 8 other Java source files; 37 parsed methods
- Gene: 3 other Java source files; 5 parsed methods
- GeneLookup: 2 other Java source files; 4 parsed methods
- Advertisement2018Group: 3 other Java source files; 3 parsed methods
- AdvertisementGroup: 2 other Java source files; 6 parsed methods
- BaseGroup: 1 other Java source files; 6 parsed methods
- BrandedAdvertisementGroup: 1 other Java source files; 0 parsed methods
- CurrencyGroup: 2 other Java source files; 2 parsed methods
- NoAdvertisementGroup: 3 other Java source files; 4 parsed methods
- ScientificRevenueGroup: 5 other Java source files; 9 parsed methods
- TutorialGroup: 7 other Java source files; 8 parsed methods
- UserGroup: 11 other Java source files; 7 parsed methods
- Island: 9 other Java source files; 19 parsed methods
- IslandLookup: 9 other Java source files; 3 parsed methods
- IslandTorch: 3 other Java source files; 3 parsed methods
- Level: 5 other Java source files; 3 parsed methods
- LevelLookup: 3 other Java source files; 3 parsed methods
- Mail: 4 other Java source files; 19 parsed methods
- MailLookup: 3 other Java source files; 5 parsed methods
- MemoryMinigameFunctions: 1 other Java source files; 2 parsed methods
- Monster: 15 other Java source files; 32 parsed methods
- MonsterCommonToRareMapping: 6 other Java source files; 7 parsed methods
- MonsterIslandData: 3 other Java source files; 0 parsed methods
- MonsterIslandToIslandMapping: 2 other Java source files; 8 parsed methods
- MonsterLookup: 19 other Java source files; 5 parsed methods
- MonsterRareData: 4 other Java source files; 0 parsed methods
- MsmSession: 2 other Java source files; 0 parsed methods
- Promo: 3 other Java source files; 8 parsed methods
- PromoLookup: 2 other Java source files; 3 parsed methods
- QuestLookup: 4 other Java source files; 5 parsed methods
- ScientificRevenue: 4 other Java source files; 37 parsed methods
- ScratchTicketFunctions: 2 other Java source files; 6 parsed methods
- SegmentationGroup: 2 other Java source files; 5 parsed methods
- Sticker: 3 other Java source files; 4 parsed methods
- StickerLookup: 2 other Java source files; 3 parsed methods
- StoreCurrencyLookup: 3 other Java source files; 4 parsed methods
- StoreGroupsLookup: 3 other Java source files; 4 parsed methods
- StoreItemsLookup: 4 other Java source files; 4 parsed methods
- StoreReplacementItem: 1 other Java source files; 1 parsed methods
- StoreReplacements: 3 other Java source files; 5 parsed methods
- Structure: 8 other Java source files; 20 parsed methods
- StructureLookup: 10 other Java source files; 5 parsed methods
- CurrencyAvailabilityList: 1 other Java source files; 2 parsed methods
- CurrencySalesList: 1 other Java source files; 2 parsed methods
- EntityAvailList: 1 other Java source files; 2 parsed methods
- EntitySalesList: 1 other Java source files; 2 parsed methods
- IslandSalesList: 1 other Java source files; 2 parsed methods
- ITimedEventTypeList: 3 other Java source files; 6 parsed methods
- KeyedTimedEventTypeList: 7 other Java source files; 4 parsed methods
- MegafySaleList: 1 other Java source files; 2 parsed methods
- PermalightTorchSaleList: 1 other Java source files; 2 parsed methods
- ShortenedFuzingList: 1 other Java source files; 2 parsed methods
- StarAvailList: 1 other Java source files; 2 parsed methods
- StarSalesList: 1 other Java source files; 2 parsed methods
- TimedEventTypeList: 3 other Java source files; 4 parsed methods
- BreedAvailabilityEvent: 1 other Java source files; 0 parsed methods
- BreedProbabilityChangeEvent: 0 other Java source files; 0 parsed methods
- CurrencyAvailabilityEvent: 1 other Java source files; 3 parsed methods
- CurrencySalesEvent: 2 other Java source files; 3 parsed methods
- EntityAvailabilityEvent: 2 other Java source files; 3 parsed methods
- EntitySalesEvent: 3 other Java source files; 9 parsed methods
- IslandSalesEvent: 2 other Java source files; 9 parsed methods
- MegafySale: 4 other Java source files; 9 parsed methods
- PermalightTorchSale: 4 other Java source files; 9 parsed methods
- ShortenedFuzing: 4 other Java source files; 9 parsed methods
- StarAvailabilityEvent: 1 other Java source files; 3 parsed methods
- StarSalesEvent: 4 other Java source files; 9 parsed methods
- TimedEvent: 20 other Java source files; 10 parsed methods
- TimedEventList: 7 other Java source files; 9 parsed methods
- TimedEventListBuilder: 1 other Java source files; 8 parsed methods
- TorchLookup: 3 other Java source files; 4 parsed methods
- TribalQuestLookup: 1 other Java source files; 2 parsed methods
- VersionData: 5 other Java source files; 5 parsed methods
- InvalidPlayerException: 1 other Java source files; 0 parsed methods
- GameStateHandler: 3 other Java source files; 241 parsed methods
- Helpers: 2 other Java source files; 3 parsed methods
- GooglePlayEvents: 2 other Java source files; 6 parsed methods
- MetricCost: 2 other Java source files; 3 parsed methods
- MSMCommandLogging: 3 other Java source files; 11 parsed methods
- MSMCommands: 1 other Java source files; 0 parsed methods
- MSMExtension: 54 other Java source files; 56 parsed methods
- MSMServerEventHandler: 1 other Java source files; 22 parsed methods
- InitialPlayerIslandData: 4 other Java source files; 0 parsed methods
- LitPlayerTorch: 3 other Java source files; 11 parsed methods
- MonsterMegaData: 1 other Java source files; 9 parsed methods
- Player: 24 other Java source files; 194 parsed methods
- PlayerAchievement: 2 other Java source files; 15 parsed methods
- PlayerActiveIslandStats: 1 other Java source files; 11 parsed methods
- PlayerBaking: 2 other Java source files; 16 parsed methods
- PlayerBreeding: 2 other Java source files; 16 parsed methods
- PlayerBuyback: 2 other Java source files; 9 parsed methods
- PlayerEgg: 2 other Java source files; 18 parsed methods
- PlayerFuzeBuddy: 4 other Java source files; 16 parsed methods
- PlayerIsland: 11 other Java source files; 140 parsed methods
- PlayerIslandFactory: 3 other Java source files; 17 parsed methods
- PlayerMonster: 8 other Java source files; 87 parsed methods
- PlayerQuest: 3 other Java source files; 34 parsed methods
- PlayerStructure: 6 other Java source files; 58 parsed methods
- ShutdownHookThread: 1 other Java source files; 1 parsed methods
- AuthTokenUpdateTask: 1 other Java source files; 1 parsed methods
- MailUpdateTask: 1 other Java source files; 1 parsed methods
- MSMAdminCatchUnreleasedAccount: 1 other Java source files; 6 parsed methods
- MSMMonsterLinksReloadTask: 1 other Java source files; 1 parsed methods
- MSMServerStatusTask: 1 other Java source files; 1 parsed methods
- MSMStats: 2 other Java source files; 52 parsed methods
- UpdateActiveTimedEvents: 3 other Java source files; 2 parsed methods
