import 'package:flutter/material.dart';

import '../i18n/app_localizations.dart';
import 'components.dart';
import 'liquid_navigation.dart';
import 'navigation_badge.dart';
import 'navigation_models.dart';
import 'tokens.dart';

class DsNavigationShell extends StatelessWidget {
  const DsNavigationShell({
    super.key,
    required this.appTitle,
    required this.productName,
    required this.destinations,
    required this.selectedIndex,
    required this.child,
    required this.onSelected,
    required this.onLogout,
    required this.logoutLabel,
    required this.languageCode,
    required this.onLanguageChanged,
    this.userName,
    this.userRole,
  });

  final String appTitle;
  final String productName;
  final List<DsNavigationDestination> destinations;
  final int selectedIndex;
  final Widget child;
  final ValueChanged<int> onSelected;
  final VoidCallback onLogout;
  final String logoutLabel;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;
  final String? userName;
  final String? userRole;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isDesktop = constraints.maxWidth >= DsBreakpoints.desktop;
        final isTablet = constraints.maxWidth >= DsBreakpoints.mobile;
        if (isDesktop || isTablet) {
          return Scaffold(
            backgroundColor: Colors.transparent,
            body: DsLiquidGlassBackdrop(
              padding: const EdgeInsets.all(DsSpacing.x3),
              child: Row(
                children: [
                  DsLiquidGlassSurface(
                    padding: EdgeInsets.zero,
                    borderRadius: DsRadius.xxLarge,
                    tint: DsColors.surface.withValues(alpha: 0.68),
                    child: _DsSideNavigation(
                      productName: productName,
                      destinations: destinations,
                      selectedIndex: selectedIndex,
                      extended: isDesktop,
                      userName: userName,
                      userRole: userRole,
                      logoutLabel: logoutLabel,
                      languageCode: languageCode,
                      onLanguageChanged: onLanguageChanged,
                      onSelected: onSelected,
                      onLogout: onLogout,
                    ),
                  ),
                  const SizedBox(width: DsSpacing.x3),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(DsRadius.xxLarge),
                      child: _DsTabPageBackground(child: child),
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          extendBody: true,
          backgroundColor: Colors.transparent,
          appBar: AppBar(
            backgroundColor: DsColors.surface.withValues(alpha: 0.76),
            surfaceTintColor: Colors.transparent,
            titleSpacing: DsSpacing.x2,
            title: Align(
              alignment: Alignment.centerLeft,
              child: DsBrandLogo(height: 22, semanticLabel: appTitle),
            ),
            actions: [
              DsLanguageSelector(
                languageCode: languageCode,
                onChanged: onLanguageChanged,
                compact: true,
              ),
              const SizedBox(width: DsSpacing.x1),
              IconButton(
                tooltip: logoutLabel,
                onPressed: onLogout,
                icon: const Icon(Icons.logout_outlined, size: 20),
              ),
              const SizedBox(width: DsSpacing.x2),
            ],
            bottom: const PreferredSize(
              preferredSize: Size.fromHeight(1),
              child: Divider(height: 1),
            ),
          ),
          body: DsLiquidGlassBackdrop(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 92),
              child: _DsTabPageBackground(child: child),
            ),
          ),
          bottomNavigationBar: DsLiquidNavigationBar(
            destinations: destinations,
            currentIndex: selectedIndex,
            onSelected: onSelected,
          ),
        );
      },
    );
  }
}

/// Wraps the active tab page in the opaque app-background so the page reads as
/// one solid block over the liquid-glass backdrop. Tab switches are
/// instantaneous on purpose: an AnimatedSwitcher/PageTransitionSwitcher here
/// would briefly keep TWO copies of go_router's ShellRoute `child` mounted, and
/// that child carries a stable `GlobalObjectKey` (go_router builder.dart) →
/// "Duplicate GlobalKey detected in widget tree". A static wrapper avoids it.
class _DsTabPageBackground extends StatelessWidget {
  const _DsTabPageBackground({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: DecoratedBox(
        decoration: const BoxDecoration(gradient: DsGradients.appBackground),
        child: child,
      ),
    );
  }
}

/// The customer's logo in the app shell header (owner request 2026-11-10):
/// the Vietnam Airlines wordmark, or only its lotus where the header is
/// narrow. Scales down to the width it is given.
class DsBrandLogo extends StatelessWidget {
  const DsBrandLogo({
    super.key,
    required this.height,
    this.markOnly = false,
    this.semanticLabel,
  });

  static const logoAsset = 'assets/images/vietnam_airlines_logo.png';
  static const markAsset = 'assets/images/vietnam_airlines_mark.png';

  final double height;
  final bool markOnly;
  final String? semanticLabel;

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      markOnly ? markAsset : logoAsset,
      height: height,
      fit: BoxFit.contain,
      filterQuality: FilterQuality.medium,
      semanticLabel: semanticLabel,
    );
  }
}

class _DsSideNavigation extends StatelessWidget {
  const _DsSideNavigation({
    required this.productName,
    required this.destinations,
    required this.selectedIndex,
    required this.extended,
    required this.onSelected,
    required this.onLogout,
    required this.logoutLabel,
    required this.languageCode,
    required this.onLanguageChanged,
    this.userName,
    this.userRole,
  });

