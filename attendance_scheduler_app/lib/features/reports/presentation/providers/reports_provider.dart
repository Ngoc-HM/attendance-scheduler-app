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
  const ExportFailure(this.message);
  final String message;
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
  final int? selectedMonth;
  final String selectedFormat; // 'csv' | 'xlsx'

  ReportsState copyWith({
    bool? isExporting,
    ExportResult? lastResult,
    int? selectedYear,
    int? selectedMonth,
    String? selectedFormat,
  }) =>
      ReportsState(
        isExporting: isExporting ?? this.isExporting,
        lastResult: lastResult ?? this.lastResult,
        selectedYear: selectedYear ?? this.selectedYear,
        selectedMonth: selectedMonth ?? this.selectedMonth,
        selectedFormat: selectedFormat ?? this.selectedFormat,
      );
}

class ReportsController extends StateNotifier<ReportsState> {
  ReportsController(this._ds)
      : super(ReportsState(
          selectedYear: DateTime.now().year,
          selectedMonth: DateTime.now().month,
        ));

  final ReportsRemoteDataSource _ds;

  void selectYear(int year) => state = state.copyWith(selectedYear: year);
  void selectMonth(int month) => state = state.copyWith(selectedMonth: month);
  void selectFormat(String fmt) => state = state.copyWith(selectedFormat: fmt);

  /// Download monthly report, save to downloads directory, surface path.
  Future<ExportResult> exportMonthly() async {
    final year = state.selectedYear;
    final month = state.selectedMonth;
    if (year == null || month == null) {
      return const ExportFailure('Select year and month first');
    }
    return _export(
      () => _ds.monthly(year, month, state.selectedFormat),
    );
  }

  /// Download yearly report, save to downloads directory, surface path.
  Future<ExportResult> exportYearly() async {
    final year = state.selectedYear;
    if (year == null) return const ExportFailure('Select year first');
    return _export(() => _ds.yearly(year, state.selectedFormat));
  }

  Future<ExportResult> _export(
    Future<ReportDownload> Function() fetch,
  ) async {
    state = state.copyWith(isExporting: true);
    try {
      final download = await fetch();
      final savedPath = await _saveFile(download.bytes, download.filename);
      final result = ExportSuccess(savedPath);
      state = state.copyWith(isExporting: false, lastResult: result);
      return result;
    } on ApiException catch (e) {
      final result = ExportFailure(e.message);
      state = state.copyWith(isExporting: false, lastResult: result);
      return result;
    } catch (e) {
      final result = ExportFailure(e.toString());
      state = state.copyWith(isExporting: false, lastResult: result);
      return result;
    }
  }

  /// Write [bytes] to the system downloads directory and return the full path.
  static Future<String> _saveFile(List<int> bytes, String filename) async {
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
