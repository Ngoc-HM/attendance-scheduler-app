import 'dart:async';
import 'dart:ui';

import 'package:flutter/material.dart';

import '../core/constants/shift_codes.dart';
import '../i18n/app_localizations.dart';
import 'tokens.dart';

class DsLiquidGlassBackdrop extends StatelessWidget {
  const DsLiquidGlassBackdrop({
    super.key,
    required this.child,
    this.padding = EdgeInsets.zero,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(gradient: DsGradients.appBackground),
      child: Stack(
        fit: StackFit.expand,
        children: [
          const Positioned(
            top: -120,
            right: -70,
            child: _DsGlassGlow(
              size: 340,
              colors: [Color(0x667DD3FC), Color(0x007DD3FC)],
            ),
          ),
          const Positioned(
            bottom: -160,
            left: -90,
            child: _DsGlassGlow(
              size: 400,
              colors: [Color(0x4DC4B5FD), Color(0x00C4B5FD)],
            ),
          ),
          Padding(padding: padding, child: child),
        ],
      ),
    );
  }
}

class _DsGlassGlow extends StatelessWidget {
  const _DsGlassGlow({required this.size, required this.colors});

  final double size;
  final List<Color> colors;

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(colors: colors),
        ),
      ),
    );
  }
}

/// The light on a glass pane's edge: a nearly clear outline, a bright glint
/// running from the top-left corner along the top and left sides, a fainter
/// one at the bottom-right, each with a soft halo.
class _GlassEdgeLightPainter extends CustomPainter {
  const _GlassEdgeLightPainter(this.radius);

  final double radius;

  @override
  void paint(Canvas canvas, Size size) {
    final edge = RRect.fromRectAndRadius(
      (Offset.zero & size).deflate(0.6),
      Radius.circular(radius),
    );
    const light = DsColors.surface;
    final glint = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        light,
        light.withValues(alpha: 0.42),
        light.withValues(alpha: 0),
        light.withValues(alpha: 0),
        light.withValues(alpha: 0.5),
      ],
      stops: const [0, 0.2, 0.42, 0.74, 1],
    ).createShader(Offset.zero & size);

    // The clear outline, all the way round.
    canvas.drawRRect(
      edge,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1
        ..color = light.withValues(alpha: 0.2),
    );
    // The halo of the glint, then the glint itself.
    canvas.drawRRect(
      edge,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 4
        ..shader = glint
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5),
    );
    canvas.drawRRect(
      edge,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4
        ..shader = glint,
    );
  }

  @override
  bool shouldRepaint(_GlassEdgeLightPainter oldDelegate) =>
      oldDelegate.radius != radius;
}

class DsLiquidGlassSurface extends StatelessWidget {
  const DsLiquidGlassSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(DsSpacing.x5),
    this.borderRadius = DsRadius.xLarge,
    this.blur = 22,
    this.tint = DsColors.glassBase,
    this.uniformTint = false,
    this.edgeLight = false,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final double blur;
  final Color tint;

  /// Paint [tint] evenly instead of the default strong-to-light gradient:
  /// a clearer pane for glass that sits on a photo (the login card).
  final bool uniformTint;

