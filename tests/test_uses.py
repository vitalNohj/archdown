from archdown.uses import parse_pactree_dependents, parse_required_by, render_dependents


def test_parse_pactree_dependents_excludes_root_and_dedupes():
    output = "openssl\ncurl\ngit\ncurl\nwget\n"
    assert parse_pactree_dependents(output, "openssl") == ["curl", "git", "wget"]


def test_parse_pactree_dependents_strips_tree_glyphs_and_annotations():
    output = "openssl\n├─curl\n│ └─git provides libgit\n└─wget\n"
    assert parse_pactree_dependents(output, "openssl") == ["curl", "git", "wget"]


def test_parse_pactree_dependents_empty_when_only_root():
    assert parse_pactree_dependents("leaf-pkg\n", "leaf-pkg") == []


def test_parse_required_by_reads_names():
    output = "Name            : openssl\nRequired By     : curl  git  wget\nDepends On      : glibc\n"
    assert parse_required_by(output) == ["curl", "git", "wget"]


def test_parse_required_by_none_is_empty():
    assert parse_required_by("Required By     : None\n") == []
    assert parse_required_by("Name : openssl\n") == []


def test_render_dependents_lists_sorted_names():
    rendered = render_dependents("openssl", ["wget", "curl", "git"], color=False)
    assert rendered == "Packages that depend on openssl\n-------------------------------\ncurl\ngit\nwget"


def test_render_dependents_reports_nothing_when_empty():
    assert render_dependents("openssl", [], color=False) == "Nothing depends on openssl."


def test_render_dependents_caps_large_lists_with_honest_total():
    dependents = [f"pkg{i:03d}" for i in range(100)]
    rendered = render_dependents("glibc", dependents, color=False, limit=3)
    lines = rendered.splitlines()
    assert lines[0] == "Packages that depend on glibc"
    assert lines[2:5] == ["pkg000", "pkg001", "pkg002"]
    assert lines[-1] == "… and 97 more (100 total)"
