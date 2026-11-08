import 'package:dio/dio.dart';

import '../../i18n/app_localizations.dart';
import 'api_exception.dart';

/// What the user sees when a call fails, chosen by status:
///
/// * no response → the server could not be reached;
/// * 5xx → a generic server error (the body may be an HTML traceback);
/// * any other status → the backend's own `detail` (already translated via
///   `Accept-Language`: last-admin lockout, already checked out, month
///   published, ...);
/// * no detail, not an API error at all, or no error (null) → [fallbackKey]
///   (default `requestFailed`), translated — never the exception's debug
///   text ("ApiException(409): ...", "Bad state: ...").
///
/// A raw [DioException] that slipped past a datasource is read the same way.
/// Controllers store the caught error object (they have no locale); pages
/// and dialogs call this to show it.
String apiErrorMessage(
  AppLocalizations l,
  Object? error, {
  String fallbackKey = 'requestFailed',
}) {
  final e = error is DioException ? ApiException.fromDio(error) : error;
  if (e is! ApiException) return l.text(fallbackKey);
  final status = e.statusCode;
  if (status == null) return l.text('requestServerUnavailable');
  if (status >= 500) return l.text('requestServerError');
  final detail = e.message.trim();
  return detail.isEmpty ? l.text(fallbackKey) : detail;
}