  /// Replace the solid white border by a nearly clear edge that catches the
  /// light: bright at the top-left corner, fading along the sides, with a
  /// fainter glint at the bottom-right (the login card).
  final bool edgeLight;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(borderRadius);
    final surface = _surface(radius);
    if (!edgeLight) return surface;
    return CustomPaint(
      foregroundPainter: _GlassEdgeLightPainter(borderRadius),
      child: surface,
    );
  }

  Widget _surface(BorderRadius radius) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: radius,
        boxShadow: [
          BoxShadow(
            color: DsColors.primary.withValues(alpha: 0.12),
            blurRadius: 32,
            offset: const Offset(0, 14),
            spreadRadius: -10,
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: tint,
              borderRadius: radius,
              border: edgeLight
                  ? null
                  : Border.all(color: DsColors.glassBorder, width: 1.4),
              gradient: edgeLight
                  // A pane lit from the top-left: a faint sheen there,
                  // fading into the plain tint.
                  ? LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        DsColors.surface.withValues(alpha: 0.16),
                        tint,
                        tint,
                      ],
                      stops: const [0, 0.45, 1],
                    )
                  : uniformTint
                  ? null
                  : LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [
                        DsColors.glassStrong,
                        tint,
                        DsColors.glassHighlight,
                      ],
                      stops: const [0, 0.5, 1],
                    ),
            ),
            child: Stack(
              children: [
                if (!edgeLight)
                  Positioned(
                    top: 0,
                    left: 18,
                    right: 18,
                    child: IgnorePointer(
                      child: Container(
                        height: 1,
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              Color(0x00FFFFFF),
                              Color(0xFFFFFFFF),
                              Color(0x00FFFFFF),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                Padding(padding: padding, child: child),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class DsLanguageSelector extends StatelessWidget {
  const DsLanguageSelector({
    super.key,
    required this.languageCode,
    required this.onChanged,
    this.compact = false,
    this.onDark = false,
  });

  final String languageCode;
  final ValueChanged<String> onChanged;
  final bool compact;

  /// On a dark surface (the login card's glass): a clear pill with white
  /// text and icons instead of the light, frosted one.
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final selectedLabel = languageCode == 'vi' ? l.vietnamese : l.english;

    return MenuAnchor(
      menuChildren: [
        MenuItemButton(
          leadingIcon: languageCode == 'en'
              ? const Icon(Icons.check, size: 18)
              : const SizedBox(width: 18),
          onPressed: () => onChanged('en'),
          child: Text(l.english),
        ),
        MenuItemButton(
          leadingIcon: languageCode == 'vi'
              ? const Icon(Icons.check, size: 18)
              : const SizedBox(width: 18),
          onPressed: () => onChanged('vi'),
          child: Text(l.vietnamese),
        ),
      ],
      builder: (context, controller, child) {
        final button = Material(
          color: Colors.transparent,
          child: InkWell(
            key: const Key('language-selector'),
            onTap: controller.open,
            borderRadius: BorderRadius.circular(DsRadius.medium),
            child: Padding(
              // Compact: 9 so icon + chevron (38) fit the collapsed
              // rail's 56 px (10 overflowed it by 2 px).
              padding: EdgeInsets.symmetric(
                horizontal: compact ? 9 : 12,
                vertical: 9,
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.language_outlined,
                    size: 18,
                    color: onDark ? DsColors.surface : DsColors.primaryHover,
                  ),
                  if (!compact) ...[
                    const SizedBox(width: DsSpacing.x2),
                    Text(
                      selectedLabel,
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: onDark ? DsColors.surface : null,
                      ),
                    ),
                  ],
                  const SizedBox(width: DsSpacing.x1),
                  Icon(
                    Icons.expand_more,
                    size: 16,
                    color: onDark ? DsColors.surface : null,
                  ),
                ],
              ),
            ),
          ),
        );
        return Tooltip(
          message: l.language,
          child: onDark
              // On the dark glass card: a plain rounded outline, as clear
              // as the card, with no glass light of its own.
              ? DecoratedBox(
                  decoration: BoxDecoration(
                    color: DsColors.surface.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(DsRadius.medium),
                    border: Border.all(
                      color: DsColors.surface.withValues(alpha: 0.6),
                    ),
                  ),
                  child: button,
                )
              : DsLiquidGlassSurface(
                  padding: EdgeInsets.zero,
                  borderRadius: DsRadius.medium,
                  blur: 14,
                  tint: DsColors.surface.withValues(alpha: 0.56),
                  child: button,
                ),
        );
      },
    );
  }
}

class DsPage extends StatelessWidget {
  const DsPage({
    super.key,
    required this.title,
    required this.child,
    this.subtitle,
    this.actions = const [],
    this.maxWidth = double.infinity,
  });

  final String title;
  final String? subtitle;
  final List<Widget> actions;
  final Widget child;

  /// Optional content cap. Defaults to [double.infinity] so pages fill the
  /// full available width (no centered side-gutters); pass a finite value only
  /// for content that reads better centered (e.g. narrow forms).
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: LayoutBuilder(
        builder: (context, constraints) {
          final horizontal = constraints.maxWidth < DsBreakpoints.mobile
              ? 16.0
              : 24.0;
          final content = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              DsPageHeader(title: title, subtitle: subtitle, actions: actions),
              const SizedBox(height: DsSpacing.x6),
              child,
            ],
          );
          return SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(
              horizontal,
              DsSpacing.x6,
              horizontal,
              DsSpacing.x8,
            ),
            // Fill the full width by default; only center when a finite cap is set.
            child: maxWidth.isFinite
                ? Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: BoxConstraints(maxWidth: maxWidth),
                      child: content,
                    ),
                  )
                : content,
          );
        },
      ),
    );
  }
}

