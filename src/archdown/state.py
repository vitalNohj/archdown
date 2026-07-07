from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, TypedDict

PackageVersionChanges = dict[str, tuple[str, str]]


class ManagedState(TypedDict):
    packages: list[str]
    versions: dict[str, str]


def default_state_path() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "archdown" / "managed-packages.json"


def _load_state(*, path: Path | None = None) -> ManagedState:
    state_path = path or default_state_path()
    if not state_path.exists():
        return {"packages": [], "versions": {}}
    try:
        data = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return {"packages": [], "versions": {}}
    if not isinstance(data, dict):
        return {"packages": [], "versions": {}}

    packages = data.get("packages", [])
    versions = data.get("versions", {})
    return {
        "packages": [str(package) for package in packages] if isinstance(packages, list) else [],
        "versions": {str(name): str(version) for name, version in versions.items()} if isinstance(versions, dict) else {},
    }


def load_managed_packages(*, path: Path | None = None) -> set[str]:
    return set(_load_state(path=path)["packages"])


def load_managed_package_versions(*, path: Path | None = None) -> dict[str, str]:
    return dict(_load_state(path=path)["versions"])


def save_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    state_path = path or default_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    package_names = sorted({package for package in packages if package})
    existing_versions = load_managed_package_versions(path=path)
    data = {
        "packages": package_names,
        "versions": {name: existing_versions[name] for name in package_names if name in existing_versions},
    }
    state_path.write_text(json.dumps(data, indent=2) + "\n")


def add_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    existing = load_managed_packages(path=path)
    existing.update(package for package in packages if package)
    save_managed_packages(existing, path=path)


def remove_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    existing = load_managed_packages(path=path)
    existing.difference_update(package for package in packages if package)
    save_managed_packages(existing, path=path)


def update_managed_package_versions(
    current_versions: dict[str, str],
    managed_packages: Iterable[str],
    *,
    path: Path | None = None,
) -> PackageVersionChanges:
    managed_names = {package for package in managed_packages if package}
    previous_versions = load_managed_package_versions(path=path)
    next_versions = {
        name: current_versions[name] if name in current_versions else previous_versions[name]
        for name in sorted(managed_names)
        if name in current_versions or name in previous_versions
    }
    changes = {
        name: (previous_versions[name], version)
        for name, version in next_versions.items()
        if name in previous_versions and previous_versions[name] != version
    }

    state_path = path or default_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "packages": sorted(managed_names),
                "versions": next_versions,
            },
            indent=2,
        )
        + "\n"
    )
    return changes
