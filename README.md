# archdown

archdown is a thin, friendly CLI wrapper around Arch Linux package tooling.

Goal: make pacman/AUR workflows feel more like Homebrew without inventing a new package ecosystem.

Examples:

```bash
archdown install neovim
archdown uninstall neovim
archdown search terminal emulator
archdown list
archdown update
archdown upgrade
archdown refresh
```

How it works

- prefers `paru` if installed
- falls back to `yay`
- falls back to `pacman`
- uses AUR-capable backends when available
- keeps `update` as an alias of full-system `upgrade` because Arch partial-upgrade semantics are risky

Status

This is an MVP scaffold.

Implemented now:
- install
- uninstall
- search
- list
- refresh
- update
- upgrade
- backend auto-detection
- dry-run mode

Not implemented yet:
- nicer output formatting
- package info/details
- explicit repo vs AUR display
- install prompts/wrappers for missing helpers
- tests
- release automation

Install locally for development

```bash
cd archdown
python -m pip install -e .
```

Try commands safely

```bash
archdown --dry-run install ripgrep
archdown --dry-run search browser
archdown --dry-run update
```

Design notes

- `update` and `upgrade` intentionally do the same thing.
- `refresh` exists for people who explicitly want metadata sync only.
- uninstall currently maps to `-Rns`, which is opinionated and may become configurable.

Roadmap ideas

1. better UX and help text
2. `archdown info <pkg>`
3. `archdown doctor` to explain available backend tooling
4. JSON output mode
5. shell completions
6. test suite
7. packaging for AUR/PyPI

Name availability research

`archdown` is not available as a clean GitHub namespace under `vitalNohj/archdown`, but the name already appears in a few unrelated public repos. It also appears free in the Arch package search, AUR search, PyPI, npm, and crates.io at the time this repo was created. So the name is usable, but not globally unique enough to assume zero collisions.
