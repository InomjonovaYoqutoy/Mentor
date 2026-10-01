# Testing & QA

Mentor uses layered checks because a desktop application can compile successfully while still containing runtime UI or data-flow defects.

## Local quality command

```bat
quality_check.bat
```

The script:

1. compiles `mentor/` and `tests/`
2. runs unit and regression tests
3. runs Qt offscreen smoke tests when PySide6 is installed

## Test categories

### Database and service tests
Persistence, CRUD, backups, lesson conflicts, attendance, assignments, templates, recurring-series behavior, lesson wrap-up, and migrations.

### Source regression tests
Protect previously reported failures and high-risk UI architecture behavior.

### Qt runtime smoke tests
Construct selected PySide6 windows with `QT_QPA_PLATFORM=offscreen`.

Covered smoke scenarios include Main Window/dock geometry, Notes, Lesson Details, Homework, templates, Student Profile, Russian UI/canonical enum persistence, and Settings preview rollback.

## Recorded Mentor 1.4 result

```text
Python compile: PASS
Tests discovered: 40
Passed: 33
Failed: 0
Errors: 0
Skipped: 7
```

The seven skips were Qt runtime tests because PySide6 was unavailable in that build environment. They remain part of the repository and should execute on a configured Windows system or CI runner.

## Release rule

Compilation alone is not sufficient release verification. UI-heavy changes should also receive a visual Windows pass.

Recommended manual checks:

- create/edit/delete a lesson
- switch Day/Week Schedule
- open a Student Profile
- mark attendance
- create/complete homework
- create/save/delete a note
- add/open a material
- use global search
- switch English/Uzbek/Russian
- preview/cancel appearance changes
- resize the main window and verify floating dock geometry
