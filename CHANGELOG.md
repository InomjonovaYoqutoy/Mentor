# Changelog

All documented Mentor releases are listed here. The repository preserves the original release naming used during development.

## [1.4.0] — Global & Personal

### Added
- Centralized localization infrastructure with English, Uzbek (Latin), and Russian.
- Canonical-enum translation so translated labels never rewrite stored status values.
- Locale-aware weekday/month presentation.
- 12-hour / 24-hour time.
- Monday / Sunday week start.
- Default Schedule view preference: Day / Week.
- Localized duration and lesson-count formatting.
- Category-based Settings workspace.
- Accent presets: Orange, Amber, Graphite, Blue, Violet.
- Glass intensity, motion, density, and atmospheric glow preferences.
- Live appearance preview with non-destructive Cancel behavior.
- About page with app version, schema version, and app-data location.
- Localization regression coverage and Qt smoke-test cases.

### Changed
- Main pages and the floating dock rebuild after language/appearance Save.
- Schedule respects regional preferences.
- Lesson/time displays honor 12/24-hour formatting.
- Custom-painted accents follow the selected theme.
- Settings rebuild preserves unsaved Notes draft and Schedule context.

### Fixed
- Localized homework status round-trips through canonical values correctly.
- Alternative accents no longer leave several hard-coded orange fragments.
- Floating UI repositioning no longer relies on a +1/-1 pixel resize workaround.

### Database
- Schema remains **v4**.
- Localization and personalization preferences use the existing `settings` table.

---

## [1.3.0] — Lessons & Assignments

### Added
- Persistent homework/assignments.
- Assignment links to learner, lesson, and material.
- Homework surfaces on Home, Student Profile, Lesson Details, and global search.
- Lesson Detail workspace.
- Post-lesson wrap-up flow for attendance, notes, and optional homework.
- Custom right-click lesson actions.
- Persistent recurring-series IDs and scoped series editing.
- Reusable lesson templates.
- `Needs review` state for past lessons not completed/cancelled.
- Assignment data in Statistics.

### Database
- Schema upgraded to **v4**.
- Added `assignments` and `lesson_templates`.
- Added `sessions.series_id`.

### QA
- Recorded result: **34 discovered, 29 passed, 0 failed, 5 skipped**.

---

## [1.2.0] — Student Intelligence

### Added
- Full Student Profile workspace.
- Persistent lesson attendance.
- Attendance: Not marked, Present, Late, Absent, Excused.
- Attendance rate/counts per student and an overall Statistics metric.
- Profile-based lesson/note actions.
- Student routing from global search.
- `quality_check.bat`.
- Headless Qt runtime smoke-test infrastructure.

### Database
- Schema upgraded to **v3** with `sessions.attendance`.

---

## [1.1.1] — Quality Hotfix

### Fixed
- Critical lesson scheduling failure caused by an ambiguous `status` column in overlap-check SQL.
- Added regression coverage for scheduling/conflict detection.
- Removed the large Home Up Next island.
- Rebuilt Notes as one unified workspace.
- Removed the decorative dock line.
- Replaced the native quick-create menu with a custom frameless popover.
- Improved new-lesson subject handling.

### QA
- Recorded hotfix validation set: **9 tests passed**.

---

## [1.1.0] — Glass & Lessons

### Added
- Expanded lesson scheduling workflow.
- Lesson type, meeting link, reminder, recurrence count.
- Subject suggestions and student-to-subject autofill.
- 30/45/60/90 minute presets.
- Focus Timer.
- Quick-create menu.
- Richer day/week schedule views.
- Per-day add controls.

### Visual
- Reworked glass dock and animated selected capsule.
- Segmented schedule control.
- Ambient orange depth and broader UI polish.

---

## [0.9.0] — First Functional Build

### Added
- Local-first PySide6 + SQLite foundation.
- Home, Schedule, Notes, Materials, Statistics.
- Students, tasks, goals, global search, local reminders.
- Session CRUD and day/week scheduling.
- Backup/restore and JSON/CSV export.
- First-run sample workspace option.
- Logging and PyInstaller workflow.

### Storage
- Application-owned data stored under `%APPDATA%\Mentor\`.

---

> Mentor did not have a formal `1.0.0` release. Development moved from `0.9.0` directly to `1.1.0`.
