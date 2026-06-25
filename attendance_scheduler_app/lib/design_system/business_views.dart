import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../core/constants/shift_codes.dart';
import '../i18n/app_localizations.dart';
import 'components.dart';
import 'forms.dart';
import 'states.dart';
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
      footer: DsTextAction(label: registerLabel, onPressed: onRegister),
    );
  }
}

class DsRegisterView<T> extends StatelessWidget {
  const DsRegisterView({
    super.key,
    required this.formKey,
    required this.usernameController,
    required this.fullNameController,
    required this.passwordController,
    required this.role,
    required this.roleOptions,
    required this.title,
    required this.subtitle,
    required this.usernameLabel,
    required this.fullNameLabel,
    required this.passwordLabel,
    required this.roleLabel,
    required this.submitLabel,
    required this.backLabel,
    required this.minThreeMessage,
    required this.requiredMessage,
    required this.minSixMessage,
    required this.languageCode,
    required this.onLanguageChanged,
    required this.onRoleChanged,
    required this.onSubmit,
    required this.onBack,
    this.error,
    this.loading = false,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController usernameController;
  final TextEditingController fullNameController;
  final TextEditingController passwordController;
  final T role;
  final List<DsSelectOption<T>> roleOptions;
  final String title;
  final String subtitle;
  final String usernameLabel;
  final String fullNameLabel;
  final String passwordLabel;
  final String roleLabel;
  final String submitLabel;
  final String backLabel;
  final String minThreeMessage;
  final String requiredMessage;
  final String minSixMessage;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;
  final ValueChanged<T> onRoleChanged;
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
      footer: DsTextAction(label: backLabel, onPressed: onBack),
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
    required this.onGenerate,
    required this.onPublish,
  });

  final DateTime month;
  final List<DsRosterRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onGenerate;
  final VoidCallback onPublish;

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
        DsSecondaryButton(
          label: l.text('publishSchedule'),
          icon: Icons.publish_outlined,
          onPressed: onPublish,
        ),
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
                    message: l.text('scheduleEmptyMessage'),
                  )
                else
                  _DsRosterTable(month: month, rows: rows, days: days),
              ],
            ),
          ),
          if (rows.isNotEmpty) ...[
            const SizedBox(height: DsSpacing.x4),
            const _DsShiftLegend(),
          ],
        ],
      ),
    );
  }
}

class _DsRosterTable extends StatelessWidget {
  const _DsRosterTable({
    required this.month,
    required this.rows,
    required this.days,
  });

  final DateTime month;
  final List<DsRosterRowData> rows;
  final int days;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return _DsDayGrid(
      month: month,
      days: days,
      trailingHeaders: ['A', 'D', l.text('off')],
      rows: [
        for (final row in rows)
          _DsDayGridRow(
            name: row.name,
            role: row.role,
            shifts: row.shifts,
            trailing: ['${row.arrivals}', '${row.departures}', '${row.offDays}'],
          ),
      ],
    );
  }
}

/// Shared, full-width day-by-day grid used by the roster and attendance boards:
/// employee · role · one cell per day · trailing summary columns. Columns are
/// distributed evenly across the full surface width (min widths double as flex
/// weights so proportions hold while stretching); it only scrolls horizontally
/// when a long month genuinely can't fit the viewport.
class _DsDayGrid extends StatelessWidget {
  const _DsDayGrid({
    required this.month,
    required this.days,
    required this.trailingHeaders,
    required this.rows,
  });

  final DateTime month;
  final int days;
  final List<String> trailingHeaders;
  final List<_DsDayGridRow> rows;

  static const double _nameMin = 150;
  static const double _roleMin = 80;
  static const double _dayMin = 46;
  static const double _trailMin = 72;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final naturalWidth = _nameMin +
        _roleMin +
        days * _dayMin +
        trailingHeaders.length * _trailMin;

