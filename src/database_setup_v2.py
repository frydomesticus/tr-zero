"""
TR-ZERO: Ulusal İklim Karar Destek Sistemi - Veritabanı Kurulum Modülü (v2.0)
=============================================================================

Bu modül, Türkiye Ulusal Sera Gazı Envanteri verilerini ve IPCC emisyon 
faktörlerini SQLite veritabanına yüklemek için tasarlanmıştır. 

Güncellemeler (v2.0):
---------------------
- Alt sektör detayları eklendi (NIR 2024 uyumlu)
- IPCC 2006 emisyon faktörleri entegre edildi
- Veri doğrulama mekanizması güçlendirildi

Metodoloji:
-----------
Veri yapısı ve hesaplama metodolojisi aşağıdaki kaynaklara dayanmaktadır:

Kaynaklar:
----------
[1] IPCC (2006). 2006 IPCC Guidelines for National Greenhouse Gas Inventories. 
    Volume 1: General Guidance and Reporting.  
    https://www.ipcc-nggip.iges.or.jp/public/2006gl/

[2] IPCC (2006). 2006 IPCC Guidelines, Volume 2: Energy, Chapter 2.  
    Stationary Combustion - Default Emission Factors (Table 2.2).  
    https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf

[3] T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (2024). 
    Turkish Greenhouse Gas Inventory 1990-2022: National Inventory Report. 
    Submitted to UNFCCC. https://unfccc.int/documents/627786

[4] T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (2024).
    First Biennial Transparency Report of Türkiye.  
    https://iklim.gov.tr/

[5] IEA (2024). Türkiye - Countries & Regions. 
    https://www.iea.org/countries/turkiye/emissions

[6] TÜİK (2024). Sera Gazı Emisyon İstatistikleri, 1990-2023.  
    https://data.tuik.gov.tr/

[7] EPA (2021). Emission Factors for Greenhouse Gas Inventories. 
    https://www.epa.gov/sites/default/files/2021-04/documents/emission-factors_apr2021.pdf

[8] Moran, D., et al. (2018). Carbon footprints of 13,000 cities.  
    Environmental Research Letters, 13(6), 064041.  
    https://doi.org/10.1088/1748-9326/aac72a

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih: Aralık 2025
Versiyon: 2.0
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

# =============================================================================
# SABİT DEĞERLER VE REFERANS VERİLERİ
# =============================================================================

# GWP Değerleri - IPCC AR5 (100 yıllık) [Kaynak: IPCC AR5, 2014]
GWP_VALUES = {
    "CO2": 1,
    "CH4": 28,      # Metan
    "N2O": 265,     # Diazot Monoksit
    "SF6": 23500,   # Kükürt Heksaflorür
    "HFC": 1430,    # Hidroflorokarbonlar (ortalama)
    "PFC": 7390     # Perflorokarbonlar (ortalama)
}

# NIR 2024 Referans Değerleri (Doğrulama için) [Kaynak: NIR 2024, Tablo ES.1]
NIR_REFERANS = {
    2022: {
        "Toplam": 558.27,
        "Enerji": 400.59,
        "IPPU": 69.91,
        "Tarim": 71.51,
        "Atik": 16.26
    },
    2021: {
        "Toplam": 571.99,
        "Enerji": 406.47
    }
}

# Sektörel Oranlar (NIR 2024, Sayfa ES-4) [Kaynak: NIR 2024]
SEKTOREL_ORANLAR_2022 = {
    "Enerji": 0.718,        # %71.8
    "Tarim": 0.128,         # %12.8
    "IPPU": 0.125,          # %12.5
    "Atik": 0.029           # %2.9
}


def veritabani_kurulumu():
    """
    Ulusal envanter verilerini ve emisyon faktörlerini SQLite veritabanına yükler.
    
    Bu fonksiyon aşağıdaki tabloları oluşturur:
    1. ulusal_envanter: Yıllık sektörel emisyon verileri
    2. il_katsayilari: İl bazlı dağılım katsayıları
    3. emisyon_faktorleri: IPCC 2006 emisyon faktörleri
    4. gwp_degerleri: Küresel Isınma Potansiyeli değerleri
    
    Returns:
        bool: Kurulum başarılı ise True, aksi halde False
    
    Methodology:
        Veri yapısı IPCC 2006 Kılavuzları Cilt 1, Bölüm 8'e uygun olarak
        tasarlanmıştır [1]. Emisyon hesaplamaları Tier 1 ve Tier 2 
        yaklaşımlarını desteklemektedir [2].  
    """
    
    print("=" * 70)
    print("TR-ZERO SİSTEM KURULUMU - VERSİYON 2.0")
    print("Türkiye Ulusal Sera Gazı Envanter Veritabanı")
    print("=" * 70)
    print(f"Kurulum Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    db_adi = "iklim_veritabani.sqlite"
    
    # =========================================================================
    # 1. VERİ DOSYALARINI KONTROL ET
    # =========================================================================
    # Metodoloji: IPCC 2006 Kılavuzları, Cilt 1, Bölüm 8 - Kalite Kontrolü [1]
    # =========================================================================
    
    gerekli_dosyalar = {
        "data/sektorel_emisyonlar_v2.csv": "Ulusal Envanter Verileri",
        "data/il_dagilim_katsayilari.csv": "İl Dağılım Katsayıları",
        "data/emisyon_faktorleri.csv": "IPCC Emisyon Faktörleri"
    }
    
    eksik_dosyalar = []
    for dosya, aciklama in gerekli_dosyalar.items():
        if os.path.exists(dosya):
            print(f"  ✅ {aciklama}: {dosya}")
        else:
            print(f"  ❌ {aciklama}: {dosya} BULUNAMADI")
            eksik_dosyalar.append(dosya)
    
    if eksik_dosyalar:
        print("\n⚠️ Eksik dosyalar nedeniyle kurulum durduruluyor.")
        print("   Lütfen eksik CSV dosyalarını proje dizinine ekleyin.")
        return False
    
    print("\n✅ Tüm veri dosyaları doğrulandı.")
    
    # =========================================================================
    # 2. VERİTABANI BAĞLANTISI
    # =========================================================================
    
    try:
        conn = sqlite3.connect(db_adi)
        cursor = conn.cursor()
        print(f"✅ Veritabanı bağlantısı: {db_adi}")
    except sqlite3.Error as e:
        print(f"❌ Veritabanı hatası: {e}")
        return False
    
    try:
        # =====================================================================
        # 3. ULUSAL ENVANTER VERİLERİ
        # =====================================================================
        # Kaynak: NIR 2024 Raporu, Tablo ES.1 - Sektörel Emisyon Özeti [3]
        # Alt sektör dağılımı: NIR 2024, Tablo 1.3 ve Sektör Raporları [3]
        # Birim: Mt CO2 eşdeğeri
        # GWP: IPCC AR5 değerleri kullanılmıştır (CO2=1, CH4=28, N2O=265)
        # =====================================================================
        
        print("\n" + "-" * 40)
        print("TABLO 1: Ulusal Envanter Verileri")
        print("-" * 40)
        
        # ✅ DÜZELTME: data/ klasörü eklendi
        df_emisyon = pd.read_csv("data/sektorel_emisyonlar_v2.csv", comment='#')
        df_emisyon = df_emisyon.fillna(0)
        
        # Veri doğrulama
        required_cols = ['Year', 'Enerji_Toplam', 'IPPU_Toplam', 'Tarim_Toplam', 
                         'Atik_Toplam', 'Toplam_LULUCF_Haric']
        
        for col in required_cols:
            if col not in df_emisyon.columns:
                raise ValueError(f"Zorunlu sütun eksik: {col}")
        
        df_emisyon.to_sql("ulusal_envanter", conn, if_exists="replace", index=False)
        
        print(f"  ✅ Kayıt sayısı: {len(df_emisyon)} yıl")
        print(f"  ✅ Zaman aralığı: {df_emisyon['Year'].min()}-{df_emisyon['Year'].max()}")
        print(f"  ✅ Sütun sayısı: {len(df_emisyon.columns)} (alt sektörler dahil)")
        
        # =====================================================================
        # 4. EMİSYON FAKTÖRLERİ
        # =====================================================================
        # Kaynak: IPCC 2006 Guidelines, Volume 2, Chapter 2, Table 2.2 [2]
        # Türkiye spesifik faktörler: NIR 2024, Annex 8 [3]
        # EPA Referans: Emission Factors for GHG Inventories, 2021 [7]
        # =====================================================================
        
        print("\n" + "-" * 40)
        print("TABLO 2: IPCC 2006 Emisyon Faktörleri")
        print("-" * 40)
        
        # ✅ DÜZELTME: data/ klasörü eklendi
        df_faktor = pd.read_csv("data/emisyon_faktorleri.csv", comment='#')
        df_faktor.to_sql("emisyon_faktorleri", conn, if_exists="replace", index=False)
        
        print(f"  ✅ Yakıt/Aktivite sayısı: {len(df_faktor)}")
        print(f"  ✅ Kaynak: IPCC 2006 Guidelines + NIR 2024 Country-Specific")
        
        # =====================================================================
        # 5. GWP DEĞERLERİ TABLOSU
        # =====================================================================
        # Kaynak: IPCC Fifth Assessment Report (AR5), 2014
        # Tablo: Supplementary Material, Table 8.A.1
        # Not: 100 yıllık GWP değerleri kullanılmaktadır
        # =====================================================================
        
        print("\n" + "-" * 40)
        print("TABLO 3: GWP Değerleri (IPCC AR5)")
        print("-" * 40)
        
        df_gwp = pd.DataFrame([
            {"Gaz": k, "GWP_100yr": v, "Kaynak": "IPCC_AR5_2014"} 
            for k, v in GWP_VALUES.items()
        ])
        df_gwp.to_sql("gwp_degerleri", conn, if_exists="replace", index=False)
        
        print(f"  ✅ Gaz sayısı: {len(df_gwp)}")
        
        # =====================================================================
        # 6. İL KATSAYILARI (DOWNSCALING)
        # =====================================================================
        # Metodoloji: Top-down emisyon dağıtımı yaklaşımı [8]
        # Proxy değişkenler: Sanayi üretimi, nüfus, enerji tüketimi
        # Kaynak: Moran et al. (2018), Environmental Research Letters [8]
        # =====================================================================
        
        print("\n" + "-" * 40)
        print("TABLO 4: İl Dağılım Katsayıları")
        print("-" * 40)
        
        # ✅ DÜZELTME: data/ klasörü eklendi
        df_il = pd.read_csv("data/il_dagilim_katsayilari.csv")
        df_il.to_sql("il_katsayilari", conn, if_exists="replace", index=False)
        
        print(f"  ✅ Bölge sayısı: {len(df_il)}")
        
        # =====================================================================
        # 7. DOĞRULAMA TESTLERİ
        # =====================================================================
        # NIR 2024 referans değerleriyle karşılaştırma
        # Tolerans: ±%1 (IPCC kalite kontrol standardı) [1]
        # =====================================================================
        
        print("\n" + "=" * 70)
        print("DOĞRULAMA TESTLERİ")
        print("=" * 70)
        
        for yil, referanslar in NIR_REFERANS.items():
            print(f"\n📅 {yil} Yılı Kontrolü:")
            
            sorgu = f"""
                SELECT Year, 
                       Enerji_Toplam as Enerji,
                       IPPU_Toplam as IPPU,
                       Tarim_Toplam as Tarim,
                       Atik_Toplam as Atik,
                       Toplam_LULUCF_Haric as Toplam
                FROM ulusal_envanter 
                WHERE Year = {yil}
            """
            sonuc = pd.read_sql(sorgu, conn)
            
            if sonuc.empty:
                print(f"   ⚠️ {yil} verisi bulunamadı")
                continue
            
            for sektor, ref_deger in referanslar.items():
                if sektor in sonuc.columns:
                    db_deger = sonuc[sektor].values[0]
                    sapma = abs(db_deger - ref_deger) / ref_deger * 100
                    
                    if sapma < 1:
                        durum = "✅"
                    elif sapma < 5:
                        durum = "⚠️"
                    else:
                        durum = "❌"
                    
                    print(f"   {durum} {sektor}: DB={db_deger:.2f} | NIR={ref_deger:.2f} | Sapma=%{sapma:.2f}")
        
        # =====================================================================
        # 8.  ÖZET İSTATİSTİKLER
        # =====================================================================
        
        print("\n" + "=" * 70)
        print("ÖZET İSTATİSTİKLER")
        print("=" * 70)
        
        # Sektörel oran kontrolü (2022)
        sorgu_2022 = """
            SELECT Enerji_Toplam, IPPU_Toplam, Tarim_Toplam, Atik_Toplam, 
                   Toplam_LULUCF_Haric
            FROM ulusal_envanter WHERE Year = 2022
        """
        df_2022 = pd.read_sql(sorgu_2022, conn)
        
        if not df_2022.empty:
            toplam = df_2022['Toplam_LULUCF_Haric'].values[0]
            print(f"\n2022 Yılı Sektörel Dağılım (NIR 2024 Referans):")
            print(f"  • Enerji:  {df_2022['Enerji_Toplam'].values[0]/toplam*100:.1f}% (Ref: 71.8%)")
            print(f"  • IPPU:    {df_2022['IPPU_Toplam'].values[0]/toplam*100:.1f}% (Ref: 12.5%)")
            print(f"  • Tarım:   {df_2022['Tarim_Toplam'].values[0]/toplam*100:.1f}% (Ref: 12.8%)")
            print(f"  • Atık:    {df_2022['Atik_Toplam'].values[0]/toplam*100:.1f}% (Ref: 2.9%)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()
        print("\n" + "=" * 70)
        print("KURULUM TAMAMLANDI")
        print("=" * 70)


def veri_sorgula(sorgu: str) -> pd.DataFrame:
    """
    Veritabanından veri sorgulama yardımcı fonksiyonu.
    
    Args:
        sorgu: SQL sorgu metni
        
    Returns:
        pd.DataFrame: Sorgu sonuçları
        
    Example:
        >>> df = veri_sorgula("SELECT * FROM ulusal_envanter WHERE Year >= 2020")
    """
    conn = sqlite3.connect("iklim_veritabani.sqlite")
    try:
        return pd.read_sql(sorgu, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    basari = veritabani_kurulumu()
    
    if basari:
        print("\n🎉 Sistem kullanıma hazır!")
        print("\n📊 Örnek Sorgu:")
        print("-" * 40)
        
        # Test sorgusu
        df = veri_sorgula("""
            SELECT Year, Enerji_Toplam, IPPU_Toplam, Toplam_LULUCF_Haric
            FROM ulusal_envanter 
            WHERE Year >= 2020
            ORDER BY Year
        """)
        print(df.to_string(index=False))
    else:
        print("\n⚠️ Kurulum başarısız.  Hataları kontrol edin.")