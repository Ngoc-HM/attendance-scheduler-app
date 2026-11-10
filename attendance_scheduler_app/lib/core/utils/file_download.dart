import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

/// A file the backend streamed back: raw bytes + the suggested filename.
class FileDownload {
  const FileDownload({required this.bytes, required this.filename});
  final List<int> bytes;
  final String filename;
}

/// Writes a downloaded file and returns the saved path. Controllers take one
/// of these so tests can pass a fake instead of touching the disk.
typedef DownloadedFileSaver = Future<String> Function(
  List<int> bytes,
  String filename,
);

/// Parse `Content-Disposition: attachment; filename="foo.csv"` → `foo.csv`,
/// or [fallback] when the header is missing or has no filename.
String filenameFromContentDisposition(
  Response<dynamic> response,
  String fallback,
) {
  final header = response.headers.value('content-disposition') ?? '';
  final match = RegExp(r'filename="?([^";]+)"?').firstMatch(header);
  return match?.group(1) ?? fallback;
}

/// Write [bytes] to the system downloads directory and return the full path.
Future<String> saveToDownloads(List<int> bytes, String filename) async {
  final dir = await _resolveDownloadsDir();
  final file = File('${dir.path}${Platform.pathSeparator}$filename');
  await file.writeAsBytes(bytes, flush: true);
  return file.path;
}

/// Resolve the best writable output directory.
///
/// Tries downloads first (Windows/macOS); falls back to documents.
Future<Directory> _resolveDownloadsDir() async {
  try {
    final downloads = await getDownloadsDirectory();
    if (downloads != null) return downloads;
  } catch (_) {
    // path_provider may not support getDownloadsDirectory on all platforms.
  }
  return getApplicationDocumentsDirectory();
}
