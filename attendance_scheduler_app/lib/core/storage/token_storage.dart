import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

/// Persists the JWT access token between app starts.
///
/// Windows and Linux use the OS secure store (Credential Manager / libsecret).
/// macOS keeps it in a file only this user can read
/// (`~/Library/Application Support/<app>/session`, mode 600): the app
/// updates itself and is not signed with a stable certificate, so every new
/// build would trigger a login-keychain password prompt (owner 2026-11-15).
/// Any failure falls back to an in-memory copy for the current session.
class TokenStorage {
  TokenStorage([FlutterSecureStorage? storage, this._useFile])
    : _storage =
          storage ??
          const FlutterSecureStorage(
            mOptions: MacOsOptions(useDataProtectionKeyChain: false),
          );

  final FlutterSecureStorage _storage;

  /// Overrides the platform choice (tests); null = file on macOS only.
  final bool? _useFile;
  static const String _key = 'access_token';

  // Session fallback used when the store is unavailable.
  String? _memory;

  bool get _fileStore => _useFile ?? Platform.isMacOS;

  Future<File> _file() async {
    final dir = await getApplicationSupportDirectory();
    await dir.create(recursive: true);
    return File('${dir.path}${Platform.pathSeparator}session');
  }

  Future<void> save(String token) async {
    _memory = token;
    try {
      if (_fileStore) {
        final file = await _file();
        await file.writeAsString(token, flush: true);
        await Process.run('chmod', ['600', file.path]);
      } else {
        await _storage.write(key: _key, value: token);
      }
    } catch (_) {
      // Store unavailable — keep the in-memory copy.
    }
  }

  Future<String?> read() async {
    if (_memory != null) return _memory;
    try {
      if (_fileStore) {
        final file = await _file();
        if (!await file.exists()) return null;
        final token = (await file.readAsString()).trim();
        return token.isEmpty ? null : token;
      }
      return await _storage.read(key: _key);
    } catch (_) {
      return _memory;
    }
  }

  Future<void> clear() async {
    _memory = null;
    try {
      if (_fileStore) {
        final file = await _file();
        if (await file.exists()) await file.delete();
      } else {
        await _storage.delete(key: _key);
      }
    } catch (_) {
      // Ignore — nothing persisted.
    }
  }
}
