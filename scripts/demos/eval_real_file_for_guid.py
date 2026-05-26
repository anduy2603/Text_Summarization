from __future__ import annotations

"""
Evaluate one real file (.txt / .docx / .pdf) against VietNews gold for a given guid.

Example:
  python scripts/demos/eval_real_file_for_guid.py \\
    --guid 6131 \\
    --file data/samples/multiformat/6131_article.docx \\
    --engine textrank --max-sentences 2
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.shared.multiformat_experiment import evaluate_real_file_for_guid


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real file ingest + summary ROUGE vs VietNews gold (same guid).",
    )
    parser.add_argument("--guid", type=str, required=True, help="VietNews guid (validation/test/train).")
    parser.add_argument("--file", type=Path, required=True, help="Path to .txt, .docx, or .pdf file.")
    parser.add_argument("--engine", type=str, default="textrank")
    parser.add_argument("--max-sentences", type=int, default=2, dest="max_sentences")
    parser.add_argument("--split", type=str, default="validation")
    parser.add_argument("--protocol", type=str, default="phase0_v2")
    args = parser.parse_args()

    result = evaluate_real_file_for_guid(
        args.guid.strip(),
        args.file,
        engine=args.engine.strip().lower(),
        max_sentences=args.max_sentences,
        target_split=args.split,
        protocol_version=args.protocol,
    )

    # JSON-safe (omit long text unless requested)
    brief = {k: v for k, v in result.items() if not k.endswith("_cleaned_text")}
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
