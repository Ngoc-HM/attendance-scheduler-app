"""SQLAlchemy ORM models.

Every model is imported here so that ``Base.metadata`` is fully populated for
Alembic autogenerate (see ``alembic/env.py``).
"""

from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.flight import Flight, FlightDay, FlightPreset
from app.models.holiday import Holiday
from app.models.leave import LeaveRequest
from app.models.role_code_counter import RoleCodeCounter
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User

__all__ = [
    "AttendanceRecord",
    "AuditLog",
    "Flight",
    "FlightDay",
    "FlightPreset",
    "Holiday",
    "LeaveRequest",
    "MonthlySchedule",
    "RoleCodeCounter",
    "ShiftAssignment",
    "ShiftChangeRequest",
    "User",
]
