#!/usr/bin/env python3
"""Learn AND assign GitLab-file topics with the SAME unsupervised model.

Unlike discover_village_topics.py this script does not train on a sample and
does not assign files using a separate keyword heuristic. EVERY regular file
contributes to incremental MiniBatchKMeans training, and EVERY regular file
is assigned using that fitted model's .predict() result.

A bounded readable-text prefix is inspected for text-like files; binaries are
represented by their names, paths and media types, not decoded binary content.
Training weights reduce the dominance of repositories with enormous file counts.
Topic titles are derived automatically from all classified files' vocabulary.
"""
import argparse
import collections
import contextlib
import csv
import datetime
import heapq
import json
import math
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import AgglomerativeClustering, MiniBatchKMeans
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

TEXT_SUFFIXES = set(".txt .md .mdx .rst .adoc .html .htm .css .scss .js .jsx .ts .tsx .py .rb .lua .rs .go .java .kt .swift .cs .c .cpp .h .hpp .php .sh .bash .json .jsonl .ndjson .yaml .yml .toml .xml .ini .cfg .conf .sql .csv .tsv .tex .log .srt .vtt .svg .ipynb".split())
MEDIA_SUFFIXES = {
    "audio": set(".mp3 .wav .flac .ogg .m4a .mid .midi .sf2 .opus".split()),
    "video": set(".mp4 .mkv .avi .mov .webm .mpeg".split()),
    "image": set(".png .jpg .jpeg .webp .gif .bmp .ico .tiff .psd .aseprite".split()),
    "geometry": set(".blend .obj .fbx .gltf .glb .stl".split()),
    "archive": set(".zip .7z .tar .gz .rar".split()),
    "document": set(".pdf .doc .docx .pptx .xlsx".split()),
}
BORING = set("""the and for with from this that into these here also using have been
github gitlab agents village ai agent source files file project projects repository
repositories data html css javascript code function import def class return true
false null content utf src dist build node modules file directory filetype
text audio image video binary markdown readme index default page pages
path tests testing test tmp example examples script scripts license none
""".split())
WORD = re.compile(r"[a-z][a-z0-9]{2,}", flags=re.I)
TAG = re.compile(r"<[^>]+>")
TITLE = re.compile(r"<(?:title|h1)(?:\s[^>]*)?>(.*?)</(?:title|h1)>", re.I | re.S)
CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
EXCLUDE = "ai-village-agents/village/argon-3d-fidelity-atlas"


def text_tokens(value):
    return [w for w in WORD.findall(CAMEL.sub(" ", value.lower())) if w not in BORING]


def detect_kind(suffix):
    for kind, suffixes in MEDIA_SUFFIXES.items():
        if suffix in suffixes:
            return kind
    return "text" if suffix in TEXT_SUFFIXES else "other"


def locate(name, known):
    if not name.startswith("repositories/") or "\\" in name or ".." in name.split("/"):
        return None
    seg = name[len("repositories/"):].split("/")
    for length in range(min(len(seg)-1, 12), 1, -1):
        candidate = "/".join(seg[:length])
        if candidate in known and len(seg) > length:
            return candidate, "/".join(seg[length:])
    return None


def readable_prefix(archive, info, limit):
    ext = Path(info.filename).suffix.lower()
    if ext not in TEXT_SUFFIXES and Path(info.filename).name.lower() not in ("dockerfile", "makefile", "license", "readme"):
        return ""
    try:
        with archive.open(info) as stream:
            raw = stream.read(limit)
        if b"\x00" in raw[:512]:
            return ""
        rawtext = raw.decode("utf-8", errors="replace")
        if ext in (".html", ".htm"):
            headings = TITLE.findall(rawtext)
            if headings:
                return " ".join(TAG.sub(" ", h) for h in headings)[:1400]
            return TAG.sub(" ", re.sub(r"(?is)<(?:script|style)[^>]*>.*?</(?:script|style)>", "", rawtext))[:1400]
        if ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".lua", ".rs", ".go", ".java", ".cpp", ".c"):
            lines = rawtext.splitlines()[:50]
            return " ".join(line for line in lines if line.lstrip().startswith(("#", "//", "* ", "/*", '"""', "'''")))[:1400]
        return rawtext[:2000]
    except (OSError, RuntimeError, ValueError):
        return ""


