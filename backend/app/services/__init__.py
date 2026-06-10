"""Service layer: business logic, called by the API endpoints.

Endpoints stay thin (validation + wiring); all rules from spec §4–§6 live
here and in ``app.scheduler`` for the solver-specific logic.
"""
