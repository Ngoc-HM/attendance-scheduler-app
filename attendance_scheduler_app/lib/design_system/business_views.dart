import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/constants/shift_codes.dart';
import '../i18n/app_localizations.dart';
import 'components.dart';
import 'forms.dart';
import 'states.dart';
import 'tables.dart';
import 'tokens.dart';
import 'view_models.dart';

class DsLoginView extends StatelessWidget {
  const DsLoginView({
    super.key,
    required this.formKey,
    required this.usernameController,
    required this.passwordController,
    required this.title,
    required this.subtitle,
    required this.usernameLabel,
    required this.passwordLabel,
    required this.loginLabel,
    required this.registerLabel,
    required this.requiredMessage,
    required this.languageCode,
    required this.onLanguageChanged,
    required this.onLogin,
    required this.onRegister,
    this.error,
    this.loading = false,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final String title;
  final String subtitle;
  final String usernameLabel;
  final String passwordLabel;
  final String loginLabel;
  final String registerLabel;
  final String requiredMessage;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;
  final VoidCallback onLogin;
  final VoidCallback onRegister;
  final String? error;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsAuthPage(
      title: title,
      subtitle: subtitle,
      languageCode: languageCode,
      onLanguageChanged: onLanguageChanged,
      form: Form(
        key: formKey,
        child: Column(
          children: [
            DsTextField(
              controller: usernameController,
              label: usernameLabel,
              prefixIcon: Icons.person_outline,
              validator: (value) =>
                  (value == null || value.isEmpty) ? requiredMessage : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsTextField(
              controller: passwordController,
              label: passwordLabel,
              prefixIcon: Icons.lock_outline,
              obscureText: true,
              onSubmitted: (_) => onLogin(),
              validator: (value) =>
                  (value == null || value.isEmpty) ? requiredMessage : null,
            ),
            if (error != null) ...[
              const SizedBox(height: DsSpacing.x4),
              DsInlineAlert(
                title: l.text('loginFailedTitle'),
                message: error!,
                tone: DsTone.danger,
              ),
            ],
            const SizedBox(height: DsSpacing.x6),
            DsPrimaryButton(
              label: loginLabel,
              onPressed: onLogin,
              loading: loading,
              expand: true,
            ),
          ],
        ),
      ),
      footer: DsTextAction(
        onDark: true,
        label: registerLabel,
        onPressed: onRegister,
      ),
    );
  }
}

/// Self-registration form. No role field: the admin assigns the role when
/// approving the pending account (F-03).
class DsRegisterView extends StatelessWidget {
  const DsRegisterView({
    super.key,
    required this.formKey,
    required this.usernameController,
    required this.fullNameController,
    required this.passwordController,
    required this.title,
    required this.subtitle,
    required this.usernameLabel,
    required this.fullNameLabel,
    required this.passwordLabel,
    required this.submitLabel,
    required this.backLabel,
    required this.minThreeMessage,
    required this.requiredMessage,
    required this.minSixMessage,
    required this.languageCode,
    required this.onLanguageChanged,
    required this.onSubmit,
    required this.onBack,
    this.error,
    this.loading = false,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController usernameController;
  final TextEditingController fullNameController;
  final TextEditingController passwordController;
  final String title;
  final String subtitle;
  final String usernameLabel;
  final String fullNameLabel;
  final String passwordLabel;
  final String submitLabel;
  final String backLabel;
  final String minThreeMessage;
  final String requiredMessage;
  final String minSixMessage;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;
  final VoidCallback onSubmit;
  final VoidCallback onBack;
  final String? error;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsAuthPage(
      title: title,
      subtitle: subtitle,
      languageCode: languageCode,
      onLanguageChanged: onLanguageChanged,
      form: Form(
        key: formKey,
        child: Column(
          children: [
            DsTextField(
              controller: usernameController,
              label: usernameLabel,
              prefixIcon: Icons.person_outline,
              validator: (value) => (value == null || value.trim().length < 3)
                  ? minThreeMessage
                  : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsTextField(
              controller: fullNameController,
              label: fullNameLabel,
              prefixIcon: Icons.badge_outlined,
              validator: (value) => (value == null || value.trim().isEmpty)
                  ? requiredMessage
                  : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsTextField(
              controller: passwordController,
              label: passwordLabel,
              prefixIcon: Icons.lock_outline,
              obscureText: true,
              validator: (value) =>
                  (value == null || value.length < 6) ? minSixMessage : null,
            ),
            if (error != null) ...[
              const SizedBox(height: DsSpacing.x4),
              DsInlineAlert(
                title: l.text('registrationFailedTitle'),
                message: error!,
                tone: DsTone.danger,
              ),
            ],
            const SizedBox(height: DsSpacing.x6),
            DsPrimaryButton(
              label: submitLabel,
              onPressed: onSubmit,
              loading: loading,
              expand: true,
            ),
          ],
        ),
      ),
      footer: DsTextAction(onDark: true, label: backLabel, onPressed: onBack),
    );
  }
}

class DsScheduleView extends StatelessWidget {
  const DsScheduleView({
    super.key,
    required this.month,
    required this.rows,
    required this.onPreviousMonth,
    required this.onNextMonth,
    this.onGenerate,
    this.onPublish,
    this.flightLabels = const {},
    this.onCellTap,
    this.isRowTappable,
    this.emptyMessage,
  });

  final DateTime month;
  final List<DsRosterRowData> rows;
  final Map<int, String>
  flightLabels; // day-of-month → FLT codes for the roster
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;

  /// Admin roster actions; each button renders only when its callback is set.
  final VoidCallback? onGenerate;
  final VoidCallback? onPublish;

  /// Cell tap: (person row, 0-based day index) — admin edit (F-09) or an
  /// employee's own shift-change request. Null → read-only roster.
  final void Function(DsRosterRowData row, int dayIndex)? onCellTap;

  /// Limits [onCellTap] to the rows it returns true for; the other rows'
  /// cells stay inert (no ripple). Null → every row is tappable.
  final bool Function(DsRosterRowData row)? isRowTappable;

  /// Empty-roster message; defaults to the admin "generate one" hint.
  final String? emptyMessage;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final arrivals = rows.fold<int>(0, (sum, row) => sum + row.arrivals);
    final departures = rows.fold<int>(0, (sum, row) => sum + row.departures);
    final doubleDuty = rows
        .expand((row) => row.shifts)
        .where((shift) => shift == ShiftCode.aD)
        .length;
    final days = rows.isEmpty ? 0 : rows.first.shifts.length;

    return DsPage(
      title: l.text('scheduleTitle'),
      subtitle: l.text('scheduleSubtitle'),
      actions: [
        if (onPublish != null)
          DsSecondaryButton(
            label: l.text('publishSchedule'),
            icon: Icons.publish_outlined,
            onPressed: onPublish,
          ),
        if (onGenerate != null)
          DsPrimaryButton(
            label: l.text('generateSchedule'),
            icon: Icons.auto_awesome_outlined,
            onPressed: onGenerate,
          ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('employees'),
                value: '${rows.length}',
                icon: Icons.people_outline,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('arrDuties'),
                value: '$arrivals',
                icon: Icons.flight_land_outlined,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: l.text('depDuties'),
                value: '$departures',
                icon: Icons.flight_takeoff_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('doubleDuties'),
                value: '$doubleDuty',
                icon: Icons.warning_amber_outlined,
                tone: DsTone.warning,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          // Legend on top (owner 2026-07-01) so codes are explained before the table.
          if (rows.isNotEmpty) ...[
            const _DsShiftLegend(),
            const SizedBox(height: DsSpacing.x4),
          ],
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(DsSpacing.x4),
                  child: Row(
                    children: [
                      Expanded(child: DsSectionHeader(l.text('monthlyRoster'))),
                      DsMonthSwitcher(
                        month: month,
                        onPrevious: onPreviousMonth,
                        onNext: onNextMonth,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                if (rows.isEmpty)
                  _DsRosterEmptyState(
                    title: l.text('scheduleEmptyTitle'),
                    message: emptyMessage ?? l.text('scheduleEmptyMessage'),
                  )
                else
                  _DsRosterTable(
                    month: month,
                    rows: rows,
                    days: days,
                    flightLabels: flightLabels,
                    onCellTap: onCellTap,
                    isRowTappable: isRowTappable,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Monthly roster — TRANSPOSED (owner 2026-07-01): days run DOWN as rows,
/// people run ACROSS as columns. Person columns fill the width evenly; only a
/// very narrow viewport / many people triggers horizontal scroll. A summary
/// block (A / D / off totals per person) closes the table.
class _DsRosterTable extends StatelessWidget {
  const _DsRosterTable({
    required this.month,
    required this.rows,
    required this.days,
    this.flightLabels = const {},
    this.onCellTap,
    this.isRowTappable,
  });

  final DateTime month;
  final List<DsRosterRowData> rows;
  final int days;
  final Map<int, String> flightLabels; // day-of-month → FLT codes
  final void Function(DsRosterRowData row, int dayIndex)? onCellTap;
  final bool Function(DsRosterRowData row)? isRowTappable;

  static const double _dayColW = 40;
  static const double _wdColW = 48;
  static const double _fltColW = 96;
  static const double _personMinW = 60;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return LayoutBuilder(
      builder: (context, constraints) {
        final n = rows.length;
        const hPad =
            DsSpacing.x3 * 2; // each row's horizontal padding (x3 both sides)
        final avail =
            constraints.maxWidth - _dayColW - _wdColW - _fltColW - hPad;
        final fits = n == 0 || n * _personMinW <= avail;
        final personW = fits && n > 0 ? avail / n : _personMinW;

        final table = Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _headerRow(l, personW),
            for (var i = 0; i < days; i++) ...[
              const Divider(height: 1, color: DsColors.border),
              _dayRow(l, i, personW),
            ],
            const Divider(height: 1, color: DsColors.border),
            _summaryRow('A', personW, (r) => '${r.arrivals}'),
            _summaryRow('D', personW, (r) => '${r.departures}'),
            _summaryRow(l.text('off'), personW, (r) => '${r.offDays}'),
          ],
        );

        if (fits) return table;
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: _dayColW + _wdColW + _fltColW + n * personW + hPad,
            child: table,
          ),
        );
      },
    );
  }

  Widget _headerRow(AppLocalizations l, double personW) => Container(
    color: DsColors.surfaceSubtle,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x3,
      vertical: DsSpacing.x2,
    ),
    child: Row(
      children: [
        SizedBox(
          width: _dayColW,
          child: Text(
            l.text('columnDay'),
            textAlign: TextAlign.center,
            style: DsType.tableHeader,
          ),
        ),
        SizedBox(
          width: _wdColW,
          child: Text(
            l.text('columnWeekday'),
            textAlign: TextAlign.center,
            style: DsType.tableHeader,
          ),
        ),
        const SizedBox(
          width: _fltColW,
          child: Text(
            'FLT',
            textAlign: TextAlign.center,
            style: DsType.tableHeader,
          ),
        ),
        for (final row in rows)
          SizedBox(
            width: personW,
            child: Text(
              row.name,
              textAlign: TextAlign.center,
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
              style: const TextStyle(
                fontSize: DsFontSize.footnote,
                fontWeight: FontWeight.w700,
                color: DsColors.textPrimary,
              ),
            ),
          ),
      ],
    ),
  );

  Widget _dayRow(AppLocalizations l, int i, double personW) {
    final date = DateTime(month.year, month.month, i + 1);
    final weekend =
        date.weekday == DateTime.saturday || date.weekday == DateTime.sunday;
    final dayColor = weekend ? DsColors.primary : DsColors.textPrimary;
    // Weekend rows get a soft background tint so Sat/Sun stand out at a
    // glance (owner 2026-07-09) — the roster is transposed: days are rows.
    return Container(
      color: weekend ? DsColors.primarySoft : null,
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x3,
        vertical: 4,
      ),
      child: Row(
        children: [
          SizedBox(
            width: _dayColW,
            child: Text(
              '${i + 1}',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: DsFontSize.footnote,
                fontWeight: FontWeight.w600,
                color: dayColor,
              ),
            ),
          ),
          SizedBox(
            width: _wdColW,
            child: Text(
              l.shortWeekday(date),
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: DsFontSize.caption,
                color: weekend ? DsColors.primary : DsColors.textMuted,
              ),
            ),
          ),
          SizedBox(
            width: _fltColW,
            child: Text(
              flightLabels[i + 1] ?? '',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: DsFontSize.micro,
                fontWeight: FontWeight.w600,
                color: DsColors.textSecondary,
                height: 1.2,
              ),
            ),
          ),
          for (final row in rows)
            SizedBox(
              width: personW,
              child: InkWell(
                onTap:
                    onCellTap != null &&
                        i < row.shifts.length &&
                        (isRowTappable?.call(row) ?? true)
                    ? () => onCellTap!(row, i)
                    : null,
                borderRadius: BorderRadius.circular(6),
                child: Center(
                  child: i < row.shifts.length
                      ? DsShiftBadge(code: row.shifts[i], compact: true)
                      : const Text(
                          '—',
                          style: TextStyle(color: DsColors.textMuted),
                        ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _summaryRow(
    String label,
    double personW,
    String Function(DsRosterRowData) value,
  ) => Container(
    color: DsColors.surfaceSubtle,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x3,
      vertical: DsSpacing.x2,
    ),
    child: Row(
      children: [
        SizedBox(
          width: _dayColW + _wdColW + _fltColW,
          child: Text(label, style: DsType.tableHeader),
        ),
        for (final row in rows)
          SizedBox(
            width: personW,
            child: Center(
              child: Text(
                value(row),
                style: const TextStyle(
                  fontSize: DsFontSize.caption,
                  color: DsColors.textPrimary,
                ),
              ),
            ),
          ),
      ],
    ),
  );
}

/// Horizontally-scrollable day-by-day grid with frozen employee/role columns.
///
/// The left two columns (employee, role) stay visible while the day and summary
/// columns scroll. Header and data rows share exact widths so they never drift.
class _DsDayGrid extends StatelessWidget {
  const _DsDayGrid({
    required this.month,
    required this.trailingHeaders,
    required this.rows,
  });

  final DateTime month;
  final List<String> trailingHeaders;
  final List<_DsDayGridRow> rows;

  static const double _nameW = 150;
  static const double _roleW = 80;
  static const double _dayW = 46;
  static const double _trailW = 72;
  static const double _headerH = 48;
  static const double _rowH = 44;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final daysInMonth = DateTime(month.year, month.month + 1, 0).day;
    final leftWidth = _nameW + _roleW;
    final rightNatural = daysInMonth * _dayW + trailingHeaders.length * _trailW;

    return LayoutBuilder(
      builder: (context, constraints) {
        final rightWidth = math.max(
          rightNatural,
          constraints.maxWidth - leftWidth,
        );

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: leftWidth,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _frozenHeader(l),
                  for (final row in rows) _frozenRow(row),
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SizedBox(
                  width: rightWidth,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _scrollHeader(l, daysInMonth),
                      for (final row in rows) _scrollRow(row, daysInMonth),
                    ],
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _frozenHeader(AppLocalizations l) => Container(
    height: _headerH,
    color: DsColors.surfaceSubtle,
    child: Row(
      children: [
        _frozenCell(
          _nameW,
          _headerText(l.text('employee'), align: TextAlign.left),
        ),
        _frozenCell(_roleW, _headerText(l.role)),
      ],
    ),
  );

  Widget _frozenRow(_DsDayGridRow row) => Container(
    height: _rowH,
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: DsColors.border)),
    ),
    child: Row(
      children: [
        _frozenCell(
          _nameW,
          Text(
            row.name,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        ),
        _frozenCell(_roleW, Center(child: DsBadge(label: row.role))),
      ],
    ),
  );

  Widget _frozenCell(double width, Widget child) => SizedBox(
    width: width,
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x3),
      child: child,
    ),
  );

  Widget _scrollHeader(AppLocalizations l, int daysInMonth) => Container(
    height: _headerH,
    color: DsColors.surfaceSubtle,
    child: Row(
      children: [
        for (var day = 1; day <= daysInMonth; day++)
          _scrollCell(
            _dayW,
            Center(
              child: _DsDayHeader(date: DateTime(month.year, month.month, day)),
            ),
          ),
        for (final h in trailingHeaders) _scrollCell(_trailW, _headerText(h)),
      ],
    ),
  );

  Widget _scrollRow(_DsDayGridRow row, int daysInMonth) => Container(
    height: _rowH,
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: DsColors.border)),
    ),
    child: Row(
      children: [
        for (var i = 0; i < daysInMonth; i++)
          _scrollCell(
            _dayW,
            InkWell(
              onTap: row.onDayTap == null ? null : () => row.onDayTap!(i + 1),
              borderRadius: BorderRadius.circular(6),
              child: _DsDayCell(
                note: i < row.notes.length ? row.notes[i] : null,
                child: i < row.shifts.length
                    ? DsShiftBadge(
                        code: row.shifts[i],
                        compact: true,
                        mark: i < row.marks.length ? row.marks[i] : null,
                      )
                    : const Text(
                        '—',
                        style: TextStyle(color: DsColors.textMuted),
                      ),
              ),
            ),
          ),
        for (final value in row.trailing)
          _scrollCell(
            _trailW,
            Center(
              child: Text(
                value,
                style: const TextStyle(color: DsColors.textPrimary),
              ),
            ),
          ),
      ],
    ),
  );

  Widget _scrollCell(double weight, Widget child) => Expanded(
    flex: weight.round(),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 2),
      child: child,
    ),
  );

  Widget _headerText(String label, {TextAlign align = TextAlign.center}) =>
      Text(label, textAlign: align, style: DsType.tableHeader);
}

class _DsDayGridRow {
  const _DsDayGridRow({
    required this.name,
    required this.role,
    required this.shifts,
    required this.trailing,
    this.notes = const [],
    this.marks = const [],
    this.onDayTap,
  });

  final String name;
  final String role;
  final List<ShiftCode> shifts;
  final List<String> trailing;
  final List<String?> notes;
  final List<DsDayMark?> marks;

  /// Tapping a day cell (day of month, 1-based); null = read-only row.
  final void Function(int day)? onDayTap;
}

/// A day cell: the code badge, the [note] as tooltip.
class _DsDayCell extends StatelessWidget {
  const _DsDayCell({required this.child, this.note});

  final Widget child;
  final String? note;

  @override
  Widget build(BuildContext context) {
    final cell = SizedBox.expand(child: Center(child: child));
    return note == null ? cell : Tooltip(message: note!, child: cell);
  }
}

/// The tint of a [DsDayMark].
Color dsDayMarkColor(DsDayMark mark) =>
    mark == DsDayMark.missing ? DsColors.dayMissing : DsColors.dayAdjusted;

/// Legend of the day tints, shown under a grid that has any.
class DsDayMarkLegend extends StatelessWidget {
  const DsDayMarkLegend({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Wrap(
      spacing: DsSpacing.x4,
      runSpacing: DsSpacing.x2,
      children: [
        for (final (mark, key) in [
          (DsDayMark.missing, 'clockMarkMissing'),
          (DsDayMark.adjusted, 'clockMarkAdjusted'),
        ])
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // The same fill and border the marked badges carry.
              DecoratedBox(
                decoration: BoxDecoration(
                  color: dsDayMarkColor(mark),
                  borderRadius: BorderRadius.circular(DsRadius.small),
                  border: Border.all(
                    color: mark == DsDayMark.missing
                        ? DsColors.danger.withValues(alpha: 0.35)
                        : DsColors.warning.withValues(alpha: 0.45),
                  ),
                ),
                child: const SizedBox(width: 30, height: 22),
              ),
              const SizedBox(width: DsSpacing.x2),
              Text(l.text(key), style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
      ],
    );
  }
}

/// Centered, full-surface placeholder shown when the month has no roster yet —
/// keeps the surface balanced instead of a bunched, content-hugging DataTable.
class _DsRosterEmptyState extends StatelessWidget {
  const _DsRosterEmptyState({required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        vertical: DsSpacing.x10,
        horizontal: DsSpacing.x4,
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.calendar_month_outlined,
              size: 32,
              color: DsColors.textDisabled,
            ),
            const SizedBox(height: DsSpacing.x3),
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: DsSpacing.x2),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: DsColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}

class _DsDayHeader extends StatelessWidget {
  const _DsDayHeader({required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SizedBox(
      width: 30,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('${date.day}'),
          Text(
            l.shortWeekday(date),
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _DsShiftLegend extends StatelessWidget {
  const _DsShiftLegend();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final items = [
      (ShiftCode.a, l.text('arrDuties')),
      (ShiftCode.d, l.text('depDuties')),
      (ShiftCode.aD, l.text('doubleDuty')),
      (ShiftCode.ad, l.text('doubleDutyNoComp')),
      (ShiftCode.oD, l.text('officeDuty')),
      (ShiftCode.t, l.text('training')),
      (ShiftCode.b, l.text('businessTrip')),
      (ShiftCode.x, l.text('off')),
      (ShiftCode.cd, l.text('compensation')),
      (ShiftCode.al, l.text('leave')),
      (ShiftCode.s, l.text('sick')),
    ];
    return Wrap(
      spacing: DsSpacing.x4,
      runSpacing: DsSpacing.x2,
      children: [
        for (final item in items)
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              DsShiftBadge(code: item.$1, compact: true),
              const SizedBox(width: DsSpacing.x2),
              Text(item.$2, style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
      ],
    );
  }
}

class DsFlightsView extends StatelessWidget {
  const DsFlightsView({
    super.key,
    required this.month,
    required this.rows,
    required this.onPreviousMonth,
    required this.onNextMonth,
    required this.onAdd,
    this.onManagePresets,
    this.onImportExcel,
    this.onDownloadTemplate,
  });

  final DateTime month;
  final List<DsFlightRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onAdd;

  /// If non-null an admin "Manage presets" toolbar action is shown.
  final VoidCallback? onManagePresets;

  /// If non-null an admin "Import Excel" toolbar action is shown (F-04).
  final VoidCallback? onImportExcel;

  /// If non-null an admin "Download template" toolbar action is shown, just
  /// before "Import Excel": the month's blank plan to fill in and import.
  final VoidCallback? onDownloadTemplate;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final pairCount = rows.fold<int>(
      0,
      (total, row) => total + row.flightPairs,
    );
    final busyDays = rows.where((row) => row.flightPairs == 2).length;
    return DsPage(
      title: l.text('flightsTitle'),
      subtitle: l.text('flightsSubtitle'),
      actions: [
        if (onDownloadTemplate != null)
          DsSecondaryButton(
            label: l.text('downloadFlightTemplate'),
            icon: Icons.download_outlined,
            onPressed: onDownloadTemplate!,
          ),
        if (onImportExcel != null)
          DsSecondaryButton(
            label: l.text('importExcel'),
            icon: Icons.upload_file_outlined,
            onPressed: onImportExcel!,
          ),
        if (onManagePresets != null)
          DsSecondaryButton(
            label: l.text('managePresets'),
            icon: Icons.tune_outlined,
            onPressed: onManagePresets!,
          ),
        DsPrimaryButton(
          label: l.text('addFlight'),
          icon: Icons.add,
          onPressed: onAdd,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('flightDays'),
                value: '${rows.length}',
                icon: Icons.calendar_today_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('flightPairs'),
                value: '$pairCount',
                icon: Icons.sync_alt_outlined,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: l.text('twoPairDays'),
                value: '$busyDays',
                icon: Icons.warning_amber_outlined,
                tone: DsTone.warning,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(DsSpacing.x4),
                  child: Row(
                    children: [
                      Expanded(child: DsSectionHeader(l.text('flightPlan'))),
                      DsMonthSwitcher(
                        month: month,
                        onPrevious: onPreviousMonth,
                        onNext: onNextMonth,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                _FlightsTable(rows: rows),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Full-width, evenly distributed flights table.
class _FlightsTable extends StatelessWidget {
  const _FlightsTable({required this.rows});

  final List<DsFlightRowData> rows;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    // date | pairs | flights | STA | STD | status
    final columns = [
      DsTableColumn(header: l.text('date'), flex: 2),
      DsTableColumn(header: l.text('pairs'), flex: 1),
      DsTableColumn(header: l.text('flights'), flex: 4),
      const DsTableColumn(header: 'STA', flex: 2),
      const DsTableColumn(header: 'STD', flex: 2),
      DsTableColumn(header: l.status, flex: 2),
    ];

    return DsDataTable(
      columns: columns,
      rows: [
        for (final row in rows)
          [
            Text(
              l.flightDate(row.date),
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text('${row.flightPairs}', style: DsType.tableCell),
            Text(
              row.flights,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text(row.arrival, style: DsType.tableCell),
            Text(row.departure, style: DsType.tableCell),
            DsBadge(
              label: l.statusLabel(row.status),
              tone: row.status == DsFlightRowData.statusComplete
                  ? DsTone.success
                  : DsTone.warning,
            ),
          ],
      ],
    );
  }
}

class DsUploadZone extends StatelessWidget {
  const DsUploadZone({
    super.key,
    required this.title,
    required this.hint,
    required this.buttonLabel,
    required this.onPressed,
  });

  final String title;
  final String hint;
  final String buttonLabel;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(DsSpacing.x6),
      decoration: BoxDecoration(
        color: DsColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(DsRadius.large),
        border: Border.all(
          color: DsColors.borderStrong,
          width: 2,
          strokeAlign: BorderSide.strokeAlignInside,
        ),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.upload_file_outlined,
            size: 28,
            color: DsColors.primary,
          ),
          const SizedBox(width: DsSpacing.x4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: DsSpacing.x1),
                Text(hint, style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          DsSecondaryButton(label: buttonLabel, onPressed: onPressed),
        ],
      ),
    );
  }
}

class DsLeavesView extends StatelessWidget {
  const DsLeavesView({
    super.key,
    required this.rows,
    required this.onMonthlyRequest,
    required this.onAnnualRequest,
    this.onRefresh,
    this.onApprove,
    this.onReject,
    this.onRevoke,
    this.registrationOpen = true,
    this.closesOnDay,
    required this.compDays,
    this.annualLeaveRemaining,
  });

  final List<DsLeaveRowData> rows;
  final VoidCallback onMonthlyRequest;
  final VoidCallback onAnnualRequest;

  /// Reloads the requests; null → no refresh button.
  final VoidCallback? onRefresh;

  /// Null → viewer cannot decide (employee): the actions column is hidden.
  final ValueChanged<int>? onApprove;
  final ValueChanged<int>? onReject;

  /// Admin: revoke a previously APPROVED leave (owner 2026-07-17).
  final ValueChanged<int>? onRevoke;

  /// Whether the monthly registration window (day 1–[closesOnDay]) is
  /// currently open — drives the banner so it never claims "open" after it
  /// closed.
  final bool registrationOpen;

  /// Last day of month M on which leave for M+1 may be registered (backend
  /// `closes_on_day`). Null while unknown → no subtitle rather than a guess.
  final int? closesOnDay;

  /// "Comp days" card value. Given explicitly: summing [rows] would show 0
  /// for someone with no requests and count a person once per request.
  final int compDays;

  /// "Annual leave left" card value (quota minus approved days this year).
  /// Null → no card (admin view, or the balance could not be loaded);
  /// negative once leave was approved past the quota.
  final int? annualLeaveRemaining;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final pending = rows.where((row) => row.status == 'Pending').length;
    final approved = rows.where((row) => row.status == 'Approved').length;
    final day = closesOnDay;
    final annualLeft = annualLeaveRemaining;
    return DsPage(
      title: l.text('leaveRequests'),
      subtitle: day == null ? null : l.leaveSubtitle(day),
      actions: [
        if (onRefresh != null)
          DsSecondaryButton(
            label: l.refresh,
            icon: Icons.refresh,
            onPressed: onRefresh,
          ),
        DsSecondaryButton(
          label: l.text('requestAnnualLeave'),
          icon: Icons.calendar_month_outlined,
          onPressed: onAnnualRequest,
        ),
        DsPrimaryButton(
          label: l.text('requestMonthlyLeave'),
          icon: Icons.add,
          onPressed: onMonthlyRequest,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('pending'),
                value: '$pending',
                icon: Icons.schedule_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: l.text('approved'),
                value: '$approved',
                icon: Icons.check_circle_outline,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: l.text('compDays'),
                value: '$compDays',
                icon: Icons.event_repeat_outlined,
                tone: DsTone.primary,
              ),
              if (annualLeft != null)
                DsMetricCard(
                  label: l.text('annualLeaveRemaining'),
                  value: '$annualLeft',
                  icon: Icons.beach_access_outlined,
                  tone: annualLeft < 0 ? DsTone.danger : DsTone.primary,
                ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          DsInlineAlert(
            title: registrationOpen
                ? l.text('registrationOpen')
                : l.text('registrationClosed'),
            message: registrationOpen
                ? l.text('shortLeaveMessage')
                : l.text('registrationClosedMessage'),
            tone: registrationOpen ? DsTone.primary : DsTone.warning,
          ),
          const SizedBox(height: DsSpacing.x6),
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(DsSpacing.x4),
                  child: DsSectionHeader(l.text('requests')),
                ),
                const Divider(height: 1),
                _LeavesTable(
                  rows: rows,
                  onApprove: onApprove,
                  onReject: onReject,
                  onRevoke: onRevoke,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Full-width, evenly distributed leaves table.
class _LeavesTable extends StatelessWidget {
  const _LeavesTable({
    required this.rows,
    this.onApprove,
    this.onReject,
    this.onRevoke,
  });

  final List<DsLeaveRowData> rows;

  /// Null → decisions hidden entirely (employee view had no-op buttons that
  /// looked like a permissions hole).
  final ValueChanged<int>? onApprove;
  final ValueChanged<int>? onReject;
  final ValueChanged<int>? onRevoke;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final canDecide = onApprove != null && onReject != null;
    // employee | role | type | dates | days | carry | status | actions(admin)
    final columns = [
      DsTableColumn(header: l.text('employee'), flex: 3),
      DsTableColumn(header: l.role, flex: 2),
      DsTableColumn(header: l.text('type'), flex: 3),
      DsTableColumn(header: l.text('dates'), flex: 3),
      DsTableColumn(header: l.text('days'), flex: 1),
      DsTableColumn(header: l.text('carry'), flex: 1),
      DsTableColumn(header: l.status, flex: 2),
      if (canDecide) DsTableColumn(header: l.actions, flex: 4),
    ];

    final table = DsDataTable(
      columns: columns,
      rows: [
        for (var index = 0; index < rows.length; index++)
          [
            Text(
              rows[index].employee,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            DsBadge(label: rows[index].role),
            Text(
              l.leaveTypeLabel(rows[index].type),
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              rows[index].range,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text('${rows[index].days}', style: DsType.tableCell),
            Text('${rows[index].carryComp}', style: DsType.tableCell),
            DsBadge(
              label: l.statusLabel(rows[index].status),
              tone: switch (rows[index].status) {
                'Approved' => DsTone.success,
                'Rejected' => DsTone.danger,
                _ => DsTone.warning,
              },
            ),
            if (canDecide)
              switch (rows[index].status) {
                'Pending' => Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DsTextAction(
                      label: l.approve,
                      icon: Icons.check,
                      tone: DsTone.success,
                      onPressed: () => onApprove!(index),
                    ),
                    DsTextAction(
                      label: l.text('reject'),
                      icon: Icons.close,
                      tone: DsTone.danger,
                      onPressed: () => onReject!(index),
                    ),
                  ],
                ),
                'Approved' when onRevoke != null => DsTextAction(
                  label: l.text('revokeApproval'),
                  icon: Icons.undo,
                  tone: DsTone.danger,
                  onPressed: () => onRevoke!(index),
                ),
                _ => const SizedBox.shrink(),
              },
          ],
      ],
      // Staffing risk sits under the row's cells, full width, so the columns
      // keep their widths at the minimum window; rows without it unchanged.
      rowFooters: [
        for (final row in rows)
          row.staffingWarnings.isEmpty
              ? null
              : _LeaveStaffingWarnings(lines: row.staffingWarnings),
      ],
    );

    // Fix cứng khung giao diện: bảng có chiều rộng tối thiểu cố định; nếu màn
    // hẹp hơn thì cuộn ngang thay vì bị overflow (DsDataTable dùng Expanded
    // nên cần đặt trong SizedBox cố định chiều rộng khi cuộn).
    const employeeMinWidth = 760.0;
    const adminMinWidth = 1000.0;
    final minWidth = canDecide ? adminMinWidth : employeeMinWidth;

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= minWidth) {
          return table;
        }
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(width: minWidth, child: table),
        );
      },
    );
  }
}

/// Flight-staffing risk of one leave request, kept on its row (owner
/// 2026-11-10: the approval toast disappears, the risk must not). Lines come
/// translated from the backend, one per day or shift, as plain text.
class _LeaveStaffingWarnings extends StatelessWidget {
  const _LeaveStaffingWarnings({required this.lines});

  final List<String> lines;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(DsTone.warning);
    final style = DsType.tableCell.copyWith(
      fontSize: DsFontSize.footnote,
      color: colors.foreground,
    );
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x3,
        vertical: DsSpacing.x2,
      ),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(DsRadius.small),
        border: Border.all(color: colors.foreground.withValues(alpha: 0.18)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            Icons.warning_amber_outlined,
            color: colors.foreground,
            size: DsFontSize.bodyLarge,
          ),
          const SizedBox(width: DsSpacing.x2),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [for (final line in lines) Text(line, style: style)],
            ),
          ),
        ],
      ),
    );
  }
}

class DsAttendanceView extends StatelessWidget {
  const DsAttendanceView({
    super.key,
    required this.month,
    required this.rows,
    required this.onPreviousMonth,
    required this.onNextMonth,
    this.onDayTap,
    this.onUpdate,
    this.onHolidays,
    this.onCloseMonth,
  });

  final DateTime month;
  final List<DsAttendanceRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;

  /// Admin toolbar actions — each button is shown only when its callback is
  /// non-null, so an employee viewing their own month sees none of them:
  /// record attendance / sick cover, public holidays, close month (F-14).
  /// Admin: a day cell was tapped (row, day of month) — edit that
  /// person's day in place.
  final void Function(DsAttendanceRowData row, int day)? onDayTap;
  final VoidCallback? onUpdate;
  final VoidCallback? onHolidays;
  final VoidCallback? onCloseMonth;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final workdays = rows.fold<int>(0, (sum, row) => sum + row.workdays);
    final absences = rows.fold<int>(0, (sum, row) => sum + row.absences);
    final sickDays = rows
        .expand((row) => row.shifts)
        .where((shift) => shift == ShiftCode.s)
        .length;
    return DsPage(
      title: l.text('attendanceTitle'),
      subtitle: l.text('attendanceSubtitle'),
      actions: [
        if (onCloseMonth != null)
          DsSecondaryButton(
            label: l.text('closeMonth'),
            icon: Icons.lock_clock_outlined,
            onPressed: onCloseMonth!,
          ),
        if (onHolidays != null)
          DsSecondaryButton(
            label: l.text('publicHolidays'),
            icon: Icons.event_outlined,
            onPressed: onHolidays,
          ),
        if (onUpdate != null)
          DsPrimaryButton(
            label: l.text('updateAttendance'),
            icon: Icons.edit_outlined,
            onPressed: onUpdate,
          ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('workdays'),
                value: '$workdays',
                icon: Icons.work_outline,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('absences'),
                value: '$absences',
                icon: Icons.event_busy_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: l.text('sickDays'),
                value: '$sickDays',
                icon: Icons.medical_information_outlined,
                tone: DsTone.danger,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(DsSpacing.x4),
                  child: Row(
                    children: [
                      Expanded(
                        child: DsSectionHeader(l.text('attendanceBoard')),
                      ),
                      DsMonthSwitcher(
                        month: month,
                        onPrevious: onPreviousMonth,
                        onNext: onNextMonth,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                if (rows.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      vertical: DsSpacing.x10,
                      horizontal: DsSpacing.x4,
                    ),
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.event_note_outlined,
                            size: 32,
                            color: DsColors.textDisabled,
                          ),
                          const SizedBox(height: DsSpacing.x3),
                          Text(
                            l.text('attendanceEmptyTitle'),
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: DsSpacing.x2),
                          Text(
                            // The admin hint points at "Update attendance",
                            // which a read-only (employee) view does not have.
                            l.text(
                              onUpdate != null
                                  ? 'attendanceEmptyMessage'
                                  : 'myAttendanceEmptyMessage',
                            ),
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: DsColors.textMuted),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  _DsDayGrid(
                    month: month,
                    trailingHeaders: [l.text('work'), l.text('absent')],
                    rows: [
                      for (final row in rows)
                        _DsDayGridRow(
                          name: row.name,
                          role: row.role,
                          shifts: row.shifts,
                          trailing: ['${row.workdays}', '${row.absences}'],
                          notes: row.dayNotes,
                          marks: row.dayMarks,
                          onDayTap: onDayTap == null
                              ? null
                              : (day) => onDayTap!(row, day),
                        ),
                    ],
                  ),
              ],
            ),
          ),
          if (rows.isNotEmpty) ...[
            const SizedBox(height: DsSpacing.x4),
            const _DsShiftLegend(),
          ],
          if (rows.any((r) => r.dayMarks.any((m) => m != null))) ...[
            const SizedBox(height: DsSpacing.x2),
            const DsDayMarkLegend(),
          ],
        ],
      ),
    );
  }
}

class DsReportsView extends StatelessWidget {
  const DsReportsView({
    super.key,
    required this.rows,
    required this.onExport,
    required this.onDownload,
    this.filters = const [],
    this.exporting = false,
  });

  final List<DsReportRowData> rows;

  /// Export the period and format chosen in [filters].
  final VoidCallback onExport;
  final ValueChanged<int> onDownload;

  /// Period / format selectors shown above the cards (D5: they used to hide
  /// behind a row's download action).
  final List<Widget> filters;

  /// An export is running: the export button shows progress.
  final bool exporting;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsPage(
      title: l.text('reportsTitle'),
      subtitle: l.text('reportsSubtitle'),
      actions: [
        DsPrimaryButton(
          label: l.text('exportReport'),
          icon: Icons.download_outlined,
          loading: exporting,
          onPressed: onExport,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (filters.isNotEmpty) ...[
            DsSurface(
              child: Wrap(
                spacing: DsSpacing.x4,
                runSpacing: DsSpacing.x3,
                children: [
                  for (final filter in filters)
                    SizedBox(width: 200, child: filter),
                ],
              ),
            ),
            const SizedBox(height: DsSpacing.x6),
          ],
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(DsSpacing.x4),
                  child: DsSectionHeader(l.text('recentExports')),
                ),
                const Divider(height: 1),
                if (rows.isEmpty)
                  Padding(
                    padding: const EdgeInsets.all(DsSpacing.x4),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        l.text('noExportsYet'),
                        style: const TextStyle(color: DsColors.textMuted),
                      ),
                    ),
                  )
                else
                  _ReportsTable(rows: rows, onDownload: onDownload),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Full-width, evenly distributed reports table.
class _ReportsTable extends StatelessWidget {
  const _ReportsTable({required this.rows, required this.onDownload});

  final List<DsReportRowData> rows;
  final ValueChanged<int> onDownload;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    // report name | period | updated | status | action
    final columns = [
      DsTableColumn(header: l.text('report'), flex: 4),
      DsTableColumn(header: l.text('period'), flex: 2),
      DsTableColumn(header: l.text('updated'), flex: 2),
      DsTableColumn(header: l.status, flex: 2),
      DsTableColumn(header: l.text('action'), flex: 2),
    ];

    return DsDataTable(
      columns: columns,
      rows: [
        for (var index = 0; index < rows.length; index++)
          [
            Text(
              rows[index].name,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              rows[index].period,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              rows[index].updated,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            DsBadge(
              label: l.statusLabel(rows[index].status),
              tone: DsTone.success,
              icon: Icons.check_circle_outline,
            ),
            DsTextAction(
              label: l.text('download'),
              icon: Icons.download_outlined,
              onPressed: () => onDownload(index),
            ),
          ],
      ],
    );
  }
}

class DsUsersView extends StatelessWidget {
  const DsUsersView({
    super.key,
    required this.users,
    required this.loading,
    required this.onRefresh,
    required this.onCreate,
    required this.onApprove,
    required this.onDisable,
    required this.onEnable,
    required this.onChangeRole,
    this.onDelete,
    this.onEditQuota,
    this.error,
  });

  final List<DsUserRowData> users;
  final bool loading;
  final String? error;
  final VoidCallback onRefresh;
  final VoidCallback onCreate;
  final ValueChanged<int> onApprove;
  final ValueChanged<int> onDisable;
  final ValueChanged<int> onEnable;

  /// Change a user's role (e.g. promote to admin `M`); the backend reassigns a
  /// matching code. Called with the user id and the new role letter.
  final void Function(int id, String role) onChangeRole;

  /// Hard-delete (with cascade) — optional so callers without permission can
  /// omit it and the action button is hidden.
  final ValueChanged<int>? onDelete;

  /// Edit the user's annual leave quota (D4); null hides the action.
  final ValueChanged<int>? onEditQuota;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final active = users.where((user) => user.status == 'active').length;
    final pending = users.where((user) => user.status == 'pending').length;
    final fixed = users.where((user) => user.role.startsWith('A')).length;
    return DsPage(
      title: l.text('usersTitle'),
      subtitle: l.text('usersSubtitle'),
      actions: [
        DsSecondaryButton(
          label: l.refresh,
          icon: Icons.refresh,
          onPressed: onRefresh,
        ),
        DsPrimaryButton(
          label: l.createUser,
          icon: Icons.person_add_outlined,
          onPressed: onCreate,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('active'),
                value: '$active',
                icon: Icons.check_circle_outline,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: l.text('pending'),
                value: '$pending',
                icon: Icons.schedule_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: l.text('fixedTeam'),
                value: '$fixed',
                icon: Icons.lock_outline,
                tone: DsTone.primary,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          if (loading)
            const DsLoadingState()
          else if (error != null)
            DsErrorState(
              title: l.text('couldNotLoadUsers'),
              message: error!,
              actionLabel: l.text('retry'),
              onRetry: onRefresh,
            )
          else if (users.isEmpty)
            DsEmptyState(
              icon: Icons.people_outline,
              title: l.noUsers,
              message: l.text('createFirstAccount'),
              actionLabel: l.createUser,
              onAction: onCreate,
            )
          else
            DsSurface(
              padding: EdgeInsets.zero,
              child: _UsersTable(
                users: users,
                onApprove: onApprove,
                onDisable: onDisable,
                onEnable: onEnable,
                onChangeRole: onChangeRole,
                onDelete: onDelete,
                onEditQuota: onEditQuota,
              ),
            ),
        ],
      ),
    );
  }
}

/// Full-width, evenly distributed users table (replaces a content-hugging
/// DataTable so columns stay balanced and aligned across the surface).
class _UsersTable extends StatelessWidget {
  const _UsersTable({
    required this.users,
    required this.onApprove,
    required this.onDisable,
    required this.onEnable,
    required this.onChangeRole,
    this.onDelete,
    this.onEditQuota,
  });

  final List<DsUserRowData> users;
  final ValueChanged<int> onApprove;
  final ValueChanged<int> onDisable;
  final ValueChanged<int> onEnable;
  final void Function(int id, String role) onChangeRole;
  final ValueChanged<int>? onDelete;
  final ValueChanged<int>? onEditQuota;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    // username | fullName | role | code | status | actions
    final columns = [
      DsTableColumn(header: l.username, flex: 2),
      DsTableColumn(header: l.fullName, flex: 3),
      DsTableColumn(header: l.role, flex: 2),
      DsTableColumn(header: l.text('clockCode'), flex: 2),
      DsTableColumn(header: l.status, flex: 2),
      DsTableColumn(header: l.actions, flex: 3),
    ];

    return DsDataTable(
      columns: columns,
      rows: [
        for (final user in users)
          [
            Text(
              user.username,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              user.fullName,
              style: DsType.tableCell,
              overflow: TextOverflow.ellipsis,
            ),
            DsBadge(label: l.roleLabel(user.role)),
            user.code.isEmpty
                ? const SizedBox.shrink()
                : DsBadge(label: user.code, tone: DsTone.neutral),
            DsBadge(
              label: l.statusLabel(user.status),
              tone: switch (user.status) {
                'active' => DsTone.success,
                'pending' => DsTone.warning,
                _ => DsTone.neutral,
              },
            ),
            // Actions cell: the status action(s) — approve / change-role +
            // disable / enable — then edit quota and delete; wraps if cramped.
            Wrap(
              spacing: DsSpacing.x2,
              runSpacing: DsSpacing.x1,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                ...switch (user.status) {
                  'pending' => [
                    _ActionButton(
                      label: l.approve,
                      tone: DsTone.success,
                      onPressed: () => onApprove(user.id),
                    ),
                  ],
                  // Active users can be disabled AND have their role changed
                  // (e.g. promoted to admin `M`).
                  'active' => [
                    _RoleChangeMenu(
                      currentRole: user.role,
                      onSelected: (role) => onChangeRole(user.id, role),
                    ),
                    _ActionButton(
                      label: l.disable,
                      tone: DsTone.danger,
                      onPressed: () => onDisable(user.id),
                    ),
                  ],
                  // Disabled (or any other non-pending, non-active status).
                  _ => [
                    _ActionButton(
                      label: l.enable,
                      tone: DsTone.primary,
                      onPressed: () => onEnable(user.id),
                    ),
                  ],
                },
                // Every status: a pending account can be set up before
                // approval, a disabled one before re-enabling.
                if (onEditQuota != null)
                  _ActionButton(
                    label: l.text('editAnnualLeaveQuota'),
                    tone: DsTone.primary,
                    onPressed: () => onEditQuota!(user.id),
                  ),
                if (onDelete != null)
                  _ActionButton(
                    label: l.text('delete'),
                    tone: DsTone.danger,
                    onPressed: () => onDelete!(user.id),
                  ),
              ],
            ),
          ],
      ],
    );
  }
}

/// Compact, clearly-bordered tonal button for a single row action (approve /
/// disable / enable). Text-only — no leading icon — so the actions column stays
/// clean and the tap target reads unmistakably as a button.
class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.onPressed,
    this.tone = DsTone.primary,
  });

