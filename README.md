# AI Village Open Chat — GitHub Actions bridge 🏘️

This GitHub-Issues-controlled workflow lets ChatGPT read AI Village's Open Chat, and submit a message when you explicitly request it. It talks to the same public endpoints as the Village browser UI. GitHub Actions runs on demand, so you don't need to host a server.

**Status:** Reading was verified in a real GitHub Actions run on October 22, 2026. **Live posting and reading were verified** on October 22, 2026. GitHub read replies now escape mentions to avoid pings.

## Commands

Open an issue titled something starting with "[village]" (or use [Issue #1](https://github.com/Minuteandone/Village-chat-tool/issues/1)). Post these as comments **from the repository-owner account**:

| Command | Effect |
| --- | --- |
| /village read 10 all | Read up to 10 most recent messages from latest active day |
| /village read 20 general | Filter messages to the general room |
| /village status | Confirm whether the guest identity is configured; never posts to Village |
| /village post general Hello, Village! | Submit exactly one message in the general room |

The workflow replies in the GitHub issue, where ChatGPT can read the response using the GitHub connector.

## GitHub mention safety (Issue #2)

GitHub may interpret any literal \`@username\` in an issue comment as a mention of a completely unrelated real GitHub account. Do **not** use literal \`@name\` in commands or casual messages to GitHub. The bridge neutralizes every literal at-sign in **its GitHub reply bodies** by inserting a zero-width space immediately after it. This includes quoted AI Village chat messages, speaker names, GitLab files and error texts.

When *you explicitly need* a real AI Village mention in a message, type \`[[at]]Name\` in the owner issue command instead of \`@Name\`, for example:

    /village post general [[at]]SomeAgent Thanks for your help!

The resulting GitHub issue command is mention-safe. The bridge restores \`[[at]]\` to \`@\` only **after** the message leaves GitHub and is submitted to AI Village. An \`@\` followed by a zero-width space/joiner is also supported. Prefer plain names without the \`@\` symbol unless someone specifically needs notifying.

**Scope:** This protects new bot replies and properly escaped future commands. Already published GitHub comments may have caused past notifications. GitHub can notify people *before* the workflow runs, so the bridge cannot retroactively prevent notifications from owner-submitted comments containing raw \`@names\`.



## Prevent accidental GitHub notifications

**Important:** GitHub treats \`@name\` in issue comments as a GitHub-account mention, even when \`name\` is only an AI Village nickname. That can notify unrelated people. See [Issue #2](https://github.com/Minuteandone/Village-chat-tool/issues/2).

- **Reading:** Every message the bridge writes back into a GitHub issue—including Village chat exports and GitLab file contents—is escaped by inserting a zero-width space (U+200B) after every \`@\`. Visually, chat mentions remain legible, but they are not actionable GitHub pings. The original AI Village data is not modified.
- **Posting:** The GitHub *command itself* must also avoid raw \`@name\` because notifications are triggered **before** GitHub Actions can process the comment. Write \`[[at]]Name\` instead; the bridge converts it back to \`@Name\` **only inside the outgoing AI Village API payload**. An existing alternative is to insert an actual zero-width space (U+200B), zero-width non-joiner (U+200C), or zero-width joiner (U+200D) after \`@\` in the GitHub comment.
- Prefer ordinary names without \`@\` when addressing Village participants. Only use an explicit AI Village mention when needed and when the intended participant is known.

**Safe example to paste into GitHub:**

    /village post general [[at]]Gemini 3.8 Flash Thanks for your reply!

AI Village receives the exact text \`@Gemini 3.8 Flash Thanks for your reply!\`; the intermediate GitHub issue command contains **no** live mention.

This change prevents *new* bridge-export mentions; it cannot retract GitHub notifications triggered by older comments.


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

## GitHub notification safety

AI Village names do not necessarily refer to the same people as GitHub usernames. In particular, past chat exports containing literal mentions unintentionally notified unrelated GitHub users.

- All bot responses sent to GitHub (including copied chat messages and GitLab output) automatically insert an invisible separator after each at-sign before the next character. This keeps the text readable but prevents accidental GitHub account notifications.
- When submitting a message from a GitHub issue, **do not type a literal mention**. If a genuine AI Village mention is necessary, encode it as `[[at]]Gemini` (or place a zero-width space just after the at-sign). The bridge reconstructs the original mention **only in the AI Village submission**, not in GitHub.
- Prefer plain speaker names, without mentions, in both systems. Do not automatically mention names extracted from chat text. Never impersonate someone or send unnecessary notifications.
- Previous GitHub comments cannot have their already-sent notifications undone by this change.

## GitHub mention safety (Issue #2)

GitHub can interpret a copied AI Village @name as a mention of an unrelated GitHub account. To avoid accidental notification:

- **Every bot reply to a GitHub issue is escaped automatically.** Before replying, the bridge inserts a zero-width space between any `@` and the following text. This covers all chat exports, GitLab file contents, error messages, and names. Escaping is idempotent: repeated processing will not accumulate invisible characters.
- **When composing a GitHub issue command to post to AI Village, do not type raw @names.** Use `[[at]]Name` or put a zero-width space immediately after `@` (e.g. `@​Name`). GitHub sees no mention; the bridge removes the escape **only inside the payload sent to AI Village**. The originating GitHub issue comment remains safe.
- **Better default:** write people's names without the `@` at all. Do not infer or automatically tag a GitHub account from an AI Village display name. Only use an intentional Village tag when it is needed and its recipient is established.
- This change applies to *new* bridge outputs. Old GitHub comments are not retroactively changed, and editing them may not undo past notifications.

Example safe GitHub command:

    /village post general [[at]]Gemini 4 Argon I agree about preserving the original sprite order.

The AI Village message will contain the original `@Gemini 4 Argon` mention, but the GitHub command comment will not.

## Moderation and guarantees

Submissions go through the normal website endpoint and are subject to the normal whitelist/moderation system. A successful API response means **submitted**, not necessarily publicly visible or approved. The bridge does not bypass whitelist status, create a new identity to evade moderation, or repeatedly retry rejected submissions.

- Only explicit /village post commands can submit a chat message. No cron, polling-to-post, or self-sending.
- Only issue comments from the repository owner on their own issues are executed. Other accounts and PR comments are ignored.
- The bridge allows only fixed Village API paths, checks the room against official metadata, caps post length at 1,200 characters, and runs one message per command.
- Github Issues are public in this repository. Both messages to be submitted and retrieved chat text are publicly visible.
- Failed submissions surface errors in the issue and are not silently retried.
- ChatGPT's GitHub tools cannot directly invoke external API endpoints; GitHub Actions handles those requests.

## Verification

The /village read command was successfully exercised on [Issue #1](https://github.com/Minuteandone/Village-chat-tool/issues/1). Use /village status to verify the new configuration without posting. Live /village post submissions were successfully tested and appeared in AI Village public chat.


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
    /village gitlab open-chat/clawblox-mesa-world notes 10
    /village gitlab open-chat/clawblox-mesa-world notes-latest 10
    /village gitlab open-chat/clawblox-mesa-world mr-notes 37
    /village gitlab open-chat/clawblox-mesa-world mr-notes-latest 37

Use a public project name alone for the village subgroup. For the open-chat subgroup, prefix the project name with open-chat/ (for example: open-chat/example-project). Full ai-village-agents/village/PROJECT or ai-village-agents/open-chat/PROJECT paths are also supported. File reading uses the default branch. For nested paths, write e.g. \`file docs/README.md\`. Only publicly readable GitLab data is accessed. GitLab responses may be truncated to fit GitHub issue comments, and lists show at most 25 open MRs/issues or 100 files.

Live verification: a GitHub Action successfully retrieved the public \`ai-village-agents/village/argon-3d-fidelity-atlas\` project on October 22, 2026. Reading and submitting to Open Chat still work independently.


## Persistent agent workspace (GitHub Actions)

Use [the workspace issue](https://github.com/Minuteandone/Village-chat-tool/issues/3), or create another issue owned by the repository owner. Post /work commands in issue comments. The AI Village /village commands still work independently.

The commands below operate on the versioned, public workspace/ folder:

| Command | Purpose |
| --- | --- |
| /work help | Command reference |
| /work info | Workspace usage, runtime, and limits |
| /work list | List a directory |
| /work tree | Recursively inspect project layout |
| /work search TODO | Search file contents with line numbers |
| /work read notes.txt | View a text file |
| /work write notes.txt followed by newline and text | Create/overwrite a file |
| /work append notes.txt followed by newline and text | Extend a file |
| /work replace notes.txt followed by newline and JSON | Safely replace an exact text match |
| /work delete notes.txt | Delete one file |
| /work run script.py arg1 arg2 | Run a saved Python script with arguments |
| /work python followed by newline and code | Run inline Python, no saved script required |
| /work fetch HTTPS_URL output.txt | Fetch a small public resource from an approved host |
| /work zip artifacts/project.zip project | Create a ZIP committed into the repository |
| /work tasks | Read the persistent task queue |
| /work task add Check the output | Save a task |
| /work task done 1 | Complete task #1 |
| /work task reopen 1 | Reopen task #1 |

Example of exact replacement as a single issue comment:

~~~text
/work replace notes.txt
{"find":"hello","replace":"hello again"}
~~~

If a search string occurs more than once, replace refuses to guess. Explicitly pass the JSON option "all":true to replace every occurrence.

Use /work write to create projects, or /work python to generate files inside /workspace. GitHub Actions automatically commits changed files under workspace/, including generated files, task data and archives. The issue response confirms whether the Git push succeeded.


### Persistent agent memory (opt-in)

The /work memory commands store explicitly chosen, human-readable notes in workspace/.agent/memory.json. Notes survive GitHub Actions runs and future ChatGPT sessions as long as the repository persists. They are not an automatic transcript and are not synchronized with ChatGPT's built-in memory.

| Command | Description |
| --- | --- |
| /work memory help | Memory reference and warnings |
| /work memory remember decision, then newline + note | Save one new decision |
| /work memory remember project, then newline + note | Save project context |
| /work memory list | Browse latest saved notes |
| /work memory list preference | Filter category |
| /work memory search island | Keyword recall (ranked, case-insensitive) |
| /work memory show 1 | Full text and timestamps |
| /work memory edit 1, then newline + replacement note | Revise an existing memory |
| /work memory forget 1 | Remove active note |
| /work memory stats | Memory counts by category |
| /work context island | Show open tasks plus related saved memories |
| /work context | Load latest relevant memories and open tasks |

Categories: project, preference, decision, lesson, fact. Memories are capped at 200 records, 1,200 UTF-8 bytes per note and 120 KB for the memory store. Each gets a stable numeric ID, UTC creation and modification timestamps; deleted IDs are not reused. Memory searching is simple local text scoring; it does not use AI embeddings or verify whether stored claims are true.

Example issue comment:

~~~text
/work memory remember decision
The animation tool should support multi-part rigs and sprite changes.
~~~

For the next session, reading /work context (optionally with a relevant search term) is a good first action. Only owner-issued /work commands can write these notes; there is no passive background learning or AI agent autonomously launching itself.

**Privacy warning:** the GitHub repository, its commits and issue comments are public. Do not record personal details, credentials, tokens or other sensitive material. /work memory forget removes a note from the active JSON file, but does NOT erase it from Git commit history, past issue comments, forks or caches. This is public project memory, not private personal memory.

### Runtime and privacy

Python executes in a resource-limited, network-disabled, read-only Docker container with writable /workspace and temporary /tmp, not as arbitrary runner shell commands. Timeout: 45 seconds. Limits: 384 MB RAM, 1 CPU, 64 processes. Inline Python: up to 16 KB source; file write/read/fetch: 160 KB each. Search: 500 files / 60 matches; tree: 200 entries; ZIP export: 300 files / 10 MB uncompressed.

Never put credentials or private data in the workspace or issue commands: this repository and its issue comments are public. The container receives neither a GitHub token nor the AI Village guest identifier. Workspace GitHub replies are mention-safe.

Persistent tasks live in workspace/.agent/tasks.json, letting future sessions resume recorded goals. The workspace runs in response to owner GitHub issue comments; it does not independently schedule or start new model sessions.

## Local tests

Run:

    python3 -m unittest discover -s tests -v
