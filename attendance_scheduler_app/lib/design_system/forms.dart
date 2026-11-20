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
    this.maxLines = 1,
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

  /// Lines the field shows (a short note: 2). Must be 1 when obscured.
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      maxLines: maxLines,
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

/// A light two-or-more-way switch: equal-width segments in one outlined
/// track, the selected one in the primary tint with primary text. Labels
/// stay on one line (ellipsized if the track is too narrow).
class DsSegmentedSwitch<T> extends StatelessWidget {
  const DsSegmentedSwitch({
    super.key,
    required this.options,
    required this.value,
    required this.onChanged,
  });

  final List<DsSelectOption<T>> options;
  final T value;
  final ValueChanged<T> onChanged;

  static const double height = 36;

  @override
  Widget build(BuildContext context) {
    final textStyle = Theme.of(context).textTheme.bodySmall?.copyWith(
      fontSize: 13,
    );
    return Container(
      height: height,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: DsColors.surface,
        borderRadius: BorderRadius.circular(DsRadius.medium),
        border: Border.all(color: DsColors.borderStrong),
      ),
      child: Row(
        children: [
          for (final option in options)
            Expanded(
              child: Semantics(
                button: true,
                selected: option.value == value,
                child: Material(
                  color: option.value == value
                      ? DsColors.primarySoft
                      : DsColors.surface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(DsRadius.small + 1),
                    side: option.value == value
                        ? BorderSide(
                            color: DsColors.primary.withValues(alpha: 0.25),
                          )
                        : BorderSide.none,
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: InkWell(
                    onTap: option.value == value
                        ? null
                        : () => onChanged(option.value),
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: DsSpacing.x1,
                        ),
                        child: Text(
                          option.label,
                          maxLines: 1,
                          softWrap: false,
                          overflow: TextOverflow.ellipsis,
                          style: textStyle?.copyWith(
                            color: option.value == value
                                ? DsColors.primary
                                : DsColors.textSecondary,
                            fontWeight: option.value == value
                                ? FontWeight.w600
                                : FontWeight.w500,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class DsAuthPage extends StatelessWidget {
  const DsAuthPage({
    super.key,
    required this.title,
    this.subtitle,
    required this.form,
    required this.footer,
    required this.languageCode,
    required this.onLanguageChanged,
  });

  /// Full-window background photo of the customer's aircraft. [footer] sits
  /// on the dark glass: build it for a dark surface (`DsTextAction.onDark`).
  static const photoAsset = 'assets/images/login_aircraft.jpg';

  final String title;

  /// One line under the title; null = none (the login needs no explanation).
  final String? subtitle;
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
                      ? const Alignment(0.86, 0.68)
                      : Alignment.center,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(DsSpacing.x6),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 540),
                      child: DsLiquidGlassSurface(
                        padding: EdgeInsets.zero,
                        borderRadius: DsRadius.xxLarge,
                        blur: 4,
                        // Clear glass on the photo (owner's reference
                        // 2026-11-10): almost no tint and a light blur, so
                        // the photo shows through; the edge and a sheen at
                        // the top-left make it read as glass. Text that sits
                        // on the glass itself is white.
                        tint: DsColors.surface.withValues(alpha: 0.05),
                        uniformTint: true,
                        edgeLight: true,
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
                                    onDark: true,
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
                              if (subtitle != null) ...[
                                const SizedBox(height: DsSpacing.x2),
                                Text(
                                  subtitle!,
                                  style: Theme.of(context).textTheme.bodyMedium
                                      ?.copyWith(
                                        color: DsColors.surface.withValues(
                                          alpha: 0.88,
                                        ),
                                      ),
                                ),
                              ],
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

/// Shows a dialog WITHOUT dimming the page, for a [DsFormDialog] placed in
/// a corner (`alignment: Alignment.topLeft`): the person keeps reading the
/// page while filling the form (customer 2026-11-18).
Future<T?> showDsCornerDialog<T>({
  required BuildContext context,
  required WidgetBuilder builder,
}) => showDialog<T>(
  context: context,
  barrierColor: Colors.transparent,
  builder: builder,
);

class DsFormDialog extends StatelessWidget {
  const DsFormDialog({
    super.key,
    required this.title,
    required this.content,
    required this.actions,
    this.width = 480,
    this.alignment,
    this.subtitle,
  });

  final String title;
  final Widget content;
  final List<Widget> actions;

  /// Width of [content]; the card adds its own padding around it.
  final double width;

  /// Where the dialog sits in the window; null = centred. A dialog the
  /// person fills in while reading the page behind it (a shift-change
  /// request over the roster) goes to a corner, see [showDsCornerDialog].
  /// A corner dialog is a floating card: the page is not dimmed, so the
  /// card carries its own border and soft shadow to stand off the page.
  final AlignmentGeometry? alignment;

  /// One muted line under the title (e.g. the day the form is about).
  final String? subtitle;

  @override
  Widget build(BuildContext context) {
    final titleWidget = subtitle == null
        ? Text(title)
        : Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title),
              const SizedBox(height: DsSpacing.x1),
              Text(
                subtitle!,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: DsColors.textSecondary),
              ),
            ],
          );
    if (alignment == null) {
      return AlertDialog(
        insetPadding: const EdgeInsets.symmetric(horizontal: 40, vertical: 24),
        title: titleWidget,
        content: SizedBox(width: width, child: content),
        actions: actions,
      );
    }
    return _DsFloatingFormCard(
      alignment: alignment!,
      title: title,
      subtitle: subtitle,
      width: width,
      content: content,
      actions: actions,
    );
  }
}

/// The corner variant of [DsFormDialog]: surface, border, rounded corners
/// and a soft shadow, hugging its corner so it covers as little as possible.
class _DsFloatingFormCard extends StatelessWidget {
  const _DsFloatingFormCard({
    required this.alignment,
    required this.title,
    required this.subtitle,
    required this.width,
    required this.content,
    required this.actions,
  });

  final AlignmentGeometry alignment;
  final String title;
  final String? subtitle;
  final double width;
  final Widget content;
  final List<Widget> actions;

  static const double _padding = DsSpacing.x5;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return SafeArea(
      child: Align(
        alignment: alignment,
        child: Padding(
          padding: const EdgeInsets.all(DsSpacing.x3),
          child: Semantics(
            scopesRoute: true,
            explicitChildNodes: true,
            namesRoute: true,
            label: title,
            child: Material(
              type: MaterialType.transparency,
              child: Container(
                // Content width + padding + the 1 px border on each side.
                width: width + 2 * _padding + 2,
                decoration: BoxDecoration(
                  color: DsColors.surface,
                  borderRadius: BorderRadius.circular(DsRadius.xLarge),
                  border: Border.all(color: DsColors.border),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x1F0F172A),
                      blurRadius: 32,
                      offset: Offset(0, 12),
                    ),
                    BoxShadow(
                      color: Color(0x140F172A),
                      blurRadius: 6,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(_padding),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        title,
                        style: textTheme.titleMedium?.copyWith(
                          color: DsColors.textPrimary,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (subtitle != null) ...[
                        const SizedBox(height: DsSpacing.x1),
                        Text(
                          subtitle!,
                          style: textTheme.bodyMedium?.copyWith(
                            color: DsColors.textSecondary,
                          ),
                        ),
                      ],
                      const SizedBox(height: DsSpacing.x4),
                      content,
                      const SizedBox(height: DsSpacing.x4),
                      // Right-aligned; stacks only if the labels cannot
                      // fit on one line (as AlertDialog's actions do).
                      OverflowBar(
                        alignment: MainAxisAlignment.end,
                        overflowAlignment: OverflowBarAlignment.end,
                        spacing: DsSpacing.x2,
                        overflowSpacing: DsSpacing.x2,
                        children: actions,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
