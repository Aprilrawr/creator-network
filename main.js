// ----------------------------------------------------
// Utilities
// ----------------------------------------------------
function slugifyTag(label) {
  if (!label) return "";
  return label
    .toString()
    .trim()
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function normalizeCategory(value) {
  if (!value) return "LIFESTYLE";

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

  if (mapDirect[upper]) return mapDirect[upper];

  const hasAny = (...words) => words.some(w => lower.includes(w));

  if (hasAny("parent", "mom", "mum", "dad", "family", "kids", "baby")) return "PARENTING";
  if (hasAny("beauty", "fashion", "make up", "makeup", "hair", "nails", "skincare", "skin")) return "BEAUTY_FASHION";
  if (hasAny("sport", "sports", "fitness", "gym", "athlete", "trainer", "coach")) return "SPORTS_FITNESS";
  if (hasAny("gaming", "gamer", "game", "stream", "twitch", "esport", "tech", "technology")) return "GAMING_TECHNOLOGY";
  if (hasAny("chef", "cook", "cooking", "recipe", "food", "restaurant", "baker", "baking")) return "COOKING";
  if (hasAny("tv host", "tv hostess", "anchor", "actress", "actor", "celebrity", "singer", "artist", "musician", "band")) return "CELEBRITIES";
  if (hasAny("comed", "stand up", "stand-up", "sketch", "satire")) return "COMEDY";
  if (hasAny("entertainment", "entertainer", "digital creator", "content creator", "media", "show", "radio host")) return "ENTERTAINMENT";

  return "LIFESTYLE";
}

function titleCase(s) {
  if (!s) return "";
  return s
    .toString()
    .trim()
    .split(/\s+/)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// ----------------------------------------------------
// Scroll rail logic and jump to top
// ----------------------------------------------------
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
      if (label) pill.removeChild(label);
    }
  });
};

const observer = new IntersectionObserver(
  (entries) => {
    let best = null;

    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      if (!best || entry.intersectionRatio > best.intersectionRatio) {
        best = entry;
      }
    });

    if (best) {
      setActiveCategory(best.target.id);
    }
  },
  { threshold: [0.25, 0.4, 0.55, 0.7] }
);

sections.forEach(section => observer.observe(section));

pills.forEach(pill => {
  pill.addEventListener("click", () => {
    const targetId = pill.getAttribute("data-target");
    const target = document.getElementById(targetId);
    if (target) target.scrollIntoView({ behavior: "smooth" });
  });
});

const handleScroll = () => {
  if (!scrollTopBtn) return;
  if (window.scrollY > 300) scrollTopBtn.classList.add("visible");
  else scrollTopBtn.classList.remove("visible");
};

window.addEventListener("scroll", handleScroll);
handleScroll();

if (scrollTopBtn) {
  scrollTopBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// ----------------------------------------------------
// Card creation
// ----------------------------------------------------
const PLACEHOLDER_IMAGE = "assets/creators/placeholder.jpg";

function createCard(inf) {
  const article = document.createElement("article");
  article.className = "card";

  const filterTags = Array.isArray(inf.filterTags) ? inf.filterTags : [];
  if (filterTags.length) {
    article.dataset.filterTags = filterTags.join(",");
  }

  // Overlay tags (chips)
  const tagsDiv = document.createElement("div");
  tagsDiv.className = "card-tags";

  const tagLabels = Array.isArray(inf.tags) ? inf.tags : [];
  tagLabels.forEach(label => {
    const slug = slugifyTag(label);
    if (!slug) return;

    const span = document.createElement("span");
    span.className = "card-tag-chip";
    span.dataset.tag = slug;
    span.textContent = label;
    tagsDiv.appendChild(span);
  });

  if (tagsDiv.children.length > 0) article.appendChild(tagsDiv);

  // Image
  const imageWrap = document.createElement("div");
  imageWrap.className = "card-image";

  const img = document.createElement("img");
  const desired = (inf.imageUrl && inf.imageUrl.toString().trim()) ? inf.imageUrl.toString().trim() : PLACEHOLDER_IMAGE;
  img.src = desired;

  img.onerror = () => {
    if (img.src.includes(PLACEHOLDER_IMAGE)) return;
    img.src = PLACEHOLDER_IMAGE;
  };

  const handleForAlt = inf.handle && !inf.handle.startsWith("@")
    ? "@" + inf.handle
    : (inf.handle || "influencer");

  img.alt = handleForAlt + " photo";
  imageWrap.appendChild(img);
  article.appendChild(imageWrap);

  // Footer
  const footer = document.createElement("div");
  footer.className = "card-footer";

  const followersDiv = document.createElement("div");
  followersDiv.className = "followers-pill";
  followersDiv.textContent = inf.followersDisplay || "";
  footer.appendChild(followersDiv);

  const handleP = document.createElement("p");
  handleP.className = "handle";
  handleP.textContent = inf.handle
    ? (inf.handle.startsWith("@") ? inf.handle : "@" + inf.handle)
    : "";
  footer.appendChild(handleP);

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
      if (!url) return;

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
    });
  }

  if (ul.children.length > 0) footer.appendChild(ul);

  article.appendChild(footer);
  return article;
}

