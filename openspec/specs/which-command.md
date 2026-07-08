# which command

## Goal

Answer "which package owns this?" for a command or a file. This is the everyday
"where did this come from?" verb, in the spirit of `brew which`, `dpkg -S`, or
`rpm -qf`. Given a bare command name (for example `rg`) or a path (for example
`/usr/bin/rg`), report the package that owns it. It is read-only and safe to run
at any time.

## Inputs

- exactly one positional argument: a command name or a path
- selected backend from normal archdown detection

`which` is intentionally a single memorable verb with one sensible default. It
does not accept filtering or selection flags. It accepts only the same
output-shaping flags archdown's other rendered commands use (`--raw` and
`--no-color`), because those belong to archdown's rendering conventions, not to
this command's semantics. Global archdown options (such as `--backend` and
`--dry-run`) still apply because they belong to archdown itself.

## Resolution behavior

- If the argument is already an existing path, use it as-is.
- Otherwise, resolve the argument to an executable path by looking it up on
  `PATH` (as a shell would). The resolved path is what gets handed to the owner
  query.
- Resolving a command name to its path first is what lets a user type the short
  name they actually invoke (`rg`) instead of remembering the install location.

## Read-only guarantee

- `which` must only query package ownership. It must never install, remove,
  sync, or upgrade anything.
- The owner lookup is a pacman-level query (`pacman -Qo <path>`, or the
  `yay`/`paru` equivalent, all of which resolve to the same pacman database).
  This query is read-only and does not touch or sync the database.

## Backend behavior

- Run the backend's package-ownership query against the resolved path.
- Preserve real backend semantics for ownership. Do not invent an owner the
  backend did not report.

## Parsing behavior

- Prefer parsing backend output into a structured result.
- The parsed result carries the owned path, the owning package name, and the
  package version.
- Treat the parsed result model as the source for rendering.

## Default output behavior

- Default output should be clearer and more compact than raw backend formatting.
- The default human view leads with the owning package's identity (name and
  version) and shows the resolved path it owns.
- Output should be optimized for terminal readability first, consistent with the
  compact renderers used by `search`, `info`, and `list`.

## Default layout

The preferred default layout leads with the package identity and shows the
resolved path beneath it:

```text
ripgrep  15.1.0-4
path: /usr/bin/rg
```

## Color behavior

- Multi-color terminal output is desirable when the terminal supports it.
- Color should improve scanning, not become decoration.
- Color must not be the only way information is conveyed; the package name,
  version, and path must remain meaningful without color.
- Color follows the same auto-detection archdown uses elsewhere (honoring
  `NO_COLOR` and non-tty output) and can be disabled with `--no-color`.

## Friendly failure behavior

`which` cares about failure states and must never emit a blank line or a raw
traceback.

- If the argument is not an existing path and cannot be resolved on `PATH`,
  print a clear single line and exit non-zero:

```text
'rg' not found on PATH.
```

- If the resolved path exists but no package owns it, print a clear single line
  and exit non-zero:

```text
No package owns 'rg'.
```

- The failure message echoes the argument the user actually typed, not just the
  resolved path, so the message stays legible.

## Fallback behavior

- Under `--raw`, print the backend's own output (and any diagnostics) rather than
  the structured render, as an escape hatch consistent with other commands.
- If the backend reports an owner but the output cannot be parsed into a
  structured result, preserve access to the raw backend output rather than
  pretend the structured renderer succeeded.

## Future extension points

- machine-readable output modes (for example `--json`)
- reporting all matches when a name resolves to multiple owned paths
