# Follow-up: Original ZIP's Git commit comment and packaging metadata

Source: https://archive.org/details/monster-game-server
Inspected byte-identical ZIP (15,170,251 bytes; SHA-1 df086c9ca4581733f73f2e8aaea1408382232e4d).

## Direct header results

- ZIP-global archive comment length: **0 bytes**. There is no embedded commit hash.
- End-of-central-directory ZIP comment length: **0** (confirmed separately from the ZIP header).
- Individual entry comments: **0** across all 215 entries.
- Root folder: `monster-game-server-266e600f69ed8e462f26416704266d042dd2cf84`.
- Entries: **215** total: **188 regular files** and **27 directory entries**.
- ZIP "system that created" value: **0** (DOS/Windows convention) on all 215 entries. This is a compatibility indicator, not proof of a Windows PC.
- ZIP compression: DEFLATE on 188 regular files, STORE on 27 directory entries.
- No central-directory extra fields and no Unix mode information in the first entry.
- No encrypted entries or UTF-8/data-descriptor flag bits set.
- The timestamps are NOT all identical:
  - All **188 regular files** have ZIP timestamps ranging from **2020-07-03 15:47:56 to 15:48:02** in 2-second increments.
  - All **27 directories** have ZIP timestamps ranging from **2021-05-09 20:25:24 to 20:25:28** in 2-second increments.
- ZIP timestamps are local-time fields, without a reliable timezone.
- The 188 file dates are nearly uniform, but **not an exact single commit timestamp**.
- ZIP member timestamps are not reliable proof of the original author, first release, or repository host.

## What this changes

Git documentation states that `git archive --format=zip <commit>` saves the commit ID as the ZIP file comment. This ZIP lacks that comment. Consequently, this byte-for-byte archived ZIP **does not match the standard signature of a direct native Git commit archive**.

This does NOT rule out a Git-sourced content tree or archives from GitHub, GitLab, Bitbucket or another platform. Those services can use different archive generators, and later unzipping/re-zipping can remove comments while preserving a commit-based directory name.

The striking discrepancy between the **July 2020 file timestamps** and **May 2021 directory timestamps** is consistent with a directory tree being constructed/repackaged after an earlier set of files, though timestamps alone cannot establish the precise packaging sequence. It weakens the previous suggestion that July 3, 2020 was necessarily the original Git commit date, or that this specific file is an untouched downloaded snapshot.

A **plausible** reconstructed chain, not a demonstrated one, is:
earlier project source -> a copy retaining `monster-game-server-<40 hexadecimal characters>` as its top folder -> a subsequently packaged ZIP with mixed member timestamps -> Internet Archive upload October 2023.

## Conclusion and remaining unknowns

Strongly supported: it is a historical software source ZIP, with a commit-shaped top-level folder, no ZIP-level commit identifier, and mixed dates.

Not supported: identification of original GitHub/GitLab server, proof the 40-character folder suffix is a real commit, proof the original studio produced the repository, exact date of first public distribution.

Original metadata also lists only a 2023 upload and the description "lmao"; it does not give a source repo. Public text searches for the full 40-character suffix returned no match.

## Reproducibility

`server_zip_provenance.py` downloads and checksums the public archive then extracts ZIP-level metadata only.
`server-zip-provenance.json` contains the exact machine-readable result.

Git `git archive` documentation: https://git-scm.com/docs/git-archive
GitHub archives documentation: https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives
