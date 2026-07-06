from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from archdown.search import _paint, _trim, should_color

APPLICATION_NAMES = {
    "alacritty",
    "brave-bin",
    "chromium",
    "cursor-bin",
    "discord",
    "firefox",
    "foot",
    "ghostty",
    "gnome-terminal",
    "kitty",
    "libreoffice-fresh",
    "neovim",
    "obsidian",
    "slack-desktop",
    "thunderbird",
    "visual-studio-code-bin",
    "wezterm",
}
APPLICATION_KEYWORDS = (
    "browser",
    "code",
    "desktop",
    "editor",
    "firefox",
    "office",
    "studio",
    "terminal",
)
UTILITY_KEYWORDS = (
    "base",
    "cli",
    "dkms",
    "driver",
    "firmware",
    "font",
    "git",
    "grep",
    "lib",
    "linux",
    "pipewire",
    "ttf",
    "ucode",
    "utils",
    "xdg",
)


@dataclass(frozen=True)
class InstalledPackage:
    name: str
    version: str


def parse_list_output(output: str) -> list[InstalledPackage]:
    packages: list[InstalledPackage] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        name, *rest = line.split(maxsplit=1)
        packages.append(InstalledPackage(name, rest[0] if rest else ""))
    return packages


def classify_package(package: InstalledPackage) -> str:
    name = package.name.lower()
    if name in APPLICATION_NAMES:
        return "applications"
    if any(keyword in name for keyword in APPLICATION_KEYWORDS) and not any(keyword in name for keyword in UTILITY_KEYWORDS):
        return "applications"
    return "utilities"


def sort_packages(packages: Iterable[InstalledPackage], *, sort: Literal["name", "version", "managed", "none"] = "name", managed: set[str] | None = None) -> list[InstalledPackage]:
    rows = list(packages)
    managed_names = managed or set()
    if sort == "none":
        return rows
    if sort == "version":
        return sorted(rows, key=lambda package: (package.version, package.name))
    if sort == "managed":
        return sorted(rows, key=lambda package: (package.name not in managed_names, package.name))
    return sorted(rows, key=lambda package: package.name)


def render_installed_packages(
    packages: Iterable[InstalledPackage],
    *,
    color: bool | None = None,
    columns: int = 3,
    managed: set[str] | None = None,
    group_managed: bool = False,
    sort: Literal["name", "version", "managed", "none"] = "name",
) -> str:
    rows = sort_packages(packages, sort=sort, managed=managed)
    if not rows:
        return "No installed packages found."

    use_color = should_color() if color is None else color
    safe_columns = max(1, columns)
    managed_names = managed or set()

    if group_managed:
        managed_rows = [row for row in rows if row.name in managed_names]
        other_rows = [row for row in rows if row.name not in managed_names]
        sections: list[str] = []
        if managed_rows:
            sections.extend(_render_package_grid("Installed with archdown", managed_rows, safe_columns, use_color))
        if other_rows:
            if sections:
                sections.append("")
            sections.extend(_render_package_grid("Other installed packages", other_rows, safe_columns, use_color))
        return "\n".join(sections)

    applications = [row for row in rows if classify_package(row) == "applications"]
    utilities = [row for row in rows if classify_package(row) == "utilities"]

    sections = []
    if applications:
        sections.extend(_render_package_grid("Applications", applications, safe_columns, use_color))
    if utilities:
        if sections:
            sections.append("")
        sections.extend(_render_package_grid("Utilities / system packages", utilities, safe_columns, use_color))
    return "\n".join(sections)


def _render_package_grid(title: str, rows: list[InstalledPackage], columns: int, color: bool) -> list[str]:
    cell_width = 22
    lines = [_paint(title, "header", color), _paint("-" * len(title), "muted", color)]
    for index in range(0, len(rows), columns):
        chunk = rows[index : index + columns]
        name_cells = []
        version_cells = []
        for row in chunk:
            name_cells.append(_paint(_trim(row.name, cell_width).ljust(cell_width), "name", color))
            version_cells.append(_paint(_trim(f"v {row.version}", cell_width).ljust(cell_width), "official", color))
        lines.append("  ".join(name_cells).rstrip())
        lines.append("  ".join(version_cells).rstrip())
    return lines
