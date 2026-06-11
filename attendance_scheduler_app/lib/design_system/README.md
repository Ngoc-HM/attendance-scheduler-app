# Design system boundary

All reusable UI belongs in this directory.

## Usage

- Feature presentation files import only `design_system.dart`.
- Feature pages own state, data mapping, and callbacks.
- Feature pages call a `Ds*View` or compose existing `Ds*` components.
- Add or extend a component here before using a new visual pattern.
- Keep tokens in `tokens.dart` and global Material defaults in `theme.dart`.
- Import `liquid_glass_bar` only in `src/liquid_navigation_native.dart`.

`test/design_system_boundary_test.dart` enforces the feature boundary.
