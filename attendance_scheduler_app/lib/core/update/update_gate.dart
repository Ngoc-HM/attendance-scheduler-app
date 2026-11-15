import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../design_system/design_system.dart';
import '../../i18n/app_localizations.dart';
import 'app_updater.dart';

/// Wraps the app: checks for a newer build at start and every hour, and
/// offers it in a small card over the app. "Update" downloads, installs and
/// restarts; a mandatory update has no "Later" (owner 2026-11-15).
class UpdateGate extends ConsumerStatefulWidget {
  const UpdateGate({super.key, required this.child});

  final Widget child;

  static const checkEvery = Duration(hours: 1);

  @override
  ConsumerState<UpdateGate> createState() => _UpdateGateState();
}

class _UpdateGateState extends ConsumerState<UpdateGate> {
  UpdateOffer? _offer;
  int? _dismissedBuild;
  double? _progress; // non-null while downloading
  bool _failed = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _check();
    _timer = Timer.periodic(UpdateGate.checkEvery, (_) => _check());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _check() async {
    if (_progress != null) return;
    final offer = await ref.read(appUpdaterProvider).check();
    if (!mounted || offer == null) return;
    if (!offer.mandatory && offer.release.build == _dismissedBuild) return;
    setState(() {
      _offer = offer;
      _failed = false;
    });
  }

  Future<void> _update() async {
    final updater = ref.read(appUpdaterProvider);
    setState(() {
      _progress = 0;
      _failed = false;
    });
    try {
      final package = await updater.download(
        _offer!.release,
        onProgress: (p) {
          if (mounted) setState(() => _progress = p);
        },
      );
      await updater.installAndRestart(package);
    } catch (_) {
      if (mounted) {
        setState(() {
          _progress = null;
          _failed = true;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final offer = _offer;
    if (offer == null) return widget.child;
    final l = AppLocalizations.of(context);
    final busy = _progress != null;
    return Stack(
      children: [
        widget.child,
        if (offer.mandatory) const ModalBarrier(color: Color(0x66000000)),
        Positioned(
          right: DsSpacing.x6,
          bottom: DsSpacing.x6,
          width: 360,
          child: Material(
            color: Colors.transparent,
            child: DsSurface(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    l.text('updateTitle'),
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: DsSpacing.x2),
                  Text(
                    _failed
                        ? l.text('updateFailed')
                        : busy
                        ? l.text('updateDownloading')
                        : offer.mandatory
                        ? l.text('updateMandatory')
                        : offer.release.notes.isNotEmpty
                        ? offer.release.notes
                        : l.updateVersion(offer.release.build),
                    style: TextStyle(
                      color: _failed ? DsColors.danger : DsColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: DsSpacing.x3),
                  if (busy)
                    LinearProgressIndicator(value: _progress)
                  else
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        if (!offer.mandatory)
                          TextButton(
                            onPressed: () => setState(() {
                              _dismissedBuild = offer.release.build;
                              _offer = null;
                            }),
                            child: Text(l.text('updateLater')),
                          ),
                        const SizedBox(width: DsSpacing.x2),
                        DsPrimaryButton(
                          label: l.text('updateNow'),
                          icon: Icons.system_update_alt,
                          onPressed: _update,
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
