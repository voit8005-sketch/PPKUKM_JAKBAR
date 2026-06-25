// ==========================================
// SUDIN PPKUKM - Professional App JS
// ==========================================

document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ Sudin PPKUKM Portal Ready");

  // -------------------------------------------
  // 1. SCROLL REVEAL - Animate elements on scroll
  // -------------------------------------------
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          // Small stagger for groups
          setTimeout(() => {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0) scale(1)";
            entry.target.style.filter = "blur(0)";
          }, i * 40);
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -40px 0px" },
  );

  document.querySelectorAll("[data-scroll-reveal]").forEach((el) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(20px) scale(0.98)";
    el.style.filter = "blur(2px)";
    el.style.transition = "opacity 0.5s ease, transform 0.5s ease, filter 0.5s ease";
    revealObserver.observe(el);
  });

  // Auto-observe cards on index
  document.querySelectorAll(".news-card, .list-news-item, .card").forEach((el, i) => {
    el.style.opacity = "0";
    el.style.transform = "translateY(16px)";
    el.style.transition = `opacity 0.5s ease ${i * 0.06}s, transform 0.5s ease ${i * 0.06}s`;
    revealObserver.observe(el);
  });

  // -------------------------------------------
  // 2. BREAKING NEWS TICKER
  // -------------------------------------------
  const ticker = document.querySelector(".animate-marquee");
  if (ticker) {
    ticker.addEventListener("mouseenter", () => (ticker.style.animationPlayState = "paused"));
    ticker.addEventListener("mouseleave", () => (ticker.style.animationPlayState = "running"));
  }

  // -------------------------------------------
  // 3. CATEGORY TABS
  // -------------------------------------------
  const tabs = document.querySelectorAll(".category-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      filterNews(tab.textContent.trim());
    });
  });

  // -------------------------------------------
  // 4. UKM MAP
  // -------------------------------------------
  initUKMMap();

  // -------------------------------------------
  // 5. SMOOTH LAZY IMAGE LOAD
  // -------------------------------------------
  document.querySelectorAll('img[loading="lazy"]').forEach((img) => {
    img.style.transition = "opacity 0.4s ease";
    img.style.opacity = img.complete ? "1" : "0";
    img.addEventListener("load", () => {
      img.style.opacity = "1";
    });
  });

  // -------------------------------------------
  // 6. FLASH MESSAGE AUTO-DISMISS
  // -------------------------------------------
  const flashMessages = document.querySelectorAll(".animate-slide-in");
  flashMessages.forEach((msg, i) => {
    setTimeout(
      () => {
        msg.style.transition = "opacity 0.5s ease, transform 0.5s ease, max-height 0.5s ease";
        msg.style.opacity = "0";
        msg.style.transform = "translateY(-8px)";
        setTimeout(() => msg.remove(), 500);
      },
      6000 + i * 300,
    );
  });

  // -------------------------------------------
  // 7. ACTIVE NAV LINK
  // -------------------------------------------
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-link").forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
      link.style.color = "var(--color-blue-600, #2563eb)";
    }
  });

  // -------------------------------------------
  // 8. TERKINI SLIDER
  // -------------------------------------------
  const slideButtons = document.querySelectorAll(".terkini-slide-btn");
  const slidePanels = document.querySelectorAll("[data-slide-panel^='terkini-']");

  if (slideButtons.length && slidePanels.length) {
    const activateSlide = (slideId) => {
      slideButtons.forEach((btn) => {
        const isActive = btn.dataset.slide === slideId;
        btn.classList.toggle("active", isActive);
        btn.setAttribute("aria-current", isActive ? "true" : "false");
      });

      slidePanels.forEach((panel) => {
        const isVisible = panel.dataset.slidePanel === slideId;
        panel.classList.toggle("block", isVisible);
        panel.classList.toggle("hidden", !isVisible);
      });
    };

    slideButtons.forEach((btn) => {
      btn.addEventListener("click", () => activateSlide(btn.dataset.slide));
    });

    activateSlide(slideButtons[0].dataset.slide);
  }
});

