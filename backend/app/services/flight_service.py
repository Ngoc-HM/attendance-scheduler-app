"""Flight schedule logic (F-04, §8).

Both manual entry and Excel import feed ``FlightDay.flight_pairs``, the
scheduler's ``flightPairs[d]`` input (spec §5.3 #4).

See ``flight_excel_parser.py`` for the expected Excel column layout.
"""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.flight import Flight, FlightDay, FlightPreset
from app.schemas.flight import FlightDayApply, FlightDayApplyBatch, FlightDayUpsert, FlightPresetUpsert, FlightUpsert
from app.services.flight_excel_parser import parse_flight_workbook
from app.services.flight_pair_derivation import derive_pairs_for_day

# Maximum allowed upload size (2 MB).
_MAX_UPLOAD_BYTES = 2 * 1024 * 1024
_ALLOWED_EXTENSION = ".xlsx"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_create_flight_day(db: Session, day: date) -> FlightDay:
    """Fetch an existing FlightDay or build a new (uncommitted) one."""
    fd = db.query(FlightDay).filter(FlightDay.day == day).one_or_none()
    if fd is None:
        fd = FlightDay(day=day, flight_pairs=0)
        db.add(fd)
    return fd


def _recompute_pairs_for_days(db: Session, days: set[date]) -> None:
    """Recompute and persist FlightDay.flight_pairs for each given day.

    Groups all Flight rows for each day, calls pure derivation, then updates
    the FlightDay row (creating it if absent).
    """
    for day in days:
        flt_numbers = [
            row.flt_number
            for row in db.query(Flight.flt_number).filter(Flight.day == day).all()
        ]
        pairs = derive_pairs_for_day(flt_numbers)
        fd = _get_or_create_flight_day(db, day)
        fd.flight_pairs = pairs


# ---------------------------------------------------------------------------
# Public API — days
# ---------------------------------------------------------------------------


def list_days(db: Session, year: int, month: int) -> list[FlightDay]:
    """Return all FlightDay rows for the given year/month, ordered by day."""
    return (
        db.query(FlightDay)
        .filter(
            FlightDay.day >= date(year, month, 1),
            FlightDay.day < date(year + (month // 12), (month % 12) + 1, 1),
        )
        .order_by(FlightDay.day)
        .all()
    )


def list_flights_for_days(db: Session, days: list[date]) -> dict[date, list[Flight]]:
    """Return Flight rows grouped by day (keyed by date), ordered by flt_number.

    Used by the endpoint to enrich FlightDayRead with its constituent legs.
    Returns an empty list for days with no Flight rows.
    """
    if not days:
        return {}

    rows = (
        db.query(Flight)
        .filter(Flight.day.in_(days))
        .order_by(Flight.day, Flight.flt_number)
        .all()
    )
    result: dict[date, list[Flight]] = {d: [] for d in days}
    for row in rows:
        result[row.day].append(row)
    return result


def upsert_day(db: Session, payload: FlightDayUpsert) -> FlightDay:
    """Manually set the flight-pair count (0/1/2) for a day.

    Pydantic validates 0 <= flight_pairs <= 2 via Field(ge=0, le=2); this
    check provides a descriptive error on any schema-bypass attempt.
    """
    if payload.flight_pairs not in (0, 1, 2):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("flight.invalid_pairs"),
        )
    fd = _get_or_create_flight_day(db, payload.day)
    fd.flight_pairs = payload.flight_pairs
    db.commit()
    db.refresh(fd)
    return fd


def upsert_flight(db: Session, payload: FlightUpsert) -> Flight:
    """Insert or update a single Flight row, then recompute that day's pairs."""
    flt = (
        db.query(Flight)
        .filter(Flight.day == payload.day, Flight.flt_number == payload.flt_number)
        .one_or_none()
    )
    if flt is None:
        flt = Flight(day=payload.day, flt_number=payload.flt_number)
        db.add(flt)

    flt.route = payload.route
    flt.sta = payload.sta
    flt.std = payload.std

    db.flush()
    _recompute_pairs_for_days(db, {payload.day})
    db.commit()
    db.refresh(flt)
    return flt


def flight_pairs_map(db: Session, days: list[date]) -> dict[date, int]:
    """Return ``{day: flight_pairs}`` for each requested day, defaulting to 0.

    Used by the scheduler (``SolverInput.flight_pairs``).
    """
    if not days:
        return {}

    rows = db.query(FlightDay).filter(FlightDay.day.in_(days)).all()
    result: dict[date, int] = {day: 0 for day in days}
    for row in rows:
        result[row.day] = row.flight_pairs
    return result


def import_excel(db: Session, file: UploadFile) -> list[Flight]:
    """F-04 — parse the monthly flight Excel (openpyxl) and upsert rows.

    See ``flight_excel_parser.py`` for full column spec.
    - File must be .xlsx and <= 2 MB.
    - Any hard parse error rejects the entire import (no partial commit).
    - On success, all Flight rows are upserted and FlightDay.flight_pairs is
      recomputed for every touched day.
    """
    # --- File validation ---
    filename = file.filename or ""
    if not filename.lower().endswith(_ALLOWED_EXTENSION):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("flight.import_bad_file"),
        )

    raw: bytes = file.file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=t("flight.import_bad_file"),
        )

    # --- Parse workbook (pure, no DB) ---
    try:
        parsed_rows, parse_errors = parse_flight_workbook(raw)
    except Exception as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("flight.import_bad_file"),
        ) from exc

    if parse_errors:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"message": t("flight.import_failed"), "errors": parse_errors},
        )

    # --- Upsert flights and recompute pairs ---
    touched_days: set[date] = set()
    upserted: list[Flight] = []

    try:
        for data in parsed_rows:
            flt = (
                db.query(Flight)
                .filter(
                    Flight.day == data["day"],
                    Flight.flt_number == data["flt_number"],
                )
                .one_or_none()
            )
            if flt is None:
                flt = Flight(day=data["day"], flt_number=data["flt_number"])
                db.add(flt)

            flt.route = data["route"]
            flt.sta = data["sta"]
            flt.std = data["std"]
            touched_days.add(data["day"])
            upserted.append(flt)

        db.flush()
        _recompute_pairs_for_days(db, touched_days)
        db.commit()

        for flt in upserted:
            db.refresh(flt)

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("flight.import_failed"),
        ) from exc

    return upserted


