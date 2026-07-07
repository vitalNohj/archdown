# list command

## Goal

Show installed packages in a structured, scan-friendly view while tracking version changes for packages managed by archdown.

## Managed package state

- A package is archdown-managed when it was installed through `archdown install` or adopted with `archdown adopt`.
- Managed state should store the package name and the last installed version observed by archdown.
- Adopted packages participate in the same tracking behavior as packages installed through archdown.

## Version observation

- Any structured `archdown list` invocation should compare the currently installed version of each managed package with its stored last-seen version.
- If a managed package has no stored last-seen version, record the current version without rendering a recently-updated tag.
- If the current version differs from the stored last-seen version, update stored state to the current version and mark that item as recently updated for this render.
- Only packages still installed should be shown or updated by `list`.

## Recently-updated tag

- Recently updated managed packages should render an inline green tag:

```text
(Recently Updated <old-version> -> <new-version>)
```

- The tag text must include both the prior stored version and the currently installed version.
- Color should improve scanning, but the text itself must remain meaningful without color.
- The tag should appear only for the `list` render that observes the change; later list runs should not repeat it unless the version changes again.

## Raw passthrough behavior

- Raw passthrough list modes should expose backend output directly.
- Raw passthrough must not update managed last-seen versions.
- Raw passthrough must not render archdown-only tags such as `Recently Updated`.

## Failure behavior

- If managed state cannot be read or written, `list` should still preserve access to installed package results when practical.
- State failures should not invent recently-updated tags.