def features(repo, relative, archive, info, text_limit):
    """Every file contributes to the model; no training-time sampling."""
    path = Path(relative)
    title = repo.rsplit("/", 1)[-1]
    kind = detect_kind(path.suffix.lower())
    prefix = readable_prefix(archive, info, text_limit)
    # Stop-words and capped text suppress boilerplate and pathological payloads.
    repo_text = " ".join(text_tokens(title))[:160]
    file_text = " ".join(text_tokens(path.stem))[:200]
    folder_text = " ".join(text_tokens(" ".join(path.parts[:-1][-5:])))[:250]
    content_text = " ".join(text_tokens(prefix)[:90])
    doc = " ".join([repo_text] * 4 + [file_text] * 3 + [folder_text] * 2
                   + ["mediatype" + kind, "extension" + (path.suffix.lower().lstrip(".") or "none")]
                   + [content_text])
    return doc, (repo_text + " " + file_text + " " + folder_text), kind, bool(prefix)


def inventory(archive, manifest):
    known = {p["name"] for p in manifest["projects"]}
    by_repo = collections.defaultdict(list)
    positions = archive.infolist()
    skipped = []
    for i, info in enumerate(positions):
        if info.is_dir():
            continue
        if not info.filename.startswith("repositories/"):
            continue
        match = locate(info.filename, known)
        if match is None:
            skipped.append(info.filename)
            continue
        repo, _ = match
        if repo == EXCLUDE:
            raise ValueError("Deliberately excluded Atlas repository was found in archive")
        by_repo[repo].append(i)
    if skipped:
        raise RuntimeError(f"{len(skipped)} unmatched repository file paths: {skipped[:3]}")
    total = sum(len(v) for v in by_repo.values())
    print("INVENTORY", total, "files in", len(by_repo), "nonempty repositories", flush=True)
    return positions, by_repo, total, known


def interleaved_training_indices(by_repo):
    """Round robin by completion fraction, retaining every file exactly once."""
    heap = []
    for repo, indices in by_repo.items():
        heap.append((0.0, repo, 0))
    heapq.heapify(heap)
    while heap:
        _, repo, ordinal = heapq.heappop(heap)
        indices = by_repo[repo]
        yield indices[ordinal], repo
        ordinal += 1
        if ordinal < len(indices):
            heapq.heappush(heap, (ordinal / len(indices), repo, ordinal))


def fit_every_file(archive, positions, by_repo, text_limit, clusters, batch_size):
    vectorizer = HashingVectorizer(
        n_features=32768, alternate_sign=False, norm="l2", lowercase=True,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-z][a-z0-9]{2,}\b",
    )
    model = MiniBatchKMeans(
        n_clusters=clusters, batch_size=batch_size,
        random_state=43, n_init=1, max_no_improvement=25,
        reassignment_ratio=0.005,
    )
    docs, weights = [], []
    seen = 0
    expected = sum(map(len, by_repo.values()))
    for idx, repo in interleaved_training_indices(by_repo):
        info = positions[idx]
        rel = info.filename[len("repositories/" + repo + "/"):]
        doc, _, _, _ = features(repo, rel, archive, info, text_limit)
        docs.append(doc)
        # Huge generated sites still contribute EVERY file, but their total
        # weight no longer dwarfs dozens of independent repositories.
        weights.append(min(3.0, max(0.05, 20.0 / math.sqrt(len(by_repo[repo])))))
        if len(docs) >= batch_size:
            vectors = vectorizer.transform(docs)
            model.partial_fit(vectors, sample_weight=np.asarray(weights))
            seen += len(docs)
            docs.clear()
            weights.clear()
            if seen % 50000 < batch_size:
                print("TRAINED on", seen, "/", expected, "files", flush=True)
    if docs:
        model.partial_fit(vectorizer.transform(docs), sample_weight=np.asarray(weights))
        seen += len(docs)
    assert seen == expected, (seen, expected)
    print("TRAINING COMPLETE", seen, "of", expected, "files", flush=True)
    return vectorizer, model, seen


