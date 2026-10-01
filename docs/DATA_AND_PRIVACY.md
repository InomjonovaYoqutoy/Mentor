# Data & Privacy

Mentor is **local-first**.

Core functionality does not require a web server, cloud database, browser runtime, user-account service, or paid API.

## Storage

Application-owned data is stored under the Windows per-user Mentor application-data directory:

```text
%APPDATA%\Mentor\
```

This keeps persistent user data separate from the source folder and executable.

## SQLite data

Structured data includes students, lessons, notes, tasks, goals, attendance, assignments, templates, activity, and settings.

## Teaching materials

Mentor stores references to external teaching files rather than copying every source file into the database. Missing external files are handled as missing references.

## Backups and exports

Mentor supports:

- database backup
- database restore
- JSON export
- CSV export where useful

Schema upgrades use migrations instead of requiring a database reset.

## Public bug reports

Do not upload real student names, contacts, private notes, or other sensitive educational information to public GitHub issues. Use anonymized reproduction data.
