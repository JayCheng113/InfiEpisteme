"""Tests for scripts/state_guard.py — verify, advance, content checks, hard constraints."""
import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main

import yaml

# Patch ROOT before importing state_guard
import scripts.state_guard as sg


class StateGuardTestBase(TestCase):
    """Base class that sets up a temp project directory mirroring InfiEpisteme structure."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self._orig_root = sg.ROOT
        sg.ROOT = self.tmpdir

        # Create minimal directory structure
        (self.tmpdir / "state").mkdir()
        (self.tmpdir / ".ai" / "core").mkdir(parents=True)
        (self.tmpdir / ".ai" / "evolution").mkdir(parents=True)

        # Create minimal registry.yaml
        self.registry = {
            "phase": "research",
            "current_stage": "S1",
            "stages": {
                "P0": {"status": "complete", "attempts": 1},
                "S0": {"status": "complete", "attempts": 1},
                "S1": {"status": "running", "attempts": 1, "papers_reviewed": 0, "target": 20},
                "S2": {"status": "pending", "attempts": 0},
                "S3": {"status": "pending", "attempts": 0},
                "S4": {"status": "pending", "attempts": 0, "tree_stages_complete": 0},
                "S5": {"status": "pending", "attempts": 0},
                "S6": {"status": "pending", "attempts": 0},
                "S7": {"status": "pending", "attempts": 0, "review_cycles": 0, "current_score": 0},
                "S8": {"status": "pending", "attempts": 0},
            },
        }
        self._write_registry()

        # Create minimal PIPELINE.md with S1 definition
        (self.tmpdir / "PIPELINE.md").write_text("""# Pipeline
### S1 — Literature
```yaml
expected_outputs:
  - RELATED_WORK.md
  - BASELINES.md
  - bibliography.bib
expected_ai_updates:
  - .ai/core/literature.md
registry_fields:
  papers_reviewed: ">= 20"
  baselines_identified: ">= 3"
```

### S2 — Ideation
```yaml
expected_outputs:
  - EXPERIMENT_PLAN.md
  - experiment_tree.json
expected_ai_updates: []
registry_fields: {}
```

### S6 — Writing
```yaml
expected_outputs:
  - paper/main.tex
  - paper.pdf
expected_ai_updates: []
registry_fields: {}
```

### S8 — Delivery
```yaml
expected_outputs:
  - DELIVERY/paper.pdf
  - DELIVERY/code/
  - DELIVERY.md
expected_ai_updates: []
registry_fields: {}
```
""")

    def tearDown(self):
        sg.ROOT = self._orig_root
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_registry(self):
        with open(self.tmpdir / "registry.yaml", "w") as f:
            yaml.dump(self.registry, f, default_flow_style=False, sort_keys=False)


class TestVerifyStage(StateGuardTestBase):
    """Test verify_stage function."""

    def test_s1_missing_outputs_fails(self):
        """S1 verify fails when expected output files are missing."""
        report = sg.verify_stage("S1")
        self.assertFalse(report["passed"])
        missing = [c for c in report["checks"] if not c.get("exists", True)]
        self.assertTrue(len(missing) >= 1)

    def test_s1_all_outputs_present_passes(self):
        """S1 verify passes when all expected files exist."""
        from datetime import datetime
        cur_year = datetime.now().year
        # Generate 30+ unique citations
        citations = " ".join(f"[Author{i}, {2020+i%5}]" for i in range(35))
        (self.tmpdir / "RELATED_WORK.md").write_text(citations + "\n## Identified Gap\nGap here.")
        (self.tmpdir / "BASELINES.md").write_text("## Baseline 1\n## Baseline 2\n## Baseline 3\n")
        # Bibliography with recent papers
        bib_entries = f"""@article{{a, title={{A}}, year={{{cur_year}}}}}
