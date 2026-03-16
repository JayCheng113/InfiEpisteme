"""Tests for scripts/vlm_api.py — VLM figure review."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase, main

import scripts.vlm_api as vlm


class TestExtractJson(TestCase):
    """Test JSON extraction from LLM responses."""

    def test_clean_json(self):
        text = '{"scores": {"readability": 4}, "overall": 4.0, "decision": "APPROVED"}'
        result = vlm._extract_json(text)
        self.assertEqual(result["decision"], "APPROVED")

    def test_json_with_markdown_fences(self):
        text = '```json\n{"scores": {"readability": 4}, "overall": 4.0, "decision": "APPROVED"}\n```'
        result = vlm._extract_json(text)
        self.assertEqual(result["decision"], "APPROVED")

    def test_json_with_surrounding_text(self):
        text = 'Here is my review:\n{"scores": {"readability": 3}, "overall": 3.0, "decision": "REVISE"}\nHope this helps!'
        result = vlm._extract_json(text)
        self.assertEqual(result["decision"], "REVISE")

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            vlm._extract_json("not json at all")


class TestGetImageMediaType(TestCase):
    """Test MIME type detection."""

    def test_png(self):
        self.assertEqual(vlm.get_image_media_type(Path("fig.png")), "image/png")

    def test_jpg(self):
        self.assertEqual(vlm.get_image_media_type(Path("fig.jpg")), "image/jpeg")

    def test_jpeg(self):
        self.assertEqual(vlm.get_image_media_type(Path("fig.jpeg")), "image/jpeg")

    def test_unknown_defaults_to_png(self):
        self.assertEqual(vlm.get_image_media_type(Path("fig.bmp")), "image/png")


class TestFallbackReview(TestCase):
    """Test fallback review when API is unavailable."""

    def test_fallback_returns_expected_structure(self):
        result = vlm.fallback_review(Path("dummy.png"))
        self.assertIn("scores", result)
        self.assertIn("overall", result)
        self.assertIn("decision", result)
        self.assertIn("feedback", result)
        self.assertTrue(result.get("_fallback"))

    def test_fallback_scores_are_numeric(self):
        result = vlm.fallback_review(Path("dummy.png"))
        for key, value in result["scores"].items():
            self.assertIsInstance(value, (int, float))

    def test_fallback_decision_is_revise(self):
        result = vlm.fallback_review(Path("dummy.png"))
        self.assertEqual(result["decision"], "REVISE")


class TestMainCli(TestCase):
    """Test CLI behavior."""

    def test_missing_image_exits_with_error(self):
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "scripts.vlm_api", "--image", "/nonexistent/fig.png", "--output", "/tmp/out.json"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_no_api_key_uses_fallback(self):
        import os
        import subprocess
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        tmp.close()
        out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        out.close()

        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        result = subprocess.run(
            ["python3", "-m", "scripts.vlm_api",
             "--image", tmp.name,
             "--output", out.name,
             "--api-key-env", "NONEXISTENT_KEY_FOR_TEST"],
            capture_output=True, text=True, env=env,
        )
        # Should use fallback (exit 1 = REVISE, not crash)
        output = json.loads(Path(out.name).read_text())
        self.assertTrue(output.get("_fallback"))

        Path(tmp.name).unlink()
        Path(out.name).unlink()


if __name__ == "__main__":
    main()
