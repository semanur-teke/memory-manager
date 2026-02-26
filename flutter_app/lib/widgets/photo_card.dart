import 'package:flutter/material.dart';
import '../models/item.dart';
import '../theme/colors.dart';
import 'encrypted_image.dart';

/// Tekil fotograf karti widget'i.
/// EncryptedImage + tarih overlay.
class PhotoCard extends StatelessWidget {
  final Item item;
  final VoidCallback? onTap;

  const PhotoCard({
    super.key,
    required this.item,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Sifreli fotograf
          EncryptedImage(itemId: item.itemId),
          // Tarih overlay (alt kisim)
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [
                    Colors.black.withOpacity(0.6),
                    Colors.transparent,
                  ],
                ),
                borderRadius: const BorderRadius.vertical(
                  bottom: Radius.circular(8),
                ),
              ),
              child: Text(
                item.dateFormatted,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          // Tip ikonu (sag ust kose) — ses dosyasi ise mikrofon goster
          if (item.type == 'Audio')
            Positioned(
              top: 4,
              right: 4,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Icon(Icons.mic, color: Colors.white, size: 14),
              ),
            ),
        ],
      ),
    );
  }
}
