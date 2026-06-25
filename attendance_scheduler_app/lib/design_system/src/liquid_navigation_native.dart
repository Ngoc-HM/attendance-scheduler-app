import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:liquid_glass_bar/liquid_glass_bar.dart';

import '../navigation_models.dart';
import '../tokens.dart';

class DsLiquidNavigationBar extends StatelessWidget {
  const DsLiquidNavigationBar({
    super.key,
    required this.destinations,
    required this.currentIndex,
    required this.onSelected,
  });

  final List<DsNavigationDestination> destinations;
  final int currentIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return LiquidGlassBar(
      items: [
        for (final item in destinations)
          LiquidGlassBarItem(iconData: item.icon, label: item.label),
      ],
      currentIndex: currentIndex,
      onTap: onSelected,
      style: LiquidGlassBarStyle(
        activeColor: DsColors.primary,
        inactiveColor: DsColors.textPrimary,
        borderRadius: 32,
        height: 60,
        padding: const EdgeInsets.fromLTRB(DsSpacing.x4, 10, DsSpacing.x4, DsSpacing.x6),
        animationDuration: DsDuration.navigation,
        animationCurve: DsCurve.smooth,
        iconSize: 22,
        selectedIconScale: 1.2,
        labelStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: DsColors.textPrimary,
          fontSize: DsFontSize.micro,
          fontWeight: FontWeight.w700,
        ),
        liquidGlassSettings: LiquidGlassSettings(
          visibility: 1,
          glassColor: DsColors.surface.withValues(alpha: 0.18),
          thickness: 18,
          blur: 6,
          chromaticAberration: 0.012,
          lightAngle: 0.45 * math.pi,
          lightIntensity: 0.6,
          ambientStrength: 0.25,
          refractiveIndex: 1.25,
          saturation: 1.15,
        ),
      ),
    );
  }
}
