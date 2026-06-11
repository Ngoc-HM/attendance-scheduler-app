import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

/// Persists the JWT access token in the OS secure store.
///
/// Production target is Windows desktop (Credential Manager — works out of the
/// box). On macOS the app sandbox blocks the data-protection Keychain unless
/// the app is signed with a development certificate, so we disable it
/// (`useDataProtectionKeyChain: false`) and additionally fall back to in-memory
/// storage if the platform call still fails — keeping login working for the
/// current session during local dev.
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage])
    : _storage =
          storage ??
          const FlutterSecureStorage(
            mOptions: MacOsOptions(useDataProtectionKeyChain: false),
          );

  final FlutterSecureStorage _storage;
  static const String _key = 'access_token';

  // Session fallback used when the secure store is unavailable.
  String? _memory;

  Future<void> save(String token) async {
    _memory = token;
    try {
      await _storage.write(key: _key, value: token);
    } catch (_) {
      // Secure store unavailable (e.g. macOS dev) — keep the in-memory copy.
    }
  }

  Future<String?> read() async {
    if (_memory != null) return _memory;
    try {
      return await _storage.read(key: _key);
    } catch (_) {
      return _memory;
    }
  }

  Future<void> clear() async {
    _memory = null;
    try {
      await _storage.delete(key: _key);
    } catch (_) {
      // Ignore — nothing persisted.
    }
  }
}
