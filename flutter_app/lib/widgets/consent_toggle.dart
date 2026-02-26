import 'package:flutter/material.dart';
import '../theme/colors.dart';

/// Riza toggle switch widget'i.
/// Yesil (riza var) / gri (riza yok).
/// NOT: Kirmizi degil — riza vermemek bir hata degil, kullanicinin hakkidir.
class ConsentToggle extends StatelessWidget {
  final bool hasConsent;
  final ValueChanged<bool>? onChanged;
  final bool enabled;

  const ConsentToggle({
    super.key,
    required this.hasConsent,
    this.onChanged,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          hasConsent ? Icons.check_circle : Icons.remove_circle_outline,
          color: hasConsent ? AppColors.consentGranted : AppColors.consentDenied,
          size: 20,
        ),
        const SizedBox(width: 8),
        Text(
          hasConsent ? 'Riza verildi' : 'Riza yok',
          style: TextStyle(
            color: hasConsent ? AppColors.consentGranted : AppColors.consentDenied,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(width: 12),
        Switch(
          value: hasConsent,
          onChanged: enabled ? onChanged : null,
          activeColor: AppColors.consentGranted,
          inactiveThumbColor: AppColors.consentDenied,
          inactiveTrackColor: AppColors.consentDenied.withOpacity(0.3),
        ),
      ],
    );
  }
}
