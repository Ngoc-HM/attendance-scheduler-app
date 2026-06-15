"""Audit logging (spec §9.5) — best-effort writer for admin actions.

Records who did what (actor, action, entity, id, optional detail) so the §9
compliance trail exists. Writing the audit row must NEVER break the underlying
action: failures are swallowed and logged, not raised.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def record(
    db: Session,
    actor_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    detail: str | None = None,
) -> None:
    """Append an audit row. Best-effort — never raises into the caller."""
    try:
        db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                detail=detail,
            )
        )
        db.commit()
    except Exception:  # noqa: BLE001 — audit must not abort the real action
        logger.exception("Audit write failed: action=%s entity=%s", action, entity)
        db.rollback()
