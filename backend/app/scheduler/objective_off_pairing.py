"""Days off come as two consecutive days, best on Fri+Sat (owner 2026-11-10).

Owner: "Ưu tiên các nhân sự nghỉ T6–T7, T7–CN, CN–T2 … được nghỉ 2 ngày liên
tiếp, theo mức độ ưu tiên lần lượt 1, 2, 3". Brings back the calendar-based
pair rewards of the removed ``objective_weekend`` (commit 4ada352) with the
new order and without the 7-day blocks. Points per person:

* base: 1 point for every X that has an X (or, on day 1, a rest day of
  history) right next to it — so a pair is worth 2 and a lone X nothing;
* weekday bonus for every adjacent X+X pair starting on a Friday, Saturday
  or Sunday: Fri+Sat +3, Sat+Sun +2, Sun+Mon +1 (``WEEKDAY_BONUS``);
* a pair may start on the previous month's last day when history says it
  was a rest day (``PersonInput.prev_codes``): day 1 off completes it.

Base points per paired DAY, not per adjacent pair: per pair, a run of four
X would hold three pairs and beat two separate pairs on the same days — on a
probe a lone person then traded a Sat+Sun week for Sat–Tue in one go. Per
paired day, four X earn 4 either way and the weekday bonus decides.

Only X the engine CHOOSES earns the weekday bonus (ruling R2): a pair
touching pinned approved leave earns no bonus, and a boundary pair earns it
only after an X (not leave) on last month's last day. Resting next to a leave
still earns the base point. Rewards are negative terms in the minimised
objective; ``bonus_pairs`` also feeds ``objective_pair_points_fair``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput

# weekday() of the pair's first day → bonus points (Mon=0 … Sun=6).
WEEKDAY_BONUS: dict[int, int] = {4: 3, 5: 2, 6: 1}  # Fri+Sat, Sat+Sun, Sun+Mon


@dataclass(frozen=True)
class BonusPair:
    """A possible Fri+Sat / Sat+Sun / Sun+Mon pair of chosen X for one person."""

    user_id: int
    first: date                       # may be last month's last day
    var: cp_model.IntVar | cp_model.LinearExpr  # 1 when both days are off
    bonus: int


def _x(x, uid: int, d: date) -> cp_model.IntVar:
    return x[(uid, d, AttendanceCode.X)]


def bonus_pairs(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[BonusPair]:
    days = sorted(inp.days)
    found: list[BonusPair] = []
    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        if days and p.prev_codes and p.prev_codes[-1] is AttendanceCode.X:
            first = days[0] - timedelta(days=1)
            bonus = WEEKDAY_BONUS.get(first.weekday(), 0)
            if bonus and days[0] not in pinned:
                found.append(BonusPair(p.user_id, first, _x(x, p.user_id, days[0]), bonus))
        for d, nxt in zip(days, days[1:], strict=False):
            bonus = WEEKDAY_BONUS.get(d.weekday(), 0)
            if not bonus or d in pinned or nxt in pinned:
                continue
            xa, xb = _x(x, p.user_id, d), _x(x, p.user_id, nxt)
            both = model.new_bool_var(f"bonuspair_{p.user_id}_{d.isoformat()}")
            # both == (xa AND xb): exact, because the fairness term reads it.
            model.add(both <= xa)
            model.add(both <= xb)
            model.add(both >= xa + xb - 1)
            found.append(BonusPair(p.user_id, d, both, bonus))
    return found


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    found: list[BonusPair],
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Reward (negative penalty) ``weight`` per base and bonus point."""
    days = sorted(inp.days)
    rewards: list[cp_model.LinearExpr] = [
        -weight * pair.bonus * pair.var for pair in found
    ]
    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        rest_before = bool(p.prev_codes) and not p.prev_codes[-1].is_working
        for i, d in enumerate(days):
            if d in pinned:
                continue  # not chosen; its neighbour earns the point instead
            neighbours: list[cp_model.IntVar | int] = []
            if i > 0:
                neighbours.append(_x(x, p.user_id, days[i - 1]))
            elif rest_before:
                neighbours.append(1)
            if i + 1 < len(days):
                neighbours.append(_x(x, p.user_id, days[i + 1]))
            if not neighbours:
                continue
            paired = model.new_bool_var(f"paired_{p.user_id}_{d.isoformat()}")
            # Rewarded, so upper bounds suffice: off today and next to an off.
            model.add(paired <= _x(x, p.user_id, d))
            model.add(paired <= sum(neighbours))
            rewards.append(-weight * paired)
    return rewards
