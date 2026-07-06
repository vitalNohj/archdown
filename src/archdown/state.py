from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable


def default_state_path() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_home / "archdown" / "managed-packages.json"


def load_managed_packages(*, path: Path | None = None) -> set[str]:
    state_path = path or default_state_path()
    if not state_path.exists():
        return set()
    try:
        data = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return set()
    packages = data.get("packages", []) if isinstance(data, dict) else []
    return {str(package) for package in packages}


def save_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    state_path = path or default_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"packages": sorted({package for package in packages if package})}
    state_path.write_text(json.dumps(data, indent=2) + "\n")


def add_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    existing = load_managed_packages(path=path)
    existing.update(package for package in packages if package)
    save_managed_packages(existing, path=path)


def remove_managed_packages(packages: Iterable[str], *, path: Path | None = None) -> None:
    existing = load_managed_packages(path=path)
    existing.difference_update(package for package in packages if package)
    save_managed_packages(existing, path=path)
