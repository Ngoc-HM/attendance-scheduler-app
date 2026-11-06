"""User management logic (F-01, F-03).

Guards enforced here:
* **last-admin lockout** — disallow role or status changes that would leave
  the system without any active admin (role ``M``).
* **fixed-team warning** — surface a soft warning when the change would empty
  the active fixed group (role ``A``) so the UI can prompt for confirmation.

Both behaviours are intentionally implemented here (not in routers) so they
apply to every entry point that mutates users.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.enums import Role, UserStatus
from app.models.leave import LeaveRequest
from app.models.role_code_counter import RoleCodeCounter
from app.models.schedule import ShiftAssignment
from app.models.self_arrange_request import SelfArrangeRequest
from app.models.shift_change_request import ShiftChangeRequest
from app.models.time_clock import TimeClockEntry
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def next_user_code(db: Session, role: Role) -> str:
    """Allocate the next never-reused code for a role (e.g. 'A1', 'T2'). Caller commits."""
    counter = (
        db.query(RoleCodeCounter)
        .filter(RoleCodeCounter.role == role.value)
        .with_for_update()
        .one_or_none()
    )
    if counter is None:
        counter = RoleCodeCounter(role=role.value, next_seq=0)
        db.add(counter)
        db.flush()
    counter.next_seq += 1
    return f"{role.value}{counter.next_seq}"


def _get_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    return user


def _ensure_username_free(db: Session, username: str) -> None:
    exists = db.query(User).filter(User.username == username).one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("user.username_taken"))


def _is_active_admin(user: User) -> bool:
    return user.role is Role.M and user.status is UserStatus.active


def _count_active_admins(db: Session) -> int:
    db.expire_all()
    return (
        db.query(User)
        .filter(User.role == Role.M, User.status == UserStatus.active)
        .count()
    )


def _count_active_fixed(db: Session) -> int:
    db.expire_all()
    return (
        db.query(User)
        .filter(User.role == Role.A, User.status == UserStatus.active)
        .count()
    )


def _persist_new(db: Session, payload: UserCreate, status_: UserStatus) -> User:
    _ensure_username_free(db, payload.username)
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
        status=status_,
        code=next_user_code(db, payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register(db: Session, payload: UserCreate) -> User:
    """F-01 — self-registration; created ``pending`` until an admin approves."""
    return _persist_new(db, payload, UserStatus.pending)


def create(db: Session, payload: UserCreate) -> User:
    """F-01/F-03 — admin creates an active user with an assigned role."""
    return _persist_new(db, payload, UserStatus.active)


def approve(db: Session, user_id: int) -> User:
    """F-01 — activate a pending account."""
    user = _get_or_404(db, user_id)
    user.status = UserStatus.active
    db.commit()
    db.refresh(user)
    return user


def _ensure_last_admin_preserved(
    db: Session, user: User, new_role: Role | None, new_status: UserStatus | None
) -> None:
    """Raise 409 if applying ``new_role``/``new_status`` removes the last admin.

    A user counts toward the admin pool only while active and role ``M``.
    ``None`` means the corresponding field is unchanged.
    """
    if not _is_active_admin(user):
        return

    effective_role = new_role if new_role is not None else user.role
    effective_status = new_status if new_status is not None else user.status

    if effective_role is Role.M and effective_status is UserStatus.active:
        return  # still an active admin after the change

    remaining = _count_active_admins(db) - 1
    if remaining < 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("user.last_admin_lockout")
        )


def _ensure_last_admin_survives_delete(db: Session, user: User) -> None:
    """Raise 409 if deleting ``user`` would leave the system admin-less."""
    if not _is_active_admin(user):
        return
    remaining = _count_active_admins(db) - 1
    if remaining < 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("user.last_admin_lockout")
        )


def _fixed_team_warning(
    db: Session, user: User, new_role: Role | None, new_status: UserStatus | None
) -> str | None:
    """Return a soft warning if the change empties the active fixed group.

    The change is still applied; the caller surfaces the message to the admin.
    """
    if user.role is not Role.A:
        return None

    effective_role = new_role if new_role is not None else user.role
    effective_status = new_status if new_status is not None else user.status

    if effective_role is Role.A and effective_status is UserStatus.active:
        return None  # still an active fixed member after the change

    remaining = _count_active_fixed(db) - 1
    if remaining < 1:
        return t("user.fixed_team_empty")
    return None


def update(db: Session, user_id: int, payload: UserUpdate) -> tuple[User, list[str]]:
    """F-03 — admin edits profile/role/status (and optionally resets password).

    Returns ``(user, warnings)``. Hard guard: last admin lockout.
    Soft warning: emptying the fixed team.
    """
    user = _get_or_404(db, user_id)
    _ensure_last_admin_preserved(db, user, payload.role, payload.status)
    warnings: list[str] = []

    if payload.full_name is not None:
        user.full_name = payload.full_name

    role_changed = payload.role is not None and payload.role != user.role
    status_changed = payload.status is not None and payload.status != user.status

    # Compute fixed-team warning against the BEFORE state so the message
    # reflects the situation that will be lost, not the one already applied.
    if role_changed:
        warning = _fixed_team_warning(db, user, payload.role, None)
        if warning:
            warnings.append(warning)
    if status_changed:
        warning = _fixed_team_warning(
            db, user, payload.role if role_changed else None, payload.status
        )
        if warning and warning not in warnings:
            warnings.append(warning)

    # Apply the actual mutations.
    if payload.role is not None:
        user.role = payload.role
        if role_changed:
            # Reassign a code matching the new role letter; old code not reused.
            user.code = next_user_code(db, payload.role)

    if payload.status is not None:
        user.status = payload.status

    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)
    return user, warnings


def delete(db: Session, user_id: int) -> None:
    """Hard delete a user and cascade their historical rows.

    Cascade order avoids FK violations on SQLite/Postgres:
    1. Audit logs that *point at* this user keep their row but null ``actor_id``
       so the audit trail of OTHER users is not lost.
    2. Attendance records ``recorded_by`` is nulled; rows owned by this user
       are deleted (they describe the user's own day).
    3. Leave / shift / self-arrange / shift-change / time-clock rows owned by
       this user are deleted.
    4. The ``User`` row itself is removed.

    Last-admin lockout is enforced before any cascade runs.
    """
    user = _get_or_404(db, user_id)
    _ensure_last_admin_survives_delete(db, user)

    db.query(AuditLog).filter(AuditLog.actor_id == user.id).update(
        {AuditLog.actor_id: None}, synchronize_session=False
    )

    db.query(AttendanceRecord).filter(
        AttendanceRecord.recorded_by == user.id
    ).update(
        {AttendanceRecord.recorded_by: None}, synchronize_session=False
    )
    db.query(AttendanceRecord).filter(AttendanceRecord.user_id == user.id).delete(
        synchronize_session=False
    )

    db.query(LeaveRequest).filter(LeaveRequest.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(ShiftAssignment).filter(ShiftAssignment.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(SelfArrangeRequest).filter(
        SelfArrangeRequest.requester_id == user.id
    ).delete(synchronize_session=False)
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.requester_id == user.id
    ).delete(synchronize_session=False)
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.counterpart_user_id == user.id
    ).delete(synchronize_session=False)
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.decided_by_id == user.id
    ).delete(synchronize_session=False)
    db.query(TimeClockEntry).filter(TimeClockEntry.user_id == user.id).delete(
        synchronize_session=False
    )

    db.delete(user)
    db.commit()


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()
