import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


# =========================
# CONFIG
# =========================

EXCEL_FILE = "AllInfluencers.xlsx"          # your Excel file
SHEET_NAME = "ALL"                     # change if different
NAME_COLUMN = "Content Creator "          # exact column name with spacing

IMAGE_FOLDER = "assets/creators/UNSORTED"                  # folder with your jpgs (relative or absolute)
MIN_SIMILARITY = 1                   # 0 to 1 (higher means stricter matching)


# =========================
# HELPERS
# =========================

def normalize_for_match(text: str) -> str:
    """
    Turn a name into a simplified string for fuzzy matching.
    Lowercase, remove accents, keep only letters and digits.
    """
    if not isinstance(text, str):
        return ""

    text = text.strip().lower()

    # remove accents (é -> e, etc)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # keep only letters and digits
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def best_match(target_norm, candidates_norm):
    """
    Given a normalized string and a dict {norm: original_name},
    return (original_name, score) for the best fuzzy match.
    """
    best_name = None
    best_score = 0.0

    for norm_val, original in candidates_norm.items():
        if not norm_val:
            continue
        score = SequenceMatcher(None, target_norm, norm_val).ratio()
        if score > best_score:
            best_score = score
            best_name = original

    return best_name, best_score


def safe_filename(name: str) -> str:
    """
    Use the Excel name but remove characters that are illegal in filenames.
    """
    # Windows reserved characters: \ / : * ? " < > |
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()


# =========================
# MAIN
# =========================

def main():
    # 1. Load Excel and pull creator names
    if not os.path.exists(EXCEL_FILE):
        raise SystemExit(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    if NAME_COLUMN not in df.columns:
        raise SystemExit(f"Column '{NAME_COLUMN}' not found in sheet '{SHEET_NAME}'")

    names = (
        df[NAME_COLUMN]
        .dropna()
        .astype(str)
        .map(str.strip)
        .tolist()
    )

    # dict of normalized_name -> original_name
    norm_to_original = {}
    for name in names:
        norm = normalize_for_match(name)
        if norm:   # avoid empty
            norm_to_original[norm] = name

    if not norm_to_original:
        raise SystemExit("No creator names found in Excel after normalization.")

    # 2. Scan image folder
    folder = Path(IMAGE_FOLDER)
    if not folder.exists():
        raise SystemExit(f"Image folder not found: {folder}")

    jpg_files = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg"))
    if not jpg_files:
        print(f"No .jpg files found in {folder.resolve()}")
        return

    print(f"Found {len(jpg_files)} jpg files in {folder.resolve()}")
    renamed_count = 0

    for path in jpg_files:
        original_stem = path.stem

        # try to remove the " - something" suffix first (your example)
        base_part = original_stem.split("-")[0].strip()
        base_part = base_part.replace("_", " ")

        target_norm = normalize_for_match(base_part)

        if not target_norm:
            print(f"[SKIP] {path.name}: could not normalize")
            continue

        match_name, score = best_match(target_norm, norm_to_original)

        if not match_name or score < MIN_SIMILARITY:
            print(f"[SKIP] {path.name}: best score {score:.2f} below threshold")
            continue

        # build final filename
        safe_name = safe_filename(match_name)
        if not safe_name:
            print(f"[SKIP] {path.name}: resulting safe name is empty")
            continue

        ext = path.suffix.lower() or ".jpg"
        new_path = path.with_name(f"{safe_name}{ext}")

        # handle collisions (two files for same creator)
        counter = 1
        while new_path.exists() and new_path != path:
            new_path = path.with_name(f"{safe_name} - {counter}{ext}")
            counter += 1

        if new_path == path:
            print(f"[KEEP] {path.name}: already correctly named")
            continue

        path.rename(new_path)
        renamed_count += 1
        print(f"[OK]  {path.name}  ->  {new_path.name}   (score {score:.2f})")

    print(f"\nDone. Renamed {renamed_count} files.")


if __name__ == "__main__":
    main()