    return LayoutBuilder(
      builder: (context, constraints) {
        final tableWidth = math.max(constraints.maxWidth, naturalWidth);
        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: tableWidth,
            child: Column(
              children: [
                _gridRow(
                  background: DsColors.surfaceSubtle,
                  name: _headerText(l.text('employee'), align: TextAlign.left),
                  role: _headerText(l.role),
                  days: [
                    for (var day = 1; day <= days; day++)
                      _DsDayHeader(date: DateTime(month.year, month.month, day)),
                  ],
                  trailing: [for (final h in trailingHeaders) _headerText(h)],
                ),
                for (final row in rows) ...[
                  const Divider(height: 1, color: DsColors.border),
                  _gridRow(
                    name: Text(
                      row.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    role: Center(child: DsBadge(label: row.role)),
                    days: [
                      for (final shift in row.shifts)
                        Center(child: DsShiftBadge(code: shift, compact: true)),
                    ],
                    trailing: [
                      for (final value in row.trailing)
                        Center(
                          child: Text(
                            value,
                            style: const TextStyle(color: DsColors.textPrimary),
                          ),
                        ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _gridRow({
    required Widget name,
    required Widget role,
    required List<Widget> days,
    required List<Widget> trailing,
    Color? background,
  }) {
    return Container(
      color: background,
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x4,
        vertical: DsSpacing.x3,
      ),
      child: Row(
        children: [
          _cell(_nameMin, name),
          _cell(_roleMin, role),
          for (final day in days) _cell(_dayMin, day),
          for (final cell in trailing) _cell(_trailMin, cell),
        ],
      ),
    );
  }

  Widget _cell(double weight, Widget child) => Expanded(
        flex: weight.round(),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 2),
          child: child,
        ),
      );

  Widget _headerText(String label, {TextAlign align = TextAlign.center}) => Text(
        label,
        textAlign: align,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: DsColors.textMuted,
        ),
      );
}

class _DsDayGridRow {
  const _DsDayGridRow({
    required this.name,
    required this.role,
    required this.shifts,
    required this.trailing,
  });

  final String name;
  final String role;
  final List<ShiftCode> shifts;
  final List<String> trailing;
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
    required this.onImport,
    required this.onAdd,
    this.onManagePresets,
  });

  final DateTime month;
  final List<DsFlightRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onImport;
  final VoidCallback onAdd;

  /// If non-null an admin "Manage presets" toolbar action is shown.
  final VoidCallback? onManagePresets;

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
        if (onManagePresets != null)
          DsSecondaryButton(
            label: l.text('managePresets'),
            icon: Icons.tune_outlined,
            onPressed: onManagePresets!,
          ),
        DsSecondaryButton(
          label: l.text('importExcel'),
          icon: Icons.upload_file_outlined,
          onPressed: onImport,
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
          const SizedBox(height: DsSpacing.x6),
          DsUploadZone(
            title: l.text('importMonthlyFlights'),
            hint: l.text('excelFileHint'),
            buttonLabel: l.text('chooseFile'),
            onPressed: onImport,
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

  // date | pairs | flights | STA | STD | status
  static const _flex = [2, 1, 4, 2, 2, 2];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      children: [
        _row(
          [
            _header(l.text('date')),
            _header(l.text('pairs')),
            _header(l.text('flights')),
            _header('STA'),
            _header('STD'),
            _header(l.status),
          ],
          background: DsColors.surfaceSubtle,
        ),
        for (final row in rows) ...[
          const Divider(height: 1, color: DsColors.border),
          _row([
            _text(l.flightDate(row.date)),
            _text('${row.flightPairs}'),
            _text(row.flights),
            _text(row.arrival),
            _text(row.departure),
            _leading(
              DsBadge(
                label: l.statusLabel(row.status),
                tone: row.status == 'Complete' ? DsTone.success : DsTone.warning,
              ),
            ),
          ]),
        ],
      ],
    );
  }

  Widget _row(List<Widget> cells, {Color? background}) => Container(
    color: background,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x5,
      vertical: DsSpacing.x4,
    ),
    child: Row(
      children: [
        for (var i = 0; i < cells.length; i++)
          Expanded(flex: _flex[i], child: cells[i]),
      ],
    ),
  );

  Widget _header(String label) => Text(
    label,
    style: const TextStyle(
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: DsColors.textMuted,
    ),
  );

  Widget _text(String value) => Text(
    value,
    style: const TextStyle(fontSize: 14, color: DsColors.textPrimary),
    overflow: TextOverflow.ellipsis,
  );

  Widget _leading(Widget child) =>
      Align(alignment: Alignment.centerLeft, child: child);
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
    required this.onNewRequest,
    required this.onApprove,
    required this.onReject,
  });

