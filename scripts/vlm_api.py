#!/usr/bin/env python3
"""VLM figure review via external API (optional, for non-Claude vision).

Usage:
    python3 scripts/vlm_api.py --image PATH --output PATH

If not needed (Claude Code handles VLM natively), this script is a no-op.
"""
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="External VLM figure review")
    parser.add_argument("--image", required=True, help="Path to figure image")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    # Default: Claude Code handles VLM natively via skills/vlm_review.md
    # This script is a placeholder for external VLM APIs if needed
    result = {
        "figure": str(image_path),
        "note": "Use skills/vlm_review.md for Claude-native VLM review",
        "external_api": False,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))
    print(f"Placeholder written to {args.output}")

if __name__ == "__main__":
    main()
