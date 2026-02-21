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