class DsPageHeader extends StatelessWidget {
  const DsPageHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.actions = const [],
  });

  final String title;
  final String? subtitle;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    final titleBlock = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.headlineMedium),
        if (subtitle != null) ...[
          const SizedBox(height: DsSpacing.x1),
          Text(subtitle!, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ],
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < DsBreakpoints.mobile && actions.isNotEmpty) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              titleBlock,
              const SizedBox(height: DsSpacing.x4),
              Wrap(
                spacing: DsSpacing.x2,
                runSpacing: DsSpacing.x2,
                children: actions,
              ),
            ],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: titleBlock),
            if (actions.isNotEmpty) ...[
              const SizedBox(width: DsSpacing.x6),
              // A Wrap in a Row gets unbounded width and never wraps: with
              // many actions it squeezed the title to nothing and overflowed.
              // Capped, the actions wrap onto a second (right-aligned) line
              // and the title keeps at least a third of the header.
              ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: constraints.maxWidth * 2 / 3,
                ),
                child: Wrap(
                  alignment: WrapAlignment.end,
                  spacing: DsSpacing.x2,
                  runSpacing: DsSpacing.x2,
                  children: actions,
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}

class DsSurface extends StatelessWidget {
  const DsSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(DsSpacing.x5),
    this.color = DsColors.surface,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(DsRadius.large),
        border: Border.all(color: DsColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A0F172A),
            blurRadius: 2,
            offset: Offset(0, 1),
          ),
        ],
      ),
      child: child,
    );
  }
}

class DsSectionHeader extends StatelessWidget {
  const DsSectionHeader(this.title, {super.key, this.trailing});

  final String title;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(title, style: Theme.of(context).textTheme.titleLarge),
        ),
        ?trailing,
      ],
    );
  }
}

class DsMetricCard extends StatelessWidget {
  const DsMetricCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    this.tone = DsTone.neutral,
  });

  final String label;
  final String value;
  final IconData icon;
  final DsTone tone;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(tone);
    return DsSurface(
      padding: const EdgeInsets.all(DsSpacing.x4),
      color: colors.background,
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: DsSpacing.x1),
                Text(
                  value,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: colors.foreground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          Icon(icon, color: colors.foreground, size: 28),
        ],
      ),
    );
  }
}

class DsBadge extends StatelessWidget {
  const DsBadge({
    super.key,
    required this.label,
    this.tone = DsTone.neutral,
    this.icon,
  });

  final String label;
  final DsTone tone;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(tone);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: DsSpacing.x2,
        vertical: DsSpacing.x1,
      ),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(DsRadius.small),
        border: Border.all(color: colors.foreground.withValues(alpha: 0.18)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 14, color: colors.foreground),
            const SizedBox(width: 5),
          ],
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: colors.foreground,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class DsResponsiveGrid extends StatelessWidget {
  const DsResponsiveGrid({
    super.key,
    required this.children,
    this.minItemWidth = 220,
    this.spacing = DsSpacing.x3,
  });

  final List<Widget> children;
  final double minItemWidth;
  final double spacing;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final count = (constraints.maxWidth / minItemWidth).floor().clamp(
          1,
          children.length,
        );
        final width = (constraints.maxWidth - (spacing * (count - 1))) / count;
        return Wrap(
          spacing: spacing,
          runSpacing: spacing,
          children: [
            for (final child in children) SizedBox(width: width, child: child),
          ],
        );
      },
    );
  }
}

/// Previous / next year, the year in between (same look as
/// [DsMonthSwitcher]).
class DsYearSwitcher extends StatelessWidget {
  const DsYearSwitcher({
    super.key,
    required this.year,
    required this.onPrevious,
    required this.onNext,
  });

