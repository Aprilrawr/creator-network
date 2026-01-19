import json
import math
import os
import re
import hashlib
import pandas as pd

# -------------------------------------
# CONFIG
# -------------------------------------
EXCEL_FILE = "AllInfluencers.xlsx"
SHEET_NAME = "ALL"

OUTPUT_JS = "influencers-data.js"
TAG_CSS_OUTPUT = "tag-variables.css"
IGNORE_FILE = "ignore_list.txt"   # optional external blocklist

# If you want ONE identical placeholder for all missing photos:
PLACEHOLDER_IMAGE = "assets/creators/placeholder.jpg"

# -------------------------------------
# Helpers
# -------------------------------------
def normalize_text(v):
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()

def get_col(df, preferred_name):
    # Makes column matching robust, even if Excel has trailing spaces
    cols = {str(c).strip().lower(): c for c in df.columns}
    key = preferred_name.strip().lower()
    return cols.get(key, preferred_name)

def slugify_tag(tag: str) -> str:
    s = tag.strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s

def color_from_text(text: str) -> str:
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    hue = int(h[0:4], 16) % 360
    sat = 70
    lig = 55

    # HSL to RGB
    import colorsys
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, lig / 100.0, sat / 100.0)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def readable_text_color(bg_hex: str) -> str:
    # Simple luminance check for readable text
    bg_hex = bg_hex.lstrip("#")
    r = int(bg_hex[0:2], 16)
    g = int(bg_hex[2:4], 16)
    b = int(bg_hex[4:6], 16)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    return "#111827" if luminance > 170 else "#ffffff"

def parse_followers_sort(val):
    # Handles: 2.5M, 257K, 300000, 300,000
    s = normalize_text(val).replace(",", "")
    if not s:
        return 0

    m = re.match(r"^(\d+(?:\.\d+)?)\s*([kKmM]?)$", s)
    if m:
        num = float(m.group(1))
        suf = m.group(2).lower()
        if suf == "m":
            return int(num * 1_000_000)
        if suf == "k":
            return int(num * 1_000)
        return int(num)

    try:
        return int(float(s))
    except Exception:
        return 0

def build_tags(raw):
    # Comma or slash separated, keeps original labels
    s = normalize_text(raw)
    if not s:
        return []
    s = s.replace("/", ",")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    out = []
    for t in parts:
        if t and t not in out:
            out.append(t)
    return out

# -------------------------------------
# Category mapping (tags do NOT affect this)
# -------------------------------------
def map_top_category(category_raw):
    cat = normalize_text(category_raw).lower()
    if not cat:
        return "LIFESTYLE"

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
    ignore = set()
    if os.path.exists(IGNORE_FILE):
        with open(IGNORE_FILE, "r", encoding="utf8") as f:
            for line in f:
                name = line.strip()
                if name:
                    ignore.add(name.lower())

    if not os.path.exists(EXCEL_FILE):
        raise SystemExit(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # Robust column picks
    col_total = get_col(df, "Total Followers")
    col_handle = get_col(df, "Content Creator")
    col_sort = get_col(df, "Sort")
    col_category = get_col(df, "Category")
    col_photo = get_col(df, "Photo")
    col_instagram = get_col(df, "Instagram")
    col_tiktok = get_col(df, "Tiktok")
    col_youtube = get_col(df, "Youtube")
    col_tags = get_col(df, "Tags")

    influencers = []
    all_tag_labels_by_slug = {}  # slug -> preferred label

    for _, row in df.iterrows():
        handle = normalize_text(row.get(col_handle))
        if not handle:
            continue

        if handle.lower() in ignore:
            continue

        followers_display = normalize_text(row.get(col_total))
        followers_sort = parse_followers_sort(row.get(col_sort))

        top_category = map_top_category(row.get(col_category))

        insta = normalize_text(row.get(col_instagram))
        tiktok = normalize_text(row.get(col_tiktok))
        youtube = normalize_text(row.get(col_youtube))

        # Photo: accept relative site paths like assets/creators/x.jpg
        photo_url = normalize_text(row.get(col_photo))
        if not photo_url:
            photo_url = PLACEHOLDER_IMAGE

        tags = build_tags(row.get(col_tags))

        # Slugs for filtering and styling, derived only from Tags column
        filter_slugs = []
        for label in tags:
            slug = slugify_tag(label)
            if not slug:
                continue
            if slug not in all_tag_labels_by_slug:
                all_tag_labels_by_slug[slug] = label
            if slug not in filter_slugs:
                filter_slugs.append(slug)

        influencers.append({
            "handle": handle,
            "followersDisplay": followers_display,
            "followersSort": followers_sort,
            "topCategory": top_category,
            "tags": tags,                 # original labels for display
            "filterTags": filter_slugs,   # slugs for filtering/styling
            "imageUrl": photo_url,
            "links": {
                "instagram": insta,
                "tiktok": tiktok,
                "youtube": youtube,
            }
        })

    # Write influencers-data.js
    js_content = "window.INFLUENCERS = " + json.dumps(influencers, ensure_ascii=False, indent=2) + ";\n"
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Written {len(influencers)} influencers → {OUTPUT_JS}")

    # Write tag-variables.css (used by BOTH pills and overlay chips)
    css_lines = [":root {"]

    for slug, label in sorted(all_tag_labels_by_slug.items(), key=lambda x: x[0]):
        bg = color_from_text(slug)
        text = readable_text_color(bg)
        css_lines.append(f"  --tag-{slug}-bg: {bg};")
        css_lines.append(f"  --tag-{slug}-text: {text};")

    css_lines.append("}")

   css_lines.append("")
    css_lines.append("/* Auto styling for BOTH filter pills and card overlay chips */")
for slug in sorted(all_tag_labels_by_slug.keys()):
    css_lines.append(
        f'.tag-pill[data-tag="{slug}"], .card-tag-chip[data-tag="{slug}"] {{ '
        f'background: var(--tag-{slug}-bg) !important; '
        f'color: var(--tag-{slug}-text) !important; '
        f'border-color: transparent !important; }}'
    )


    with open(TAG_CSS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(css_lines))

    print(f"Generated {len(all_tag_labels_by_slug)} tag styles → {TAG_CSS_OUTPUT}")

if __name__ == "__main__":
    main()
