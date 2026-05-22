#!/usr/bin/env python3
"""Generate _geo_info.md from the No Borders Geography Quiz data files.

Parses no-borders-geography-quiz.html (capitals dicts, registerSubdivision
calls, US_STATES_50, name overrides) and reads the local GeoJSON / world-
atlas files to produce a prettified markdown listing of every region's
display name, flag emoji, and capital city.

Mirrors the JS loader's transforms: raw property -> trim -> nameClean ->
nameOverrides -> displayName; capital lookup falls back from overridden
name to raw name; per-dataset feature filters are applied.

Output is printed to stdout and saved to _geo_info.md alongside the HTML.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
HTML_PATH = HERE / "no-borders-geography-quiz.html"
OUTPUT_PATH = HERE / "_geo_info.md"

# Per-dataset special behaviour mirroring the JS lambdas (filter / nameClean).
# Keyed by the registerSubdivision key.
SPECIAL_RULES = {
    "australian-states": {"exclude_raw": {"Other Territories"}},
    "uk-ceremonial-counties": {"require_raw_nonempty": True},
    "thai-provinces": {"strip_suffix": " Province"},
}

CONTINENT_ORDER = [
    "Africa", "Antarctica", "Asia", "Europe",
    "North America", "Oceania", "South America",
]


def parse_balanced(text: str, open_idx: int) -> tuple[str, int]:
    """Return (body, close_idx) where body is text inside { ... } and
    close_idx points at the closing brace."""
    if text[open_idx] != "{":
        raise ValueError(f"Expected '{{' at index {open_idx}")
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1 : i], i
    raise ValueError("Unmatched brace")


def parse_string_dict(body: str) -> dict[str, str]:
    """Parse a JS string->string object literal body."""
    kv = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"')
    out: dict[str, str] = {}
    for m in kv.finditer(body):
        k = m.group(1).encode("utf-8").decode("unicode_escape")
        v = m.group(2).encode("utf-8").decode("unicode_escape")
        out[k] = v
    return out


def parse_capitals_dicts(html: str) -> dict[str, dict[str, str]]:
    """Extract `const FOO_CAPITALS = { ... };` blocks."""
    out: dict[str, dict[str, str]] = {}
    for m in re.finditer(r"const (\w+_CAPITALS)\s*=\s*\{", html):
        name = m.group(1)
        body, _ = parse_balanced(html, m.end() - 1)
        out[name] = parse_string_dict(body)
    return out


def parse_us_states_50(html: str) -> set[str]:
    m = re.search(r"const US_STATES_50\s*=\s*new Set\(\s*\[", html)
    if not m:
        return set()
    body, _ = parse_balanced(html, html.index("[", m.end() - 1) - 0) if False else (None, None)
    # Simpler: extract the array contents directly between [ and ]
    start = html.index("[", m.end() - 1)
    depth = 0
    for i in range(start, len(html)):
        if html[i] == "[":
            depth += 1
        elif html[i] == "]":
            depth -= 1
            if depth == 0:
                arr = html[start + 1 : i]
                break
    return {s.group(1) for s in re.finditer(r'"([^"]+)"', arr)}


def parse_register_calls(html: str) -> list[dict]:
    """Parse all registerSubdivision("key", { ... }) calls into dicts."""
    out = []
    for m in re.finditer(r'registerSubdivision\("([^"]+)",\s*\{', html):
        key = m.group(1)
        body, _ = parse_balanced(html, m.end() - 1)
        entry = {"key": key}
        for field in ("label", "flag", "localPath", "cdnUrl", "nameKey", "searchType"):
            fm = re.search(rf'\b{field}:\s*"((?:[^"\\]|\\.)*)"', body)
            if fm:
                entry[field] = fm.group(1).encode("utf-8").decode("unicode_escape")
        cap_m = re.search(r"\bcapitals:\s*(\w+)", body)
        if cap_m:
            entry["capitals_var"] = cap_m.group(1)
        no_m = re.search(r"\bnameOverrides:\s*\{", body)
        if no_m:
            no_body, _ = parse_balanced(body, no_m.end() - 1)
            entry["nameOverrides"] = parse_string_dict(no_body)
        out.append(entry)
    return out


def derive_continent(region: str, subregion: str) -> str:
    if region == "Americas":
        return "South America" if subregion == "South America" else "North America"
    if region == "Antarctic":
        return "Antarctica"
    return region or "Other"


def load_countries() -> tuple[list[dict], dict[str, list[dict]]]:
    """Load world-atlas + world-countries metadata, build a feature list
    matching the JS loader. Return (all_features, by_continent)."""
    with open(HERE / "countries-50m.json", encoding="utf-8") as f:
        topo = json.load(f)
    with open(HERE / "world-countries.json", encoding="utf-8") as f:
        meta_list = json.load(f)
    meta_by_id: dict[int, dict] = {}
    for m in meta_list:
        try:
            n = int(m.get("ccn3") or "")
        except (TypeError, ValueError):
            continue
        meta_by_id[n] = m

    geoms = topo["objects"]["countries"]["geometries"]
    out: list[dict] = []
    by_continent: dict[str, list[dict]] = {}
    for g in geoms:
        gid = g.get("id")
        try:
            n = int(gid)
        except (TypeError, ValueError):
            n = None
        meta = meta_by_id.get(n) if n is not None else None
        if meta:
            region = meta.get("region") or ""
            subregion = meta.get("subregion") or ""
            continent = derive_continent(region, subregion)
            name = (meta.get("name") or {}).get("common") or g.get("properties", {}).get("name", "")
            flag = meta.get("flag") or "🏳"
            cap_list = meta.get("capital") or []
            capital = cap_list[0] if cap_list else ""
        else:
            region = subregion = ""
            continent = "Other"
            name = g.get("properties", {}).get("name", "")
            flag = "🏳"
            capital = ""
        feat = {
            "name": name,
            "flag": flag,
            "capital": capital,
            "continent": continent,
            "subregion": subregion or continent,
        }
        out.append(feat)
        by_continent.setdefault(continent, []).append(feat)
    out.sort(key=lambda f: f["name"])
    for arr in by_continent.values():
        arr.sort(key=lambda f: f["name"])
    return out, by_continent


def load_us_states(html: str, capitals: dict[str, dict[str, str]]) -> list[dict]:
    state_caps = capitals.get("STATE_CAPITALS", {})
    states_50 = parse_us_states_50(html)
    with open(HERE / "states-10m.json", encoding="utf-8") as f:
        topo = json.load(f)
    out = []
    for g in topo["objects"]["states"]["geometries"]:
        name = g["properties"].get("name", "")
        if name not in states_50:
            continue
        out.append({"name": name, "flag": "🇺🇸", "capital": state_caps.get(name, "")})
    out.sort(key=lambda f: f["name"])
    return out


def load_subdivision(entry: dict, capitals: dict[str, dict[str, str]]) -> list[dict]:
    path = HERE / entry["localPath"]
    with open(path, encoding="utf-8") as f:
        geo = json.load(f)
    name_key = entry.get("nameKey", "name")
    overrides = entry.get("nameOverrides", {})
    caps = capitals.get(entry.get("capitals_var", ""), {})
    rules = SPECIAL_RULES.get(entry["key"], {})
    exclude_raw = rules.get("exclude_raw", set())
    strip_suffix = rules.get("strip_suffix")
    require_nonempty = rules.get("require_raw_nonempty", False)

    out = []
    for f in geo["features"]:
        raw = (f["properties"].get(name_key) or "").strip()
        if require_nonempty and not raw:
            continue
        if strip_suffix and raw.endswith(strip_suffix):
            raw = raw[: -len(strip_suffix)]
        if raw in exclude_raw:
            continue
        name = overrides.get(raw, raw)
        cap = caps.get(name, "") or caps.get(raw, "")
        out.append({"name": name, "flag": entry.get("flag", ""), "capital": cap})
    out.sort(key=lambda f: f["name"])
    return out


def md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def render_section(title: str, items: list[dict]) -> str:
    lines = [f"## {title}", "", f"_{len(items)} region(s)_", "", "| Name | Flag | Capital |", "|------|:----:|---------|"]
    for it in items:
        lines.append(
            f"| {md_escape(it['name'])} | {it.get('flag','')} | {md_escape(it.get('capital','') or '—')} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    html = HTML_PATH.read_text(encoding="utf-8")
    capitals = parse_capitals_dicts(html)
    sections: list[tuple[str, list[dict]]] = []

    countries, by_continent = load_countries()
    sections.append(("All Countries", countries))
    for c in CONTINENT_ORDER:
        if c in by_continent:
            sections.append((c, by_continent[c]))

    sections.append(("US States", load_us_states(html, capitals)))

    for entry in parse_register_calls(html):
        try:
            feats = load_subdivision(entry, capitals)
            sections.append((entry["label"], feats))
        except FileNotFoundError as e:
            print(f"# skip {entry['key']}: {e}", file=sys.stderr)

    parts = [
        "# Geography Quiz — Region Data",
        "",
        "Generated by `generate_geo_info.py` from the local HTML and GeoJSON files.",
        "Each section lists every region the quiz can prompt or display, with its",
        "flag emoji and the capital city the quiz shows.",
        "",
        "## Table of contents",
        "",
    ]
    for title, items in sections:
        anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        parts.append(f"- [{title}](#{anchor}) — {len(items)}")
    parts.append("")
    for title, items in sections:
        parts.append(render_section(title, items))
    md = "\n".join(parts) + "\n"

    sys.stdout.write(md)
    OUTPUT_PATH.write_text(md, encoding="utf-8")
    print(f"\nWrote {OUTPUT_PATH.relative_to(HERE)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
