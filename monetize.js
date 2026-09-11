/* Monetization switchboard for Spanish Restaurants in Europe.
 * Blank IDs = the site renders exactly as before.
 * viatorPid: Viator affiliate account ID (format P000xxxxx). Once set, every
 *   viator.com link on the site is upgraded to an affiliate link by adding
 *   pid/mcid/medium tracking parameters, per Viator's link documentation.
 * adsenseClient: AdSense publisher ID (format ca-pub-XXXX). Once set, the
 *   AdSense loader (Auto ads) is injected site-wide.
 * Fill these in after enrolment; no page regeneration is needed.
 */
window.MONETIZE = {
  viatorPid: "P00319561",
  viatorMcid: "42383",
  adsenseClient: "ca-pub-8044414958800783",
  goatcounterEndpoint: "https://spanishrestaurants.goatcounter.com/count"
};
(function () {
  var cfg = window.MONETIZE;
  function upgradeViator() {
    if (!cfg.viatorPid) return;
    document.querySelectorAll('a[href*="viator.com"]').forEach(function (a) {
      try {
        var u = new URL(a.href);
        if (!u.searchParams.get("pid")) {
          u.searchParams.set("pid", cfg.viatorPid);
          u.searchParams.set("mcid", cfg.viatorMcid);
          u.searchParams.set("medium", "link");
          a.href = u.toString();
        }
        a.rel = "sponsored noopener";
      } catch (e) {}
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", upgradeViator);
  } else {
    upgradeViator();
  }
  if (cfg.adsenseClient) {
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + cfg.adsenseClient;
    document.head.appendChild(s);
  }

  /* Lightweight, cookie-free analytics. Query strings are deliberately
   * excluded so shared-list contents and filter choices never leave the page.
   * Custom events use fixed category names only, never link text or URLs. */
  if (cfg.goatcounterEndpoint) {
    var eventQueue = [];
    window.goatcounter = {
      path: function () { return location.pathname || "/"; },
      referrer: function () {
        if (!document.referrer) return "";
        try { return new URL(document.referrer).origin; } catch (e) { return ""; }
      }
    };
    function sendEvent(name) {
      if (window.goatcounter && typeof window.goatcounter.count === "function") {
        window.goatcounter.count({path: name, title: name, event: true});
      } else {
        eventQueue.push(name);
      }
    }
    function flushEvents() {
      while (eventQueue.length && window.goatcounter && typeof window.goatcounter.count === "function") {
        var name = eventQueue.shift();
        window.goatcounter.count({path: name, title: name, event: true});
      }
    }
    function outboundEvent(a) {
      var u;
      try { u = new URL(a.href, location.href); } catch (e) { return ""; }
      if (u.origin === location.origin || (u.protocol !== "http:" && u.protocol !== "https:")) return "";
      var host = u.hostname.toLowerCase().replace(/^www\./, "");
      if (host === "google.com" || host.endsWith(".google.com") || host === "maps.app.goo.gl") return "outbound-google-maps";
      if (host === "viator.com" || host.endsWith(".viator.com")) return "outbound-viator";
      if (/\bmenu|carta|men[uú]\b/i.test((a.textContent || "") + " " + u.pathname)) return "outbound-menu";
      if (/\/shops\.html$/.test(location.pathname)) return "outbound-shop";
      return "outbound-restaurant";
    }
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a) return;
      var name = outboundEvent(a);
      if (name) sendEvent(name);
    }, true);
    var gc = document.createElement("script");
    gc.setAttribute("data-goatcounter", cfg.goatcounterEndpoint);
    gc.async = true;
    gc.src = "//gc.zgo.at/count.js";
    gc.addEventListener("load", function () {
      flushEvents();
      if (new URLSearchParams(location.search).get("list")) sendEvent("shared-list-open");
    });
    document.head.appendChild(gc);
  }
})();
