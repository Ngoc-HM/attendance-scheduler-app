import 'package:flutter/material.dart';

import 'tokens.dart';

/// Side-view line drawing of a twin-engine wide-body airliner, for the login
/// page's context panel (owner request 2026-11-10). Decorative only: it is
/// hidden from the accessibility tree and scales to the width it is given.
class DsAircraftLineArt extends StatelessWidget {
  const DsAircraftLineArt({super.key});

  /// Width / height of the drawing's design box.
  static const double aspectRatio = _designWidth / _designHeight;

  @override
  Widget build(BuildContext context) {
    return ExcludeSemantics(
      child: AspectRatio(
        aspectRatio: aspectRatio,
        child: const CustomPaint(painter: _AircraftPainter()),
      ),
    );
  }
}

const double _designWidth = 1000;
const double _designHeight = 250;

class _AircraftPainter extends CustomPainter {
  const _AircraftPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.width / _designWidth;
    canvas.save();
    // The design is drawn nose-left; mirrored so the aircraft flies to the
    // right, away from the text block above it.
    canvas.translate(size.width, 0);
    canvas.scale(-scale, scale);

    final line = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6 / scale
      ..strokeJoin = StrokeJoin.round
      ..strokeCap = StrokeCap.round
      ..color = DsColors.primaryHover.withValues(alpha: 0.72);
    final detail = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1 / scale
      ..strokeJoin = StrokeJoin.round
      ..strokeCap = StrokeCap.round
      ..color = DsColors.primaryHover.withValues(alpha: 0.42);
    // Shapes in front (wing, engine) hide the lines behind them.
    final cover = Paint()
      ..style = PaintingStyle.fill
      ..color = DsColors.primarySoft;

    // Far-side horizontal stabiliser and fin sit behind the fuselage.
    final fin = Path()
      ..moveTo(752, 104)
      ..cubicTo(800, 96, 850, 40, 892, 8)
      ..lineTo(948, 8)
      ..lineTo(928, 112);
    canvas.drawPath(fin, line);
    canvas.drawLine(const Offset(912, 10), const Offset(890, 106), detail);

    final fuselage = Path()
      ..moveTo(28, 150)
      ..cubicTo(36, 130, 76, 110, 130, 106)
      ..cubicTo(160, 104, 180, 104, 200, 104)
      ..lineTo(790, 104)
      ..cubicTo(860, 104, 930, 112, 976, 122)
      ..lineTo(976, 130)
      ..cubicTo(900, 146, 800, 170, 700, 176)
      ..lineTo(150, 176)
      ..cubicTo(96, 176, 44, 170, 28, 150)
      ..close();
    canvas.drawPath(fuselage, cover);
    canvas.drawPath(fuselage, line);

    // Cockpit glazing.
    final cockpit = Path()
      ..moveTo(68, 131)
      ..lineTo(98, 117)
      ..lineTo(124, 117)
      ..lineTo(124, 131)
      ..close();
    canvas.drawPath(cockpit, detail);
    canvas.drawLine(const Offset(100, 117), const Offset(102, 131), detail);

    // Doors, then the window line between them.
    const doors = [150.0, 352.0, 600.0, 790.0];
    for (final x in doors) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x, 124, 15, 34),
          const Radius.circular(4),
        ),
        detail,
      );
    }
    for (var x = 178.0; x < 780; x += 13) {
      final nearDoor = doors.any((d) => x > d - 9 && x < d + 24);
      if (!nearDoor) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromCenter(center: Offset(x, 134), width: 5, height: 7),
            const Radius.circular(2.5),
          ),
          detail,
        );
      }
    }

    // Near-side horizontal stabiliser.
    final stabiliser = Path()
      ..moveTo(842, 134)
      ..lineTo(962, 120)
      ..lineTo(994, 121)
      ..lineTo(994, 127)
      ..lineTo(880, 142)
      ..close();
    canvas.drawPath(stabiliser, cover);
    canvas.drawPath(stabiliser, line);

    // Near-side wing, swept back and down toward the viewer, with a winglet.
    final wing = Path()
      ..moveTo(398, 170)
      ..lineTo(592, 232)
      ..lineTo(644, 232)
      ..lineTo(566, 176)
      ..close();
    canvas.drawPath(wing, cover);
    canvas.drawPath(wing, line);
    final winglet = Path()
      ..moveTo(624, 232)
      ..lineTo(654, 202)
      ..lineTo(664, 202)
      ..lineTo(644, 232);
    canvas.drawPath(winglet, cover);
    canvas.drawPath(winglet, line);

    // Engine nacelle ahead of the wing's leading edge, on a short pylon.
    canvas.drawLine(const Offset(424, 193), const Offset(442, 184), detail);
    final exhaust = Path()
      ..moveTo(470, 199)
      ..lineTo(498, 208)
      ..lineTo(470, 217)
      ..close();
    canvas.drawPath(exhaust, cover);
    canvas.drawPath(exhaust, detail);
    final nacelle = Path()
      ..moveTo(382, 190)
      ..lineTo(468, 195)
      ..quadraticBezierTo(484, 208, 468, 221)
      ..lineTo(382, 226)
      ..quadraticBezierTo(370, 208, 382, 190)
      ..close();
    canvas.drawPath(nacelle, cover);
    canvas.drawPath(nacelle, line);
    final intake = Path()
      ..moveTo(394, 191)
      ..quadraticBezierTo(384, 208, 394, 225);
    canvas.drawPath(intake, detail);

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _AircraftPainter oldDelegate) => false;
}
