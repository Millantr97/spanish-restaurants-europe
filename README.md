# spanish-restaurants-europe
Interactive map of Spanish restaurants and tapas bars across Europe: filter by dish, price and Google rating, with per-restaurant comments (Disqus).

## Best-cities ranking pipeline

`guides/europe-best-cities-spanish-food.html` (EN) and `guides/es/europa-mejores-ciudades-comida-espanola.html` (ES) are generated, not hand-edited:

- Venue counts come from the `DATA` object embedded in `index.html`, with city-name normalization (postcodes, districts, language variants) in `scripts/build_city_ranking.py`.
- Populations live in `data/city_populations.json` — one entry per ranked city with year, statistical boundary and source URL.
- Rebuild after any dataset change: `python3 scripts/build_city_ranking.py`
- Gate before publishing: `python3 scripts/build_city_ranking.py --check` exits 1 if the pages are stale, any venue's city normalizes to a blank/postcode, or any ranked city lacks a population, boundary, year or source.
