#!/usr/bin/env python3
"""Inline the 5 base JSON data files into each HTML app.

Once inlined, the apps load their base data directly from inline
<script type="application/json"> blocks instead of fetch()ing it,
which lets them work under the file:// scheme where fetch is blocked.

Idempotent: a BEGIN/END comment pair marks the inserted block, and
re-running this script replaces that block in place. Pass --remove
to strip the block (so the apps fall back to local-file then CDN
loading as before).

Run:
    python3 inline_data.py            # inline / re-inline
    python3 inline_data.py --remove   # remove inlined blocks
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent

JSON_FILES = [
    "countries-50m.json",
    "countries-110m.json",
    "world-countries.json",
    "ne_50m_lakes.json",
    "ne_50m_rivers_lake_centerlines.json",
]

HTML_FILES = [
    "no-borders-geography.html",
    "simple-mercator-world-map.html",
    "simple-robinson-world-map.html",
]

BEGIN = "<!-- BEGIN INLINED DATA -->"
END = "<!-- END INLINED DATA -->"
INSERT_BEFORE = '<script src="d3.v7.min.js">'


def build_block() -> str:
    """Produce the BEGIN/END-wrapped block with one <script> per JSON."""
    parts = [BEGIN]
    for fname in JSON_FILES:
        path = HERE / fname
        text = path.read_text(encoding="utf-8")
        # Validate it's parsable JSON.
        json.loads(text)
        # The HTML parser only ends a <script> on </script>; pre-escape
        # any </ to <\/ so the JSON can never close the host script tag
        # (JSON.parse turns \/ back into /).
        safe = text.replace("</", "<\\/")
        slug = fname.rsplit(".", 1)[0]
        parts.append(f'<script type="application/json" id="data-{slug}">{safe}</script>')
    parts.append(END)
    return "\n".join(parts)


def inject(html: str, block: str) -> str:
    """Insert (or replace) the inlined-data block in an HTML string."""
    begin_idx = html.find(BEGIN)
    end_idx = html.find(END)
    if begin_idx >= 0 and end_idx >= 0:
        # Replace existing block
        end_idx += len(END)
        # Trim leading whitespace before existing block so re-inserting
        # doesn't accumulate blank lines.
        line_start = html.rfind("\n", 0, begin_idx) + 1
        return html[:line_start] + block + "\n" + html[end_idx:].lstrip("\n")
    # First insert: anchor on the d3 script tag and place the block right
    # before it on its own line.
    idx = html.find(INSERT_BEFORE)
    if idx < 0:
        raise SystemExit(f"  ✗ marker {INSERT_BEFORE!r} not found")
    line_start = html.rfind("\n", 0, idx) + 1
    indent = html[line_start:idx]  # preserve indentation level
    return html[:line_start] + block + "\n" + indent + html[idx:]


def remove(html: str) -> str:
    begin_idx = html.find(BEGIN)
    end_idx = html.find(END)
    if begin_idx < 0 or end_idx < 0:
        return html
    end_idx += len(END)
    line_start = html.rfind("\n", 0, begin_idx) + 1
    return html[:line_start] + html[end_idx:].lstrip("\n")


def main() -> int:
    removing = "--remove" in sys.argv[1:]
    block = None if removing else build_block()

    for fname in HTML_FILES:
        path = HERE / fname
        before = path.stat().st_size
        html = path.read_text(encoding="utf-8")
        new_html = remove(html) if removing else inject(html, block)
        path.write_text(new_html, encoding="utf-8")
        after = path.stat().st_size
        delta = after - before
        sign = "+" if delta >= 0 else ""
        print(f"  {fname}: {before:>10,} → {after:>10,} bytes ({sign}{delta:,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