  final String productName;
  final List<DsNavigationDestination> destinations;
  final int selectedIndex;
  final bool extended;
  final ValueChanged<int> onSelected;
  final VoidCallback onLogout;
  final String logoutLabel;
  final String languageCode;
  final ValueChanged<String> onLanguageChanged;
  final String? userName;
  final String? userRole;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SizedBox(
      width: extended ? 240 : 80,
      child: Column(
        children: [
          Container(
            height: 72,
            padding: EdgeInsets.symmetric(horizontal: extended ? DsSpacing.x5 : DsSpacing.x4),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: DsColors.border)),
            ),
            // The customer's logo stands for the product name here: the full
            // wordmark when the rail is wide, only the lotus when collapsed.
            alignment: extended ? Alignment.centerLeft : Alignment.center,
            child: DsBrandLogo(
              height: 28,
              markOnly: !extended,
              semanticLabel: productName,
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(
                horizontal: DsSpacing.x3,
                vertical: DsSpacing.x4,
              ),
              itemCount: destinations.length,
              separatorBuilder: (_, _) => const SizedBox(height: DsSpacing.x1),
              itemBuilder: (context, index) => _DsNavigationItem(
                item: destinations[index],
                selected: selectedIndex == index,
                extended: extended,
                onTap: () => onSelected(index),
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(DsSpacing.x3),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: DsColors.border)),
            ),
            child: Column(
              children: [
                Align(
                  alignment: Alignment.center,
                  child: DsLanguageSelector(
                    languageCode: languageCode,
                    onChanged: onLanguageChanged,
                    compact: !extended,
                  ),
                ),
                const SizedBox(height: DsSpacing.x3),
                if (extended)
                  Row(
                    children: [
                      DsUserAvatar(name: userName),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              userName ?? l.text('signedIn'),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodyMedium
                                  ?.copyWith(
                                    color: DsColors.textPrimary,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                            Text(
                              userRole ?? l.text('user'),
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: logoutLabel,
                        onPressed: onLogout,
                        icon: const Icon(Icons.logout, size: 20),
                      ),
                    ],
                  )
                else
                  Tooltip(
                    message: logoutLabel,
                    child: IconButton(
                      onPressed: onLogout,
                      icon: const Icon(Icons.logout, size: 20),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DsNavigationItem extends StatelessWidget {
  const _DsNavigationItem({
    required this.item,
    required this.selected,
    required this.extended,
    required this.onTap,
  });

  final DsNavigationDestination item;
  final bool selected;
  final bool extended;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = selected ? DsColors.primaryHover : DsColors.textSecondary;
    final badge = dsNavigationBadgeText(item.badgeCount);
    final countText = badge == null
        ? null
        : AppLocalizations.of(context).navPendingCount(item.badgeCount!);
    final icon = Icon(item.icon, color: color, size: 20);
    final content = Material(
      color: selected ? DsColors.primarySoft : Colors.transparent,
      borderRadius: BorderRadius.circular(DsRadius.medium),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(DsRadius.medium),
        child: Container(
          height: DsControlHeight.touch,
          padding: EdgeInsets.symmetric(horizontal: extended ? DsSpacing.x3 : 0),
          decoration: BoxDecoration(
            border: selected
                ? const Border(
                    right: BorderSide(color: DsColors.primary, width: 2),
                  )
                : null,
          ),
          child: Row(
            mainAxisAlignment: extended
                ? MainAxisAlignment.start
                : MainAxisAlignment.center,
            children: [
              if (badge != null && !extended)
                DsNavigationIconBadge(icon: icon, text: badge)
              else
                icon,
              if (extended) ...[
                const SizedBox(width: DsSpacing.x3),
                Expanded(
                  child: Text(
                    item.label,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: color,
                      fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                    ),
                  ),
                ),
                if (badge != null) ...[
                  const SizedBox(width: DsSpacing.x2),
                  DsNavigationCountPill(text: badge),
                ],
              ],
            ],
          ),
        ),
      ),
    );
    final label = countText == null ? item.label : '${item.label}, $countText';
    // One announcement per item, the count in words included; the tap
    // action is kept on the node itself.
    final tile = extended ? content : Tooltip(message: label, child: content);
    return Semantics(
      container: true,
      button: true,
      selected: selected,
      label: label,
      onTap: onTap,
      excludeSemantics: true,
      child: tile,
    );
  }
}

class DsUserAvatar extends StatelessWidget {
  const DsUserAvatar({super.key, this.name});

  final String? name;

  @override
  Widget build(BuildContext context) {
    final initial = (name?.trim().isNotEmpty ?? false)
        ? name!.trim().characters.first.toUpperCase()
        : 'U';
    return CircleAvatar(
      radius: 18,
      backgroundColor: DsColors.surfaceMuted,
      foregroundColor: DsColors.textSecondary,
      child: Text(initial, style: Theme.of(context).textTheme.labelLarge),
    );
  }
}
