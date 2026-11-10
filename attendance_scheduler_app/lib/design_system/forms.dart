import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
    this.onDark = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final DsTone tone;

  /// On a dark surface (the login card's glass) the action is white.
  final bool onDark;

  @override
  Widget build(BuildContext context) {
    final color = onDark ? DsColors.surface : dsToneColors(tone).foreground;
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
    this.inputFormatters,
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
  final List<TextInputFormatter>? inputFormatters;
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
      inputFormatters: inputFormatters,
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
      // Fill the field and ellipsize long labels instead of overflowing.
      isExpanded: true,
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

  /// Full-window background photo of the customer's aircraft. [footer] sits
  /// on the dark glass: build it for a dark surface (`DsTextAction.onDark`).
  static const photoAsset = 'assets/images/login_aircraft.jpg';

  final String title;
  final String subtitle;
  final Widget form;
  final Widget footer;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // The photo fills the window (owner 2026-11-10); the form sits on
          // it in a frosted-glass card.
          const Image(
            key: Key('login-photo'),
            image: AssetImage(photoAsset),
            fit: BoxFit.cover,
            // Show more of the clouds below the aircraft than of the sky
            // above it: that is where the card sits.
            alignment: Alignment(0, 0.6),
            // The photo is smaller than a desktop window: smooth upscaling.
            filterQuality: FilterQuality.high,
            excludeFromSemantics: true,
          ),
          SafeArea(
            child: LayoutBuilder(
              builder: (context, constraints) {
                // Wide windows: lower right, the part of the photo the
                // aircraft leaves free. Narrow windows: centred.
                final wide = constraints.maxWidth >= DsBreakpoints.desktop;
                return Align(
                  alignment: wide
                      ? const Alignment(0.86, 0.9)
                      : Alignment.center,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(DsSpacing.x6),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 540),
                      child: DsLiquidGlassSurface(
                        padding: EdgeInsets.zero,
                        borderRadius: DsRadius.xxLarge,
                        blur: 14,
                        // Clear, dark glass on the photo (owner's reference
                        // 2026-11-10): a navy tint and a soft blur. Text
                        // that sits on the glass itself is white, so the
                        // tint is deep enough for it on a bright photo too
                        // (the current one is mostly white clouds).
                        tint: DsColors.textPrimary.withValues(alpha: 0.46),
                        uniformTint: true,
                        child: Padding(
                          padding: const EdgeInsets.all(DsSpacing.x10),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  // Shrinks beside the selector when the card
                                  // is narrow.
                                  const Flexible(
                                    child: DsBrandLogo(
                                      height: 38,
                                      onDark: true,
                                    ),
                                  ),
                                  const SizedBox(width: DsSpacing.x4),
                                  DsLanguageSelector(
                                    languageCode: languageCode,
                                    onChanged: onLanguageChanged,
                                  ),
                                ],
                              ),
                              const SizedBox(height: DsSpacing.x8),
                              Text(
                                title,
                                style: Theme.of(context)
                                    .textTheme
                                    .headlineMedium
                                    ?.copyWith(color: DsColors.surface),
                              ),
                              const SizedBox(height: DsSpacing.x2),
                              Text(
                                subtitle,
                                style: Theme.of(context).textTheme.bodyMedium
                                    ?.copyWith(
                                      color: DsColors.surface.withValues(
                                        alpha: 0.88,
                                      ),
                                    ),
                              ),
                              const SizedBox(height: DsSpacing.x8),
                              Theme(data: _onGlassTheme(context), child: form),
                              const SizedBox(height: DsSpacing.x4),
                              Center(child: footer),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// Theme for the form on the auth card's dark glass: field labels float
/// INSIDE the white field (an outlined field's label straddles its border and
/// would be half on the glass) and a field's error line is white.
ThemeData _onGlassTheme(BuildContext context) {
  final theme = Theme.of(context);
  const radius = BorderRadius.all(Radius.circular(DsRadius.medium));
  UnderlineInputBorder border(Color color, [double width = 0]) =>
      UnderlineInputBorder(
        borderRadius: radius,
        borderSide: width == 0
            ? BorderSide.none
            : BorderSide(color: color, width: width),
      );
  return theme.copyWith(
    inputDecorationTheme: theme.inputDecorationTheme.copyWith(
      contentPadding: const EdgeInsets.fromLTRB(14, 8, 14, 8),
      border: border(DsColors.borderStrong),
      enabledBorder: border(DsColors.borderStrong),
      focusedBorder: border(DsColors.primary, 2),
      errorBorder: border(DsColors.danger, 2),
      focusedErrorBorder: border(DsColors.danger, 2),
      errorStyle: const TextStyle(color: DsColors.surface),
    ),
  );
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
