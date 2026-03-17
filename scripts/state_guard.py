#!/usr/bin/env python3
"""State Guardian — validates and repairs pipeline state after each skill execution.

Deterministic Python logic (not LLM). Ensures state integrity even when
Claude Code misses updates.

Usage:
    python3 scripts/state_guard.py verify --stage S1    → verify S1 outputs and state
    python3 scripts/state_guard.py advance --stage S1   → read JUDGE_RESULT.json, advance if passed
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
STAGE_ORDER = ["P0", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def load_registry():
    with open(ROOT / "registry.yaml") as f:
        return yaml.safe_load(f)

def save_registry(reg):
    with open(ROOT / "registry.yaml", "w") as f:
        yaml.dump(reg, f, default_flow_style=False, sort_keys=False)

def load_pipeline():
    """Parse PIPELINE.md for stage definitions (expected_outputs, registry_fields)."""
    pipeline_path = ROOT / "PIPELINE.md"
    if not pipeline_path.exists():
        return {}
    content = pipeline_path.read_text()
    # Simple YAML block extraction from markdown fenced blocks
    stages = {}
    current_stage = None
    in_yaml = False
    yaml_lines = []

    for line in content.split("\n"):
        if re.match(r'^###\s+(P0|S\d)', line):
            if current_stage and yaml_lines:
                try:
                    stages[current_stage] = yaml.safe_load("\n".join(yaml_lines))
                except yaml.YAMLError:
                    pass
            current_stage = re.match(r'^###\s+(P0|S\d)', line).group(1)
            yaml_lines = []
            in_yaml = False
        elif line.strip() == "```yaml":
            in_yaml = True
        elif line.strip() == "```" and in_yaml:
            in_yaml = False
        elif in_yaml:
            yaml_lines.append(line)

    if current_stage and yaml_lines:
        try:
            stages[current_stage] = yaml.safe_load("\n".join(yaml_lines))
        except yaml.YAMLError:
            pass

    return stages


def verify_stage(stage: str) -> dict:
    """Verify a stage's outputs and state, attempt repairs."""
    report = {
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "repairs": [],
        "warnings": [],
        "passed": True,
    }

    reg = load_registry()
    pipeline = load_pipeline()
    stage_def = pipeline.get(stage, {})

    # Check 1: Expected output files exist
    expected_outputs = stage_def.get("expected_outputs", [])
    for output_file in expected_outputs:
        path = ROOT / output_file
        if path.exists():
            report["checks"].append({"file": output_file, "exists": True})
        else:
            report["checks"].append({"file": output_file, "exists": False})
            report["passed"] = False

    # Check 2: .ai/ docs updated (modification time + content quality)
    expected_ai = stage_def.get("expected_ai_updates", [])
    for ai_file in expected_ai:
        path = ROOT / ai_file
        if path.exists():
            mtime = os.path.getmtime(path)
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            if age_hours > 24:
                report["warnings"].append(f"{ai_file} not updated recently ({age_hours:.0f}h old)")
            # Content quality check
            content = path.read_text()
            quality = _check_ai_content_quality(ai_file, content)
            if quality:
                report["warnings"].append(f"{ai_file}: {quality}")
        else:
            report["warnings"].append(f"{ai_file} does not exist")

    # Check 2.5: Memory sync result
    mem_sync_path = ROOT / "state" / "MEMORY_SYNC_RESULT.json"
    if mem_sync_path.exists():
        mem_result = json.loads(mem_sync_path.read_text())
        if mem_result.get("stage") == stage:
            report["checks"].append({"file": "memory_sync", "exists": True})
        else:
            report["warnings"].append("MEMORY_SYNC_RESULT.json exists but for different stage")

    # Check 2.6: Context chain has entry for this stage
    chain_path = ROOT / ".ai" / "context_chain.md"
    if chain_path.exists():
        chain_content = chain_path.read_text()
        if f"## {stage}:" in chain_content:
            report["checks"].append({"file": "context_chain_entry", "exists": True})
        else:
            report["warnings"].append(f"context_chain.md missing entry for {stage}")

    # Check 3: Registry fields
    registry_fields = stage_def.get("registry_fields", {})
    stage_info = reg["stages"].get(stage, {})
    for field, constraint in registry_fields.items():
        actual = stage_info.get(field)
        if actual is None:
            # Attempt repair: infer from output files
            repaired_value = _infer_field(stage, field)
            if repaired_value is not None:
                reg["stages"][stage][field] = repaired_value
                report["repairs"].append(f"Set {stage}.{field} = {repaired_value} (inferred)")
            else:
                report["warnings"].append(f"{stage}.{field} missing, could not infer")

    # Check 4: experiment_tree.json consistency (for S3, S4)
    if stage in ("S3", "S4"):
        tree_path = ROOT / "experiment_tree.json"
        if tree_path.exists():
            tree = json.loads(tree_path.read_text())
            nodes = tree.get("nodes", [])

            # Schema validation: every node must have required fields
            required_node_fields = {"id", "status"}
            for node in nodes:
                missing = required_node_fields - set(node.keys())
                if missing:
                    report["warnings"].append(
                        f"Node {node.get('id', '?')} missing fields: {missing}"
                    )
                if node.get("status") == "complete" and node.get("results_path"):
                    results_path = ROOT / node["results_path"]
                    if not results_path.exists():
                        report["warnings"].append(
                            f"Node {node['id']} claims complete but {node['results_path']} missing"
                        )

            # S2 check: >= 6 nodes (verified at S2, not S3)
            if stage == "S2" and len(nodes) < 6:
                report["warnings"].append(f"experiment_tree.json has only {len(nodes)} nodes (need >= 6)")

    # Check 5: Content-level deterministic checks per stage
    _run_content_checks(stage, report)

    # Check 6: Hard constraint enforcement
    _enforce_hard_constraints(stage, report)

    # Save repairs if any
    if report["repairs"]:
        save_registry(reg)

    # Write guard result
    guard_path = ROOT / "state" / "GUARD_RESULT.json"
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    guard_path.write_text(json.dumps(report, indent=2))

    return report


