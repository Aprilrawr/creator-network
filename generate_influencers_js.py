import json
import math
import os
import hashlib
import pandas as pd

# -------------------------------------
# CONFIG
# -------------------------------------
EXCEL_FILE = "Influencers .xlsx"
SHEET_NAME = "Sheet3"

OUTPUT_JS = "influencers-data.js"
TAG_CSS_OUTPUT = "tag-variables.css"
IGNORE_FILE = "ignore_list.txt"   # optional external blocklist


# -------------------------------------
# Helpers
# -------------------------------------
def normalize_text(s):
    if not isinstance(s, str):
        return None
    return s.strip()


def slugify(tag):
    return tag.lower().replace(" ", "-").replace("/", "-")


def color_from_text(text):
    """Generate stable color from tag text via MD5 hash."""
    h = hashlib.md5(text.encode()).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_followers(val):
    """Convert strings like '1.2M', '320K', '300,000', '300000' into sortable integers."""
    if val is None:
        return 0

    s = str(val).strip().replace(",", "")  # remove commas

    if s.endswith(("M", "m")):
        try:
            return int(float(s[:-1]) * 1_000_000)
        except:
            return 0

    if s.endswith(("K", "k")):
        try:
            return int(float(s[:-1]) * 1_000)
        except:
            return 0

    try:
        return int(float(s))
    except:
        return 0


# -------------------------------------
# Tag extraction
# -------------------------------------
def build_tags(raw):
    """Extract tags from Excel row. Comma or slash delimited."""
    if not isinstance(raw, str):
        return []

    raw = raw.replace("/", ",")
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    out = []

    for t in parts:
        if t and t not in out:
            out.append(t)

    return out


# -------------------------------------
# Category mapping
# -------------------------------------
def map_top_category(category_raw):
    if not isinstance(category_raw, str):
        return "LIFESTYLE"

    cat = category_raw.lower()

    if "parent" in cat:
        return "PARENTING"

    if any(x in cat for x in ["beauty", "fashion", "makeup", "make up", "hair", "skin"]):
        return "BEAUTY_FASHION"

    if any(x in cat for x in ["sport", "fitness", "gym", "athlete", "coach"]):
        return "SPORTS_FITNESS"

    if any(x in cat for x in ["game", "gamer", "gaming", "tech", "technology", "stream"]):
        return "GAMING_TECHNOLOGY"

    if any(x in cat for x in ["chef", "cook", "recipe", "food"]):
        return "COOKING"

    if any(x in cat for x in ["tv host", "actress", "actor", "celebrity", "singer"]):
        return "CELEBRITIES"

    if "comed" in cat:
        return "COMEDY"

    if "entertain" in cat or "creator" in cat:
        return "ENTERTAINMENT"

    return "LIFESTYLE"


# -------------------------------------
# Main
# -------------------------------------
def main():
    # Load ignore list (optional)
    ignore = set()
    if os.path.exists(IGNORE_FILE):
        with open(IGNORE_FILE, "r", encoding="utf8") as f:
            for line in f:
                name = line.strip()
                if name:
                    ignore.add(name.lower())

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Column definitions
    col_total = "Total Followers "
    col_handle = "Content Creator "
    col_sort = "Sort"
    col_category = "Category "
    col_photo = "Photo"  # user said they already have this column
    col_instagram = "Instagram "
    col_tiktok = "Tiktok "
    col_youtube = "Youtube "
    col_tags = "Tags"  # new optional column

    influencers = []
    ALL_TAGS = set()

    for idx, row in df.iterrows():

        # Handle
        handle_raw = row.get(col_handle)
        handle = normalize_text(handle_raw)
        if not handle:
            continue

        # Skip ignored creators
        if handle.lower() in ignore:
            continue

        # Display followers
        followers_display = str(row.get(col_total)).strip()

        # Sort followers
        followers_sort = parse_followers(row.get(col_sort))

        # Category
        cat_raw = row.get(col_category)
        top_category = map_top_category(cat_raw)

        # Links
        insta = normalize_text(row.get(col_instagram))
        tiktok = normalize_text(row.get(col_tiktok))
        youtube = normalize_text(row.get(col_youtube))

        # Photo
        photo_value = normalize_text(row.get(col_photo))
        if photo_value and not photo_value.lower().startswith(("http://", "https://")):
            # make local image path
            photo_url = f"photos/{photo_value}"
        else:
            photo_url = photo_value or ""

        # Tags coming from new Excel column
        tag_raw = row.get(col_tags)
        tags = build_tags(tag_raw)
        for t in tags:
            ALL_TAGS.add(t)

        influencers.append({
            "handle": handle,
            "followersDisplay": followers_display,
            "followersSort": followers_sort,
            "topCategory": top_category,
            "tags": tags,
            "imageUrl": photo_url,
            "links": {
                "instagram": insta or "",
                "tiktok": tiktok or "",
                "youtube": youtube or "",
            }
        })

    # Write JS file
    js_content = "window.INFLUENCERS = " + json.dumps(
        influencers, ensure_ascii=False, indent=2
    ) + ";\n"

    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Written {len(influencers)} influencers → {OUTPUT_JS}")

    # ----------------------------------
    # Generate tag color CSS
    # ----------------------------------
    css_lines = [":root {"]

    for tag in sorted(ALL_TAGS):
        slug = slugify(tag)
        bg = color_from_text(tag)
        text_color = "#ffffff"
        css_lines.append(f"  --tag-{slug}-bg: {bg};")
        css_lines.append(f"  --tag-{slug}-text: {text_color};")

    css_lines.append("}")

    # Auto selectors
    css_lines.append("\n/* Auto selectors: card chip colors */")
    for tag in sorted(ALL_TAGS):
        slug = slugify(tag)
        css_lines.append(
            f'.card-tag-chip[data-tag="{slug}"] {{ background: var(--tag-{slug}-bg); color: var(--tag-{slug}-text); }}'
        )

    with open(TAG_CSS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(css_lines))

    print(f"Generated {len(ALL_TAGS)} tag styles → {TAG_CSS_OUTPUT}")


if __name__ == "__main__":
    main()
