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
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.enums import LeaveStatus, Role, UserStatus
from app.models.leave import LeaveRequest
from app.models.role_code_counter import RoleCodeCounter
from app.models.schedule import ShiftAssignment
from app.models.self_arrange_request import SelfArrangeRequest
from app.models.shift_change_request import ShiftChangeRequest
from app.models.time_clock import TimeClockEntry
from app.models.user import User
from app.schemas.user import RegisterRequest, UserCreate, UserUpdate


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
    """A name is taken whatever its case: login ignores case
    (``auth_service.find_by_username``), so two accounts must never answer
    to the same typed name."""
    exists = (
        db.query(User.id)
        .filter(func.lower(User.username) == username.strip().lower())
        .first()
    )
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
        username=payload.username.strip(),  # login trims what is typed
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
        status=status_,
        code=next_user_code(db, payload.role),
    )
    # Unset → the model default (ANNUAL_LEAVE_DEFAULT_DAYS) applies on insert.
    if payload.annual_leave_quota is not None:
        user.annual_leave_quota = payload.annual_leave_quota
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register(db: Session, payload: RegisterRequest) -> User:
    """F-01 — self-registration; created ``pending`` with role ``T`` until an
    admin approves it and assigns the real role (F-03)."""
    return _persist_new(
        db, UserCreate(**payload.model_dump(), role=Role.T), UserStatus.pending
    )


def create(db: Session, payload: UserCreate) -> User:
    """F-01/F-03 — admin creates an active user with an assigned role."""
    return _persist_new(db, payload, UserStatus.active)


def approve(db: Session, user_id: int, role: Role) -> User:
    """F-01/F-03 — activate a pending account with the role the admin assigns.

    Only ``pending`` accounts qualify (409 otherwise), so approval is never a
    second role-change path: active/disabled users change role via
    :func:`update`, which carries the admin and fixed-team guards. A role
    change reallocates the code for the new role (the old one is never reused).
    """
    user = _get_or_404(db, user_id)
    if user.status is not UserStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("user.not_pending"))
    if role != user.role:
        user.role = role
        user.code = next_user_code(db, role)
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


def _recorder_after_delete(db: Session, user: User, acting_admin_id: int) -> int:
    """Who the deleted user's recorded actuals are attributed to (#39).

    Normally the admin doing the delete. An admin deleting their own account
    hands them to another active admin instead — one always exists, because
    the last-admin guard has already run.
    """
    if acting_admin_id != user.id:
        return acting_admin_id
    other = (
        db.query(User.id)
        .filter(
            User.id != user.id,
            User.role == Role.M,
            User.status == UserStatus.active,
        )
        .order_by(User.id)
        .first()
    )
    if other is None:  # unreachable after the last-admin guard
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("user.last_admin_lockout")
        )
    return int(other[0])


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
    """F-03 — admin edits profile/role/status/annual leave quota (and
    optionally resets the password).

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

    if payload.annual_leave_quota is not None:
        user.annual_leave_quota = payload.annual_leave_quota

    db.commit()
    db.refresh(user)
    return user, warnings


def ensure_deletable(db: Session, user_id: int) -> User:
    """Run the delete guards (404, last-admin lockout) without changing data.

    The endpoint calls this before writing the ``user.delete`` audit row, so a
    refused delete never leaves an audit entry behind.
    """
    user = _get_or_404(db, user_id)
    _ensure_last_admin_survives_delete(db, user)
    return user


def delete(db: Session, user_id: int, acting_admin_id: int) -> None:
    """Hard delete a user and cascade their historical rows.

    Cascade order avoids FK violations on SQLite/Postgres:
    1. Audit logs that *point at* this user keep their row but null ``actor_id``
       so the audit trail of OTHER users is not lost.
    2. Attendance rows this user RECORDED (as admin) are reattributed to the
       acting admin (decision #39): a NULL ``recorded_by`` means "still as
       seeded from the roster", and roster edits would then overwrite those
       real actuals. Rows owned by this user are deleted (they describe the
       user's own day).
    3. Leave / shift / self-arrange / shift-change / time-clock rows owned by
       this user are deleted.
    4. Requests of OTHER users (ruling R8): the ones this user decided keep
       their row with ``decided_by_id`` NULL (shift changes and self-arrange
       batches); a swap naming this user as counterpart is deleted while
       pending and kept with ``counterpart_user_id`` NULL once decided.
    5. The ``User`` row itself is removed.

    Last-admin lockout is enforced before any cascade runs.
    """
    user = ensure_deletable(db, user_id)

    db.query(AuditLog).filter(AuditLog.actor_id == user.id).update(
        {AuditLog.actor_id: None}, synchronize_session=False
    )

    db.query(AttendanceRecord).filter(
        AttendanceRecord.recorded_by == user.id
    ).update(
        {AttendanceRecord.recorded_by: _recorder_after_delete(db, user, acting_admin_id)},
        synchronize_session=False,
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
    db.query(TimeClockEntry).filter(TimeClockEntry.user_id == user.id).delete(
        synchronize_session=False
    )

    # R8 — other users' requests outlive the people who decided or joined them.
    # Pending counterpart swaps go first; the null-out below would hide them.
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.counterpart_user_id == user.id,
        ShiftChangeRequest.status == LeaveStatus.pending,
    ).delete(synchronize_session=False)
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.counterpart_user_id == user.id
    ).update(
        {ShiftChangeRequest.counterpart_user_id: None}, synchronize_session=False
    )
    db.query(ShiftChangeRequest).filter(
        ShiftChangeRequest.decided_by_id == user.id
    ).update({ShiftChangeRequest.decided_by_id: None}, synchronize_session=False)
    db.query(SelfArrangeRequest).filter(
        SelfArrangeRequest.decided_by_id == user.id
    ).update({SelfArrangeRequest.decided_by_id: None}, synchronize_session=False)

    db.delete(user)
    db.commit()


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def list_directory(db: Session) -> list[User]:
    """Active users ordered by code, for the employee-visible code directory."""
    return (
        db.query(User)
        .filter(User.status == UserStatus.active)
        .order_by(User.code)
        .all()
    )
