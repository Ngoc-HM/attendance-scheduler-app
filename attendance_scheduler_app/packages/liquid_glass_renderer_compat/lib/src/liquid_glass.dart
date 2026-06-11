import 'dart:ui';

import 'package:flutter/material.dart';

import 'liquid_glass_settings.dart';
import 'liquid_shape.dart';

class LiquidGlass extends StatelessWidget {
  const LiquidGlass.withOwnLayer({
    super.key,
    required this.shape,
    required this.child,
    this.settings = const LiquidGlassSettings(),
  });

  final LiquidShape shape;
  final LiquidGlassSettings settings;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final radius = switch (shape) {
      LiquidRoundedRectangle(:final borderRadius) => borderRadius,
      _ => 0.0,
    };
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: settings.blur, sigmaY: settings.blur),
        child: ColoredBox(color: settings.glassColor, child: child),
      ),
    );
  }
}
