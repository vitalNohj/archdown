from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Backend:
    name: str
    install: list[str]
    uninstall: list[str]
    search: list[str]
    list_installed: list[str]
    refresh: list[str]
    upgrade: list[str]


def make_backend(name: str) -> Backend:
    if name == "paru":
        return Backend("paru", ["paru", "-S"], ["paru", "-Rns"], ["paru", "-Ss"], ["paru", "-Qe"], ["paru", "-Sy"], ["paru", "-Syu"])
    if name == "yay":
        return Backend("yay", ["yay", "-S"], ["yay", "-Rns"], ["yay", "-Ss"], ["yay", "-Qe"], ["yay", "-Sy"], ["yay", "-Syu"])
    if name == "pacman":
        return Backend("pacman", ["sudo", "pacman", "-S"], ["sudo", "pacman", "-Rns"], ["pacman", "-Ss"], ["pacman", "-Qe"], ["sudo", "pacman", "-Sy"], ["sudo", "pacman", "-Syu"])
    raise AssertionError(f"Unknown backend: {name}")


def detect_backend() -> Backend:
    for candidate in ("paru", "yay", "pacman"):
        if shutil.which(candidate):
            return make_backend(candidate)
    raise SystemExit("archdown could not find paru, yay, or pacman in PATH")


def run(cmd: Sequence[str], dry_run: bool) -> int:
    pretty = " ".join(cmd)
    print(f"backend command: {pretty}")
    if dry_run:
        return 0
    completed = subprocess.run(list(cmd))
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archdown",
        description="A friendly Homebrew-style wrapper over Arch package tooling.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the backend command without executing it")
    parser.add_argument("--backend", choices=["auto", "paru", "yay", "pacman"], default="auto", help="Force a backend")

    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Install one or more packages")
    install.add_argument("packages", nargs="+", help="Package names")

    uninstall = sub.add_parser("uninstall", help="Remove one or more packages with dependencies no longer needed")
    uninstall.add_argument("packages", nargs="+", help="Package names")

    search = sub.add_parser("search", help="Search official repos and AUR when supported")
    search.add_argument("query", nargs="+", help="Search terms")

    sub.add_parser("list", help="List explicitly installed packages")
    sub.add_parser("refresh", help="Refresh package databases only")
    sub.add_parser("upgrade", help="Upgrade the full system")
    sub.add_parser("update", help="Alias for upgrade; safer than Homebrew-style split semantics on Arch")
    return parser


def select_backend(name: str) -> Backend:
    if name == "auto":
        return detect_backend()
    if not shutil.which(name):
        raise SystemExit(f"Requested backend '{name}' is not installed")
    return make_backend(name)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    backend = select_backend(args.backend)

    if args.command == "install":
        return run([*backend.install, *args.packages], args.dry_run)
    if args.command == "uninstall":
        return run([*backend.uninstall, *args.packages], args.dry_run)
    if args.command == "search":
        return run([*backend.search, *args.query], args.dry_run)
    if args.command == "list":
        return run(backend.list_installed, args.dry_run)
    if args.command == "refresh":
        print("warning: refresh only syncs databases. On Arch, full upgrades are usually safer.", file=sys.stderr)
        return run(backend.refresh, args.dry_run)
    if args.command in {"upgrade", "update"}:
        return run(backend.upgrade, args.dry_run)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
