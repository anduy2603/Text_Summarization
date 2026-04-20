import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "raw" / "vietnews"
EXPECTED_SPLITS = ["train", "validation", "test"]
DATASET_NAME = "nam194/vietnews"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download VietNews raw splits for Phase 0 protocol.")
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Optional Hugging Face dataset revision/commit to pin.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing split files if they already exist.",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading VietNews dataset...")
    load_kwargs = {"path": DATASET_NAME}
    if args.revision:
        load_kwargs["revision"] = args.revision
    dataset = load_dataset(**load_kwargs)

    missing = [s for s in EXPECTED_SPLITS if s not in dataset]
    if missing:
        raise ValueError(f"Missing expected splits from source: {missing}")

    row_counts: dict[str, int] = {}
    total_rows = 0

    for split in EXPECTED_SPLITS:
        path = DATA_DIR / f"{split}.jsonl"
        if path.exists() and not args.overwrite:
            raise FileExistsError(
                f"Output file already exists: {path}. Use --overwrite to replace it."
            )
        split_rows = 0
        with path.open("w", encoding="utf-8") as f:
            # Stream records to avoid materializing an in-memory list via to_list().
            for row in dataset[split]:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                split_rows += 1
        row_counts[split] = split_rows
        total_rows += split_rows
        print(f"Saved {split} -> {path} ({split_rows} rows)")

    metadata = {
        "dataset_name": DATASET_NAME,
        "expected_splits": EXPECTED_SPLITS,
        "revision": args.revision,
        "row_counts": row_counts,
        "total_rows": total_rows,
        "downloaded_utc": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = DATA_DIR / "source_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Wrote source metadata -> {metadata_path}")
    print("Done.")


if __name__ == "__main__":
    main()