import 'dart:io';

import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/app_config.dart';

/// The newest build the server publishes (`GET /app/latest`).
class AppRelease extends Equatable {
  const AppRelease({
    required this.build,
    required this.version,
    this.minBuild = 0,
    this.notes = '',
    this.downloads = const {},
  });

  final int build;
  final String version;

  /// Builds below this must update before they can be used.
  final int minBuild;
  final String notes;

  /// platform ("windows" / "macos" / "linux") -> path under the API base.
  final Map<String, String> downloads;

  factory AppRelease.fromJson(Map<String, dynamic> json) => AppRelease(
    build: json['build'] as int,
    version: json['version'] as String? ?? '',
    minBuild: json['min_build'] as int? ?? 0,
    notes: json['notes'] as String? ?? '',
    downloads: {
      for (final e in (json['downloads'] as Map? ?? {}).entries)
        e.key as String: e.value as String,
    },
  );

  @override
  List<Object?> get props => [build, version, minBuild, notes, downloads];
}

/// What the updater found for this app.
class UpdateOffer {
  const UpdateOffer(this.release, {required this.mandatory});

  final AppRelease release;

  /// The running build is below the server's minimum: no "later" button.
  final bool mandatory;
}

/// Self-update for the desktop clients (owner 2026-11-15): ask the server
/// for the newest build, download this platform's package and install it in
/// place, then start the new app.
class AppUpdater {
  AppUpdater({Dio? dio, this.currentBuild = AppConfig.appBuild})
    : _dio = dio ?? Dio(BaseOptions(baseUrl: AppConfig.apiBaseUrl));

  final Dio _dio;

  /// This app's build number (0 = a development build: never updates).
  final int currentBuild;

  static String? get platform => Platform.isWindows
      ? 'windows'
      : Platform.isMacOS
      ? 'macos'
      : Platform.isLinux
      ? 'linux'
      : null;

  /// A newer build for this platform, or null (none, dev build, offline).
  Future<UpdateOffer?> check() async {
    final key = platform;
    if (currentBuild <= 0 || key == null) return null;
    try {
      final res = await _dio.get('/app/latest');
      if (res.data is! Map) return null;
      final release = AppRelease.fromJson(
        Map<String, dynamic>.from(res.data as Map),
      );
      if (release.build <= currentBuild ||
          !release.downloads.containsKey(key)) {
        return null;
      }
      return UpdateOffer(release, mandatory: currentBuild < release.minBuild);
    } catch (_) {
      return null; // an update check never blocks the app
    }
  }

  /// Downloads the package into a fresh temp folder; [onProgress] gets 0..1.
  Future<File> download(
    AppRelease release, {
    void Function(double)? onProgress,
  }) async {
    final key = platform!;
    final dir = await Directory.systemTemp.createTemp('roster_fra_update_');
    final name = switch (key) {
      'windows' => 'RosterFRA-Setup.exe',
      'macos' => 'update.zip',
      _ => 'update.tar.gz',
    };
    final file = File('${dir.path}${Platform.pathSeparator}$name');
    var expected = -1;
    await _dio.download(
      release.downloads[key]!,
      file.path,
      onReceiveProgress: (received, total) {
        expected = total;
        if (total > 0) onProgress?.call(received / total);
      },
    );
    if (expected > 0 && await file.length() != expected) {
      throw const FileSystemException('Incomplete update download');
    }
    return file;
  }

  /// Starts the installer / swap script detached, then quits this app.
  /// The new build starts by itself once it is in place.
  Future<void> installAndRestart(File package) async {
    switch (platform) {
      case 'windows':
        // The Inno Setup installer replaces the files and, when silent,
        // starts the app again (windows/installer/roster_fra.iss).
        await Process.start(
          package.path,
          ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'],
          mode: ProcessStartMode.detached,
        );
      case 'macos':
        // .../Roster.app/Contents/MacOS/<exe> -> the .app bundle.
        final bundle = File(Platform.resolvedExecutable).parent.parent.parent;
        await _runSwap(package, bundle.path, '''
ditto -x -k "\$PKG" "\$WORK/new"
NEW=\$(find "\$WORK/new" -maxdepth 1 -name '*.app' | head -n 1)
[ -n "\$NEW" ] || exit 1
rm -rf "\$TARGET"
mv "\$NEW" "\$TARGET"
xattr -dr com.apple.quarantine "\$TARGET" 2>/dev/null
open "\$TARGET"
''');
      case 'linux':
        final bundle = File(Platform.resolvedExecutable).parent;
        final exe = Platform.resolvedExecutable.split('/').last;
        await _runSwap(package, bundle.path, '''
mkdir -p "\$WORK/new"
tar -xzf "\$PKG" -C "\$WORK/new"
[ -d "\$WORK/new/bundle" ] || exit 1
cp -a "\$WORK/new/bundle/." "\$TARGET/"
nohup "\$TARGET/$exe" >/dev/null 2>&1 &
''');
    }
    exit(0);
  }

  /// Writes and starts a shell script that waits for this process to end,
  /// swaps the app in place and starts it again.
  Future<void> _runSwap(File package, String target, String body) async {
    final work = package.parent.path;
    final script = File('$work/swap.sh');
    await script.writeAsString('''
#!/bin/sh
PKG="${package.path}"
WORK="$work"
TARGET="$target"
while kill -0 $pid 2>/dev/null; do sleep 0.3; done
$body''');
    await Process.start('/bin/sh', [
      script.path,
    ], mode: ProcessStartMode.detached);
  }
}

final appUpdaterProvider = Provider<AppUpdater>((ref) => AppUpdater());