# ---------------------------------------------------------------------------
# Public API — presets
# ---------------------------------------------------------------------------


def list_presets(db: Session) -> list[FlightPreset]:
    """Return all FlightPreset rows ordered by sort_order then id."""
    return (
        db.query(FlightPreset)
        .order_by(FlightPreset.sort_order, FlightPreset.id)
        .all()
    )


def create_preset(db: Session, payload: FlightPresetUpsert) -> FlightPreset:
    """Insert a new FlightPreset row."""
    preset = FlightPreset(
        label=payload.label,
        route=payload.route,
        flt_arr=payload.flt_arr,
        flt_dep=payload.flt_dep,
        sta=payload.sta,
        std=payload.std,
        sort_order=payload.sort_order,
        is_active=payload.is_active,
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


def update_preset(db: Session, preset_id: int, payload: FlightPresetUpsert) -> FlightPreset:
    """Update an existing FlightPreset; raises 404 if not found."""
    preset = db.query(FlightPreset).filter(FlightPreset.id == preset_id).one_or_none()
    if preset is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=t("flight.preset_not_found"),
        )

    preset.label = payload.label
    preset.route = payload.route
    preset.flt_arr = payload.flt_arr
    preset.flt_dep = payload.flt_dep
    preset.sta = payload.sta
    preset.std = payload.std
    preset.sort_order = payload.sort_order
    preset.is_active = payload.is_active

    db.commit()
    db.refresh(preset)
    return preset


def delete_preset(db: Session, preset_id: int) -> None:
    """Delete a FlightPreset; raises 404 if not found."""
    preset = db.query(FlightPreset).filter(FlightPreset.id == preset_id).one_or_none()
    if preset is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=t("flight.preset_not_found"),
        )
    db.delete(preset)
    db.commit()


def _apply_presets_no_commit(db: Session, day: date, preset_ids: list[int]) -> FlightDay:
    """Replace a day's Flight legs from presets WITHOUT committing.

    - Load preset rows for given IDs (silently skip missing).
    - DELETE existing Flight rows for the day.
    - Build arrival + departure legs, deduped by flt_number (later wins).
    - flush() + recompute pairs. Caller must commit.
    """
    # Load requested presets in order; silently skip non-existent IDs.
    presets: list[FlightPreset] = []
    for pid in preset_ids:
        p = db.query(FlightPreset).filter(FlightPreset.id == pid).one_or_none()
        if p is not None:
            presets.append(p)

    # Delete all existing Flight rows for this day (replace semantics).
    db.query(Flight).filter(Flight.day == day).delete(synchronize_session=False)

    # Build legs deduped by flt_number; later preset in the list wins.
    legs: dict[int, Flight] = {}
    for preset in presets:
        # Arrival leg: carries sta only.
        legs[preset.flt_arr] = Flight(
            day=day,
            flt_number=preset.flt_arr,
            route=preset.route,
            sta=preset.sta,
            std=None,
        )
        # Departure leg: carries std only.
        legs[preset.flt_dep] = Flight(
            day=day,
            flt_number=preset.flt_dep,
            route=preset.route,
            sta=None,
            std=preset.std,
        )

    for leg in legs.values():
        db.add(leg)

    db.flush()
    _recompute_pairs_for_days(db, {day})
    # Flush again so the FlightDay row (possibly just created by _recompute_pairs_for_days)
    # is visible to subsequent queries within this session before commit.
    db.flush()
    fd = db.query(FlightDay).filter(FlightDay.day == day).one()
    return fd


def apply_presets_to_day(db: Session, payload: FlightDayApply) -> FlightDay:
    """Replace the day's Flight legs with legs derived from the selected presets.

    Semantics:
    - Load preset rows for the given IDs (silently ignore missing IDs).
    - DELETE all existing Flight rows for that day.
    - For each preset create arrival + departure legs.
      DEDUP by flt_number (dict keyed by flt_number; later preset wins)
      to prevent duplicate (day, flt_number) rows.
    - Flush, recompute flight_pairs, commit. Returns refreshed FlightDay.
    """
    fd = _apply_presets_no_commit(db, payload.day, payload.preset_ids)
    db.commit()
    db.refresh(fd)
    return fd


def apply_presets_batch(db: Session, payload: FlightDayApplyBatch) -> list[FlightDay]:
    """Replace Flight legs for multiple days atomically in a single commit.

    Each item behaves identically to apply_presets_to_day (replace semantics;
    empty preset_ids clears that day → flight_pairs 0).  All mutations are
    flushed then committed once, preserving atomicity.  Returns FlightDay rows
    in input order.
    """
    fds: list[FlightDay] = []
    for item in payload.items:
        fd = _apply_presets_no_commit(db, item.day, item.preset_ids)
        fds.append(fd)

    db.commit()

    for fd in fds:
        db.refresh(fd)

    return fds
