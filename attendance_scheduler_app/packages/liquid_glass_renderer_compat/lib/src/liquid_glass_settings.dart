import 'package:flutter/material.dart';

class LiquidGlassSettings {
  const LiquidGlassSettings({
    this.thickness = 20,
    this.blur = 16,
    this.glassColor = const Color(0xCCFFFFFF),
    this.lightIntensity = 0.6,
    this.refractiveIndex = 1.5,
  });

  final double thickness;
  final double blur;
  final Color glassColor;
  final double lightIntensity;
  final double refractiveIndex;
}
