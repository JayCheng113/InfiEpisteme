"""Tests for scripts/verify_citations.py — BibTeX parsing and citation verification logic."""
import json
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main, mock

import scripts.verify_citations as vc


class TestBibtexParsing(TestCase):
    """Test BibTeX parsing functions."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_parse_single_entry(self):
        bib = self.tmpdir / "test.bib"
        bib.write_text("""@article{vaswani_2017_attention,
  title={Attention Is All You Need},
  author={Vaswani, Ashish and Shazeer, Noam},
  year={2017},
  journal={NeurIPS}
}
""")
        entries = vc.parse_bibtex(bib)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["key"], "vaswani_2017_attention")
        self.assertEqual(entries[0]["title"], "Attention Is All You Need")
        self.assertEqual(entries[0]["year"], "2017")

    def test_parse_multiple_entries(self):
        bib = self.tmpdir / "test.bib"
        bib.write_text("""@inproceedings{devlin_2019_bert,
  title={BERT: Pre-training of Deep Bidirectional Transformers},
  author={Devlin, Jacob},
  year={2019},
  booktitle={NAACL}
}

@article{brown_2020_language,
  title={Language Models are Few-Shot Learners},
  author={Brown, Tom B.},
  year={2020},
  journal={NeurIPS}
}
""")
        entries = vc.parse_bibtex(bib)
        self.assertEqual(len(entries), 2)
        keys = {e["key"] for e in entries}
        self.assertEqual(keys, {"devlin_2019_bert", "brown_2020_language"})

    def test_parse_empty_file(self):
        bib = self.tmpdir / "test.bib"
        bib.write_text("")
        entries = vc.parse_bibtex(bib)
        self.assertEqual(len(entries), 0)

    def test_parse_nested_braces(self):
        bib = self.tmpdir / "test.bib"
        bib.write_text("""@article{test_2023_nested,
  title={A {Framework} for {Deep Learning}},
  author={Test, Author},
  year={2023}
}
""")
        entries = vc.parse_bibtex(bib)
        self.assertEqual(len(entries), 1)
        self.assertIn("Framework", entries[0]["title"])

    def test_extract_field_missing(self):
        block = "@article{test, author={Smith}, year={2023}}"
        title = vc._extract_field(block, "title")
        self.assertEqual(title, "")


class TestTitleSimilarity(TestCase):
    """Test title matching logic."""

    def test_identical_titles(self):
        score = vc._title_similarity("Attention Is All You Need", "Attention Is All You Need")
        self.assertGreater(score, 0.9)

    def test_similar_titles(self):
        score = vc._title_similarity("Attention Is All You Need", "Attention is All We Need")
        self.assertGreater(score, 0.5)

    def test_different_titles(self):
        score = vc._title_similarity("Attention Is All You Need", "Deep Reinforcement Learning for Robotics")
        self.assertLess(score, 0.3)

    def test_empty_title(self):
        score = vc._title_similarity("", "Something")
        self.assertEqual(score, 0.0)


class TestFindCitedKeys(TestCase):
    """Test extracting citation keys from .tex files."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_find_cite_keys(self):
        tex_dir = self.tmpdir / "paper" / "sections"
        tex_dir.mkdir(parents=True)
        (tex_dir / "intro.tex").write_text(
            r"As shown by \cite{vaswani_2017_attention}, transformers are powerful. "
            r"See also \cite{devlin_2019_bert,brown_2020_language}."
        )
        keys = vc.find_cited_keys(self.tmpdir / "paper")
        self.assertEqual(keys, {"vaswani_2017_attention", "devlin_2019_bert", "brown_2020_language"})

    def test_find_citep_keys(self):
        tex_dir = self.tmpdir / "paper"
        tex_dir.mkdir()
        (tex_dir / "main.tex").write_text(r"\citep{smith_2023_test}")
        keys = vc.find_cited_keys(tex_dir)
        self.assertIn("smith_2023_test", keys)

    def test_no_tex_files(self):
        tex_dir = self.tmpdir / "paper"
        tex_dir.mkdir()
        keys = vc.find_cited_keys(tex_dir)
        self.assertEqual(keys, set())


class TestVerifyEntry(TestCase):
    """Test verify_entry with mocked API."""

    def test_missing_title_returns_error(self):
        entry = {"key": "test", "title": "", "author": "Smith", "year": "2023"}
        session = mock.MagicMock()
        result = vc.verify_entry(session, entry)
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing title", result["error"])

    def test_api_error_returns_error(self):
        import requests
        entry = {"key": "test", "title": "Some Paper", "author": "Smith", "year": "2023"}
        session = mock.MagicMock()
        session.get.side_effect = requests.RequestException("Connection refused")
        result = vc.verify_entry(session, entry)
        self.assertEqual(result["status"], "error")
        self.assertIn("API error", result["error"])

    def test_no_results_returns_unverified(self):
        entry = {"key": "test", "title": "Nonexistent Paper Title XYZ", "author": "Nobody", "year": "2099"}
        session = mock.MagicMock()
        mock_resp = mock.MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = mock.MagicMock()
        session.get.return_value = mock_resp

        result = vc.verify_entry(session, entry)
        self.assertEqual(result["status"], "unverified")

    def test_good_match_returns_verified(self):
        entry = {"key": "vaswani_2017_attention", "title": "Attention Is All You Need",
                 "author": "Vaswani, Ashish", "year": "2017"}
        session = mock.MagicMock()
        mock_resp = mock.MagicMock()
        mock_resp.json.return_value = {"data": [{
            "paperId": "abc123",
            "title": "Attention Is All You Need",
            "authors": [{"name": "Ashish Vaswani"}, {"name": "Noam Shazeer"}],
            "year": 2017,
            "externalIds": {"ArXiv": "1706.03762"},
        }]}
        mock_resp.raise_for_status = mock.MagicMock()
        session.get.return_value = mock_resp

        result = vc.verify_entry(session, entry)
        self.assertEqual(result["status"], "verified")
        self.assertGreater(result["confidence"], 0.7)


if __name__ == "__main__":
    main()
