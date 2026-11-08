import '../../../core/network/api_exception.dart';
import '../../../i18n/app_localizations.dart';

/// What the admin sees when a user-management call fails, chosen by status:
///
/// * no response → the server could not be reached;
/// * 5xx → a generic server error (the body may be an HTML traceback);
/// * any other status → the backend's own `detail` (already translated via
///   `Accept-Language`: last-admin lockout, username taken, not pending,
///   quota out of range, admin rights required, ...);
/// * anything else (no detail, not an [ApiException]) → a generic failure.
String userErrorMessage(AppLocalizations l, Object error) {
  if (error is! ApiException) return l.text('requestFailed');
  final status = error.statusCode;
  if (status == null) return l.text('requestServerUnavailable');
  if (status >= 500) return l.text('requestServerError');
  final detail = error.message.trim();
  return detail.isEmpty ? l.text('requestFailed') : detail;
}
