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
