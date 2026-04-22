from common.config import ASSETS_DIR, USERNAME
from common.svg import escape_svg, wrap_text


def test_escape_svg_angle_brackets():
    assert escape_svg("<script>") == "&lt;script&gt;"


def test_escape_svg_ampersand():
    assert escape_svg("a & b") == "a &amp; b"


def test_escape_svg_quotes():
    assert escape_svg('"hello"') == "&quot;hello&quot;"


def test_escape_svg_clean_string():
    assert escape_svg("hello world") == "hello world"


def test_wrap_text_short_string():
    assert wrap_text("hello", max_chars=45) == ["hello"]


def test_wrap_text_exact_fit():
    result = wrap_text("ab cd", max_chars=5)
    assert result == ["ab cd"]


def test_wrap_text_wraps_correctly():
    result = wrap_text("one two three four", max_chars=10)
    assert result == ["one two", "three four"]


def test_wrap_text_empty_string():
    assert wrap_text("") == []


def test_wrap_text_single_long_word():
    result = wrap_text("superlongword", max_chars=5)
    assert result == ["superlongword"]


def test_username_is_andreabonn():
    assert USERNAME == "AndreaBonn"


def test_assets_dir_ends_with_assets():
    assert ASSETS_DIR.name == "assets"


def test_svg_lines_renders_text():
    from common.svg import svg_lines

    result = svg_lines(["Hello", "World"], start_y=100)
    assert "Hello" in result
    assert "World" in result
    assert "<text" in result


def test_svg_lines_italic():
    from common.svg import svg_lines

    result = svg_lines(["Test"], start_y=100, italic=True)
    assert 'font-style="italic"' in result


def test_svg_lines_no_italic_by_default():
    from common.svg import svg_lines

    result = svg_lines(["Test"], start_y=100)
    assert "italic" not in result


def test_svg_lines_escapes_special_chars():
    from common.svg import svg_lines

    result = svg_lines(["A < B & C"], start_y=100)
    assert "&lt;" in result
    assert "&amp;" in result
