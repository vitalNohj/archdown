from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence

from archdown.info import parse_info_output, render_package_info
from archdown.listing import parse_list_output, parse_outdated_output, render_installed_packages, render_outdated_packages
from archdown.search import parse_search_output, render_search_results
from archdown.state import add_managed_packages, load_managed_packages, remove_managed_packages, update_managed_package_versions
from archdown.uses import parse_pactree_dependents, parse_required_by, render_dependents
from archdown.which import parse_owner_output, render_owner


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
    outdated: list[str]
    orphans: list[str]
    owns: list[str]
    local_info: list[str]


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
            ["paru", "-Qu"],
            ["paru", "-Qtdq"],
            ["paru", "-Qo"],
            ["paru", "-Qi"],
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
            ["yay", "-Qu"],
            ["yay", "-Qtdq"],
            ["yay", "-Qo"],
            ["yay", "-Qi"],
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
            ["pacman", "-Qu"],
            ["pacman", "-Qtdq"],
            ["pacman", "-Qo"],
            ["pacman", "-Qi"],
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


def print_success(message: str, *, dry_run: bool, code: int) -> None:
    if code == 0 and not dry_run:
        print(message)


def format_package_confirmation(verb: str, packages: Sequence[str]) -> str:
    if len(packages) == 1:
        return f"{verb} {packages[0]}."
    return f"{verb} {len(packages)} packages: {', '.join(packages)}."


def run_confirmed(cmd: Sequence[str], dry_run: bool, success_message: str) -> int:
    code = run(cmd, dry_run)
    print_success(success_message, dry_run=dry_run, code=code)
    return code


def run_install(cmd: Sequence[str], packages: Sequence[str], dry_run: bool) -> int:
    code = run(cmd, dry_run)
    if code == 0 and not dry_run:
        add_managed_packages(packages)
        print(format_package_confirmation("Installed", packages))
    return code


def run_uninstall(cmd: Sequence[str], packages: Sequence[str], dry_run: bool) -> int:
    code = run(cmd, dry_run)
    if code == 0 and not dry_run:
        remove_managed_packages(packages)
        print(format_package_confirmation("Removed", packages))
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
    elif output.strip():
        # Backend produced output we could not parse: fall back to raw rather
        # than claim the structured renderer found nothing.
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
    else:
        # No matches: route the empty result through the renderer so the user
        # gets a clear "No packages found." line instead of blank output.
        print(render_search_results(results, color=color))
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
    recent_updates = update_managed_package_versions({package.name: package.version for package in packages}, managed)
    print(
        render_installed_packages(
            packages,
            color=color,
            columns=columns,
            managed=managed,
            recent_updates=recent_updates,
            group_managed=group == "managed",
            sort=sort,
        )
    )
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def resolve_outdated_command(backend: Backend) -> list[str]:
    # `checkupdates` (from pacman-contrib) is the safe repo update check for the
    # plain pacman backend: it works against a private database copy and never
    # touches the user's real db. paru/yay keep their own `-Qu` query because it
    # also reports AUR upgrades against the already-synced db.
    if backend.name == "pacman" and shutil.which("checkupdates"):
        return ["checkupdates"]
    return list(backend.outdated)


def _surface_outdated_failure(completed: subprocess.CompletedProcess[str]) -> int:
    print("archdown: could not check for outdated packages", file=sys.stderr)
    if completed.stdout.strip():
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


UPGRADE_HINT = "Run `archdown upgrade` to upgrade them."


def _print_upgrade_hint(enabled: bool) -> None:
    # The hint accompanies an actual list of upgradable packages; an up-to-date
    # system has nothing to point `archdown upgrade` at.
    if enabled:
        print(f"\n{UPGRADE_HINT}")