  final List<DsLeaveRowData> rows;
  final VoidCallback onNewRequest;
  final ValueChanged<int> onApprove;
  final ValueChanged<int> onReject;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final pending = rows.where((row) => row.status == 'Pending').length;
    final approved = rows.where((row) => row.status == 'Approved').length;
    final carry = rows.fold<int>(0, (sum, row) => sum + row.carryComp);
    return DsPage(
      title: l.text('leaveRequests'),
      subtitle: l.text('leaveSubtitle'),
      actions: [
        DsPrimaryButton(
          label: l.text('requestLeave'),
          icon: Icons.add,
          onPressed: onNewRequest,
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
                value: '$carry',
                icon: Icons.event_repeat_outlined,
                tone: DsTone.primary,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          DsInlineAlert(
            title: l.text('registrationOpen'),
            message: l.text('shortLeaveMessage'),
            tone: DsTone.primary,
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
    required this.onApprove,
    required this.onReject,
  });

  final List<DsLeaveRowData> rows;
  final ValueChanged<int> onApprove;
  final ValueChanged<int> onReject;

  // employee | role | type | dates | days | carry | status | actions
  static const _flex = [3, 2, 2, 3, 1, 1, 2, 3];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      children: [
        _row(
          [
            _header(l.text('employee')),
            _header(l.role),
            _header(l.text('type')),
            _header(l.text('dates')),
            _header(l.text('days')),
            _header(l.text('carry')),
            _header(l.status),
            _header(l.actions),
          ],
          background: DsColors.surfaceSubtle,
        ),
        for (var index = 0; index < rows.length; index++) ...[
          const Divider(height: 1, color: DsColors.border),
          _row([
            _text(rows[index].employee),
            _leading(DsBadge(label: rows[index].role)),
            _text(l.leaveTypeLabel(rows[index].type)),
            _text(rows[index].range),
            _text('${rows[index].days}'),
            _text('${rows[index].carryComp}'),
            _leading(
              DsBadge(
                label: l.statusLabel(rows[index].status),
                tone: switch (rows[index].status) {
                  'Approved' => DsTone.success,
                  'Rejected' => DsTone.danger,
                  _ => DsTone.warning,
                },
              ),
            ),
            _leading(
              rows[index].status == 'Pending'
                  ? Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        DsTextAction(
                          label: l.approve,
                          icon: Icons.check,
                          tone: DsTone.success,
                          onPressed: () => onApprove(index),
                        ),
                        DsTextAction(
                          label: l.text('reject'),
                          icon: Icons.close,
                          tone: DsTone.danger,
                          onPressed: () => onReject(index),
                        ),
                      ],
                    )
                  : const SizedBox.shrink(),
            ),
          ]),
        ],
      ],
    );
  }

  Widget _row(List<Widget> cells, {Color? background}) => Container(
    color: background,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x5,
      vertical: DsSpacing.x4,
    ),
    child: Row(
      children: [
        for (var i = 0; i < cells.length; i++)
          Expanded(flex: _flex[i], child: cells[i]),
      ],
    ),
  );

  Widget _header(String label) => Text(
    label,
    style: const TextStyle(
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: DsColors.textMuted,
    ),
  );

  Widget _text(String value) => Text(
    value,
    style: const TextStyle(fontSize: 14, color: DsColors.textPrimary),
    overflow: TextOverflow.ellipsis,
  );

  Widget _leading(Widget child) =>
      Align(alignment: Alignment.centerLeft, child: child);
}

class DsAttendanceView extends StatelessWidget {
  const DsAttendanceView({
    super.key,
    required this.month,
    required this.rows,
    required this.onPreviousMonth,
    required this.onNextMonth,
    required this.onUpdate,
    required this.onHolidays,
  });

  final DateTime month;
  final List<DsAttendanceRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onUpdate;
  final VoidCallback onHolidays;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final workdays = rows.fold<int>(0, (sum, row) => sum + row.workdays);
    final absences = rows.fold<int>(0, (sum, row) => sum + row.absences);
    final sickDays = rows
        .expand((row) => row.shifts)
        .where((shift) => shift == ShiftCode.s)
        .length;
    final days = rows.isEmpty ? 0 : rows.first.shifts.length;
    return DsPage(
      title: l.text('attendanceTitle'),
      subtitle: l.text('attendanceSubtitle'),
      actions: [
        DsSecondaryButton(
          label: l.text('publicHolidays'),
          icon: Icons.event_outlined,
          onPressed: onHolidays,
        ),
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
                            l.text('attendanceEmptyMessage'),
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
                    days: days,
                    trailingHeaders: [l.text('work'), l.text('absent')],
                    rows: [
                      for (final row in rows)
                        _DsDayGridRow(
                          name: row.name,
                          role: row.role,
                          shifts: row.shifts,
                          trailing: ['${row.workdays}', '${row.absences}'],
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
        ],
      ),
    );
  }
}

class DsReportsView extends StatelessWidget {
  const DsReportsView({
    super.key,
    required this.rows,
    required this.onExportMonthly,
    required this.onExportYearly,
    required this.onDownload,
  });

