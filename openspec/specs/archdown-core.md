# archdown core

## Goal

archdown is a user-friendly CLI wrapper for Arch package workflows. It is not a new package manager.

## Product philosophy

- archdown must execute real backend commands rather than simulate package state.
- archdown should make common package tasks easier to read and use.
- backend choice is an implementation detail, not the user experience.

## Backend strategy

- Use an available Arch backend such as `yay`, `paru`, or `pacman`.
- Preserve real backend semantics for package operations.
- Use Homebrew-style split semantics: `update` refreshes package metadata without installing packages, while `upgrade` performs a full-system upgrade.
- Keep `refresh` as an alias for `update`.
- Document that Arch does not support partial upgrades and recommend upgrading before package installation after metadata is refreshed.

## Output philosophy

- Prefer parsing backend output into structured internal models where practical.
- Render user-facing output from those structured models.
- The default UX should favor compact, scan-friendly terminal layouts over raw backend output.
- Use aligned columns, grouping, and optional color where they materially improve readability.
- Raw backend passthrough is a fallback or escape hatch, not the default UX.

## Command semantics

- Commands should feel consistent and predictable across supported backends.
- User-visible wording should reflect archdown behavior, not leak backend quirks unless needed.
- `search` should optimize for quick scanning, while `info` should carry fuller package detail.
- `list` should render structured installed-package views and may update archdown-managed package metadata as part of that structured render.

## Empty and missing states

- When a command has nothing to show, it should print a clear one-line message rather than blank or placeholder output.
- `search` with no matches prints "No packages found."; `info` for a package the backend does not know prints "No package found." instead of an empty detail block.
- Friendly empty/missing output is a display concern only: backend exit codes are preserved so callers and scripts still see the real success/failure.

## Completion confirmations

- Mutating commands (`install`, `uninstall`, `update`/`refresh`, `upgrade`, and the removal `cleanup` performs) should end with a clear, friendly one-line confirmation so the user knows the operation finished.
- A confirmation is printed only after the backend exits successfully (exit code `0`) and only for a real run. archdown must never claim success on a non-zero backend exit, and must preserve the backend's own output and stderr on failure.
- `--dry-run` stays a preview: it prints the backend command it would run but must not print a completion confirmation, since nothing was executed.
- Package confirmations name what changed, e.g. "Installed ripgrep." for one package or "Installed 2 packages: ripgrep, fd." for several; `update`/`refresh` and `upgrade` confirm the overall operation ("Package metadata refreshed.", "System upgrade completed.").
- Read-only structured commands (`search`, `info`, `which`, `uses`, `list`, `outdated`) do not add completion confirmations, and `doctor` stays an explicit diagnostic explainer.

## Fallback behavior

- If structured parsing is unavailable or fails, archdown should degrade gracefully.
- Fallback behavior should preserve access to backend results without pretending parsing succeeded.
