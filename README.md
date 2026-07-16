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
- uses Homebrew-style split semantics: `update` fetches package metadata and `upgrade` installs available upgrades

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
- update
- upgrade
- backend auto-detection
- dry-run mode

Not implemented yet:
- install prompts/wrappers for missing helpers
- release automation

Specs

- Specs live under `openspec/`.
- archdown is being built as a parsed UX wrapper over Arch backends, not a thin passthrough of raw backend output.
- Current command specs include `openspec/specs/search-command.md`, `openspec/specs/list-command.md`, `openspec/specs/outdated-command.md`, `openspec/specs/cleanup-command.md`, `openspec/specs/which-command.md`, and `openspec/specs/uses-command.md`.

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
archdown --dry-run update
```

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

- `update` refreshes package databases without upgrading installed packages.
- `upgrade` performs the full-system upgrade.
- `refresh` remains an alias for `update`.
- Arch does not support partial upgrades: after refreshing metadata, prefer `archdown upgrade` before installing packages when updates are available.
- mutating commands (`install`, `uninstall`, `update`/`refresh`, `upgrade`, and `cleanup`) print a friendly completion line only after the backend exits successfully; failures and `--dry-run` previews never claim success.
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
