import json
import math
import os

import pandas as pd


EXCEL_FILE = "Influencers .xlsx"   # adjust if the file name changes
SHEET_NAME = "Sheet3"
OUTPUT_JS = "influencers-data.js"

# Hard coded list of creators to ignore
# Use the exact text from the "Content Creator " column in Excel
IGNORED_HANDLES = {
    # "@valiahtz_",
    # "@gingerbread_bae",
    # "@elina_kalitzaki"

}


def normalize_text(s):
    if not isinstance(s, str):
        return None
    return s.strip()


def parse_manual_tags(raw):
    """
    Read the Tags column.
    Expected format in Excel: "TV, Radio, Stage"
    Returns: ["TV", "Radio", "Stage"]
    """
    if not isinstance(raw, str):
        return []

    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    tags = [p for p in parts if p]
    out = []
    for t in tags:
        if t not in out:
            out.append(t)
    return out


def map_top_category(category_raw):
    """
    Map the Excel Category string to one of the fixed site categories:
    ENTERTAINMENT, COMEDY, SPORTS_FITNESS, BEAUTY_FASHION,
    GAMING_TECHNOLOGY, COOKING, PARENTING, CELEBRITIES, LIFESTYLE.
    """
    if not isinstance(category_raw, str):
        return "LIFESTYLE"

    cat_lower = category_raw.lower()

    if "parent" in cat_lower:
        return "PARENTING"

    if "beauty" in cat_lower or "fashion" in cat_lower or "make up" in cat_lower or "makeup" in cat_lower:
        return "BEAUTY_FASHION"

    if "sport" in cat_lower or "fitness" in cat_lower or "athlete" in cat_lower:
        return "SPORTS_FITNESS"

    if "gamer" in cat_lower or "gaming" in cat_lower or "stream" in cat_lower or "tech" in cat_lower:
        return "GAMING_TECHNOLOGY"

    if "chef" in cat_lower or "cook" in cat_lower or "recipe" in cat_lower or "food" in cat_lower:
        return "COOKING"

    if (
        "tv host" in cat_lower
        or "tv hostess" in cat_lower
        or "actress" in cat_lower
        or "celebrity" in cat_lower
        or "singer" in cat_lower
    ):
        return "CELEBRITIES"

    if "comed" in cat_lower:
        return "COMEDY"

    if (
        "entertainment" in cat_lower
        or "digital creator" in cat_lower
        or "content creator" in cat_lower
    ):
        return "ENTERTAINMENT"

    return "LIFESTYLE"


def is_row_ignored(row, col_handle):
    """Return True if this row should be skipped based on the IGNORED_HANDLES set."""
    handle_raw = row.get(col_handle)
    handle_norm = normalize_text(handle_raw) or ""
    return handle_norm in IGNORED_HANDLES


def main():
    if not os.path.exists(EXCEL_FILE):
        raise SystemExit(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Exact column names from your sheet
    col_total = "Total Followers "
    col_sort = "Sort"
    col_handle = "Content Creator "
    col_instagram = "Instagram "
    col_tiktok = "Tiktok "
    col_youtube = "Youtube "
    col_category = "Category "
    col_tags = "Tags"   # manual tags column

    influencers = []

    for idx, row in df.iterrows():
        # skip if in hard coded ignore list
        if is_row_ignored(row, col_handle):
            continue

        handle_raw = row.get(col_handle)
        handle = normalize_text(handle_raw)
        if not handle:
            continue

        followers_display = row.get(col_total)
        if isinstance(followers_display, float) and not math.isnan(followers_display):
            followers_display = str(int(followers_display))
        followers_display = str(followers_display).strip() if followers_display is not None else ""

        sort_val = row.get(col_sort)
        try:
            followers_sort = int(sort_val) if not pd.isna(sort_val) else 0
        except Exception:
            followers_sort = 0

        cat_raw = row.get(col_category)
        top_category = map_top_category(cat_raw)

        manual_tags = parse_manual_tags(row.get(col_tags))

        insta = normalize_text(row.get(col_instagram))
        tiktok = normalize_text(row.get(col_tiktok))
        youtube = normalize_text(row.get(col_youtube))

        inf = {
            "handle": handle,  # without @, renderer adds @ for display
            "followersDisplay": followers_display,
            "followersSort": followers_sort,
            "topCategory": top_category,
            "tags": manual_tags,        # chips shown on the card
            "filterTags": manual_tags,  # used by main.js for filtering
            "imageSeed": handle,
            "links": {
                "instagram": insta or "",
                "tiktok": tiktok or "",
                "youtube": youtube or "",
            },
        }

        influencers.append(inf)

    js_content = "window.INFLUENCERS = " + json.dumps(
        influencers, ensure_ascii=False, indent=2
    ) + ";\n"

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Written {len(influencers)} influencers to " + OUTPUT_JS)


if __name__ == "__main__":
    main()
