# Contributing

Current development loop:

```bash
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/archdown --dry-run search ripgrep
```

Initial priorities:
1. tests for backend selection and command mapping
2. better UX around uninstall semantics
3. info/doctor commands
4. package/release strategy
