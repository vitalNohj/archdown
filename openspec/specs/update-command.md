# update command

## Goal

Give `archdown update` Homebrew-like semantics: refresh update knowledge safely
and report what could be upgraded, without upgrading anything. `update` is the
"do a pull, then tell me what's new" verb; `upgrade` remains the only verb that
actually changes installed packages.

## Inputs

- no positional arguments
- `--no-color` to disable colored output
- selected backend from normal archdown detection

Global archdown options (such as `--backend` and `--dry-run`) still apply.

## Read-only guarantee

- `update` must never install, remove, or upgrade a package.
- `update` must never run the backend's upgrade command (`-Syu` style) or any
  interactive prompt-driven command.
- `update` must never sync the user's real package databases. In particular it
  must not run a bare `-Sy` style refresh, because a lone database sync followed
  by later partial installs is the partial-upgrade footgun archdown warns about
  elsewhere. Users who explicitly want a live metadata sync keep the separate
  `refresh` verb, which carries its own warning.
- Update availability is refreshed and computed the same safe way as `outdated`:
  prefer `checkupdates` (from `pacman-contrib`) on the pacman backend, because
  it syncs against a private temporary database copy and leaves the real
  databases untouched; on AUR helpers use the helper's own query-upgrades mode
  (`-Qu`), which also reports AUR upgrades.

## Relationship with `outdated`

- `update` and `outdated` present the same report of available upgrades, backed
  by the same safe backend resolution. Neither verb is removed or broken.
- `outdated` stays the plain, flagless report verb (see
  `outdated-command.md`): just the facts, no follow-up suggestion.
- `update` is the Homebrew-flow verb: the same report, plus a closing hint that
  `archdown upgrade` performs the actual upgrade when updates are available.

## Default output behavior

- Reuse the structured outdated rendering: an "Outdated packages" section with
  aligned columns, each row showing the package name and the version transition
  from installed to available.
- When at least one update is available, end with a gentle hint on its own line:

```text
Outdated packages
-----------------
ripgrep   14.1.1-1 -> 14.2.0-1
fd        10.2.0-1 -> 10.3.0-1

Run `archdown upgrade` to upgrade them.
```

- When everything is current, print the friendly single line and exit `0`,
  with no upgrade hint (there is nothing to upgrade):

```text
Everything is up to date.
```

## Color behavior

- The report is colored when the terminal supports it, following archdown's
  usual auto-detection (honoring `NO_COLOR` and non-tty output).
- `--no-color` forces plain output.
- Color must not be the only way information is conveyed; the version
  transition text must remain meaningful without color.

## Failure and fallback behavior

- Same as `outdated`: genuine backend failures are reported honestly on stderr
  with the backend's exit code, unparseable output is preserved raw rather than
  hidden, and a failure is never presented as "Everything is up to date."

## Documentation behavior

- `doctor` lists `update` and `upgrade` as separate mappings: `update` maps to
  the safe read-only check, `upgrade` maps to the backend's full upgrade.
- Help text must not describe `update` as an alias for `upgrade`.
