import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../core/constants/shift_codes.dart';
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
  final VoidCallback onLogin;
  final VoidCallback onRegister;
  final String? error;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return DsAuthPage(
      title: title,
      subtitle: subtitle,
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
                title: 'Login failed',
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
  final ValueChanged<T> onRoleChanged;
  final VoidCallback onSubmit;
  final VoidCallback onBack;
  final String? error;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return DsAuthPage(
      title: title,
      subtitle: subtitle,
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
                title: 'Registration failed',
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
    final arrivals = rows.fold<int>(0, (sum, row) => sum + row.arrivals);
    final departures = rows.fold<int>(0, (sum, row) => sum + row.departures);
    final doubleDuty = rows
        .expand((row) => row.shifts)
        .where((shift) => shift == ShiftCode.aD)
        .length;
    final days = rows.isEmpty ? 0 : rows.first.shifts.length;

    return DsPage(
      title: 'Schedule',
      subtitle: 'Monthly roster for the Frankfurt team',
      actions: [
        DsSecondaryButton(
          label: 'Publish schedule',
          icon: Icons.publish_outlined,
          onPressed: onPublish,
        ),
        DsPrimaryButton(
          label: 'Generate schedule',
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
                label: 'Employees',
                value: '${rows.length}',
                icon: Icons.people_outline,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: 'ARR duties',
                value: '$arrivals',
                icon: Icons.flight_land_outlined,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: 'DEP duties',
                value: '$departures',
                icon: Icons.flight_takeoff_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: 'A/D duties',
                value: '$doubleDuty',
                icon: Icons.warning_amber_outlined,
                tone: DsTone.warning,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          DsInlineAlert(
            title: 'Ready for review',
            message:
                'Hard constraints pass. Review shift balance before publishing.',
            tone: DsTone.success,
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
                      const Expanded(child: DsSectionHeader('Monthly roster')),
                      DsMonthSwitcher(
                        month: month,
                        onPrevious: onPreviousMonth,
                        onNext: onNextMonth,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                _DsRosterTable(month: month, rows: rows, days: days),
              ],
            ),
          ),
          const SizedBox(height: DsSpacing.x4),
          const _DsShiftLegend(),
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
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: [
          const DataColumn(label: Text('Employee')),
          const DataColumn(label: Text('Role')),
          for (var day = 1; day <= days; day++)
            DataColumn(
              label: _DsDayHeader(date: DateTime(month.year, month.month, day)),
            ),
          const DataColumn(label: Text('A')),
          const DataColumn(label: Text('D')),
          const DataColumn(label: Text('Off')),
        ],
        rows: [
          for (final row in rows)
            DataRow(
              cells: [
                DataCell(
                  SizedBox(
                    width: 110,
                    child: Text(
                      row.name,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                DataCell(DsBadge(label: row.role)),
                for (final shift in row.shifts)
                  DataCell(DsShiftBadge(code: shift, compact: true)),
                DataCell(Text('${row.arrivals}')),
                DataCell(Text('${row.departures}')),
                DataCell(Text('${row.offDays}')),
              ],
            ),
        ],
      ),
    );
  }
}

class _DsDayHeader extends StatelessWidget {
  const _DsDayHeader({required this.date});

  final DateTime date;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 30,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('${date.day}'),
          Text(
            DateFormat('E').format(date).substring(0, 2),
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
    const items = [
      (ShiftCode.a, 'ARR'),
      (ShiftCode.d, 'DEP'),
      (ShiftCode.aD, 'Double duty'),
      (ShiftCode.x, 'Off'),
      (ShiftCode.cd, 'Compensation'),
      (ShiftCode.al, 'Leave'),
      (ShiftCode.s, 'Sick'),
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
  });

  final DateTime month;
  final List<DsFlightRowData> rows;
  final VoidCallback onPreviousMonth;
  final VoidCallback onNextMonth;
  final VoidCallback onImport;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final pairCount = rows.fold<int>(
      0,
      (total, row) => total + row.flightPairs,
    );
    final busyDays = rows.where((row) => row.flightPairs == 2).length;
    return DsPage(
      title: 'Flights',
      subtitle: 'STA and STD use Frankfurt local time',
      actions: [
        DsSecondaryButton(
          label: 'Import Excel',
          icon: Icons.upload_file_outlined,
          onPressed: onImport,
        ),
        DsPrimaryButton(label: 'Add flight', icon: Icons.add, onPressed: onAdd),
      ],
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DsResponsiveGrid(
            children: [
              DsMetricCard(
                label: 'Flight days',
                value: '${rows.length}',
                icon: Icons.calendar_today_outlined,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: 'Flight pairs',
                value: '$pairCount',
                icon: Icons.sync_alt_outlined,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: 'Two-pair days',
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
                      const Expanded(child: DsSectionHeader('Flight plan')),
                      DsMonthSwitcher(
                        month: month,
                        onPrevious: onPreviousMonth,
                        onNext: onNextMonth,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Date')),
                      DataColumn(label: Text('Pairs')),
                      DataColumn(label: Text('Flights')),
                      DataColumn(label: Text('STA')),
                      DataColumn(label: Text('STD')),
                      DataColumn(label: Text('Status')),
                    ],
                    rows: [
                      for (final row in rows)
                        DataRow(
                          cells: [
                            DataCell(Text(row.date)),
                            DataCell(Text('${row.flightPairs}')),
                            DataCell(
                              SizedBox(width: 180, child: Text(row.flights)),
                            ),
                            DataCell(Text(row.arrival)),
                            DataCell(Text(row.departure)),
                            DataCell(
                              DsBadge(
                                label: row.status,
                                tone: row.status == 'Complete'
                                    ? DsTone.success
                                    : DsTone.warning,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: DsSpacing.x6),
          DsUploadZone(
            title: 'Import monthly flights',
            hint: 'Excel files up to 10 MB',
            buttonLabel: 'Choose file',
            onPressed: onImport,
          ),
        ],
      ),
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
    final pending = rows.where((row) => row.status == 'Pending').length;
    final approved = rows.where((row) => row.status == 'Approved').length;
    final carry = rows.fold<int>(0, (sum, row) => sum + row.carryComp);
    return DsPage(
      title: 'Leave requests',
      subtitle: 'Monthly requests close on the 20th',
      actions: [
        DsPrimaryButton(
          label: 'Request leave',
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
                label: 'Pending',
                value: '$pending',
                icon: Icons.schedule_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: 'Approved',
                value: '$approved',
                icon: Icons.check_circle_outline,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: 'Comp days',
                value: '$carry',
                icon: Icons.event_repeat_outlined,
                tone: DsTone.primary,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          const DsInlineAlert(
            title: 'Registration open',
            message:
                'Short leave is under 5 consecutive days. Longer leave uses the annual request.',
            tone: DsTone.primary,
          ),
          const SizedBox(height: DsSpacing.x6),
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                const Padding(
                  padding: EdgeInsets.all(DsSpacing.x4),
                  child: DsSectionHeader('Requests'),
                ),
                const Divider(height: 1),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Employee')),
                      DataColumn(label: Text('Role')),
                      DataColumn(label: Text('Type')),
                      DataColumn(label: Text('Dates')),
                      DataColumn(label: Text('Days')),
                      DataColumn(label: Text('Carry')),
                      DataColumn(label: Text('Status')),
                      DataColumn(label: Text('Actions')),
                    ],
                    rows: [
                      for (var index = 0; index < rows.length; index++)
                        DataRow(
                          cells: [
                            DataCell(Text(rows[index].employee)),
                            DataCell(DsBadge(label: rows[index].role)),
                            DataCell(Text(rows[index].type)),
                            DataCell(Text(rows[index].range)),
                            DataCell(Text('${rows[index].days}')),
                            DataCell(Text('${rows[index].carryComp}')),
                            DataCell(
                              DsBadge(
                                label: rows[index].status,
                                tone: switch (rows[index].status) {
                                  'Approved' => DsTone.success,
                                  'Rejected' => DsTone.danger,
                                  _ => DsTone.warning,
                                },
                              ),
                            ),
                            DataCell(
                              rows[index].status == 'Pending'
                                  ? Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        DsTextAction(
                                          label: 'Approve',
                                          icon: Icons.check,
                                          tone: DsTone.success,
                                          onPressed: () => onApprove(index),
                                        ),
                                        DsTextAction(
                                          label: 'Reject',
                                          icon: Icons.close,
                                          tone: DsTone.danger,
                                          onPressed: () => onReject(index),
                                        ),
                                      ],
                                    )
                                  : const SizedBox.shrink(),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
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
    final workdays = rows.fold<int>(0, (sum, row) => sum + row.workdays);
    final absences = rows.fold<int>(0, (sum, row) => sum + row.absences);
    final sickDays = rows
        .expand((row) => row.shifts)
        .where((shift) => shift == ShiftCode.s)
        .length;
    final days = rows.isEmpty ? 0 : rows.first.shifts.length;
    return DsPage(
      title: 'Attendance',
      subtitle: 'Actual daily status and public holidays',
      actions: [
        DsSecondaryButton(
          label: 'Public holidays',
          icon: Icons.event_outlined,
          onPressed: onHolidays,
        ),
        DsPrimaryButton(
          label: 'Update attendance',
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
                label: 'Workdays',
                value: '$workdays',
                icon: Icons.work_outline,
                tone: DsTone.primary,
              ),
              DsMetricCard(
                label: 'Absences',
                value: '$absences',
                icon: Icons.event_busy_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: 'Sick days',
                value: '$sickDays',
                icon: Icons.medical_information_outlined,
                tone: DsTone.danger,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          const DsInlineAlert(
            title: 'Restricted health data',
            message:
                'Sick status is visible to administrators only. Do not record medical details.',
            tone: DsTone.warning,
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
                      const Expanded(
                        child: DsSectionHeader('Attendance board'),
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
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: [
                      const DataColumn(label: Text('Employee')),
                      const DataColumn(label: Text('Role')),
                      for (var day = 1; day <= days; day++)
                        DataColumn(
                          label: _DsDayHeader(
                            date: DateTime(month.year, month.month, day),
                          ),
                        ),
                      const DataColumn(label: Text('Work')),
                      const DataColumn(label: Text('Absent')),
                    ],
                    rows: [
                      for (final row in rows)
                        DataRow(
                          cells: [
                            DataCell(
                              SizedBox(
                                width: 110,
                                child: Text(
                                  row.name,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                            DataCell(DsBadge(label: row.role)),
                            for (final shift in row.shifts)
                              DataCell(
                                DsShiftBadge(code: shift, compact: true),
                              ),
                            DataCell(Text('${row.workdays}')),
                            DataCell(Text('${row.absences}')),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: DsSpacing.x4),
          const _DsShiftLegend(),
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
    return DsPage(
      title: 'Reports',
      subtitle: 'Attendance exports by month and year',
      actions: [
        DsSecondaryButton(
          label: 'Export year',
          icon: Icons.calendar_view_month_outlined,
          onPressed: onExportYearly,
        ),
        DsPrimaryButton(
          label: 'Export month',
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
                label: 'Reports',
                value: '${rows.length}',
                icon: Icons.description_outlined,
                tone: DsTone.primary,
              ),
              const DsMetricCard(
                label: 'Formats',
                value: '2',
                icon: Icons.file_present_outlined,
                tone: DsTone.success,
              ),
              const DsMetricCard(
                label: 'Retention',
                value: 'EU',
                icon: Icons.shield_outlined,
                tone: DsTone.neutral,
              ),
            ],
          ),
          const SizedBox(height: DsSpacing.x6),
          const DsInlineAlert(
            title: 'Flexible export format',
            message:
                'The final customer report layout is not fixed yet. Exports remain modular.',
          ),
          const SizedBox(height: DsSpacing.x6),
          DsSurface(
            padding: EdgeInsets.zero,
            child: Column(
              children: [
                const Padding(
                  padding: EdgeInsets.all(DsSpacing.x4),
                  child: DsSectionHeader('Recent exports'),
                ),
                const Divider(height: 1),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: const [
                      DataColumn(label: Text('Report')),
                      DataColumn(label: Text('Period')),
                      DataColumn(label: Text('Updated')),
                      DataColumn(label: Text('Status')),
                      DataColumn(label: Text('Action')),
                    ],
                    rows: [
                      for (var index = 0; index < rows.length; index++)
                        DataRow(
                          cells: [
                            DataCell(
                              SizedBox(
                                width: 240,
                                child: Text(rows[index].name),
                              ),
                            ),
                            DataCell(Text(rows[index].period)),
                            DataCell(Text(rows[index].updated)),
                            DataCell(
                              DsBadge(
                                label: rows[index].status,
                                tone: DsTone.success,
                                icon: Icons.check_circle_outline,
                              ),
                            ),
                            DataCell(
                              DsTextAction(
                                label: 'Download',
                                icon: Icons.download_outlined,
                                onPressed: () => onDownload(index),
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
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

  @override
  Widget build(BuildContext context) {
    final active = users.where((user) => user.status == 'active').length;
    final pending = users.where((user) => user.status == 'pending').length;
    final fixed = users.where((user) => user.role.startsWith('A')).length;
    return DsPage(
      title: 'Users',
      subtitle: 'Accounts, roles and approvals',
      actions: [
        DsSecondaryButton(
          label: 'Refresh',
          icon: Icons.refresh,
          onPressed: onRefresh,
        ),
        DsPrimaryButton(
          label: 'Create user',
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
                label: 'Active',
                value: '$active',
                icon: Icons.check_circle_outline,
                tone: DsTone.success,
              ),
              DsMetricCard(
                label: 'Pending',
                value: '$pending',
                icon: Icons.schedule_outlined,
                tone: DsTone.warning,
              ),
              DsMetricCard(
                label: 'Fixed team',
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
              title: 'Could not load users',
              message: error!,
              actionLabel: 'Retry',
              onRetry: onRefresh,
            )
          else if (users.isEmpty)
            DsEmptyState(
              icon: Icons.people_outline,
              title: 'No users yet',
              message: 'Create the first account and assign a role.',
              actionLabel: 'Create user',
              onAction: onCreate,
            )
          else
            DsSurface(
              padding: EdgeInsets.zero,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: DataTable(
                  columns: const [
                    DataColumn(label: Text('Username')),
                    DataColumn(label: Text('Full name')),
                    DataColumn(label: Text('Role')),
                    DataColumn(label: Text('Status')),
                    DataColumn(label: Text('Actions')),
                  ],
                  rows: [
                    for (final user in users)
                      DataRow(
                        cells: [
                          DataCell(Text(user.username)),
                          DataCell(
                            SizedBox(width: 180, child: Text(user.fullName)),
                          ),
                          DataCell(DsBadge(label: user.role)),
                          DataCell(
                            DsBadge(
                              label: user.status,
                              tone: switch (user.status) {
                                'active' => DsTone.success,
                                'pending' => DsTone.warning,
                                _ => DsTone.neutral,
                              },
                            ),
                          ),
                          DataCell(switch (user.status) {
                            'pending' => DsTextAction(
                              label: 'Approve',
                              icon: Icons.check,
                              tone: DsTone.success,
                              onPressed: () => onApprove(user.id),
                            ),
                            'active' => DsTextAction(
                              label: 'Disable',
                              icon: Icons.block,
                              tone: DsTone.danger,
                              onPressed: () => onDisable(user.id),
                            ),
                            _ => DsTextAction(
                              label: 'Enable',
                              icon: Icons.lock_open,
                              onPressed: () => onEnable(user.id),
                            ),
                          }),
                        ],
                      ),
                  ],
                ),
              ),
            ),
        ],
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
    return DsFormDialog(
      title: 'Create user',
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
                title: 'Could not create user',
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
    return DsFormDialog(
      title: 'Request leave',
      content: const Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            decoration: InputDecoration(
              labelText: 'Leave type',
              prefixIcon: Icon(Icons.event_available_outlined, size: 20),
            ),
          ),
          SizedBox(height: DsSpacing.x4),
          TextField(
            decoration: InputDecoration(
              labelText: 'Date range',
              prefixIcon: Icon(Icons.date_range_outlined, size: 20),
            ),
          ),
          SizedBox(height: DsSpacing.x4),
          TextField(
            maxLines: 3,
            decoration: InputDecoration(labelText: 'Note'),
          ),
        ],
      ),
      actions: [
        DsTextAction(label: 'Cancel', onPressed: onCancel),
        DsPrimaryButton(label: 'Submit request', onPressed: onSubmit),
      ],
    );
  }
}