def advance_stage(stage: str) -> bool:
    """Read JUDGE_RESULT.json and advance pipeline if passed."""
    judge_path = ROOT / "state" / "JUDGE_RESULT.json"

    if not judge_path.exists():
        print(f"ERROR: state/JUDGE_RESULT.json not found", file=sys.stderr)
        return False

    result = json.loads(judge_path.read_text())

    # Handle both direct JSON and claude -p wrapped output
    if "result" in result and isinstance(result["result"], str):
        # Try to extract JSON from the result string
        text = result["result"]
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                result = json.loads(text[json_start:json_end])
            except json.JSONDecodeError:
                pass

    passed = result.get("passed", False)
    if isinstance(passed, str):
        passed = passed.lower() in ("true", "yes", "1")

    reg = load_registry()

    if passed:
        reg["stages"][stage]["status"] = "complete"
        idx = STAGE_ORDER.index(stage)
        if idx + 1 < len(STAGE_ORDER):
            next_s = STAGE_ORDER[idx + 1]
            reg["current_stage"] = next_s
        else:
            reg["current_stage"] = "COMPLETE"
            reg["phase"] = "complete"
        save_registry(reg)
        print(f"PASSED — advanced to {reg['current_stage']}")
        return True
    else:
        reasons = result.get("reasons", result.get("retry_guidance", "unknown"))
        reg["stages"][stage]["last_failure_reason"] = str(reasons)[:500]

        # Circuit breaker: track consecutive same-criterion failures
        # Extract failing criteria names for robust comparison (not raw text)
        criteria = result.get("criteria", [])
        failing_criteria = sorted([c.get("criterion", "")[:50] for c in criteria if not c.get("met", True)])
        failing_key = "|".join(failing_criteria) if failing_criteria else str(reasons)[:100]

        prev_key = reg["stages"][stage].get("prev_failure_key", "")
        if failing_key == prev_key:
            count = reg["stages"][stage].get("consecutive_same_failure", 0) + 1
            reg["stages"][stage]["consecutive_same_failure"] = count
            if count >= 3:
                print(f"CIRCUIT BREAKER: {stage} failed 3x on same criterion. Pausing.", file=sys.stderr)
        else:
            reg["stages"][stage]["consecutive_same_failure"] = 1
        reg["stages"][stage]["prev_failure_key"] = failing_key

        save_registry(reg)
        print(f"FAILED — {reasons}")
        return False


