# Overlooked MSM preservation leads — November 4, 2026

Scope: new public leads beyond the previously investigated server ZIP and official guide DLC collection. This document is evidence-based reconnaissance, not a declaration of recovered lost files.

## Highest priority: historically posted Android APKs on 4PDA

The Russian Android forum 4PDA, topic `389382`, indexed posts describing older *My Singing Monsters* APK attachments:

| Version | Dated forum evidence | File label and recorded size | Why it matters |
|---|---|---|---|
| 1.0.4 | 2012-era version in thread's pinned listing | `singingmonsters.full-1.apk` — 19.93 MB | Very early Android version, contemporaneous with 2012 game |
| 1.1.6 | 15 May 2013, post #18 | `My Singing Monsters-17.apk` — 26.84 MB | Listed as lost in one lost-version catalog |
| 1.2.4 | 22 Jan 2014, post #52 | `com.bigbluebubble.singingmonsters.full-1.2.4.apk` — 44.55 MB | Precedes rare 1.2.5/1.2.7 |
| 1.2.5 | 1 Feb 2014, post #59 | `com.bigbluebubble.singingmonsters.full-1.apk` — 46.76 MB | Intermediate version in potentially preserved copy |
| 1.2.7 | 24 Apr 2014, post #83 | `com.bigbluebubble.singingmonsters.full-1.2.7.apk` — 46.76 MB | Version listed as lost in one fan-maintained catalog |
| 1.2.9 | 2014 posts from same thread | `com.bigbluebubble.singingmonsters.full-1.2.9.apk` — 48.82 MB | Historical reference build |
| 1.3.0 and 1.3.1 | Oct–Dec 2014 | separately advertised copies | Some version labels were disputed in the thread; don't trust names alone |

Evidence:
- https://4pda.to/forum/index.php?showtopic=389382
- https://4pda.to/forum/index.php?showtopic=389382&st=40
- https://4pda.to/forum/index.php?showtopic=389382&st=80
- https://lostmediaarchive.fandom.com/wiki/My_Singing_Monsters_(lost_apk_versions)

The indexed posts and listing text **are verified to exist**. We have **not** recovered or fingerprinted the APK file bytes. The forum blocks live page access in this environment (HTTP 403); attachments may require login, may be gone, and may not match the labels. A 2014 post in the same thread explicitly complains about a version mismatch, reinforcing the need for package-name, signed-version, and hash verification before treating any file as genuine. Do not install unverified APKs.

Independent historical corroboration for 1.2.7: https://mysingingmonsters.info/fails-but-no-support/ — May 2014 user says they installed 1.2.7 from Google Play.

Another public catalog lists an APK identified as **1.0.4** and dated Oct 19, 2012 with size 19.93 MB:
https://my-singing-monsters.apk.gold/
That independently matches the 4PDA archive-list size, but does **not** independently establish checksum or binary identity.

## Secondary: old Monster Choir international branches

The Chinese/Korean official licensed versions `怪兽合唱团` and `몬스터 합창단` used distinct artwork, gameplay variant systems, and a separate update line. Wiki documentation mentions unused placeholder sprites and earlier redesigned variant artwork, including 1.2 and 1.3 versions. The key question for preservation is whether an older app package (rather than just screenshots or later builds) contains otherwise missing layers, audio, and sprite assets.

- https://mysingingmonsters.fandom.com/wiki/Monster_Choir
- https://mysingingmonsters.fandom.com/wiki/Monsters_(Monster_Choir)
- https://www.spriters-resource.com/mobile/monsterchoirmysingingmonsterskoreanchineseversion/

This is **not** a new find of unused art; those references are already documented publicly. It is a **file-recovery comparison priority**, and needs separate checksums/version stamps to avoid mixing Chinese/Korean versions.

## Negative result: worldXX.mid files on Steam are not naturally cut songs

A Steam discussion from July 2026 wondered about `world01.mid` and `world101.mid`; SteamDB confirms they exist alongside many other numbered world files.

However, the open-source `msm-song-creator` demonstrably uses `world01.mid` for recreating **normal island arrangements** together with the recorded audio stems. Treat this as a false positive rather than calling the MIDIs scrapped music.

- https://steamdb.info/depot/1419171/manifests/
- https://steamcommunity.com/app/1419170/discussions/0/588432892838007314/
- https://github.com/RubixDev/msm-song-creator

SteamDB historical **changes**, not filenames alone, may still reveal temporarily shipped assets that disappeared in later updates.

## Other platform comparison opportunities

- The 2014 PS Vita version remained unupdated while other versions changed. A verified offline-era Vita build could potentially preserve art, arrangement, and UI differences.
- The discontinued Big Fish Windows version ended at 1.2.9; do not conflate it with Steam versions.
- The 2015 Amazon Appstore/Kindle builds of Dawn of Fire could preserve version-specific packages compared with Google Play and iOS.
- The early My Muppets Show beta files and 2013 versions may preserve abandoned stages, but this has its own existing preservation literature and is secondary to MSM-specific leads.

## Status and priorities

**Recovered and authenticated new unused files:** none yet.
**Strong lead with verifiable historical attachment listings:** 4PDA MSM Android 1.1.6 and 1.2.7, including specific dates, names and sizes.
**Next discriminating evidence:** actual file bytes, APK manifest versionCode/versionName, code signing certificates and SHA-256; compare with game-version timeline and available modern/old file catalogs, without executing the app.

This avoids misidentifying standard island MIDIs or fan content as official scrapped assets.
