import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shimmer/shimmer.dart';
import '../providers/gallery_provider.dart';
import '../theme/colors.dart';

/// Sifreli fotograf gosterim widget'i — PROJENIN EN KRITIK WIDGET'I.
///
/// NEDEN FutureBuilder DEGIL ConsumerWidget:
/// FutureBuilder, build() her cagirildiginda YENI bir Future olusturur.
/// GridView'da scroll yapildiginda widget'lar rebuild olur → her seferinde
/// API cagrisi tekrarlanir → yuzlerce gereksiz istek + gorseller surekli
/// yanip soner. Riverpod FutureProvider.family sonucu otomatik cache'ler,
/// rebuild'de API tekrar cagirilmaz.
class EncryptedImage extends ConsumerWidget {
  final int itemId;
  final double? width;
  final double? height;

  const EncryptedImage({
    super.key,
    required this.itemId,
    this.width,
    this.height,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final thumbnailAsync = ref.watch(thumbnailProvider(itemId));

    return thumbnailAsync.when(
      // Yukleniyor — shimmer efekti
      loading: () => Shimmer.fromColors(
        baseColor: AppColors.border,
        highlightColor: AppColors.background,
        child: Container(
          width: width,
          height: height,
          decoration: BoxDecoration(
            color: AppColors.border,
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      // Basarili — gorseli goster
      data: (bytes) => ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Image.memory(
          bytes,
          width: width,
          height: height,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => _errorWidget(),
        ),
      ),
      // Hata
      error: (_, __) => _errorWidget(),
    );
  }

  Widget _errorWidget() {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.border,
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Icon(
        Icons.broken_image,
        size: 48,
        color: AppColors.textSecondary,
      ),
    );
  }
}
