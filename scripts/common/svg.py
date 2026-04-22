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
