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

class DsLiquidGlassSurface extends StatelessWidget {
  const DsLiquidGlassSurface({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(DsSpacing.x5),
    this.borderRadius = DsRadius.xLarge,
    this.blur = 22,
    this.tint = DsColors.glassBase,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final double blur;
  final Color tint;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(borderRadius);
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
              border: Border.all(color: DsColors.glassBorder, width: 1.4),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [DsColors.glassStrong, tint, DsColors.glassHighlight],
                stops: const [0, 0.5, 1],
              ),
            ),
            child: Stack(
              children: [
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
  });

  final String languageCode;
  final ValueChanged<String> onChanged;
  final bool compact;

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
        return Tooltip(
          message: l.language,
          child: DsLiquidGlassSurface(
            padding: EdgeInsets.zero,
            borderRadius: DsRadius.medium,
            blur: 14,
            tint: DsColors.surface.withValues(alpha: 0.56),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                key: const Key('language-selector'),
                onTap: controller.open,
                borderRadius: BorderRadius.circular(DsRadius.medium),
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: compact ? 10 : 12,
                    vertical: 9,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.language_outlined,
                        size: 18,
                        color: DsColors.primaryHover,
                      ),
                      if (!compact) ...[
                        const SizedBox(width: DsSpacing.x2),
                        Text(
                          selectedLabel,
                          style: Theme.of(context).textTheme.labelLarge,
                        ),
                      ],
                      const SizedBox(width: DsSpacing.x1),
                      const Icon(Icons.expand_more, size: 16),
                    ],
                  ),
                ),
              ),
            ),
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
            padding: EdgeInsets.fromLTRB(horizontal, 24, horizontal, 32),
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
              Wrap(
                spacing: DsSpacing.x2,
                runSpacing: DsSpacing.x2,
                children: actions,
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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

abstract final class DsFeedback {
  static void show(
    BuildContext context,
    String message, {
    DsTone tone = DsTone.primary,
  }) {
    final colors = dsToneColors(tone);
    final icon = switch (tone) {
      DsTone.success => Icons.check_circle_outline,
      DsTone.warning => Icons.warning_amber_outlined,
      DsTone.danger => Icons.error_outline,
      DsTone.primary => Icons.info_outline,
      DsTone.neutral => Icons.info_outline,
    };
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          duration: tone == DsTone.danger
              ? const Duration(seconds: 8)
              : const Duration(seconds: 4),
          backgroundColor: colors.background,
          content: Row(
            children: [
              Icon(icon, color: colors.foreground, size: 18),
              const SizedBox(width: DsSpacing.x2),
              Expanded(
                child: Text(
                  message,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: colors.foreground,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
  }
}
