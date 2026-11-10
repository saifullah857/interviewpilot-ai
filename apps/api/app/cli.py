"""Admin command line. Run from apps/api:  python -m app.cli <command>"""

import argparse
import getpass
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import service as auth_service
from app.coding import problems as coding_problems
from app.companies import seed, service
from app.core.db import get_engine
from app.models.audit import record
from app.models.user import User


def cmd_import_seed(args) -> int:
    with Session(get_engine()) as db:
        r = seed.import_seed(db, Path(args.file) if args.file else seed.DEFAULT_SEED)
    print(f"Seed imported: {r}. All companies are candidates until an admin verifies them.")
    return 0


def cmd_import_problems(args) -> int:
    with Session(get_engine()) as db:
        r = coding_problems.import_bank(db, Path(args.file) if args.file else coding_problems.DEFAULT_BANK)
    print(f"Coding problems imported: {r}.")
    return 0


def cmd_make_admin(args) -> int:
    with Session(get_engine()) as db:
        user = db.scalars(select(User).where(User.email == args.email.strip().lower())).first()
        if user is None:
            print("No user with that email. Sign up in the app first.", file=sys.stderr)
            return 1
        user.role = "admin"
        record(db, "admin_granted", None, user_id=str(user.id))
        db.commit()
    print("Done. That user is now an admin; they must log in again.")
    return 0


def cmd_reset_password(args) -> int:
    """For a forgotten password (there is no email service in the local MVP). The new password is typed at a hidden prompt, never given as an argument."""
    with Session(get_engine()) as db:
        user = db.scalars(select(User).where(User.email == args.email.strip().lower())).first()
        if user is None:
            print("No user with that email.", file=sys.stderr)
            return 1
        pw = getpass.getpass("New password (at least 8 characters): ")
        if len(pw) < 8 or len(pw) > 128:
            print("The password must be 8 to 128 characters.", file=sys.stderr)
            return 1
        if pw != getpass.getpass("Repeat the new password: "):
            print("The two passwords do not match.", file=sys.stderr)
            return 1
        auth_service.set_password(db, user, pw)
        record(db, "password_reset_by_admin", None, user_id=str(user.id))
        db.commit()
    print("Done. All of that user's sessions were signed out; they can log in with the new password.")
    return 0


def cmd_stale_check(_args) -> int:
    with Session(get_engine()) as db:
        n = service.mark_overdue_stale(db)
        db.commit()
    print(f"{n} company(ies) marked stale (office evidence older than 180 days).")
    return 0


def cmd_import_questions(args) -> int:
    from app.questions import service as qs

    with Session(get_engine()) as db:
        print(f"Questions imported: {qs.import_bank(db)}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import-seed", help="Import Lahore candidate companies (never verified)")
    s.add_argument("--file")
    s.set_defaults(fn=cmd_import_seed)
    c = sub.add_parser("import-problems", help="Import or update the coding problem bank")
    c.add_argument("--file")
    c.set_defaults(fn=cmd_import_problems)
    qn = sub.add_parser("import-questions", help="Import or update the company-wise question bank from data/questions")
    qn.set_defaults(fn=cmd_import_questions)
    a = sub.add_parser("make-admin", help="Give an existing user the admin role")
    a.add_argument("email")
    a.set_defaults(fn=cmd_make_admin)
    r = sub.add_parser("reset-password", help="Set a new password for a user who forgot theirs (prompts; signs them out everywhere)")
    r.add_argument("email")
    r.set_defaults(fn=cmd_reset_password)
    k = sub.add_parser("stale-check", help="Mark verified companies stale when evidence is over 180 days old")
    k.set_defaults(fn=cmd_stale_check)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
