import 'dart:math' as math;

import 'package:flutter/material.dart';

class LiquidGlassSettings {
  const LiquidGlassSettings({
    this.visibility = 1,
    this.thickness = 20,
    this.blur = 5,
    this.glassColor = const Color(0x00FFFFFF),
    this.chromaticAberration = 0.01,
    this.lightAngle = 0.5 * math.pi,
    this.lightIntensity = 0.5,
    this.ambientStrength = 0,
    this.refractiveIndex = 1.2,
    this.saturation = 1.5,
  });

  final double visibility;
  final double thickness;
  final double blur;
  final Color glassColor;
  final double chromaticAberration;
  final double lightAngle;
  final double lightIntensity;
  final double ambientStrength;
  final double refractiveIndex;
  final double saturation;

  double get effectiveThickness => thickness * visibility;
  double get effectiveBlur => blur * visibility;
  double get effectiveLightIntensity => lightIntensity * visibility;
  double get effectiveAmbientStrength => ambientStrength * visibility;
  double get effectiveSaturation => 1 + (saturation - 1) * visibility;
  double get effectiveChromaticAberration => chromaticAberration * visibility;
  Color get effectiveGlassColor =>
      glassColor.withValues(alpha: glassColor.a * visibility);
}
