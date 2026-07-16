# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Spec-first project: update or add the relevant spec under `openspec/specs/` before or alongside behavior changes, and keep code and specs agreeing. Workflow and spec index: `openspec/README.md`; contribution rules: `CONTRIBUTING.md`.
- Dev loop: `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`, then `.venv/bin/pytest -q`. Tests never touch real package managers — they monkeypatch `subprocess.run` and `shutil.which` (see `tests/test_cli.py`).
- Release version source: `src/archdown/_version.py`. Follow the checklist in `CONTRIBUTING.md`; pushing a matching `vX.Y.Z` tag publishes GitHub release artifacts.
- Safety invariant: only `upgrade` (and `install`/`uninstall`/`cleanup`/`refresh`) may mutate the system. `update`, `outdated`, `which`, `uses`, `list`, `search`, `info` are read-only and must never run a bare `-Sy` sync against the live databases (Arch partial-upgrade footgun; see `openspec/specs/update-command.md` and `outdated-command.md`).
- Add durable project-specific notes here as they are discovered through real work.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
