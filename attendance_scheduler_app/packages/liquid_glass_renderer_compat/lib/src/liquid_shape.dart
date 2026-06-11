abstract class LiquidShape {
  const LiquidShape();
}

class LiquidRoundedRectangle extends LiquidShape {
  const LiquidRoundedRectangle({required this.borderRadius});

  final double borderRadius;
}
