/**
 * Acoruss Web Application - Main JavaScript
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
  console.log("Acoruss web application loaded.");

  // Mobile drawer: close on link click
  initMobileDrawer();

  // Smooth scroll for hash links
  initSmoothScroll();

  // Scroll animations (intersection observer)
  initScrollAnimations();

  // Tab system (services, projects)
  initTabs();

  // Blog posts from Substack RSS
  initBlogLoader();

  // Currency display (USD default, KES for Kenya)
  initCurrencyDisplay();
});

/**
 * Close mobile drawer when a link inside it is clicked.
 */
function initMobileDrawer() {
  const drawer = document.getElementById("mobile-drawer");
  if (!drawer) return;

  const drawerLinks = document.querySelectorAll(
    ".drawer-side a, .drawer-side button"
  );
  drawerLinks.forEach((link) => {
    link.addEventListener("click", () => {
      drawer.checked = false;
    });
  });
}

/**
 * Smooth scroll for anchor links.
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.replaceState(null, "", targetId);
      }
    });
  });
}

/**
 * Scroll-triggered fade-in animations via IntersectionObserver.
 */
function initScrollAnimations() {
  const animatedElements = document.querySelectorAll("[data-animate]");
  if (!animatedElements.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-fade-in-up");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  animatedElements.forEach((el) => observer.observe(el));
}

/**
 * Generic tab system for service-tab / project-tab pattern.
 * Reads data-tab attribute to match tab → panel.
 * Also handles hash-based tab activation on page load.
 */
function initTabs() {
  const tabGroups = [
    { tabSelector: ".service-tab", panelSelector: ".service-panel" },
    { tabSelector: ".project-tab", panelSelector: ".project-panel" },
  ];

  tabGroups.forEach(({ tabSelector, panelSelector }) => {
    const tabs = document.querySelectorAll(tabSelector);
    const panels = document.querySelectorAll(panelSelector);
    if (!tabs.length || !panels.length) return;

    // Hash-based activation on load
    const hash = window.location.hash.substring(1);
    if (hash) {
      const targetPanel = document.getElementById(hash);
      if (targetPanel && targetPanel.classList.contains(panelSelector.substring(1))) {
        panels.forEach((p) => p.classList.add("hidden"));
        targetPanel.classList.remove("hidden");
        tabs.forEach((t) => {
          t.classList.remove("tab-active");
          t.setAttribute("aria-selected", "false");
        });
        const activeTab = document.querySelector(`[data-tab="${hash}"]`);
        if (activeTab) {
          activeTab.classList.add("tab-active");
          activeTab.setAttribute("aria-selected", "true");
        }
      }
    }

    // Click handlers
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.tab;
        panels.forEach((p) => p.classList.add("hidden"));
        const targetPanel = document.getElementById(target);
        if (targetPanel) targetPanel.classList.remove("hidden");
        tabs.forEach((t) => {
          t.classList.remove("tab-active");
          t.setAttribute("aria-selected", "false");
        });
        tab.classList.add("tab-active");
        tab.setAttribute("aria-selected", "true");
        history.replaceState(null, "", "#" + target);
      });
    });
  });
}

/**
 * Load blog posts from Substack RSS feed via server-side proxy.
 * Falls back to a "Visit our blog" card on error.
 */
function initBlogLoader() {
  const container = document.getElementById("blog-posts");
  if (!container) return;

  fetch("/api/blog-feed/")
    .then((res) => {
      if (!res.ok) throw new Error("Feed fetch failed");
      return res.json();
    })
    .then((posts) => {
      if (!posts.length) {
        container.innerHTML = renderFallbackCard();
        return;
      }
      container.innerHTML = posts
        .slice(0, 3)
        .map((post, i) => renderBlogCard(post, i))
        .join("");
    })
    .catch(() => {
      container.innerHTML = renderFallbackCard();
    });
}

function renderBlogCard(post, index) {
  const date = new Date(post.published).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const hiddenOnMobile = index === 2 ? "hidden sm:block" : "";
  return `
    <a href="${escapeHtml(post.link)}" target="_blank" rel="noopener noreferrer"
       class="group rounded-2xl border border-base-300/30 bg-base-200/50 p-7 transition-all duration-300 hover:border-accent/30 hover:shadow-lg hover:shadow-accent/5 ${hiddenOnMobile}">
      <div class="text-xs text-accent font-semibold uppercase tracking-wider mb-3">${escapeHtml(date)}</div>
      <h3 class="text-lg font-bold mb-2 group-hover:text-accent transition-colors line-clamp-2">${escapeHtml(post.title)}</h3>
      <p class="text-sm text-base-content/50 line-clamp-3">${escapeHtml(post.summary)}</p>
      <div class="mt-4 flex items-center gap-1 text-accent text-sm font-semibold">
        <span>Read more</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
             class="transition-transform group-hover:translate-x-1">
          <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
        </svg>
      </div>
    </a>`;
}

