# cleanup command

## Goal

Remove packages that were installed as dependencies but that nothing needs
anymore. This is the everyday "tidy up leftovers" verb, in the spirit of `brew
autoremove` or `apt autoremove`. It hides the classic cryptic Arch incantation
(`pacman -Qtdq | sudo pacman -Rns -`) behind one memorable word.

## Inputs

- no positional arguments
- no command-specific flags
- selected backend from normal archdown detection

`cleanup` is intentionally a single memorable verb with one sensible default. It
does not accept filtering, selection, or format flags. Global archdown options
(such as `--backend` and `--dry-run`) still apply because they belong to
archdown itself, not to this command.

## Backend behavior

- Determine orphans with the backend's query for packages that were installed as
  dependencies and are no longer required (`pacman -Qtdq`, or the `yay`/`paru`
  equivalent). This query is read-only and safe to run at any time.
- Remove the orphans with the same removal path archdown's `uninstall` uses
  (`-Rns`), so dependencies pulled in solely for them are cleaned up too.
- Preserve real backend semantics for which packages count as orphans. Do not
  invent removals the backend did not report.

## Show-then-remove behavior

- `cleanup` must FIRST show the user exactly which packages it is about to
  remove, listing them by name, before removing anything.
- After showing the list, `cleanup` performs the removal by shelling out to the
  backend's removal command. The removal runs interactively so the user sees the
  backend command and gets the backend's own confirmation prompt before any
  package is actually removed.
- Packages removed this way are dropped from archdown's managed-package state,
  the same as an ordinary `uninstall`.
- After a successful removal, `cleanup` prints the same friendly confirmation an
  ordinary `uninstall` does (for example "Removed ripgrep."), so the user knows
  the orphans were actually cleaned up.

## Dry-run behavior

- Under `--dry-run`, `cleanup` still runs the read-only orphan query so it can
  show the user exactly what would be removed.
- Under `--dry-run`, `cleanup` must print the removal command it would run but
  must not remove any package and must not modify managed-package state.

## Nothing-to-clean behavior

- When there are no orphaned packages, print a clear, friendly single line rather
  than empty output, and exit `0`.

```text
Nothing to clean up.
```

- The nothing-to-clean result is a normal, successful outcome. archdown should
  not surface the backend's "no orphans" exit-code quirk (an empty query exiting
  non-zero) as a failure.

## Failure behavior

- A genuine failure of the orphan query (database lock, permission error, or any
  unexpected diagnostic output) must be reported honestly: print a clear message
  on stderr, preserve the backend's output, and exit non-zero. Such a failure
  must never be swallowed as "Nothing to clean up."
