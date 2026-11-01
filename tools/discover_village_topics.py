#!/usr/bin/env python3
"""Discover AI Village's own file topics, then generate one ZIP per learned topic.

Uses balanced, deterministic samples from the original combined ZIP, TF-IDF,
Latent Semantic Analysis (SVD), and unsupervised MiniBatchKMeans.
No predefined topic labels or keyword taxonomy. Topic names and phrases are
learned from the actual sampled files; every file is assigned using the learned
topic lexicon and samples of text (falling back to repo's learned topic).

Output:
  <output>/LEARNED_TOPICS.json       inferred topic names, signatures, evidence
  <output>/FILE_INDEX.csv           original file paths + chosen topic
  <output>/categories/<topic>.zip    separate ZIPs (original paths preserved)

This is unsupervised lexical/latent-semantic discovery, not a neural embedding
model. Some topics may need renaming or manual review.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import heapq
import json
import math
import re
import shutil
import zipfile
from pathlib import Path

import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

TXT = set(".txt .md .mdx .rst .adoc .html .css .js .jsx .ts .tsx .py .rb .lua .rs .go .java .kt .swift .cs .c .cpp .h .hpp .php .sh .bash .json .jsonc .yaml .yml .toml .xml .ini .cfg .conf .sql .csv .tsv .tex .log .srt .vtt .svg .ipynb".split())
GENERIC = set("the and for from with this that using file files repo project example examples readme overview main index indexjs source src code script scripts data github gitlab village public license new test tests docs document ai agent agents assets image images function import return javascript python python3 true false name content created default current output input this their".split())
WORD = re.compile(r"[a-z][a-z0-9]{2,}")
CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")

def words(s):
    return WORD.findall(CAMEL.sub(" ", s).lower())

def valid_path(name):
    return (name.startswith("repositories/") and "\\" not in name
            and ".." not in name.split("/") and not name.startswith("/"))

def locate(name, repos):
    if not valid_path(name):
        return None
    seg = name[len("repositories/"):].split("/")
    # Most projects are 3 segments; nested projects use longer namespaces.
    for n in range(min(len(seg)-1, 12), 1, -1):
        candidate = "/".join(seg[:n])
        if candidate in repos:
            return candidate, "/".join(seg[n:])
    return None

def sample_text(archive, info, maximum=1400):
    suffix = Path(info.filename).suffix.lower()
    base = Path(info.filename).name.lower()
    if suffix not in TXT and base not in ("dockerfile", "makefile", "readme", "license"):
        return ""
    try:
        with archive.open(info) as f:
            raw = f.read(maximum)
        if b"\x00" in raw[:200]:
            return ""
        return raw.decode("utf-8", "replace")
    except Exception:
        return ""

BOILERPLATE = set("href meta property const export class style margin padding font http https www com org usr bin gitignore stroke include stddef var let div span html header body footer link rel content script charset viewport node modules package public lang utf id type source map encoding return null false true utf8 path json".split())


def corpus_text(repo, rel, sample):
    """Prefer meaning (project titles, file purpose, comments) over raw syntax."""
    project = repo.split("/")[-1]
    path = Path(rel)
    suffix = path.suffix.lower()
    title_words = [t for t in words(project) if t not in BOILERPLATE]
    filename_words = [t for t in words(path.stem) if t not in BOILERPLATE]
    directory_words = [t for t in words(" ".join(path.parts[:-1][-4:]))
                       if t not in BOILERPLATE]
    # Only documentation prose and programming comments describe subject matter
    # reliably. Raw HTML/CSS/JSON/Python code otherwise clusters by syntax.
    if suffix in (".md", ".mdx", ".txt", ".rst", ".adoc"):
        relevant = sample[:700]
    elif suffix in (".py", ".js", ".ts", ".tsx", ".jsx", ".lua", ".rb",
                    ".rs", ".go", ".java", ".c", ".cpp", ".cs", ".sh"):
        lines = sample[:1200].splitlines()
        relevant = " ".join(line for line in lines[:25]
                            if line.lstrip().startswith(("#", "//", "/*", "* ", '"""', "'''")))
    elif suffix in (".htm", ".html"):
        tags = re.findall(r"<title[^>]*>(.*?)</title>", sample[:1200], re.I | re.S)
        relevant = " ".join(tags)
    else:
        relevant = ""
    content_words = [t for t in words(relevant) if t not in BOILERPLATE
                     and t not in GENERIC][:80]
    return " ".join(title_words * 9 + filename_words * 4
                    + directory_words * 2 + content_words)

