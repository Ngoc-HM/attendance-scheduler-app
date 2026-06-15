import 'dart:math' as math;
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
    final saturationFilter = settings.effectiveSaturation == 1
        ? null
        : ColorFilter.matrix(_saturationMatrix(settings.effectiveSaturation));
    final blurFilter = ImageFilter.blur(
      sigmaX: settings.effectiveBlur,
      sigmaY: settings.effectiveBlur,
      tileMode: TileMode.mirror,
    );
    final filter = saturationFilter == null
        ? blurFilter
        : ImageFilter.compose(inner: saturationFilter, outer: blurFilter);

    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: filter,
        child: CustomPaint(
          foregroundPainter: _LiquidGlassHighlightPainter(
            radius: radius,
            settings: settings,
          ),
          child: ColoredBox(
            color: settings.effectiveGlassColor,
            child: Opacity(
              opacity: settings.visibility.clamp(0, 1),
              child: child,
            ),
          ),
        ),
      ),
    );
  }

  static List<double> _saturationMatrix(double saturation) {
    const lumR = 0.299;
    const lumG = 0.587;
    const lumB = 0.114;
    final inverse = 1 - saturation;
    return [
      lumR * inverse + saturation,
      lumG * inverse,
      lumB * inverse,
      0,
      0,
      lumR * inverse,
      lumG * inverse + saturation,
      lumB * inverse,
      0,
      0,
      lumR * inverse,
      lumG * inverse,
      lumB * inverse + saturation,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
    ];
  }
}

class _LiquidGlassHighlightPainter extends CustomPainter {
  const _LiquidGlassHighlightPainter({
    required this.radius,
    required this.settings,
  });

  final double radius;
  final LiquidGlassSettings settings;

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;

    final bounds = Offset.zero & size;
    final path = Path()
      ..addRRect(
        RRect.fromRectAndRadius(
          bounds.deflate(1),
          Radius.circular(math.max(0, radius - 1)),
        ),
      );
    final x = math.cos(settings.lightAngle);
    final y = math.sin(settings.lightAngle);
    final light = settings.effectiveLightIntensity.clamp(0.0, 1.0);
    final ambient = settings.effectiveAmbientStrength.clamp(0.0, 1.0);
    final edge = (settings.effectiveThickness / 12).clamp(1.0, 2.2);
    final specular = LinearGradient(
      begin: Alignment(x, y),
      end: Alignment(-x, -y),
      colors: [
        Colors.white.withValues(alpha: 0.96 * light),
        Colors.white.withValues(alpha: 0.20 + ambient * 0.35),
        Colors.white.withValues(alpha: 0.06 + ambient * 0.18),
        Colors.white.withValues(alpha: 0.82 * light),
      ],
      stops: const [0, 0.28, 0.72, 1],
    ).createShader(bounds);

    canvas.drawPath(
      path,
      Paint()
        ..shader = specular
        ..style = PaintingStyle.stroke
        ..strokeWidth = edge,
    );

    final aberration = (settings.effectiveChromaticAberration * 180).clamp(
      0.0,
      2.4,
    );
    if (aberration > 0) {
      final fringeAlpha = (aberration / 2.4) * 0.28;
      canvas.save();
      canvas.translate(-aberration, 0);
      canvas.drawPath(
        path,
        Paint()
          ..color = const Color(0xFF38BDF8).withValues(alpha: fringeAlpha)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1,
      );
      canvas.restore();

      canvas.save();
      canvas.translate(aberration, 0);
      canvas.drawPath(
        path,
        Paint()
          ..color = const Color(0xFFC084FC).withValues(alpha: fringeAlpha)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1,
      );
      canvas.restore();
    }

    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(18, 1, math.max(0, size.width - 36), 1),
        const Radius.circular(1),
      ),
      Paint()
        ..shader = const LinearGradient(
          colors: [Color(0x00FFFFFF), Color(0xE6FFFFFF), Color(0x00FFFFFF)],
        ).createShader(bounds),
    );
  }

  @override
  bool shouldRepaint(covariant _LiquidGlassHighlightPainter oldDelegate) =>
      oldDelegate.radius != radius || oldDelegate.settings != settings;
}