def run_outdated(cmd: Sequence[str], *, dry_run: bool, color: bool | None = None, upgrade_hint: bool = False) -> int:
    pretty = " ".join(cmd)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(list(cmd), capture_output=True, text=True)
    output = completed.stdout

    if cmd[0] == "checkupdates":
        # checkupdates exit codes: 0 => updates available, 2 => nothing to
        # upgrade, anything else => a real failure.
        if completed.returncode == 2:
            print(render_outdated_packages([], color=color))
            return 0
        if completed.returncode != 0:
            return _surface_outdated_failure(completed)
        packages = parse_outdated_output(output)
        if packages:
            print(render_outdated_packages(packages, color=color))
            _print_upgrade_hint(upgrade_hint)
        elif output.strip():
            print(output, end="")
            _print_upgrade_hint(upgrade_hint)
        else:
            print(render_outdated_packages([], color=color))
        return 0

    packages = parse_outdated_output(output)
    if packages:
        print(render_outdated_packages(packages, color=color))
        _print_upgrade_hint(upgrade_hint)
        return 0
    if output.strip():
        return _surface_outdated_failure(completed)
    if completed.returncode in (0, 1) and not completed.stderr:
        print(render_outdated_packages([], color=color))
        return 0
    return _surface_outdated_failure(completed)


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
    if info.is_empty:
        # A missing package yields empty backend output, which parses to an empty
        # PackageInfo; show a clear line instead of an empty "Package information" block.
        print("No package found.")
    else:
        print(render_package_info(info, color=color))
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode


