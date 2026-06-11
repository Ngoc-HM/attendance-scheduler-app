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
}
