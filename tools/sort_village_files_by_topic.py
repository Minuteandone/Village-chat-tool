#!/usr/bin/env python3
"""Content-aware, per-file topical classifier and ZIP sorter for AI Village.

Input: already combined GitLab archive from the 2741-project GitHub artifact.
Output: one ZIP per discovered topic, a global CSV index, and a JSON report.

Classification is an interpretable local *semantic keyword/topic* classifier:
topic synonyms and phrases, repo and file paths, extensions, and the first 8 KiB
of readable content. This is not a neural embedding model. Each file is placed
in exactly one primary ZIP, and possible secondary topics go in the index.
No files are discarded because of the words they contain.
"""
import argparse
import collections
import contextlib
import csv
import datetime
import json
import re
import shutil
import zipfile
from pathlib import Path

CATEGORIES = {
    "ai-agents": {
        "title": "AI Agents and Autonomous Systems",
        "terms": "agent agents agentic autonomous autonomy swarm swarms village chatbot chatbots assistant assistants orchestration multiagent multi-agent llm large language model prompt prompting deliberation planning memory memories coordination delegate delegation tool calling model context protocol claude gemini gpt grok deepseek",
    },
    "machine-learning": {
        "title": "Machine Learning and Neural Networks",
        "terms": "machine learning neural network training trained inference diffusion transformer token tokenizer embeddings embedding dataset fine tuning finetune pytorch tensorflow keras classifier regression checkpoint gradient optimizer weights lora autoencoder reinforcement learning loss function architecture model evaluation",
    },
    "games-simulations": {
        "title": "Games RPGs and Simulations",
        "terms": "game games gameplay gamejam game-jam jam videogame minigame level player players boss quest quests rpg dungeon combat inventory minecraft pokemon pikmin sandbox simulation simulator sprite sprites unity godot scratch character enemy monsters monster turn based puzzle adventure racing",
    },
    "web-apps": {
        "title": "Websites and Frontend Apps",
        "terms": "website websites webpage html css frontend front-end tailwind react nextjs next.js vue svelte typescript javascript browser ui ux dashboard app landing page webapp web app vite layout component responsive spa pwa",
    },
    "messaging-collaboration": {
        "title": "Chats Messaging and Collaborative Tools",
        "terms": "chat chats chatter messaging messenger messages forum community conversation discussions channels comments replies social collaboration collaborate coordination group discussion moderation votes voting poll polls",
    },
    "economics-markets": {
        "title": "Economics Markets and Business",
        "terms": "business market markets economics economy economic forecasting predictions prediction finance financial stocks trading trade asset valuation price pricing revenue profit earning cash money currency mana marketplace manifold venture startup budget funding auction commerce sales merchants stock ticker forecast",
    },
    "science-research": {
        "title": "Science Research and Experiments",
        "terms": "science scientific research study studies experiment experiments laboratory lab investigation evidence hypothesis peer reviewed findings result methodology methodology biology physics chemistry medicine medical healthcare health anatomy astronomy statistics statistical computational simulation archaeology ecology survey survey analysis interpretability",
    },
    "history-archives": {
        "title": "History Archives and Primary Sources",
        "terms": "history historical archive archival archives preservation timeline centuries century year treaty treaties document transcript record records historical census reservation indian school indigenous rosa parks pamphlet antebellum historic biography genealogy 1800 1900 1960 constitution rights jurisprudence",
    },
    "education-learning": {
        "title": "Education Teaching and Learning",
        "terms": "education educational learn learning teach teacher teaching class classroom curriculum lesson lessons tutorial guide guides student school schools course courses homework assignments quiz questions textbook workshop study flashcards knowledge",
    },
    "creative-writing": {
        "title": "Stories Literature Poetry and Scripts",
        "terms": "story stories fiction fictional narrative storytelling book novel poetry poem poems haiku prose screenplay screenplay script dialogue character chapters writing writers anthology fable mythology lore fairy tale fanfic literary theater scene act protagonist",
    },
    "music-audio": {
        "title": "Music Sounds and Audio Production",
        "terms": "music musical song songs audio melody midi beat beats soundtrack soundtracks synth synthesis synthesizer samples sample piano notes chord chords drum drums percussion bass vocal vocals singing voice harmony wav mp3 flac ogg soundfont",
    },
    "visual-art-3d": {
        "title": "Images Art Graphics and 3D",
        "terms": "image images picture pictures photo photography art artwork illustration illustrated drawing paintings pixel sprite graphic graphics animation design textures texture 3d 3-d three dimensional mesh meshes obj glb gltf blender render rendering model models shader shaders svg png jpeg",
    },
    "video-animation": {
        "title": "Videos Filmmaking and Animation",
        "terms": "video videos movie movies film filmmaking animation animated frames frame footage cinematic trailer streaming mp4 webm mkv ffmpeg blender scene clip clips storyboard",
    },
    "data-datasets": {
        "title": "Datasets Records Tables and Analysis",
        "terms": "data dataset datasets table tables csv tsv parquet spreadsheet excel xlsx sql query queries database databases records statistics analytics pandas dataframe visualization chart charts scrape scraper scraping metrics measurements benchmarks jsonl ndjson api results export",
    },
    "developer-tools": {
        "title": "Software Libraries Utilities and Automation",
        "terms": "tool tools utility utilities library libraries package pip npm cli command script scripting scripts automation automated bot developer development sdk api github gitlab git workflow deployment docker server endpoint service services build pipeline integration plugin plugins function functions shell bash python rust node",
    },
    "testing-prototypes": {
        "title": "Tests Prototypes and Debugging",
        "terms": "test testing tests pytest unittest spec specs debug debugging issue fix bug bugs benchmark benchmarking prototype prototypes proof of concept poc scratchpad demo demos mocks fixture fixtures mock experiment validation verification",
    },
    "documents-reference": {
        "title": "Documents Notes and Reference",
        "terms": "readme docs documentation document documents notes note memo manual instructions faq reference references paper papers pdf plaintext text markdown license changelog todo specification specifications overview summary plan planning report reports",
    },
    "miscellaneous": {
        "title": "Miscellaneous and Unclassified Files",
        "terms": "",
    },
}

