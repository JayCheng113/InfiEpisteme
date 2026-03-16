"""Tests for scripts/update_state.py."""
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase, main

import yaml


class TestUpdateState(TestCase):
    """Test update_state.py CLI commands."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.registry = {
            "phase": "research",
            "current_stage": "S1",
            "stages": {
                "P0": {"status": "complete", "attempts": 1},
                "S0": {"status": "complete", "attempts": 1},
                "S1": {"status": "pending", "attempts": 0},
                "S2": {"status": "pending", "attempts": 0},
                "S3": {"status": "pending", "attempts": 0},
                "S4": {"status": "pending", "attempts": 0},
                "S5": {"status": "pending", "attempts": 0},
                "S6": {"status": "pending", "attempts": 0},
                "S7": {"status": "pending", "attempts": 0},
                "S8": {"status": "pending", "attempts": 0},
            },
        }
        (self.tmpdir / "registry.yaml").write_text(
            yaml.dump(self.registry, default_flow_style=False, sort_keys=False)
        )
        scripts_src = Path(__file__).resolve().parent.parent / "scripts"
        shutil.copytree(scripts_src, self.tmpdir / "scripts")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args):
        return subprocess.run(
            ["python3", str(self.tmpdir / "scripts" / "update_state.py")] + list(args),
            capture_output=True, text=True, cwd=self.tmpdir,
        )

    def _load_reg(self):
        with open(self.tmpdir / "registry.yaml") as f:
            return yaml.safe_load(f)

    def test_set_running(self):
        self._run("set_running", "S1")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["status"], "running")
        self.assertEqual(reg["stages"]["S1"]["attempts"], 1)
        self.assertEqual(reg["current_stage"], "S1")

    def test_set_running_increments_attempts(self):
        self._run("set_running", "S1")
        self._run("set_running", "S1")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["attempts"], 2)

    def test_advance(self):
        self._run("set_running", "S1")
        self._run("advance", "S1")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["status"], "complete")
        self.assertEqual(reg["current_stage"], "S2")

    def test_advance_s8_completes_pipeline(self):
        self._run("advance", "S8")
        reg = self._load_reg()
        self.assertEqual(reg["current_stage"], "COMPLETE")
        self.assertEqual(reg["phase"], "complete")

    def test_fail(self):
        self._run("fail", "S1")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["status"], "failed")

    def test_reset(self):
        self._run("set_running", "S1")
        self._run("advance", "S1")
        self._run("set_running", "S2")
        self._run("reset", "S1")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["status"], "pending")
        self.assertEqual(reg["stages"]["S2"]["status"], "pending")
        self.assertEqual(reg["current_stage"], "S1")

    def test_reset_all(self):
        self._run("set_running", "S1")
        self._run("advance", "S1")
        self._run("reset_all")
        reg = self._load_reg()
        self.assertEqual(reg["current_stage"], "P0")
        self.assertEqual(reg["phase"], "alignment")
        for s in ["P0", "S0", "S1", "S2"]:
            self.assertEqual(reg["stages"][s]["status"], "pending")

    def test_set_field(self):
        self._run("set", "S1", "papers_reviewed", "25")
        reg = self._load_reg()
        self.assertEqual(reg["stages"]["S1"]["papers_reviewed"], 25)

    def test_invalid_stage_fails(self):
        result = self._run("set_running", "INVALID")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    main()
