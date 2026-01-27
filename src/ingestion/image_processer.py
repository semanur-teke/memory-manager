from PIL import Image, ImageOps
from pathlib import Path

class ImageProcessor:
    """
    Fotoğrafların yönünü düzeltir ve boyutlarını optimize eder.
    """
    
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size  # Maksimum genişlik veya yükseklik

    def fix_orientation(self, img: Image.Image) -> Image.Image:
        """
        EXIF verisine bakarak fotoğrafı doğru açıya döndürür[cite: 27].
        """
        # ImageOps.exif_transpose, EXIF yönlendirme etiketlerini 
        # otomatik okur ve görüntüyü düzeltir.
        return ImageOps.exif_transpose(img)

    def resize_if_needed(self, img: Image.Image) -> Image.Image:
        """
        Görüntü çok büyükse en boy oranını koruyarak küçültür.
        """
        if max(img.size) > self.max_size:
            img.thumbnail((self.max_size, self.max_size), Image.Resampling.LANCZOS)
        return img

    def process_image(self, image_path: Path) -> bool:
        """
        Ana iş akışı: Aç, düzelt, boyutlandır ve üzerine yaz[cite: 27].
        """
        try:
            with Image.open(image_path) as img:
                # 1. Yönü düzelt
                img = self.fix_orientation(img)
                
                # 2. Boyutu kontrol et ve gerekirse küçült
                img = self.resize_if_needed(img)
                
                # 3. Dosyayı kaydet (Üzerine yazar veya yeni bir yol alabilir)
                img.save(image_path, quality=95)
                return True
        except Exception as e:
            print(f"İşlem hatası ({image_path}): {e}")
            return False