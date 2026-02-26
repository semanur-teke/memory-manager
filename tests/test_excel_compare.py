# -*- coding: utf-8 -*-
"""
real_rapor.xlsx (elle yazilmis) ile exif_rapor.xlsx (kodun urettigi)
dosyalarini karsilastirir. Sadece her iki dosyada da olan sutunlar icin
deger eslesmelerini kontrol eder.

Calistirmak icin:
    pytest tests/test_excel_compare.py -s
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- YOL AYARI ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# ========== AYARLAR ==========
REAL_RAPOR = os.path.join(root_dir, "real_rapor.xlsx")
EXIF_RAPOR = os.path.join(root_dir, "exif_rapor_v2.xlsx")
# ==============================


def normalize_col_name(name: str) -> str:
    """Sutun adindaki ':' ve bosluklari temizler."""
    return name.strip().rstrip(":")


def normalize_yuz(val) -> str:
    """Yuz_Var_Mi degerlerini normalize eder (Hayir/Evet)."""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    s = str(val).strip()
    # Turkce 'Hayir' varyasyonlari
    if s.lower() in ("hayir", "hay\u0131r"):
        return "Hayir"
    if s.lower() == "evet":
        return "Evet"
    return s


def normalize_date(val) -> str:
    """Tarihi YYYY-MM-DD formatina cevirir (karsilastirma icin)."""
    if pd.isna(val) or str(val).strip() == "":
        return ""
    s = str(val).strip()

    # Zaten datetime objesi ise
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")

    # pandas Timestamp
    if hasattr(val, 'strftime'):
        return val.strftime("%Y-%m-%d")

    # "2019-02-26" formati
    try:
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # "2/26/2019" formati
    try:
        dt = datetime.strptime(s, "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return s


def normalize_gps(val) -> str:
    """
    GPS koordinatlarini normalize eder.
    '38,401,27,111' (TR) ve '38.401,27.111' (EN) ayni formata cevirir.
    Sonuc: 'LAT,LNG' noktali format, 3 ondalik.
    """
    if pd.isna(val) or str(val).strip() == "":
        return ""
    s = str(val).strip()

    # '38.401,27.111' formati (kodun urettigi)
    if s.count(",") == 1 and "." in s:
        parts = s.split(",")
        try:
            lat = round(float(parts[0]), 3)
            lng = round(float(parts[1]), 3)
            return f"{lat},{lng}"
        except ValueError:
            pass

    # '38,401,27,111' formati (TR Excel)
    # Bu 4 parcali: lat_tam, lat_ondal, lng_tam, lng_ondal
    if s.count(",") == 3:
        parts = s.split(",")
        try:
            lat = round(float(f"{parts[0]}.{parts[1]}"), 3)
            lng = round(float(f"{parts[2]}.{parts[3]}"), 3)
            return f"{lat},{lng}"
        except ValueError:
            pass

    return s


def load_and_normalize(filepath: str) -> pd.DataFrame:
    """Excel dosyasini yukler ve sutun adlarini normalize eder."""
    df = pd.read_excel(filepath)
    # Sutun adlarini normalize et
    df.columns = [normalize_col_name(c) for c in df.columns]
    # 'Unnamed' sutunlari kaldir
    df = df[[c for c in df.columns if not c.startswith("Unnamed")]]
    return df


# ============= PYTEST TESTLERI =============

@pytest.fixture
def dataframes():
    """Her iki Excel dosyasini yukler."""
    real_path = Path(REAL_RAPOR)
    exif_path = Path(EXIF_RAPOR)

    if not real_path.exists():
        pytest.skip(f"real_rapor.xlsx bulunamadi: {REAL_RAPOR}")
    if not exif_path.exists():
        pytest.skip(f"exif_rapor.xlsx bulunamadi: {EXIF_RAPOR}")

    real_df = load_and_normalize(REAL_RAPOR)
    exif_df = load_and_normalize(EXIF_RAPOR)
    return real_df, exif_df


def test_dosya_adlari_eslesiyor(dataframes):
    """Her iki dosyadaki Dosya_Adi listesi ayni olmali."""
    real_df, exif_df = dataframes

    real_names = set(real_df["Dosya_Adi"].tolist())
    exif_names = set(exif_df["Dosya_Adi"].tolist())

    sadece_real = real_names - exif_names
    sadece_exif = exif_names - real_names

    if sadece_real:
        print(f"\n  Sadece real_rapor'da olan: {sadece_real}")
    if sadece_exif:
        print(f"\n  Sadece exif_rapor'da olan: {sadece_exif}")

    ortak = real_names & exif_names
    assert len(ortak) > 0, "Ortak dosya adi yok!"
    print(f"\n  Ortak dosya sayisi: {len(ortak)} / real:{len(real_names)} / exif:{len(exif_names)}")


def test_ortak_sutunlar_mevcut(dataframes):
    """Ortak sutunlarin varligini kontrol eder."""
    real_df, exif_df = dataframes

    real_cols = set(real_df.columns)
    exif_cols = set(exif_df.columns)
    ortak = real_cols & exif_cols

    print(f"\n  Real sutunlar : {sorted(real_cols)}")
    print(f"  Exif sutunlar : {sorted(exif_cols)}")
    print(f"  Ortak sutunlar: {sorted(ortak)}")

    assert len(ortak) >= 2, "En az 2 ortak sutun olmali!"


def test_tarih_karsilastirma(dataframes):
    """Gercek_Tarih degerlerini karsilastirir."""
    real_df, exif_df = dataframes

    if "Gercek_Tarih" not in real_df.columns or "Gercek_Tarih" not in exif_df.columns:
        pytest.skip("Gercek_Tarih sutunu her iki dosyada da yok")

    # Dosya_Adi uzerinden birlestir
    merged = real_df[["Dosya_Adi", "Gercek_Tarih"]].merge(
        exif_df[["Dosya_Adi", "Gercek_Tarih"]],
        on="Dosya_Adi", suffixes=("_real", "_exif")
    )

    eslesme = 0
    uyumsuz = []

    for _, row in merged.iterrows():
        real_val = normalize_date(row["Gercek_Tarih_real"])
        exif_val = normalize_date(row["Gercek_Tarih_exif"])

        # Ikisi de bos ise eslesir
        if real_val == "" and exif_val == "":
            eslesme += 1
            continue

        if real_val == exif_val:
            eslesme += 1
        else:
            uyumsuz.append({
                "Dosya": row["Dosya_Adi"],
                "Real": real_val,
                "Exif": exif_val
            })

    toplam = len(merged)
    oran = (eslesme / toplam * 100) if toplam > 0 else 0

    print(f"\n  Tarih eslesmesi: {eslesme}/{toplam} ({oran:.1f}%)")
    if uyumsuz:
        print(f"  Uyumsuz tarihler ({len(uyumsuz)}):")
        for u in uyumsuz:
            print(f"    {u['Dosya']}: real={u['Real']} | exif={u['Exif']}")

    assert oran >= 80, \
        f"Tarih uyumsuzlugu: {len(uyumsuz)} dosyada farklilik var ({oran:.1f}% < %80)"


def test_konum_karsilastirma(dataframes):
    """Gercek_Konum degerlerini karsilastirir."""
    real_df, exif_df = dataframes

    if "Gercek_Konum" not in real_df.columns or "Gercek_Konum" not in exif_df.columns:
        pytest.skip("Gercek_Konum sutunu her iki dosyada da yok")

    merged = real_df[["Dosya_Adi", "Gercek_Konum"]].merge(
        exif_df[["Dosya_Adi", "Gercek_Konum"]],
        on="Dosya_Adi", suffixes=("_real", "_exif")
    )

    eslesme = 0
    uyumsuz = []

    for _, row in merged.iterrows():
        real_val = normalize_gps(row["Gercek_Konum_real"])
        exif_val = normalize_gps(row["Gercek_Konum_exif"])

        if real_val == "" and exif_val == "":
            eslesme += 1
            continue

        if real_val == exif_val:
            eslesme += 1
        else:
            uyumsuz.append({
                "Dosya": row["Dosya_Adi"],
                "Real": real_val,
                "Exif": exif_val
            })

    toplam = len(merged)
    oran = (eslesme / toplam * 100) if toplam > 0 else 0

    print(f"\n  Konum eslesmesi: {eslesme}/{toplam} ({oran:.1f}%)")
    if uyumsuz:
        print(f"  Uyumsuz konumlar ({len(uyumsuz)}):")
        for u in uyumsuz:
            print(f"    {u['Dosya']}: real={u['Real']} | exif={u['Exif']}")

    assert oran >= 80, \
        f"Konum uyumsuzlugu: {len(uyumsuz)} dosyada farklilik var ({oran:.1f}% < %80)"


def test_yuz_karsilastirma(dataframes):
    """Yuz_Var_Mi degerlerini karsilastirir."""
    real_df, exif_df = dataframes

    if "Yuz_Var_Mi" not in real_df.columns or "Yuz_Var_Mi" not in exif_df.columns:
        pytest.skip("Yuz_Var_Mi sutunu her iki dosyada da yok")

    merged = real_df[["Dosya_Adi", "Yuz_Var_Mi"]].merge(
        exif_df[["Dosya_Adi", "Yuz_Var_Mi"]],
        on="Dosya_Adi", suffixes=("_real", "_exif")
    )

    eslesme = 0
    uyumsuz = []

    for _, row in merged.iterrows():
        real_val = normalize_yuz(row["Yuz_Var_Mi_real"])
        exif_val = normalize_yuz(row["Yuz_Var_Mi_exif"])

        if real_val == exif_val:
            eslesme += 1
        else:
            uyumsuz.append({
                "Dosya": row["Dosya_Adi"],
                "Real": real_val,
                "Exif": exif_val
            })

    toplam = len(merged)
    oran = (eslesme / toplam * 100) if toplam > 0 else 0

    print(f"\n  Yuz eslesmesi: {eslesme}/{toplam} ({oran:.1f}%)")
    if uyumsuz:
        print(f"  Uyumsuz yuz verileri ({len(uyumsuz)}):")
        for u in uyumsuz:
            print(f"    {u['Dosya']}: real={u['Real']} | exif={u['Exif']}")

    assert oran >= 80, \
        f"Yuz uyumsuzlugu: {len(uyumsuz)} dosyada farklilik var ({oran:.1f}% < %80)"


def test_tum_ortak_sutunlar_ozet(dataframes):
    """
    Tum ortak sutunlari tek seferde karsilastirir ve genel bir ozet cikarir.
    Bu test FAIL etmez, sadece rapor uretir.
    """
    real_df, exif_df = dataframes

    real_cols = set(real_df.columns)
    exif_cols = set(exif_df.columns)
    ortak = sorted(real_cols & exif_cols)

    if "Dosya_Adi" not in ortak:
        pytest.skip("Dosya_Adi sutunu yok, birlestirme yapilamaz")

    karsilastirma_sutunlari = [c for c in ortak if c != "Dosya_Adi"]

    merged = real_df[ortak].merge(
        exif_df[ortak],
        on="Dosya_Adi", suffixes=("_real", "_exif")
    )

    print(f"\n  {'='*65}")
    print(f"  GENEL KARSILASTIRMA RAPORU")
    print(f"  {'='*65}")
    print(f"  Ortak dosya sayisi: {len(merged)}")
    print(f"  Karsilastirilan sutunlar: {karsilastirma_sutunlari}")
    print(f"  {'-'*65}")

    normalizers = {
        "Gercek_Tarih": normalize_date,
        "Gercek_Konum": normalize_gps,
        "Yuz_Var_Mi": normalize_yuz,
    }

    toplam_eslesme = 0
    toplam_hucre = 0

    for col in karsilastirma_sutunlari:
        real_col = f"{col}_real"
        exif_col = f"{col}_exif"

        if real_col not in merged.columns or exif_col not in merged.columns:
            continue

        norm_fn = normalizers.get(col, lambda x: "" if pd.isna(x) else str(x).strip())

        eslesme = 0
        for _, row in merged.iterrows():
            rv = norm_fn(row[real_col])
            ev = norm_fn(row[exif_col])
            if rv == ev:
                eslesme += 1

        toplam = len(merged)
        toplam_eslesme += eslesme
        toplam_hucre += toplam
        oran = (eslesme / toplam * 100) if toplam > 0 else 0
        durum = "OK" if eslesme == toplam else "FARK VAR"
        print(f"  {col:20s}: {eslesme}/{toplam} ({oran:5.1f}%) [{durum}]")

    print(f"  {'-'*65}")
    genel_oran = (toplam_eslesme / toplam_hucre * 100) if toplam_hucre > 0 else 0
    print(f"  {'GENEL':20s}: {toplam_eslesme}/{toplam_hucre} ({genel_oran:.1f}%)")
    print(f"  {'='*65}")
