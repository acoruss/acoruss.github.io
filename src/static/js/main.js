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