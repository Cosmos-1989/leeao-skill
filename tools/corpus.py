#!/usr/bin/env python3
"""Read-only corpus search and reproducible metadata for the Lee Ao skill."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPSTREAM = ROOT.parent / "leeao-upstream"
MANIFEST = ROOT / "knowledge" / "source_manifest.json"
CATEGORY = re.compile(r"^\d{2}\.")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def corpus_files(upstream):
    upstream = Path(upstream).resolve()
    if not upstream.is_dir():
        raise ValueError(f"Corpus directory is missing: {upstream}")
    for path in sorted(upstream.rglob("*.md")):
        relative = path.relative_to(upstream)
        if path.is_symlink() or any(part.startswith(".") for part in relative.parts):
            continue
        if len(relative.parts) == 1 or CATEGORY.match(relative.parts[0]):
            yield path


def is_work(relative):
    return len(relative.parts) > 1 and relative.name != "README.md"


def git_revision(upstream):
    result = subprocess.run(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build_manifest(upstream):
    upstream = Path(upstream).resolve()
    records = []
    categories = {}
    for path in corpus_files(upstream):
        relative = path.relative_to(upstream)
        data = path.read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        work = is_work(relative)
        if len(relative.parts) > 1:
            count = categories.setdefault(relative.parts[0], {"markdown": 0, "works": 0})
            count["markdown"] += 1
            count["works"] += int(work)
        records.append({
            "path": relative.as_posix(),
            "kind": "work" if work else "metadata",
            "bytes": len(data),
            "lines": len(lines),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return {
        "schema_version": 1,
        "source_url": "https://github.com/whatot/leeao",
        "upstream_commit": git_revision(upstream),
        "markdown_file_count": len(records),
        "work_file_count": sum(r["kind"] == "work" for r in records),
        "categories": categories,
        "files": records,
    }


def search(upstream, terms, work=None, require_all=False, limit=5, context=1):
    if limit < 1 or context < 0:
        raise ValueError("limit must be positive; context must be nonnegative")
    if not terms or any(not isinstance(term, str) or not term for term in terms):
        raise ValueError("search terms must be nonempty strings")
    upstream = Path(upstream).resolve()
    hits = []
    for path in corpus_files(upstream):
        relative = path.relative_to(upstream)
        if not is_work(relative) or (work and work not in relative.as_posix()):
            continue
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        heading = None
        for offset, line in enumerate(lines):
            match = HEADING.match(line)
            if match:
                heading = match.group(1)
            matches = [term in line for term in terms]
            if not (all(matches) if require_all else any(matches)):
                continue
            start = max(0, offset - context)
            end = min(len(lines), offset + context + 1)
            hits.append({
                "path": relative.as_posix(), "line": offset + 1,
                "markdown_heading": heading,
                "context": [{"line": n + 1, "text": lines[n]} for n in range(start, end)],
            })
            if len(hits) == limit:
                return hits
    return hits


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    index = commands.add_parser("index", help="Rebuild metadata in this project")
    index.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    query = commands.add_parser("search", help="Search literal keywords by source line")
    query.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    query.add_argument("--work", help="Substring of corpus-relative work path")
    query.add_argument("--all", action="store_true", dest="require_all")
    query.add_argument("--limit", type=positive, default=5)
    query.add_argument("--context", type=int, choices=range(0, 6), default=1)
    query.add_argument("terms", nargs="+")
    args = parser.parse_args()
    try:
        if args.command == "index":
            manifest = build_manifest(args.upstream)
            MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({
                "manifest": str(MANIFEST), "markdown": manifest["markdown_file_count"],
                "works": manifest["work_file_count"], "categories": len(manifest["categories"]),
                "upstream_commit": manifest["upstream_commit"],
            }, ensure_ascii=False))
        else:
            print(json.dumps(search(
                args.upstream, args.terms, args.work, args.require_all, args.limit, args.context,
            ), ensure_ascii=False, indent=2))
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
