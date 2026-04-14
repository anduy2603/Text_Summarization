from datasets import load_dataset
from pathlib import Path
import json

# nơi lưu dataset
DATA_DIR = Path("../data/raw/vietnews")
DATA_DIR.mkdir(parents=True, exist_ok=True)

print("Downloading VietNews dataset...")

dataset = load_dataset("nam194/vietnews")

for split in dataset:
    path = DATA_DIR / f"{split}.json"
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            dataset[split].to_list(),
            f,
            ensure_ascii=False,
            indent=2
        )
    
    print(f"Saved {split} -> {path}")

print("Done.")