// Scroll rail logic and jump to top

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

/* Card creation from window.INFLUENCERS */

function createCard(inf) {
    const article = document.createElement("article");
    article.className = "card";

    const filterTags = Array.isArray(inf.filterTags) ? inf.filterTags : [];
    if (filterTags.length) {
        article.dataset.filterTags = filterTags.join(",");
    }

    // top tags on the card
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

    // image
    const imageWrap = document.createElement("div");
    imageWrap.className = "card-image";
    const img = document.createElement("img");
    const seed = inf.imageSeed || inf.handle || Math.random().toString(36).slice(2);
    img.src = "https://picsum.photos/seed/" + encodeURIComponent(seed) + "/400/260";
    const handleForAlt = inf.handle && !inf.handle.startsWith("@")
        ? "@" + inf.handle
        : (inf.handle || "influencer");
    img.alt = handleForAlt + " photo";
    imageWrap.appendChild(img);
    article.appendChild(imageWrap);

    // footer
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

/* Render influencers into the grids
   Assumes Python has already mapped topCategory to one of:
   ENTERTAINMENT, COMEDY, SPORTS_FITNESS, BEAUTY_FASHION,
   GAMING_TECHNOLOGY, COOKING, PARENTING, CELEBRITIES, LIFESTYLE.
*/

(function renderInfluencers() {
    if (!window.INFLUENCERS || !Array.isArray(window.INFLUENCERS)) {
        return;
    }

    const byCategory = {};

    window.INFLUENCERS.forEach(inf => {
        const catKey = inf.topCategory || "LIFESTYLE";
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
        const catKey = grid.getAttribute("data-category");
        const list = byCategory[catKey] || [];
        list.forEach(inf => {
            const card = createCard(inf);
            grid.appendChild(card);
        });
    });
})();

/* Tag based filtering inside each category */

sections.forEach(section => {
    const tagPills = section.querySelectorAll(".tag-pill[data-tag]");
    const cards = section.querySelectorAll(".cards-grid .card");

    if (!tagPills.length || !cards.length) {
        return;
    }

    tagPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const tag = pill.dataset.tag;
            const isActive = pill.classList.contains("active");

            tagPills.forEach(p => p.classList.remove("active"));
            cards.forEach(card => card.classList.remove("is-hidden"));

            if (!isActive) {
                pill.classList.add("active");

                cards.forEach(card => {
                    const raw = card.dataset.filterTags || "";
                    const cardTags = raw.split(",")
                        .map(t => t.trim())
                        .filter(t => t.length > 0);

                    if (!cardTags.includes(tag)) {
                        card.classList.add("is-hidden");
                    }
                });
            }
        });
    });
});
