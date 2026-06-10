"""Domain enumerations shared by models, schemas and the scheduler.

These encode the fixed vocabulary from the spec: roles (§3), attendance
symbols (§7) and leave/schedule lifecycle states.
"""

from __future__ import annotations

import enum


class Role(str, enum.Enum):
    """Personnel roles (spec §3)."""

    M = "M"    # Admin + flexible
    T = "T"    # Flexible (may request changes; not forced)
    A1 = "A1"  # Fixed / mandatory
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"

    @property
    def is_admin(self) -> bool:
        return self is Role.M

    @property
    def is_fixed(self) -> bool:
        """A1–A4 must follow the system schedule strictly (spec §3)."""
        return self in {Role.A1, Role.A2, Role.A3, Role.A4}

    @property
    def is_flexible(self) -> bool:
        return self in {Role.M, Role.T}


class UserStatus(str, enum.Enum):
    """Account lifecycle (F-01: self-register then admin approval)."""

    pending = "pending"
    active = "active"
    disabled = "disabled"


class AttendanceCode(str, enum.Enum):
    """Per-day attendance / shift symbols (spec §7).

    Exactly one code is assigned to each (person, day) — both in the planned
    schedule (``ShiftAssignment``) and in the actual record (``AttendanceRecord``).
    """

    A = "A"      # ARR duty — working day
    D = "D"      # DEP duty — working day
    A_D = "A/D"  # ARR+DEP in one day — counts as 2 working days, earns 1 comp day
    AD = "AD"    # Two shifts, but NO comp day (differs from A/D)
    X = "X"      # OFF day (includes public holidays)
    CD = "CD"    # Compensation day off
    O_D = "O/D"  # Office duty — working day
    T = "T"      # Training / online course — working day
    B = "B"      # Business trip — working day
    S = "S"      # Reported sick (special-category health data — spec §9.1)
    AL = "AL"    # Annual leave

    @property
    def is_working(self) -> bool:
        return self in {
            AttendanceCode.A,
            AttendanceCode.D,
            AttendanceCode.A_D,
            AttendanceCode.AD,
            AttendanceCode.O_D,
            AttendanceCode.T,
            AttendanceCode.B,
        }

    @property
    def workday_value(self) -> int:
        """Number of working days this code counts as (A/D = 2, spec §7)."""
        if self is AttendanceCode.A_D:
            return 2
        return 1 if self.is_working else 0


class LeaveType(str, enum.Enum):
    """Leave registration buckets (F-05 / F-06)."""

    monthly = "monthly"  # < 5 consecutive days — registered each month
    annual = "annual"    # >= 5 consecutive days — registered as annual leave


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ScheduleStatus(str, enum.Enum):
    draft = "draft"          # generated, awaiting admin review / manual edits (F-09)
    published = "published"  # locked & visible to all users
