import 'package:flutter/material.dart';

class DsNavigationDestination {
  const DsNavigationDestination({
    required this.path,
    required this.label,
    required this.icon,
  });

  final String path;
  final String label;
  final IconData icon;
}
