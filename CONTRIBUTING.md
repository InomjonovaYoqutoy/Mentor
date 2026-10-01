# Contributing to Mentor

Mentor values **stability, data safety, coherent UX, and maintainable code** over feature volume.

## Development setup

```bat
python -m pip install -r requirements.txt
python main.py
```

Run the quality suite before proposing a change:

```bat
quality_check.bat
```

## Engineering expectations

- Keep UI, service, and database responsibilities separated.
- Use parameterized SQL and preserve foreign-key behavior.
- Add a migration when a schema change is required; never require users to delete an existing database.
- Avoid fake buttons, placeholder statistics, and decorative controls that imply unavailable functionality.
- Preserve the no-sidebar / floating-dock navigation model.
- Keep localization keys synchronized across English, Uzbek, and Russian.
- Prefer focused fixes over unrelated rewrites.
- Add regression coverage when fixing a bug that could reasonably return.

## Pull requests

A useful PR should include:

1. A concise problem/solution description.
2. Database migration implications, if any.
3. Screenshots for visible UI changes where useful.
4. Test results from `quality_check.bat`.
5. Localization notes if UI strings changed.

## Release priority

**Functionality → Stability → UX → Visual quality → Animation → Extra features**
