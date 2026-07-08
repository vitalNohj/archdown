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


@dataclass(frozen=True)
class OutdatedPackage:
    name: str
    current_version: str
    new_version: str


def parse_outdated_output(output: str) -> list[OutdatedPackage]:
    packages: list[OutdatedPackage] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if " -> " not in line:
            continue
        left, right = line.split(" -> ", 1)
        left_parts = left.split()
        right_parts = right.split()
        if len(left_parts) < 2 or not right_parts:
            continue
        packages.append(OutdatedPackage(left_parts[0], left_parts[1], right_parts[0]))
    return packages


def render_outdated_packages(packages: Iterable[OutdatedPackage], *, color: bool | None = None) -> str:
    rows = list(packages)
    if not rows:
        return "Everything is up to date."

    use_color = should_color() if color is None else color
    title = "Outdated packages"
    name_width = max(len(row.name) for row in rows)
    current_width = max(len(row.current_version) for row in rows)

    lines = [_paint(title, "header", use_color), _paint("-" * len(title), "muted", use_color)]
    for row in rows:
        name = _paint(row.name.ljust(name_width), "name", use_color)
        current = _paint(row.current_version.ljust(current_width), "muted", use_color)
        new = _paint(row.new_version, "installed", use_color)
        lines.append(f"{name}  {current} -> {new}")
    return "\n".join(lines)


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
    recent_updates: dict[str, tuple[str, str]] | None = None,
    group_managed: bool = False,
    sort: Literal["name", "version", "managed", "none"] = "name",
) -> str:
    rows = sort_packages(packages, sort=sort, managed=managed)
    if not rows:
        return "No installed packages found."

    use_color = should_color() if color is None else color
    safe_columns = max(1, columns)
    managed_names = managed or set()
    update_markers = recent_updates or {}

    if group_managed:
        managed_rows = [row for row in rows if row.name in managed_names]
        other_rows = [row for row in rows if row.name not in managed_names]
        sections: list[str] = []
        if managed_rows:
            sections.extend(_render_package_grid("Installed with archdown", managed_rows, safe_columns, use_color, recent_updates=update_markers))
        if other_rows:
            if sections:
                sections.append("")
            sections.extend(_render_package_grid("Other installed packages", other_rows, safe_columns, use_color))
        return "\n".join(sections)

    user_installed = [row for row in rows if row.name in managed_names]
    untracked_rows = [row for row in rows if row.name not in managed_names]
    applications = [row for row in untracked_rows if classify_package(row) == "applications"]
    libraries = [row for row in untracked_rows if classify_package(row) == "utilities"]

    sections = []
    if libraries:
        sections.extend(_render_package_grid("Libraries", libraries, safe_columns, use_color))
    if applications:
        if sections:
            sections.append("")
        sections.extend(_render_package_grid("Applications", applications, safe_columns, use_color))
    if user_installed:
        if sections:
            sections.append("")
        sections.extend(
            _render_package_grid(
                "User installed",
                user_installed,
                safe_columns,
                use_color,
                recent_updates=update_markers,
                note="Packages tracked by archdown. Use `archdown adopt <package>` to track existing installs.",
            )
        )
    return "\n".join(sections)


def _render_package_grid(
    title: str,
    rows: list[InstalledPackage],
    columns: int,
    color: bool,
    *,
    recent_updates: dict[str, tuple[str, str]] | None = None,
    note: str = "",
) -> list[str]:
    cell_width = max(22, *(len(_format_package_name(row, recent_updates or {}, False)) for row in rows))
    lines = [_paint(title, "header", color), _paint("-" * len(title), "muted", color)]
    if note:
        lines.append(_paint(note, "muted", color))
    for index in range(0, len(rows), columns):
        chunk = rows[index : index + columns]
        name_cells = []
        version_cells = []
        for row in chunk:
            name_cells.append(_format_name_cell(row, recent_updates or {}, cell_width, color))
            version_cells.append(_paint(_trim(f"v {row.version}", cell_width).ljust(cell_width), "official", color))
        lines.append("  ".join(name_cells).rstrip())
        lines.append("  ".join(version_cells).rstrip())
    lines.append(_paint("-" * len(title), "muted", color))
    lines.append(_paint(title, "header", color))
    return lines


def _format_package_name(row: InstalledPackage, recent_updates: dict[str, tuple[str, str]], color: bool) -> str:
    if row.name not in recent_updates:
        return row.name
    old, new = recent_updates[row.name]
    marker = _paint(f"(Recently Updated {old} -> {new})", "installed", color)
    return f"{row.name} {marker}"


def _format_name_cell(row: InstalledPackage, recent_updates: dict[str, tuple[str, str]], width: int, color: bool) -> str:
    if row.name not in recent_updates:
        return _paint(_trim(row.name, width).ljust(width), "name", color)
    uncolored = _format_package_name(row, recent_updates, False)
    padding = " " * max(0, width - len(uncolored))
    old, new = recent_updates[row.name]
    marker = _paint(f"(Recently Updated {old} -> {new})", "installed", color)
    return f"{_paint(row.name, 'name', color)} {marker}{padding}"
