import 'package:flutter/material.dart';

import 'tokens.dart';

abstract final class AppTheme {
  static const _radius = BorderRadius.all(Radius.circular(DsRadius.medium));
  static const _cardRadius = BorderRadius.all(Radius.circular(DsRadius.large));

  static ThemeData get light {
    const scheme = ColorScheme.light(
      primary: DsColors.primary,
      onPrimary: Colors.white,
      primaryContainer: DsColors.primarySoft,
      onPrimaryContainer: DsColors.primaryHover,
      secondary: DsColors.textSecondary,
      onSecondary: Colors.white,
      surface: DsColors.surface,
      onSurface: DsColors.textPrimary,
      error: DsColors.danger,
      onError: Colors.white,
      outline: DsColors.borderStrong,
      outlineVariant: DsColors.border,
    );

    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: scheme,
      scaffoldBackgroundColor: DsColors.background,
      fontFamily: 'Inter',
      fontFamilyFallback: const ['Segoe UI', 'SF Pro Text', 'Roboto', 'Arial'],
      visualDensity: VisualDensity.standard,
    );

    final textTheme = base.textTheme.copyWith(
      displaySmall: base.textTheme.displaySmall?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 36,
        height: 44 / 36,
        fontWeight: FontWeight.w700,
      ),
      headlineMedium: base.textTheme.headlineMedium?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 30,
        height: 38 / 30,
        fontWeight: FontWeight.w700,
      ),
      headlineSmall: base.textTheme.headlineSmall?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 24,
        height: 32 / 24,
        fontWeight: FontWeight.w600,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 20,
        height: 28 / 20,
        fontWeight: FontWeight.w600,
      ),
      titleMedium: base.textTheme.titleMedium?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 16,
        height: 24 / 16,
        fontWeight: FontWeight.w600,
      ),
      bodyLarge: base.textTheme.bodyLarge?.copyWith(
        color: DsColors.textPrimary,
        fontSize: 16,
        height: 1.5,
      ),
      bodyMedium: base.textTheme.bodyMedium?.copyWith(
        color: DsColors.textSecondary,
        fontSize: 14,
        height: 20 / 14,
      ),
      bodySmall: base.textTheme.bodySmall?.copyWith(
        color: DsColors.textMuted,
        fontSize: 12,
        height: 16 / 12,
        fontWeight: FontWeight.w500,
      ),
      labelLarge: base.textTheme.labelLarge?.copyWith(
        fontSize: 14,
        height: 20 / 14,
        fontWeight: FontWeight.w600,
      ),
    );

    return base.copyWith(
      textTheme: textTheme,
      dividerColor: DsColors.border,
      cardTheme: const CardThemeData(
        color: DsColors.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: _cardRadius,
          side: BorderSide(color: DsColors.border),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: DsColors.surface,
        foregroundColor: DsColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        surfaceTintColor: Colors.transparent,
      ),
      inputDecorationTheme: const InputDecorationTheme(
        filled: true,
        fillColor: DsColors.surface,
        isDense: true,
        contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        hintStyle: TextStyle(color: DsColors.textMuted),
        labelStyle: TextStyle(color: DsColors.textSecondary),
        border: OutlineInputBorder(
          borderRadius: _radius,
          borderSide: BorderSide(color: DsColors.borderStrong),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: _radius,
          borderSide: BorderSide(color: DsColors.borderStrong),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: _radius,
          borderSide: BorderSide(color: DsColors.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: _radius,
          borderSide: BorderSide(color: DsColors.danger),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: _radius,
          borderSide: BorderSide(color: DsColors.danger, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, DsControlHeight.medium),
          padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4),
          shape: const RoundedRectangleBorder(borderRadius: _radius),
          textStyle: textTheme.labelLarge,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: DsColors.textPrimary,
          minimumSize: const Size(0, DsControlHeight.medium),
          padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4),
          side: const BorderSide(color: DsColors.borderStrong),
          shape: const RoundedRectangleBorder(borderRadius: _radius),
          textStyle: textTheme.labelLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(
            DsControlHeight.medium,
            DsControlHeight.medium,
          ),
          padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x3),
          shape: const RoundedRectangleBorder(borderRadius: _radius),
          textStyle: textTheme.labelLarge,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          minimumSize: const Size(
            DsControlHeight.medium,
            DsControlHeight.medium,
          ),
          foregroundColor: DsColors.textSecondary,
          shape: const RoundedRectangleBorder(borderRadius: _radius),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: DsColors.primary,
        foregroundColor: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: _cardRadius),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: DsColors.surfaceSubtle,
        side: const BorderSide(color: DsColors.border),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(DsRadius.small)),
        ),
        labelStyle: textTheme.bodySmall?.copyWith(
          color: DsColors.textSecondary,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 6),
      ),
      dialogTheme: const DialogThemeData(
        backgroundColor: DsColors.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 10,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(DsRadius.xLarge)),
        ),
      ),
      snackBarTheme: const SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: DsColors.surface,
        contentTextStyle: TextStyle(color: DsColors.textPrimary),
        elevation: 4,
        shape: RoundedRectangleBorder(borderRadius: _radius),
      ),
      dataTableTheme: DataTableThemeData(
        headingRowColor: const WidgetStatePropertyAll(DsColors.surfaceSubtle),
        headingTextStyle: textTheme.bodySmall?.copyWith(
          color: DsColors.textSecondary,
          fontWeight: FontWeight.w700,
        ),
        dataTextStyle: textTheme.bodyMedium?.copyWith(
          color: DsColors.textPrimary,
        ),
        dividerThickness: 1,
        horizontalMargin: DsSpacing.x4,
        columnSpacing: DsSpacing.x6,
        dataRowMinHeight: 52,
        dataRowMaxHeight: 56,
        headingRowHeight: 44,
      ),
      tooltipTheme: const TooltipThemeData(
        decoration: BoxDecoration(
          color: DsColors.surface,
          border: Border.fromBorderSide(
            BorderSide(color: DsColors.borderStrong),
          ),
          borderRadius: BorderRadius.all(Radius.circular(DsRadius.small)),
        ),
        textStyle: TextStyle(color: DsColors.textPrimary, fontSize: 12),
      ),
    );
  }
}
