#!/usr/bin/env python3
"""Dispatch paper review to external model (GPT-4o, Gemini, etc).

Usage:
    python3 scripts/cross_review.py --paper PAPER_PATH --persona R1 --output OUTPUT_PATH

Reads cross_review config from config.yaml. Calls external model API.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

PERSONA_PROMPTS = {
    "R1": """You are Reviewer R1 — Methods-Focused Reviewer.
Focus: technical soundness, experimental rigor, statistical significance.
Be skeptical of claims not backed by ablations. Want to see error bars and significance tests.
Score: Soundness (1-4), Presentation (1-4), Contribution (1-4), Overall (1-10).
List: strengths (3+), weaknesses (3+), questions, suggestions.
End with: Accept / Weak Accept / Borderline / Weak Reject / Reject.""",

    "R2": """You are Reviewer R2 — Clarity-Focused Reviewer.
Focus: writing quality, paper organization, accessibility.
Want clear motivation, good examples, intuitive explanations, consistent notation.
Score: Soundness (1-4), Presentation (1-4), Contribution (1-4), Overall (1-10).
List: strengths (3+), weaknesses (3+), questions, suggestions.
End with: Accept / Weak Accept / Borderline / Weak Reject / Reject.""",

    "R3": """You are Reviewer R3 — Novelty-Focused Reviewer.
Focus: contribution significance, comparison to prior work.
Compare carefully against related work. Want clear differentiation and meaningful improvement.
Score: Soundness (1-4), Presentation (1-4), Contribution (1-4), Overall (1-10).
List: strengths (3+), weaknesses (3+), questions, suggestions.
End with: Accept / Weak Accept / Borderline / Weak Reject / Reject.""",
}

def load_config():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def call_openai(model: str, api_key: str, system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI-compatible API."""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return response.choices[0].message.content
    except ImportError:
        # Fallback: use requests directly
        import requests
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

def main():
    parser = argparse.ArgumentParser(description="Dispatch cross-model review")
    parser.add_argument("--paper", required=True, help="Path to paper (main.tex or .pdf)")
    parser.add_argument("--persona", required=True, choices=["R1", "R2", "R3"])
    parser.add_argument("--output", required=True, help="Output review .md path")
    parser.add_argument("--model", default=None, help="Model override")
    args = parser.parse_args()

    config = load_config()
    cr_config = config.get("cross_review", {})

    if not cr_config.get("enabled", False):
        print("Cross-review disabled in config.yaml", file=sys.stderr)
        sys.exit(1)

    model = args.model or cr_config.get("model", "gpt-4o")
    api_key_env = cr_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env)

    if not api_key:
        print(f"ERROR: {api_key_env} not set in environment", file=sys.stderr)
        sys.exit(1)

    # Read paper content
    paper_path = Path(args.paper)
    if not paper_path.exists():
        print(f"ERROR: Paper not found: {paper_path}", file=sys.stderr)
        sys.exit(1)
    paper_content = paper_path.read_text()

    # Truncate if too long (API limits)
    if len(paper_content) > 100000:
        paper_content = paper_content[:100000] + "\n\n[... truncated due to length ...]"

    system_prompt = PERSONA_PROMPTS[args.persona]
    user_prompt = f"""Please review the following research paper thoroughly.

{paper_content}

Provide your complete review following the format specified in your role."""

    print(f"Sending to {model} as {args.persona}...")
    review = call_openai(model, api_key, system_prompt, user_prompt)

    # Write review
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"# Review by {args.persona} (External: {model})\n\n{review}\n")

    print(f"Review written to {args.output}")

if __name__ == "__main__":
    main()
