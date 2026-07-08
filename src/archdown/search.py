from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Iterable

RESET = "\033[0m"
COLORS = {
    "header": "\033[38;5;111m",
    "official": "\033[38;5;75m",
    "aur": "\033[38;5;214m",
    "name": "\033[1m",
    "installed": "\033[38;5;83m",
    "muted": "\033[38;5;245m",
}


@dataclass(frozen=True)
class PackageSearchResult:
    source: str
    name: str
    version: str
    installed: bool = False
    description: str = ""

    @property
    def is_aur(self) -> bool:
        return self.source.lower() == "aur"


def parse_search_output(output: str) -> list[PackageSearchResult]:
    results: list[PackageSearchResult] = []
    current: PackageSearchResult | None = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        if not line.startswith((" ", "\t")):
            current = _parse_result_header(line)
            if current:
                results.append(current)
            continue

        if current and not current.description:
            description = line.strip()
            results[-1] = PackageSearchResult(
                current.source,
                current.name,
                current.version,
                current.installed,
                description,
            )
            current = results[-1]

    return results


def _parse_result_header(line: str) -> PackageSearchResult | None:
    first, *_ = line.split(maxsplit=1)
    if "/" not in first:
        return None

    source, name = first.split("/", 1)
    rest = line[len(first):].strip()
    version = rest.split(maxsplit=1)[0] if rest else ""
    lowered = line.lower()
    installed = "[installed" in lowered or "(installed" in lowered
    return PackageSearchResult(source, name, version, installed)


def render_search_results(results: Iterable[PackageSearchResult], *, color: bool | None = None) -> str:
    rows = list(results)
    if not rows:
        return "No packages found."

    use_color = should_color() if color is None else color
    official = [row for row in rows if not row.is_aur]
    aur = [row for row in rows if row.is_aur]

    source_width = max((len(row.source) for row in rows), default=6)
    name_width = min(max((len(row.name) for row in rows), default=4), 32)
    version_width = min(max((len(row.version) for row in rows), default=7), 18)

    sections: list[str] = []
    if official:
        sections.extend(_render_section("Official repositories", official, source_width, name_width, version_width, use_color))
    if aur:
        if sections:
            sections.append("")
        sections.extend(_render_section("AUR", aur, source_width, name_width, version_width, use_color))
    return "\n".join(sections)


def _render_section(
    title: str,
    rows: list[PackageSearchResult],
    source_width: int,
    name_width: int,
    version_width: int,
    color: bool,
) -> list[str]:
    lines = [_paint(title, "header", color), _paint("-" * len(title), "muted", color)]
    for row in rows:
        source = _paint(row.source.ljust(source_width), "aur" if row.is_aur else "official", color)
        name = _paint(_trim(row.name, name_width).ljust(name_width), "name", color)
        version = _trim(row.version, version_width).ljust(version_width)
        installed = _paint("installed", "installed", color) if row.installed else ""
        lines.append(f"{source}   {name}  {version}  {installed}".rstrip())
        if row.description:
            lines.append(f"  {_paint(row.description, 'muted', color)}")
    return lines


def should_color() -> bool:
    if "NO_COLOR" in os.environ:
        return False
    return sys.stdout.isatty()


def _paint(text: str, color_name: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{COLORS[color_name]}{text}{RESET}"


def _trim(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: max(0, width - 1)] + "…"
