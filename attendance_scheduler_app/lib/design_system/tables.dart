import 'package:flutter/material.dart';

import 'tokens.dart';

/// Column definition for [DsDataTable].
class DsTableColumn {
  const DsTableColumn({
    required this.header,
    required this.flex,
    this.alignment = Alignment.centerLeft,
  });

  /// Header label string.
  final String header;

  /// Flex weight for this column (same unit as Expanded flex).
  final int flex;

  /// Alignment applied to every cell widget in this column.
  final AlignmentGeometry alignment;
}

/// Reusable fixed-size cell for custom grids (e.g. the month-batch preset grid).
///
/// Kept in the design system so feature code does not recreate Container +
/// BoxDecoration combinations. Borders are configurable per edge so frozen/scroll
/// bands can share the same visual cell and stay pixel-aligned.
class DsGridCell extends StatelessWidget {
  const DsGridCell({
    super.key,
    required this.width,
    required this.height,
    this.background,
    this.rightBorder = false,
    this.bottomBorder = true,
    this.alignment = Alignment.center,
    this.padding = EdgeInsets.zero,
    this.child,
  });

  final double width;
  final double height;
  final Color? background;
  final bool rightBorder;
  final bool bottomBorder;
  final AlignmentGeometry alignment;
  final EdgeInsetsGeometry padding;
  final Widget? child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      alignment: alignment,
      padding: padding,
      decoration: BoxDecoration(
        color: background,
        border: Border(
          bottom: bottomBorder
              ? const BorderSide(color: DsColors.border)
              : BorderSide.none,
          right: rightBorder
              ? const BorderSide(color: DsColors.border)
              : BorderSide.none,
        ),
      ),
      child: child,
    );
  }
}

/// A reusable static-data table that renders a header row + data rows with
/// consistent padding, light dividers, optional zebra striping, and token-based
/// colours/text styles. Columns are distributed via [Expanded] flex weights.
///
/// This is intentionally simple — for complex interactive grids (e.g. checkbox
/// matrices) keep the specialised widget and just apply design tokens manually.
class DsDataTable extends StatelessWidget {
  const DsDataTable({
    super.key,
    required this.columns,
    required this.rows,
    this.zebra = false,
    this.cellPaddingH = DsSpacing.x5,
    this.cellPaddingV = DsSpacing.x4,
  });

  /// Column definitions — length must equal each row's cell count.
  final List<DsTableColumn> columns;

  /// Each row is a list of cell widgets, one per column.
  final List<List<Widget>> rows;

  /// Whether to apply subtle alternating row tint on odd rows.
  final bool zebra;

  /// Horizontal cell padding (defaults to [DsSpacing.x5]).
  final double cellPaddingH;

  /// Vertical cell padding (defaults to [DsSpacing.x4]).
  final double cellPaddingV;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _buildHeaderRow(),
        for (var i = 0; i < rows.length; i++) ...[
          const Divider(height: 1, color: DsColors.border),
          _buildDataRow(rows[i], striped: zebra && i.isOdd),
        ],
      ],
    );
  }

  Widget _buildHeaderRow() {
    return Container(
      color: DsColors.surfaceSubtle,
      padding: EdgeInsets.symmetric(
        horizontal: cellPaddingH,
        vertical: cellPaddingV,
      ),
      child: Row(
        children: [
          for (final col in columns)
            Expanded(
              flex: col.flex,
              child: Align(
                alignment: col.alignment,
                child: Text(col.header, style: DsType.tableHeader),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDataRow(List<Widget> cells, {bool striped = false}) {
    assert(
      cells.length == columns.length,
      'DsDataTable: row has ${cells.length} cells but table has '
      '${columns.length} columns.',
    );
    return Container(
      color: striped ? DsColors.surfaceSubtle.withValues(alpha: 0.5) : null,
      padding: EdgeInsets.symmetric(
        horizontal: cellPaddingH,
        vertical: cellPaddingV,
      ),
      child: Row(
        children: [
          for (var i = 0; i < columns.length; i++)
            Expanded(
              flex: columns[i].flex,
              child: Align(
                alignment: columns[i].alignment,
                child: cells[i],
              ),
            ),
        ],
      ),
    );
  }
}