def _run_content_checks(stage: str, report: dict):
    """Content-level deterministic checks that go beyond file existence."""

    if stage == "S1":
        # RELATED_WORK.md: count unique citations >= 30
        rw_path = ROOT / "RELATED_WORK.md"
        if rw_path.exists():
            content = rw_path.read_text()
            # Count citation patterns: [Author, Year], [Author et al., Year] or \cite{key} style
            bracket_cites = set(re.findall(r'\[[A-Z][\w\s.,&]+\d{4}\]', content))
            latex_cites = set(re.findall(r'\\cite[tp]?\{([^}]+)\}', content))
            # Expand comma-separated \cite{a,b,c}
            expanded_latex = set()
            for group in latex_cites:
                for key in group.split(","):
                    expanded_latex.add(key.strip())
            total_cites = len(bracket_cites) + len(expanded_latex)
            if total_cites < 30:
                report["checks"].append({"check": "S1_paper_count", "exists": False})
                report["passed"] = False
                report["warnings"].append(
                    f"RELATED_WORK.md has only {total_cites} unique citations (need >= 30)"
                )
            else:
                report["checks"].append({"check": "S1_paper_count", "exists": True})

        # bibliography.bib: recency check — at least 3 papers from current or previous year
        bib_path = ROOT / "bibliography.bib"
        if bib_path.exists():
            bib_content = bib_path.read_text()
            current_year = datetime.now().year
            recent_years = {str(current_year), str(current_year - 1)}
            bib_years = re.findall(r'year\s*=\s*\{?(\d{4})\}?', bib_content)
            recent_count = sum(1 for y in bib_years if y in recent_years)
            if recent_count < 3:
                report["checks"].append({"check": "S1_recency", "exists": False})
                report["passed"] = False
                report["warnings"].append(
                    f"bibliography.bib has only {recent_count} papers from {current_year-1}-{current_year} (need >= 3)"
                )
            else:
                report["checks"].append({"check": "S1_recency", "exists": True})

        # BASELINES.md: count baselines >= 3
        bl_path = ROOT / "BASELINES.md"
        if bl_path.exists():
            count = bl_path.read_text().count("## Baseline")
            if count < 3:
                report["checks"].append({"check": "S1_baseline_count", "exists": False})
                report["passed"] = False
                report["warnings"].append(f"BASELINES.md has only {count} baselines (need >= 3)")
            else:
                report["checks"].append({"check": "S1_baseline_count", "exists": True})

    elif stage == "S2":
        # experiment_tree.json: >= 6 nodes with required fields
        tree_path = ROOT / "experiment_tree.json"
        if tree_path.exists():
            tree = json.loads(tree_path.read_text())
            nodes = tree.get("nodes", [])
            valid = [n for n in nodes if n.get("id") and n.get("approach") and n.get("status")]
            if len(valid) < 6:
                report["checks"].append({"check": "S2_node_count", "exists": False})
                report["passed"] = False
                report["warnings"].append(
                    f"experiment_tree.json has {len(valid)} valid nodes (need >= 6)"
                )
            else:
                report["checks"].append({"check": "S2_node_count", "exists": True})

    elif stage == "S5":
        # ANALYSIS.md must contain p-value or significance keywords
        analysis_path = ROOT / "ANALYSIS.md"
        if analysis_path.exists():
            content = analysis_path.read_text().lower()
            has_stats = any(kw in content for kw in ["p-value", "p =", "p<", "significance", "confidence interval", "t-test", "bootstrap"])
            if not has_stats:
                report["warnings"].append("ANALYSIS.md missing statistical significance keywords")

        # tables/ must have .tex files
        tables_dir = ROOT / "tables"
        if tables_dir.exists():
            tex_files = list(tables_dir.glob("*.tex"))
            if not tex_files:
                report["warnings"].append("tables/ directory exists but has no .tex files")

    elif stage == "S6":
        # bibliography.bib must have entries
        bib_path = ROOT / "bibliography.bib"
        if bib_path.exists():
            content = bib_path.read_text()
            entry_count = len(re.findall(r'@\w+\{', content))
            if entry_count == 0:
                report["checks"].append({"check": "S6_bib_entries", "exists": False})
                report["passed"] = False
                report["warnings"].append("bibliography.bib has 0 entries")
            else:
                report["checks"].append({"check": "S6_bib_entries", "exists": True})

            # Validate BibTeX entries have required fields (reuse verify_citations parser)
            try:
                from scripts.verify_citations import parse_bibtex
                entries = parse_bibtex(bib_path)
                entries_missing_fields = []
                for entry in entries:
                    if not entry.get("title"):
                        entries_missing_fields.append(f"{entry['key']}: missing title")
                    if not entry.get("year"):
                        entries_missing_fields.append(f"{entry['key']}: missing year")
                if entries_missing_fields:
                    report["warnings"].append(
                        f"BibTeX entries with missing fields: {entries_missing_fields[:5]}"
                    )
            except ImportError:
                pass  # verify_citations not available, skip deep validation

        # Citation count in paper >= 30
        paper_dir = ROOT / "paper"
        if paper_dir.exists():
            cite_keys = set()
            for tex_file in paper_dir.rglob("*.tex"):
                tex_content = tex_file.read_text()
                for match in re.finditer(r'\\cite[tp]?\{([^}]+)\}', tex_content):
                    for key in match.group(1).split(","):
                        cite_keys.add(key.strip())
            if len(cite_keys) < 30:
                report["checks"].append({"check": "S6_citation_count", "exists": False})
                report["passed"] = False
                report["warnings"].append(
                    f"Paper has only {len(cite_keys)} unique citations (need >= 30)"
                )
            else:
                report["checks"].append({"check": "S6_citation_count", "exists": True})

        # Recency check on bibliography used in paper
        if bib_path.exists():
            bib_content = bib_path.read_text()
            current_year = datetime.now().year
            recent_years = {str(current_year), str(current_year - 1)}
            bib_years = re.findall(r'year\s*=\s*\{?(\d{4})\}?', bib_content)
            recent_count = sum(1 for y in bib_years if y in recent_years)
            if recent_count < 3:
                report["warnings"].append(
                    f"Bibliography has only {recent_count} papers from {current_year-1}-{current_year} (need >= 3). Paper may appear outdated."
                )

        # paper.pdf file size > 0
        pdf_path = ROOT / "paper.pdf"
        if pdf_path.exists() and pdf_path.stat().st_size == 0:
            report["checks"].append({"check": "S6_pdf_nonzero", "exists": False})
            report["passed"] = False
            report["warnings"].append("paper.pdf exists but is empty (0 bytes)")

        # Citation verification result
        cv_path = ROOT / "state" / "CITATION_VERIFY.json"
        if cv_path.exists():
            cv = json.loads(cv_path.read_text())
            if cv.get("pass_rate", 0) < 1.0:
                unverified = cv.get("unverified", 0)
                report["warnings"].append(
                    f"Citation verification: {unverified} unverified entries "
                    f"(pass rate: {cv.get('pass_rate', 0):.0%})"
                )
            orphans = cv.get("orphan_citations", [])
            if orphans:
                report["warnings"].append(f"Orphan citations (in .tex but not .bib): {orphans}")

    elif stage == "S8":
        # DELIVERY/ completeness
        delivery = ROOT / "DELIVERY"
        if delivery.exists():
            required = ["paper.pdf", "code", "README.md"]
            for item in required:
                if not (delivery / item).exists():
                    report["warnings"].append(f"DELIVERY/{item} missing")

        checklist_path = delivery / "checklist_report.md" if delivery.exists() else None
        if checklist_path and not checklist_path.exists():
            report["warnings"].append("DELIVERY/checklist_report.md missing")


