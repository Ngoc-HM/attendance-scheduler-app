"""Monthly flight plan in Excel: template download + apply (F-04, owner 2026-11).

The pure halves live in ``flight_plan_template`` (build) and
``flight_plan_parser`` (read); this module adds the database side.

Applying a plan only touches what the file speaks about: the presets that
appear in it, on the days of its month. An unmarked day removes that preset's
two legs when both are there, a marked day writes them exactly like a preset applied to a day
(``flight_service._apply_presets_no_commit``). Legs of other FLT numbers,
and a lone leg of a preset (never shown as marked), are left alone, so a
download → upload round trip keeps the same legs.
"""

from __future__ import annotations

import calendar
from collections import Counter
from datetime import date, time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.flight import Flight, FlightPreset
from app.services import flight_service
from app.services.flight_pair_derivation import MAX_PAIRS
from app.services.flight_plan_parser import PlanParseResult
from app.services.flight_plan_template import TemplateRow, build_template

_LegSpec = tuple[str | None, time | None, time | None]  # (route, sta, std)


def _month_range(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _active_presets_by_pair(db: Session) -> dict[tuple[int, int], FlightPreset]:
    """Active presets keyed by (arrival, departure), in ``list_presets`` order.

    Two active presets with the same pair would make the template list the pair
    twice and its own re-upload fail as a duplicate row, so the first one wins.
    """
    by_pair: dict[tuple[int, int], FlightPreset] = {}
    for preset in flight_service.list_presets(db):
        if preset.is_active:
            by_pair.setdefault((preset.flt_arr, preset.flt_dep), preset)
    return by_pair


def template_bytes(db: Session, year: int, month: int) -> bytes:
    """The plan template, prefilled with the days both legs already exist."""
    presets = _active_presets_by_pair(db)
    if not presets:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("flight.template_no_presets")
        )
    first, last = _month_range(year, month)
    existing = {
        (row.day, row.flt_number)
        for row in db.query(Flight.day, Flight.flt_number).filter(
            Flight.day >= first, Flight.day <= last
        )
    }
    rows = [
        TemplateRow(
            p.label, p.flt_arr, p.flt_dep,
            {
                d for d in range(1, last.day + 1)
                if (date(year, month, d), p.flt_arr) in existing
                and (date(year, month, d), p.flt_dep) in existing
            },
        )
        for p in presets.values()
    ]
    return build_template(year, month, rows)


def _validate(
    plan: PlanParseResult, presets: dict[tuple[int, int], FlightPreset]
) -> list[str]:
    """Rule errors the parser cannot see: unknown presets and per-day limits."""
    errors = [
        t("flight.plan_unknown_preset").format(row=r.row, arr=r.flt_arr, dep=r.flt_dep)
        for r in plan.rows
        if (r.flt_arr, r.flt_dep) not in presets
    ]
    for day_no in range(1, calendar.monthrange(plan.year, plan.month)[1] + 1):
        marked = [r for r in plan.rows if day_no in r.days]
        day = date(plan.year, plan.month, day_no).isoformat()
        # The scheduler staffs at most MAX_PAIRS pairs a day (§5.3 #4).
        if len(marked) > MAX_PAIRS:
            errors.append(t("flight.plan_too_many_presets").format(day=day, max=MAX_PAIRS))
        counts = Counter(f for r in marked for f in {r.flt_arr, r.flt_dep})
        for flt in sorted(f for f, n in counts.items() if n > 1):
            errors.append(t("flight.plan_shared_flt").format(day=day, flt=flt))
    return errors


def import_plan(db: Session, plan: PlanParseResult) -> list[Flight]:
    """Apply a parsed plan in one transaction; any error writes nothing (422).

    Only FlightDay rows of days where a leg was written or deleted are
    recomputed, so untouched days get no row.
    """
    presets = _active_presets_by_pair(db)
    errors = plan.errors or _validate(plan, presets)
    if errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": t("flight.import_failed"), "errors": errors},
        )

    first, last = _month_range(plan.year, plan.month)
    flts = {f for r in plan.rows for f in (r.flt_arr, r.flt_dep)}
    existing = {
        (leg.day, leg.flt_number): leg
        for leg in db.query(Flight).filter(
            Flight.day >= first, Flight.day <= last, Flight.flt_number.in_(flts)
        )
    } if flts else {}

    to_write: dict[tuple[date, int], _LegSpec] = {}
    to_clear: set[tuple[date, int]] = set()
    for r in plan.rows:
        p = presets[(r.flt_arr, r.flt_dep)]
        for day_no in range(1, last.day + 1):
            day = date(plan.year, plan.month, day_no)
            legs = {(day, p.flt_arr), (day, p.flt_dep)}
            if day_no in r.days:
                # Same legs as applying the preset to a day (arrival: STA only,
                # departure: STD only); a departure equal to the arrival wins.
                to_write[(day, p.flt_arr)] = (p.route, p.sta, None)
                to_write[(day, p.flt_dep)] = (p.route, None, p.std)
            elif legs <= existing.keys():
                # Only a day the template showed as "x" (both legs present) is
                # cleared: a lone leg was never marked, so an unchanged
                # re-upload must not delete it.
                to_clear |= legs
    # A FLT cleared for one preset but written for another that day is kept.
    to_clear -= to_write.keys()

    touched: set[date] = set()
    try:
        # Deletions first (flushed) so the unique (day, flt) key is free again.
        for key in to_clear & existing.keys():
            db.delete(existing.pop(key))
            touched.add(key[0])
        db.flush()
        written: list[Flight] = []
        for (day, flt), (route, sta, std) in sorted(to_write.items()):
            leg = existing.get((day, flt)) or Flight(day=day, flt_number=flt)
            leg.route, leg.sta, leg.std = route, sta, std
            db.add(leg)
            written.append(leg)
            touched.add(day)
        db.flush()
        flight_service._recompute_pairs_for_days(db, touched)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("flight.import_failed")
        ) from exc
    for leg in written:
        db.refresh(leg)
    return written
