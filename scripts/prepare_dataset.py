#!/usr/bin/env python3
"""
Prepare VietNews for experiments: apply Phase 0 preprocessing and write processed JSONL + manifest.

Reads:  data/raw/vietnews/{train,validation,test}.jsonl
Writes: data/processed/vietnews/{train,validation,test}.jsonl (gitignored) + dataset_manifest.json

Preprocessing matches backend pipeline (see configs/phase0_protocol.yaml).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT / "evaluation") not in sys.path:
    sys.path.insert(0, str(ROOT / "evaluation"))

from preprocess import preprocess_and_split  # type: ignore[import-not-found]  # noqa: E402

PROTOCOL_VERSION = "phase0_v2"
PROTOCOL_CONFIG_PATH = ROOT / "configs" / "phase0_protocol.yaml"
SPLIT_SEED_OFFSETS = {"train": 101, "validation": 202, "test": 303}


def _load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    json_error_count = 0
    with path.open("r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                json_error_count += 1
                print(f"[WARN] Skip invalid JSON line {line_idx} in {path.name}")
    return rows, json_error_count


def _maybe_limit(
    rows: list[dict],
    limit: int | None,
    seed: int,
) -> tuple[list[dict], list[int] | None, bool]:
    if limit is None or limit <= 0 or len(rows) <= limit:
        return rows, None, False
    idx = list(range(len(rows)))
    rng = random.Random(seed)
    rng.shuffle(idx)
    picked = sorted(idx[:limit])
    return [rows[i] for i in picked], picked, True


def _transform_record(rec: dict) -> tuple[dict | None, str | None]:
    article = rec.get("article")
    abstract = rec.get("abstract")
    art, art_sents = preprocess_and_split(article)
    ref, ref_sents = preprocess_and_split(abstract)
    if not art.strip():
        return None, "empty_article"
    if not ref.strip():
        return None, "empty_reference_summary"
    out = {
        "guid": rec.get("guid"),
        "title": rec.get("title"),
        "article": art,
        "reference_summary": ref,
        "meta": {
            "protocol_version": PROTOCOL_VERSION,
            "article_char_len": len(art),
            "reference_summary_char_len": len(ref),
            "article_sentence_count": len(art_sents),
            "reference_summary_sentence_count": len(ref_sents),
        },
    }
    return out, None


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare VietNews JSONL with Phase 0 preprocessing.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "vietnews",
        help="Directory containing train.jsonl, validation.jsonl, test.jsonl",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data" / "processed" / "vietnews",
        help="Output directory for processed JSONL",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed for optional subset sampling.")
    parser.add_argument("--limit-train", type=int, default=0, help="Max train articles after shuffle (0=all).")
    parser.add_argument("--limit-val", type=int, default=0, help="Max validation articles (0=all).")
    parser.add_argument("--limit-test", type=int, default=0, help="Max test articles (0=all).")
    args = parser.parse_args()

    splits = {
        "train": "train.jsonl",
        "validation": "validation.jsonl",
        "test": "test.jsonl",
    }
    limits = {
        "train": args.limit_train or None,
        "validation": args.limit_val or None,
        "test": args.limit_test or None,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_config_path": str(PROTOCOL_CONFIG_PATH.resolve()),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "base_seed": args.seed,
        "raw_dir": str(args.raw_dir.resolve()),
        "output_dir": str(args.out_dir.resolve()),
        "splits": {},
        "global_stats": {},
    }

    total_raw_rows = 0
    total_subset_rows = 0
    total_written_rows = 0
    total_json_decode_errors = 0
    total_dropped_empty_article = 0
    total_dropped_empty_reference = 0
    global_article_char_lengths: list[int] = []
    global_reference_char_lengths: list[int] = []
    global_article_sentence_counts: list[int] = []
    global_reference_sentence_counts: list[int] = []

    for split_name, fname in splits.items():
        src = args.raw_dir / fname
        if not src.is_file():
            raise FileNotFoundError(f"Missing raw file: {src}")
        rows, json_decode_errors = _load_jsonl(src)
        total_json_decode_errors += json_decode_errors
        raw_rows = len(rows)
        lim = limits[split_name]
        split_seed = args.seed + SPLIT_SEED_OFFSETS[split_name]
        rows, selected_indices, subset_applied = _maybe_limit(rows, lim, split_seed)

        kept: list[dict] = []
        dropped_empty_article = 0
        dropped_empty_reference = 0
        selected_guids: list[int | str] = []
        for rec in rows:
            tr, drop_reason = _transform_record(rec)
            if tr is None:
                if drop_reason == "empty_article":
                    dropped_empty_article += 1
                elif drop_reason == "empty_reference_summary":
                    dropped_empty_reference += 1
                continue
            kept.append(tr)
            if tr.get("guid") is not None:
                selected_guids.append(tr["guid"])
            global_article_char_lengths.append(tr["meta"]["article_char_len"])
            global_reference_char_lengths.append(tr["meta"]["reference_summary_char_len"])
            global_article_sentence_counts.append(tr["meta"]["article_sentence_count"])
            global_reference_sentence_counts.append(tr["meta"]["reference_summary_sentence_count"])

        out_path = args.out_dir / fname
        with out_path.open("w", encoding="utf-8") as f:
            for rec in kept:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        total_raw_rows += raw_rows
        total_subset_rows += len(rows)
        total_written_rows += len(kept)
        total_dropped_empty_article += dropped_empty_article
        total_dropped_empty_reference += dropped_empty_reference

        split_manifest = {
            "source_file": str(src.resolve()),
            "output_file": str(out_path.resolve()),
            "raw_rows": raw_rows,
            "subset_rows": len(rows),
            "written_rows": len(kept),
            "dropped_empty_article": dropped_empty_article,
            "dropped_empty_reference_summary": dropped_empty_reference,
            "json_decode_errors": json_decode_errors,
            "limit": lim,
            "subset_seed": split_seed,
        }
        if subset_applied:
            split_manifest["selected_indices"] = selected_indices or []
            split_manifest["selected_guids"] = selected_guids
        manifest["splits"][split_name] = split_manifest

    manifest["global_stats"] = {
        "total_raw_rows": total_raw_rows,
        "total_subset_rows": total_subset_rows,
        "total_written_rows": total_written_rows,
        "total_json_decode_errors": total_json_decode_errors,
        "total_dropped_empty_article": total_dropped_empty_article,
        "total_dropped_empty_reference_summary": total_dropped_empty_reference,
        "mean_article_char_len": mean(global_article_char_lengths) if global_article_char_lengths else 0.0,
        "mean_reference_summary_char_len": mean(global_reference_char_lengths) if global_reference_char_lengths else 0.0,
        "mean_article_sentence_count": mean(global_article_sentence_counts) if global_article_sentence_counts else 0.0,
        "mean_reference_summary_sentence_count": (
            mean(global_reference_sentence_counts) if global_reference_sentence_counts else 0.0
        ),
    }

    manifest_path = args.out_dir / "dataset_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Wrote manifest: {manifest_path}")
    for name, info in manifest["splits"].items():
        print(f"{name}: {info['written_rows']} rows -> {info['output_file']}")


if __name__ == "__main__":
    main()
