/*
 * Samarasyam 2026: progressive enhancement only. The page is complete without
 * this file; each feature does nothing if the markup it needs is missing.
 * Loaded with `defer`; no inline scripts anywhere (the CSP forbids them).
 */
(function () {
  "use strict";

  var IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;

  function todayInIST() {
    return new Date(Date.now() + IST_OFFSET_MS).toISOString().slice(0, 10);
  }

  /* Day 1 / Day 2 tabs. Without JS the tabs are plain links and both days show. */
  function initTabs() {
    var lists = document.querySelectorAll('[role="tablist"]');
    Array.prototype.forEach.call(lists, function (list) {
      var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
      var panels = tabs.map(function (tab) {
        return document.getElementById(tab.getAttribute("aria-controls"));
      });
      if (!tabs.length || panels.indexOf(null) !== -1) return;

      function select(index, focus) {
        tabs.forEach(function (tab, i) {
          var on = i === index;
          tab.setAttribute("aria-selected", on ? "true" : "false");
          tab.tabIndex = on ? 0 : -1;
          panels[i].hidden = !on;
        });
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

      // Start on: the day a link points into (e.g. #session-s12), else today's day during the event, else Day 1.
      var start = 0;
      var target = location.hash ? document.getElementById(location.hash.slice(1)) : null;
      var today = todayInIST();
      panels.forEach(function (panel, i) {
        if (panel.getAttribute("data-date") === today) start = i;
      });
      panels.forEach(function (panel, i) {
        if (target && panel.contains(target)) start = i;
      });
      select(start, false);
      if (target && target.tagName === "DETAILS") target.open = true;
    });
  }

  /* Countdown: replaces the date text with "N days to go" / under way / concluded. */
  function initCountdown() {
    var els = document.querySelectorAll("[data-countdown]");
    Array.prototype.forEach.call(els, function (el) {
      var start = Date.parse(el.getAttribute("datetime"));
      var end = Date.parse(el.getAttribute("data-end"));
      if (isNaN(start)) return;
      var now = Date.now();
      if (now < start) {
        var days = Math.ceil((start - now) / 86400000);
        el.textContent = days + " " + el.getAttribute(days === 1 ? "data-label-day" : "data-label-days");
      } else if (!isNaN(end) && now <= end) {
        el.textContent = el.getAttribute("data-label-live");
      } else {
        el.textContent = el.getAttribute("data-label-over");
      }
    });
  }

  /* Desktop hover preview hook for session cards: adds a class the stylesheet can use.
     Click / tap still opens the <details> as normal. */
  function initHoverPreview() {
    if (!window.matchMedia || !window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    var cards = document.querySelectorAll("details.session");
    Array.prototype.forEach.call(cards, function (card) {
      card.addEventListener("mouseenter", function () { card.classList.add("is-previewing"); });
      card.addEventListener("mouseleave", function () { card.classList.remove("is-previewing"); });
    });
  }

  initTabs();
  initCountdown();
  initHoverPreview();
})();
