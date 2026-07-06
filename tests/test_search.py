from archdown.search import PackageSearchResult, parse_search_output, render_search_results


YAY_SEARCH = """aur/claude-code 1.0.44-1 (+12 1.50)
    Claude Code CLI
extra/claude-desktop 0.9.0-1 [installed]
    Desktop app for Claude
"""

PACMAN_SEARCH = """extra/claude-desktop 0.9.0-1 [installed]
    Desktop app for Claude
extra/claude-tools 2.0.0-1
    Helper tools for Claude
"""


def test_parse_search_output_extracts_package_fields():
    results = parse_search_output(YAY_SEARCH)
    assert results == [
        PackageSearchResult("aur", "claude-code", "1.0.44-1", False, "Claude Code CLI"),
        PackageSearchResult("extra", "claude-desktop", "0.9.0-1", True, "Desktop app for Claude"),
    ]


def test_render_search_results_groups_sources_and_aligns_columns():
    output = render_search_results(parse_search_output(YAY_SEARCH), color=False)
    assert "Official repositories" in output
    assert "AUR" in output
    assert "extra   claude-desktop" in output
    assert "installed" in output
    assert "  Desktop app for Claude" in output
    assert "aur     claude-code" in output
    assert "  Claude Code CLI" in output


def test_parse_search_output_handles_pacman_shape():
    results = parse_search_output(PACMAN_SEARCH)
    assert results[0].source == "extra"
    assert results[0].name == "claude-desktop"
    assert results[0].installed is True
    assert results[1].description == "Helper tools for Claude"


def test_render_search_results_empty_message():
    assert render_search_results([], color=False) == "No packages found."
