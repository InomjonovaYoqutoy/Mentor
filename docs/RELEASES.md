# Release History

Mentor has evolved through six documented releases.

| Version | Codename | Main theme |
| --- | --- | --- |
| 0.9.0 | First Functional Build | Complete local-first foundation |
| 1.1.0 | Glass & Lessons | Scheduling depth and visual polish |
| 1.1.1 | Quality Hotfix | Regression repair and release discipline |
| 1.2.0 | Student Intelligence | Profiles and attendance |
| 1.3.0 | Lessons & Assignments | Connected lesson/homework workflow |
| 1.4.0 | Global & Personal | Localization and personalization |

> There was no formal 1.0.0 release. Development moved from 0.9.0 directly to 1.1.0.

## 0.9.0 — First Functional Build

Established the working product: PySide6 shell, SQLite persistence, Home, Schedule, Notes, Materials, Statistics, students, tasks, goals, search, reminders, backup/export, keyboard navigation, and PyInstaller workflow.

## 1.1.0 — Glass & Lessons

Expanded lesson scheduling with lesson types, meeting links, reminders, recurrence count, duration presets, subject autofill, Focus Timer, quick-create, richer schedule views, and a stronger glass/dock treatment.

The release also exposed an important lesson: source/database checks were not enough for a UI-heavy desktop release. Real Windows use revealed regressions addressed immediately in 1.1.1.

## 1.1.1 — Quality Hotfix

Focused on reliability rather than new features.

Critical work:
- fixed lesson scheduling failure caused by ambiguous SQL `status`
- added scheduling regression coverage
- removed the oversized Home Up Next island
- unified Notes into one workspace
- removed the dock decoration line
- replaced native quick-create menu styling with a custom popover

This release marked a shift toward explicit regression testing after serious UI/data bugs.

## 1.2.0 — Student Intelligence

Made students first-class workspaces through Student Profiles and persistent attendance.

Highlights:
- attendance states and attendance rates
- profile-based lesson/note actions
- safer duplicate/recurring lesson defaults
- search routing to student profiles
- `quality_check.bat`
- Qt offscreen smoke-test infrastructure

Database schema advanced to v3.

## 1.3.0 — Lessons & Assignments

Connected the teaching lifecycle end to end.

Highlights:
- homework/assignments
- Lesson Detail workspace
- post-lesson wrap-up
- recurring-series IDs and scoped controls
- lesson templates
- Needs review state
- assignment completion statistics

Database schema advanced to v4.

Recorded QA: **34 discovered, 29 passed, 0 failed, 5 skipped**.

## 1.4.0 — Global & Personal

Focused on product maturity.

Highlights:
- English / Uzbek / Russian localization
- canonical enum translation
- locale-aware dates and grammar
- 12/24-hour time
- Monday/Sunday week start
- Day/Week default schedule
- Orange/Amber/Graphite/Blue/Violet accents
- glass, motion, density, and glow preferences
- redesigned Settings
- live appearance preview with rollback
- localization regression coverage

Database schema remains v4.

Recorded QA: **40 discovered, 33 passed, 0 failed, 0 errors, 7 skipped**. The skipped cases were Qt runtime tests unavailable in that build environment.
