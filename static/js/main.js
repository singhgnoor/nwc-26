/*
 * Samarasyam 2026: progressive enhancement only. The page is complete without
 * this file: both programme days and both speaker days are readable, the
 * countdown shows the date, phones get a scrolling link row instead of the
 * menu, and the photo carousel is a swipeable strip. Each feature does nothing
 * if the markup it needs is missing. Loaded with `defer`; no inline scripts
 * anywhere (the CSP forbids them). No dependencies.
 */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;
  root.classList.add("js");

  var IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function todayInIST() {
    return new Date(Date.now() + IST_OFFSET_MS).toISOString().slice(0, 10);
  }

  function each(list, fn) {
    Array.prototype.forEach.call(list, fn);
  }

  /* ---------------------------------------------------------------------
   * Day 1 / Day 2 tabs. They switch the programme panels and keep the
   * "Dignitaries & speakers" section on the same day. Day 1 is the default;
   * on 7 December (IST) Day 2 is. A link into a day (e.g. #details-s12) wins.
   * ------------------------------------------------------------------- */
  function initTabs() {
    var list = doc.querySelector('.tabs[role="tablist"]');
    if (!list) return;
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    var panels = tabs.map(function (tab) { return doc.getElementById(tab.getAttribute("aria-controls")); });
    if (!tabs.length || panels.indexOf(null) !== -1) return;
    var dayIds = panels.map(function (p) { return p.id; });

    function syncSpeakers(dayId) {
      each(doc.querySelectorAll("#speakers [data-day]"), function (el) {
        el.hidden = el.getAttribute("data-day") !== dayId;
      });
    }

    function select(index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      syncSpeakers(dayIds[index]);
      if (focus) tabs[index].focus();
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function (event) {
        event.preventDefault();
        select(i, false);
      });
      tab.addEventListener("keydown", function (event) {
        var next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[event.key];
        if (next === undefined) return;
        event.preventDefault();
        select((next + tabs.length) % tabs.length, true);
      });
    });

    var start = 0;
    var today = todayInIST();
    panels.forEach(function (panel, i) {
      if (panel.getAttribute("data-date") === today) start = i;
    });
    function fromHash() {
      var target = location.hash ? doc.getElementById(decodeURIComponent(location.hash.slice(1))) : null;
      if (!target) return -1;
      for (var i = 0; i < panels.length; i++) {
        if (panels[i] === target || panels[i].contains(target)) {
          if (target.tagName === "DETAILS") target.open = true;
          var inner = target.querySelector && target.querySelector("details");
          if (target.classList.contains("tl") && inner) inner.open = true;
          return i;
        }
      }
      return -1;
    }
    var hashed = fromHash();
    select(hashed >= 0 ? hashed : start, false);
    window.addEventListener("hashchange", function () {
      var i = fromHash();
      if (i >= 0) select(i, false);
    });
  }

  /* ---------------------------------------------------------------------
   * Countdown to the opening (6 Dec, 09:30 IST). During the conclave it
   * reads "Happening now · Day N"; after the last day the block hides.
   * ------------------------------------------------------------------- */
  function initCountdown() {
    var box = doc.querySelector("[data-countdown]");
    if (!box) return;
    var num = box.querySelector("[data-countdown-num]");
    var text = box.querySelector("[data-countdown-text]");
    var line = box.querySelector(".countdown");
    var start = Date.parse(box.getAttribute("data-start"));
    var end = Date.parse(box.getAttribute("data-end"));
    if (isNaN(start) || isNaN(end) || !num || !text) return;

    // Whole calendar days in IST between today and the opening day (so 5 Dec reads "1 day",
    // and the opening day itself, from midnight, already reads "Happening now · Day 1").
    function istDayNumber(ms) {
      return Math.floor((ms + IST_OFFSET_MS) / 86400000);
    }

    function update() {
      var now = Date.now();
      var days = istDayNumber(start) - istDayNumber(now);
      if (days > 0) {
        num.textContent = String(days);
        text.textContent = box.getAttribute(days === 1 ? "data-label-day" : "data-label-days");
        line.classList.remove("is-live");
      } else if (now <= end) {
        num.textContent = "";
        var today = todayInIST();
        var label = box.getAttribute("data-label-live");
        for (var i = 1; box.hasAttribute("data-day-" + i); i++) {
          var parts = box.getAttribute("data-day-" + i).split("|");
          if (parts[0] === today) label += " · " + parts[1];
        }
        text.textContent = label;
        line.classList.add("is-live");
      } else {
        box.hidden = true;
        return;
      }
      window.setTimeout(update, 60000);
    }
    update();
  }

  /* ---------------------------------------------------------------------
   * Sticky nav: highlight the section in view.
   * ------------------------------------------------------------------- */
  function initScrollSpy() {
    var links = doc.querySelectorAll('.nav__link[href^="#"], .menu__link[href^="#"]');
    if (!links.length || !("IntersectionObserver" in window)) return;
    var byId = {};
    each(links, function (a) {
      var id = a.getAttribute("href").slice(1);
      (byId[id] = byId[id] || []).push(a);
    });
    var sections = Object.keys(byId).map(function (id) { return doc.getElementById(id); }).filter(Boolean);
    var visible = {};
    function paint() {
      var current = null;
      sections.forEach(function (s) { if (visible[s.id] && !current) current = s.id; });
      Object.keys(byId).forEach(function (id) {
        byId[id].forEach(function (a) {
          if (id === current) { a.classList.add("is-active"); a.setAttribute("aria-current", "true"); }
          else { a.classList.remove("is-active"); a.removeAttribute("aria-current"); }
        });
      });
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
      paint();
    }, { rootMargin: "-35% 0px -55% 0px" });
    sections.forEach(function (s) { observer.observe(s); });
  }

  /* ---------------------------------------------------------------------
   * Mobile menu: focus trapped while open, Esc closes, choosing a link
   * closes, page scroll locked.
   * ------------------------------------------------------------------- */
  function initMenu() {
    var menu = doc.getElementById("menu");
    var openBtn = doc.querySelector("[data-menu-open]");
    var closeBtn = menu && menu.querySelector("[data-menu-close]");
    if (!menu || !openBtn || !closeBtn) return;
    openBtn.hidden = false;
    var main = doc.getElementById("main");
    var outside = [doc.querySelector(".site-header"), doc.getElementById("navbar"), main, doc.querySelector(".site-footer")];

    function focusables() {
      return Array.prototype.filter.call(
        menu.querySelectorAll('a[href], button:not([disabled])'),
        function (el) { return el.offsetParent !== null; });
    }
    function setOutside(inert) {
      outside.forEach(function (el) {
        if (!el) return;
        if (inert) { el.setAttribute("aria-hidden", "true"); if ("inert" in el) el.inert = true; }
        else { el.removeAttribute("aria-hidden"); if ("inert" in el) el.inert = false; }
      });
    }
    function open() {
      menu.hidden = false;
      doc.body.classList.add("menu-open");
      openBtn.setAttribute("aria-expanded", "true");
      setOutside(true);
      closeBtn.focus();
    }
    function close(restoreFocus) {
      menu.hidden = true;
      doc.body.classList.remove("menu-open");
      openBtn.setAttribute("aria-expanded", "false");
      setOutside(false);
      if (restoreFocus) openBtn.focus();
    }
    openBtn.addEventListener("click", open);
    closeBtn.addEventListener("click", function () { close(true); });
    menu.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest("a[href]");
      if (link) close(false);
    });
    menu.addEventListener("keydown", function (event) {
      if (event.key === "Escape") { event.preventDefault(); close(true); return; }
      if (event.key !== "Tab") return;
      var items = focusables();
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (event.shiftKey && doc.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && doc.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    var wide = window.matchMedia("(min-width: 1024px)");
    function onWide() { if (wide.matches && !menu.hidden) close(false); }
    if (wide.addEventListener) wide.addEventListener("change", onWide); else if (wide.addListener) wide.addListener(onWide);
  }

  /* ---------------------------------------------------------------------
   * Moments carousel (after the event): arrows, keyboard, swipe (native
   * scroll-snap), thumbnails. No autoplay.
   * ------------------------------------------------------------------- */
  function initCarousels() {
    each(doc.querySelectorAll("[data-carousel]"), function (box) {
      var track = box.querySelector("[data-carousel-track]");
      var prev = box.querySelector("[data-carousel-prev]");
      var next = box.querySelector("[data-carousel-next]");
      if (!track || !prev || !next) return;
      var slides = Array.prototype.slice.call(track.children);
      var thumbs = Array.prototype.slice.call(box.querySelectorAll(".carousel__thumb"));
      if (!slides.length) return;
      var index = 0;
      prev.hidden = next.hidden = slides.length < 2;

      function go(i, focusTrack) {
        index = Math.max(0, Math.min(slides.length - 1, i));
        track.scrollTo({ left: slides[index].offsetLeft - track.offsetLeft, behavior: reduceMotion ? "auto" : "smooth" });
        paint();
        if (focusTrack) track.focus();
      }
      function paint() {
        prev.disabled = index === 0;
        next.disabled = index === slides.length - 1;
        thumbs.forEach(function (t, i) {
          if (i === index) t.setAttribute("aria-current", "true"); else t.removeAttribute("aria-current");
        });
        slides.forEach(function (s, i) { s.setAttribute("aria-hidden", i === index ? "false" : "true"); });
      }
      prev.addEventListener("click", function () { go(index - 1); });
      next.addEventListener("click", function () { go(index + 1); });
      track.addEventListener("keydown", function (event) {
        if (event.key === "ArrowRight") { event.preventDefault(); go(index + 1); }
        else if (event.key === "ArrowLeft") { event.preventDefault(); go(index - 1); }
        else if (event.key === "Home") { event.preventDefault(); go(0); }
        else if (event.key === "End") { event.preventDefault(); go(slides.length - 1); }
      });
      thumbs.forEach(function (t, i) {
        t.addEventListener("click", function (event) { event.preventDefault(); go(i); });
      });
      var timer = null;
      track.addEventListener("scroll", function () {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
          var width = track.clientWidth || 1;
          var i = Math.round(track.scrollLeft / width);
          if (i !== index) { index = Math.max(0, Math.min(slides.length - 1, i)); paint(); }
        }, 80);
      }, { passive: true });
      paint();
    });
  }

  initTabs();
  initCountdown();
  initScrollSpy();
  initMenu();
  initCarousels();
})();
