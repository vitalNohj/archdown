from archdown.info import PackageInfo, parse_info_output, render_package_info


INFO_OUTPUT = """Repository      : extra
Name            : ripgrep
Version         : 14.1.1-1
Description     : A search tool that combines grep with useful defaults
Architecture    : x86_64
URL             : https://github.com/BurntSushi/ripgrep
Licenses        : MIT
Groups          : None
Provides        : None
Depends On      : gcc-libs  pcre2
Optional Deps   : None
Installed Size  : 5.27 MiB
Packager        : Arch Linux
Build Date      : Mon 01 Jan 2026 12:00:00 AM UTC
Validated By    : Signature
"""


def test_parse_info_output_extracts_fields():
    info = parse_info_output(INFO_OUTPUT)
    assert info.name == "ripgrep"
    assert info.version == "14.1.1-1"
    assert info.repository == "extra"
    assert info.description == "A search tool that combines grep with useful defaults"
    assert info.fields["URL"] == "https://github.com/BurntSushi/ripgrep"
    assert info.fields["Depends On"] == "gcc-libs  pcre2"


def test_render_package_info_prioritizes_main_fields_without_color():
    output = render_package_info(parse_info_output(INFO_OUTPUT), color=False)
    assert "ripgrep  14.1.1-1" in output
    assert "source: extra" in output
    assert "description: A search tool that combines grep with useful defaults" in output
    assert "URL" in output
    assert "Depends On" in output
    assert "\033[" not in output


def test_render_package_info_supports_color():
    output = render_package_info(PackageInfo(name="ripgrep", version="14.1.1-1", repository="extra", description="grep"), color=True)
    assert "\033[" in output
    assert "ripgrep" in output
