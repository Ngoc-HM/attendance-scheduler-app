/// Data model: maps backend [FlightPresetRead] JSON → domain data used by the UI.
///
/// Backend shape:
///   { "id": int, "label": str, "route": str|null, "flt_arr": int,
///     "flt_dep": int, "sta": "HH:MM:SS", "std": "HH:MM:SS",
///     "sort_order": int, "is_active": bool }
class FlightPresetModel {
  const FlightPresetModel({
    required this.id,
    required this.label,
    this.route,
    required this.fltArr,
    required this.fltDep,
    required this.sta,
    required this.std,
    required this.sortOrder,
    required this.isActive,
  });

  final int id;
  final String label;
  final String? route;
  final int fltArr;
  final int fltDep;

  /// Trimmed to "HH:MM" for display.
  final String sta;

  /// Trimmed to "HH:MM" for display.
  final String std;

  final int sortOrder;
  final bool isActive;

  factory FlightPresetModel.fromJson(Map<String, dynamic> json) =>
      FlightPresetModel(
        id: json['id'] as int,
        label: json['label'] as String,
        route: json['route'] as String?,
        fltArr: json['flt_arr'] as int,
        fltDep: json['flt_dep'] as int,
        sta: _trimSeconds(json['sta'] as String),
        std: _trimSeconds(json['std'] as String),
        sortOrder: json['sort_order'] as int,
        isActive: json['is_active'] as bool,
      );

  /// Backend expects "HH:MM:SS" — append ":00" if the stored value is "HH:MM".
  Map<String, dynamic> toJson() => {
        'label': label,
        'route': route,
        'flt_arr': fltArr,
        'flt_dep': fltDep,
        'sta': _appendSeconds(sta),
        'std': _appendSeconds(std),
        'sort_order': sortOrder,
        'is_active': isActive,
      };

  FlightPresetModel copyWith({
    int? id,
    String? label,
    String? route,
    int? fltArr,
    int? fltDep,
    String? sta,
    String? std,
    int? sortOrder,
    bool? isActive,
  }) =>
      FlightPresetModel(
        id: id ?? this.id,
        label: label ?? this.label,
        route: route ?? this.route,
        fltArr: fltArr ?? this.fltArr,
        fltDep: fltDep ?? this.fltDep,
        sta: sta ?? this.sta,
        std: std ?? this.std,
        sortOrder: sortOrder ?? this.sortOrder,
        isActive: isActive ?? this.isActive,
      );

  static String _trimSeconds(String raw) {
    final parts = raw.split(':');
    if (parts.length >= 2) return '${parts[0]}:${parts[1]}';
    return raw;
  }

  static String _appendSeconds(String hhmm) {
    // If already "HH:MM:SS" (length > 5), return as-is.
    if (hhmm.length > 5) return hhmm;
    return '$hhmm:00';
  }
}
