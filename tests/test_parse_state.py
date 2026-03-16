"""Tests for scripts/parse_state.py."""
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase, main

import yaml


class TestParseState(TestCase):
    """Test parse_state.py CLI commands."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.registry = {
            "phase": "research",
            "current_stage": "S3",
            "stages": {
                "P0": {"status": "complete", "attempts": 1},
                "S0": {"status": "complete", "attempts": 1},
                "S1": {"status": "complete", "attempts": 2, "papers_reviewed": 25, "target": 20},
                "S2": {"status": "complete", "attempts": 1},
                "S3": {"status": "running", "attempts": 1},
                "S4": {"status": "pending", "attempts": 0, "tree_stages_complete": 0, "tree_stages_total": 4},
                "S5": {"status": "pending", "attempts": 0},
                "S6": {"status": "pending", "attempts": 0},
                "S7": {"status": "pending", "attempts": 0, "review_cycles": 0, "current_score": 0},
                "S8": {"status": "pending", "attempts": 0},
            },
            "target_venue": "NeurIPS 2026",
            "target_score": 6.0,
        }
        (self.tmpdir / "registry.yaml").write_text(
            yaml.dump(self.registry, default_flow_style=False, sort_keys=False)
        )
        # Copy scripts
        scripts_src = Path(__file__).resolve().parent.parent / "scripts"
        scripts_dst = self.tmpdir / "scripts"
        shutil.copytree(scripts_src, scripts_dst)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        result = subprocess.run(
            ["python3", str(self.tmpdir / "scripts" / "parse_state.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir,
        )
        return result

    def test_current_stage(self):
        result = self._run("current_stage")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "S3")

    def test_stage_status(self):
        result = self._run("stage_status", "S1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "complete")

    def test_stage_status_running(self):
        result = self._run("stage_status", "S3")
        self.assertEqual(result.stdout.strip(), "running")

    def test_next_stage(self):
        result = self._run("next_stage", "S3")
        self.assertEqual(result.stdout.strip(), "S4")

    def test_next_stage_last(self):
        result = self._run("next_stage", "S8")
        self.assertEqual(result.stdout.strip(), "COMPLETE")

    def test_status_full(self):
        result = self._run("status")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Current Stage: S3", result.stdout)
        self.assertIn("S1: complete", result.stdout)
        self.assertIn("papers: 25/20", result.stdout)

    def test_unknown_command(self):
        result = self._run("nonexistent")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    main()
