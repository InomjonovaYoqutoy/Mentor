# Security Policy

Mentor is a local-first desktop application. Security-sensitive areas include SQLite writes, backup/restore, file-path handling, imported data, and packaged Windows builds.

## Reporting a vulnerability

Please avoid publishing exploitable details in a public issue before a fix is available. Report the problem privately to the repository owner through GitHub where possible, including:

- affected Mentor version
- clear reproduction steps
- expected vs actual behavior
- security impact
- relevant logs or screenshots with personal data removed

## Project security principles

- parameterized SQL
- SQLite foreign-key enforcement
- input validation at application boundaries
- no arbitrary user-provided SQL execution
- no required cloud backend
- per-user application-data storage
- explicit backup/restore handling
- cautious handling of external material paths

Do not include real student information, private contact details, or sensitive teaching notes in public bug reports.
