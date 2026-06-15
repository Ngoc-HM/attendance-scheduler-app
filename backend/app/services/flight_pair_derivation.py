"""Pure flight-pair counting logic (F-04, §8).

A "pair" = one arrival + one departure of the same route on the same day.
Route pairs (spec §8):
  - FLT 37 (HAN→FRA, arrival) + FLT 36 (FRA→HAN, departure)  = one HAN-FRA pair
  - FLT 31 (SGN→FRA, arrival) + FLT 30 (FRA→SGN, departure)  = one SGN-FRA pair

Derived ``flight_pairs`` = min(2, total matched pairs across both routes).

This module is intentionally side-effect-free so it is easy to unit-test.
"""

from __future__ import annotations

from collections import Counter

# Arrival → departure mapping for known pair routes (spec §8).
# Key = arrival FLT number; value = departure FLT number.
ARRIVAL_TO_DEPARTURE: dict[int, int] = {
    37: 36,  # HAN-FRA pair
    31: 30,  # SGN-FRA pair
}

# Maximum flight pairs per day per spec §5.3 #4.
MAX_PAIRS = 2


def derive_pairs_for_day(flt_numbers: list[int]) -> int:
    """Count matched arrival/departure pairs for a single day.

    Args:
        flt_numbers: All FLT numbers that appear for a given day.
                     Duplicates (e.g. two FLT-37s) do NOT generate extra pairs —
                     each arrival can match at most one departure per route.

    Returns:
        int in {0, 1, 2}: min(matched_route_pairs, 2).
    """
    flt_set = set(flt_numbers)  # each FLT type is counted at most once per day
    matched = sum(
        1
        for arrival, departure in ARRIVAL_TO_DEPARTURE.items()
        if arrival in flt_set and departure in flt_set
    )
    return min(MAX_PAIRS, matched)


def derive_pairs_from_flight_rows(
    day_flights: dict[object, list[int]],
) -> dict[object, int]:
    """Derive ``flight_pairs`` for a collection of days.

    Args:
        day_flights: mapping of day → list of FLT numbers on that day.

    Returns:
        mapping of day → derived flight_pairs (0/1/2).
    """
    return {day: derive_pairs_for_day(flts) for day, flts in day_flights.items()}
