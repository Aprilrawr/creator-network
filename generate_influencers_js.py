import json
import math
import os
import hashlib
import re
import pandas as pd

# -------------------------------------
# CONFIG
# -------------------------------------
EXCEL_FILE = "AllInfluencers.xlsx"
SHEET_NAME = "ALL"

OUTPUT_JS = "influencers-data.js"
TAG_CSS_OUTPUT = "tag-variables.css"
IGNORE_FILE = "ignore_list.txt"   # optional external blocklist

# If Photo column is empty, use this pattern:
DEFAULT_PHOTO_BASE = "assets/creators"   # relative to site root
DEFAULT_PHOTO_EXT = ".jpg"


# -------------------------------------
# Helpers
# -------------------------------------
def normalize_text(s):
    if s is None:
        return None
    if isinstance(s, float) and math.isnan(s):
        return None
    return str(s).strip()


def slugify(tag):
    tag = tag.strip().lower()
    tag = re.sub(r"\s+", "-", tag)
    tag = tag.replace("/", "-")
    tag = re.sub(r"[^a-z0-9\-]", "", tag)
    tag = re.sub(r"-{2,}", "-", tag).strip("-")
    return tag


def color_from_text(text):
    """Generate stable color from tag text via MD5 hash."""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_followers(val):
    """
    Convert strings like:
    '1.2M', '1,2M', '320K', '300,000', '300000', 300000
    into sortable integers.
    """
    if val is None:
        return 0
    if isinstance(val, float) and math.isnan(val):
        return 0

    s = str(val).strip()

    # handle european decimal comma: 1,2M
    s = s.replace(" ", "")
    s = s.replace(",", ".") if ("M" in s.upper() or "K" in s.upper()) else s
    s = s.replace(",", "")  # remaining commas as thousand separators

    m = re.match(r"^([0-9]*\.?[0-9]+)([MmKk])?$", s)
    if not m:
        # last attempt: strip non numeric
        s2 = re.sub(r"[^0-9\.]", "", s)
        try:
            return int(float(s2))
        except:
            return 0

    num = float(m.group(1))
    suffix = m.group(2)

    if suffix in ("M", "m"):
        return int(num * 1_000_000)
    if suffix in ("K", "k"):
        return int(num * 1_000)

    return int(num)


def looks_like_url_or_path(v: str) -> bool:
    if not v:
        return False
    low = v.lower()
    if low.startswith(("http://", "https://")):
        return True
    # treat these as valid paths:
    if low.startswith(("assets/", "./", "../")):
        return True
    # also accept simple relative filenames like "name.jpg"
    if "/" in v or "\\" in v:
        return True
    if low.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return True
    return False


def normalize_slashes(v: str) -> str:
    # Convert windows backslashes to web slashes
    return v.replace("\\", "/")


# -------------------------------------
# Tag extraction
# -------------------------------------
def build_tags(raw):
    """
    Extract tags from Excel row. Comma or slash delimited.
    If there are NO tags, return [].
    """
    raw = normalize_text(raw)
    if not raw:
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
    category_raw = normalize_text(category_raw)
    if not category_raw:
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

    if not os.path.exists(EXCEL_FILE):
        raise SystemExit(f"Excel file not found: {EXCEL_FILE}")

    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

    # IMPORTANT: normalize column names so trailing spaces don't break lookups
    df.columns = [str(c).strip() for c in df.columns]

    # Column definitions (match trimmed headers)
    col_total = "Total Followers"
    col_handle = "Content Creator"
    col_sort = "Sort"
    col_category = "Category"
    col_photo = "Photo"
    col_instagram = "Instagram"
    col_tiktok = "Tiktok"
    col_youtube = "Youtube"
    col_tags = "Tags"  # optional column with filter tags

    influencers = []
    ALL_TAGS = set()

    for _, row in df.iterrows():
        # Handle
        handle = normalize_text(row.get(col_handle))
        if not handle:
            continue

        if handle.lower() in ignore:
            continue

        # followers display
        followers_display = normalize_text(row.get(col_total)) or ""

        # sort followers
        sort_raw = row.get(col_sort)
        followers_sort = parse_followers(sort_raw)
        if followers_sort == 0:
            # fallback to Total Followers if Sort is empty or wrong
            followers_sort = parse_followers(row.get(col_total))

        # category (only from Category column, tags do not affect this)
        top_category = map_top_category(row.get(col_category))

        # links
        insta = normalize_text(row.get(col_instagram)) or ""
        tiktok = normalize_text(row.get(col_tiktok)) or ""
        youtube = normalize_text(row.get(col_youtube)) or ""

        # tags (filter + overlay), do NOT influence category
        tags = build_tags(row.get(col_tags))
        for t in tags:
            ALL_TAGS.add(t)

        # photo
        photo_value = normalize_text(row.get(col_photo)) or ""
        photo_value = normalize_slashes(photo_value)

        if photo_value and looks_like_url_or_path(photo_value):
            image_url = photo_value
        elif photo_value:
            # If they typed something like "asimina.jpg" with no folder,
            # assume it belongs in DEFAULT_PHOTO_BASE
            image_url = f"{DEFAULT_PHOTO_BASE}/{photo_value}"
        else:
            # no photo in excel, fallback to predictable local path
            image_url = f"{DEFAULT_PHOTO_BASE}/{handle}{DEFAULT_PHOTO_EXT}"

        influencers.append({
            "handle": handle,
            "followersDisplay": followers_display,
            "followersSort": followers_sort,
            "topCategory": top_category,
            "tags": tags,
            "imageUrl": image_url,
            "links": {
                "instagram": insta,
                "tiktok": tiktok,
                "youtube": youtube,
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

    for tag in sorted(ALL_TAGS, key=lambda x: x.lower()):
        slug = slugify(tag)
        bg = color_from_text(tag)
        text_color = "#ffffff"
        css_lines.append(f"  --tag-{slug}-bg: {bg};")
        css_lines.append(f"  --tag-{slug}-text: {text_color};")

    css_lines.append("}")

    css_lines.append("")
    css_lines.append("/* Auto selectors: card chip colors */")
    css_lines.append("/* Use data-tag=\"<slug>\" in your markup/JS to apply these */")
    for tag in sorted(ALL_TAGS, key=lambda x: x.lower()):
        slug = slugify(tag)
        css_lines.append(
            f'.card-tag-chip[data-tag="{slug}"] {{ background: var(--tag-{slug}-bg); color: var(--tag-{slug}-text); }}'
        )

    with open(TAG_CSS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(css_lines))

    print(f"Generated {len(ALL_TAGS)} tag styles → {TAG_CSS_OUTPUT}")


if __name__ == "__main__":
    main()