@article{{b, title={{B}}, year={{{cur_year}}}}}
@article{{c, title={{C}}, year={{{cur_year-1}}}}}
@article{{d, title={{D}}, year={{2021}}}}
"""
        (self.tmpdir / "bibliography.bib").write_text(bib_entries)
        (self.tmpdir / ".ai" / "core" / "literature.md").write_text(
            "---\n---\n# Literature\n[A, 2023] [B, 2024] [C, 2025]\nBecause reasons."
        )

        report = sg.verify_stage("S1")
        failed_checks = [c for c in report["checks"] if not c.get("exists", True)]
        self.assertEqual(len(failed_checks), 0, f"Failed checks: {failed_checks}")

    def test_verify_writes_guard_result(self):
        """verify_stage writes state/GUARD_RESULT.json."""
        sg.verify_stage("S1")
        guard_path = self.tmpdir / "state" / "GUARD_RESULT.json"
        self.assertTrue(guard_path.exists())
        result = json.loads(guard_path.read_text())
        self.assertEqual(result["stage"], "S1")

    def test_ai_content_quality_warns_on_short(self):
        """Warns when .ai/ files are too short."""
        (self.tmpdir / ".ai" / "core" / "literature.md").write_text("short")
        (self.tmpdir / "RELATED_WORK.md").write_text("x")
        (self.tmpdir / "BASELINES.md").write_text("x")
        (self.tmpdir / "bibliography.bib").write_text("x")

        report = sg.verify_stage("S1")
        quality_warnings = [w for w in report["warnings"] if "too short" in w]
        self.assertTrue(len(quality_warnings) > 0, f"Warnings: {report['warnings']}")

    def test_infer_papers_reviewed(self):
        """_infer_field correctly counts citations from RELATED_WORK.md."""
        (self.tmpdir / "RELATED_WORK.md").write_text(
            "[Smith, 2023] [Jones, 2024] [Lee, 2022]"
        )
        count = sg._infer_field("S1", "papers_reviewed")
        self.assertEqual(count, 3)


class TestAdvanceStage(StateGuardTestBase):
    """Test advance_stage function."""

    def test_advance_on_pass(self):
        """advance_stage returns True and updates registry when passed."""
        judge_result = {
            "stage": "S1",
            "passed": True,
            "action": "advance",
            "criteria": [],
        }
        (self.tmpdir / "state" / "JUDGE_RESULT.json").write_text(json.dumps(judge_result))

        result = sg.advance_stage("S1")
        self.assertTrue(result)

        reg = sg.load_registry()
        self.assertEqual(reg["stages"]["S1"]["status"], "complete")
        self.assertEqual(reg["current_stage"], "S2")

    def test_advance_on_fail(self):
        """advance_stage returns False and records failure reason."""
        judge_result = {
            "stage": "S1",
            "passed": False,
            "action": "retry",
            "retry_guidance": "Need more papers",
            "criteria": [{"criterion": "paper_count", "met": False}],
        }
        (self.tmpdir / "state" / "JUDGE_RESULT.json").write_text(json.dumps(judge_result))

        result = sg.advance_stage("S1")
        self.assertFalse(result)

        reg = sg.load_registry()
        self.assertIn("last_failure_reason", reg["stages"]["S1"])

    def test_advance_missing_judge_result(self):
        """advance_stage returns False when JUDGE_RESULT.json is missing."""
        result = sg.advance_stage("S1")
        self.assertFalse(result)

    def test_circuit_breaker_on_3_same_failures(self):
        """Circuit breaker triggers after 3 consecutive failures on same criterion."""
        judge_result = {
            "passed": False,
            "criteria": [{"criterion": "paper_count", "met": False}],
            "retry_guidance": "Need more papers",
        }
        (self.tmpdir / "state" / "JUDGE_RESULT.json").write_text(json.dumps(judge_result))

        # Fail 3 times
        for _ in range(3):
            sg.advance_stage("S1")

        reg = sg.load_registry()
        self.assertEqual(reg["stages"]["S1"]["consecutive_same_failure"], 3)

    def test_advance_handles_string_passed_field(self):
        """advance_stage handles passed as string ("true")."""
        judge_result = {"passed": "true", "criteria": []}
        (self.tmpdir / "state" / "JUDGE_RESULT.json").write_text(json.dumps(judge_result))

        result = sg.advance_stage("S1")
        self.assertTrue(result)

    def test_advance_to_complete(self):
        """Advancing from S8 sets current_stage to COMPLETE."""
        self.registry["current_stage"] = "S8"
        self.registry["stages"]["S8"] = {"status": "running", "attempts": 1}
        self._write_registry()

        judge_result = {"passed": True, "criteria": []}
        (self.tmpdir / "state" / "JUDGE_RESULT.json").write_text(json.dumps(judge_result))

        sg.advance_stage("S8")
        reg = sg.load_registry()
        self.assertEqual(reg["current_stage"], "COMPLETE")
        self.assertEqual(reg["phase"], "complete")


class TestContentChecks(StateGuardTestBase):
    """Test _run_content_checks."""

    def test_s1_paper_count_too_low(self):
        """S1 content check fails when < 20 citations."""
        (self.tmpdir / "RELATED_WORK.md").write_text("[A, 2023] [B, 2024]\n")
        (self.tmpdir / "BASELINES.md").write_text("## Baseline 1\n## Baseline 2\n## Baseline 3\n")
        (self.tmpdir / "bibliography.bib").write_text("@article{a, title={A}}\n")

        report = {"checks": [], "warnings": [], "passed": True}
        sg._run_content_checks("S1", report)
        self.assertFalse(report["passed"])

    def test_s1_baseline_count_too_low(self):
        """S1 fails when < 3 baselines."""
        (self.tmpdir / "BASELINES.md").write_text("## Baseline 1\n")

        report = {"checks": [], "warnings": [], "passed": True}
        sg._run_content_checks("S1", report)
        self.assertFalse(report["passed"])

    def test_s2_node_count_validation(self):
        """S2 fails when experiment_tree has < 6 valid nodes."""
        tree = {"nodes": [{"id": "H1_R1", "approach": "test", "status": "pending"}]}
        (self.tmpdir / "experiment_tree.json").write_text(json.dumps(tree))

        report = {"checks": [], "warnings": [], "passed": True}
        sg._run_content_checks("S2", report)
        self.assertFalse(report["passed"])

    def test_s6_empty_pdf_fails(self):
        """S6 fails when paper.pdf is 0 bytes."""
        (self.tmpdir / "paper.pdf").write_text("")

        report = {"checks": [], "warnings": [], "passed": True}
        sg._run_content_checks("S6", report)
        self.assertFalse(report["passed"])

    def test_s6_bib_missing_fields_warns(self):
        """S6 warns when BibTeX entries have missing fields."""
        (self.tmpdir / "bibliography.bib").write_text("@article{test,\nauthor={Smith},\n}\n")

        report = {"checks": [], "warnings": [], "passed": True}
        sg._run_content_checks("S6", report)
        field_warnings = [w for w in report["warnings"] if "missing" in w.lower() and "field" in w.lower()]
        self.assertTrue(len(field_warnings) > 0)


class TestHardConstraints(StateGuardTestBase):
    """Test _enforce_hard_constraints."""

    def test_gpu_budget_exceeded(self):
        """GPU budget check fails when usage exceeds budget."""
        config = {"compute": {"gpu_hours": 10}}
        (self.tmpdir / "config.yaml").write_text(yaml.dump(config))

        tree = {"nodes": [
            {"id": "H1_R1", "status": "complete", "results": {"gpu_hours": 6}},
            {"id": "H1_R2", "status": "complete", "results": {"gpu_hours": 5}},
        ]}
        (self.tmpdir / "experiment_tree.json").write_text(json.dumps(tree))

        report = {"checks": [], "warnings": [], "passed": True}
        sg._enforce_hard_constraints("S4", report)
        self.assertFalse(report["passed"])
        budget_warnings = [w for w in report["warnings"] if "BUDGET EXCEEDED" in w]
        self.assertTrue(len(budget_warnings) > 0)

    def test_gpu_budget_ok(self):
        """GPU budget check passes when within budget."""
        config = {"compute": {"gpu_hours": 100}}
        (self.tmpdir / "config.yaml").write_text(yaml.dump(config))

        tree = {"nodes": [
            {"id": "H1_R1", "status": "complete", "results": {"gpu_hours": 5}},
        ]}
        (self.tmpdir / "experiment_tree.json").write_text(json.dumps(tree))

        report = {"checks": [], "warnings": [], "passed": True}
        sg._enforce_hard_constraints("S4", report)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    main()
