# Mentor — Project Overview

## Purpose

Mentor is a Windows desktop application for teachers, tutors, mentors, and private instructors. It brings students, lessons, attendance, assignments, notes, materials, tasks, goals, and statistics into one local workspace.

The product is built around a simple operational question:

> What does a teacher need to know and do right now?

That framing keeps the Home screen focused on today's workload, upcoming lessons, student context, and actions needing attention instead of filling the interface with unrelated analytics.

## Problem addressed

Teaching workflows are often split across calendars, notes apps, folders, spreadsheets, and messaging tools. That fragmentation makes simple questions harder to answer quickly:

- Who am I teaching today?
- What happened in the previous lesson?
- Was the student present?
- What homework is due?
- Where are the related materials?
- How much teaching work has been completed?

Mentor connects those relationships in one local database.

## Project objectives

1. Build a persistent desktop application, not disconnected mock screens.
2. Keep core functionality usable without internet connectivity.
3. Preserve user data across restarts and upgrades.
4. Maintain a modern Windows UI without a permanent sidebar.
5. Keep the data model relational so teaching entities connect meaningfully.
6. Support English, Uzbek, and Russian interfaces.
7. Keep the architecture modular enough for continued development.

## Technology

- **Python 3.12+** — readable, productive application development.
- **PySide6 / Qt** — native desktop windows, layouts, painting, animation, shortcuts, and packaging.
- **SQLite** — transactional embedded relational persistence with no database server.
- **PyInstaller** — Windows application packaging.

## Design direction

Mentor uses dark layered surfaces, restrained accent colors, a floating bottom dock, subtle glass treatment, rounded geometry, and short transitions.

Important constraints:

- no permanent left sidebar
- five primary navigation destinations
- floating dock stays inside the window
- visible UI should be functional
- animation should not compromise stability or modest hardware

## Current scope — v1.4

- Home dashboard
- Day/week Schedule
- Student profiles
- Attendance
- Lesson details and wrap-up
- Homework/assignments
- Recurring lessons and templates
- Notes
- Materials
- Tasks and goals
- Statistics
- Global search
- Reminders
- Backup/restore/export
- English / Uzbek / Russian localization
- Regional and appearance preferences

## Engineering evolution

- **0.9** established the working local-first foundation.
- **1.1** expanded scheduling and visual polish.
- **1.1.1** repaired real regressions and strengthened QA.
- **1.2** added student profiles and attendance.
- **1.3** connected lessons with assignments and post-lesson workflows.
- **1.4** introduced localization, regional settings, and personalization.

## Current limitations

- Designed for a single local user.
- No cloud sync or multi-device collaboration.
- Visual/runtime validation on Windows remains important for each UI-heavy release.
- Teaching Mode and advanced calendar drag/drop are planned, not shipped.

## Academic value

Mentor demonstrates practical work across desktop UI engineering, relational data modelling, migrations, persistence, backups, internationalization, automated regression testing, Windows packaging, and iterative UX refinement based on observed failures.
