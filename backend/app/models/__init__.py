"""SQLAlchemy ORM models.

Every model is imported here so that ``Base.metadata`` is fully populated for
Alembic autogenerate (see ``alembic/env.py``).
"""

from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.flight import Flight, FlightDay
from app.models.holiday import Holiday
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User

__all__ = [
    "AttendanceRecord",
    "AuditLog",
    "Flight",
    "FlightDay",
    "Holiday",
    "LeaveRequest",
    "MonthlySchedule",
    "ShiftAssignment",
    "User",
]
