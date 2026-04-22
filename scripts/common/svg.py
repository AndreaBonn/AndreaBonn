import html


def escape_svg(text: str) -> str:
    """Escape text for safe embedding in SVG/XML."""
    return html.escape(text, quote=True)


def wrap_text(text: str, max_chars: int = 45) -> list[str]:
    """Wrap text into lines of at most max_chars characters, breaking on words."""
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        if not line or len(line) + len(word) + 1 <= max_chars:
            line += ("" if not line else " ") + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def svg_lines(
    lines: list[str],
    start_y: int,
    *,
    line_height: int = 28,
    svg_width: int = 680,
    font_size: int = 18,
    italic: bool = False,
) -> str:
    """Render centered text lines as SVG <text> elements."""
    style = ' font-style="italic"' if italic else ""
    out = ""
    for i, line in enumerate(lines):
        out += (
            f'<text x="{svg_width // 2}" y="{start_y + i * line_height}" '
            f'font-family="monospace" font-size="{font_size}" fill="#e6edf3" '
            f'text-anchor="middle"{style}>{escape_svg(line)}</text>\n'
        )
    return out
