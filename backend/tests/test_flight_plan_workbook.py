"""Pure tests for the monthly flight-plan template and its parser (F-04).

Builds the workbook with ``build_template`` (no DB) and checks the layout the
parser relies on, then feeds edited copies to ``read_plan``.
"""

from __future__ import annotations

import io

import openpyxl
import pytest

from app.core.i18n import MESSAGES, t
from app.services.flight_plan_parser import read_plan
from app.services.flight_plan_template import TemplateRow, build_template

ROWS = [
    TemplateRow("HAN–FRA (37/36)", 37, 36, {1, 15}),
    TemplateRow("SGN–FRA (31/30)", 31, 30, set()),
]
NEW_KEYS = sorted(
    k for k in MESSAGES["en"] if k.startswith(("flight.template_", "flight.plan_"))
)


def _load(raw: bytes) -> openpyxl.Workbook:
    return openpyxl.load_workbook(io.BytesIO(raw))


def _save(wb: openpyxl.Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _template(year: int = 2026, month: int = 11) -> openpyxl.Workbook:
    return _load(build_template(year, month, ROWS))


@pytest.mark.parametrize(
    ("year", "month", "n_days"),
    [(2026, 2, 28), (2028, 2, 29), (2026, 11, 30), (2026, 12, 31)],
)
def test_template_has_exactly_n_day_columns(year: int, month: int, n_days: int):
    ws = _template(year, month).active
    assert ws.title == "FlightPlan"
    assert ws["B1"].value == f"{year}-{month:02d}"
    assert ws["B1"].data_type == "s"
    days = [ws.cell(row=2, column=c).value for c in range(4, ws.max_column + 1)]
    assert days == list(range(1, n_days + 1))
    assert ws.max_column == 3 + n_days


def test_template_layout_texts_and_marks():
    ws = _template().active
    assert ws["A1"].value == t("flight.template_month_label", "en")
    assert ws["D1"].value == t("flight.template_instruction", "en")
    assert [ws["A2"].value, ws["B2"].value, ws["C2"].value] == [
        "Flight preset", "Arrival FLT", "Departure FLT",
    ]
    # 2026-11-01 is a Sunday.
    assert ws["D3"].value == "Sun"
    assert ws["E3"].value == "Mon"
    assert [ws["A4"].value, ws["B4"].value, ws["C4"].value] == ["HAN–FRA (37/36)", 37, 36]
    assert ws["D4"].value == "x" and ws["R4"].value == "x"  # days 1 and 15
    assert ws["E4"].value is None
    assert all(ws.cell(row=5, column=c).value is None for c in range(4, 34))
    assert ws.freeze_panes == "D4"
    assert ws["D2"].font.bold
    assert ws["D4"].fill.fgColor.rgb.endswith("EDEDED")  # Sunday column
    assert ws["E4"].fill.fill_type is None
    assert ws.column_dimensions["A"].width == 26
    assert ws.column_dimensions["D"].width == 4.5
    validation = ws.data_validations.dataValidation[0]
    assert validation.formula1 == '"x,X"'
    assert str(validation.sqref) == "D4:AG5"


def test_template_texts_follow_language(monkeypatch):
    from app.core import i18n

    monkeypatch.setattr(i18n, "_request_language", i18n.ContextVar("lang", default="vi"))
    ws = _template().active
    assert ws["A1"].value == "Tháng"
    assert ws["A2"].value == "Mẫu chuyến bay"
    assert ws["D3"].value == "CN"
    assert ws["E3"].value == "T2"
    assert ws["D1"].value == "Đánh dấu x vào ngày có chuyến. Không sửa cột A–C và 3 hàng đầu."


def test_round_trip_parses_prefilled_marks():
    plan = read_plan(build_template(2026, 11, ROWS))
    assert plan is not None
    assert (plan.year, plan.month, plan.errors) == (2026, 11, [])
    assert [(r.row, r.flt_arr, r.flt_dep, set(r.days)) for r in plan.rows] == [
        (4, 37, 36, {1, 15}),
        (5, 31, 30, set()),
    ]


def test_list_format_is_not_a_plan():
    wb = openpyxl.Workbook()
    wb.active.append(["date", "flt_number", "route", "sta", "std"])
    wb.active.append(["2026-11-01", 37, "HAN-FRA", "06:00", None])
    assert read_plan(_save(wb)) is None


def test_marks_accept_case_spaces_and_numeric_text():
    wb = _template()
    ws = wb.active
    ws["E5"] = " X "
    ws["F5"] = "   "
    ws["B5"] = "31"
    ws["C5"] = 30.0
    ws["AH5"] = "note right of the grid"  # beyond day 30: ignored
    plan = read_plan(_save(wb))
    assert plan is not None and plan.errors == []
    assert set(plan.rows[1].days) == {2}


def test_bad_mark_names_cell_and_echoes_value():
    wb = _template()
    wb.active["H5"] = "yes please"
    wb.active["I5"] = 1
    plan = read_plan(_save(wb))
    assert plan is not None
    assert plan.errors == [
        t("flight.plan_bad_mark", "en").format(cell="H5", value="yes please"),
        t("flight.plan_bad_mark", "en").format(cell="I5", value="1"),
    ]


def test_changed_header_is_one_error():
    wb = _template()
    wb.active.delete_cols(10)  # drops day 7: every later day shifts
    wb.active["H5"] = "bad"
    plan = read_plan(_save(wb))
    assert plan is not None
    assert plan.errors == [t("flight.plan_layout_changed", "en")]


def test_header_with_an_extra_day_is_rejected():
    wb = _template()
    wb.active["AH2"] = 31  # November has 30 days
    plan = read_plan(_save(wb))
    assert plan is not None and plan.errors == [t("flight.plan_layout_changed", "en")]


@pytest.mark.parametrize("value", ["2026-13", "1999-05", "2026-00"])
def test_bad_month_in_b1(value: str):
    wb = _template()
    wb.active["B1"] = value
    plan = read_plan(_save(wb))
    assert plan is not None
    assert plan.errors == [
        t("flight.plan_bad_month", "en").format(value=value, min=2000, max=2100)
    ]


def test_bad_flt_and_duplicate_pair_rows():
    wb = _template()
    ws = wb.active
    ws.append(["copy", 37, 36])  # row 6 repeats row 4
    ws.append(["broken", "abc", 7.5])  # row 7
    ws.append([None] * 10)  # empty: skipped
    plan = read_plan(_save(wb))
    assert plan is not None
    assert plan.errors == [
        t("flight.plan_duplicate_pair", "en").format(row=6, first_row=4, arr=37, dep=36),
        t("flight.plan_row_invalid_flt", "en").format(row=7, col="B", value="abc"),
        t("flight.plan_row_invalid_flt", "en").format(row=7, col="C", value="7.5"),
    ]


@pytest.mark.parametrize("key", NEW_KEYS)
def test_every_new_key_has_vietnamese(key: str):
    assert MESSAGES["vi"].get(key), key
    if key != "flight.template_weekdays":
        assert MESSAGES["vi"][key] != MESSAGES["en"][key], key
    en_params = {p for p in MESSAGES["en"][key].split("{")[1:]}
    vi_params = {p for p in MESSAGES["vi"][key].split("{")[1:]}
    assert {p.split("}")[0] for p in en_params} == {p.split("}")[0] for p in vi_params}


def test_weekday_lists_have_seven_entries():
    for lang in ("en", "vi"):
        assert len(MESSAGES[lang]["flight.template_weekdays"].split(",")) == 7
