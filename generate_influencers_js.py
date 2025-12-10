import json
import math
import os

import pandas as pd


# Adjust file names if needed
EXCEL_FILE = "Influencers .xlsx"  # rename here if your file name is different
SHEET_NAME = "Sheet3"
OUTPUT_JS = "influencers-data.js"


def normalize_text(s):
    if not isinstance(s, str):
        return None
    return s.strip()


def build_tags(category_raw):
    """Return a list of tag labels for the card based on the Category column."""
    if not isinstance(category_raw, str):
        return []

    cat = category_raw.strip()
    base = cat.replace(" / ", "/")
    parts = [p.strip() for p in base.split("/") if p.strip()]

    tags = []
    for p in parts:
        pl = p.lower()
        if "lifestyle" in pl:
            tags.append("Lifestyle")
        elif "beauty" in pl:
            tags.append("Beauty")
        elif "fashion" in pl:
            tags.append("Fashion")
        elif "parent" in pl:
            tags.append("Parenting")
        elif "make up" in pl or "makeup" in pl:
            tags.append("Makeup")
        elif "tv host" in pl or "tv hostess" in pl:
            tags.append("TV Host")
        elif "actress" in pl:
            tags.append("Actress")
        elif "celebrity" in pl:
            tags.append("Celebrity")
        elif "digital creator" in pl:
            tags.append("Digital Creator")
        elif "content creator" in pl:
            tags.append("Content Creator")
        else:
            tags.append(p.strip())

    # deduplicate while keeping order
    out = []
    for t in tags:
        if t and t not in out:
            out.append(t)
    return out


def map_top_category(category_raw):
    """
    Map the Excel Category string to one of the fixed site categories:
    ENT, COMEDY, SPORTS_FITNESS, BEAUTY_FASHION, GAMING_TECHNOLOGY,
    COOKING, PARENTING, CELEBRITIES, LIFESTYLE.
    Works even if Category is just 'Sports', 'Fitness', 'Gaming', 'Technology', etc.
    """
    if not isinstance(category_raw, str):
        return "LIFESTYLE"

    cat_lower = category_raw.strip().lower()

    def has_any(*words):
        return any(w in cat_lower for w in words)

    # Parenting first, since "family lifestyle" could exist
    if has_any("parent", "mom", "mum", "dad", "family", "kids", "baby"):
        return "PARENTING"

    # Beauty / fashion
    if has_any("beauty", "fashion", "make up", "makeup", "hair", "nails"):
        return "BEAUTY_FASHION"

    # Sports and fitness
    if has_any("sport", "sports", "fitness", "fit ", "gym", "athlete", "trainer", "coach"):
        return "SPORTS_FITNESS"

    # Gaming / technology
    if has_any("gaming", "gamer", "game", "stream", "twitch", "esport", "tech", "technology"):
        return "GAMING_TECHNOLOGY"

    # Cooking / food
    if has_any("chef", "cook", "cooking", "recipe", "food", "restaurant", "baker", "baking"):
        return "COOKING"

    # Celebrities, high profile
    if has_any("tv host", "tv hostess", "anchor", "actress", "actor", "celebrity",
               "singer", "artist", "musician", "band"):
        return "CELEBRITIES"

    # Comedy
    if has_any("comed", "stand up", "stand-up", "sketch", "satire"):
        return "COMEDY"

    # Entertainment / generic creators
    if has_any("entertainment", "entertainer", "digital creator", "content creator",
               "media", "show", "radio host"):
        return "ENTERTAINMENT"

    # Default bucket
    return "LIFESTYLE"


def main():
    if not os.path.exists(EXCEL_FILE):
        raise SystemExit(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Use exact column names from your sheet
    col_total = "Total Followers "
    col_sort = "Sort"
    col_handle = "Content Creator "
    col_instagram = "Instagram "
    col_tiktok = "Tiktok "
    col_youtube = "Youtube "
    col_category = "Category "

    influencers = []

    for idx, row in df.iterrows():
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
        tags = build_tags(cat_raw)
        top_category = map_top_category(cat_raw)

        insta = normalize_text(row.get(col_instagram))
        tiktok = normalize_text(row.get(col_tiktok))
        youtube = normalize_text(row.get(col_youtube))

        inf = {
            "handle": handle,  # without @, renderer adds @ for display
            "followersDisplay": followers_display,
            "followersSort": followers_sort,
            "topCategory": top_category,
            "tags": tags,
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

    print(f"Written {len(influencers)} influencers to {OUTPUT_JS}")


if __name__ == "__main__":
    main()