def run_which(cmd: Sequence[str], arg: str, *, dry_run: bool, raw: bool, color: bool | None) -> int:
    # Resolve the argument to a path first: an existing path is used as-is,
    # otherwise treat it as a command name and look it up on PATH like a shell
    # would. This is what lets a user type the short name they actually invoke.
    if os.path.exists(arg):
        target = arg
    else:
        resolved = shutil.which(arg)
        if resolved is None:
            print(f"'{arg}' not found on PATH.", file=sys.stderr)
            return 1
        target = resolved

    full = [*cmd, target]
    pretty = " ".join(full)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(full, capture_output=True, text=True)
    output = completed.stdout
    if raw:
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode

    # `pacman -Qo` exits non-zero with an "error: No package owns ..." diagnostic
    # when nothing owns the path. Surface that as one friendly line, never a blank
    # line or a raw traceback.
    if completed.returncode != 0 or not output.strip():
        print(f"No package owns '{arg}'.", file=sys.stderr)
        return completed.returncode or 1

    owner = parse_owner_output(output)
    if owner is None:
        # Owner reported but unparseable: preserve the raw backend output rather
        # than pretend the structured render succeeded.
        print(output, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        return completed.returncode
    print(render_owner(owner, color=color))
    return 0


def resolve_uses_command(backend: Backend) -> tuple[list[str], str]:
    # `pactree -r` (from pacman-contrib) reports reverse dependencies directly.
    # `-l` prints them one per line, which parses cleanly regardless of backend.
    # Without pactree, fall back to reading the `Required By` field of the
    # backend's local `-Qi` query, which resolves against the same local db.
    if shutil.which("pactree"):
        return (["pactree", "-r", "-l"], "pactree")
    return (list(backend.local_info), "qi")


def _surface_uses_failure(completed: subprocess.CompletedProcess[str], package: str) -> int:
    print(f"archdown: could not determine what depends on {package}", file=sys.stderr)
    if completed.stdout.strip():
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return completed.returncode or 1


def run_uses(cmd: Sequence[str], package: str, source: str, *, dry_run: bool) -> int:
    full = [*cmd, package]
    pretty = " ".join(full)
    if dry_run:
        print(f"backend command: {pretty}")
        return 0

    completed = subprocess.run(full, capture_output=True, text=True)

    # A non-zero exit means the query itself failed (package not installed, db
    # lock, ...). That is a genuine error, never a "nothing depends on it"
    # result, so surface it honestly rather than swallow it.
    if completed.returncode != 0:
        return _surface_uses_failure(completed, package)

    if source == "pactree":
        dependents = parse_pactree_dependents(completed.stdout, package)
    else:
        dependents = parse_required_by(completed.stdout)

    print(render_dependents(package, dependents, color=None))
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return 0


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


def run_cleanup(query_cmd: Sequence[str], uninstall_cmd: Sequence[str], *, dry_run: bool) -> int:
    # The orphan query (`-Qtdq`) is read-only, so it runs even under --dry-run to
    # show the user exactly what would be removed.
    completed = subprocess.run(list(query_cmd), capture_output=True, text=True)
    orphans = [line.strip() for line in completed.stdout.splitlines() if line.strip()]

    if not orphans:
        if completed.stderr.strip():
            print("archdown: could not check for orphaned packages", file=sys.stderr)
            print(completed.stderr, end="", file=sys.stderr)
            return completed.returncode or 1
        # `-Qtdq` exits non-zero with empty output when there is nothing to clean.
        print("Nothing to clean up.")
        return 0

    print("Orphaned packages to remove:")
    for name in orphans:
        print(f"- {name}")
    return run_uninstall([*uninstall_cmd, *orphans], orphans, dry_run)


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

    which = sub.add_parser("which", help="Show which package owns a command or file (read-only)")
    which.add_argument("target", help="Command name or path")
    which.add_argument("--raw", action="store_true", help="Show raw backend output")
    which.add_argument("--no-color", action="store_true", help="Disable colored output")

    uses = sub.add_parser("uses", help="Show what still depends on a package (read-only)")
    uses.add_argument("package", help="Package name")

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

    sub.add_parser("outdated", help="List packages with an available upgrade (read-only; does not sync or upgrade)")
    sub.add_parser("cleanup", help="Remove orphaned dependency packages nothing needs anymore")
    sub.add_parser("refresh", help="Refresh package databases only")
    sub.add_parser("upgrade", help="Upgrade the full system (the only verb that installs upgrades)")
    update = sub.add_parser("update", help="Safely check for available updates and report them (read-only; use `upgrade` to install)")
    update.add_argument("--no-color", action="store_true", help="Disable colored output")
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
    print(f"- which: {' '.join(backend.owns)} <path>")
    print(f"- uses: {' '.join(resolve_uses_command(backend)[0])} <pkg>")
    print(f"- list: {' '.join(backend.list_installed)}")
    print(f"- outdated: {' '.join(resolve_outdated_command(backend))}")
    print(f"- cleanup: {' '.join(backend.orphans)} | {' '.join(backend.uninstall)} -")
    print(f"- refresh: {' '.join(backend.refresh)}")
    print(f"- update: {' '.join(resolve_outdated_command(backend))} (read-only check; use upgrade to install)")
    print(f"- upgrade: {' '.join(backend.upgrade)}")


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
    if args.command == "which":
        return run_which(backend.owns, args.target, dry_run=args.dry_run, raw=args.raw, color=False if args.no_color else None)
    if args.command == "uses":
        cmd, source = resolve_uses_command(backend)
        return run_uses(cmd, args.package, source, dry_run=args.dry_run)
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
    if args.command == "outdated":
        return run_outdated(resolve_outdated_command(backend), dry_run=args.dry_run)
    if args.command == "update":
        # Homebrew-style update: refresh update knowledge via the safe outdated
        # check (never a live -Sy sync, never an upgrade) and report the result.
        return run_outdated(
            resolve_outdated_command(backend),
            dry_run=args.dry_run,
            color=False if args.no_color else None,
            upgrade_hint=True,
        )
    if args.command == "cleanup":
        return run_cleanup(backend.orphans, backend.uninstall, dry_run=args.dry_run)
    if args.command == "refresh":
        print("warning: refresh only syncs databases. On Arch, full upgrades are usually safer.", file=sys.stderr)
        return run_confirmed(backend.refresh, args.dry_run, "Package databases refreshed.")
    if args.command == "upgrade":
        return run_confirmed(backend.upgrade, args.dry_run, "System update completed.")
    if args.command == "doctor":
        print_doctor(backend)
        return 0
    if args.command == "adopt":
        return run_adopt(backend.list_installed, packages=args.packages, from_current=args.from_current, dry_run=args.dry_run)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
