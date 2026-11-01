# AI Village topic sorter 🗂️

This tool sorts **individual files**, not entire repositories, from the combined
public GitLab snapshot. The intentionally omitted `argon-3d-fidelity-atlas`
repo stays omitted because it is not present in the input snapshot.

## Input and output

Run `python3 tools/sort_village_files_by_topic.py --input all-projects.zip --output output/topics`.

Outputs:

- `categories/<topic>.zip`: one archive per discovered primary topic, with the
  original `repositories/<namespace>/<repo>/<path>` structure preserved.
- `FILE_INDEX.csv`: searchable filename/path, repo, primary topic, secondary
  topics, file size, confidence score, and whether a text sample was used.
- `TOPIC_REPORT.json`: counts, source-file byte totals, category sizes and sample files.

The corresponding GitHub Actions workflow uploads **each category ZIP as a
separate artifact** and publishes the index/report as another artifact.

## How classification works

The classifier makes one primary assignment per file. It weighs:

1. Repository name, not generic `ai-village-agents` namespace text.
2. Filename and relative path.
3. File extension (strong for music, movies, images, 3D and datasets).
4. A small, decoded text excerpt from readable files (at most 8192 bytes).

Topic names are interpretable labels such as music/audio, games/simulations,
agents, economics, research, history, creative writing, developer tools and
documents. The topics with at least one matching file automatically produce ZIPs.

**Limitations:** This is hybrid lexical, topic-aware filtering rather than
neural embeddings or whole-document LLM analysis. It cannot reliably understand
all code or multimedia semantics; files without clear cues go in miscellaneous.
Scores are ranking signals, **not probabilities**. The CSV includes additional
topic hints for searching and possible manual reclassification. Readable content
sampling is capped to keep the job practical for enormous archives.

No words or project topics are used as exclusion criteria: every readable
archived file is placed in exactly one category, and errors stop the job.

This is a default-branch snapshot, not a mirror of all Git history or binary
Git LFS content.
