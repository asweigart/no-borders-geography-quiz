# No Borders Geography Quiz

**🌐 Play it online: <https://inventwithpython.com/no-borders-geography.html>**

An interactive, borderless 3D globe for learning world geography. Spin and zoom
a clean globe (no political borders drawn by default) and identify countries,
US states, and dozens of country subdivisions — as a quiz, a guided tour, or a
free-form info explorer.

The whole app is a **single self-contained HTML file** that works **offline**:
save `no-borders-geography.html` and open it in any modern browser. No build
step, server, or network connection is required to run it.

## Features

- **Borderless orthographic globe** rendered with D3 — drag to spin, zoom, pan,
  and roll.
- **Four modes:**
  - **Quiz** — you're given a region to find; click it on the globe. A wrong
    guess shows what you clicked and offers **Try Again** or **Show Answer**
    (which focuses the correct region); a correct guess flashes **Correct!** and
    moves on.
  - **Info** — hover (or center the reticle on touch) any region to see its
    name, capital, and a Wikipedia link.
  - **Show All** — draw every border in the current dataset at once.
  - **Tour** — auto-fly between regions one at a time.
- **Atlas** — a searchable, browsable list of every region in the current
  dataset; click to fly to it.
- **Many datasets** — all countries, individual continents, US states, and 45+
  country subdivision sets (provinces, states, regions, prefectures, oblasts,
  cantons, counties, …).
- **40 languages** with automatic browser-language detection, persisted choice,
  right-to-left support, and localized place names where data allows.
- **Customizable colors** — preset schemes plus a full custom palette, with
  JSON import/export and a reset-to-default option.

## Quick start

```
# Just open the file — no install needed:
open no-borders-geography.html        # macOS
# or double-click it in your file manager, or drag it into a browser tab.
```

If opened from a CDN-reachable network instead of `file://`, missing local data
falls back to public CDNs automatically.

## Controls

| Action | Input |
| --- | --- |
| Spin the globe | drag, or **Q** / **E** |
| Zoom | scroll / pinch, or **+** / **−** |
| Pan | **WASD** / arrow keys |
| Reset view | **0** |
| Settings | the ⚙ button (top-right) |

Touch devices also get an on-screen control pad (toggle it under **Settings →
Options**).

## Languages

The UI, prompts, dataset names, and color-scheme names are translated into 40
languages:

English, Simplified Chinese, Spanish, Arabic, Indonesian, Portuguese, French,
Japanese, Russian, German, Hindi, Bengali, Urdu, Korean, Vietnamese, Turkish,
Italian, Dutch, Polish, Thai, Persian, Ukrainian, Czech, Malay, Romanian,
Greek, Hebrew, Swedish, Filipino, Tamil, Hungarian, Danish, Finnish, Norwegian
Bokmål, Slovak, Bulgarian, Serbian, Croatian, Slovenian, Catalan.

On first load the app picks a language from the browser's settings (falling back
to English) and remembers any manual choice in `localStorage`. Country/region
names are localized for the ~23 languages covered by the bundled name data;
other languages and all subdivisions fall back to English. Wikipedia links point
to the matching-language Wikipedia, or English when no localized name exists.

## Color schemes

Pick a preset (Default, Daylight, Parchment, Neon, Mono, Sunset, Forest, Arctic,
Volcanic) or set each color by hand. Under **Settings → Colors** you can:

- **Export** the current palette as a JSON file.
- **Import** a palette from a JSON file.
- **Reset** back to the Default scheme (with confirmation).

The exported format:

```json
{
  "type": "no-borders-color-scheme",
  "version": 1,
  "colors": {
    "bg": "#050912",
    "land": "#3d6b48",
    "ocean": "#16335a",
    "rivers": "#78aae6",
    "highlight": "#7ec8ff",
    "clicked": "#ffd54a",
    "correct": "#7adba0"
  }
}
```

## Project structure

| Path | Purpose |
| --- | --- |
| `no-borders-geography.html` | The quiz app (self-contained, with data inlined). |
| `simple-mercator-world-map.html`, `simple-robinson-world-map.html` | Standalone flat-map variants. |
| `*.geojson`, `*.json` | Source geographic data (countries, subdivisions, lakes, rivers). |
| `build_i18n.py` | Builds the translation table and injects it into the app. |
| `inline_data.py` | Inlines the base JSON data into the HTML so it runs offline. |
| `generate_geo_info.py` | Regenerates `_geo_info.md`, a listing of every region's name, flag, and capital. |

### Regenerating / editing

The translation data and base map data are **generated** into the HTML, so edit
the sources and re-run the scripts rather than hand-editing the injected blocks:

```
python3 build_i18n.py        # rebuild the i18n table (edit LANGS / EN / TR in this file first)
python3 inline_data.py       # re-inline base data   (--remove to strip it again)
python3 generate_geo_info.py # refresh _geo_info.md
```

`build_i18n.py` replaces the block between the `<!-- NBGQ-I18N-START -->` /
`<!-- NBGQ-I18N-END -->` markers; `inline_data.py` replaces its own
`BEGIN/END INLINED DATA` block. Both are idempotent.

## Tech

- [D3.js v7](https://d3js.org/) + [d3-geo-projection](https://github.com/d3/d3-geo-projection)
  for the globe and projections.
- [topojson-client](https://github.com/topojson/topojson-client) for TopoJSON.
- Vanilla HTML/CSS/JS otherwise — no framework, no bundler.

Library files (`d3.v7.min.js`, `topojson-client.v3.min.js`,
`d3-geo-projection.v4.min.js`) are vendored locally so the app stays offline,
with CDN fallbacks if they're absent.

## Data sources

Bundled geographic data comes from these open datasets:

- [world-atlas](https://github.com/topojson/world-atlas) — country TopoJSON.
- [world-countries](https://github.com/mledoze/countries) — names, flags,
  capitals, and localized name translations.
- [Natural Earth](https://www.naturalearthdata.com/) (via
  [natural-earth-geojson](https://github.com/martynafford/natural-earth-geojson))
  — lakes and rivers.
- [us-atlas](https://github.com/topojson/us-atlas) — US states.
- [geoBoundaries](https://www.geoboundaries.org/) — country subdivisions.

Each retains its respective license; please consult the upstream projects for
reuse terms.

## Credits

Created by [Al Sweigart](https://inventwithpython.com).
