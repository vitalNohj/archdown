# archdown

archdown is a friendly CLI wrapper around Arch Linux package tooling.

Goal: make pacman/AUR workflows feel more like Homebrew without inventing a new package ecosystem.

Examples:

```bash
archdown install neovim
archdown uninstall neovim
archdown search terminal emulator
archdown info neovim
archdown doctor
archdown list
archdown update
archdown upgrade
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
- info
- doctor
- list
- refresh
- update
- upgrade
- backend auto-detection
- dry-run mode

Not implemented yet:
- parsed search rendering
- explicit repo vs AUR display
- install prompts/wrappers for missing helpers
- release automation

Specs

- Specs live under `openspec/`.
- archdown is being built as a parsed UX wrapper over Arch backends, not a thin passthrough of raw backend output.
- The first detailed command target is `openspec/specs/search-command.md`.

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
archdown doctor
archdown --dry-run update
```

Run tests

```bash
.venv/bin/pytest -q
```

Design notes

- `update` and `upgrade` intentionally do the same thing.
- `refresh` exists for people who explicitly want metadata sync only.
- uninstall currently maps to `-Rns`, which is opinionated and may become configurable.
- `doctor` is a human-readable backend explainer, not a machine interface.
- default UX should move toward structured parsing and rendering over backend output.

Roadmap ideas

1. better UX and help text
2. richer `archdown info <pkg>` output
3. JSON output mode
4. shell completions
5. test suite expansion
6. packaging for AUR/PyPI

Name availability research

`archdown` already appears in a few unrelated public repositories. It also appeared free in the Arch package search, AUR search, PyPI, npm, and crates.io at the time this repo was created. So the name is usable, but not globally unique enough to assume zero collisions.
