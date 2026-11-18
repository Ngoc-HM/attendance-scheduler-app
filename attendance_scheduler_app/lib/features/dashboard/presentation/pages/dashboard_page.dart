import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/api_error_message.dart';
import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/dashboard_datasource.dart';

/// Reloaded every time the admin opens the page.
final dashboardProvider = FutureProvider.autoDispose<DashboardData>(
  (ref) => ref.watch(dashboardDataSourceProvider).fetch(),
);

/// Admin dashboard (customer 2026-11-18): today's duty, missing punches,
/// requests waiting, the state of this and next month's roster and
/// everyone's leave — read-only, each part mirrors the page that owns it.
class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  static String _two(int n) => n.toString().padLeft(2, '0');
  static String _date(DateTime d) =>
      '${_two(d.day)}/${_two(d.month)}/${d.year}';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = AppLocalizations.of(context);
    final data = ref.watch(dashboardProvider);
    return DsPage(
      title: l.text('navDashboard'),
      subtitle: data.valueOrNull == null ? null : _date(data.value!.today),
      child: data.when(
        loading: () => const DsLoadingState(),
        error: (error, _) => DsErrorState(
          title: l.text('dashboardLoadFailed'),
          message: apiErrorMessage(l, error),
          actionLabel: l.text('retry'),
          onRetry: () => ref.invalidate(dashboardProvider),
        ),
        data: (d) => _DashboardBody(data: d),
      ),
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final violations = data.thisMonth.violations.length;
    final staffToday = data.working.length + data.off.length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DsResponsiveGrid(
          children: [
            DsMetricCard(
              label: l.text('dashWorkingToday'),
              value: '${data.working.length}/$staffToday',
              icon: Icons.groups_outlined,
              tone: DsTone.primary,
            ),
            DsMetricCard(
              label: l.text('dashMissingClock'),
              value: '${data.missingClock.length}',
              icon: Icons.timer_off_outlined,
              tone: data.missingClock.isEmpty ? DsTone.success : DsTone.danger,
            ),
            DsMetricCard(
              label: l.text('dashPending'),
              value: '${data.pendingTotal}',
              icon: Icons.pending_actions_outlined,
              tone: data.pendingTotal == 0 ? DsTone.success : DsTone.warning,
            ),
            DsMetricCard(
              label: l.text('dashViolations'),
              value: '$violations',
              icon: Icons.rule_outlined,
              tone: violations == 0 ? DsTone.success : DsTone.danger,
            ),
          ],
        ),
        const SizedBox(height: DsSpacing.x6),
        // Two equal columns on a wide window, stacked below that.
        LayoutBuilder(
          builder: (context, constraints) {
            final left = Column(
              children: [
                _TodaySection(data: data),
                const SizedBox(height: DsSpacing.x6),
                _RosterSection(months: [data.thisMonth, data.nextMonth]),
              ],
            );
            final right = _MissingSection(rows: data.missingClock);
            if (constraints.maxWidth < 900) {
              return Column(
                children: [
                  left,
                  const SizedBox(height: DsSpacing.x6),
                  right,
                ],
              );
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: left),
                const SizedBox(width: DsSpacing.x6),
                Expanded(child: right),
              ],
            );
          },
        ),
        const SizedBox(height: DsSpacing.x6),
        _LeaveSection(year: data.leaveYear, rows: data.leave),
      ],
    );
  }
}

/// A titled surface holding a table, or [empty] when it has no rows.
class _Section extends StatelessWidget {
  const _Section({required this.title, required this.table, this.empty});

  final String title;
  final Widget table;

  /// Shown instead of [table] when not null.
  final String? empty;

  @override
  Widget build(BuildContext context) {
    return DsSurface(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(DsSpacing.x4),
            child: DsSectionHeader(title),
          ),
          const Divider(height: 1),
          if (empty == null)
            table
          else
            Padding(
              padding: const EdgeInsets.all(DsSpacing.x5),
              child: Text(empty!, style: DsType.tableCell),
            ),
        ],
      ),
    );
  }
}

Text _cell(String text) =>
    Text(text, style: DsType.tableCell, overflow: TextOverflow.ellipsis);

