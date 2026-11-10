// One rule for every error toast/state (review 2026-11-08, final wave): the
// backend detail for a 4xx, a translated text when the server is down or
// crashed, and never an exception's debug text.

import 'package:attendance_scheduler_app/core/network/api_error_message.dart';
import 'package:attendance_scheduler_app/core/network/api_exception.dart';
import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:dio/dio.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

const _en = AppLocalizations(Locale('en'));
const _vi = AppLocalizations(Locale('vi'));

void main() {
  // POST /flights/import rejects a file with {message, errors: [...]}: the
  // toast shows the sentence and which rows/cells are wrong, not a map dump.
  test('an import rejection lists its row errors', () {
    final detail = ApiException.detailOf({
      'detail': {
        'message': 'Excel import failed.',
        'errors': ['Cell W4: "y" is not a valid mark.', 'Row 6: no preset.'],
      },
    });
    expect(
      detail,
      'Excel import failed. Cell W4: "y" is not a valid mark.; Row 6: no preset.',
    );
  });

  test('a long import error list is cut after five with the rest counted', () {
    final detail = ApiException.detailOf({
      'detail': {
        'message': 'Excel import failed.',
        'errors': [for (var i = 1; i <= 8; i++) 'e$i'],
      },
    });
    expect(detail, 'Excel import failed. e1; e2; e3; e4; e5 (+3)');
  });

  test('a 4xx shows only the backend detail', () {
    const e = ApiException('You already checked out today.', statusCode: 409);
    expect(apiErrorMessage(_en, e), 'You already checked out today.');
  });

  test('no response is "server unavailable", translated', () {
    const e = ApiException('The connection errored');
    expect(apiErrorMessage(_en, e), _en.text('requestServerUnavailable'));
    expect(apiErrorMessage(_vi, e), _vi.text('requestServerUnavailable'));
    expect(apiErrorMessage(_en, e), isNot(contains('connection errored')));
  });

  test('a 5xx is a translated server error, never the body', () {
    const e = ApiException('<html>Traceback</html>', statusCode: 502);
    expect(apiErrorMessage(_vi, e), _vi.text('requestServerError'));
  });

  test('an empty detail falls back to the generic text', () {
    const e = ApiException('  ', statusCode: 400);
    expect(apiErrorMessage(_en, e), _en.text('requestFailed'));
  });

  test('a non-ApiException never shows its toString', () {
    final e = StateError('boom');
    expect(apiErrorMessage(_en, e), _en.text('requestFailed'));
    expect(
      apiErrorMessage(_en, e, fallbackKey: 'clockActionFailed'),
      _en.text('clockActionFailed'),
    );
  });

  test('a raw DioException is read like an ApiException', () {
    final request = RequestOptions(path: '/x');
    final offline = DioException(
      requestOptions: request,
      type: DioExceptionType.connectionError,
      message: 'SocketException: Connection refused',
    );
    expect(apiErrorMessage(_en, offline), _en.text('requestServerUnavailable'));

    final conflict = DioException(
      requestOptions: request,
      response: Response(
        requestOptions: request,
        statusCode: 409,
        data: {'detail': 'Taken.'},
      ),
      type: DioExceptionType.badResponse,
    );
    expect(apiErrorMessage(_en, conflict), 'Taken.');
  });
}