def _enforce_hard_constraints(stage: str, report: dict):
    """Hard constraints that MUST be enforced programmatically."""

    # GPU budget check (for S4)
    if stage == "S4":
        config_path = ROOT / "config.yaml"
        tree_path = ROOT / "experiment_tree.json"
        if config_path.exists() and tree_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            budget = config.get("compute", {}).get("gpu_hours", 0)

            tree = json.loads(tree_path.read_text())
            total_used = 0.0
            for node in tree.get("nodes", []):
                results = node.get("results", {})
                if isinstance(results, dict):
                    total_used += results.get("gpu_hours", 0)

            if budget > 0 and total_used > budget:
                report["checks"].append({"check": "gpu_budget", "exists": False})
                report["passed"] = False
                report["warnings"].append(
                    f"GPU BUDGET EXCEEDED: used {total_used:.1f}h of {budget}h budget"
                )
            elif budget > 0:
                report["checks"].append({"check": "gpu_budget", "exists": True})
                remaining = budget - total_used
                if remaining < budget * 0.1:
                    report["warnings"].append(
                        f"GPU budget low: {remaining:.1f}h remaining of {budget}h"
                    )

    # Git pre-registration check (for S4)
    if stage == "S4":
        import subprocess
        try:
            log = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                capture_output=True, text=True, cwd=ROOT, timeout=10,
            )
            if log.returncode == 0:
                lines = log.stdout.strip().split("\n")
                protocol_commits = [l for l in lines if "research(protocol):" in l]
                result_commits = [l for l in lines if "research(results):" in l]

                if result_commits and not protocol_commits:
                    report["warnings"].append(
                        "Git pre-registration violation: found research(results): "
                        "commits but no research(protocol): commits"
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Git not available, skip check


def _check_ai_content_quality(ai_file: str, content: str) -> str | None:
    """Check if an .ai/ file has meaningful content. Returns warning string or None."""
    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("---") and not l.startswith("#") and not l.startswith(">") and not l.startswith("<!--")]

    # Skip template-only files (contain "To be filled")
    if any("to be filled" in l.lower() for l in lines):
        return "still contains template placeholders ('To be filled')"

    # Minimum content thresholds by file type
    if "literature.md" in ai_file:
        if len(lines) < 10:
            return f"too short ({len(lines)} content lines, need ≥10)"
        # Should contain at least some paper references
        citations = re.findall(r'\[[A-Z][\w\s.,&]+\d{4}\]', content)
        if len(citations) < 3:
            return f"only {len(citations)} citations found (need ≥3)"

    elif "methodology.md" in ai_file:
        if len(lines) < 5:
            return f"too short ({len(lines)} content lines, need ≥5)"
        # Should explain "why" not just "what"
        rationale_words = ["because", "reason", "since", "motivated", "due to",
                           "in order to", "rationale", "justification", "driven by",
                           "as a result", "therefore", "consequently"]
        if not any(w in content.lower() for w in rationale_words):
            return "missing rationale — methodology should explain WHY (no rationale keywords found)"

    elif "research-context.md" in ai_file:
        if len(lines) < 3:
            return f"too short ({len(lines)} content lines, need ≥3)"

    elif "negative-results.md" in ai_file:
        pass  # Append-only, no minimum

    elif "decisions.md" in ai_file:
        pass  # Append-only, no minimum

    elif "experiment-log.md" in ai_file:
        pass  # Append-only, no minimum

    elif "context_chain.md" in ai_file:
        if len(lines) < 3:
            return f"too short ({len(lines)} content lines)"

    return None


