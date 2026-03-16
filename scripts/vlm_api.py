#!/usr/bin/env python3
"""VLM figure review via Anthropic Claude Vision API.

Usage:
    python3 scripts/vlm_api.py --image PATH --output PATH [--api-key-env ANTHROPIC_API_KEY]

Scores a scientific figure on 5 criteria (1-5 each):
  readability, information_density, technical_correctness, aesthetic_quality, accessibility

Outputs JSON with scores, overall mean, decision (APPROVED/REVISE/REJECT), and feedback.
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

# Try to import anthropic SDK; fall back to requests if unavailable
try:
    import anthropic
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    try:
        import requests
        HAS_REQUESTS = True
    except ImportError:
        HAS_REQUESTS = False


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, stripping markdown fences and extra text."""
    # Strip markdown code fences
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    # Find first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    # Last resort: try the whole text
    return json.loads(text)


REVIEW_PROMPT = """You are a scientific figure reviewer. Evaluate this figure for publication quality.

Score each criterion from 1 (poor) to 5 (excellent):

1. **Readability**: Are labels, axes, legends clear? Font size >= 12pt? Resolution adequate?
2. **Information density**: Does the figure convey its message efficiently without clutter?
3. **Technical correctness**: Are axes properly labeled with units? Error bars present where needed? Scale appropriate?
4. **Aesthetic quality**: Is the figure visually clean? Consistent style? Professional appearance?
5. **Accessibility**: Colorblind-friendly palette? Sufficient contrast? Patterns/markers distinguishable without color?

Respond with ONLY valid JSON (no markdown fences):
{
  "scores": {
    "readability": <1-5>,
    "information_density": <1-5>,
    "technical_correctness": <1-5>,
    "aesthetic_quality": <1-5>,
    "accessibility": <1-5>
  },
  "overall": <mean of 5 scores>,
  "decision": "<APPROVED if overall >= 4.0, REVISE if 3.0-3.9, REJECT if < 3.0>",
  "feedback": "<specific actionable feedback for improvement>",
  "regeneration_instructions": "<if REVISE/REJECT: exact changes needed; if APPROVED: null>"
}"""


def get_image_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "image/png")


def review_with_sdk(image_path: Path, api_key: str) -> dict:
    """Review figure using the Anthropic Python SDK."""
    client = anthropic.Anthropic(api_key=api_key)

    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    media_type = get_image_media_type(image_path)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                },
                {"type": "text", "text": REVIEW_PROMPT},
            ],
        }],
    )

    text = message.content[0].text
    return _extract_json(text)


def review_with_requests(image_path: Path, api_key: str) -> dict:
    """Review figure using raw HTTP requests (no SDK dependency)."""
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    media_type = get_image_media_type(image_path)

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": REVIEW_PROMPT},
                ],
            }],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["content"][0]["text"]
    return _extract_json(text)


def fallback_review(image_path: Path) -> dict:
    """Fallback when no API is available — returns a warning with default pass scores."""
    return {
        "scores": {
            "readability": 3,
            "information_density": 3,
            "technical_correctness": 3,
            "aesthetic_quality": 3,
            "accessibility": 3,
        },
        "overall": 3.0,
        "decision": "REVISE",
        "feedback": "VLM API unavailable — this is a fallback score. Manual review recommended.",
        "regeneration_instructions": "No API available for automated review. Please review manually.",
        "_fallback": True,
    }


def main():
    parser = argparse.ArgumentParser(description="VLM figure review via Claude Vision")
    parser.add_argument("--image", required=True, help="Path to figure image")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--api-key-env", default="ANTHROPIC_API_KEY", help="Env var for API key")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get(args.api_key_env, "")

    result = None

    if api_key:
        try:
            if HAS_SDK:
                result = review_with_sdk(image_path, api_key)
            elif HAS_REQUESTS:
                result = review_with_requests(image_path, api_key)
        except Exception as e:
            print(f"WARNING: VLM API call failed: {e}", file=sys.stderr)

    if result is None:
        if not api_key:
            print(f"WARNING: {args.api_key_env} not set — using fallback scores", file=sys.stderr)
        result = fallback_review(image_path)

    # Add metadata
    result["figure"] = str(image_path)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    decision = result.get("decision", "UNKNOWN")
    overall = result.get("overall", 0)
    print(f"VLM Review: {decision} (score: {overall:.1f}/5.0) → {args.output}")

    # Exit code: 0 for APPROVED, 1 for REVISE/REJECT
    sys.exit(0 if decision == "APPROVED" else 1)


if __name__ == "__main__":
    main()