function renderFallbackCard() {
  return `
    <a href="https://acoruss.substack.com" target="_blank" rel="noopener noreferrer"
       class="col-span-full rounded-2xl border border-base-300/30 bg-base-200/50 p-10 text-center hover:border-accent/30 transition-all">
      <h3 class="text-lg font-bold mb-2">Visit Our Blog</h3>
      <p class="text-sm text-base-content/50">Read the latest insights on technology and strategy on our Substack.</p>
    </a>`;
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Currency display — USD default, KES for visitors in Kenya
// ---------------------------------------------------------------------------

const RATE_CACHE_KEY = "acoruss_usd_kes_rate";
const RATE_CACHE_TTL = 3600000; // 1 hour in ms

function isKenyaTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone === "Africa/Nairobi";
  } catch {
    return false;
  }
}

function getCachedRate() {
  try {
    const raw = sessionStorage.getItem(RATE_CACHE_KEY);
    if (!raw) return null;
    const cached = JSON.parse(raw);
    if (Date.now() - cached.fetchedAt < RATE_CACHE_TTL) return cached.rate;
    sessionStorage.removeItem(RATE_CACHE_KEY);
  } catch {
    // Ignore parse errors
  }
  return null;
}

function setCachedRate(rate) {
  try {
    sessionStorage.setItem(
      RATE_CACHE_KEY,
      JSON.stringify({ rate, fetchedAt: Date.now() })
    );
  } catch {
    // sessionStorage unavailable (private browsing, etc.)
  }
}

function formatCurrency(amount, currency, locale) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function applyPrices(currency, rate, locale) {
  document.querySelectorAll("[data-price]").forEach((el) => {
    const usdAmount = parseFloat(el.dataset.price);
    if (isNaN(usdAmount)) return;
    const amount = currency === "KES" ? Math.round(usdAmount * rate) : usdAmount;
    el.textContent = formatCurrency(amount, currency, locale);
  });

  // Handle range prices: data-price-min / data-price-max
  document.querySelectorAll("[data-price-min]").forEach((el) => {
    const minUsd = parseFloat(el.dataset.priceMin);
    const maxUsd = parseFloat(el.dataset.priceMax);
    const suffix = el.dataset.priceSuffix || "";
    if (isNaN(minUsd)) return;

    const min = currency === "KES" ? Math.round(minUsd * rate) : minUsd;
    const formattedMin = formatCurrency(min, currency, locale);

    if (!isNaN(maxUsd)) {
      const max = currency === "KES" ? Math.round(maxUsd * rate) : maxUsd;
      const formattedMax = formatCurrency(max, currency, locale);
      el.textContent = formattedMin + " – " + formattedMax + suffix;
    } else {
      el.textContent = formattedMin + suffix;
    }
  });
}

// Current state for toggle support
let _currentCurrency = "USD";
let _kesRate = null;

function updateToggleButtons(currency) {
  const btnUsd = document.getElementById("btn-usd");
  const btnKes = document.getElementById("btn-kes");
  if (!btnUsd || !btnKes) return;
  if (currency === "USD") {
    btnUsd.classList.add("btn-primary");
    btnUsd.classList.remove("btn-ghost");
    btnKes.classList.add("btn-ghost");
    btnKes.classList.remove("btn-primary");
  } else {
    btnKes.classList.add("btn-primary");
    btnKes.classList.remove("btn-ghost");
    btnUsd.classList.add("btn-ghost");
    btnUsd.classList.remove("btn-primary");
  }
}

async function getKesRate() {
  if (_kesRate) return _kesRate;
  const cached = getCachedRate();
  if (cached) { _kesRate = cached; return _kesRate; }
  try {
    const res = await fetch("/api/rates/usd-kes/");
    if (!res.ok) throw new Error("Rate fetch failed");
    const data = await res.json();
    if (data.rate) { _kesRate = data.rate; setCachedRate(_kesRate); return _kesRate; }
  } catch { /* fall through */ }
  return null;
}

async function switchCurrency(currency) {
  if (currency === "KES") {
    const rate = await getKesRate();
    if (rate) {
      applyPrices("KES", rate, "en-KE");
      _currentCurrency = "KES";
    }
  } else {
    applyPrices("USD", 1, "en-US");
    _currentCurrency = "USD";
  }
  updateToggleButtons(_currentCurrency);
}

function initCurrencyToggle() {
  const btnUsd = document.getElementById("btn-usd");
  const btnKes = document.getElementById("btn-kes");
  if (!btnUsd || !btnKes) return;
  btnUsd.addEventListener("click", () => switchCurrency("USD"));
  btnKes.addEventListener("click", () => switchCurrency("KES"));
}

async function initCurrencyDisplay() {
  const hasPrice = document.querySelector("[data-price], [data-price-min]");
  if (!hasPrice) return;

  // Always default to USD
  applyPrices("USD", 1, "en-US");
  _currentCurrency = "USD";

  updateToggleButtons(_currentCurrency);
  initCurrencyToggle();
}