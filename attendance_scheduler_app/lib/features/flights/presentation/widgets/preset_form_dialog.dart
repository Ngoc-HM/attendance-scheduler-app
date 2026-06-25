import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../design_system/design_system.dart';
import '../../../../i18n/app_localizations.dart';
import '../../data/models/flight_preset_model.dart';

/// Add / Edit dialog for a [FlightPresetModel].
///
/// When [initial] is null a blank "Add" form is shown; otherwise the fields
/// are pre-filled for editing. On save, [onSave] is called with the filled
/// model; the caller is responsible for persisting it.
class PresetFormDialog extends StatefulWidget {
  const PresetFormDialog({
    super.key,
    this.initial,
    required this.onSave,
  });

  final FlightPresetModel? initial;
  final void Function(FlightPresetModel preset) onSave;

  @override
  State<PresetFormDialog> createState() => _PresetFormDialogState();
}

class _PresetFormDialogState extends State<PresetFormDialog> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _label;
  late final TextEditingController _route;
  late final TextEditingController _fltArr;
  late final TextEditingController _fltDep;
  late final TextEditingController _sortOrder;

  /// Stored as "HH:MM".
  late String _sta;
  late String _std;
  late bool _isActive;

  @override
  void initState() {
    super.initState();
    final p = widget.initial;
    _label = TextEditingController(text: p?.label ?? '');
    _route = TextEditingController(text: p?.route ?? '');
    _fltArr = TextEditingController(text: p != null ? '${p.fltArr}' : '');
    _fltDep = TextEditingController(text: p != null ? '${p.fltDep}' : '');
    _sortOrder = TextEditingController(
      text: p != null ? '${p.sortOrder}' : '0',
    );
    _sta = p?.sta ?? '06:00';
    _std = p?.std ?? '14:00';
    _isActive = p?.isActive ?? true;
  }

  @override
  void dispose() {
    _label.dispose();
    _route.dispose();
    _fltArr.dispose();
    _fltDep.dispose();
    _sortOrder.dispose();
    super.dispose();
  }

  Future<void> _pickTime({
    required String current,
    required ValueChanged<String> onPicked,
  }) async {
    final parts = current.split(':');
    final initial = TimeOfDay(
      hour: int.tryParse(parts[0]) ?? 0,
      minute: int.tryParse(parts.length > 1 ? parts[1] : '0') ?? 0,
    );
    final picked = await showTimePicker(context: context, initialTime: initial);
    if (picked != null) {
      onPicked(
        '${picked.hour.toString().padLeft(2, '0')}:'
        '${picked.minute.toString().padLeft(2, '0')}',
      );
    }
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    final preset = FlightPresetModel(
      id: widget.initial?.id ?? 0,
      label: _label.text.trim(),
      route: _route.text.trim().isEmpty ? null : _route.text.trim(),
      fltArr: int.parse(_fltArr.text.trim()),
      fltDep: int.parse(_fltDep.text.trim()),
      sta: _sta,
      std: _std,
      sortOrder: int.tryParse(_sortOrder.text.trim()) ?? 0,
      isActive: _isActive,
    );
    Navigator.of(context).pop();
    widget.onSave(preset);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final isEdit = widget.initial != null;

    return DsFormDialog(
      title: isEdit ? l.text('editPreset') : l.text('addPreset'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Label (required)
            TextFormField(
              controller: _label,
              decoration: InputDecoration(labelText: l.text('presetLabel')),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? l.fieldRequired : null,
            ),
            const SizedBox(height: DsSpacing.x4),
            // Route (optional)
            TextField(
              controller: _route,
              decoration: InputDecoration(labelText: l.text('presetRoute')),
            ),
            const SizedBox(height: DsSpacing.x4),
            // FLT ARR / FLT DEP
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _fltArr,
                    decoration: InputDecoration(labelText: l.text('fltArr')),
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    validator: (v) =>
                        (v == null || v.trim().isEmpty) ? l.fieldRequired : null,
                  ),
                ),
                const SizedBox(width: DsSpacing.x4),
                Expanded(
                  child: TextFormField(
                    controller: _fltDep,
                    decoration: InputDecoration(labelText: l.text('fltDep')),
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    validator: (v) =>
                        (v == null || v.trim().isEmpty) ? l.fieldRequired : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: DsSpacing.x4),
            // STA / STD time pickers
            Row(
              children: [
                Expanded(
                  child: _TimePickerField(
                    label: l.text('sta'),
                    value: _sta,
                    onTap: () => _pickTime(
                      current: _sta,
                      onPicked: (t) => setState(() => _sta = t),
                    ),
                  ),
                ),
                const SizedBox(width: DsSpacing.x4),
                Expanded(
                  child: _TimePickerField(
                    label: l.text('std'),
                    value: _std,
                    onTap: () => _pickTime(
                      current: _std,
                      onPicked: (t) => setState(() => _std = t),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: DsSpacing.x4),
            // Sort order (optional)
            TextField(
              controller: _sortOrder,
              decoration: InputDecoration(labelText: l.text('sortOrder')),
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            ),
            const SizedBox(height: DsSpacing.x2),
            // Active toggle
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(l.text('isActive')),
              value: _isActive,
              onChanged: (v) => setState(() => _isActive = v),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(l.cancel),
        ),
        DsPrimaryButton(
          label: l.text('save'),
          onPressed: _submit,
        ),
      ],
    );
  }
}

/// Read-only tappable field that shows "HH:MM" and opens a time picker.
class _TimePickerField extends StatelessWidget {
  const _TimePickerField({
    required this.label,
    required this.value,
    required this.onTap,
  });

  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(DsRadius.medium),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          suffixIcon: const Icon(Icons.access_time_outlined, size: 18),
        ),
        child: Text(value),
      ),
    );
  }
}
