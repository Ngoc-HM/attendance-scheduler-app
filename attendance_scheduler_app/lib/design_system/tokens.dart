import 'package:flutter/material.dart';

abstract final class DsColors {
  static const background = Color(0xFFF5F7FB);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceSubtle = Color(0xFFF3F6FB);
  static const surfaceMuted = Color(0xFFE2E8F0);
  static const textPrimary = Color(0xFF0F172A);
  static const textSecondary = Color(0xFF475569);
  static const textMuted = Color(0xFF64748B);
  static const textDisabled = Color(0xFF94A3B8);
  static const border = Color(0xFFE2E8F0);
  static const borderStrong = Color(0xFFCBD5E1);
  static const focusRing = Color(0xFF7DD3FC);
  static const primary = Color(0xFF0284C7);
  static const primaryHover = Color(0xFF0369A1);
  static const primarySoft = Color(0xFFF0F9FF);
  static const glassBase = Color(0xBFFFFFFF);
  static const glassStrong = Color(0xE6FFFFFF);
  static const glassBorder = Color(0xF2FFFFFF);
  static const glassHighlight = Color(0x99FFFFFF);
  static const success = Color(0xFF15803D);
  static const successSoft = Color(0xFFF0FDF4);
  static const warning = Color(0xFFB45309);
  static const warningSoft = Color(0xFFFFFBEB);
  static const danger = Color(0xFFBE123C);
  static const dangerSoft = Color(0xFFFFF1F2);
}

abstract final class DsSpacing {
  static const double x1 = 4;
  static const double x2 = 8;
  static const double x3 = 12;
  static const double x4 = 16;
  static const double x5 = 20;
  static const double x6 = 24;
  static const double x8 = 32;
  static const double x10 = 40;
  static const double x12 = 48;
}

abstract final class DsRadius {
  static const double small = 6;
  static const double medium = 10;
  static const double large = 12;
  static const double xLarge = 16;
  static const double xxLarge = 20;
}

abstract final class DsBreakpoints {
  static const double mobile = 768;
  static const double desktop = 1024;
  static const double wide = 1440;
}

abstract final class DsControlHeight {
  static const double compact = 32;
  static const double medium = 40;
  static const double touch = 44;
}

abstract final class DsDuration {
  static const fast = Duration(milliseconds: 120);
  static const base = Duration(milliseconds: 160);
  static const medium = Duration(milliseconds: 220);
  static const slow = Duration(milliseconds: 280);
  static const navigation = Duration(milliseconds: 320);
  static const pageTransition = Duration(milliseconds: 480); // full-page slide
  static const shimmer = Duration(milliseconds: 900);
}

/// Shared gradients so the page-background reads identically whether it is the
/// static window backdrop or an individual page sliding as one opaque block.
abstract final class DsGradients {
  static const appBackground = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFFF8FCFF),
      Color(0xFFEAF7FF),
      Color(0xFFF7F5FF),
      Color(0xFFFFFFFF),
    ],
    stops: [0, 0.38, 0.72, 1],
  );
}

/// Font-size scale — single source of truth for every numeric fontSize literal.
/// Values mirror the textTheme in theme.dart (those stay as-is; they're the
/// authoritative source). Add here any size that recurs in inline TextStyles.
abstract final class DsFontSize {
  static const double micro = 11;
  static const double caption = 12;
  static const double small = 12.5;
  static const double footnote = 13;
  static const double body = 14;
  static const double bodyLarge = 16;
  static const double title = 20;
  static const double headingSmall = 24;
  static const double headingMedium = 30;
  static const double display = 36;
}

/// Semantic const TextStyles for the recurring patterns found across the
/// design-system and feature files. Only styles that share a fixed color
/// everywhere they appear have color baked in; others rely on context.
abstract final class DsType {
  /// Table/grid header cell: footnote size, semibold, muted colour.
  static const tableHeader = TextStyle(
    fontSize: DsFontSize.footnote,
    fontWeight: FontWeight.w600,
    color: DsColors.textMuted,
  );

  /// Standard table data cell: body size, primary text colour.
  static const tableCell = TextStyle(
    fontSize: DsFontSize.body,
    color: DsColors.textPrimary,
  );

  /// Bold table data cell (e.g. row actions, prominent data).
  static const tableCellStrong = TextStyle(
    fontSize: DsFontSize.footnote,
    fontWeight: FontWeight.w600,
  );

  /// Caption / helper text: caption size, muted colour.
  static const caption = TextStyle(
    fontSize: DsFontSize.caption,
    color: DsColors.textMuted,
  );

  /// Micro label (nav-bar labels, tiny helpers): micro size, muted colour.
  static const micro = TextStyle(
    fontSize: DsFontSize.micro,
    color: DsColors.textMuted,
  );

  /// Footnote / secondary hint text: footnote size, secondary colour.
  static const footnote = TextStyle(
    fontSize: DsFontSize.footnote,
    color: DsColors.textSecondary,
  );

  /// Grid small label (batch-dialog weekday/day): small size, muted colour.
  static const gridSmall = TextStyle(
    fontSize: DsFontSize.small,
    color: DsColors.textMuted,
  );

  /// Grid column header in batch-dialog preset columns.
  static const gridHeader = TextStyle(
    fontSize: DsFontSize.small,
    fontWeight: FontWeight.w700,
    color: DsColors.textPrimary,
  );
}

/// Single source of truth for motion easing — every animation in the design
/// system uses one of these so transitions feel coordinated, not ad-hoc.
abstract final class DsCurve {
  /// Default for enter/move motion (Material "emphasized decelerate").
  static const standard = Cubic(0.2, 0.0, 0.0, 1.0);

  /// Symmetric ease for reversible motion (e.g. shimmer, nav pill).
  static const smooth = Curves.easeOutCubic;

  /// Accelerate-out for elements leaving the screen.
  static const exit = Cubic(0.4, 0.0, 1.0, 1.0);
}
