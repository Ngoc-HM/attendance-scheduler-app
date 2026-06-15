import 'package:flutter/material.dart';

import '../i18n/app_localizations.dart';
import 'components.dart';
import 'navigation.dart';
import 'tokens.dart';

class DsPrimaryButton extends StatelessWidget {
  const DsPrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.loading = false,
    this.expand = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool loading;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final child = FilledButton(
      onPressed: loading ? null : onPressed,
      child: loading
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Row(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 18),
                  const SizedBox(width: DsSpacing.x2),
                ],
                Text(label),
              ],
            ),
    );
    return expand ? SizedBox(width: double.infinity, child: child) : child;
  }
}

class DsSecondaryButton extends StatelessWidget {
  const DsSecondaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.expand = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool expand;

  @override
  Widget build(BuildContext context) {
    final child = OutlinedButton(
      onPressed: onPressed,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 18),
            const SizedBox(width: DsSpacing.x2),
          ],
          Text(label),
        ],
      ),
    );
    return expand ? SizedBox(width: double.infinity, child: child) : child;
  }
}

class DsTextAction extends StatelessWidget {
  const DsTextAction({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.tone = DsTone.primary,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final DsTone tone;

  @override
  Widget build(BuildContext context) {
    final color = dsToneColors(tone).foreground;
    return TextButton(
      onPressed: onPressed,
      style: TextButton.styleFrom(foregroundColor: color),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 17),
            const SizedBox(width: DsSpacing.x2),
          ],
          Text(label),
        ],
      ),
    );
  }
}

class DsTextField extends StatelessWidget {
  const DsTextField({
    super.key,
    required this.controller,
    required this.label,
    this.validator,
    this.obscureText = false,
    this.onSubmitted,
    this.prefixIcon,
    this.keyboardType,
    this.hint,
    this.enabled = true,
  });

  final TextEditingController controller;
  final String label;
  final String? Function(String?)? validator;
  final bool obscureText;
  final ValueChanged<String>? onSubmitted;
  final IconData? prefixIcon;
  final TextInputType? keyboardType;
  final String? hint;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      validator: validator,
      obscureText: obscureText,
      onFieldSubmitted: onSubmitted,
      keyboardType: keyboardType,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: prefixIcon == null ? null : Icon(prefixIcon, size: 20),
      ),
    );
  }
}

class DsSelectField<T> extends StatelessWidget {
  const DsSelectField({
    super.key,
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String label;
  final T value;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?>? onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<T>(
      initialValue: value,
      decoration: InputDecoration(labelText: label),
      items: items,
      onChanged: onChanged,
    );
  }
}

class DsSelectOption<T> {
  const DsSelectOption({required this.value, required this.label});

  final T value;
  final String label;
}

class DsAuthPage extends StatelessWidget {
  const DsAuthPage({
    super.key,
    required this.title,
    required this.subtitle,
    required this.form,
    required this.footer,
    required this.languageCode,
    required this.onLanguageChanged,
  });

  final String title;
  final String subtitle;
  final Widget form;
  final Widget footer;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: DsLiquidGlassBackdrop(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(DsSpacing.x6),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1040),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final showContext =
                        constraints.maxWidth >= DsBreakpoints.desktop;
                    return DsLiquidGlassSurface(
                      padding: EdgeInsets.zero,
                      borderRadius: DsRadius.xxLarge,
                      tint: DsColors.surface.withValues(alpha: 0.62),
                      child: IntrinsicHeight(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (showContext)
                              const Expanded(child: _DsAuthContextPanel()),
                            Expanded(
                              child: Padding(
                                padding: const EdgeInsets.all(DsSpacing.x8),
                                child: ConstrainedBox(
                                  constraints: const BoxConstraints(
                                    maxWidth: 420,
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          const DsBrandMark(size: 44),
                                          const Spacer(),
                                          DsLanguageSelector(
                                            languageCode: languageCode,
                                            onChanged: onLanguageChanged,
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: DsSpacing.x6),
                                      Text(
                                        title,
                                        style: Theme.of(
                                          context,
                                        ).textTheme.headlineMedium,
                                      ),
                                      const SizedBox(height: DsSpacing.x2),
                                      Text(
                                        subtitle,
                                        style: Theme.of(
                                          context,
                                        ).textTheme.bodyMedium,
                                      ),
                                      const SizedBox(height: DsSpacing.x8),
                                      form,
                                      const SizedBox(height: DsSpacing.x4),
                                      Center(child: footer),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DsAuthContextPanel extends StatelessWidget {
  const _DsAuthContextPanel();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            DsColors.primarySoft.withValues(alpha: 0.88),
            DsColors.surface.withValues(alpha: 0.36),
          ],
        ),
        border: const Border(right: BorderSide(color: DsColors.glassBorder)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(DsSpacing.x8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              l.productName,
              style: Theme.of(
                context,
              ).textTheme.headlineMedium?.copyWith(color: DsColors.textPrimary),
            ),
            const SizedBox(height: DsSpacing.x3),
            Text(
              l.text('authPanelSubtitle'),
              style: Theme.of(
                context,
              ).textTheme.bodyLarge?.copyWith(color: DsColors.textSecondary),
            ),
            const SizedBox(height: DsSpacing.x8),
            _DsFeatureLine(
              icon: Icons.auto_awesome_outlined,
              label: l.text('authFeatureSchedule'),
            ),
            const SizedBox(height: DsSpacing.x4),
            _DsFeatureLine(
              icon: Icons.balance_outlined,
              label: l.text('authFeatureBalance'),
            ),
            const SizedBox(height: DsSpacing.x4),
            _DsFeatureLine(
              icon: Icons.fact_check_outlined,
              label: l.text('authFeatureAttendance'),
            ),
          ],
        ),
      ),
    );
  }
}

class _DsFeatureLine extends StatelessWidget {
  const _DsFeatureLine({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: DsColors.primary, size: 20),
        const SizedBox(width: DsSpacing.x3),
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: DsColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class DsFormDialog extends StatelessWidget {
  const DsFormDialog({
    super.key,
    required this.title,
    required this.content,
    required this.actions,
    this.width = 480,
  });

  final String title;
  final Widget content;
  final List<Widget> actions;
  final double width;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(title),
      content: SizedBox(width: width, child: content),
      actions: actions,
    );
  }
}
