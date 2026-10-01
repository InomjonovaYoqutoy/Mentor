# Localization

Mentor 1.4 supports:

- English
- Uzbek (Latin)
- Russian

## Core rule

The database stores stable canonical values; the UI translates those values only for display.

Example:

```text
Stored:     Completed
English:    Completed
Uzbek:      Yakunlangan
Russian:    Завершён
```

This prevents a language switch from rewriting business data.

## Translation system

`mentor/i18n.py` contains the centralized catalog and helpers. UI code should request stable translation keys instead of branching directly on language.

Conceptually:

```python
tr("schedule.new_lesson")
```

## Regional behavior

Localization also covers formatting:

- weekday/month names
- lesson-count grammar
- duration formatting
- 12/24-hour time
- Monday/Sunday week start
- default Day/Week Schedule view

User-created names, subjects, notes, and assignment instructions are never automatically translated.

## Adding UI text

1. Add a stable translation key.
2. Add English, Uzbek, and Russian entries.
3. Use the key in UI code.
4. Run the quality suite.

Regression coverage checks literal UI translation-key coverage for Uzbek and Russian.
