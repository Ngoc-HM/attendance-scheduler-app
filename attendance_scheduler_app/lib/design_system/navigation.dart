import 'package:flutter/material.dart';

import 'liquid_navigation.dart';
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
            body: Row(
              children: [
                _DsSideNavigation(
                  productName: productName,
                  destinations: destinations,
                  selectedIndex: selectedIndex,
                  extended: isDesktop,
                  userName: userName,
                  userRole: userRole,
                  logoutLabel: logoutLabel,
                  onSelected: onSelected,
                  onLogout: onLogout,
                ),
                Expanded(child: child),
              ],
            ),
          );
        }

        return Scaffold(
          extendBody: true,
          appBar: AppBar(
            titleSpacing: DsSpacing.x2,
            title: Row(
              children: [
                const DsBrandMark(size: 32),
                const SizedBox(width: 10),
                Text(appTitle, style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            actions: [
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
          body: Padding(
            padding: const EdgeInsets.only(bottom: 88),
            child: child,
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

class DsBrandMark extends StatelessWidget {
  const DsBrandMark({super.key, required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: DsColors.primary,
        borderRadius: BorderRadius.circular(DsRadius.medium),
      ),
      child: Icon(
        Icons.flight_takeoff_outlined,
        color: Colors.white,
        size: size * 0.55,
      ),
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
  final String? userName;
  final String? userRole;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: extended ? 240 : 80,
      color: DsColors.surface,
      child: Column(
        children: [
          Container(
            height: 72,
            padding: EdgeInsets.symmetric(horizontal: extended ? 20 : 16),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: DsColors.border)),
            ),
            child: Row(
              mainAxisAlignment: extended
                  ? MainAxisAlignment.start
                  : MainAxisAlignment.center,
              children: [
                const DsBrandMark(size: 36),
                if (extended) ...[
                  const SizedBox(width: DsSpacing.x3),
                  Expanded(
                    child: Text(
                      productName,
                      style: Theme.of(context).textTheme.titleMedium,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ],
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
            child: extended
                ? Row(
                    children: [
                      DsUserAvatar(name: userName),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              userName ?? 'Signed in',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodyMedium
                                  ?.copyWith(
                                    color: DsColors.textPrimary,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                            Text(
                              userRole ?? 'User',
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
                : Tooltip(
                    message: logoutLabel,
                    child: IconButton(
                      onPressed: onLogout,
                      icon: const Icon(Icons.logout, size: 20),
                    ),
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
    final content = Material(
      color: selected ? DsColors.primarySoft : Colors.transparent,
      borderRadius: BorderRadius.circular(DsRadius.medium),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(DsRadius.medium),
        child: Container(
          height: DsControlHeight.touch,
          padding: EdgeInsets.symmetric(horizontal: extended ? 12 : 0),
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
              Icon(item.icon, color: color, size: 20),
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
              ],
            ],
          ),
        ),
      ),
    );
    return extended ? content : Tooltip(message: item.label, child: content);
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
