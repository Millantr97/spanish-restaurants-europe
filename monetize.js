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
  adsenseClient: "ca-pub-8044414958800783"
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
})();
