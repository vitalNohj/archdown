# Contributing

Current development loop:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
.venv/bin/archdown --dry-run search ripgrep
```

Contribution rules

- For major behavior changes, update the relevant spec under `openspec/` before or alongside the code change.
- Add or update tests for spec-backed behavior changes.
- Prefer structured parsing and renderer improvements over raw backend output passthrough.
- If code and spec disagree, fix one immediately.

Current commands:
- install
- uninstall
- search
- info
- list
- outdated
- refresh
- update
- upgrade
- doctor

Initial priorities:
1. expand tests around CLI behavior and output
2. improve uninstall semantics and configurability
3. enrich info output and backend introspection
4. package and release strategy
