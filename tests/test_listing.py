from archdown.listing import (
    InstalledPackage,
    OutdatedPackage,
    classify_package,
    parse_list_output,
    parse_outdated_output,
    render_installed_packages,
    render_outdated_packages,
    sort_packages,
)


OUTDATED_OUTPUT = """ripgrep 14.1.1-1 -> 14.2.0-1
fd 10.2.0-1 -> 10.3.0-1
"""


def test_parse_outdated_output_extracts_version_transitions():
    packages = parse_outdated_output(OUTDATED_OUTPUT)
    assert packages == [
        OutdatedPackage("ripgrep", "14.1.1-1", "14.2.0-1"),
        OutdatedPackage("fd", "10.2.0-1", "10.3.0-1"),
    ]


def test_parse_outdated_output_ignores_lines_without_transition():
    packages = parse_outdated_output(":: Synchronizing package databases...\nripgrep 14.1.1-1 -> 14.2.0-1\n\n")
    assert packages == [OutdatedPackage("ripgrep", "14.1.1-1", "14.2.0-1")]


def test_render_outdated_packages_shows_aligned_transitions():
    output = render_outdated_packages(parse_outdated_output(OUTDATED_OUTPUT), color=False)
    assert "Outdated packages" in output
    assert "ripgrep  14.1.1-1 -> 14.2.0-1" in output
    assert "fd       10.2.0-1 -> 10.3.0-1" in output


def test_render_outdated_packages_supports_color():
    output = render_outdated_packages(parse_outdated_output(OUTDATED_OUTPUT), color=True)
    assert "\033[38;5;111mOutdated packages\033[0m" in output
    assert "\033[1mripgrep\033[0m" in output
    assert "\033[38;5;83m14.2.0-1\033[0m" in output
    # The transition stays readable without relying on color alone.
    assert " -> " in output


def test_render_outdated_packages_without_color_has_no_ansi():
    output = render_outdated_packages(parse_outdated_output(OUTDATED_OUTPUT), color=False)
    assert "\033[" not in output


def test_render_outdated_packages_empty_message():
    assert render_outdated_packages([], color=False) == "Everything is up to date."


LIST_OUTPUT = """firefox 152.0.4-1
neovim 0.11.5-1
ripgrep 14.1.1-1
base-devel 1-2
visual-studio-code-bin 1.102.0-1
bluez-utils 5.87-2
alacritty 0.17.0-1
jq 1.8.1-1
herdr 0.7.1-1
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
    assert "Libraries" in output
    assert "firefox" in output
    assert "152.0.4-1" in output
    assert "ripgrep" in output
    assert "14.1.1-1" in output
    assert "ripgrep" in output.split("Applications")[0]
    assert "firefox" in output.split("Applications")[1]
    assert "\033[" not in output


def test_render_installed_packages_puts_libraries_before_applications_and_repeats_labels():
    output = render_installed_packages(parse_list_output(LIST_OUTPUT), color=False, columns=3)
    lines = output.splitlines()

    assert lines.index("Libraries") < lines.index("Applications")
    assert output.count("Libraries") == 2
    assert output.count("Applications") == 2
    assert lines[0] == "Libraries"
    assert lines[-1] == "Applications"
    assert "ripgrep" in output.split("Applications")[0]
    assert "firefox" in output.split("Applications")[1]


def test_render_installed_packages_can_show_user_installed_section_with_adopt_hint():
    output = render_installed_packages(
        parse_list_output(LIST_OUTPUT),
        color=False,
        columns=3,
        managed={"herdr"},
    )
    lines = output.splitlines()

    assert lines.index("Libraries") < lines.index("Applications") < lines.index("User installed")
    assert "herdr" in output.split("User installed")[1]
    assert "adopt" in output
    assert "archdown adopt <package>" in output
    assert output.count("User installed") == 2
    assert lines[-1] == "User installed"


def test_render_installed_packages_marks_recently_updated_managed_packages_without_color():
    output = render_installed_packages(
        parse_list_output(LIST_OUTPUT),
        color=False,
        columns=3,
        managed={"herdr"},
        recent_updates={"herdr": ("0.7.0-1", "0.7.1-1")},
    )

    assert "herdr (Recently Updated 0.7.0-1 -> 0.7.1-1)" in output
    assert "\033[" not in output


def test_render_installed_packages_marks_recently_updated_managed_packages_with_green_color():
    output = render_installed_packages(
        parse_list_output(LIST_OUTPUT),
        color=True,
        columns=3,
        managed={"herdr"},
        recent_updates={"herdr": ("0.7.0-1", "0.7.1-1")},
    )

    assert "herdr" in output
    assert "\033[38;5;83m(Recently Updated 0.7.0-1 -> 0.7.1-1)\033[0m" in output


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


def test_render_installed_packages_marks_recently_updated_packages_in_managed_group():
    output = render_installed_packages(
        parse_list_output(LIST_OUTPUT),
        color=False,
        columns=3,
        managed={"herdr"},
        group_managed=True,
        recent_updates={"herdr": ("0.7.0-1", "0.7.1-1")},
    )

    assert "Installed with archdown" in output
    assert "herdr (Recently Updated 0.7.0-1 -> 0.7.1-1)" in output.split("Other installed packages")[0]
