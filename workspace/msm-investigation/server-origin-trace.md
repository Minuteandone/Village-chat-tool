# Where did the "My Singing Monsters Game Server" archive come from?

Investigation date: 2026-11-03 (US Eastern).

## Short conclusion

**Best-supported lead:** the 2023 Internet Archive upload appears to contain a **GitHub-style source snapshot** of a repository named `monster-game-server`, probably at a snapshot whose embedded date is 2020-07-03. The precise repository owner, origin of the underlying source, and authorization to distribute it are **not established**.

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
- All **187 non-wordlist regular files examined** have the *same ZIP entry date* **July 3, 2020**.
- The ZIP contains a coherent Java server source tree and compiled JARs, plus the `my_singing_monsters_clean_20120810.sql` seed database. Later-era classes such as `Advertisement2018Group.java` make the idea of an untouched 2012 codebase untenable.

### Why the folder format matters

GitHub's documentation explains that source snapshots can be generated for specific commits and that the name of the repository is part of the archive's internal directory structure:

https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives

The Git project documents that archives of a commit normally use the commit time for archive member modification times:

https://github.com/git/git/blob/master/Documentation/git-archive.adoc

The directory name `monster-game-server-` followed by a 40-hex-digit identifier, combined with uniform internal timestamps, **strongly resembles a commit-specific GitHub ZIP**. In that case, the identifier is likely a full commit SHA and July 3, 2020 likely the commit timestamp. This is a high-confidence *format inference*, not a cryptographic validation that the hash is a real commit or was created by an authorized studio member.

### Can we retrieve the old repository?

Public GitHub repository-name search presently did not locate the exact historical project `monster-game-server`; results for that name were unrelated projects. Searches for the complete 40-digit identifier and archive-specific class/SQL filenames also did not yield an indexed original source repository.

An examination of `MSM-Hacks/MSM-Hacks-Server` found a **different source layout**, and the current repository was created in 2023. It is not evidence that this 2020-dated ZIP came from that repo.

The old repository might have been deleted, renamed, made private, or not indexed by public search; the archive might also have been renamed or assembled to mimic GitHub naming. **Do not choose among these possibilities without evidence.**

### Two different origin questions

1. **Immediate origin of the Internet Archive ZIP:** likely a previously distributed GitHub-style project snapshot. Who downloaded it or passed it to the 2023 uploader remains unknown.
2. **Original source of the MSM server implementation:** its internal package names and gameplay-specific data suggest substantial historical MSM/BBB-derived backend code, not a tiny toy remake, but the original studio repository, employee authorship, and release authorization have **not** been independently authenticated. It may have been repackaged or modified in fan communities.

### What the upload does *not* prove

- It does not prove the Big Blue Bubble official account uploaded this (the archive's `creator` field is self-reported).
- It does not prove a malicious leak or security breach occurred.
- It does not prove the source was publicly available on GitHub in 2020; a commit's timestamp is not the date it was publicly released.
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
