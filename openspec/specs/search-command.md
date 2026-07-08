# search command

## Goal

Provide a cleaner, more structured search experience than raw backend output while still using the real Arch package backends underneath.

## Inputs

- search query text
- selected backend from normal archdown detection
- future flags such as `--raw`, `--json`, and view toggles

## Backend behavior

- Run the appropriate backend search command.
- Preserve backend search scope and package availability semantics.
- Do not invent package results that the backend did not return.

## Parsing behavior

- Prefer parsing backend search output into structured results.
- Separate package name, version, source, installed state, and description cleanly.
- Detect and expose installed state when the backend output provides it.
- Treat the parsed result model as the source for rendering.

## Default output behavior

- Default output should be clearer and more compact than raw backend formatting.
- The default human view should use multiple aligned columns so results are easy to scan.
- The primary row should prioritize package identity over description.
- The description may appear on a second indented line in the default view when space allows.
- Results should clearly distinguish package source such as `core`, `extra`, `community`, or AUR.
- Installed packages should be visibly marked inline.
- Output should be optimized for terminal readability first.

## Default layout

The preferred default search layout is:

- one primary row per result
- aligned columns for:
  - source
  - package name
  - version
  - installed marker
- optional second line for the description
- visually distinct grouping for official repositories versus AUR when both are present

Example direction:

```text
Official repositories
---------------------
extra   ripgrep              14.1.1-1    installed
  recursively searches directories for a regex pattern

AUR
---
ripgrep-all                  0.10.6-1
  ripgrep with PDF, ebook, and office document search
```

## Description strategy

- Search should remain compact enough for multi-result scanning.
- The package description may be shown beneath each result in the default view if it does not make the output too noisy.
- `archdown info <package>` should remain the place for fuller package detail.
- If the default search view becomes too dense, archdown may shorten or omit descriptions in compact mode rather than removing core identity columns.

## Color behavior

- Multi-color terminal output is desirable when the terminal supports it.
- Color should improve scanning, not become decoration.
- Color usage should remain readable on dark terminal themes.
- Color must not be the only way information is conveyed.
- A future no-color mode should be possible.

Suggested color direction:
- source labels: subtle distinct color by source class
- package names: brighter emphasis color
- installed marker: positive/success color
- section headers: muted accent color

## Ranking and grouping

- Keep backend result ordering unless archdown has a clear user-facing reason to improve grouping.
- Grouping should never hide package identity or source.
- If both official repo and AUR results exist, official repo results should appear first by default.

## Failure and fallback behavior

- If parsing fails, degrade gracefully instead of crashing.
- Raw backend output should remain available as fallback behavior.
- A future `--raw` mode should expose backend output directly.
- A fallback path must never pretend the structured renderer succeeded when it did not.

## Empty results behavior

- When a search matches nothing (empty backend output), the default view must print a clear "No packages found." line rather than blank output.
- The empty result should be routed through the normal search renderer so the friendly message stays consistent with the structured view.
- Non-empty output that fails to parse still falls back to raw passthrough; only genuinely empty results show the "No packages found." message.
- The backend exit code is preserved; the friendly message is a display concern, not a change in success semantics.

## Future extension points

- compact and richer human views
- machine-readable output modes
- explicit `--raw` and `--json` options
- explicit `--no-color` option
- configurable description visibility
