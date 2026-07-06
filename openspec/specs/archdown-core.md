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
- Keep `update` and `upgrade` as aliases because partial-upgrade workflows are risky on Arch.

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

## Fallback behavior

- If structured parsing is unavailable or fails, archdown should degrade gracefully.
- Fallback behavior should preserve access to backend results without pretending parsing succeeded.
