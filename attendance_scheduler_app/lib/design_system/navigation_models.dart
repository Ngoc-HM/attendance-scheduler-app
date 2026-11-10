import 'package:flutter/material.dart';

class DsNavigationDestination {
  const DsNavigationDestination({
    required this.path,
    required this.label,
    required this.icon,
    this.badgeCount,
  });

  final String path;
  final String label;
  final IconData icon;

  /// Items waiting for the user on this tab (owner 2026-11-10); no badge
  /// when null or 0.
  final int? badgeCount;
}