def _infer_field(stage: str, field: str):
    """Try to infer a registry field from output files."""
    if stage == "S1" and field == "papers_reviewed":
        rw_path = ROOT / "RELATED_WORK.md"
        if rw_path.exists():
            content = rw_path.read_text()
            citations = re.findall(r'\[[A-Z][\w\s.,&]+\d{4}\]', content)
            return len(set(citations))
    if stage == "S1" and field == "baselines_identified":
        bl_path = ROOT / "BASELINES.md"
        if bl_path.exists():
            return bl_path.read_text().count("## Baseline")
    if stage == "S7" and field == "review_cycles":
        reviews_dir = ROOT / "reviews"
        if reviews_dir.exists():
            cycles = [d.name for d in reviews_dir.iterdir() if d.is_dir() and d.name.startswith("cycle_")]
            return len(cycles)
    return None


def main():
    parser = argparse.ArgumentParser(description="State Guardian")
    parser.add_argument("command", choices=["verify", "advance"])
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()

    if args.command == "verify":
        report = verify_stage(args.stage)
        n_checks = len(report["checks"])
        n_passed = sum(1 for c in report["checks"] if c.get("exists", True))
        n_repairs = len(report["repairs"])
        n_warnings = len(report["warnings"])
        print(f"Guard: {n_passed}/{n_checks} checks passed, {n_repairs} repairs, {n_warnings} warnings")
        for r in report["repairs"]:
            print(f"  REPAIR: {r}")
        for w in report["warnings"]:
            print(f"  WARN: {w}")

    elif args.command == "advance":
        passed = advance_stage(args.stage)
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