  final String label;
  final VoidCallback onPressed;
  final DsTone tone;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(tone);
    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(
        backgroundColor: colors.background,
        foregroundColor: colors.foreground,
        padding: const EdgeInsets.symmetric(
          horizontal: DsSpacing.x3,
          vertical: DsSpacing.x2,
        ),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        textStyle: const TextStyle(
          fontSize: DsFontSize.footnote,
          fontWeight: FontWeight.w600,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DsRadius.medium),
          side: BorderSide(color: colors.foreground.withValues(alpha: 0.30)),
        ),
      ),
      child: Text(label),
    );
  }
}

/// Bordered button that opens a small menu to switch a user's role between
/// M / T / A. Current role is checked + disabled; selecting another fires
/// [onSelected] with the new role letter (the caller confirms + persists).
class _RoleChangeMenu extends StatelessWidget {
  const _RoleChangeMenu({required this.currentRole, required this.onSelected});

  final String currentRole;
  final ValueChanged<String> onSelected;

  static const _roles = ['M', 'T', 'A', 'F'];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return PopupMenuButton<String>(
      tooltip: l.text('changeRole'),
      onSelected: onSelected,
      position: PopupMenuPosition.under,
      itemBuilder: (_) => [
        for (final role in _roles)
          PopupMenuItem<String>(
            value: role,
            enabled: role != currentRole,
            child: Row(
              children: [
                if (role == currentRole) ...[
                  const Icon(Icons.check, size: 16, color: DsColors.primary),
                  const SizedBox(width: DsSpacing.x2),
                ],
                Text(l.roleLabel(role)),
              ],
            ),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.fromLTRB(
          DsSpacing.x3,
          DsSpacing.x2,
          DsSpacing.x1,
          DsSpacing.x2,
        ),
        decoration: BoxDecoration(
          color: DsColors.primarySoft,
          borderRadius: BorderRadius.circular(DsRadius.medium),
          border: Border.all(
            color: DsColors.primaryHover.withValues(alpha: 0.30),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              l.text('changeRole'),
              style: const TextStyle(
                fontSize: DsFontSize.footnote,
                fontWeight: FontWeight.w600,
                color: DsColors.primaryHover,
              ),
            ),
            const Icon(
              Icons.arrow_drop_down,
              size: 18,
              color: DsColors.primaryHover,
            ),
          ],
        ),
      ),
    );
  }
}

