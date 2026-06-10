"""User model (spec §3 — roles & permissions)."""

from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import Role, UserStatus


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    hashed_password: Mapped[str] = mapped_column(String(255))

    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role"))
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"), default=UserStatus.pending
    )

    # --- Auto-calculated carry-over fields (scheduler input §5.1, F-14) ----
    # Remaining annual-leave balance (informational; complex accrual is out of
    # scope per F-14 note).
    annual_leave_balance: Mapped[int] = mapped_column(Integer, default=0)
    # Outstanding compensation days (CD) carried from the previous month —
    # used as a tie-breaker when leave requests conflict (§5.4 #9).
    carry_comp: Mapped[int] = mapped_column(Integer, default=0)
    # Consecutive working days at the end of the previous month — feeds the
    # "max 5 consecutive" constraint across the month boundary (§5.5).
    carry_streak: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username} role={self.role.value}>"
