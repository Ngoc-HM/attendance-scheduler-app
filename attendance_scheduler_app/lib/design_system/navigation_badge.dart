import 'package:flutter/material.dart';

import 'components.dart';
import 'tokens.dart';

/// Pending-item counts on navigation items (owner 2026-11-10): nothing for
/// null or 0, the number up to 99, then "99+".
String? dsNavigationBadgeText(int? count) {
  if (count == null || count <= 0) return null;
  return count > 99 ? '99+' : '$count';
}

/// Wide side rail: the count as a [DsBadge] pill after the label. The digits
/// are excluded from semantics; the item announces the count in words.
class DsNavigationCountPill extends StatelessWidget {
  const DsNavigationCountPill({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: DsBadge(label: text, tone: DsTone.warning),
    );
  }
}

/// Collapsed rail and phone bar: [icon] with the count on its top-right
/// corner. The badge paints outside the icon's box, so the icon keeps its
/// size and position and nothing is laid out wider.
class DsNavigationIconBadge extends StatelessWidget {
  const DsNavigationIconBadge({
    super.key,
    required this.icon,
    required this.text,
  });

  final Widget icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = dsToneColors(DsTone.warning);
    return Stack(
      clipBehavior: Clip.none,
      alignment: Alignment.center,
      children: [
        icon,
        Positioned(
          top: -DsSpacing.x2,
          left: DsSpacing.x3,
          child: ExcludeSemantics(
            child: DecoratedBox(
              decoration: ShapeDecoration(
                color: colors.foreground,
                shape: const StadiumBorder(
                  side: BorderSide(color: DsColors.surface, width: 1.5),
                ),
              ),
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  minWidth: DsSpacing.x4,
                  minHeight: DsSpacing.x4,
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: DsSpacing.x1),
                  child: Center(
                    widthFactor: 1,
                    heightFactor: 1,
                    child: Text(
                      text,
                      maxLines: 1,
                      style: DsType.micro.copyWith(
                        color: DsColors.surface,
                        fontWeight: FontWeight.w700,
                        height: 1.2,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
