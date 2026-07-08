# OpenSpec for archdown

This directory holds behavior specs for archdown.

## Principles

- Specs define intended user behavior.
- Code should implement specs, not the other way around.
- Backend tools such as `yay`, `paru`, and `pacman` are implementation details.
- archdown should prefer a clearer parsed UX over raw backend output.

## Specs

- `specs/archdown-core.md` - cross-command product and backend principles.
- `specs/search-command.md` - structured search behavior.
- `specs/list-command.md` - structured list behavior, managed package version tracking, and recently-updated tags.
- `specs/outdated-command.md` - read-only structured listing of packages with an available upgrade.

## Workflow

1. Update or add a spec.
2. Implement against the spec.
3. Add or adjust tests.
4. Verify behavior.

If code and spec disagree, fix one immediately.
