from archdown.which import PackageOwner, parse_owner_output, render_owner


def test_parse_owner_output_extracts_path_name_version():
    owner = parse_owner_output("/usr/bin/rg is owned by ripgrep 15.1.0-4\n")
    assert owner == PackageOwner("/usr/bin/rg", "ripgrep", "15.1.0-4")


def test_parse_owner_output_handles_missing_version():
    owner = parse_owner_output("/usr/bin/rg is owned by ripgrep\n")
    assert owner == PackageOwner("/usr/bin/rg", "ripgrep", "")


def test_parse_owner_output_returns_none_on_error_line():
    assert parse_owner_output("error: No package owns /usr/bin/nope\n") is None
    assert parse_owner_output("") is None


def test_render_owner_leads_with_identity_and_shows_path():
    owner = PackageOwner("/usr/bin/rg", "ripgrep", "15.1.0-4")
    rendered = render_owner(owner, color=False)
    assert rendered == "ripgrep  15.1.0-4\npath: /usr/bin/rg"


def test_render_owner_without_version():
    owner = PackageOwner("/usr/bin/rg", "ripgrep", "")
    assert render_owner(owner, color=False) == "ripgrep\npath: /usr/bin/rg"
