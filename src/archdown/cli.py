from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence

from archdown.info import parse_info_output, render_package_info
from archdown.listing import parse_list_output, render_installed_packages
from archdown.search import parse_search_output, render_search_results
from archdown.state import add_managed_packages, load_managed_packages, remove_managed_packages


@dataclass(frozen=True)
class Backend:
    name: str
    install: list[str]
    uninstall: list[str]
    search: list[str]
    list_installed: list[str]
    refresh: list[str]
    upgrade: list[str]
    info: list[str]


def make_backend(name: str) -> Backend:
    if name == "paru":
        return Backend(
            "paru",
            ["paru", "-S"],
            ["paru", "-Rns"],
            ["paru", "-Ss"],
            ["paru", "-Qe"],
            ["paru", "-Sy"],
            ["paru", "-Syu"],
            ["paru", "-Si"],
        )
    if name == "yay":
        return Backend(
            "yay",
            ["yay", "-S"],
            ["yay", "-Rns"],
            ["yay", "-Ss"],
            ["yay", "-Qe"],
            ["yay", "-Sy"],
            ["yay", "-Syu"],
            ["yay", "-Si"],
        )
    if name == "pacman":
        return Backend(
            "pacman",
            ["sudo", "pacman", "-S"],
            ["sudo", "pacman", "-Rns"],
            ["pacman", "-Ss"],
            ["pacman", "-Qe"],
            ["sudo", "pacman", "-Sy"],
            ["sudo", "pacman", "-Syu"],
            ["pacman", "-Si"],
        )
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


def run_install(cmd: Sequence[str], packages: Sequence[str], dry_run: bool) -> int:
    code = run(cmd, dry_run)
    if code == 0 and not dry_run:
        add_managed_packages(packages)
    return code


def run_uninstall(cmd: Sequence[str], packages: Sequence[str], dry_run: bool) -> int:
    code = run(cmd, dry_run)
    if code == 0 and not dry_run:
        remove_managed_packages(packages)
    return code


def run_search(cmd: Sequence[str], *, dry_run: bool, raw: bool, color: bool | None) -> int:
    pretty = " ".join(cmd)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(list(cmd), capture_output=True, text=True)
    output = completed.stdout
    if raw:
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode

    results = parse_search_output(output)
    if results:
        print(render_search_results(results, color=color))
    else:
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def run_list(
    cmd: Sequence[str],
    *,
    dry_run: bool,
    raw: bool,
    color: bool | None,
    sort: str,
    group: str,
    columns: int,
) -> int:
    pretty = " ".join(cmd)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(list(cmd), capture_output=True, text=True)
    output = completed.stdout
    if raw:
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode

    packages = parse_list_output(output)
    managed = load_managed_packages()
    print(
        render_installed_packages(
            packages,
            color=color,
            columns=columns,
            managed=managed,
            group_managed=group == "managed",
            sort=sort,
        )
    )
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def run_info(cmd: Sequence[str], *, dry_run: bool, raw: bool, color: bool | None) -> int:
    pretty = " ".join(cmd)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(list(cmd), capture_output=True, text=True)
    output = completed.stdout
    if raw:
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode

    info = parse_info_output(output)
    print(render_package_info(info, color=color))
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def run_adopt(cmd: Sequence[str], *, packages: Sequence[str], from_current: bool, dry_run: bool) -> int:
    if not packages and not from_current:
        raise SystemExit("adopt requires package names or --from-current")

    adopted = list(packages)
    if from_current:
        completed = subprocess.run(list(cmd), capture_output=True, text=True)
        if completed.returncode != 0:
            if completed.stderr:
                print(completed.stderr, end="", file=sys.stderr)
            return completed.returncode
        adopted.extend(package.name for package in parse_list_output(completed.stdout))

    adopted = sorted({package for package in adopted if package})
    if dry_run:
        print("would adopt:")
    else:
        add_managed_packages(adopted)
        print("adopted:")
    for package in adopted:
        print(f"- {package}")
    return 0


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
    search.add_argument("--raw", action="store_true", help="Show raw backend output")
    search.add_argument("--no-color", action="store_true", help="Disable colored output")

    info = sub.add_parser("info", help="Show package details from the active backend")
    info.add_argument("package", help="Package name")
    info.add_argument("--raw", action="store_true", help="Show raw backend output")
    info.add_argument("--no-color", action="store_true", help="Disable colored output")

    listing = sub.add_parser("list", help="List explicitly installed packages")
    listing.add_argument("--raw", action="store_true", help="Show raw backend output")
    listing.add_argument("--no-color", action="store_true", help="Disable colored output")
    listing.add_argument("--sort", choices=["name", "version", "managed", "none"], default="name", help="Sort list output")
    listing.add_argument("--group", choices=["type", "managed"], default="type", help="Group list output")
    listing.add_argument("--columns", type=int, default=3, help="Number of list columns")
    adopt = sub.add_parser("adopt", help="Mark existing packages as managed by archdown")
    adopt.add_argument("packages", nargs="*", help="Package names to adopt")
    adopt.add_argument("--from-current", action="store_true", help="Adopt every currently listed explicit package")
    adopt.add_argument("--dry-run", action="store_true", help="Preview what would be adopted without writing state")

    sub.add_parser("refresh", help="Refresh package databases only")
    sub.add_parser("upgrade", help="Upgrade the full system")
    sub.add_parser("update", help="Alias for upgrade; safer than Homebrew-style split semantics on Arch")
    sub.add_parser("doctor", help="Show detected backend tooling and command mapping")
    return parser


