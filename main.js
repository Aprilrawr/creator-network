// ===============================
// Scroll rail logic and Jump-to-top
// ===============================

const sections = document.querySelectorAll("section.category");
const pills = document.querySelectorAll(".cat-pill");
const scrollTopBtn = document.querySelector(".scroll-top-btn");

const setActiveCategory = (id) => {
    pills.forEach(pill => {
        const target = pill.getAttribute("data-target");
        if (target === id) {
            pill.classList.add("active");
            pill.classList.remove("inactive");

            if (!pill.querySelector(".cat-pill-label")) {
                const label = document.createElement("span");
                label.className = "cat-pill-label";
                const labelText = pill.getAttribute("data-label") || id.replace("-", " ").toUpperCase();
                label.textContent = labelText;
                pill.appendChild(label);
            }
        } else {
            pill.classList.remove("active");
            pill.classList.add("inactive");
            const label = pill.querySelector(".cat-pill-label");
            if (label) {
                pill.removeChild(label);
            }
        }
    });
};

const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                setActiveCategory(id);
            }
        });
    },
    {
        threshold: 0.55
    }
);

sections.forEach(section => observer.observe(section));

pills.forEach(pill => {
    pill.addEventListener("click", () => {
        const targetId = pill.getAttribute("data-target");
        const target = document.getElementById(targetId);
        if (target) {
            target.scrollIntoView({ behavior: "smooth" });
        }
    });
});

const handleScroll = () => {
    if (!scrollTopBtn) {
        return;
    }

    if (window.scrollY > 300) {
        scrollTopBtn.classList.add("visible");
    } else {
        scrollTopBtn.classList.remove("visible");
    }
};

window.addEventListener("scroll", handleScroll);
handleScroll();

if (scrollTopBtn) {
    scrollTopBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
}

// ===============================
// Category normalization
// ===============================

function normalizeCategory(value) {
    if (!value) {
        return "LIFESTYLE";
    }

    const raw = value.toString().trim();
    const upper = raw.toUpperCase();
    const lower = raw.toLowerCase();

    const mapDirect = {
        "ENTERTAINMENT": "ENTERTAINMENT",
        "COMEDY": "COMEDY",
        "SPORTS_FITNESS": "SPORTS_FITNESS",
        "BEAUTY_FASHION": "BEAUTY_FASHION",
        "GAMING_TECHNOLOGY": "GAMING_TECHNOLOGY",
        "COOKING": "COOKING",
        "PARENTING": "PARENTING",
        "CELEBRITIES": "CELEBRITIES",
        "LIFESTYLE": "LIFESTYLE"
    };

    if (mapDirect[upper]) {
        return mapDirect[upper];
    }

    const hasAny = (...words) => words.some(w => lower.includes(w));

    if (hasAny("parent", "mom", "mum", "dad", "family", "kids", "baby")) {
        return "PARENTING";
    }

    if (hasAny("beauty", "fashion", "make up", "makeup", "hair", "nails")) {
        return "BEAUTY_FASHION";
    }

    if (hasAny("sport", "sports", "fitness", "fit ", "gym", "athlete", "trainer", "coach")) {
        return "SPORTS_FITNESS";
    }

    if (hasAny("gaming", "gamer", "game", "stream", "twitch", "esport", "tech", "technology")) {
        return "GAMING_TECHNOLOGY";
    }

    if (hasAny("chef", "cook", "cooking", "recipe", "food", "restaurant", "baker", "baking")) {
        return "COOKING";
    }

    if (hasAny("tv host", "tv hostess", "anchor", "actress", "actor", "celebrity",
               "singer", "artist", "musician", "band")) {
        return "CELEBRITIES";
    }

    if (hasAny("comed", "stand up", "stand-up", "sketch", "satire")) {
        return "COMEDY";
    }

    if (hasAny("entertainment", "entertainer", "digital creator", "content creator",
               "media", "show", "radio host")) {
        return "ENTERTAINMENT";
    }

    return "LIFESTYLE";
}

