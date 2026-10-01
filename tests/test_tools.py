import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.corpus import ROOT, build_manifest, search
from tools.validate_skill import (
    check_cards, check_links, check_manifest, check_source_snapshot,
    read_jsonl, safe_source, validate,
)


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.upstream = self.base / "corpus"
        self.upstream.mkdir()
        write(self.upstream, "README.md", "alpha metadata\n")
        write(self.upstream, "01.example/README.md", "alpha category\n")
        write(self.upstream, "01.example/first.md", "# First\nalpha\nalpha beta\n\n## End\nbeta [x]\n")
        write(self.upstream, "01.example/second.md", "# Second\nbeta\n")
        write(self.upstream, ".hidden/secret.md", "alpha\n")
        write(self.upstream, "misc/not-a-work.md", "alpha\n")

    def test_manifest_excludes_hidden_and_noncategory(self):
        manifest = build_manifest(self.upstream)
        self.assertEqual(manifest["markdown_file_count"], 4)
        self.assertEqual(manifest["work_file_count"], 2)
        self.assertEqual(manifest["categories"], {"01.example": {"markdown": 3, "works": 2}})
        self.assertEqual(check_manifest(manifest), [])

    def test_metadata_is_not_a_search_work(self):
        hits = search(self.upstream, ["metadata", "category"])
        self.assertEqual(hits, [])

    def test_line_context_and_heading(self):
        hit = search(self.upstream, ["[x]"], context=1)[0]
        self.assertEqual(hit["line"], 6)
        self.assertEqual(hit["markdown_heading"], "End")
        self.assertEqual(hit["context"], [{"line": 5, "text": "## End"}, {"line": 6, "text": "beta [x]"}])

    def test_default_or_and_same_line(self):
        self.assertEqual(len(search(self.upstream, ["alpha", "beta"])), 4)
        hits = search(self.upstream, ["alpha", "beta"], require_all=True)
        self.assertEqual([hit["line"] for hit in hits], [3])

    def test_work_filter(self):
        hits = search(self.upstream, ["beta"], work="second")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["path"], "01.example/second.md")

    def test_limit_and_zero_context(self):
        hits = search(self.upstream, ["alpha"], limit=1, context=0)
        self.assertEqual(len(hits), 1)
        self.assertEqual(len(hits[0]["context"]), 1)

    def test_empty_terms_rejected(self):
        for terms in ([], [""], [None]):
            with self.assertRaises(ValueError):
                search(self.upstream, terms)

    def test_invalid_limit_and_context(self):
        for kwargs in ({"limit": 0}, {"context": -1}):
            with self.assertRaises(ValueError):
                search(self.upstream, ["alpha"], **kwargs)

    def test_missing_corpus_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.base / "missing")

    def test_symlink_file_excluded(self):
        (self.upstream / "01.example/link.md").symlink_to(self.upstream / "01.example/first.md")
        self.assertEqual(build_manifest(self.upstream)["work_file_count"], 2)

    def test_cli_from_different_directory(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/corpus.py"), "search", "--upstream",
             str(self.upstream), "--work", "first", "--all", "alpha", "beta"],
            cwd=self.base, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)[0]["line"], 3)

    def test_cli_missing_corpus_fails(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/corpus.py"), "search", "--upstream",
             str(self.base / "missing"), "alpha"], capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "skill"
        self.upstream = self.base / "corpus"
        self.root.mkdir()
        self.upstream.mkdir()
        write(self.upstream, "README.md", "source metadata\n")
        write(self.upstream, "01.example/first.md", "# Chapter\nanchor\nending\n")
        self.manifest = build_manifest(self.upstream)
        self.card = {
            "id": "E01", "source": "01.example/first.md", "section": "Chapter",
            "line_start": 1, "line_end": 3, "anchors": ["anchor"], "date": None,
            "date_basis": "unknown", "modes": ["essay"], "observation": "observed",
            "application": "writing use", "limit": "not a factual certification",
        }
        write(self.root, "VERSION", "2.0.0\n")
        write(self.root, "skills/leeao/SKILL.md", "---\nname: leeao\ndescription: Test entry\n---\n# v2.0\nE01\n")
        write(self.root, "knowledge/source_manifest.json", json.dumps(self.manifest))
        write(self.root, "knowledge/style_evidence.jsonl", json.dumps(self.card) + "\n")
        write(self.root, "facts/leeao/verified.jsonl", json.dumps({
            "kind": "corpus_metadata", "source_base": "upstream", "source": "README.md",
        }) + "\n")
        self.case = {"id": "C01", "prompt": "test", "baseline_risk": "test", "must": ["test"], "avoid": ["test"]}
        write(self.root, "evals/cases.json", json.dumps([self.case]))

    def errors(self, card=None, offline=False):
        return check_cards([card or self.card], self.manifest, self.upstream, offline)

    def test_valid_card_and_project(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(validate(self.root, self.upstream)["errors"], [])

    def test_anchor_drift_detected(self):
        card = copy.deepcopy(self.card)
        card["anchors"] = ["not in passage"]
        self.assertIn("anchor outside", " ".join(self.errors(card)))

    def test_range_is_inclusive(self):
        card = copy.deepcopy(self.card)
        card.update(line_start=3, line_end=3, anchors=["ending"])
        self.assertEqual(self.errors(card), [])

    def test_invalid_range_rejected(self):
        for start, end in ((0, 2), (3, 2), (1, 4), (True, 2)):
            card = dict(self.card, line_start=start, line_end=end)
            self.assertIn("invalid line range", " ".join(self.errors(card)))

    def test_safe_source_rejects_escape(self):
        for value in ("../outside.md", "/tmp/outside.md", "a\\b", ""):
            with self.assertRaises(ValueError):
                safe_source(self.upstream, value)

    def test_safe_source_rejects_symlink_escape(self):
        outside = write(self.base, "outside.md", "anchor\n")
        (self.upstream / "01.example/escape.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            safe_source(self.upstream, "01.example/escape.md")

    def test_duplicate_card_id_rejected(self):
        errors = check_cards([self.card, self.card], self.manifest, self.upstream)
        self.assertIn("duplicate id", " ".join(errors))

    def test_invalid_date_rejected(self):
        self.assertIn("date must", " ".join(self.errors(dict(self.card, date="1999-02-30"))))

    def test_manifest_counts_checked(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["work_file_count"] = 99
        self.assertIn("inconsistent file counts", " ".join(check_manifest(manifest)))

    def test_snapshot_detects_content_change(self):
        write(self.upstream, "01.example/first.md", "# Chapter\nanchor\nchanged\n")
        self.assertIn("content/metadata drift", " ".join(check_source_snapshot(self.manifest, self.upstream)))

    def test_snapshot_detects_added_file(self):
        write(self.upstream, "01.example/extra.md", "new\n")
        self.assertIn("file set differs", " ".join(check_source_snapshot(self.manifest, self.upstream)))

    def test_offline_explicitly_skips_missing_source(self):
        missing = self.base / "missing"
        report = validate(self.root, missing, offline=True)
        self.assertEqual(report["errors"], [])
        self.assertIn("SKIPPED", report["source_checks"])
        with self.assertRaises(ValueError):
            validate(self.root, missing)

    def test_offline_still_checks_card_schema(self):
        self.assertIn("invalid line range", " ".join(self.errors(dict(self.card, line_end=99), offline=True)))

    def test_missing_evidence_reference_before_chinese_text(self):
        write(self.root, "README.md", "E77未定位\n")
        self.assertIn("missing evidence card E77", " ".join(validate(self.root, self.upstream)["errors"]))

    def test_markdown_links_and_fragment(self):
        write(self.root, "README.md", "[valid](VERSION) [fragment](#top) [remote](https://example.org/)\n")
        self.assertEqual(check_links(self.root), [])
        write(self.root, "README.md", "[bad](missing.md) [escape](../outside.md)\n")
        self.assertEqual(len(check_links(self.root)), 2)

    def test_jsonl_reports_bad_line(self):
        path = write(self.root, "broken.jsonl", '{}\n{broken}\n')
        with self.assertRaisesRegex(ValueError, "broken.jsonl:2"):
            read_jsonl(path)

    def test_root_relative_code_resource_checked(self):
        write(self.root, "README.md", "`evals/cases.json` and `evals/cases.json check` and `prompts/missing.md`\n")
        errors = check_links(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing root-relative resource", errors[0])

    def test_legacy_facts_label_checked(self):
        write(self.root, "facts/leeao/verified.jsonl", '{"source":"README.md"}\n')
        self.assertIn("corpus_metadata", " ".join(validate(self.root, self.upstream)["errors"]))

    def test_case_duplicate_checked(self):
        write(self.root, "evals/cases.json", json.dumps([self.case, self.case]))
        self.assertIn("duplicate case", " ".join(validate(self.root, self.upstream)["errors"]))

    def test_cli_offline_from_different_directory(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_skill.py"), "--offline", "--upstream",
             str(self.base / "missing")], cwd=self.base, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIPPED", json.loads(result.stdout)["source_checks"])


if __name__ == "__main__":
    unittest.main()