EXT_GROUPS = {
    "music-audio": set(".mp3 .wav .flac .ogg .m4a .aiff .aif .mid .midi .sf2 .sfz .opus .mod .xm".split()),
    "video-animation": set(".mp4 .mkv .avi .mov .webm .mpeg .mpg .gifv".split()),
    "visual-art-3d": set(".png .jpg .jpeg .webp .gif .bmp .ico .tif .tiff .svg .psd .aseprite .blend .obj .fbx .gltf .glb .stl .mtl .hdr .exr .ktx".split()),
    "data-datasets": set(".csv .tsv .parquet .feather .arrow .jsonl .ndjson .sqlite .sqlite3 .db .xlsx .ods .ipynb".split()),
}
TEXT_EXT = set(".txt .md .mdx .rst .adoc .html .htm .css .scss .js .jsx .ts .tsx .py .rb .lua .rs .go .java .kt .swift .cs .c .cpp .h .hpp .php .sh .bash .json .jsonc .yml .yaml .toml .xml .ini .cfg .conf .sql .csv .tsv .tex .log .srt .vtt .gitignore .ipynb .svg .bat .ps1 .gradle".split())
COMMON = set("a an and are as at be by can do for from has have if in into is it its of on or our out per re so than that the their these this to was were what when where which who with you your using used via how make makes built build new we i no not".split())
TOKEN_RE = re.compile(r"[a-z][a-z0-9]{1,30}")
CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
TOPIC_WORDS = {}
for category, detail in CATEGORIES.items():
    words = TOKEN_RE.findall(detail["terms"])
    TOPIC_WORDS[category] = set(x for x in words if x not in COMMON)

def tokens(value):
    value = CAMEL.sub(" ", str(value))
    return [x for x in TOKEN_RE.findall(value.lower()) if x not in COMMON]

def source_paths(name):
    # Repo paths have ai-village-agents/<scope>/..., then filename.
    parts = name.split("/")
    if len(parts) < 5 or parts[0] != "repositories" or parts[1] != "ai-village-agents":
        return None
    after = parts[2:]
    # Some GitLab projects are nested more deeply than the usual scope/repo.
    # Identify the repo from the manifest, not a fixed path length.
    return after

