# -*- coding: utf-8 -*-
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# --- YOL AYARI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.ingestion.exif_extractor import EXIFExtractor

# OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.jfif'}

# ========== AYARLAR ==========
TEST_FOLDER = r"C:\Users\sema\Desktop\test_images"
OUTPUT_EXCEL = r"C:\Users\sema\Desktop\memory-manager\exif_rapor_v2.xlsx"

# DNN model dosyalari
MODEL_DIR = os.path.join(root_dir, "models", "face_detector")
PROTOTXT = os.path.join(MODEL_DIR, "deploy.prototxt")
CAFFEMODEL = os.path.join(MODEL_DIR, "res10_300x300_ssd_iter_140000.caffemodel")
DNN_CONFIDENCE = 0.55  # Minimum guven esigi
# ==============================

# DNN modelini bir kez yukle (her gorsel icin tekrar yuklemek yavas olur)
_face_net = None

def _get_face_net():
    """DNN yuz tespiti modelini yukler (lazy loading)."""
    global _face_net
    if _face_net is not None:
        return _face_net
    if CV2_AVAILABLE and os.path.exists(PROTOTXT) and os.path.exists(CAFFEMODEL):
        _face_net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)
    return _face_net


def detect_faces(image_path: Path) -> bool:
    """
    DNN tabanli yuz tespiti (OpenCV DNN + ResNet SSD).
    Haar Cascade'den cok daha isabetli - false positive oranini dusurur.
    DNN modeli yoksa Haar Cascade'e doner.
    """
    if not CV2_AVAILABLE:
        return False

    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return False

        net = _get_face_net()
        if net is not None:
            return _detect_faces_dnn(img, net)
        else:
            return _detect_faces_haar(img)
    except Exception:
        return False


