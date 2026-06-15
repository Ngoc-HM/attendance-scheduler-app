import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('feature presentation code composes the centralized design system', () {
    final forbidden = RegExp(
      r'\b(?:Container|Card|DataTable|TextFormField|FilledButton|'
      r'OutlinedButton|NavigationBar|NavigationRail|AlertDialog)\s*\('
      r'|BoxDecoration\s*\(|\bColors\.',
    );
    final violations = <String>[];
    final presentationFiles = Directory('lib/features')
        .listSync(recursive: true)
        .whereType<File>()
        .where(
          (file) =>
              file.path.endsWith('.dart') &&
              file.path.contains('${Platform.pathSeparator}presentation'),
        );

    for (final file in presentationFiles) {
      final content = file.readAsStringSync();
      if (forbidden.hasMatch(content)) violations.add(file.path);
    }

    expect(
      violations,
      isEmpty,
      reason:
          'Feature presentation files must call components from lib/design_system.',
    );
  });

  test('liquid_glass_bar is imported only by its design-system adapter', () {
    final violations = <String>[];
    final dartFiles = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((file) => file.path.endsWith('.dart'));

    for (final file in dartFiles) {
      final content = file.readAsStringSync();
      if (content.contains("package:liquid_glass_bar/") &&
          !file.path.endsWith(
            'design_system${Platform.pathSeparator}src'
            '${Platform.pathSeparator}liquid_navigation_native.dart',
          )) {
        violations.add(file.path);
      }
    }

    expect(violations, isEmpty);
  });

  test('feature presentation code does not recreate glass effects', () {
    final forbidden = RegExp(
      r'\b(?:BackdropFilter|ImageFilter\.blur|LiquidGlassBar|'
      r'DsLiquidGlassSurface|DsLiquidGlassBackdrop)\b',
    );
    final violations = <String>[];
    final presentationFiles = Directory('lib/features')
        .listSync(recursive: true)
        .whereType<File>()
        .where(
          (file) =>
              file.path.endsWith('.dart') &&
              file.path.contains('${Platform.pathSeparator}presentation'),
        );

    for (final file in presentationFiles) {
      if (forbidden.hasMatch(file.readAsStringSync())) {
        violations.add(file.path);
      }
    }

    expect(
      violations,
      isEmpty,
      reason: 'Glass is owned and composed only inside lib/design_system.',
    );
  });

  test('dark text tokens are never used as structural surfaces', () {
    const darkToken =
        r'(?:DsColors\.textPrimary|Colors\.black|Color\(0xFF0F172A\))';
    final forbiddenPatterns = [
      RegExp(r'(?:backgroundColor|fillColor)\s*:\s*' + darkToken),
      RegExp(r'ColoredBox\s*\(\s*color\s*:\s*' + darkToken),
      RegExp(r'BoxDecoration\s*\(\s*color\s*:\s*' + darkToken),
      RegExp(r'Container\s*\(\s*color\s*:\s*' + darkToken),
    ];
    final allowedTextFiles = {
      'lib/design_system/theme.dart',
      'lib/design_system/forms.dart',
      'lib/design_system/navigation.dart',
      'lib/design_system/components.dart',
    };
    final violations = <String>[];

    for (final path in allowedTextFiles) {
      final content = File(path).readAsStringSync();
      for (final pattern in forbiddenPatterns) {
        for (final match in pattern.allMatches(content)) {
          final prefix = content.substring(0, match.start);
          final line = '\n'.allMatches(prefix).length + 1;
          violations.add('$path:$line');
        }
      }
    }

    expect(
      violations,
      isEmpty,
      reason: 'Dark tokens are reserved for text and icon foregrounds.',
    );
  });
}