  final int year;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Container(
      height: DsControlHeight.medium,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(DsRadius.medium),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            tooltip: l.text('previousYear'),
            onPressed: onPrevious,
            icon: const Icon(Icons.chevron_left, size: 20),
          ),
          SizedBox(
            width: 64,
            child: Text(
              '$year',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          ),
          IconButton(
            tooltip: l.text('nextYear'),
            onPressed: onNext,
            icon: const Icon(Icons.chevron_right, size: 20),
          ),
        ],
      ),
    );
  }
}

class DsMonthSwitcher extends StatelessWidget {
  const DsMonthSwitcher({
    super.key,
    required this.month,
    required this.onPrevious,
    required this.onNext,
  });

  final DateTime month;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Container(
      height: DsControlHeight.medium,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(DsRadius.medium),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            tooltip: l.text('previousMonth'),
            onPressed: onPrevious,
            icon: const Icon(Icons.chevron_left, size: 20),
          ),
          SizedBox(
            width: 112,
            child: Text(
              l.monthYear(month),
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelLarge,
            ),
          ),
          IconButton(
            tooltip: l.text('nextMonth'),
            onPressed: onNext,
            icon: const Icon(Icons.chevron_right, size: 20),
          ),
        ],
      ),
    );
  }
}

class DsShiftBadge extends StatelessWidget {
  const DsShiftBadge({super.key, required this.code, this.compact = false});

  final ShiftCode code;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final colors = switch (code) {
      ShiftCode.a ||
      ShiftCode.d ||
      ShiftCode.ad => dsToneColors(DsTone.primary),
      ShiftCode.aD => dsToneColors(DsTone.warning),
      ShiftCode.x || ShiftCode.cd => dsToneColors(DsTone.neutral),
      ShiftCode.s => dsToneColors(DsTone.danger),
      ShiftCode.al => dsToneColors(DsTone.success),
      ShiftCode.oD || ShiftCode.t || ShiftCode.b => const DsToneColors(
        DsColors.surfaceSubtle,
        DsColors.textSecondary,
      ),
    };
    return Container(
      constraints: BoxConstraints(minWidth: compact ? 30 : 38),
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 5 : 7,
        vertical: compact ? 3 : 4,
      ),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(DsRadius.small),
        border: Border.all(color: colors.foreground.withValues(alpha: 0.2)),
      ),
      child: Text(
        code.code,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: colors.foreground,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class DsTableFrame extends StatelessWidget {
  const DsTableFrame({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(DsRadius.large),
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: DsColors.surface,
          border: Border.all(color: DsColors.border),
          borderRadius: BorderRadius.circular(DsRadius.large),
        ),
        child: child,
      ),
    );
  }
}

class DsInlineAlert extends StatelessWidget {
  const DsInlineAlert({
    super.key,
    required this.title,
    required this.message,
    this.tone = DsTone.primary,
    this.action,
  });

  final String title;
  final String message;
  final DsTone tone;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(tone);
    final icon = switch (tone) {
      DsTone.success => Icons.check_circle_outline,
      DsTone.warning => Icons.warning_amber_outlined,
      DsTone.danger => Icons.error_outline,
      DsTone.primary => Icons.info_outline,
      DsTone.neutral => Icons.info_outline,
    };
    return Container(
      padding: const EdgeInsets.all(DsSpacing.x4),
      decoration: BoxDecoration(
        color: colors.background,
        borderRadius: BorderRadius.circular(DsRadius.medium),
        border: Border.all(color: colors.foreground.withValues(alpha: 0.18)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: colors.foreground, size: 20),
          const SizedBox(width: DsSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colors.foreground,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: DsSpacing.x1),
                Text(
                  message,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(color: colors.foreground),
                ),
              ],
            ),
          ),
          if (action != null) ...[const SizedBox(width: DsSpacing.x3), action!],
        ],
      ),
    );
  }
}

enum DsTone { neutral, primary, success, warning, danger }

class DsToneColors {
  const DsToneColors(this.background, this.foreground);

  final Color background;
  final Color foreground;
}

