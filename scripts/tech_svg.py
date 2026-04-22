"""SVG generation for the Tech Stack word cloud."""

from common.svg import escape_svg
from tech_mappings import CATEGORIES


def measure_text(text: str, font_size: int) -> int:
    """Stima larghezza testo monospace."""
    return int(len(text) * font_size * 0.62) + 16


def generate_svg(data: dict[str, dict[str, int]]) -> str:
    SVG_W = 880
    PADDING_X = 24
    PILL_H = 28
    PILL_GAP = 8
    SECTION_GAP = 16
    HEADER_H = 28

    def get_items(cat_data: dict[str, int]) -> list[tuple[str, int, int]]:
        """Ritorna [(name, count, font_size)] ordinati per count desc."""
        if not cat_data:
            return []
        items = sorted(cat_data.items(), key=lambda x: -x[1])
        max_count = items[0][1]
        min_count = items[-1][1]
        result = []
        for name, count in items:
            if max_count == min_count:
                ratio = 1.0
            else:
                ratio = (count - min_count) / (max_count - min_count)
            font_size = int(11 + ratio * 5)  # 11-16px range
            result.append((name, count, font_size))
        return result

    # Pre-calculate layout
    sections = []
    y_cursor = 28 + 10  # dopo top bar

    for cat_key, cat_info in CATEGORIES.items():
        items = get_items(data.get(cat_key, {}))
        if not items:
            continue

        section_y = y_cursor
        y_cursor += HEADER_H

        # Layout pills in rows
        rows = []
        current_row = []
        row_w = PADDING_X

        for name, count, font_size in items:
            pill_w = measure_text(name, font_size) + 12
            if row_w + pill_w + PILL_GAP > SVG_W - PADDING_X and current_row:
                rows.append(current_row)
                current_row = []
                row_w = PADDING_X
            current_row.append((name, count, font_size, pill_w))
            row_w += pill_w + PILL_GAP

        if current_row:
            rows.append(current_row)

        y_cursor += len(rows) * (PILL_H + PILL_GAP)
        y_cursor += SECTION_GAP

        sections.append(
            {
                "cat": cat_key,
                "info": cat_info,
                "rows": rows,
                "y": section_y,
            }
        )

    SVG_H = y_cursor + 10

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SVG_W} {SVG_H}" width="100%">',
        f'  <rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="#0d1117"/>',
        f'  <rect x="1" y="1" width="{SVG_W - 2}" height="{SVG_H - 2}" rx="9" fill="none" stroke="#30363d" stroke-width="1.5"/>',
        # Top bar
        f'  <rect x="1" y="1" width="{SVG_W - 2}" height="26" rx="9" fill="#1c2128"/>',
        f'  <rect x="1" y="18" width="{SVG_W - 2}" height="9" fill="#1c2128"/>',
        f'  <line x1="1" y1="27" x2="{SVG_W - 1}" y2="27" stroke="#30363d" stroke-width="1"/>',
        '  <circle cx="16" cy="14" r="3" fill="#e6861a" opacity="0.8"/>',
        f'  <circle cx="{SVG_W - 16}" cy="14" r="3" fill="#e6861a" opacity="0.8"/>',
        f'  <text x="{SVG_W // 2}" y="19" text-anchor="middle" font-family="monospace" font-size="11" fill="#8b949e" letter-spacing="4" font-weight="bold">TECH STACK</text>',
    ]

    for section in sections:
        info = section["info"]
        y = section["y"]

        # Category label
        svg_parts.append(
            f'  <text x="{PADDING_X}" y="{y + 18}" font-family="monospace" '
            f'font-size="12" fill="{info["color"]}" letter-spacing="2" '
            f'font-weight="bold">{info["label"]}</text>'
        )

        # Separator line
        svg_parts.append(
            f'  <line x1="{PADDING_X}" y1="{y + 24}" '
            f'x2="{SVG_W - PADDING_X}" y2="{y + 24}" '
            f'stroke="{info["color"]}" stroke-width="0.5" opacity="0.3"/>'
        )

        pill_y = y + HEADER_H
        for row in section["rows"]:
            # Center the row
            total_row_w = sum(pw for _, _, _, pw in row) + PILL_GAP * (len(row) - 1)
            x = (SVG_W - total_row_w) // 2

            for name, _count, font_size, pill_w in row:
                # Pill background
                svg_parts.append(
                    f'  <rect x="{x}" y="{pill_y}" width="{pill_w}" '
                    f'height="{PILL_H}" rx="14" fill="{info["bg"]}" '
                    f'stroke="{info["color"]}" stroke-width="0.8" opacity="0.9"/>'
                )
                # Pill text
                text_y = pill_y + PILL_H // 2 + font_size // 3
                svg_parts.append(
                    f'  <text x="{x + pill_w // 2}" y="{text_y}" '
                    f'text-anchor="middle" font-family="monospace" '
                    f'font-size="{font_size}" fill="{info["color"]}" '
                    f'font-weight="{"bold" if font_size >= 14 else "normal"}">'
                    f"{escape_svg(name)}</text>"
                )
                x += pill_w + PILL_GAP

            pill_y += PILL_H + PILL_GAP

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)
