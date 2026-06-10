/// Compile-time configuration.
///
/// Override the API base URL at build/run time:
///   flutter run -d windows --dart-define=API_BASE_URL=https://api.example.eu/api/v1
class AppConfig {
  const AppConfig._();

  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );
}
