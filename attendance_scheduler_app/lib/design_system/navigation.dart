import 'package:animations/animations.dart';
import 'package:flutter/material.dart';

import '../i18n/app_localizations.dart';
import 'components.dart';
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
                      child: _DsDirectionalTabTransition(
                        index: selectedIndex,
                        child: child,
                      ),
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
            title: Row(
              children: [
                const DsBrandMark(size: 32),
                const SizedBox(width: 10),
                Text(appTitle, style: Theme.of(context).textTheme.titleMedium),
              ],
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
              child: _DsDirectionalTabTransition(
                index: selectedIndex,
                child: child,
              ),
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

class _DsDirectionalTabTransition extends StatefulWidget {
  const _DsDirectionalTabTransition({required this.index, required this.child});

  final int index;
  final Widget child;

  @override
  State<_DsDirectionalTabTransition> createState() =>
      _DsDirectionalTabTransitionState();
}

class _DsDirectionalTabTransitionState
    extends State<_DsDirectionalTabTransition> {
  late int _previousIndex;
  // false → forward (selected a LOWER tab): new content slides in from the
  // RIGHT, old fades-through out to the left (right→left).
  // true  → reverse (selected a HIGHER tab): left→right.
  bool _reverse = false;

  @override
  void initState() {
    super.initState();
    _previousIndex = widget.index;
  }

  @override
  void didUpdateWidget(covariant _DsDirectionalTabTransition oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.index == _previousIndex) return;
    _reverse = widget.index < _previousIndex; // going up the nav order
    _previousIndex = widget.index;
  }

  @override
  Widget build(BuildContext context) {
    // Full-page directional slide: the whole page moves as one block.
    // Forward (selected a LOWER tab → higher index): new page slides in from
    // the RIGHT, old page exits LEFT (right→left). ``reverse`` flips it so
    // going UP (to a higher tab) slides left→right. A light fade smooths the
    // hand-off without the "zoom" of a shared-axis scale.
    return PageTransitionSwitcher(
      duration: DsDuration.pageTransition,
      reverse: _reverse,
      transitionBuilder: (child, primary, secondary) {
        final entering = Tween<Offset>(
          begin: const Offset(1, 0),
          end: Offset.zero,
        ).animate(CurvedAnimation(parent: primary, curve: DsCurve.standard));
        final leaving = Tween<Offset>(
          begin: Offset.zero,
          end: const Offset(-1, 0),
        ).animate(CurvedAnimation(parent: secondary, curve: DsCurve.standard));
        // Pure slide, no fade: each page is an opaque block that travels as a
        // single unit — the incoming page fully covers what it slides over.
        // While sliding we rasterize the page into ONE flat image so the
        // `BackdropFilter` blur inside glass surfaces is baked in and travels
        // WITH its frame; otherwise the blur re-samples the screen each frame
        // and visually lags behind the moving panels ("each element on its
        // own"). Live blur returns the moment the slide settles.
        return SlideTransition(
          position: leaving,
          child: SlideTransition(
            position: entering,
            child: _RasterWhileAnimating(
              primary: primary,
              secondary: secondary,
              child: child,
            ),
          ),
        );
      },
      child: KeyedSubtree(
        key: ValueKey(widget.index),
        // Opaque page-background travels WITH the content so the whole page
        // reads as one solid block, not loose widgets over a static backdrop.
        child: RepaintBoundary(
          child: DecoratedBox(
            decoration: const BoxDecoration(
              gradient: DsGradients.appBackground,
            ),
            child: widget.child,
          ),
        ),
      ),
    );
  }
}

/// Flattens [child] into a single rasterized image while either transition
/// animation is running, then drops back to the live widget tree once both
/// settle. This keeps the whole page moving as one block during the slide —
/// crucially baking the `BackdropFilter` blur of glass surfaces into the
/// snapshot so it can't lag behind its own frame.
class _RasterWhileAnimating extends StatefulWidget {
  const _RasterWhileAnimating({
    required this.primary,
    required this.secondary,
    required this.child,
  });

  final Animation<double> primary;
  final Animation<double> secondary;
  final Widget child;

  @override
  State<_RasterWhileAnimating> createState() => _RasterWhileAnimatingState();
}

class _RasterWhileAnimatingState extends State<_RasterWhileAnimating> {
  final SnapshotController _controller = SnapshotController();

  @override
  void initState() {
    super.initState();
    widget.primary.addStatusListener(_sync);
    widget.secondary.addStatusListener(_sync);
    _sync(AnimationStatus.dismissed);
  }

  @override
  void dispose() {
    widget.primary.removeStatusListener(_sync);
    widget.secondary.removeStatusListener(_sync);
    _controller.dispose();
    super.dispose();
  }

  bool _isMoving(Animation<double> a) =>
      a.status == AnimationStatus.forward ||
      a.status == AnimationStatus.reverse;

  void _sync(AnimationStatus _) {
    _controller.allowSnapshotting =
        _isMoving(widget.primary) || _isMoving(widget.secondary);
  }

  @override
  Widget build(BuildContext context) {
    return SnapshotWidget(controller: _controller, child: widget.child);
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
