#!/usr/bin/env python3
"""Semantic Scholar search CLI — used by skills for literature discovery.

Usage:
    python3 scripts/scholarly_search.py search "query string" [--limit 50]
    python3 scripts/scholarly_search.py novelty "research question" [--method "method name"]
    python3 scripts/scholarly_search.py bibtex PAPER_ID [PAPER_ID ...]

Outputs results as JSON to stdout.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
S2_API = "https://api.semanticscholar.org/graph/v1"

def load_config():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def get_session():
    config = load_config()
    session = requests.Session()
    api_key = config.get("resources", {}).get("semantic_scholar_key", "")
    if api_key:
        session.headers["x-api-key"] = api_key
    session.headers["User-Agent"] = "InfiEpisteme/2.0"
    return session

def search(query: str, limit: int = 50) -> list:
    session = get_session()
    papers = []
    offset = 0
    per_page = min(limit, 100)

    while len(papers) < limit:
        params = {
            "query": query, "offset": offset, "limit": per_page,
            "fields": "title,abstract,authors,year,venue,citationCount,url,externalIds",
        }
        try:
            resp = session.get(f"{S2_API}/paper/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", []):
                papers.append({
                    "paperId": item.get("paperId", ""),
                    "title": item.get("title", ""),
                    "abstract": (item.get("abstract") or "")[:500],
                    "authors": [a.get("name", "") for a in item.get("authors", [])],
                    "year": item.get("year"),
                    "venue": item.get("venue", ""),
                    "citationCount": item.get("citationCount", 0),
                    "url": item.get("url", ""),
                    "arxivId": (item.get("externalIds") or {}).get("ArXiv"),
                })
            if not data.get("data") or len(data["data"]) < per_page:
                break
            offset += per_page
            time.sleep(1)
        except requests.RequestException as e:
            print(f"API error: {e}", file=sys.stderr)
            break

    return papers[:limit]

def check_novelty(question: str, method: str = "") -> dict:
    queries = [question]
    if method:
        queries.append(f"{method} {question}")

    all_papers = {}
    for q in queries:
        for paper in search(q, limit=20):
            all_papers[paper["paperId"]] = paper
        time.sleep(1)

    question_words = set(question.lower().split())
    high_sim = []
    for paper in all_papers.values():
        words = set(paper["title"].lower().split()) | set(paper.get("abstract", "").lower().split())
        overlap = len(question_words & words) / max(len(question_words), 1)
        if overlap > 0.4:
            high_sim.append(paper)

    return {
        "is_novel": len(high_sim) < 3,
        "high_similarity_count": len(high_sim),
        "total_papers_found": len(all_papers),
        "similar_papers": high_sim[:10],
        "summary": f"Found {len(high_sim)} highly similar papers out of {len(all_papers)} total.",
    }

def fetch_bibtex(paper_ids: list) -> list:
    session = get_session()
    entries = []
    for pid in paper_ids:
        try:
            resp = session.get(f"{S2_API}/paper/{pid}", params={"fields": "citationStyles"})
            resp.raise_for_status()
            bib = (resp.json().get("citationStyles") or {}).get("bibtex", "")
            if bib:
                entries.append(bib)
            time.sleep(0.5)
        except requests.RequestException:
            continue
    return entries

def main():
    parser = argparse.ArgumentParser(description="Semantic Scholar search CLI")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=50)

    p_novelty = sub.add_parser("novelty")
    p_novelty.add_argument("question")
    p_novelty.add_argument("--method", default="")

    p_bib = sub.add_parser("bibtex")
    p_bib.add_argument("paper_ids", nargs="+")

    args = parser.parse_args()

    if args.command == "search":
        result = search(args.query, args.limit)
        print(json.dumps(result, indent=2))
    elif args.command == "novelty":
        result = check_novelty(args.question, args.method)
        print(json.dumps(result, indent=2))
    elif args.command == "bibtex":
        entries = fetch_bibtex(args.paper_ids)
        print("\n\n".join(entries))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
