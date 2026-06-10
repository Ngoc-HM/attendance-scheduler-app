"""Reporting / export logic (F-15).

Returns structured rows; an exporter (Excel via openpyxl, CSV, ...) renders
them. Keeping data and format separate lets new layouts be added later
without API changes (spec §4.7 [CHỐT])."""

from __future__ import annotations

from sqlalchemy.orm import Session


def monthly(db: Session, year: int, month: int) -> dict:
    """F-15 — month attendance matrix (person × day) + per-person totals."""
    raise NotImplementedError  # TODO


def yearly(db: Session, year: int) -> dict:
    """F-15 — year roll-up per person."""
    raise NotImplementedError  # TODO
