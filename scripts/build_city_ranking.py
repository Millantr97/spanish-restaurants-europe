#!/usr/bin/env python3
"""Build the best-cities ranking pages (EN + ES) from the dataset embedded in index.html.

Source of truth for venues: the `const DATA = {...}` object in ../index.html.
Source of truth for populations: ../data/city_populations.json (one entry per ranked
city, with year, statistical boundary and source URL).

Run from anywhere:
    python3 scripts/build_city_ranking.py            # rewrite both ranking pages
    python3 scripts/build_city_ranking.py --check    # validate only; exit 1 on any problem

Build-time validation fails (exit 1) when:
  - any venue's city normalizes to blank / a bare postcode (the blank-row bug)
  - any ranked city is missing from data/city_populations.json
  - any ranked row would render a blank city, country, population or per-capita
"""
import json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
POPS = ROOT / "data" / "city_populations.json"
EN_PAGE = ROOT / "guides" / "europe-best-cities-spanish-food.html"
ES_PAGE = ROOT / "guides" / "es" / "europa-mejores-ciudades-comida-espanola.html"
TOP_N = 30

# Language variants and same-city spellings merged to one canonical key.
ALIASES = {
    "milano": "milan", "munchen": "munich", "koln": "cologne", "koeln": "cologne",
    "antwerpen": "antwerp", "wien": "vienna", "lisboa": "lisbon", "bruxelles": "brussels",
    "goteborg": "gothenburg", "kobenhavn": "copenhagen", "hannover": "hanover",
    "torino": "turin", "napoli": "naples", "brugge": "bruges", "gent": "ghent",
    "luzern": "lucerne", "luxembourg city": "luxembourg",
    "frankfurt am main": "frankfurt", "geneve": "geneva", "warszawa": "warsaw",
    "freiburg im breisgau": "freiburg",
    # Same-city districts (Google sometimes reports the district as the city).
    "hamburg-nord": "hamburg", "koln-lindenthal": "cologne", "cologne-ehrenfeld": "cologne",
    "koln-rodenkirchen": "cologne", "munchen-schwabing-freimann": "munich",
    "munchen-ludwigsvorstadt-isarvorstadt": "munich",
    "hannover-linden-limmer": "hanover", "hannover-ricklingen": "hanover",
    "dusseldorf-stadtbezirk 2": "dusseldorf", "dusseldorf-stadtbezirk 7": "dusseldorf",
    "bonn-hardtberg": "bonn", "frankfurt am main nord-ost": "frankfurt",
    "frankfurt am main-kalbach-riedberg": "frankfurt", "dublin 6w": "dublin",
    # Dutch postcode letters leaked as a prefix ("1017 BK Amsterdam" -> "BK Amsterdam").
    "bk amsterdam": "amsterdam", "gr amsterdam": "amsterdam",
    "jh amsterdam": "amsterdam", "vx amsterdam": "amsterdam",
}

# Venues whose Google city field is only a postcode/road code: city recovered
# from the venue's own address (or coordinates for the N122 roadside stop).
RECOVER_CITY = {
    "tapas-come-059": "viana do alentejo",            # 7830-059 -> Viana do Alentejo
    "cantina-do-largo-095": "alfarim",                # Alfarim, 2970-095 (Sesimbra)
    "tapas-271": "vagos",                             # 3840-271 -> Vagos
    "taberna-do-merendas-021": "santiago de riba-ul", # 3720-021 -> Santiago de Riba-Ul
    "taberna-da-estacao-012": "viana do castelo",     # 4900-012 -> Viana do Castelo
    "taberna-da-cruz-790": "amarante",                # 4600-790 -> Amarante
    "taberna-cabrita-ic1": "ourique",                 # IC1, 7670 -> Ourique
    "a-taberna-do-ramos-n122": "mertola",             # N122, 37.437,-7.509 -> Mertola
    "paella-bar": "nessebar",                         # Nesebar, Bulgaria (Cyrillic city)
    "solas-tapas-wine-v92-y79t": "dingle",
    "la-cantina-company-t12-yx76": "cork",
    "bodega-x91-xw2r": "waterford",
    "a-taste-of-spain-spanish-gourmet-shop-d02-tx29": "dublin",
    "la-casa-tapas-wine-claremorris-f12-eh75": "claremorris",
    "the-gallery-cafe-wine-tapas-bar-open-tuesday-saturday-bank-h": "westport",
    "meson-elias-d01-fk49": "dublin",
    "the-old-town-whiskey-bar-at-bodega-t12-w27h": "cork",
    "cantina-valentina-dublin-d02-e044": "dublin",
    "mr-croqueta-d02-tx29": "dublin",
    "dos-almas-tapas-cocktail-bar-sa": "terravecchia",  # Terravecchia (SA), Italy
    "tapas-bar-32-060": "piekary",                        # Piekary 383, 32-060 (gmina Liszki)
}

def normalize_city(raw):
    c = raw.strip()
    c = re.sub(r"^[-\d]*\d+\s+(?=\D)", "", c)                 # leading postcode: "-019 Lisboa", "20 Stockholm"
    c = re.sub(r"\b[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d?[A-Z]{0,2}\b", "", c)  # UK-style postcodes
    c = re.sub(r"\s+\b[A-Z]{2}\b$", "", c)                    # trailing province code: "Roma RM"
    c = c.strip(" -,")
    c = c.replace("ø", "o").replace("Ø", "O").replace("ß", "ss")
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode().lower()
    return ALIASES.get(c, c)

