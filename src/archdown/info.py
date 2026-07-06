from __future__ import annotations

from dataclasses import dataclass, field

from archdown.search import _paint, should_color

MAIN_KEYS = {
    "Repository": "repository",
    "Name": "name",
    "Version": "version",
    "Description": "description",
}


@dataclass(frozen=True)
class PackageInfo:
    name: str = ""
    version: str = ""
    repository: str = ""
    description: str = ""
    fields: dict[str, str] = field(default_factory=dict)


def parse_info_output(output: str) -> PackageInfo:
    fields: dict[str, str] = {}
    current_key = ""
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        if ":" in raw_line:
            key, value = raw_line.split(":", 1)
            current_key = key.strip()
            fields[current_key] = value.strip()
        elif current_key:
            fields[current_key] = f"{fields[current_key]} {raw_line.strip()}".strip()

    return PackageInfo(
        name=fields.get("Name", ""),
        version=fields.get("Version", ""),
        repository=fields.get("Repository", ""),
        description=fields.get("Description", ""),
        fields=fields,
    )


def render_package_info(info: PackageInfo, *, color: bool | None = None) -> str:
    use_color = should_color() if color is None else color
    title = "  ".join(part for part in (info.name, info.version) if part)
    lines = [_paint(title or "Package information", "header", use_color)]
    if info.repository:
        lines.append(f"source: {_paint(info.repository, 'official' if info.repository.lower() != 'aur' else 'aur', use_color)}")
    if info.description:
        lines.append(f"description: {_paint(info.description, 'muted', use_color)}")

    extra_fields = [(key, value) for key, value in info.fields.items() if key not in MAIN_KEYS]
    if extra_fields:
        lines.append("")
        label_width = max(len(key) for key, _ in extra_fields)
        for key, value in extra_fields:
            lines.append(f"{key.ljust(label_width)}  {value}")
    return "\n".join(lines)
