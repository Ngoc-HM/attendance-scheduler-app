# DESIGN

- `DESIGN_GUI.md` and `DESIGN_GUI_VN.md` (same rules, English / Vietnamese) are the GUI rules that apply to this Flutter app.
- `DESIGN_IMPLEMENTATION_GUIDE.md` and `UI_STYLE_GUIDE.md` were written for a different Next.js / Tailwind CSS project; they do NOT apply here (no Tailwind classes, `app/globals.css` or React components exist in this repo).
- In code, the rules live in `attendance_scheduler_app/lib/design_system/` (tokens, theme, `Ds*` widgets); see its `README.md`.
- Visual baselines: `attendance_scheduler_app/test/goldens/` (checked by `test/visual_golden_test.dart`).
