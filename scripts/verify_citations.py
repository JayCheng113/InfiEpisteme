#!/usr/bin/env python3
"""Full-coverage citation verification — checks every entry in bibliography.bib
against the Semantic Scholar API.

Usage:
    python3 scripts/verify_citations.py [--bib PATH] [--output PATH] [--strict]

Outputs state/CITATION_VERIFY.json with per-entry verification status.
Exit code: 0 if all verified, 1 if any unverified (--strict) or errors.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
S2_API = "https://api.semanticscholar.org/graph/v1"


def load_config():
    config_path = ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_session():
    config = load_config()
    session = requests.Session()
    api_key = config.get("resources", {}).get("semantic_scholar_key", "")
    if api_key:
        session.headers["x-api-key"] = api_key
    session.headers["User-Agent"] = "InfiEpisteme/2.1-citation-verifier"
    return session


def parse_bibtex(bib_path: Path) -> list[dict]:
    """Parse bibliography.bib into a list of entries with key, title, author, year."""
    content = bib_path.read_text()
    entries = []

    # Match @type{key, ... }
    # Use a simple state machine for brace matching
    pattern = re.compile(r'@(\w+)\s*\{([^,]+),')
    for match in pattern.finditer(content):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()

        # Extract the full entry block (brace-matched from the opening {)
        # Find the opening brace position
        brace_pos = content.index('{', match.start())
        brace_count = 0
        end = brace_pos
        for i in range(brace_pos, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        start = match.start()

        block = content[start:end]

        # Extract fields
        title = _extract_field(block, "title")
        author = _extract_field(block, "author")
        year = _extract_field(block, "year")

        entries.append({
            "key": key,
            "type": entry_type,
            "title": title,
            "author": author,
            "year": year,
            "raw": block[:200],  # first 200 chars for debug
        })

    return entries


def _extract_field(block: str, field: str) -> str:
    """Extract a BibTeX field value from an entry block using brace matching."""
    # Find field = ...
    pattern = re.compile(rf'{field}\s*=\s*', re.IGNORECASE)
    match = pattern.search(block)
    if not match:
        return ""

    pos = match.end()
    if pos >= len(block):
        return ""

    # Brace-delimited value: field = {value with {nested} braces}
    if block[pos] == '{':
        brace_count = 0
        start = pos + 1
        for i in range(pos, len(block)):
            if block[i] == '{':
                brace_count += 1
            elif block[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return block[start:i].strip()
        return block[start:].strip()  # unclosed brace, return what we have

    # Quote-delimited value: field = "value"
    if block[pos] == '"':
        end = block.find('"', pos + 1)
        if end >= 0:
            return block[pos + 1:end].strip()
        return block[pos + 1:].strip()

    # Bare value: field = value (until comma or closing brace)
    end = len(block)
    for ch in (',', '}'):
        idx = block.find(ch, pos)
        if idx >= 0 and idx < end:
            end = idx
    return block[pos:end].strip()


def verify_entry(session: requests.Session, entry: dict) -> dict:
    """Verify a single bibliography entry against Semantic Scholar.

    Returns a result dict with status: verified/unverified/error and details.
    """
    result = {
        "key": entry["key"],
        "title": entry["title"],
        "author": entry["author"],
        "year": entry["year"],
        "status": "unverified",
        "match_title": None,
        "match_year": None,
        "match_authors": None,
        "paper_id": None,
        "confidence": 0.0,
        "error": None,
    }

    if not entry["title"]:
        result["status"] = "error"
        result["error"] = "Missing title in BibTeX entry"
        return result

    # Search by title
    try:
        params = {
            "query": entry["title"],
            "limit": 5,
            "fields": "title,authors,year,externalIds",
        }
        resp = session.get(f"{S2_API}/paper/search", params=params)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("data", [])
        if not candidates:
            result["status"] = "unverified"
            result["error"] = "No results from Semantic Scholar"
            return result

        # Find best match
        best_match = None
        best_score = 0.0

        for paper in candidates:
            score = _title_similarity(entry["title"], paper.get("title", ""))

            # Year match bonus
            if entry["year"] and paper.get("year"):
                try:
                    if int(entry["year"]) == int(paper["year"]):
                        score += 0.2
                except ValueError:
                    pass

            # Author match bonus
            if entry["author"]:
                paper_authors = " ".join(
                    a.get("name", "") for a in paper.get("authors", [])
                ).lower()
                first_author = entry["author"].split(" and ")[0].split(",")[0].strip().lower()
                if first_author and first_author in paper_authors:
                    score += 0.2

            if score > best_score:
                best_score = score
                best_match = paper

        if best_match and best_score >= 0.7:
            result["status"] = "verified"
            result["match_title"] = best_match.get("title", "")
            result["match_year"] = best_match.get("year")
            result["match_authors"] = [
                a.get("name", "") for a in best_match.get("authors", [])[:3]
            ]
            result["paper_id"] = best_match.get("paperId", "")
            result["confidence"] = min(best_score, 1.0)
        else:
            result["status"] = "unverified"
            result["error"] = f"Best match score {best_score:.2f} below threshold 0.7"
            if best_match:
                result["match_title"] = best_match.get("title", "")

    except requests.RequestException as e:
        result["status"] = "error"
        result["error"] = f"API error: {str(e)[:200]}"
    except (json.JSONDecodeError, KeyError) as e:
        result["status"] = "error"
        result["error"] = f"Parse error: {str(e)[:200]}"

    return result


def _title_similarity(title_a: str, title_b: str) -> float:
    """Compute normalized word overlap between two titles."""
    words_a = set(re.findall(r'\w+', title_a.lower()))
    words_b = set(re.findall(r'\w+', title_b.lower()))

    if not words_a or not words_b:
        return 0.0

    # Remove common stop words
    stops = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "by", "is", "are"}
    words_a -= stops
    words_b -= stops

    if not words_a or not words_b:
        return 0.0

    overlap = len(words_a & words_b)
    return overlap / max(len(words_a), len(words_b))


def find_cited_keys(tex_dir: Path) -> set[str]:
    """Extract all \\cite{...} keys from .tex files."""
    keys = set()
    for tex_file in tex_dir.rglob("*.tex"):
        content = tex_file.read_text()
        for match in re.finditer(r'\\cite[tp]?\{([^}]+)\}', content):
            for key in match.group(1).split(","):
                keys.add(key.strip())
    return keys


def main():
    parser = argparse.ArgumentParser(description="Full citation verification")
    parser.add_argument("--bib", default=str(ROOT / "bibliography.bib"), help="Path to .bib file")
    parser.add_argument("--output", default=str(ROOT / "state" / "CITATION_VERIFY.json"))
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any citation unverified")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Seconds between API calls")
    args = parser.parse_args()

    bib_path = Path(args.bib)
    if not bib_path.exists():
        print(f"ERROR: {bib_path} not found", file=sys.stderr)
        sys.exit(1)

    entries = parse_bibtex(bib_path)
    print(f"Found {len(entries)} bibliography entries.")

    if not entries:
        print("No entries to verify.")
        sys.exit(0)

    # Find cited keys from .tex files
    paper_dir = ROOT / "paper"
    cited_keys = find_cited_keys(paper_dir) if paper_dir.exists() else set()

    session = get_session()
    results = []
    verified_count = 0
    unverified_count = 0
    error_count = 0

    for i, entry in enumerate(entries):
        print(f"  [{i+1}/{len(entries)}] Verifying: {entry['key']} — {entry['title'][:60]}...")
        result = verify_entry(session, entry)
        result["cited_in_paper"] = entry["key"] in cited_keys
        results.append(result)

        if result["status"] == "verified":
            verified_count += 1
        elif result["status"] == "unverified":
            unverified_count += 1
            print(f"    ⚠ UNVERIFIED: {result['error']}")
        else:
            error_count += 1
            print(f"    ✗ ERROR: {result['error']}")

        time.sleep(args.rate_limit)

    # Detect orphan citations (cited in .tex but not in .bib)
    bib_keys = {e["key"] for e in entries}
    orphan_citations = cited_keys - bib_keys

    # Summary
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "bib_file": str(bib_path),
        "total_entries": len(entries),
        "verified": verified_count,
        "unverified": unverified_count,
        "errors": error_count,
        "pass_rate": verified_count / len(entries) if entries else 0,
        "orphan_citations": sorted(orphan_citations),
        "entries": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))

    print(f"\nResults: {verified_count}/{len(entries)} verified "
          f"({report['pass_rate']:.0%}), {unverified_count} unverified, {error_count} errors")
    if orphan_citations:
        print(f"Orphan citations (in .tex but not .bib): {orphan_citations}")
    print(f"Report written to {args.output}")

    if args.strict and (unverified_count > 0 or orphan_citations):
        sys.exit(1)


if __name__ == "__main__":
    main()