// ==========================================
// NEWS FILTER (client-side demo)
// ==========================================
function filterNews(category) {
  const items = document.querySelectorAll(".news-card, .list-news-item, .featured-article");
  items.forEach((item, i) => {
    const tag = item.querySelector('span[class*="bg-"]');
    const show = category === "SEMUA" || !tag || tag.textContent.trim().toUpperCase().includes(category.toUpperCase());
    item.style.transition = `opacity 0.3s ease ${i * 0.03}s, transform 0.3s ease ${i * 0.03}s`;
    if (show) {
      item.style.opacity = "1";
      item.style.transform = "scale(1)";
      item.style.display = "";
    } else {
      item.style.opacity = "0.3";
      item.style.transform = "scale(0.97)";
    }
  });
}

// ==========================================
// UKM MAP (Leaflet.js — Jakarta Barat)
// ==========================================
function initUKMMap() {
  const container = document.getElementById("ukm-map");
  if (!container) return;

  // Tunggu Leaflet siap — retry jika belum load
  if (typeof L === "undefined") {
    setTimeout(initUKMMap, 300);
    return;
  }

  const kecamatan = [
    { name: "Cengkareng", ukm: 1240, lat: -6.1404, lon: 106.7329, color: "#34d399" },
    { name: "Kalideres", ukm: 520, lat: -6.1328, lon: 106.6961, color: "#4ade80" },
    { name: "Kembangan", ukm: 680, lat: -6.1856, lon: 106.7316, color: "#fb923c" },
    { name: "Kebon Jeruk", ukm: 910, lat: -6.1974, lon: 106.7783, color: "#38bdf8" },
    { name: "Palmerah", ukm: 830, lat: -6.2001, lon: 106.7992, color: "#a78bfa" },
    { name: "Grogol Petamburan", ukm: 890, lat: -6.168, lon: 106.7949, color: "#60a5fa" },
    { name: "Tambora", ukm: 970, lat: -6.1456, lon: 106.8098, color: "#fbbf24" },
    { name: "Taman Sari", ukm: 760, lat: -6.1432, lon: 106.8181, color: "#f472b6" },
  ];

  const map = L.map(container, {
    center: [-6.1676, 106.7633],
    zoom: 12,
    zoomControl: true,
    scrollWheelZoom: false,
  });

  // Tile: OpenStreetMap (paling reliabel, tidak butuh API key)
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
    crossOrigin: true,
  }).addTo(map);

  kecamatan.forEach((k) => {
    // Area lingkaran per kecamatan
    L.circle([k.lat, k.lon], {
      color: k.color,
      fillColor: k.color,
      fillOpacity: 0.15,
      weight: 2,
      opacity: 0.7,
      radius: 1300,
    }).addTo(map);

    // Marker titik
    const marker = L.circleMarker([k.lat, k.lon], {
      radius: 9 + Math.round(k.ukm / 220),
      color: "#fff",
      weight: 2.5,
      fillColor: k.color,
      fillOpacity: 1,
    }).addTo(map);

    marker.bindPopup(
      `<div style="font-family:Inter,sans-serif;padding:4px 2px;min-width:170px">
        <div style="font-weight:800;font-size:13px;color:#1e293b;margin-bottom:6px">${k.name}</div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="width:12px;height:12px;border-radius:50%;background:${k.color};flex-shrink:0;display:inline-block"></span>
          <span style="font-size:13px;font-weight:700;color:#0f172a">${k.ukm.toLocaleString("id")} UKM</span>
        </div>
        <div style="font-size:11px;color:#64748b">Kec. ${k.name}, Jakarta Barat</div>
      </div>`,
      { maxWidth: 220, closeButton: false },
    );

    // Label selalu tampil
    marker.bindTooltip(k.name, {
      permanent: true,
      direction: "top",
      offset: [0, -16],
      className: "ukm-tooltip",
    });
  });

  // Scroll-zoom hanya aktif saat hover peta
  container.addEventListener("mouseenter", () => map.scrollWheelZoom.enable());
  container.addEventListener("mouseleave", () => map.scrollWheelZoom.disable());

  // Perbaiki ukuran peta setelah animasi scroll-reveal selesai
  setTimeout(() => map.invalidateSize(), 600);
  window.addEventListener("resize", () => map.invalidateSize());
}
