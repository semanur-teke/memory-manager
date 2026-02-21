/// Fotograf galerisi ekrani.
/// Grid gorunumunde thumbnail'lar, filtreleme, infinite scroll.
///
/// API Cagrilari:
///   GET /api/items?page=N&size=40&year=Y&month=M&sort=desc
///   GET /api/items/{id}/thumbnail (lazy loaded)
///
/// Performans:
///   - GridView.builder → sadece gorunen alan render edilir
///   - Her sayfa 40 foto, thumbnail 200x200 JPEG
///   - Infinite scroll ile sonraki sayfa otomatik yuklenir

class GalleryScreen {
  // Widget build(BuildContext context)
}