  final List<DsReportRowData> rows;
  final VoidCallback onExportMonthly;
  final VoidCallback onExportYearly;
  final ValueChanged<int> onDownload;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsPage(
      title: l.text('reportsTitle'),
      subtitle: l.text('reportsSubtitle'),
      actions: [
        DsSecondaryButton(
          label: l.text('exportYear'),
          icon: Icons.calendar_view_month_outlined,
          onPressed: onExportYearly,
        ),
        DsPrimaryButton(
          label: l.text('exportMonth'),
          icon: Icons.download_outlined,
          onPressed: onExportMonthly,
        ),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: l.text('reports'),
                value: '${rows.length}',
                icon: Icons.description_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: l.text('formats'),
                value: '2',
                icon: Icons.file_present_outlined,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: l.text('retention'),
                value: 'EU',
                icon: Icons.shield_outlined,
                tone: DsTone.neutral,
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
                  child: DsSectionHeader(l.text('recentExports')),
                ),
                const Divider(height: 1),
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

  // report name | period | updated | status | action
  static const _flex = [4, 2, 2, 2, 2];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      children: [
        _row(
          [
            _header(l.text('report')),
            _header(l.text('period')),
            _header(l.text('updated')),
            _header(l.status),
            _header(l.text('action')),
          ],
          background: DsColors.surfaceSubtle,
        ),
        for (var index = 0; index < rows.length; index++) ...[
          const Divider(height: 1, color: DsColors.border),
          _row([
            _text(rows[index].name),
            _text(rows[index].period),
            _text(rows[index].updated),
            _leading(
              DsBadge(
                label: l.statusLabel(rows[index].status),
                tone: DsTone.success,
                icon: Icons.check_circle_outline,
              ),
            ),
            _leading(
              DsTextAction(
                label: l.text('download'),
                icon: Icons.download_outlined,
                onPressed: () => onDownload(index),
              ),
            ),
          ]),
        ],
      ],
    );
  }

  Widget _row(List<Widget> cells, {Color? background}) => Container(
    color: background,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x5,
      vertical: DsSpacing.x4,
    ),
    child: Row(
      children: [
        for (var i = 0; i < cells.length; i++)
          Expanded(flex: _flex[i], child: cells[i]),
      ],
    ),
  );

  Widget _header(String label) => Text(
    label,
    style: const TextStyle(
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: DsColors.textMuted,
    ),
  );

  Widget _text(String value) => Text(
    value,
    style: const TextStyle(fontSize: 14, color: DsColors.textPrimary),
    overflow: TextOverflow.ellipsis,
  );

  Widget _leading(Widget child) =>
      Align(alignment: Alignment.centerLeft, child: child);
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
  });

  final List<DsUserRowData> users;
  final ValueChanged<int> onApprove;
  final ValueChanged<int> onDisable;
  final ValueChanged<int> onEnable;
  final void Function(int id, String role) onChangeRole;

  // Column flex weights — header and body cells must stay in sync.
  static const _flex = [2, 3, 2, 2, 2, 3];

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Column(
      children: [
        _row(
          [
            _header(l.username),
            _header(l.fullName),
            _header(l.role),
            _header('Code'),
            _header(l.status),
            _header(l.actions),
          ],
          background: DsColors.surfaceSubtle,
        ),
        for (final user in users) ...[
          const Divider(height: 1, color: DsColors.border),
          _row([
            _text(user.username),
            _text(user.fullName),
            _leading(DsBadge(label: l.roleLabel(user.role))),
            _leading(
              user.code.isEmpty
                  ? const SizedBox.shrink()
                  : DsBadge(label: user.code, tone: DsTone.neutral),
            ),
            _leading(
              DsBadge(
                label: l.statusLabel(user.status),
                tone: switch (user.status) {
                  'active' => DsTone.success,
                  'pending' => DsTone.warning,
                  _ => DsTone.neutral,
                },
              ),
            ),
            _leading(switch (user.status) {
              'pending' => _ActionButton(
                label: l.approve,
                tone: DsTone.success,
                onPressed: () => onApprove(user.id),
              ),
              // Active users can be disabled AND have their role changed
              // (e.g. promoted to admin `M`); both actions wrap if cramped.
              'active' => Wrap(
                spacing: DsSpacing.x2,
                runSpacing: DsSpacing.x1,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
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
              ),
              _ => _ActionButton(
                label: l.enable,
                tone: DsTone.primary,
                onPressed: () => onEnable(user.id),
              ),
            }),
          ]),
        ],
      ],
    );
  }

  Widget _row(List<Widget> cells, {Color? background}) => Container(
    color: background,
    padding: const EdgeInsets.symmetric(
      horizontal: DsSpacing.x5,
      vertical: DsSpacing.x4,
    ),
    child: Row(
      children: [
        for (var i = 0; i < cells.length; i++)
          Expanded(flex: _flex[i], child: cells[i]),
      ],
    ),
  );

  Widget _header(String label) => Text(
    label,
    style: const TextStyle(
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: DsColors.textMuted,
    ),
  );

  Widget _text(String value) => Text(
    value,
    style: const TextStyle(fontSize: 14, color: DsColors.textPrimary),
    overflow: TextOverflow.ellipsis,
  );

  Widget _leading(Widget child) =>
      Align(alignment: Alignment.centerLeft, child: child);
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
        textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
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

  static const _roles = ['M', 'T', 'A'];

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
                fontSize: 13,
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
    this.error,
    this.loading = false,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController usernameController;
  final TextEditingController fullNameController;
  final TextEditingController passwordController;
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