class DsCreateUserDialog<T> extends StatelessWidget {
  const DsCreateUserDialog({
    super.key,
    required this.formKey,
    required this.usernameController,
    required this.fullNameController,
    required this.passwordController,
    required this.role,
    required this.roleOptions,
    required this.onRoleChanged,
    required this.onCancel,
    required this.onSubmit,
    required this.usernameLabel,
    required this.fullNameLabel,
    required this.passwordLabel,
    required this.roleLabel,
    required this.cancelLabel,
    required this.submitLabel,
    required this.minThreeMessage,
    required this.requiredMessage,
    required this.minSixMessage,
    required this.quotaController,
    required this.quotaLabel,
    required this.quotaHint,
    required this.quotaInvalidMessage,
    this.error,
    this.loading = false,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController usernameController;
  final TextEditingController fullNameController;
  final TextEditingController passwordController;

  /// Optional annual leave quota in days (0–365); empty keeps the server
  /// default.
  final TextEditingController quotaController;
  final String quotaLabel;
  final String quotaHint;
  final String quotaInvalidMessage;
  final T role;
  final List<DsSelectOption<T>> roleOptions;
  final ValueChanged<T> onRoleChanged;
  final VoidCallback onCancel;
  final VoidCallback onSubmit;
  final String usernameLabel;
  final String fullNameLabel;
  final String passwordLabel;
  final String roleLabel;
  final String cancelLabel;
  final String submitLabel;
  final String minThreeMessage;
  final String requiredMessage;
  final String minSixMessage;
  final String? error;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsFormDialog(
      title: l.createUser,
      content: Form(
        key: formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DsTextField(
              controller: usernameController,
              label: usernameLabel,
              validator: (value) => (value == null || value.trim().length < 3)
                  ? minThreeMessage
                  : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsTextField(
              controller: fullNameController,
              label: fullNameLabel,
              validator: (value) => (value == null || value.trim().isEmpty)
                  ? requiredMessage
                  : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsTextField(
              controller: passwordController,
              label: passwordLabel,
              obscureText: true,
              validator: (value) =>
                  (value == null || value.length < 6) ? minSixMessage : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            DsSelectField<T>(
              label: roleLabel,
              value: role,
              items: [
                for (final option in roleOptions)
                  DropdownMenuItem(
                    value: option.value,
                    child: Text(option.label),
                  ),
              ],
              onChanged: (value) {
                if (value != null) onRoleChanged(value);
              },
            ),
            const SizedBox(height: DsSpacing.x4),
            DsAnnualLeaveQuotaField(
              controller: quotaController,
              label: quotaLabel,
              hint: quotaHint,
              invalidMessage: quotaInvalidMessage,
              optional: true,
            ),
            if (error != null) ...[
              const SizedBox(height: DsSpacing.x4),
              DsInlineAlert(
                title: l.text('couldNotCreateUser'),
                message: error!,
                tone: DsTone.danger,
              ),
            ],
          ],
        ),
      ),
      actions: [
        DsTextAction(label: cancelLabel, onPressed: onCancel),
        DsPrimaryButton(
          label: submitLabel,
          onPressed: onSubmit,
          loading: loading,
        ),
      ],
    );
  }
}

/// Annual leave quota input: whole days per calendar year, 0–365 (owner
/// decision D4). Empty passes validation only when [optional] (the server
/// default then applies).
class DsAnnualLeaveQuotaField extends StatelessWidget {
  const DsAnnualLeaveQuotaField({
    super.key,
    required this.controller,
    required this.label,
    required this.invalidMessage,
    this.hint,
    this.optional = false,
  });

  final TextEditingController controller;
  final String label;
  final String invalidMessage;
  final String? hint;
  final bool optional;

  @override
  Widget build(BuildContext context) {
    return DsTextField(
      controller: controller,
      label: label,
      hint: hint,
      keyboardType: TextInputType.number,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      validator: (value) {
        final text = value?.trim() ?? '';
        if (text.isEmpty) return optional ? null : invalidMessage;
        final days = int.tryParse(text);
        return (days == null || days < 0 || days > 365) ? invalidMessage : null;
      },
    );
  }
}

class DsLeaveRequestDialog extends StatelessWidget {
  const DsLeaveRequestDialog({
    super.key,
    required this.onCancel,
    required this.onSubmit,
  });

  final VoidCallback onCancel;
  final VoidCallback onSubmit;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsFormDialog(
      title: l.text('requestLeave'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            decoration: InputDecoration(
              labelText: l.text('leaveType'),
              prefixIcon: const Icon(Icons.event_available_outlined, size: 20),
            ),
          ),
          const SizedBox(height: DsSpacing.x4),
          TextField(
            decoration: InputDecoration(
              labelText: l.text('dateRange'),
              prefixIcon: const Icon(Icons.date_range_outlined, size: 20),
            ),
          ),
          const SizedBox(height: DsSpacing.x4),
          TextField(
            maxLines: 3,
            decoration: InputDecoration(labelText: l.text('note')),
          ),
        ],
      ),
      actions: [
        DsTextAction(label: l.cancel, onPressed: onCancel),
        DsPrimaryButton(label: l.text('submitRequest'), onPressed: onSubmit),
      ],
    );
  }
}
