from __future__ import annotations

from mentor.app import MentorApplication


def main() -> int:
    return MentorApplication().run()


if __name__ == "__main__":
    raise SystemExit(main())