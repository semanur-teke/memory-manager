import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

class EXIFExtractor:
    """
    Fotoğraflardan EXIF metadata çıkarır.
    """
    
    def __init__(self):
        pass
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Dosyanın SHA256 hash'ini hesaplar (Duplicate kontrolü için)[cite: 24, 26].
        """
        # EKLENEN KONTROL:
        if not file_path.exists():
            return "" # Veya hata fırlatmak yerine boş string dön
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_datetime(self, image_path: Path) -> Optional[datetime]:
        """
        Fotoğrafın çekilme tarih/saatini çıkarır.

        """
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if not exif:
                    return None
                
                # 'DateTimeOriginal' tagi genellikle çekim tarihini tutar
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id)
                    if tag_name == "DateTimeOriginal":
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except Exception:
            return None
        return None

    def _convert_to_degrees(self, value) -> float:
        """GPS verisini (derece, dakika, saniye) ondalık dereceye çevirir."""
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    def extract_gps_coordinates(self, image_path: Path) -> Optional[Tuple[float, float]]:
        """
        GPS koordinatlarını çıkarır ve ondalık formata çevirir.
        """
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if not exif:
                    return None
                
                gps_info = {}
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id)
                    if tag_name == "GPSInfo":
                        for key in value:
                            sub_tag = GPSTAGS.get(key, key)
                            gps_info[sub_tag] = value[key]
                
                if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                    lat = self._convert_to_degrees(gps_info["GPSLatitude"])
                    if gps_info.get("GPSLatitudeRef") == "S":
                        lat = -lat
                        
                    lng = self._convert_to_degrees(gps_info["GPSLongitude"])
                    if gps_info.get("GPSLongitudeRef") == "W":
                        lng = -lng
                        
                    return (lat, lng)
        except Exception:
            return None
        return None

    def extract_camera_info(self, image_path: Path) -> Dict[str, Optional[str]]:
        """
        Kamera markası ve modelini çıkarır.
        """
        info = {'make': None, 'model': None}
        try:
            with Image.open(image_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = TAGS.get(tag_id)
                        if tag_name == "Make":
                            info['make'] = value.strip()
                        elif tag_name == "Model":
                            info['model'] = value.strip()
        except Exception:
            pass
        return info

    def extract_metadata(self, image_path: Path) -> Dict:
        """
        Tüm metodları birleştirerek tam bir paket döndürür.
        """
        # --- KRİTİK EKLEME: DOSYA KONTROLÜ ---
        if not image_path.exists():
            return {
                "error": "File not found",
                "file_name": image_path.name
            }

        gps = self.extract_gps_coordinates(image_path)
        camera = self.extract_camera_info(image_path)
        
        return {
            "created_at": self.extract_datetime(image_path),
            "location_lat": gps[0] if gps else None,
            "location_lng": gps[1] if gps else None,
            "camera_make": camera['make'],
            "camera_model": camera['model'],
            "file_hash": self.calculate_file_hash(image_path),
            "file_size": image_path.stat().st_size # Artık burası güvenli
        }
    