def consolidate_microclusters(model, threshold):
    centers = normalize(model.cluster_centers_)
    grouping = AgglomerativeClustering(
        n_clusters=None, distance_threshold=threshold,
        linkage="average", metric="cosine",
    ).fit(centers)
    raw = grouping.labels_
    mapping = {micro: int(cluster) for micro, cluster in enumerate(raw)}
    return mapping, len(set(mapping.values()))


def update_keywords(counter, vocab, repo_weight):
    words = text_tokens(vocab)
    for token in set(words):
        if 4 <= len(token) <= 26:
            counter[token] += repo_weight


def decide_names(counters, topic_counts, topic_repos, topic_examples):
    used = set()
    topics = []
    for topic_id in sorted(topic_counts):
        candidates = [term for term, score in counters[topic_id].most_common(120)
                      if term not in BORING and not term.startswith("extension")]
        selected = candidates[:3] or [f"cluster{topic_id+1}"]
        title = " / ".join(t.title() for t in selected)
        slug = f"topic-{topic_id+1:02d}-" + "-".join(selected[:2])[:55]
        if slug in used:
            slug += f"-{topic_id}"
        used.add(slug)
        topics.append({
            "id": topic_id, "slug": slug, "name": title,
            "files": topic_counts[topic_id],
            "repositories": len(topic_repos[topic_id]),
            "signature": [{"term": x, "weighted_count": round(float(v), 2)}
                          for x, v in counters[topic_id].most_common(18)],
            "examples": topic_examples[topic_id],
        })
    return topics


