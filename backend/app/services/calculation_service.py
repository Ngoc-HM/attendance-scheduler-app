"""Automatic month-end calculations (F-14)."""

from __future__ import annotations

from sqlalchemy.orm import Session


def close_month(db: Session, year: int, month: int) -> dict:
    """F-14 — close the month and prepare carry-over to the next month.

    For each user, from the actual attendance:
        * count comp days earned (A/D → +1 CD) vs. taken,
        * update ``carry_comp``,
        * compute ``carry_streak`` = consecutive working days up to the last
          day of the month (0 if the last day is off) — feeds §5.5.

    Per F-14, no complex annual-leave accrual is performed here.
    Returns a per-user summary.
    """
    raise NotImplementedError  # TODO
