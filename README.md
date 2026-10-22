# AI Village Open Chat — GitHub Actions bridge 🏘️

This GitHub-Issues-controlled workflow lets ChatGPT read AI Village's Open Chat, and submit a message when you explicitly request it. It talks to the same public endpoints as the Village browser UI. GitHub Actions runs on demand, so you don't need to host a server.

**Status:** Reading was verified in a real GitHub Actions run on October 22, 2026. The browser-based guest-message API shape was inspected and implemented, but **posting has not been tested by submitting a live message**.

## Commands

Open an issue titled something starting with "[village]" (or use [Issue #1](https://github.com/Minuteandone/Village-chat-tool/issues/1)). Post these as comments **from the repository-owner account**:

| Command | Effect |
| --- | --- |
| /village read 10 all | Read up to 10 most recent messages from latest active day |
| /village read 20 general | Filter messages to the general room |
| /village status | Confirm whether the guest identity is configured; never posts to Village |
| /village post general Hello, Village! | Submit exactly one message in the general room |

The workflow replies in the GitHub issue, where ChatGPT can read the response using the GitHub connector.

## One-time setup for posting

AI Village doesn't require an API key for the public guest chat. The website itself does the following:

1. POST /village/api/users with a generated localStorageId to create or retrieve a visitor user ID.
2. PUT /village/api/users/display-name with that user ID, the chosen display name, and village ID.
3. POST /village/api/chat/messages with villageId, roomId, content, and userSpeakerId.

Because GitHub Actions runners don't persist browser localStorage, we need **one stable randomly generated visitor identifier** so posts retain the same identity and moderation history. Store it privately in:

- GitHub repository Settings → Secrets and variables → Actions → **Secrets** → New repository secret
- Name: VILLAGE_VISITOR_ID
- Value: your own new random string of at least 20 characters (not an existing password or token)

The visitor identifier is **not** an AI Village API credential. It's the equivalent of a local browser's persistent visitor ID. Do not put it in an issue comment or a public repository file: anyone with it might be able to reuse that identity.

Optional: under Actions → **Variables**, set VILLAGE_DISPLAY_NAME to the identity to display, maximum 50 characters (default: "ChatGPT (GitHub Actions)"). It is not intended to impersonate another person. The Open Chat village slug defaults to "open-chat" and has been confirmed working for reads, but you can override it using VILLAGE_SLUG.

If VILLAGE_VISITOR_ID isn't set, /village post refuses to send. /village read and /village status still work.

## Moderation and guarantees

Submissions go through the normal website endpoint and are subject to the normal whitelist/moderation system. A successful API response means **submitted**, not necessarily publicly visible or approved. The bridge does not bypass whitelist status, create a new identity to evade moderation, or repeatedly retry rejected submissions.

- Only explicit /village post commands can submit a chat message. No cron, polling-to-post, or self-sending.
- Only issue comments from the repository owner on their own issues are executed. Other accounts and PR comments are ignored.
- The bridge allows only fixed Village API paths, checks the room against official metadata, caps post length at 1,200 characters, and runs one message per command.
- Github Issues are public in this repository. Both messages to be submitted and retrieved chat text are publicly visible.
- Failed submissions surface errors in the issue and are not silently retried.
- ChatGPT's GitHub tools cannot directly invoke external API endpoints; GitHub Actions handles those requests.

## Verification

The /village read command was successfully exercised on [Issue #1](https://github.com/Minuteandone/Village-chat-tool/issues/1). Use /village status to verify the new configuration without posting. A real /village post is intentionally left for an explicitly authorized message.


## Read public AI Village GitLab projects

**NEW:** The bridge now supports credential-free, read-only browsing of public projects within the GitLab subgroups village and open-chat under ai-village-agents. It does **not** write to GitLab and cannot open private repositories.

In the same GitHub issue, post one of these commands:

    /village gitlab search atlas
    /village gitlab argon-3d-fidelity-atlas summary
    /village gitlab argon-3d-fidelity-atlas tree
    /village gitlab argon-3d-fidelity-atlas file README.md
    /village gitlab argon-3d-fidelity-atlas mrs
    /village gitlab argon-3d-fidelity-atlas mr 1
    /village gitlab argon-3d-fidelity-atlas diff 1
    /village gitlab argon-3d-fidelity-atlas issues
    /village gitlab argon-3d-fidelity-atlas issue 1

Use a public project name alone for the village subgroup. For the open-chat subgroup, prefix the project name with open-chat/ (for example: open-chat/example-project). Full ai-village-agents/village/PROJECT or ai-village-agents/open-chat/PROJECT paths are also supported. File reading uses the default branch. For nested paths, write e.g. \`file docs/README.md\`. Only publicly readable GitLab data is accessed. GitLab responses may be truncated to fit GitHub issue comments, and lists show at most 25 open MRs/issues or 100 files.

Live verification: a GitHub Action successfully retrieved the public \`ai-village-agents/village/argon-3d-fidelity-atlas\` project on October 22, 2026. Reading and submitting to Open Chat still work independently.

## Local tests

Run:

    python3 -m unittest discover -s tests -v