def sample_candidates(source, known, per_repo):
    """Deterministic priority reservoir per repo with balanced text and media."""
    selected = collections.defaultdict(lambda: {"text": [], "other": []})
    scanned = 0
    for info in source.infolist():
        if info.is_dir() or not valid_path(info.filename):
            continue
        pair = locate(info.filename, known)
        if not pair:
            continue
        repo, rel = pair
        if not rel:
            continue
        typ = "text" if Path(rel).suffix.lower() in TXT else "other"
        limit = per_repo if typ == "text" else max(5, per_repo // 4)
        heap = selected[repo][typ]
        # Smallest hash wins; selecting without reading all file contents.
        rank = int.from_bytes(hashlib.blake2b(info.filename.encode(), digest_size=8).digest(), "big")
        choice = (-rank, info)
        if len(heap) < limit:
            heapq.heappush(heap, choice)
        elif choice[0] > heap[0][0]:
            heapq.heapreplace(heap, choice)
        scanned += 1
    candidates = [(repo, info) for repo, pools in selected.items()
                  for heap in pools.values() for _, info in heap]
    candidates.sort(key=lambda x: (x[0], x[1].filename))
    print("Indexed", scanned, "archive files; selected", len(candidates),
          "balanced representatives from", len(selected), "repositories", flush=True)
    return candidates

def discover(source, manifest, per_repo):
    names = {row["name"] for row in manifest["projects"]}
    samples = []
    doc_repos = []
    doc_paths = []
    candidates = sample_candidates(source, names, per_repo)
    for n, (repo, info) in enumerate(candidates, 1):
        rel = info.filename[len("repositories/" + repo + "/"):]
        content = sample_text(source, info)
        text = corpus_text(repo, rel, content)
        if len(text.strip()) < 5:
            continue
        samples.append(text)
        doc_repos.append(repo)
        doc_paths.append(rel)
        if n % 6000 == 0:
            print("Read representative file", n, "/", len(candidates), flush=True)
    if len(samples) < 100:
        raise RuntimeError("Insufficient representative files for unsupervised discovery")
    print("Discovering latent topics from", len(samples), "representative files", flush=True)
    vectorizer = TfidfVectorizer(
        stop_words="english", max_features=18000, min_df=3, max_df=0.70,
        ngram_range=(1, 2), sublinear_tf=True,
        token_pattern=r"(?u)\b[a-z][a-z0-9]{2,}\b",
    )
    sparse = vectorizer.fit_transform(samples)
    components = min(72, sparse.shape[0] - 1, sparse.shape[1] - 1)
    if components < 6:
        raise RuntimeError("Corpus has too little vocabulary for topic discovery")
    lsa = TruncatedSVD(n_components=components, n_iter=5, random_state=43)
    dense = normalize(lsa.fit_transform(sparse), copy=False)
    candidates_k = [k for k in (12, 16, 22, 28, 36) if k < len(samples) // 10]
    if not candidates_k:
        candidates_k = [max(3, len(samples) // 20)]
    trials = []
    for k in candidates_k:
        model = MiniBatchKMeans(n_clusters=k, batch_size=2048, n_init=3,
                                max_iter=70, random_state=43)
        labels = model.fit_predict(dense)
        present = len(set(labels))
        if present < k:
            score = -10.0
        else:
            score = float(silhouette_score(dense, labels, sample_size=min(700, len(labels)),
                                           random_state=43, metric="cosine"))
        # Small preference for finer-grained topics when quality is similar.
        score_adjusted = score + 0.002 * math.log(k)
        trials.append((score_adjusted, k, model, labels, score))
        print("Topic count candidate", k, "silhouette", round(score, 4), flush=True)
    _, chosen_k, model, labels, quality = max(trials, key=lambda t: t[0])
    print("Learned", chosen_k, "topic clusters; silhouette", round(quality, 4), flush=True)

    all_terms = np.asarray(vectorizer.get_feature_names_out())
    global_mean = np.asarray(sparse.mean(axis=0)).ravel()
    learned = []
    used_slugs = set()
    for cluster_id in range(chosen_k):
        indices = np.where(labels == cluster_id)[0]
        if not len(indices):
            continue
        local_mean = np.asarray(sparse[indices].mean(axis=0)).ravel()
        # Distinctive, sufficiently frequent phrases beat common boilerplate.
        strength = (local_mean ** 1.25) / (global_mean + 0.00025) ** 0.48
        ranks = np.argsort(-strength)
        terms = []
        for idx in ranks:
            term = str(all_terms[idx])
            segments = term.split()
            if (any(t in GENERIC for t in segments)
                    or len(term) < 4 or term.replace(" ", "").isdigit()):
                continue
            terms.append({"term": term, "weight": round(float(strength[idx]), 5)})
            if len(terms) >= 36:
                break
        if not terms:
            terms = [{"term": f"group-{cluster_id+1}", "weight": 1.0}]
        # Names are generated from distinctive learned terms, not fixed labels.
        name_terms = [x["term"] for x in terms[:3]]
        title = " / ".join(x.title() for x in name_terms)
        slug_words = re.findall(r"[a-z0-9]+", "-".join(name_terms[:2]).lower())
        slug = "-".join(slug_words)[:55].strip("-") or f"cluster-{cluster_id+1}"
        slug = f"topic-{cluster_id+1:02d}-{slug}"
        assert slug not in used_slugs
        used_slugs.add(slug)
        evidence = [
            {"repository": doc_repos[i], "file": doc_paths[i]}
            for i in indices[:8]
        ]
        learned.append({
            "cluster_id": int(cluster_id), "slug": slug,
            "generated_title": title, "sample_file_count": len(indices),
            "signature": terms, "examples": evidence,
        })
    repo_votes = collections.defaultdict(collections.Counter)
    for repo, label in zip(doc_repos, labels):
        repo_votes[repo][int(label)] += 1
    repo_default = {repo: votes.most_common(1)[0][0] for repo, votes in repo_votes.items()}
    return learned, repo_default, chosen_k, quality, len(samples), [(k, round(score, 4)) for _, k, _, _, score in trials]

def make_topic_index(topics):
    """Inverted signatures make file-level inference practical at 2.6M files."""
    inverted = collections.defaultdict(list)
    for topic in topics:
        for term in topic["signature"]:
            inverted[term["term"]].append(
                (topic["cluster_id"], max(0.02, term["weight"]))
            )
    return dict(inverted)


def identify(repo, relative, excerpt, topic_index, repo_default):
    """File-level scoring using the lexicon learned by latent clustering."""
    title = repo.split("/")[-1]
    path = Path(relative)
    def featurize(s):
        w = words(s)
        c = collections.Counter(w)
        c.update(" ".join(w[i:i+2]) for i in range(len(w)-1))
        return c
    scores = collections.defaultdict(float)
    for features, scalar in (
        (featurize(title + " " + path.stem), 3.0),
        (featurize(str(path.parent)), 1.6),
        (featurize(excerpt[:1400]), 0.25),
    ):
        for term, count in features.items():
            hits = topic_index.get(term, ())
            if hits:
                for cluster_id, weight in hits:
                    scores[cluster_id] += weight * scalar * min(3, count)
    if scores:
        selected = max(scores, key=scores.get)
        return selected, round(scores[selected], 4), "lexicon"
    return repo_default.get(repo, 0), 0.0, "repo_fallback"

def sort_files(source, manifest, topics, repo_default, output):
    output.mkdir(parents=True, exist_ok=True)
    category_dir = output / "categories"
    category_dir.mkdir(parents=True, exist_ok=True)
    known = {row["name"] for row in manifest["projects"]}
    counts = collections.Counter()
    sizes = collections.Counter()
    method_counts = collections.Counter()
    errors = []
    topic_index = make_topic_index(topics)
    from contextlib import ExitStack
    with ExitStack() as stack:
        targets = {t["cluster_id"]: stack.enter_context(
            zipfile.ZipFile(category_dir / (t["slug"] + ".zip"), "w",
                            compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True)
        ) for t in topics}
        with (output / "FILE_INDEX.csv").open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(["discovered_topic", "topic_title", "repository",
                             "repository_relative_path", "original_archive_path",
                             "bytes", "score", "assignment_method"])
            for info in source.infolist():
                if info.is_dir() or not valid_path(info.filename):
                    continue
                located = locate(info.filename, known)
                if not located:
                    errors.append({"file": info.filename, "reason": "unknown repository"})
                    continue
                repo, relative = located
                excerpt = sample_text(source, info, 1400)
                cluster_id, score, method = identify(repo, relative, excerpt, topic_index, repo_default)
                topic = topics[cluster_id]
                try:
                    with source.open(info) as original, targets[cluster_id].open(
                            info.filename, mode="w", force_zip64=True) as target:
                        shutil.copyfileobj(original, target, length=1024 * 1024)
                except Exception as exc:
                    errors.append({"file": info.filename, "reason": str(exc)[:200]})
                    continue
                writer.writerow([topic["slug"], topic["generated_title"], repo, relative,
                                 info.filename, info.file_size, score, method])
                counts[cluster_id] += 1
                sizes[cluster_id] += info.file_size
                method_counts[method] += 1
                n = sum(counts.values())
                if n % 100000 == 0:
                    print("Placed", n, "files into", len(topics), "learned categories", flush=True)
        for topic in topics:
            targets[topic["cluster_id"]].writestr(
                "TOPIC_INFO.txt",
                f"Automatically discovered theme: {topic['generated_title']}\n"
                f"Category identifier: {topic['slug']}\n"
                "File paths are preserved under repositories/.\n"
                "Topics are unsupervised interpretations, not verified subject labels.\n")
    if errors:
        raise RuntimeError(f"{len(errors)} file assignments failed; examples: {errors[:5]}")
    return counts, sizes, method_counts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-per-repo", type=int, default=22)
    parser.add_argument("--discovery-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.input, "r", allowZip64=True) as source:
        manifest = json.loads(source.read("COMBINED_MANIFEST.json"))
        topics, defaults, n, quality, sample_count, trials = discover(
            source, manifest, args.sample_per_repo)
        learned = {
            "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "method": "TF-IDF + latent semantic analysis (TruncatedSVD) + unsupervised MiniBatchKMeans; learned characteristic terms",
            "note": "Neither category words nor category count were predefined. Number of clusters selected from a range based on cosine silhouette quality.",
            "source_archive": args.input.name,
            "repository_count": manifest["represented_project_count"],
            "sampled_file_count": sample_count,
            "number_of_discovered_categories": len(topics),
            "candidate_counts_and_silhouette": trials,
            "selected_silhouette": quality,
            "topics": topics,
        }
        (args.output / "LEARNED_TOPICS.json").write_text(
            json.dumps(learned, indent=2, ensure_ascii=False), encoding="utf-8")
        print("GENERATED TOPIC NAMES", flush=True)
        for t in topics:
            print(f"  {t['slug']}: {t['generated_title']} ({t['sample_file_count']} sampled)", flush=True)
        if args.discovery_only:
            return
        counts, sizes, methods = sort_files(source, manifest, topics, defaults, args.output)
        learned["assigned_file_count"] = sum(counts.values())
        learned["assignment_methods"] = dict(methods)
        for t in learned["topics"]:
            cid = t["cluster_id"]
            t["assigned_file_count"] = counts[cid]
            t["original_file_bytes"] = sizes[cid]
            t["zip_bytes"] = (args.output / "categories" / (t["slug"] + ".zip")).stat().st_size
        (args.output / "LEARNED_TOPICS.json").write_text(
            json.dumps(learned, indent=2, ensure_ascii=False), encoding="utf-8")
        print("FINAL assigned", learned["assigned_file_count"], "files", dict(methods), flush=True)

if __name__ == "__main__":
    main()
