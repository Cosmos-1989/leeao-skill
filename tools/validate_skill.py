#!/usr/bin/env python3
"""Check local links, evidence locators, and pinned corpus metadata, not prose quality."""

import argparse
import datetime
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

try:
    from .corpus import DEFAULT_UPSTREAM, ROOT, build_manifest
except ImportError:
    from corpus import DEFAULT_UPSTREAM, ROOT, build_manifest

REQUIRED_CARD_FIELDS = {
    "id", "source", "section", "line_start", "line_end", "anchors", "date",
    "date_basis", "modes", "observation", "application", "limit",
}
CARD_ID = re.compile(r"E\d{2}")
LOCAL_LINK = re.compile(r"\[[^\]\n]*\]\((<[^>]+>|[^)\n]+)\)")
RESOURCE_PATH = re.compile(r"`((?:prompts|knowledge|facts|docs|evals|tools|tests|skills)/[^`\s]+)[^`\n]*`")


def read_jsonl(path):
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{path.name}:{number}: invalid JSON: {error.msg}") from error
    return records


def safe_source(base, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("source path must be a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe source path: {value}")
    result = (Path(base) / value).resolve()
    if not result.is_relative_to(Path(base).resolve()):
        raise ValueError(f"source escapes corpus: {value}")
    return result


def check_links(root):
    errors = []
    for document in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in document.relative_to(root).parts):
            continue
        for target in LOCAL_LINK.findall(document.read_text(encoding="utf-8")):
            target = target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (document.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.is_file():
                errors.append(f"{document.relative_to(root)}: broken/internal escaping link: {target}")
        for resource in RESOURCE_PATH.findall(document.read_text(encoding="utf-8")):
            if any(char in resource for char in "*?["):
                exists = any(root.glob(resource))
            else:
                destination = (root / resource).resolve()
                exists = destination.is_relative_to(root.resolve()) and destination.exists()
            if not exists:
                errors.append(f"{document.relative_to(root)}: missing root-relative resource: {resource}")
    return errors


def check_manifest(manifest):
    errors = []
    if manifest.get("schema_version") != 1:
        errors.append("manifest: unsupported schema")
    files = manifest.get("files")
    if not isinstance(files, list):
        return errors + ["manifest: files must be a list"]
    seen = set()
    categories = {}
    works = 0
    for record in files:
        if not isinstance(record, dict):
            errors.append("manifest: record must be an object")
            continue
        source = record.get("path")
        try:
            safe_source(Path("/tmp/leeao-validation-base"), source)
        except ValueError as error:
            errors.append(f"manifest: {error}")
            continue
        if source in seen:
            errors.append(f"manifest: duplicate path {source}")
        seen.add(source)
        parts = PurePosixPath(source).parts
        expected_kind = "work" if len(parts) > 1 and parts[-1] != "README.md" else "metadata"
        if record.get("kind") != expected_kind:
            errors.append(f"manifest: wrong kind {source}")
        works += int(expected_kind == "work")
        if len(parts) > 1:
            group = categories.setdefault(parts[0], {"markdown": 0, "works": 0})
            group["markdown"] += 1
            group["works"] += int(expected_kind == "work")
        if not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", ""))):
            errors.append(f"manifest: invalid hash {source}")
        for field in ("bytes", "lines"):
            if type(record.get(field)) is not int or record[field] < 0:
                errors.append(f"manifest: invalid {field} {source}")
    if manifest.get("markdown_file_count") != len(files) or manifest.get("work_file_count") != works:
        errors.append("manifest: inconsistent file counts")
    if manifest.get("categories") != categories:
        errors.append("manifest: inconsistent category counts")
    return errors


def check_cards(cards, manifest, upstream, offline=False):
    errors = []
    ids = set()
    sources = {record["path"]: record for record in manifest["files"]}
    for card in cards:
        if not isinstance(card, dict) or not REQUIRED_CARD_FIELDS.issubset(card):
            errors.append("evidence: missing required fields")
            continue
        label = str(card["id"])
        if not CARD_ID.fullmatch(label) or label in ids:
            errors.append(f"evidence: invalid or duplicate id {label}")
        ids.add(label)
        try:
            path = safe_source(upstream, card["source"])
        except ValueError as error:
            errors.append(f"{label}: {error}")
            continue
        record = sources.get(card["source"])
        if record is None or record["kind"] != "work":
            errors.append(f"{label}: source is not a manifest work")
            continue
        start, end = card["line_start"], card["line_end"]
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= record["lines"]:
            errors.append(f"{label}: invalid line range")
            continue
        for field in ("section", "date_basis", "observation", "application", "limit"):
            if not isinstance(card[field], str) or not card[field].strip():
                errors.append(f"{label}: empty/invalid {field}")
        valid_anchors = isinstance(card["anchors"], list) and bool(card["anchors"]) and all(
            isinstance(anchor, str) and anchor.strip() for anchor in card["anchors"]
        )
        if not valid_anchors:
            errors.append(f"{label}: anchors must contain nonempty strings")
        if not isinstance(card["modes"], list) or not card["modes"] or not all(
            isinstance(mode, str) and mode.strip() for mode in card["modes"]
        ):
            errors.append(f"{label}: invalid modes")
        if card["date"] is not None:
            try:
                datetime.date.fromisoformat(card["date"])
            except (ValueError, TypeError):
                errors.append(f"{label}: date must be ISO date or null")
        if offline:
            continue
        if not path.is_file():
            errors.append(f"{label}: missing source {card['source']}")
            continue
        passage = "\n".join(path.read_text(encoding="utf-8-sig").splitlines()[start - 1:end])
        if valid_anchors:
            for anchor in card["anchors"]:
                if anchor not in passage:
                    errors.append(f"{label}: anchor outside selected lines: {anchor}")
    return errors


def check_source_snapshot(manifest, upstream):
    current = build_manifest(upstream)
    errors = []
    old = {item["path"]: item for item in manifest["files"]}
    new = {item["path"]: item for item in current["files"]}
    if old.keys() != new.keys():
        errors.append("corpus: file set differs from pinned manifest")
    for path in sorted(old.keys() & new.keys()):
        if old[path] != new[path]:
            errors.append(f"corpus: content/metadata drift: {path}")
    if manifest.get("upstream_commit") and current.get("upstream_commit") != manifest["upstream_commit"]:
        errors.append("corpus: git commit differs from pinned manifest")
    return errors


def validate(root=ROOT, upstream=DEFAULT_UPSTREAM, offline=False):
    root, upstream = Path(root), Path(upstream)
    errors = check_links(root)
    version = (root / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("VERSION: expected semantic version")
    entry = (root / "skills/leeao/SKILL.md").read_text(encoding="utf-8")
    if not entry.startswith("---\n") or "\n---\n" not in entry[4:]:
        errors.append("SKILL: missing YAML frontmatter")
    else:
        frontmatter = entry.split("---\n", 2)[1]
        if not re.search(r"^name: leeao$", frontmatter, re.M):
            errors.append("SKILL: wrong name")
        if not re.search(r"^description: \S.+$", frontmatter, re.M):
            errors.append("SKILL: missing description")
    if f"v{'.'.join(version.split('.')[:2])}" not in entry:
        errors.append("SKILL: displayed version differs from VERSION")
    manifest = json.loads((root / "knowledge/source_manifest.json").read_text(encoding="utf-8"))
    manifest_errors = check_manifest(manifest)
    errors.extend(manifest_errors)
    cards = read_jsonl(root / "knowledge/style_evidence.jsonl")
    if not manifest_errors:
        errors.extend(check_cards(cards, manifest, upstream, offline))
        if not offline:
            errors.extend(check_source_snapshot(manifest, upstream))
    ids = {card.get("id") for card in cards if isinstance(card, dict)}
    for path in root.rglob("*.md"):
        for referenced in set(re.findall(r"(?<![A-Za-z0-9])E\d{2}(?!\d)", path.read_text(encoding="utf-8"))):
            if referenced not in ids:
                errors.append(f"{path.relative_to(root)}: missing evidence card {referenced}")
    for record in read_jsonl(root / "facts/leeao/verified.jsonl"):
        if record.get("kind") != "corpus_metadata" or record.get("source_base") != "upstream":
            errors.append("facts: legacy records must be labeled corpus_metadata/upstream")
        if record.get("source") not in {item["path"] for item in manifest.get("files", [])}:
            errors.append("facts: unknown metadata source")
    cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
    case_ids = set()
    for case in cases:
        if not isinstance(case, dict) or not {"id", "prompt", "baseline_risk", "must", "avoid"}.issubset(case):
            errors.append("evals: incomplete case")
            continue
        if case["id"] in case_ids:
            errors.append(f"evals: duplicate case {case['id']}")
        case_ids.add(case["id"])
        for field in ("must", "avoid"):
            if not isinstance(case[field], list) or not case[field]:
                errors.append(f"evals: missing criteria {case['id']}/{field}")
    return {
        "version": version, "evidence_cards": len(cards),
        "sampled_works": len({card.get("source") for card in cards if isinstance(card, dict)}),
        "evaluation_cases": len(cases),
        "source_checks": "SKIPPED (offline)" if offline else "performed",
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--offline", action="store_true", help="Skip source content/commit checks explicitly")
    args = parser.parse_args()
    try:
        report = validate(upstream=args.upstream, offline=args.offline)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as error:
        parser.exit(1, f"Validation could not finish: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