DsToneColors dsToneColors(DsTone tone) => switch (tone) {
  DsTone.primary => const DsToneColors(
    DsColors.primarySoft,
    DsColors.primaryHover,
  ),
  DsTone.success => const DsToneColors(DsColors.successSoft, DsColors.success),
  DsTone.warning => const DsToneColors(DsColors.warningSoft, DsColors.warning),
  DsTone.danger => const DsToneColors(DsColors.dangerSoft, DsColors.danger),
  DsTone.neutral => const DsToneColors(
    DsColors.surfaceSubtle,
    DsColors.textSecondary,
  ),
};

/// Blocking "please wait" overlay for slow actions (owner 2026-07-18: the
/// schedule solve runs up to ~30s and the button gave no feedback, so users
/// thought the app had frozen). [DsBusy.run] shows a dimmed, non-dismissible
/// dialog with a spinner + message, runs the action, then always closes it.
abstract final class DsBusy {
  static Future<T> run<T>(
    BuildContext context,
    String message,
    Future<T> Function() action,
  ) async {
    final navigator = Navigator.of(context, rootNavigator: true);
    // Fire-and-forget: the barrier stays up until we pop it below.
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x59000000),
      builder: (_) => const _DsBusyDialog(),
      routeSettings: RouteSettings(arguments: message),
    );
    try {
      return await action();
    } finally {
      if (navigator.canPop()) navigator.pop();
    }
  }
}

class _DsBusyDialog extends StatelessWidget {
  const _DsBusyDialog();

  @override
  Widget build(BuildContext context) {
    final message = ModalRoute.of(context)?.settings.arguments as String? ?? '';
    // Back-button / swipe must not dismiss a critical in-flight operation.
    return PopScope(
      canPop: false,
      child: Dialog(
        backgroundColor: DsColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(DsRadius.large),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: DsSpacing.x6,
            vertical: DsSpacing.x5,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2.5),
              ),
              const SizedBox(width: DsSpacing.x4),
              Flexible(
                child: Text(
                  message,
                  style: const TextStyle(
                    fontSize: DsFontSize.body,
                    fontWeight: FontWeight.w600,
                    color: DsColors.textPrimary,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// App-wide toast, anchored TOP-RIGHT (owner 2026-07-17: "mọi noti để ở góc
/// trên bên phải"). Overlay-based so it floats above every page; a new toast
/// replaces the current one; tap to dismiss early.
abstract final class DsFeedback {
  static OverlayEntry? _entry;
  static Timer? _timer;

  static void show(
    BuildContext context,
    String message, {
    DsTone tone = DsTone.primary,
  }) {
    final overlay = Overlay.of(context, rootOverlay: true);
    final colors = dsToneColors(tone);
    final icon = switch (tone) {
      DsTone.success => Icons.check_circle_outline,
      DsTone.warning => Icons.warning_amber_outlined,
      DsTone.danger => Icons.error_outline,
      DsTone.primary => Icons.info_outline,
      DsTone.neutral => Icons.info_outline,
    };

    _dismiss();
    final entry = OverlayEntry(
      builder: (_) => Positioned(
        top: DsSpacing.x4,
        right: DsSpacing.x4,
        child: Material(
          color: const Color(0x00000000),
          child: GestureDetector(
            onTap: _dismiss,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: DsSpacing.x4,
                  vertical: DsSpacing.x3,
                ),
                decoration: BoxDecoration(
                  color: colors.background,
                  borderRadius: BorderRadius.circular(DsRadius.medium),
                  border: Border.all(
                    color: colors.foreground.withValues(alpha: 0.25),
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x1F0F172A),
                      blurRadius: 12,
                      offset: Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, color: colors.foreground, size: 18),
                    const SizedBox(width: DsSpacing.x2),
                    Flexible(
                      child: Text(
                        message,
                        maxLines: 4,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: DsFontSize.footnote,
                          color: colors.foreground,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
    overlay.insert(entry);
    _entry = entry;
    // Errors and warnings carry consequences — give them longer to be read.
    _timer = Timer(
      tone == DsTone.danger || tone == DsTone.warning
          ? const Duration(seconds: 8)
          : const Duration(seconds: 4),
      _dismiss,
    );
  }

  static void _dismiss() {
    _timer?.cancel();
    _timer = null;
    _entry?.remove();
    _entry = null;
  }
}
