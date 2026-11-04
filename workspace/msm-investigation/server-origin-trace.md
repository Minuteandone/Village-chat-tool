# Where did the "My Singing Monsters Game Server" archive come from?

Investigation date: 2026-11-03 (US Eastern).

## Short conclusion

**Updated assessment after inspecting the ZIP header:** the upload has a Git-like folder name, but the ZIP has **no archive comment** and mixed July 2020 file / May 2021 directory timestamps. It could be a **repackaged copy of a Git-derived tree**; the exact packaging tool, hosting provider, original repository owner and author are **not established**. See `server-zip-comment-analysis.md`.

### Facts independently verified from the archive

- Archive item: https://archive.org/details/monster-game-server
- Original metadata: https://archive.org/metadata/monster-game-server
- Public upload date: **October 7, 2023**.
- `creator` value is the unverified, uploader-supplied label **Big Blue Bubble**.
- Entire description is `lmao`. Neither description nor original XML metadata contains an origin story or source-repository URL.
- The item has one later review (January 2026) asking what it does; it provides no provenance.
- Original ZIP filename is `monster-game-server.zip`, size **15,170,251 bytes**, SHA-1 `df086c9ca4581733f73f2e8aaea1408382232e4d`.
- The ZIP's sole top-level directory is:
  `monster-game-server-266e600f69ed8e462f26416704266d042dd2cf84`
- The ZIP has **188 regular files** (including the excluded wordlist) with dates July 3, 2020 at **15:47:56–15:48:02**, and **27 directories** dated May 9, 2021 at **20:25:24–20:25:28**. These are local ZIP timestamps, not independently verified commit dates.
- **ZIP-global comment: empty** (0 bytes; also confirmed directly in end-of-central-directory header). A normal native `git archive --format=zip` of a commit writes the commit ID there.
- The ZIP contains a coherent Java server source tree and compiled JARs, plus the `my_singing_monsters_clean_20120810.sql` seed database. Later-era classes such as `Advertisement2018Group.java` make the idea of an untouched 2012 codebase untenable.

### Why the folder format matters

GitHub's documentation explains that source snapshots can be generated for specific commits and that the name of the repository is part of the archive's internal directory structure:

https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives

The Git project documents that archives of a commit normally use the commit time for archive member modification times:

https://github.com/git/git/blob/master/Documentation/git-archive.adoc

The directory name `monster-game-server-` followed by a 40-hex-digit identifier **resembles** the root prefix of a Git-hosted source snapshot, but that form is not specific to GitHub. Crucially, the ZIP lacks a commit comment and contains different timestamps for files versus directories, with a gap of ten months. These findings **weaken** the hypothesis that the surviving ZIP is an untouched `git archive` from a specific July 2020 commit. Its contents could have originated in Git and been **repacked later**; neither the original provider nor the meaning of the suffix has been cryptographically proven.

### Can we retrieve the old repository?

Public GitHub repository-name search presently did not locate the exact historical project `monster-game-server`; results for that name were unrelated projects. Searches for the complete 40-digit identifier and archive-specific class/SQL filenames also did not yield an indexed original source repository.

An examination of `MSM-Hacks/MSM-Hacks-Server` found a **different source layout**, and the current repository was created in 2023. It is not evidence that this 2020-dated ZIP came from that repo.

The old repository might have been deleted, renamed, made private, or not indexed by public search; the archive might also have been renamed or assembled to mimic GitHub naming. **Do not choose among these possibilities without evidence.**

### Two different origin questions

1. **Immediate origin of the Internet Archive ZIP:** possibly a repackaged Git-derived source tree. Mixed timestamp groups and absence of an archive comment argue against identifying the exact ZIP as a direct native Git commit archive. Who packaged it and where it circulated before 2023 remain unknown.
2. **Original source of the MSM server implementation:** its internal package names and gameplay-specific data suggest substantial historical MSM/BBB-derived backend code, not a tiny toy remake, but the original studio repository, employee authorship, and release authorization have **not** been independently authenticated. It may have been repackaged or modified in fan communities.

### What the upload does *not* prove

- It does not prove the Big Blue Bubble official account uploaded this (the archive's `creator` field is self-reported).
- It does not prove a malicious leak or security breach occurred.
- It does not prove the source was publicly available on GitHub in 2020; the 2020 date is only an entry timestamp here, and **cannot be reliably called a commit timestamp**.
- It does not prove the old repo still exists or that the owner of the 2023 Archive upload owned the source in 2020.
- It does not prove the 2012-named SQL file was itself made in August 2012; it is an internal filename in a later snapshot.

## Further legitimate provenance leads

- A public 2020-or-earlier archive/citation of a repository whose exact name is `monster-game-server` and contains commit `266e600f69ed8e462f26416704266d042dd2cf84`.
- Public release notes or project README mentioning this exact repository or hash.
- An answer from the 2023 Internet Archive contributor about where they obtained the ZIP.
- An authorized statement from Big Blue Bubble about whether this tree resembles their backend source.

Do not access private repos without permissions or attempt to use the archived credentials/infrastructure for attribution.

## Research outputs

The complete file-level assessment remains in `server-everything-summary.md`, `server-full-file-audit.json`, `server-full-file-index.csv`, and related scripts. The existing reports do not republish server code.

## ZIP comment verification (new)

Full inspected metadata: `server-zip-provenance.json`; explanation: `server-zip-comment-analysis.md`. ZIP-global comment length **0**, entry comments **0**, all ZIP creator-system values **0 (DOS convention)**, and **no extra fields**. This does not identify a service. Files and directories have different timestamp groups; do not claim an untouched 2020 snapshot.
