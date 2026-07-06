from archdown.listing import (
    InstalledPackage,
    classify_package,
    parse_list_output,
    render_installed_packages,
    sort_packages,
)


LIST_OUTPUT = """firefox 152.0.4-1
neovim 0.11.5-1
ripgrep 14.1.1-1
base-devel 1-2
visual-studio-code-bin 1.102.0-1
bluez-utils 5.87-2
alacritty 0.17.0-1
jq 1.8.1-1
"""


def test_parse_list_output_extracts_installed_packages():
    packages = parse_list_output("base 3-2\nbash 5.3.3-1\nripgrep 14.1.1-1\nvisual-studio-code-bin 1.102.0-1\n")
    assert packages == [
        InstalledPackage("base", "3-2"),
        InstalledPackage("bash", "5.3.3-1"),
        InstalledPackage("ripgrep", "14.1.1-1"),
        InstalledPackage("visual-studio-code-bin", "1.102.0-1"),
    ]


def test_classify_package_separates_apps_from_utilities():
    assert classify_package(InstalledPackage("firefox", "152.0.4-1")) == "applications"
    assert classify_package(InstalledPackage("visual-studio-code-bin", "1.102.0-1")) == "applications"
    assert classify_package(InstalledPackage("alacritty", "0.17.0-1")) == "applications"
    assert classify_package(InstalledPackage("ripgrep", "14.1.1-1")) == "utilities"
    assert classify_package(InstalledPackage("bluez-utils", "5.87-2")) == "utilities"
    assert classify_package(InstalledPackage("intel-ucode", "20260512-1")) == "utilities"
    assert classify_package(InstalledPackage("ttf-firacode-nerd", "3.4.0-2")) == "utilities"


def test_render_installed_packages_groups_and_uses_three_columns_without_color():
    output = render_installed_packages(parse_list_output(LIST_OUTPUT), color=False, columns=3)
    assert "Applications" in output
    assert "Utilities / system packages" in output
    assert "firefox" in output
    assert "152.0.4-1" in output
    assert "ripgrep" in output
    assert "14.1.1-1" in output
    assert "firefox" in output.split("Utilities / system packages")[0]
    assert "ripgrep" in output.split("Utilities / system packages")[1]
    assert "\033[" not in output


def test_render_installed_packages_puts_name_and_version_on_separate_rows():
    output = render_installed_packages(
        [
            InstalledPackage("firefox", "152.0.4-1"),
            InstalledPackage("neovim", "0.11.5-1"),
            InstalledPackage("alacritty", "0.17.0-1"),
        ],
        color=False,
        columns=3,
    )
    lines = output.splitlines()
    name_line = next(line for line in lines if "firefox" in line and "neovim" in line and "alacritty" in line)
    version_line = lines[lines.index(name_line) + 1]
    assert "v 152.0.4-1" in version_line
    assert "v 0.11.5-1" in version_line
    assert "v 0.17.0-1" in version_line
    assert "firefox" in name_line.split("neovim")[0]


def test_render_installed_packages_uses_tighter_cells():
    output = render_installed_packages(
        [
            InstalledPackage("firefox", "152.0.4-1"),
            InstalledPackage("neovim", "0.11.5-1"),
            InstalledPackage("alacritty", "0.17.0-1"),
        ],
        color=False,
        columns=3,
    )
    name_line = next(line for line in output.splitlines() if "firefox" in line and "neovim" in line)
    assert name_line.index("neovim") - name_line.index("firefox") <= 24


def test_render_installed_packages_supports_color():
    output = render_installed_packages([InstalledPackage("ripgrep", "14.1.1-1")], color=True)
    assert "\033[" in output
    assert "ripgrep" in output
    assert "14.1.1-1" in output


def test_render_installed_packages_handles_empty_results():
    assert render_installed_packages([], color=False) == "No installed packages found."


def test_sort_packages_supports_name_version_and_managed_ordering():
    packages = [
        InstalledPackage("ripgrep", "14.1.1-1"),
        InstalledPackage("firefox", "152.0.4-1"),
        InstalledPackage("fd", "10.3.0-1"),
    ]
    assert [pkg.name for pkg in sort_packages(packages, sort="name", managed=set())] == ["fd", "firefox", "ripgrep"]
    assert [pkg.name for pkg in sort_packages(packages, sort="version", managed=set())] == ["fd", "ripgrep", "firefox"]
    assert [pkg.name for pkg in sort_packages(packages, sort="managed", managed={"ripgrep"})] == ["ripgrep", "fd", "firefox"]


def test_render_installed_packages_can_separate_archdown_managed_packages():
    output = render_installed_packages(
        parse_list_output(LIST_OUTPUT),
        color=False,
        columns=3,
        managed={"firefox", "ripgrep"},
        group_managed=True,
    )
    assert "Installed with archdown" in output
    assert "Other installed packages" in output
    assert "firefox" in output.split("Other installed packages")[0]
    assert "ripgrep" in output.split("Other installed packages")[0]
    assert "base-devel" in output.split("Other installed packages")[1]