def get_text_sample(archive, info):
    suffix = Path(info.filename).suffix.lower()
    basename = Path(info.filename).name.lower()
    if info.file_size == 0 or info.is_dir():
        return ""
    if suffix not in TEXT_EXT and basename not in ("dockerfile", "makefile", "license", "readme"):
        return ""
    try:
        with archive.open(info) as handle:
            chunk = handle.read(8192)
        if b"\x00" in chunk[:1024]:
            return ""
        return chunk.decode("utf-8", "replace").lower()
    except (UnicodeError, ValueError, RuntimeError, OSError):
        return ""

def classify(repo, relative, info, sample):
    fname = Path(relative).name
    stem = Path(relative).stem
    suffix = Path(relative).suffix.lower()
    repo_words = set(tokens(repo))
    path_words = set(tokens(relative))
    file_words = set(tokens(stem))
    # Head only: reading the beginning lets large files be sorted safely.
    text_words = set(tokens(sample[:8192]))
    scores = collections.defaultdict(float)
    for cat, dictionary in TOPIC_WORDS.items():
        if cat == "miscellaneous":
            continue
        scores[cat] = (
            3.0 * len(repo_words & dictionary)
            + 2.0 * len(path_words & dictionary)
            + 2.8 * len(file_words & dictionary)
            + 0.22 * min(22, len(text_words & dictionary))
        )
    # File types are strongest for recognizable media/binary assets.
    for cat, extensions in EXT_GROUPS.items():
        if suffix in extensions:
            scores[cat] += 40
    if suffix in (".md", ".rst", ".adoc", ".pdf", ".txt"):
        scores["documents-reference"] += 3
    if fname.lower().startswith(("readme", "license", "contributing", "changelog")):
        scores["documents-reference"] += 18
    if suffix in (".py", ".js", ".ts", ".sh", ".rs", ".go", ".rb", ".lua"):
        scores["developer-tools"] += 1
    if suffix in (".jsonl", ".csv", ".parquet"):
        scores["data-datasets"] += 10
    if re.search(r"(^|/)(tests?|__tests__|specs?|fixtures?)(/|$)", relative.lower()):
        scores["testing-prototypes"] += 24
    if re.search(r"(^|/)(node_modules|vendor|dist|build|__pycache__)(/|$)", relative.lower()):
        scores["developer-tools"] += 6
    # Prevent generic words like "model" or "library" from deciding a file alone:
    # require an affirmative score threshold and keep uncertain items separate.
    sorted_scores = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    top, points = sorted_scores[0]
    if points < 3:
        top = "miscellaneous"
    secondary = [k for k, v in sorted_scores if k != top and v >= max(4, points * 0.65)][:3]
    return top, round(points, 2), secondary

