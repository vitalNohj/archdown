# archdown

archdown is a friendly CLI wrapper around Arch Linux package tooling.

Goal: make pacman/AUR workflows feel more like Homebrew without inventing a new package ecosystem.

Why this exists

Arch users often bounce between Debian-based distros, macOS systems with Homebrew, and Arch. archdown aims to make Arch feel just as approachable day-to-day without giving up the power of `pacman`, `yay`, and the AUR.

archdown is meant to be that missing comfort layer: familiar verbs like `install`, `uninstall`, `search`, and `update`, backed by the real Arch ecosystem instead of a separate repository or package manager.

Examples:

```bash
archdown install neovim
archdown uninstall neovim
archdown search terminal emulator
archdown info neovim
archdown which rg
archdown uses openssl
archdown doctor
archdown list
archdown list --group managed
archdown adopt herdr
archdown outdated
archdown cleanup
archdown update
archdown upgrade
```

How it works

- prefers `paru` if installed
- falls back to `yay`
- falls back to `pacman`
- uses AUR-capable backends when available
- `update` is a safe, read-only Homebrew-style check: it refreshes update knowledge via `checkupdates`' temporary database copy (or the AUR helper's query mode) and reports what could be upgraded, without touching the live sync databases
- `upgrade` is the only verb that actually installs upgrades, and it always does a full `-Syu`, because partial upgrades are risky on Arch

Status

This is an MVP scaffold.

Implemented now:
- install
- uninstall
- search
- info
- which (read-only lookup of which package owns a command or file)
- uses (read-only lookup of what still depends on a package)
- doctor
- list with structured Libraries / Applications / User installed sections
- adopt existing packages into archdown's managed package state
- recently-updated markers for tracked packages after external upgrades
- outdated (read-only structured list of packages with an available upgrade; never syncs or upgrades)
- cleanup (remove orphaned dependency packages nothing needs anymore)
- refresh
- update (read-only refresh-and-report of available updates, with a hint to run `upgrade`)
- upgrade (full system upgrade)
- backend auto-detection
- dry-run mode

Not implemented yet:
- install prompts/wrappers for missing helpers
- release automation

Specs

- Specs live under `openspec/`.
- archdown is being built as a parsed UX wrapper over Arch backends, not a thin passthrough of raw backend output.
- Current command specs include `openspec/specs/search-command.md`, `openspec/specs/list-command.md`, `openspec/specs/outdated-command.md`, `openspec/specs/update-command.md`, `openspec/specs/cleanup-command.md`, `openspec/specs/which-command.md`, and `openspec/specs/uses-command.md`.

Install locally for development

```bash
cd archdown
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

Try commands safely

```bash
archdown --dry-run install ripgrep
archdown --dry-run search browser
archdown --dry-run info ripgrep
archdown which rg
archdown uses openssl
archdown doctor
archdown outdated
archdown --dry-run cleanup
archdown update
```

`archdown update` is always safe to run: it never installs, upgrades, or syncs
the live package databases. With updates available it prints a colored report
and a hint:

```text
Outdated packages
-----------------
ripgrep   14.1.1-1 -> 14.2.0-1
fd        10.2.0-1 -> 10.3.0-1

Run `archdown upgrade` to upgrade them.
```

On a current system it prints `Everything is up to date.`

Color follows archdown's usual auto-detection (honoring `NO_COLOR` and non-tty
output); `archdown update --no-color` forces plain output.

Managed packages and recent updates

- `archdown install <pkg>` records the package as managed by archdown after a successful install.
- `archdown adopt <pkg>` marks an already-installed package as managed by archdown.
- `archdown list` stores the last seen installed version for managed packages.
- If a managed package changes version outside archdown, the next structured `archdown list` marks it inline:

```text
herdr (Recently Updated 0.7.0-1 -> 0.7.1-1)
v 0.7.1-1
```

- `archdown list --raw` stays a backend passthrough and does not update archdown's managed version state.

Run tests

```bash
.venv/bin/pytest -q
```

Design notes

- `update` follows the Homebrew mental model: it only refreshes update knowledge and reports, while `upgrade` is what changes the system. The report is shared with `outdated`; `update` adds the closing `archdown upgrade` hint.
- `update` refreshes safely: `checkupdates` works against a temporary database copy, and AUR helpers are queried in `-Qu` mode, so the real sync databases are never touched and no partial-upgrade window is opened.
- `refresh` exists for people who explicitly want a live metadata sync only, and warns about the partial-upgrade risk.
- mutating commands (`install`, `uninstall`, `refresh`, `upgrade`, and `cleanup`) print a friendly completion line only after the backend exits successfully; failures and `--dry-run` previews never claim success.
- uninstall currently maps to `-Rns`, which is opinionated and may become configurable.
- `doctor` is a human-readable backend explainer, not a machine interface.
- default UX should move toward structured parsing and rendering over backend output.
- `list` separates package browsing into Homebrew-inspired sections: Libraries, Applications, and User installed.
- `User installed` means packages tracked by archdown, either installed through `archdown install` or adopted with `archdown adopt`.
- Structured `list` uses tracked packages to surface version changes caused by external tools like `yay` or `pacman`.

Roadmap ideas

1. better UX and help text
2. richer `archdown info <pkg>` output
3. JSON output mode
4. shell completions
5. test suite expansion
6. packaging for AUR/PyPI

Name availability research

`archdown` already appears in a few unrelated public repositories. It also appeared free in the Arch package search, AUR search, PyPI, npm, and crates.io at the time this repo was created. So the name is usable, but not globally unique enough to assume zero collisions.
