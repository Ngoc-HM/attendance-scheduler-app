import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import '../../../../core/network/api_exception.dart';
import '../../data/datasources/reports_remote_datasource.dart';

/// Result of a completed export: saved file path or error message.
sealed class ExportResult {
  const ExportResult();
}

class ExportSuccess extends ExportResult {
  const ExportSuccess(this.path);
  final String path;
}

class ExportFailure extends ExportResult {
  /// A failed download: [error] is the caught [ApiException], which the page
  /// shows with `apiErrorMessage` (backend detail, or a translated "server
  /// unavailable" / "server error"); [message] is its raw detail.
  ExportFailure(ApiException this.error)
      : message = error.message,
        messageKey = null;

  /// A client-side check failed; the page localizes [messageKey].
  const ExportFailure.localized(String this.messageKey)
      : message = '',
        error = null;

  final String message;
  final String? messageKey;
  final ApiException? error;
}

/// State for the reports page.
class ReportsState {
  const ReportsState({
    this.isExporting = false,
    this.lastResult,
    this.selectedYear,
    this.selectedMonth,
    this.selectedFormat = 'csv',
  });

  final bool isExporting;
  final ExportResult? lastResult;
  final int? selectedYear;

  /// 1..12, or null for the full year (yearly endpoint; never month 0,
  /// which the backend rejects).
  final int? selectedMonth;
  final String selectedFormat; // 'csv' | 'xlsx'

  ReportsState copyWith({
    bool? isExporting,
    ExportResult? lastResult,
    int? selectedYear,
    int? selectedMonth,
    bool fullYear = false,
    String? selectedFormat,
  }) =>
      ReportsState(
        isExporting: isExporting ?? this.isExporting,
        lastResult: lastResult ?? this.lastResult,
        selectedYear: selectedYear ?? this.selectedYear,
        selectedMonth: fullYear ? null : (selectedMonth ?? this.selectedMonth),
        selectedFormat: selectedFormat ?? this.selectedFormat,
      );
}

/// Writes a downloaded report and returns the saved path.
typedef ReportFileSaver = Future<String> Function(
  List<int> bytes,
  String filename,
);

class ReportsController extends StateNotifier<ReportsState> {
  /// [saveFile] defaults to the system downloads folder; tests pass a fake.
  ReportsController(this._ds, {ReportFileSaver? saveFile})
      : _saveFile = saveFile ?? _saveToDownloads,
        super(ReportsState(
          selectedYear: DateTime.now().year,
          selectedMonth: DateTime.now().month,
        ));

  final ReportsRemoteDataSource _ds;
  final ReportFileSaver _saveFile;

  void selectYear(int year) => state = state.copyWith(selectedYear: year);

  /// [month] 1..12, or null for the full year.
  void selectMonth(int? month) => state = month == null
      ? state.copyWith(fullYear: true)
      : state.copyWith(selectedMonth: month);
  void selectFormat(String fmt) => state = state.copyWith(selectedFormat: fmt);

  /// Export the selected period: the month's report, or the yearly report
  /// when the full year is selected. Null when an export is already running
  /// (the click is ignored).
  Future<ExportResult?> export() =>
      state.selectedMonth == null ? exportYearly() : exportMonthly();

  /// Download monthly report, save to downloads directory, surface path.
  Future<ExportResult?> exportMonthly() async {
    final year = state.selectedYear;
    final month = state.selectedMonth;
    if (year == null || month == null) {
      return const ExportFailure.localized('selectYearMonthFirst');
    }
    return _export(
      () => _ds.monthly(year, month, state.selectedFormat),
    );
  }

  /// Download yearly report, save to downloads directory, surface path.
  Future<ExportResult?> exportYearly() async {
    final year = state.selectedYear;
    if (year == null) {
      return const ExportFailure.localized('selectYearFirst');
    }
    return _export(() => _ds.yearly(year, state.selectedFormat));
  }

  /// One export at a time: a second click (Export or a row's Download)
  /// while one runs returns null. A failed download shows the backend detail
  /// or `reportExportFailed`; only a failed file write is `reportSaveFailed`.
  Future<ExportResult?> _export(
    Future<ReportDownload> Function() fetch,
  ) async {
    if (state.isExporting) return null;
    state = state.copyWith(isExporting: true);
    final ReportDownload download;
    try {
      download = await fetch();
    } on ApiException catch (e) {
      return _finish(ExportFailure(e));
    } catch (_) {
      // A malformed response (e.g. a body that is not bytes).
      return _finish(const ExportFailure.localized('reportExportFailed'));
    }
    try {
      final path = await _saveFile(download.bytes, download.filename);
      return _finish(ExportSuccess(path));
    } catch (_) {
      // No writable folder, disk full, ...: a localized message instead of
      // the raw exception text.
      return _finish(const ExportFailure.localized('reportSaveFailed'));
    }
  }

  /// Store [result] unless the controller was disposed meanwhile (logout
  /// resets the providers mid-export).
  ExportResult _finish(ExportResult result) {
    if (mounted) {
      state = state.copyWith(isExporting: false, lastResult: result);
    }
    return result;
  }

  /// Write [bytes] to the system downloads directory and return the full path.
  static Future<String> _saveToDownloads(
    List<int> bytes,
    String filename,
  ) async {
    final dir = await _resolveDownloadsDir();
    final file = File('${dir.path}${Platform.pathSeparator}$filename');
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  /// Resolve the best writable output directory.
  ///
  /// Tries downloads first (Windows/macOS); falls back to documents.
  static Future<Directory> _resolveDownloadsDir() async {
    try {
      final downloads = await getDownloadsDirectory();
      if (downloads != null) return downloads;
    } catch (_) {
      // path_provider may not support getDownloadsDirectory on all platforms.
    }
    return getApplicationDocumentsDirectory();
  }
}

final reportsControllerProvider =
    StateNotifierProvider<ReportsController, ReportsState>(
  (ref) => ReportsController(ref.watch(reportsDataSourceProvider)),
);
