import 'package:flutter/material.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';

/// Edits one person's annual leave quota (owner decision D4). Starts from
/// [quota] and pops the new value in days (0–365), or null when cancelled.
class EditQuotaDialog extends StatefulWidget {
  const EditQuotaDialog({
    super.key,
    required this.username,
    required this.quota,
  });

  final String username;
  final int quota;

  @override
  State<EditQuotaDialog> createState() => _EditQuotaDialogState();
}

class _EditQuotaDialogState extends State<EditQuotaDialog> {
  final _formKey = GlobalKey<FormState>();
  late final _quota = TextEditingController(text: '${widget.quota}');

  @override
  void dispose() {
    _quota.dispose();
    super.dispose();
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.of(context).pop(int.parse(_quota.text.trim()));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return DsFormDialog(
      title: '${l.text('editAnnualLeaveQuota')}: ${widget.username}',
      width: 380,
      content: Form(
        key: _formKey,
        child: DsAnnualLeaveQuotaField(
          controller: _quota,
          label: l.text('annualLeaveQuota'),
          invalidMessage: l.text('annualLeaveQuotaInvalid'),
        ),
      ),
      actions: [
        DsTextAction(
          label: l.cancel,
          onPressed: () => Navigator.of(context).pop(),
        ),
        DsPrimaryButton(label: l.text('save'), onPressed: _save),
      ],
    );
  }
}