def classify_all(archive, positions, by_repo, known, vectorizer, model,
                 micro_to_topic, output, text_limit, batch_size, train_count):
    """Same fitted model predicts EVERY file; no separate keyword classifier."""
    category_dir = output / "categories"
    category_dir.mkdir(parents=True, exist_ok=True)
    repo_sizes = {k: len(v) for k, v in by_repo.items()}
    counters = collections.defaultdict(collections.Counter)
    topic_counts = collections.Counter()
    topic_repos = collections.defaultdict(set)
    topic_examples = collections.defaultdict(list)
    total = 0
    sampled_text = 0
    pending = []
    with (output / "FILE_INDEX.csv").open("w", encoding="utf-8", newline="") as idx:
        writer = csv.writer(idx)
        writer.writerow(["learned_topic_id", "repository", "relative_path",
                         "original_archive_path", "bytes", "content_prefix_read",
                         "media_kind", "microcluster_id"])
        # Avoid opening dozens of ZIP files until we know the topic count.
        with contextlib.ExitStack() as stack:
            destinations = {tid: stack.enter_context(
                zipfile.ZipFile(category_dir / f"cluster-{tid:02d}.zip", "w",
                                compression=zipfile.ZIP_DEFLATED,
                                compresslevel=1, allowZip64=True))
                for tid in sorted(set(micro_to_topic.values()))}

            def flush():
                nonlocal total, sampled_text
                if not pending:
                    return
                X = vectorizer.transform([p[3] for p in pending])
                predictions = model.predict(X)
                for item, micro in zip(pending, predictions):
                    info, repo, rel, doc, name_words, kind, has_text = item
                    topic = micro_to_topic[int(micro)]
                    with archive.open(info) as src, destinations[topic].open(
                        info.filename, "w", force_zip64=True) as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                    writer.writerow((topic, repo, rel, info.filename, info.file_size,
                                     has_text, kind, int(micro)))
                    topic_counts[topic] += 1
                    topic_repos[topic].add(repo)
                    weight = min(1.0, 6.0 / math.sqrt(repo_sizes[repo]))
                    update_keywords(counters[topic], name_words, weight)
                    if len(topic_examples[topic]) < 10:
                        topic_examples[topic].append({"repository": repo, "path": rel})
                    total += 1
                    sampled_text += has_text
                    if total % 100000 == 0:
                        print("PREDICTED AND ARCHIVED", total, "/", train_count, flush=True)
                pending.clear()

            for info in positions:
                if info.is_dir() or not info.filename.startswith("repositories/"):
                    continue
                match = locate(info.filename, known)
                if match is None:
                    raise RuntimeError("Unmapped file in assignment: " + info.filename)
                repo, relative = match
                doc, name_words, kind, has_text = features(
                    repo, relative, archive, info, text_limit)
                pending.append((info, repo, relative, doc, name_words, kind, has_text))
                if len(pending) >= batch_size:
                    flush()
            flush()
    if train_count != total:
        raise RuntimeError(f"Coverage mismatch: trained {train_count}, archived {total}")
    topics = decide_names(counters, topic_counts, topic_repos, topic_examples)
    for topic in topics:
        src = category_dir / f"cluster-{topic['id']:02d}.zip"
        dst = category_dir / (topic["slug"] + ".zip")
        src.rename(dst)
        topic["zip_bytes"] = dst.stat().st_size
    return topics, total, sampled_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--microclusters", type=int, default=48)
    parser.add_argument("--merge-distance", type=float, default=0.42)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--text-bytes", type=int, default=4096)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.input, "r", allowZip64=True) as archive:
        manifest = json.loads(archive.read("COMBINED_MANIFEST.json"))
        positions, by_repo, expected, known = inventory(archive, manifest)
        if expected < args.microclusters:
            parser.error("microclusters exceed the available file count")
        vectorizer, model, trained = fit_every_file(
            archive, positions, by_repo, args.text_bytes,
            args.microclusters, args.batch_size)
        micro_to_topic, n_topics = consolidate_microclusters(
            model, args.merge_distance)
        print("MODEL GENERATED", n_topics, "categories from",
              args.microclusters, "microclusters", flush=True)
        topics, assigned, text_read = classify_all(
            archive, positions, by_repo, known, vectorizer, model,
            micro_to_topic, args.output, args.text_bytes,
            args.batch_size, trained)
    joblib.dump({
        "vectorizer": vectorizer, "fitted_clusterer": model,
        "microcluster_to_topic": micro_to_topic,
        "topic_names": {p["id"]: p["name"] for p in topics},
    }, args.output / "TRAINED_MODEL.joblib", compress=3)
    result = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "description": "Streaming unsupervised clustering trained on and used to predict every archived file",
        "input": args.input.name,
        "training_file_count": trained,
        "assigned_file_count": assigned,
        "text_prefix_inspected_count": text_read,
        "sampling_exclusions": 0,
        "n_microclusters": args.microclusters,
        "learned_final_topic_count": len(topics),
        "merge_distance": args.merge_distance,
        "method": "HashingVectorizer + weighted online MiniBatchKMeans.partial_fit for ALL files; same fitted MiniBatchKMeans.predict for ALL file assignments; agglomerative merging of learned centroids; automatically named from ALL assigned filename vocabularies",
        "content_policy": f"Up to {args.text_bytes} bytes of readable text per file; non-text binary payloads are preserved in ZIPs and represented by metadata for clustering.",
        "topics": topics,
    }
    (args.output / "LEARNED_TOPICS.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FINAL", assigned, "files; trained", trained,
          "topics", len(topics), "content prefixes", text_read, flush=True)
    for p in sorted(topics, key=lambda t: -t["files"]):
        print("TOPIC", p["slug"], p["files"], "files", p["repositories"],
              "repos", p["name"], flush=True)
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## Same-model all-file topic discovery\n\nTrained and assigned **{assigned:,}** files in **{len(topics)}** learned categories.\n\n")
            f.write("| Category | Files | Repos |\n|---|---:|---:|\n")
            for p in sorted(topics, key=lambda t: -t["files"]):
                f.write(f"| {p['name']} | {p['files']:,} | {p['repositories']:,} |\n")

if __name__ == "__main__":
    main()
