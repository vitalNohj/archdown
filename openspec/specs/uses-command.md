# uses command

## Goal

Answer "what still depends on this?" for a package. This is the everyday
"why is this here / what needs it" verb you reach for before removing
something, in the spirit of `apt rdepends`, `brew uses`, or `pactree -r`. Given
a package name (for example `openssl`), report the packages that depend on it,
so a user can see what would break before removing it. It is read-only and safe
to run at any time.

## Inputs

- exactly one positional argument: a package name
- selected backend from normal archdown detection

`uses` is intentionally a single memorable verb with one sensible default. It
takes one package name and no command-specific flags: no filtering, sorting, or
format knobs. Global archdown options (such as `--backend` and `--dry-run`)
still apply because they belong to archdown itself, not to this command. Color
follows archdown's normal auto-detection (honoring `NO_COLOR` and non-tty
output); there is no per-command switch for it.

## Read-only guarantee

- `uses` must only query the reverse-dependency relationship. It must never
  install, remove, sync, or upgrade anything.
- The reverse-dependency lookup is a local pacman-level query (`pactree -r`, or
  parsing the `Required By` field of `pacman -Qi`, both of which resolve against
  the already-installed database). These queries are read-only and do not sync
  the database.

## Backend behavior

- Prefer `pactree -r <pkg>` (from `pacman-contrib`) when it is available: it
  gives the reverse-dependency listing directly.
- When `pactree` is not installed, fall back to the active backend's local
  package query (`pacman -Qi <pkg>`, or the `yay`/`paru` equivalent) and read
  the packages named in its `Required By` field.
- Degrade gracefully: whichever source is used, the result is the same
  structured "packages that depend on `<pkg>`" model.
- Preserve real backend semantics for what depends on the package. Do not invent
  dependents the backend did not report.

## Parsing behavior

- Prefer parsing backend output into a structured result: the queried package
  name plus the set of packages that depend on it.
- From `pactree` output, take the reverse-dependency package names, excluding the
  queried package itself (the tree root) and de-duplicating repeated names.
- From `pacman -Qi` output, read the whitespace-separated names in the
  `Required By` field; a value of `None` means nothing depends on the package.
- Treat the parsed result model as the source for rendering.

## Default output behavior

- Default output should be clearer and more compact than raw backend formatting.
- The default human view leads with a titled section naming the queried package,
  then lists the dependent packages, sorted, one per line, so the result is easy
  to scan.

## Default layout

The preferred default layout titles the section with the queried package and
lists what depends on it beneath it:

```text
Packages that depend on openssl
-------------------------------
curl
git
wget
```

## Large-tree behavior

- Reverse-dependency trees can be enormous for core packages (for example
  `glibc`), where a naive dump would print thousands of lines.
- `uses` must cap the listing to a sensible number of entries and, when it caps,
  print a clear summary line reporting how many more were omitted and the true
  total, so the output stays friendly and never floods the terminal:

```text
Packages that depend on glibc
-----------------------------
acl
attr
… and 1483 more (1516 total)
```

- The cap affects only how many names are shown, never the reported total.

## Nothing-depends-on behavior

- When nothing depends on the package, print a clear, friendly single line rather
  than empty output. This is a normal, successful outcome and exits `0`.

```text
Nothing depends on openssl.
```

## Color behavior

- Multi-color terminal output is desirable when the terminal supports it.
- Color should improve scanning, not become decoration.
- Color must not be the only way information is conveyed; the package names and
  the omitted-count summary must remain meaningful without color.
- Color follows the same auto-detection archdown uses elsewhere (honoring
  `NO_COLOR` and non-tty output).

## Failure behavior

`uses` must distinguish a genuine backend failure from a legitimate "nothing
depends on it" result, and must never report the former as the latter.

- An empty dependent set from a successful query is the friendly
  "Nothing depends on `<pkg>`." result, exit `0`.
- A genuine backend failure (the package is not installed, a database lock, a
  permission error, or any non-zero backend exit) must be reported honestly:
  print a clear message on stderr, preserve any backend output, and exit with the
  backend's non-zero return code. Such a failure must never be swallowed as
  "Nothing depends on it."

## Future extension points

- machine-readable output modes (for example `--json`)
- an explicit `--raw` escape hatch
- limiting to direct dependents versus the full recursive tree