def parse_repo_path(member_name, known_repos):
    # Match longest known repo prefix to support subgroup/repo nesting.
    if not member_name.startswith("repositories/"):
        return None
    relative = member_name[len("repositories/"):]
    for ancestor in range(len(relative.split("/")) - 1, 1, -1):
        parts = relative.split("/")
        candidate = "/".join(parts[:ancestor])
        if candidate in known_repos:
            inner_path = "/".join(parts[ancestor:])
            if inner_path:
                return candidate, inner_path
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-files", type=int, default=0, help="For smoke tests only; 0=all")
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    category_dir = a.output / "categories"
    category_dir.mkdir(parents=True, exist_ok=True)
    index_path = a.output / "FILE_INDEX.csv"
    report_path = a.output / "TOPIC_REPORT.json"
    counts = collections.Counter()
    bytes_per_cat = collections.Counter()
    repos_per_cat = collections.defaultdict(set)
    examples = collections.defaultdict(list)
    errors = []
    categories = {}
    total, analyzed_samples, accounted = 0, 0, 0
    with zipfile.ZipFile(a.input, "r", allowZip64=True) as source:
        manifest = json.loads(source.read("COMBINED_MANIFEST.json"))
        names = {row["name"] for row in manifest["projects"]}
        with contextlib.ExitStack() as stack:
            for category in CATEGORIES:
                dest = category_dir / (category + ".zip")
                categories[category] = stack.enter_context(
                    zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED,
                                    compresslevel=1, allowZip64=True)
                )
            with index_path.open("w", encoding="utf-8", newline="") as out:
                csvw = csv.writer(out)
                csvw.writerow(("topic", "repository", "repository_relative_path", "original_archive_path",
                               "bytes", "confidence_score", "also_related_to", "text_preview_used"))
                for info in source.infolist():
                    if info.is_dir() or not info.filename.startswith("repositories/"):
                        continue
                    found = parse_repo_path(info.filename, names)
                    if not found:
                        errors.append({"path": info.filename, "error": "Unmatched repo path"})
                        continue
                    repo, rel = found
                    sample = get_text_sample(source, info)
                    if sample:
                        analyzed_samples += 1
                    category, score, secondary = classify(repo, rel, info, sample)
                    try:
                        with source.open(info) as infile:
                            with categories[category].open(info.filename, "w", force_zip64=True) as outfile:
                                shutil.copyfileobj(infile, outfile, length=1024 * 1024)
                    except Exception as exc:
                        errors.append({"path": info.filename, "error": str(exc)[:200]})
                        continue
                    csvw.writerow((category, repo, rel, info.filename, info.file_size,
                                   score, "|".join(secondary), bool(sample)))
                    counts[category] += 1
                    bytes_per_cat[category] += info.file_size
                    repos_per_cat[category].add(repo)
                    if len(examples[category]) < 7:
                        examples[category].append({"repository": repo, "path": rel})
                    total += 1
                    accounted += info.file_size
                    if total % 2000 == 0:
                        print("Classified", total, "files;", len([x for x in counts.values() if x]), "active categories", flush=True)
                    if a.max_files and total >= a.max_files:
                        break
            for category, dest in categories.items():
                dest.writestr("CATEGORY_README.txt", (
                    f"{CATEGORIES[category]['title']}\n"
                    f"Primary topic ZIP: {category}\n"
                    "Every original file path has been preserved under repositories/.\n"
                    "See the global FILE_INDEX.csv for secondary topics, classification scores and paths.\n"
                    "Sorting is local and heuristic, using names, paths, extensions, and small UTF-8 text samples.\n"
                ))
    # Remove empty category ZIPs; they're not actual discovered topics.
    for category in CATEGORIES:
        if counts[category] == 0:
            (category_dir / (category + ".zip")).unlink()
    report = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": a.input.name,
        "input_project_count": manifest["represented_project_count"],
        "input_archived_project_count": manifest["archived_project_count"],
        "excluded_project": manifest["excluded_project"],
        "total_files_sorted": total,
        "readable_content_samples_used": analyzed_samples,
        "total_original_file_bytes": accounted,
        "sorting": "one primary topic per file, possible secondary topics stored in index",
        "classification_method": "local hybrid weighted lexical topic similarity + repository/file path + file extension + text content sample; not a neural embedding model",
        "sample_limit_bytes": 8192,
        "categories": [
            {"slug": cat, "label": CATEGORIES[cat]["title"],
             "file_count": counts[cat], "original_bytes": bytes_per_cat[cat],
             "repository_count": len(repos_per_cat[cat]),
             "zip_bytes": (category_dir / (cat + ".zip")).stat().st_size,
             "examples": examples[cat]}
            for cat in CATEGORIES if counts[cat] > 0
        ],
        "errors": errors[:500],
        "error_count": len(errors),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("FINAL REPORT", json.dumps(
        {x["slug"]: x["file_count"] for x in report["categories"]}, indent=2), flush=True)
    print("TOTAL", total, "ERRORS", len(errors), "SAMPLED", analyzed_samples, flush=True)
    if errors:
        raise RuntimeError(f"Sorting encountered {len(errors)} failed/unmatched file entries.")
    if a.max_files == 0 and total == 0:
        raise RuntimeError("No source files were sorted")
    if summary := __import__("os").environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## AI Village semantic-style file categorization\n\n")
            handle.write(f"Sorted **{total:,} files** into **{len(report['categories'])} category ZIPs**.\n\n")
            handle.write("| Topic | Files | Repos | ZIP bytes |\n|---|---:|---:|---:|\n")
            for x in report["categories"]:
                handle.write(f"| {x['label']} | {x['file_count']:,} | {x['repository_count']:,} | {x['zip_bytes']:,} |\n")

if __name__ == "__main__":
    main()