def load_places():
    for line in INDEX.open(encoding="utf-8"):
        if line.startswith("const DATA"):
            j = line.strip()[len("const DATA = "):].rstrip(";")
            return json.loads(j)["places"]
    raise SystemExit("could not find const DATA in index.html")

def looks_like_code(key):
    return (not key) or key.isdigit() or bool(re.match(r"^[a-z]{0,2}\d", key))

def canonical_city(place):
    g = normalize_city(place.get("city", ""))
    if looks_like_code(g) and place["uid"] in RECOVER_CITY:
        g = RECOVER_CITY[place["uid"]]
    return g

def aggregate(places):
    groups = {}
    for p in places:
        groups.setdefault(canonical_city(p), []).append(p)
    rows = []
    for key, ps in groups.items():
        rated = [p["rating"] for p in ps if p.get("rating")]
        rows.append({
            "key": key,
            "venues": len(ps),
            "avg": round(sum(rated) / len(rated), 2) if rated else 0,
            "reviews": sum(p.get("rcount", 0) for p in ps),
            "menus": sum(1 for p in ps if p.get("menu")),
        })
    pops = json.load(POPS.open(encoding="utf-8"))
    rows.sort(key=lambda r: (-r["venues"], pops.get(r["key"], {}).get("name_en", r["key"])))
    return rows, pops, len(places)

def validate(rows, pops, ranked):
    problems = []
    for r in rows:
        k = r["key"]
        if looks_like_code(k):
            problems.append(f"venue group normalizes to blank/postcode city: {k!r} ({r['venues']} venues)")
    for r in ranked:
        k = r["key"]
        e = pops.get(k)
        if not e:
            problems.append(f"ranked city missing from data/city_populations.json: {k}")
            continue
        for field in ("name_en", "name_es", "country_en", "country_es", "population", "year", "boundary", "source"):
            if not e.get(field):
                problems.append(f"{k}: empty field {field} in city_populations.json")
        if not isinstance(e.get("population"), int) or not (10_000 <= e["population"] <= 20_000_000):
            problems.append(f"{k}: implausible population {e.get('population')}")
        if not str(e.get("source", "")).startswith("https://"):
            problems.append(f"{k}: source is not an https URL")
    return problems

def slug(name_en):
    s = unicodedata.normalize("NFKD", name_en).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", "-", s)

def guide_link(key, lang):
    e = POPS_CACHE[key]
    sl = slug(e["name_en"])
    if lang == "en":
        f = ROOT / "guides" / f"{sl}-best-spanish-restaurants.html"
        return f"{sl}-best-spanish-restaurants.html" if f.exists() else None
    f = ROOT / "guides" / "es" / f"{sl}-mejores-restaurantes-espanoles.html"
    return f"{sl}-mejores-restaurantes-espanoles.html" if f.exists() else None

def fmt_pop(n, lang):
    return f"{n:,}".replace(",", "." if lang == "es" else ",")

def render_rows(ranked, pops, lang):
    out = []
    for i, r in enumerate(ranked, 1):
        e = pops[r["key"]]
        name = e["name_en"] if lang == "en" else e["name_es"]
        country = e["country_en"] if lang == "en" else e["country_es"]
        per100k = round(r["venues"] / e["population"] * 100_000, 1)
        link = guide_link(r["key"], lang)
        city_html = f'<a href="{link}">{name}</a>' if link else name
        out.append(
            f'<tr><td>{i}</td><td>{city_html} <span class="cc">({country})</span></td>'
            f'<td>{r["venues"]}</td><td>{fmt_pop(e["population"], lang)}</td><td>{per100k}</td>'
            f'<td>{r["avg"]:.2f}</td><td>{r["reviews"]:,}</td><td>{r["menus"]}</td></tr>'
        )
    return "\n".join(out)

def splice(page, new_rows):
    html = page.read_text(encoding="utf-8")
    start = html.index('<table class="rank">')
    head_end = html.index("</tr>", start) + len("</tr>")
    end = html.index("</table>", head_end)
    return html[:head_end] + "\n" + new_rows + "\n" + html[end:]

def main():
    check = "--check" in sys.argv
    places = load_places()
    rows, pops, total = aggregate(places)
    global POPS_CACHE
    POPS_CACHE = pops
    ranked = rows[:TOP_N]
    problems = validate(rows, pops, ranked)
    if problems:
        print("BUILD FAILED - city ranking validation:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    en_rows, es_rows = render_rows(ranked, pops, "en"), render_rows(ranked, pops, "es")
    en_new, es_new = splice(EN_PAGE, en_rows), splice(ES_PAGE, es_rows)
    if check:
        same = (en_new == EN_PAGE.read_text(encoding="utf-8")) and (es_new == ES_PAGE.read_text(encoding="utf-8"))
        print(("OK: ranking pages match the generator output "
               f"({total} venues, top {TOP_N} cities, all rows populated).") if same
              else "STALE: ranking pages differ from generator output - rerun build_city_ranking.py")
        sys.exit(0 if same else 1)
    EN_PAGE.write_text(en_new, encoding="utf-8")
    ES_PAGE.write_text(es_new, encoding="utf-8")
    print(f"wrote {EN_PAGE.relative_to(ROOT)} and {ES_PAGE.relative_to(ROOT)} "
          f"({total} venues, top {TOP_N} cities, all rows populated).")

if __name__ == "__main__":
    main()
