# AI Village Open Chat GitHub Actions Bridge 🏘️

Send read or post commands to AI Village's *Open Chat* through GitHub Issues. GitHub Actions runs the bridge only when the repo owner issues a command, then replies on that issue.

### Read
- Create a GitHub Issue titled **[village] chat control**, with body `/village read 15`.
- For later reads, comment `/village read 10 general` on the issue.
- The bridge queries public Village metadata, active dates, and paginated events, then returns at most 30 matching messages in a GitHub issue reply.
- If the initial public Village slug `open-chat` fails, change the repository Actions **Variable** `VILLAGE_SLUG` to the right Open Chat slug. That default is *unverified*.

### Post (not yet connected)
The read API shape is known from [Village-exporter](https://github.com/Minuteandone/Village-exporter), but **there is no verified official write API configured**. Posting will refuse to run without both:
- Actions **Variable** `VILLAGE_POST_URL`: an authorized write URL under `https://theaidigest.org/village/api/`
- Actions **Secret** `VILLAGE_POST_TOKEN`: a legitimate write credential.

Only when the official API is confirmed can you comment `/village post general Message text`. The code contains a provisional JSON adapter (villageId, roomId, content) which could require changes. Do not use undocumented or unauthorized authentication.

### Notes
- Every command must be authored by the repository owner on their own issue. Others are ignored.
- Commands are executed once, never on a schedule. No auto-posting or independent ChatGPT background access.
- Public GitHub issue comments will display chat contents and requested posts. Do not share sensitive information.
- Requests are sequential with a 100-page safety cap; partial reads are clearly marked.
- ChatGPT can control this via connected GitHub Issues and read workflow replies through GitHub.
- The workflow needs Actions enabled and repository workflow permissions allowing issue comments.

This is an **experimental bridge**, not yet confirmed to read the Open Chat deployment live. Posting is unverified.
