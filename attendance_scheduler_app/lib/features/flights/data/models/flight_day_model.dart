/// Data model: maps backend [FlightDayRead] JSON → domain data used by the UI.
///
/// Backend shape:
///   { "id": int, "day": "YYYY-MM-DD", "flight_pairs": 0|1|2,
///     "flights": [FlightRead, ...] }
class FlightDayModel {
  const FlightDayModel({
    required this.id,
    required this.day,
    required this.flightPairs,
    this.flights = const [],
  });

  final int id;
  final DateTime day;
  final int flightPairs;

  /// Individual flight legs for this day (arrival + departure per pair).
  final List<FlightModel> flights;

  factory FlightDayModel.fromJson(Map<String, dynamic> json) => FlightDayModel(
    id: json['id'] as int,
    day: DateTime.parse(json['day'] as String),
    flightPairs: json['flight_pairs'] as int,
    flights: (json['flights'] as List<dynamic>? ?? [])
        .map((e) => FlightModel.fromJson(e as Map<String, dynamic>))
        .toList(),
  );
}

/// Data model: maps backend [FlightRead] JSON → domain data.
///
/// Backend shape:
///   { "id": int, "day": "YYYY-MM-DD", "flt_number": int,
///     "route": str|null, "sta": "HH:MM:SS"|null, "std": "HH:MM:SS"|null }
class FlightModel {
  const FlightModel({
    required this.id,
    required this.day,
    required this.fltNumber,
    this.route,
    this.sta,
    this.std,
  });

  final int id;
  final DateTime day;
  final int fltNumber;
  final String? route;
  final String? sta;
  final String? std;

  factory FlightModel.fromJson(Map<String, dynamic> json) => FlightModel(
    id: json['id'] as int,
    day: DateTime.parse(json['day'] as String),
    fltNumber: json['flt_number'] as int,
    route: json['route'] as String?,
    sta: _trimSeconds(json['sta'] as String?),
    std: _trimSeconds(json['std'] as String?),
  );

  /// Backend returns "HH:MM:SS" — trim to "HH:MM" for display.
  static String? _trimSeconds(String? raw) {
    if (raw == null) return null;
    final parts = raw.split(':');
    if (parts.length >= 2) return '${parts[0]}:${parts[1]}';
    return raw;
  }
}
