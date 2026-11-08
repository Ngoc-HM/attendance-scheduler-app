// Every literal key passed to `text(...)` in lib/ exists in the i18n map, so
// no screen shows a raw key such as "year" or "requestLeave". Literal keys
// inside a conditional argument (`text(a ? 'x' : 'y')`) are checked too.

import 'dart:io';

import 'package:attendance_scheduler_app/i18n/app_localizations.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('every_t_key_used_in_lib_exists', () {
    final call = RegExp(r'\btext\(([^()]*)\)');
    final literal = RegExp(r'''['"]([^'"]*)['"]''');
    final missing = <String>[];
    var checked = 0;

    final files = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));
    for (final file in files) {
      final source = file.readAsStringSync();
      for (final match in call.allMatches(source)) {
        for (final key in literal.allMatches(match.group(1)!)) {
          checked++;
          final name = key.group(1)!;
          if (!AppLocalizations.hasKey(name)) {
            missing.add('${file.path}: $name');
          }
        }
      }
    }

    expect(checked, greaterThan(100), reason: 'the scan found no keys');
    expect(missing, isEmpty);
    expect(AppLocalizations.translationsAreComplete, isTrue);
  });
}
