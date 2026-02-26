import 'package:flutter/material.dart';
import '../models/item.dart';
import '../theme/app_theme.dart';
import 'photo_card.dart';

/// Sayfalanmis fotograf grid widget'i.
/// GridView.builder ile lazy rendering + infinite scroll destegi.
class PhotoGrid extends StatefulWidget {
  final List<Item> items;
  final void Function(Item item) onTap;
  final VoidCallback? onLoadMore;
  final bool isLoading;

  const PhotoGrid({
    super.key,
    required this.items,
    required this.onTap,
    this.onLoadMore,
    this.isLoading = false,
  });

  @override
  State<PhotoGrid> createState() => _PhotoGridState();
}

class _PhotoGridState extends State<PhotoGrid> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    // Scroll sonuna yaklasinca sonraki sayfayi yukle
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      widget.onLoadMore?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: GridView.builder(
            controller: _scrollController,
            padding: AppSpacing.pagePadding,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 4,
              crossAxisSpacing: AppSpacing.gridSpacing,
              mainAxisSpacing: AppSpacing.gridSpacing,
              childAspectRatio: 1.0,
            ),
            itemCount: widget.items.length,
            itemBuilder: (context, index) {
              final item = widget.items[index];
              return PhotoCard(
                item: item,
                onTap: () => widget.onTap(item),
              );
            },
          ),
        ),
        // Yuklenme gostergesi
        if (widget.isLoading)
          const Padding(
            padding: EdgeInsets.all(16),
            child: CircularProgressIndicator(),
          ),
      ],
    );
  }
}
