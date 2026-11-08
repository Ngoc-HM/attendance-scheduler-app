"""Audit logging (spec §9.5) — fail-loud writer for admin actions.

Records who did what (actor, action, entity, id, optional detail) so the §9
compliance trail exists. An audit row that cannot be written is an incident,
not a footnote: the failure is logged with a stack trace and surfaced to the
caller as HTTP 500 so it is never silently lost.

Limitation (documented in ``docs/deployment-guide.md``): services commit the
business change before the endpoint records the audit row, so a failed audit
write can leave the change persisted while the client receives a 500. The
error log carries the full action/entity context for reconciliation.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


def record(
    db: Session,
    actor_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    detail: str | None = None,
) -> AuditLog:
    """Append an audit row and commit it. Raises HTTP 500 when the write fails."""
    row = AuditLog(
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
    )
    try:
        db.add(row)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Audit write failed: actor=%s action=%s entity=%s id=%s detail=%s",
            actor_id, action, entity, entity_id, detail,
        )
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=t("audit.write_failed"),
        ) from exc
    return row
