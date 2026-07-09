from __future__ import annotations

from archdown.search import _paint, should_color

# How many dependents to list before summarizing the rest. Reverse-dependency
# trees for core packages (glibc, gcc-libs, ...) can run to thousands of lines;
# capping keeps the output friendly while the summary keeps it honest.
DEFAULT_LIMIT = 40

# Leading characters pactree draws for its graph output (unicode and ASCII
# forms), stripped so a package name can be read regardless of layout mode.
_TREE_GLYPHS = "├└│─╰╭ \t|`+-"


def parse_pactree_dependents(output: str, package: str) -> list[str]:
    dependents: list[str] = []
    seen: set[str] = set()
    for raw_line in output.splitlines():
        line = raw_line.strip().lstrip(_TREE_GLYPHS).strip()
        if not line:
            continue
        # The first token is the package name; pactree may append a
        # " provides ..." annotation we do not want to treat as a name.
        name = line.split()[0]
        if name == package or name in seen:
            continue
        seen.add(name)
        dependents.append(name)
    return dependents


def parse_required_by(output: str) -> list[str]:
    for raw_line in output.splitlines():
        if not raw_line.startswith("Required By"):
            continue
        _, _, value = raw_line.partition(":")
        value = value.strip()
        if not value or value == "None":
            return []
        return value.split()
    return []


def render_dependents(
    package: str,
    dependents: list[str],
    *,
    color: bool | None = None,
    limit: int = DEFAULT_LIMIT,
) -> str:
    use_color = should_color() if color is None else color
    if not dependents:
        return f"Nothing depends on {package}."

    ordered = sorted(dict.fromkeys(dependents))
    total = len(ordered)
    title = f"Packages that depend on {package}"
    lines = [_paint(title, "header", use_color), _paint("-" * len(title), "muted", use_color)]
    for name in ordered[:limit]:
        lines.append(_paint(name, "name", use_color))
    if total > limit:
        remaining = total - limit
        lines.append(_paint(f"… and {remaining} more ({total} total)", "muted", use_color))
    return "\n".join(lines)