def _detect_faces_dnn(img, net) -> bool:
    """DNN tabanli yuz tespiti."""
    h, w = img.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(img, (300, 300)),
        1.0, (300, 300),
        (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > DNN_CONFIDENCE:
            # Tespit edilen bolgenin boyutunu kontrol et
            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            x1, y1, x2, y2 = box.astype("int")
            face_w = x2 - x1
            face_h = y2 - y1

            # Cok kucuk tespitleri atla (gurultu)
            if face_w < 20 or face_h < 20:
                continue

            return True
    return False


def _detect_faces_haar(img) -> bool:
    """Haar Cascade yuz tespiti (yedek yontem, daha siki parametreler)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=8,     # 5'ten 8'e cikarildi (daha siki)
        minSize=(60, 60),   # 30'dan 60'a cikarildi
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return len(faces) > 0


def extract_all_exif_tags(image_path: Path) -> dict:
    """Fotograf dosyasindan TUM EXIF etiketlerini cikarir."""
    all_tags = {}
    skip_tags = {"MakerNote", "PrintImageMatching", "GPSInfo", "UserComment",
                 "ComponentsConfiguration", "FileSource", "SceneType",
                 "InteroperabilityIFD", "ExifIFD"}
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    if tag_name in skip_tags:
                        continue
                    if isinstance(value, bytes):
                        continue
                    if isinstance(value, (str, int, float)):
                        all_tags[tag_name] = value
                    elif isinstance(value, tuple):
                        all_tags[tag_name] = str(value)
                    elif isinstance(value, dict):
                        continue
                    else:
                        all_tags[tag_name] = str(value)
    except Exception:
        pass
    return all_tags


def sanitize_value(value):
    """Excel'e yazilamayan karakterleri temizler."""
    if isinstance(value, str):
        import re
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', value)
    return value


def format_date(dt: datetime) -> str:
    """Tarihi M/D/YYYY formatina cevirir."""
    if dt is None:
        return ""
    return f"{dt.month}/{dt.day}/{dt.year}"


def format_gps(lat, lng) -> str:
    """GPS koordinatlarini string formatina cevirir."""
    if lat is None or lng is None:
        return ""
    return f"{round(lat, 3)},{round(lng, 3)}"


def process_folder_to_excel(folder_path: str, output_path: str) -> pd.DataFrame:
    """
    Verilen klasordeki TUM gorsellerin EXIF verilerini cikarip Excel'e kaydeder.
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Klasor bulunamadi: {folder_path}")

    extractor = EXIFExtractor()
    results = []

    image_files = sorted([
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not image_files:
        raise ValueError(f"Klasorde gorsel bulunamadi: {folder_path}")

    # DNN modeli durumunu goster
    net = _get_face_net()
    if net is not None:
        print("\n  Yuz tespiti: DNN (ResNet SSD) - yuksek isabetle")
    else:
        print("\n  Yuz tespiti: Haar Cascade (yedek yontem)")

    print(f"  {len(image_files)} gorsel bulundu, isleniyor...\n")

    for i, img_path in enumerate(image_files, 1):
        has_face = detect_faces(img_path)
        face_label = "YUZ VAR" if has_face else "-"
        print(f"  [{i}/{len(image_files)}] {img_path.name:55s} {face_label}")

        metadata = extractor.extract_metadata(img_path)
        if "error" in metadata:
            print(f"           HATA: {metadata['error']}")
            continue

        row = {
            "Dosya_Adi": img_path.stem,
            "Gercek_Tarih": format_date(metadata.get("created_at")),
            "Gercek_Konum": format_gps(
                metadata.get("location_lat"),
                metadata.get("location_lng")
            ),
            "Yuz_Var_Mi": "Evet" if has_face else "Hayir",
            "Kamera_Marka": metadata.get("camera_make") or "",
            "Kamera_Model": metadata.get("camera_model") or "",
            "Dosya_Boyutu_KB": round(metadata.get("file_size", 0) / 1024, 1),
            "Dosya_Hash": metadata.get("file_hash", ""),
        }

        # Ek EXIF etiketlerini ekle
        all_exif = extract_all_exif_tags(img_path)
        already_covered = {
            "DateTimeOriginal", "DateTime", "DateTimeDigitized",
            "Make", "Model", "GPSInfo"
        }
        for tag_name, tag_value in all_exif.items():
            if tag_name not in already_covered:
                row[tag_name] = tag_value

        results.append(row)

    df = pd.DataFrame(results)

    main_cols = [
        "Dosya_Adi", "Gercek_Tarih", "Gercek_Konum", "Yuz_Var_Mi",
        "Kamera_Marka", "Kamera_Model", "Dosya_Boyutu_KB", "Dosya_Hash"
    ]
    extra_cols = [c for c in df.columns if c not in main_cols]
    df = df[main_cols + extra_cols]
    df = df.fillna("")

    # Gecersiz karakterleri temizle
    for col in df.columns:
        df[col] = df[col].apply(sanitize_value)

    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"\n  Excel kaydedildi: {output_path}")
    print(f"  Toplam {len(df)} gorsel, {len(df.columns)} sutun")

    return df


# ============= PYTEST TEST SENARYOLARI =============

@pytest.fixture
def extractor():
    return EXIFExtractor()


def test_folder_to_excel():
    """ANA TEST: Klasordeki tum gorsellerin EXIF verilerini Excel'e kaydeder."""
    folder = Path(TEST_FOLDER)
    if not folder.exists():
        pytest.skip(f"Test klasoru bulunamadi: {TEST_FOLDER}")

    df = process_folder_to_excel(TEST_FOLDER, OUTPUT_EXCEL)

    assert len(df) > 0, "Hicbir gorsel islenemedi!"
    assert "Dosya_Adi" in df.columns
    assert "Gercek_Tarih" in df.columns
    assert "Gercek_Konum" in df.columns
    assert "Yuz_Var_Mi" in df.columns

    valid_values = {"Evet", "Hayir"}
    assert set(df["Yuz_Var_Mi"].unique()).issubset(valid_values)

    print(f"\n  {'='*60}")
    print(f"  BASARILI: {len(df)} gorsel islendi")
    print(f"  Excel: {OUTPUT_EXCEL}")
    print(f"  {'='*60}")


def test_single_image_metadata(extractor):
    """Tek bir gorselden metadata cikarma testi."""
    folder = Path(TEST_FOLDER)
    if not folder.exists():
        pytest.skip("Test klasoru bulunamadi")
    images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        pytest.skip("Gorsel bulunamadi")
    metadata = extractor.extract_metadata(images[0])
    assert isinstance(metadata, dict)
    assert "error" not in metadata
    assert "created_at" in metadata
    assert "file_hash" in metadata


def test_invalid_file_path(extractor):
    """Var olmayan dosya verildiginde hata sozlugu dondurmeli."""
    fake_path = Path("olmayan_foto.jpg")
    metadata = extractor.extract_metadata(fake_path)
    assert isinstance(metadata, dict)
    assert "error" in metadata
    assert metadata["error"] == "File not found"


def test_face_detection():
    """Yuz tespiti fonksiyonunun calistigini dogrula."""
    if not CV2_AVAILABLE:
        pytest.skip("OpenCV yuklu degil")
    folder = Path(TEST_FOLDER)
    if not folder.exists():
        pytest.skip("Test klasoru bulunamadi")
    images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        pytest.skip("Gorsel bulunamadi")
    result = detect_faces(images[0])
    assert isinstance(result, bool)


def test_all_exif_tags():
    """Ek EXIF etiketlerinin cikarildigini dogrula."""
    folder = Path(TEST_FOLDER)
    if not folder.exists():
        pytest.skip("Test klasoru bulunamadi")
    images = [f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
    if not images:
        pytest.skip("Gorsel bulunamadi")
    tags = extract_all_exif_tags(images[0])
    assert isinstance(tags, dict)
    print(f"\nBulunan EXIF etiketleri: {list(tags.keys())}")


# ============= DOGRUDAN CALISTIRMA =============
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EXIF -> Excel")
    parser.add_argument("folder", nargs="?", default=TEST_FOLDER)
    parser.add_argument("-o", "--output", default=OUTPUT_EXCEL)
    args = parser.parse_args()

    print("EXIF Extractor - Klasor -> Excel")
    print(f"Klasor: {args.folder}")
    print(f"Cikti:  {args.output}")
    df = process_folder_to_excel(args.folder, args.output)
    print(f"\nOnizleme (ilk 5 satir):")
    print(df.head().to_string(index=False))
