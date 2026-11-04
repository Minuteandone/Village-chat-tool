# My Singing Monsters public shared-file and pre-release archive audit
Research performed: November 3, 2026 (U.S. Eastern time)

## Executive summary
The strongest concrete lead is **My Singing Monsters Official Guide Downloaded Assets**, a user-uploaded public Internet Archive item posted on 2026-02-27. Its own description identifies archived assets from beta versions and a never-released Guide update from 2019. It is **not** an internal Big Blue Bubble source repository, an early playable main-game build, or a verified developer hard-drive leak.

Original item: https://archive.org/details/msm_official_guide_dlcs
Metadata endpoint (retrieved successfully from the GitHub Actions workspace): https://archive.org/metadata/msm_official_guide_dlcs

### Verified manifest inventory
- 471 file records, comprising **470** original entries and one additional derived metadata entry.
- The **40 version-labelled DLC folders**, ranging from 868 to 1428, are accompanied by four root-level archival files. (A count including the root as a group is 41, but it is not a version.)
- Listed sizes total ~4.70 GB, which is a sum of archive file records and not a single packaged archive size.
- Version 1428 (labelled October 23, 2019) has 21 entries across Android and iOS, approximately 249.6 MB of file-record sizes.
- Version 1383 (labelled September 26, 2019) has nine Android entries.
- The small public text file `missing prerelease files.txt` lists **108** paths absent from the current archive, from versions 868 through 1040. This explicitly documents gaps; the archive is not a complete beta reconstruction.
- The archive also includes versions labelled `1044 (1.0.0)`, `1072 (1.1.0)`, `1148 (1.2.0)`, and `1280 (1.3.0)`, as well as version folders with uncertain 2019 dates. These labels are from the archivist's directory names.

### Evidence of differences in 2019 bundles
Compared Android files in folders 1383 and 1428 using the archive's SHA-1 hashes:
- 5 shared files changed (`Server`, `data.unity3d`, `master.unity3d`, `msm1.unity3d`, `msm2.unity3d`).
- 3 shared files have identical SHA-1 hashes (`menu.unity3d`, `misc.unity3d`, `prefabs.unity3d`).
- 2 Android files appear in the 1428 folder but not the 1383 folder (`localization.unity3d` and `splash.unity3d`).
- `static_data.unity3d` appears in the 1383 folder but is not included in 1428's Android directory.
- **Caveat:** missing entries can mean an incomplete archive; these comparisons are of preserved files, not necessarily complete source builds. The hashes establish difference, not the reason for the difference.

This is *strong evidence of archived historical development-era materials*, but not evidence of a specific scrapped monster or unreleased feature in the binaries without further asset-level analysis.

### Supplementary public shared files

1. **Two official MSM press-kit ZIPs** linked from BBB's public press page. Direct links point to public Google Drive share pages (file titles verified by web display); contents not inspected. Official page: https://www.bigbluebubble.com/my-singing-monsters-press/
   - Old press kit: https://drive.google.com/file/d/0B7Dps0A2pdxWRHcwYXEzS08zSG8/view
   - MSM press kit: https://drive.google.com/file/d/0B7Dps0A2pdxWaXpzN3lsN1Zzb1U/view?resourcekey=0-EPOaiW6Ju8-Dz4q42JQ9uQ
   These are explicitly public PR material, not internal developer archives.
2. **Official educational file-sharing archive:** BBB's public teaching-guide page links an `All Lesson Plans.zip` on Google Drive with separate Grade 1–3 resources. Useful as independently published production material, but not inherently cut-content evidence. Official page: https://www.bigbluebubble.com/education/
3. **Old Windows build archive listing:** https://debugging.games/Windows contains public index entries for My Singing Monsters dated April 21 and May 18, 2021. These are listed as old PC manifests/build packages, *not* verified private development builds. No downloads performed.
4. **Original concept/design disclosures:** https://mysingingmonsters.fandom.com/wiki/Concept_Art catalogs studio-revealed early monster concepts and design codenames; these are not original source files or a verified shared studio directory.
5. **Main MSM extracted current asset set:** https://github.com/Next-Private-Server/Resources (covered in the earlier audit). This is one current extracted asset snapshot, not a historical source repo.

### Public document access checks
- `https://archive.org/metadata/msm_official_guide_dlcs`: readable via the owner's GitHub Actions `/work web download`; metadata file saved as `official-guide-archive-metadata.json`.
- The publicly posted `missing prerelease files.txt` redirects to an Archive.org file server. The generic workspace downloader intentionally forbids redirects, so a tightly-scoped owner-only public-note reader workflow was used. It retrieved the full note; its contents appeared in GitHub issue #3. No private API authorization or bypass was used.
- The actual 4.7GB Unity binary content was **not** downloaded or analyzed in this pass.
- No verified publicly shared internal studio source-code archive, private developer build, or original design repository surfaced in this investigation.

## Most promising next steps
1. Inspect just the small 2019 `data.unity3d`/`master.unity3d` bundles of versions 1383 and 1428; compare internal object names, without downloading 80MB image bundles if unnecessary.
2. Examine historically documented concepts from first-party videos/press materials for names that also appear in public archival file inventories.
3. Search for preserved early-guide releases rather than attempting inaccessible private Steam branches or Big Blue Bubble server paths.

## Evidence and tool links
- Public archive item: https://archive.org/details/msm_official_guide_dlcs
- Workspace source and findings: https://github.com/Minuteandone/Village-chat-tool/tree/main/workspace/msm-investigation
- Owner issue containing output of the public note reader: https://github.com/Minuteandone/Village-chat-tool/issues/3
- Public-source note retrieval workflow: https://github.com/Minuteandone/Village-chat-tool/blob/main/.github/workflows/msm-archive-note.yml