class _TodaySection extends StatelessWidget {
  const _TodaySection({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final rows = [...data.working, ...data.off];
    return _Section(
      title: l.text('dashToday'),
      empty: rows.isEmpty ? l.text('dashNoRosterToday') : null,
      table: DsDataTable(
        columns: [
          DsTableColumn(header: l.text('clockCode'), flex: 2),
          DsTableColumn(header: l.text('dashShift'), flex: 2),
          DsTableColumn(header: l.text('clockIn'), flex: 2),
          DsTableColumn(header: l.text('clockOut'), flex: 2),
        ],
        rows: [
          for (final duty in rows)
            [
              _cell(duty.code),
              duty.shift == null
                  ? _cell('—')
                  : DsShiftBadge(code: duty.shift!, compact: true),
              _cell(duty.checkIn ?? '—'),
              _cell(duty.checkOut ?? '—'),
            ],
        ],
      ),
    );
  }
}

class _RosterSection extends StatelessWidget {
  const _RosterSection({required this.months});

  final List<DashboardSchedule> months;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return _Section(
      title: l.text('dashRoster'),
      table: DsDataTable(
        columns: [
          DsTableColumn(header: l.text('month'), flex: 3),
          DsTableColumn(header: l.status, flex: 3),
          DsTableColumn(header: l.text('dashViolations'), flex: 3),
        ],
        rows: [
          for (final m in months)
            [
              _cell(l.monthYear(DateTime(m.year, m.month))),
              Align(
                alignment: Alignment.centerLeft,
                child: switch (m.status) {
                  'published' => DsBadge(
                    label: l.text('dashPublished'),
                    tone: DsTone.success,
                  ),
                  'draft' => DsBadge(
                    label: l.text('dashDraft'),
                    tone: DsTone.warning,
                  ),
                  _ => DsBadge(label: l.text('dashNotCreated')),
                },
              ),
              _cell(m.status == null ? '—' : '${m.violations.length}'),
            ],
        ],
      ),
    );
  }
}

class _MissingSection extends StatelessWidget {
  const _MissingSection({required this.rows});

  /// Most recent day first.
  final List<DashboardMissing> rows;

  /// The newest days only: the count is on the card above and every day is
  /// on the Attendance tab; a long month must not push the leave table away.
  static const _shown = 8;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return _Section(
      title: l.text('dashMissingClock'),
      empty: rows.isEmpty ? l.text('dashNoMissingClock') : null,
      table: DsDataTable(
        columns: [
          DsTableColumn(header: l.text('clockCode'), flex: 3),
          DsTableColumn(header: l.text('date'), flex: 3),
          DsTableColumn(header: l.status, flex: 3),
        ],
        rows: [
          for (final row in rows.take(_shown))
            [
              _cell(row.code),
              _cell(DashboardPage._date(row.workDate)),
              Align(
                alignment: Alignment.centerLeft,
                child: DsBadge(
                  label: row.status == 'missed_out'
                      ? l.text('dashNoCheckOut')
                      : l.text('dashNoCheckIn'),
                  tone: DsTone.danger,
                ),
              ),
            ],
        ],
      ),
    );
  }
}

class _LeaveSection extends StatelessWidget {
  const _LeaveSection({required this.year, required this.rows});

  final int year;
  final List<DashboardLeave> rows;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return _Section(
      title: '${l.text('dashLeave')} $year',
      empty: rows.isEmpty ? l.text('dashNoStaff') : null,
      table: DsDataTable(
        columns: [
          DsTableColumn(header: l.text('clockCode'), flex: 2),
          DsTableColumn(header: l.text('dashQuota'), flex: 2),
          DsTableColumn(header: l.text('approved'), flex: 2),
          DsTableColumn(header: l.text('pending'), flex: 2),
          DsTableColumn(header: l.text('dashLeft'), flex: 2),
          DsTableColumn(header: l.text('compDays'), flex: 2),
        ],
        rows: [
          for (final row in rows)
            [
              _cell(row.code),
              _cell('${row.quota}'),
              _cell('${row.used}'),
              _cell('${row.pending}'),
              Align(
                alignment: Alignment.centerLeft,
                child: DsBadge(
                  label: '${row.available}',
                  tone: row.available <= 0
                      ? DsTone.danger
                      : (row.available <= 5 ? DsTone.warning : DsTone.success),
                ),
              ),
              _cell('${row.carryComp}'),
            ],
        ],
      ),
    );
  }
}