def select_backend(name: str) -> Backend:
    if name == "auto":
        return detect_backend()
    if not shutil.which(name):
        raise SystemExit(f"Requested backend '{name}' is not installed")
    return make_backend(name)


def print_doctor(backend: Backend) -> None:
    available = {name: bool(shutil.which(name)) for name in ("paru", "yay", "pacman")}
    print("archdown doctor")
    print(f"selected backend: {backend.name}")
    for name, present in available.items():
        print(f"- {name}: {'found' if present else 'missing'}")
    print("command mapping:")
    print(f"- install: {' '.join(backend.install)} <pkg...>")
    print(f"- uninstall: {' '.join(backend.uninstall)} <pkg...>")
    print(f"- search: {' '.join(backend.search)} <query...>")
    print(f"- info: {' '.join(backend.info)} <pkg>")
    print(f"- list: {' '.join(backend.list_installed)}")
    print(f"- refresh: {' '.join(backend.refresh)}")
    print(f"- upgrade/update: {' '.join(backend.upgrade)}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    backend = select_backend(args.backend)

    if args.command == "install":
        return run_install([*backend.install, *args.packages], args.packages, args.dry_run)
    if args.command == "uninstall":
        return run_uninstall([*backend.uninstall, *args.packages], args.packages, args.dry_run)
    if args.command == "search":
        return run_search([*backend.search, *args.query], dry_run=args.dry_run, raw=args.raw, color=False if args.no_color else None)
    if args.command == "info":
        return run_info([*backend.info, args.package], dry_run=args.dry_run, raw=args.raw, color=False if args.no_color else None)
    if args.command == "list":
        return run_list(
            backend.list_installed,
            dry_run=args.dry_run,
            raw=args.raw,
            color=False if args.no_color else None,
            sort=args.sort,
            group=args.group,
            columns=args.columns,
        )
    if args.command == "refresh":
        print("warning: refresh only syncs databases. On Arch, full upgrades are usually safer.", file=sys.stderr)
        return run(backend.refresh, args.dry_run)
    if args.command in {"upgrade", "update"}:
        return run(backend.upgrade, args.dry_run)
    if args.command == "doctor":
        print_doctor(backend)
        return 0
    if args.command == "adopt":
        return run_adopt(backend.list_installed, packages=args.packages, from_current=args.from_current, dry_run=args.dry_run)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
