# outdated command

## Goal

Show which installed packages have a newer version available, without changing
anything. This is the everyday "what could I upgrade?" verb, in the spirit of
`brew outdated` or `apt list --upgradable`. It is read-only and safe to run at
any time.

## Inputs

- no positional arguments
- no command-specific flags
- selected backend from normal archdown detection

`outdated` is intentionally a single memorable verb with one sensible default.
It does not accept filtering, sorting, or format flags. Global archdown options
(such as `--backend` and `--dry-run`) still apply because they belong to
archdown itself, not to this command.

## Read-only guarantee

- `outdated` must only query update availability. It must never install,
  remove, or upgrade a package.
- `outdated` must never sync the package database. In particular it must not run
  a `-Sy` style refresh, because a lone database sync followed by later partial
  installs is the partial-upgrade footgun archdown warns about elsewhere.
- Update availability is computed against the already-synced database, using a
  safe non-syncing check (such as `checkupdates` from `pacman-contrib`, or the
  backend's own query-upgrades mode). The user's real database is left untouched.

## Backend behavior

- Run the appropriate backend query for available upgrades.
- Prefer a check that does not touch the real database when one is available.
- Preserve real backend semantics for which packages are considered upgradable,
  including AUR packages when the active backend tracks them.
- Do not invent upgrades the backend did not report.

## Parsing behavior

- Prefer parsing backend output into structured results.
- Each result carries the package name, the currently installed version, and the
  new available version.
- Treat the parsed result model as the source for rendering.

## Default output behavior

- Default output should be clearer and more compact than raw backend formatting.
- The default human view should use aligned columns so results are easy to scan.
- Each row should show the package identity together with the version change from
  the installed version to the available version.
- Output should be optimized for terminal readability first.

## Default layout

The preferred default layout groups outdated packages under a single section and
shows the version transition per package:

```text
Outdated packages
-----------------
ripgrep   14.1.1-1 -> 14.2.0-1
fd        10.2.0-1 -> 10.3.0-1
```

## Nothing-outdated behavior

- When no packages are outdated, print a clear, friendly single line rather than
  empty output.

```text
Everything is up to date.
```

- The nothing-outdated result is a normal, successful outcome. archdown should
  not surface the backend's "no updates" exit-code quirk as a failure. The
  friendly line is printed and the command exits `0`.
- "Nothing outdated" must be inferred only from a genuine no-updates signal: for
  `checkupdates` that is exit code `2`; for a `-Qu` query that is empty output
  with the backend's known no-updates exit and no error diagnostics. Any other
  outcome is treated as a failure, not as up-to-date.

## Color behavior

- Multi-color terminal output is desirable when the terminal supports it.
- Color should improve scanning, not become decoration.
- Color must not be the only way information is conveyed; the version transition
  text must remain meaningful without color.
- Color follows the same auto-detection archdown uses elsewhere (honoring
  `NO_COLOR` and non-tty output).

## Failure and fallback behavior

- If parsing fails, degrade gracefully instead of crashing.
- If the backend prints output that cannot be parsed into structured results,
  archdown should preserve access to that raw output rather than pretend the
  structured renderer succeeded or claim everything is up to date.
- A genuine backend failure (database lock, network failure, `checkupdates`
  temp-db copy failure, permission error, or any unexpected exit code) must be
  reported honestly: print a clear message on stderr, preserve any backend
  output, and exit with the backend's non-zero return code. Such a failure must
  never be swallowed as "Everything is up to date."

## Future extension points

- machine-readable output modes
- explicit `--raw` and `--json` options
