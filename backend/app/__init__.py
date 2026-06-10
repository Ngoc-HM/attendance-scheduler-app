"""Attendance & Auto-Scheduler backend.

FastAPI service that holds the business logic and the constraint-solver
scheduling engine (see spec sections 4 & 5). See ``app.main`` for the entry
point and ``app.scheduler`` for the OR-Tools engine.
"""

__version__ = "0.1.0"
