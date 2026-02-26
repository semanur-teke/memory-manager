import 'package:flutter/material.dart';
import '../theme/colors.dart';

/// Silme/cascade onay diyalogu.
/// Tehlikeli islemlerde cift onay mekanizmasi.
/// requireTextInput=true olursa kullanici "SIL" yazmadan onaylayamaz.
class ConfirmDialog extends StatefulWidget {
  final String title;
  final String message;
  final String confirmText;
  final bool requireTextInput;
  final String? requiredInput; // "SIL" gibi

  const ConfirmDialog({
    super.key,
    required this.title,
    required this.message,
    this.confirmText = 'Onayla',
    this.requireTextInput = false,
    this.requiredInput,
  });

  /// Diyalogu goster ve sonucu don
  static Future<bool?> show(
    BuildContext context, {
    required String title,
    required String message,
    String confirmText = 'Onayla',
    bool requireTextInput = false,
    String? requiredInput,
  }) {
    return showDialog<bool>(
      context: context,
      builder: (_) => ConfirmDialog(
        title: title,
        message: message,
        confirmText: confirmText,
        requireTextInput: requireTextInput,
        requiredInput: requiredInput,
      ),
    );
  }

  @override
  State<ConfirmDialog> createState() => _ConfirmDialogState();
}

class _ConfirmDialogState extends State<ConfirmDialog> {
  final _controller = TextEditingController();
  bool _canConfirm = false;

  @override
  void initState() {
    super.initState();
    _canConfirm = !widget.requireTextInput;
    if (widget.requireTextInput) {
      _controller.addListener(() {
        setState(() {
          _canConfirm = _controller.text == (widget.requiredInput ?? 'SIL');
        });
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(widget.message),
          if (widget.requireTextInput) ...[
            const SizedBox(height: 16),
            Text(
              'Onaylamak icin "${widget.requiredInput ?? 'SIL'}" yazin:',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: AppColors.danger,
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _controller,
              autofocus: true,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: widget.requiredInput ?? 'SIL',
              ),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Vazgec'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
          onPressed: _canConfirm ? () => Navigator.pop(context, true) : null,
          child: Text(
            widget.confirmText,
            style: const TextStyle(color: Colors.white),
          ),
        ),
      ],
    );
  }
}
