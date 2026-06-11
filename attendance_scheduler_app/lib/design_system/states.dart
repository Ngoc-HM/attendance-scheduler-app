import 'package:flutter/material.dart';

import 'components.dart';
import 'forms.dart';
import 'tokens.dart';

class DsLoadingState extends StatelessWidget {
  const DsLoadingState({super.key, this.rows = 6});

  final int rows;

  @override
  Widget build(BuildContext context) {
    return DsSurface(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          const _DsSkeletonRow(height: 44, muted: true),
          for (var index = 0; index < rows; index++)
            const _DsSkeletonRow(height: 54),
        ],
      ),
    );
  }
}

class _DsSkeletonRow extends StatefulWidget {
  const _DsSkeletonRow({required this.height, this.muted = false});

  final double height;
  final bool muted;

  @override
  State<_DsSkeletonRow> createState() => _DsSkeletonRowState();
}

class _DsSkeletonRowState extends State<_DsSkeletonRow>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => Container(
        height: widget.height,
        padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x4),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: DsColors.border)),
        ),
        child: Row(
          children: [
            Expanded(flex: 3, child: _bar(widget.muted ? 0.42 : 0.28)),
            const SizedBox(width: DsSpacing.x6),
            Expanded(flex: 2, child: _bar(0.18)),
            const SizedBox(width: DsSpacing.x6),
            Expanded(child: _bar(0.22)),
          ],
        ),
      ),
    );
  }

  Widget _bar(double baseOpacity) {
    return FractionallySizedBox(
      alignment: Alignment.centerLeft,
      widthFactor: 0.78,
      child: Container(
        height: 12,
        decoration: BoxDecoration(
          color: DsColors.surfaceMuted.withValues(
            alpha: baseOpacity + (_controller.value * 0.35),
          ),
          borderRadius: BorderRadius.circular(DsRadius.small),
        ),
      ),
    );
  }
}

class DsErrorState extends StatelessWidget {
  const DsErrorState({
    super.key,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onRetry,
  });

  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return DsSurface(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: DsSpacing.x8),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              children: [
                const Icon(
                  Icons.error_outline,
                  size: 32,
                  color: DsColors.danger,
                ),
                const SizedBox(height: DsSpacing.x3),
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: DsSpacing.x2),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: DsSpacing.x5),
                DsSecondaryButton(
                  label: actionLabel,
                  icon: Icons.refresh,
                  onPressed: onRetry,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class DsEmptyState extends StatelessWidget {
  const DsEmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return DsSurface(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: DsSpacing.x8),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              children: [
                Icon(icon, size: 32, color: DsColors.primary),
                const SizedBox(height: DsSpacing.x3),
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: DsSpacing.x2),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: DsSpacing.x5),
                DsPrimaryButton(label: actionLabel, onPressed: onAction),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
