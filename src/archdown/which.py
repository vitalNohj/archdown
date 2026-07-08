from __future__ import annotations

from dataclasses import dataclass

from archdown.search import _paint, should_color


@dataclass(frozen=True)
class PackageOwner:
    path: str
    name: str
    version: str = ""


def parse_owner_output(output: str) -> PackageOwner | None:
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if " is owned by " not in line:
            continue
        path, rest = line.split(" is owned by ", 1)
        name, _, version = rest.strip().rpartition(" ")
        if not name:
            name, version = rest.strip(), ""
        return PackageOwner(path.strip(), name.strip(), version.strip())
    return None


def render_owner(owner: PackageOwner, *, color: bool | None = None) -> str:
    use_color = should_color() if color is None else color
    title = "  ".join(part for part in (owner.name, owner.version) if part)
    lines = [_paint(title or "Package owner", "header", use_color)]
    if owner.path:
        lines.append(f"path: {_paint(owner.path, 'muted', use_color)}")
    return "\n".join(lines)