// ----------------------------------------------------
// Render influencers into grids
// ----------------------------------------------------
function renderInfluencers() {
  if (!window.INFLUENCERS || !Array.isArray(window.INFLUENCERS)) return;

  const byCategory = {};
  window.INFLUENCERS.forEach(inf => {
    const catKey = normalizeCategory(inf.topCategory || inf.category || "");
    if (!byCategory[catKey]) byCategory[catKey] = [];
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

    grid.innerHTML = "";
    list.forEach(inf => grid.appendChild(createCard(inf)));
  });
}

// ----------------------------------------------------
// Build filter pills dynamically per category
// ----------------------------------------------------
function buildFilterPills() {
  if (!window.INFLUENCERS || !Array.isArray(window.INFLUENCERS)) return;

  // Build tag sets per category
  const tagsByCategory = {};
  window.INFLUENCERS.forEach(inf => {
    const catKey = normalizeCategory(inf.topCategory || "");
    const labels = Array.isArray(inf.tags) ? inf.tags : [];
    if (!labels.length) return;

    if (!tagsByCategory[catKey]) tagsByCategory[catKey] = new Map(); // slug -> label
    labels.forEach(label => {
      const slug = slugifyTag(label);
      if (!slug) return;
      if (!tagsByCategory[catKey].has(slug)) {
        tagsByCategory[catKey].set(slug, label);
      }
    });
  });

  // For each section, replace its tag row with pills for that category
  document.querySelectorAll("section.category").forEach(section => {
    const grid = section.querySelector(".cards-grid[data-category]");
    const row = section.querySelector(".category-tag-row");
    if (!grid || !row) return;

    const catAttr = grid.getAttribute("data-category") || "";
    const catKey = normalizeCategory(catAttr);

    row.innerHTML = "";

    const map = tagsByCategory[catKey];
    if (!map || map.size === 0) {
      // No tags, show nothing (per your rule)
      return;
    }

    const entries = Array.from(map.entries())
      .sort((a, b) => a[1].localeCompare(b[1]));

    entries.forEach(([slug, label]) => {
      const pill = document.createElement("span");
      pill.className = "tag-pill";
      pill.dataset.tag = slug;
      pill.textContent = label;
      row.appendChild(pill);
    });
  });
}

// ----------------------------------------------------
// Filter logic per category section
// ----------------------------------------------------
function wireTagFiltering() {
  document.querySelectorAll("section.category").forEach(section => {
    const tagPills = Array.from(section.querySelectorAll(".tag-pill[data-tag]"));
    const cards = Array.from(section.querySelectorAll(".cards-grid .card"));

    if (!tagPills.length || !cards.length) return;

    tagPills.forEach(pill => {
      pill.addEventListener("click", () => {
        const tag = pill.dataset.tag;
        const isActive = pill.classList.contains("active");

        tagPills.forEach(p => p.classList.remove("active"));
        cards.forEach(card => card.classList.remove("is-hidden"));

        if (isActive) return;

        pill.classList.add("active");

        cards.forEach(card => {
          const raw = card.dataset.filterTags || "";
          const cardTags = raw.split(",").map(t => t.trim()).filter(Boolean);
          if (!cardTags.includes(tag)) card.classList.add("is-hidden");
        });
      });
    });
  });
}

// ----------------------------------------------------
// Boot
// ----------------------------------------------------
(function boot() {
  renderInfluencers();
  buildFilterPills();
  wireTagFiltering();
})();