// Utility to slugify tag labels consistently
function slugifyTag(text) {
    if (!text) {
        return "";
    }
    return text
        .toString()
        .trim()
        .toLowerCase()
        .replace(/&/g, "and")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

// ===============================
// Card creation
// ===============================

function createCard(inf) {
    const article = document.createElement("article");
    article.className = "card";

    const filterTags = Array.isArray(inf.filterTags) ? inf.filterTags : [];
    if (filterTags.length) {
        article.dataset.filterTags = filterTags.join(",");
    }

    // Tags at top
    const tagsDiv = document.createElement("div");
    tagsDiv.className = "card-tags";
    (inf.tags || []).forEach(tag => {
        const span = document.createElement("span");
        span.className = "card-tag-chip";
        const lower = tag.toLowerCase();
        if (lower === "actor") {
            span.classList.add("actor");
        }
        if (lower.includes("host")) {
            span.classList.add("host");
        }
        span.textContent = tag;
        tagsDiv.appendChild(span);
    });
    article.appendChild(tagsDiv);

    // Image with fallback to placeholder
    const imageWrap = document.createElement("div");
    imageWrap.className = "card-image";
    const img = document.createElement("img");

    const hasPhotoUrl =
        typeof inf.photoUrl === "string" &&
        inf.photoUrl.trim().length > 0;

    if (hasPhotoUrl) {
        img.src = inf.photoUrl.trim();
    } else {
        const seed = inf.imageSeed || inf.handle || Math.random().toString(36).slice(2);
        img.src = "https://picsum.photos/seed/" + encodeURIComponent(seed) + "/400/260";
    }

    const handleForAlt = inf.handle && !inf.handle.startsWith("@")
        ? "@" + inf.handle
        : (inf.handle || "influencer");
    img.alt = handleForAlt + " photo";

    imageWrap.appendChild(img);
    article.appendChild(imageWrap);

    // Footer
    const footer = document.createElement("div");
    footer.className = "card-footer";

    const handleP = document.createElement("p");
    handleP.className = "handle";
    if (inf.handle) {
        handleP.textContent = inf.handle.startsWith("@") ? inf.handle : "@" + inf.handle;
    } else {
        handleP.textContent = "";
    }
    footer.appendChild(handleP);

    const followersDiv = document.createElement("div");
    followersDiv.className = "followers-pill";
    followersDiv.textContent = inf.followersDisplay || "";
    footer.appendChild(followersDiv);

    const ul = document.createElement("ul");
    ul.className = "sci";

    const platforms = [
        { key: "instagram", icon: "fa-brands fa-instagram" },
        { key: "tiktok", icon: "fa-brands fa-tiktok" },
        { key: "youtube", icon: "fa-brands fa-youtube" }
    ];

    let i = 1;
    if (inf.links) {
        platforms.forEach(p => {
            const url = inf.links[p.key];
            if (url) {
                const li = document.createElement("li");
                li.style.setProperty("--i", String(i));
                const a = document.createElement("a");
                a.href = url;
                a.target = "_blank";
                a.rel = "noopener";
                const icon = document.createElement("i");
                icon.className = p.icon;
                icon.setAttribute("aria-hidden", "true");
                a.appendChild(icon);
                li.appendChild(a);
                ul.appendChild(li);
                i += 1;
            }
        });
    }

    if (ul.children.length > 0) {
        footer.appendChild(ul);
    }

    article.appendChild(footer);
    return article;
}

// ===============================
// Render influencers into grids
// ===============================

(function renderInfluencers() {
    if (!window.INFLUENCERS || !Array.isArray(window.INFLUENCERS)) {
        return;
    }

    const byCategory = {};

    window.INFLUENCERS.forEach(inf => {
        const catKey = normalizeCategory(inf.topCategory || inf.category || "");
        if (!byCategory[catKey]) {
            byCategory[catKey] = [];
        }
        byCategory[catKey].push(inf);
    });

    Object.keys(byCategory).forEach(cat => {
        byCategory[cat].sort((a, b) => {
            const sa = typeof a.followersSort === "number" ? a.followersSort : 0;
            const sb = typeof b.followersSort === "number" ? b.followersSort : 0;
            return sb - sa;
        });
    });

    document.querySelectorAll(".cards-grid[data-category]").forEach(grid => {
        const catAttr = grid.getAttribute("data-category") || "";
        const catKey = normalizeCategory(catAttr);
        const list = byCategory[catKey] || [];
        list.forEach(inf => {
            const card = createCard(inf);
            grid.appendChild(card);
        });
    });
})();

// ===============================
// Tag-based filtering per category
// ===============================

sections.forEach(section => {
    const tagPills = section.querySelectorAll(".tag-pill");
    const grid = section.querySelector(".cards-grid");

    if (!tagPills.length || !grid) {
        return;
    }

    tagPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const tagSlug = slugifyTag(pill.dataset.tag || pill.textContent);
            const isActive = pill.classList.contains("active");

            const cards = grid.querySelectorAll(".card");

            // reset all pills and cards
            tagPills.forEach(p => p.classList.remove("active"));
            cards.forEach(card => card.classList.remove("is-hidden"));

            if (!isActive && tagSlug) {
                pill.classList.add("active");

                cards.forEach(card => {
                    const raw = card.dataset.filterTags || "";
                    const cardTags = raw
                        .split(",")
                        .map(t => slugifyTag(t))
                        .filter(t => t.length > 0);

                    if (!cardTags.includes(tagSlug)) {
                        card.classList.add("is-hidden");
                    }
                });
            }
        });
    });
});
