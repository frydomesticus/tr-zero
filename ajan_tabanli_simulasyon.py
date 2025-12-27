"""
TR-ZERO:  Ajan Tabanlı Karbon Piyasası Simülasyonu (v2.1 - Düzeltilmiş)
=======================================================================

Bu modül, Türkiye Emisyon Ticaret Sistemi'ni (ETS) simüle etmek için
geliştirilmiş Ajan Tabanlı Model (ABM) içermektedir.

Düzeltmeler (v2.1):
-------------------
✅ PiyasaOperatoru ve MRV agents listesine eklendi
✅ Tahsisat (allowance) mekanizması eklendi
✅ Bankalama (banking) sistemi eklendi
✅ Ceza geri bildirimi tesislere aktarılıyor
✅ NPV hesabı MAC önemleriyle entegre edildi
✅ Kaynak atıfları düzeltildi
✅ Tüm parametrelere birim eklendi

Metodoloji:
-----------
1. Ajan Heterojenliği:  Yu et al. (2020)
2. Cap & Trade Mekanizması: Zhou et al. (2016)
3. MAC Analizi: McKinsey (2009) - Türkiye'ye uyarlanmış
4. Tahsisat ve Ticaret: EU ETS Directive 2003/87/EC

Kaynaklar:
----------
[1] Yu, S., et al. (2020). Modeling the emission trading scheme from 
    an agent-based perspective. European Journal of Operational Research.
    https://doi.org/10.1016/j.ejor.2020.03.080

[2] Zhou, P., et al. (2016). Multi-agent-based Simulation for Policy 
    Evaluation of Carbon Emissions.  Springer.
    https://doi.org/10.1007/978-981-10-2669-0_29

[3] McKinsey & Company (2009). Pathways to a Low-Carbon Economy: 
    Version 2 of the Global Greenhouse Gas Abatement Cost Curve.
    [NOT: MAC değerleri Türkiye sektörlerine uyarlanmıştır]

[4] T. C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (2025). 
    Türkiye ETS Yönetmelik Taslağı.
    https://iklim.gov.tr/taslaklar-i-2124

[5] European Commission (2003). EU ETS Directive 2003/87/EC
    https://eur-lex.europa.eu/legal-content/EN/TXT/? uri=CELEX:32003L0087

[6] EBRD & PwC (2024). A Low Carbon Pathway for the Cement Sector 
    in the Republic of Türkiye. 

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih:  Aralık 2025
Versiyon: 2.1 (Düzeltilmiş)
"""

from mesa import Agent, Model
from mesa. datacollection import DataCollector
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random
import os
import sqlite3
from datetime import datetime

# =============================================================================
# PROJE DİZİNİ AYARLARI
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# Çıktı klasörünü oluştur
try:
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
except OSError as e:
    print(f"⚠️ Klasör oluşturulamadı: {e}")
    OUTPUT_DIR = SCRIPT_DIR

# =============================================================================
# SABİT DEĞERLER VE PARAMETRELER
# =============================================================================

# Türkiye ETS Parametreleri
# [Kaynak: Kesin değerler - TR-ETS Taslak 2025; Tahmini - AB ETS'den uyarlanmış]
ETS_PARAMS = {
    "PILOT_BASLANGIC": 2026,     # [TR-ETS Taslak, Madde 5]
    "TAM_UYGULAMA": 2028,         # [TR-ETS Taslak, Madde 5]
    "TABAN_FIYAT": 20,            # [TAHMİNİ - $/ton CO₂, modelleme için]
    "TAVAN_FIYAT": 150,           # [TAHMİNİ - $/ton CO₂, AB ETS 2027 ~€111]
    "CEZA_MIKTARI": 100           # [TAHMİNİ - $/ton CO₂, AB ETS €100/ton]
}

# Sektör Profilleri
# [Kaynak: (1) NIR 2024 - sektör emisyonları
#         (2) TÜİK sanayi istatistikleri
#         (3) IPCC EF veritabanı
#         NOT: Değerler Türkiye sektörlerine uyarlanmış tahminlerdir]
SEKTOR_PROFILLERI = {
    "Enerji": {
        "baz_emisyon":  1.0,           # Mt CO₂/yıl (temsilci tesis ortalaması)
        "ihracat_orani": 0.05,        # 0. 05 = %5 (sektör üretiminin ihraç payı)
        "skdm_kapsam": False,         # boolean (AB SKDM/CBAM kapsamında mı?)
        "maliyet_limit": 90,          # Milyon $/yıl (işletme kapanma eşiği)
        "yatirim_bedeli": 200,        # Milyon $ (temizlik teknolojisi CAPEX)
        "duyarlilik":  "Vergi",        # string (politika duyarlılığı)
        "mac_onlemler": {
            "enerji_verimliligi": {"mac": -15, "potansiyel": 0.08, "sure": 2},  # $/ton, oran, yıl
            "yakit_degisimi": {"mac": 35, "potansiyel": 0.20, "sure": 3},
            "yenilenebilir":  {"mac": 50, "potansiyel": 0.35, "sure": 5}
        }
    },
    "Sanayi": {
        "baz_emisyon": 0.75,          # Mt CO₂/yıl
        "ihracat_orani": 0.40,        # 0.40 = %40
        "skdm_kapsam": True,          # AB SKDM kapsamında
        "maliyet_limit": 110,         # Milyon $/yıl
        "yatirim_bedeli": 250,        # Milyon $
        "duyarlilik": "Vergi",
        "mac_onlemler": {
            "enerji_verimliligi": {"mac":  -5, "potansiyel": 0.10, "sure": 2},
            "proses_iyilestirme": {"mac": 25, "potansiyel": 0.15, "sure": 3},
            "teknoloji_degisimi": {"mac": 60, "potansiyel": 0.30, "sure": 6}
        }
    },
    "Tarim": {
        "baz_emisyon": 0.3,           # Mt CO₂/yıl
        "ihracat_orani": 0.20,        # 0.20 = %20
        "skdm_kapsam": False,
        "maliyet_limit":  999,         # Milyon $/yıl (tarım hassas sektör)
        "yatirim_bedeli": 300,        # Milyon $
        "duyarlilik":  "Tesvik",       # Teşvik odaklı sektör
        "mac_onlemler": {
            "gubre_optimizasyonu": {"mac": 10, "potansiyel": 0.15, "sure": 1},
            "metan_yakalama": {"mac": 40, "potansiyel": 0.25, "sure": 5}
        }
    }
}

# =============================================================================
# AJAN SINIFLARI
# =============================================================================

class PiyasaOperatoru(Agent):
    """
    ETS Piyasa Operatörü - Cap & Trade mekanizmasını yönetir. 
    
    Referanslar:
    - [cite:  Yu et al. 2020] Piyasa-clearing mekanizması
    - [cite: EU ETS Directive] Cap azaltma kuralları
    """
    
    def __init__(self, model, baslangic_cap, azalma_orani):
        super().__init__(model)
        self.ajan_tipi = "PiyasaOperatoru"
        self.cap = baslangic_cap  # Mt CO₂
        self.azalma_orani = azalma_orani  # yıllık oran (0-1 arası)
        self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"]  # $/ton
        self.fiyat_gecmisi = []
        self.toplam_gelir = 0  # Milyon $
        
    def step(self):
        """Her yıl için piyasa operatörü adımı."""
        # Cap azaltma sadece ETS aktif olduğunda
        if self. model.yil >= ETS_PARAMS["PILOT_BASLANGIC"]: 
            self.cap *= (1 - self.azalma_orani)
        
        # Toplam Emisyon Hesaplama
        toplam_emisyon = self._toplam_emisyon_hesapla()
        
        # Fiyat Belirleme (Arz-Talep Modeli) - Sadece ETS aktifse
        if self.model.yil >= ETS_PARAMS["PILOT_BASLANGIC"] and self.cap > 0 and toplam_emisyon > 0:
            # Emisyon/Cap oranına göre fiyat belirleme
            arz_talep_orani = toplam_emisyon / self.cap
            
            # Fiyat formülü: Oran > 1 ise fiyat hızla artar
            if arz_talep_orani > 1:
                self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"] * (arz_talep_orani ** 2)
            else:
                self.piyasa_fiyati = ETS_PARAMS["TABAN_FIYAT"] * (arz_talep_orani ** 0.5)
            
            # Taban ve tavan sınırları
            self.piyasa_fiyati = max(ETS_PARAMS["TABAN_FIYAT"], 
                                    min(ETS_PARAMS["TAVAN_FIYAT"], self.piyasa_fiyati))
        else:
            # ETS öncesi dönem - fiyat sıfır
            self.piyasa_fiyati = 0
        
        # Model fiyatını güncelle
        self.model.karbon_fiyati = self.piyasa_fiyati
        self.fiyat_gecmisi.append(self.piyasa_fiyati)
        
        # Açık artırma geliri hesapla (Tam uygulama döneminde)
        if self.model.yil >= ETS_PARAMS["TAM_UYGULAMA"] and self.piyasa_fiyati > 0:
            acik_artirma_orani = 0.3  # %30 açık artırma
            acik_artirma_miktari = self.cap * acik_artirma_orani
            self.toplam_gelir += acik_artirma_miktari * self.piyasa_fiyati
    
    def _toplam_emisyon_hesapla(self):
        """Aktif tesislerin toplam emisyonunu hesaplar."""
        return sum(
            agent.emisyon for agent in self.model.agents
            if hasattr(agent, 'ajan_tipi') and agent.ajan_tipi in ["Tesis", "IhracatciTesis"] 
            and agent.durum != "Kapali"
        )


class EndustriyelTesis(Agent):
    """
    Endüstriyel Tesis Ajanı - Geliştirilmiş karar mekanizması. 
    
    Özellikler:
    1. MAC Analizi (McKinsey 2009)
    2. NPV Hesabı (standart finans modeli)
    3. Tahsisat ve Bankalama (EU ETS)
    4. Kapanma Eşiği
    
    Referanslar:
    - [cite: McKinsey 2009] MAC eğrileri
    - [cite: Tang et al. 2022] Firma karar mekanizması
    - [cite: EU ETS Directive] Tahsisat kuralları
    """
    
    def __init__(self, model, sektor, city="Istanbul"):
        super().__init__(model)
        self.ajan_tipi = "Tesis"
        self.sektor = sektor
        self.city = city
        self.profil = SEKTOR_PROFILLERI. get(sektor, SEKTOR_PROFILLERI["Sanayi"])
        
        # Emisyon (heterojen) - il katsayısı ile çarpılır
        il_katsayi = model.il_katsayilari. get(city, {}).get(sektor. lower(), 1.0) if hasattr(model, 'il_katsayilari') else 1.0
        self.emisyon = self.profil["baz_emisyon"] * np.random.uniform(0.7, 1.3) * il_katsayi  # Mt CO₂/yıl
        self.baslangic_emisyon = self.emisyon
        
        # SKDM:  İhracatçı mı? 
        self.ihracatci = random.random() < self.profil["ihracat_orani"]
        
        # Durum
        self.durum = "Aktif"  # Aktif, Donusum, Temiz, Kapali
        self.yatirim_durumu = None
        self.kalan_yatirim_suresi = 0
        self.emisyon_azalma_potansiyeli = 0
        
        # Maliyet parametreleri
        self.maliyet_limit = self.profil["maliyet_limit"]  # Milyon $/yıl
        self. yatirim_bedeli = self. profil["yatirim_bedeli"]  # Milyon $
        self. duyarlilik = self.profil["duyarlilik"]
        
        # ETS mekanizmaları (YENİ)
        self.ucretsiz_tahsisat = 0  # tCO₂/yıl
        self.izin_bankasi = 0  # tCO₂ (birikmiş izinler)
        self.net_emisyon = 0  # tCO₂ (tahsisat sonrası)
        
        # Ceza takibi (YENİ)
        self.ceza_durumu = False
        self.ceza_miktari = 0.0  # Milyon $
        
    def step(self):
        """Her yıl için tesis karar adımı."""
        if self.durum == "Kapali":
            return
        
        # 1. Efektif Karbon Fiyatı (SKDM dahil)
        if self.ihracatci and self.profil["skdm_kapsam"]:
            efektif_fiyat = max(self.model.karbon_fiyati, self.model.ab_skdm_fiyat)
        else:
            efektif_fiyat = self.model.karbon_fiyati
        
        # 2. ÜCRETSİZ TAHSİSAT HESAPLA (YENİ)
        if self.model.yil >= ETS_PARAMS["PILOT_BASLANGIC"]:
            if self.model.yil < ETS_PARAMS["TAM_UYGULAMA"]: 
                ucretsiz_oran = 1.0  # Pilot dönem %100
            else:
                ucretsiz_oran = 0.7  # Tam uygulama %70
            
            self.ucretsiz_tahsisat = self.baslangic_emisyon * ucretsiz_oran
            
            # BANKALAMA MEKANİZMASI (YENİ)
            fazla_tahsisat = self.ucretsiz_tahsisat - self.emisyon
            
            if fazla_tahsisat > 0:
                # Fazla izni bankala
                self.izin_bankasi += fazla_tahsisat
                self.net_emisyon = 0
            else:
                # Önce bankadan kullan
                eksik = abs(fazla_tahsisat)
                bankadan_kullan = min(eksik, self.izin_bankasi)
                self.izin_bankasi -= bankadan_kullan
                self.net_emisyon = eksik - bankadan_kullan
        else:
            # ETS öncesi dönem
            self.net_emisyon = 0
        
        # 3. Yatırım süreci devam ediyor mu?
        if self. kalan_yatirim_suresi > 0:
            self. kalan_yatirim_suresi -= 1
            if self.kalan_yatirim_suresi == 0:
                self.emisyon *= (1 - self.emisyon_azalma_potansiyeli)
                self.durum = "Temiz"
                self.ceza_durumu = False  # Yatırım tamamlandı, ceza sıfırlandı
            return
        
        # 4. Karar Mekanizması
        if self.durum == "Aktif":
            karar = self._karar_ver(efektif_fiyat)
            
            if karar == "yatirim":
                self._yatirim_baslat(efektif_fiyat)
            elif karar == "kapat":
                self. durum = "Kapali"
                self.emisyon = 0
    
    def _karar_ver(self, efektif_fiyat):
        """
        Geliştirilmiş karar algoritması - Hibrit ve Dinamik Yapı. 
        
        Üç aşamalı karar mekanizması:
        1. MAC Analizi:  Karbon fiyatı vs marjinal azaltım maliyeti
        2. NPV Hesabı: Yatırımın net bugünkü değeri (her MAC önlemi için)
        3. Kapanma Eşiği:  Karbon maliyeti faaliyet limitini geçerse
        
        Referanslar:
        - MAC Analizi: [cite: McKinsey 2009]
        - NPV Formülü: [cite: Brealey et al. 2020, Corporate Finance]
        - Kapanma Eşiği: [cite:  Tang et al. 2022]
        """
        # Teşvik duyarlı sektörler (Tarım)
        if self. duyarlilik == "Tesvik":
            if self.model.tesvik_miktari >= (self.yatirim_bedeli * 0.6 * 1000):
                return "yatirim"
            return "bekle"
        
        # Ceza aldıysa zorla yatırım yap
        if self.ceza_durumu:
            return "yatirim"
        
        # --- GELİŞTİRİLMİŞ KARAR MEKANİZMASI ---
        
        # NPV Parametreleri
        r = 0.08  # İskonto oranı (Türkiye risk primi dahil)
        ekonomik_omur = 10  # Yatırım ekonomik ömrü (yıl)
        
        # Her MAC önlemi için NPV hesapla
        mac_onlemler = self. profil. get("mac_onlemler", {})
        en_iyi_npv = -9999
        en_iyi_onlem = None
        
        for onlem_adi, onlem in mac_onlemler.items():
            # 1. MAC Kontrolü
            if onlem["mac"] >= efektif_fiyat: 
                continue  # Bu önlem karbon fiyatından pahalı, atla
            
            # 2. NPV Hesabı (her önlem için özel)
            yillik_azaltim = self.emisyon * onlem["potansiyel"]  # tCO₂/yıl
            yillik_tasarruf = yillik_azaltim * efektif_fiyat * 1e6  # $/yıl (Mt -> ton)
            
            # Yatırım maliyeti
            if onlem["mac"] > 0:
                yatirim_maliyeti = yillik_azaltim * onlem["mac"] * 1e6  # $
            else:
                yatirim_maliyeti = 0  # Negatif MAC = kar ediyor
            
            # NPV Formülü: -Yatırım + Σ(Tasarruf / (1+r)^t)
            npv = -yatirim_maliyeti
            for t in range(1, ekonomik_omur + 1):
                npv += yillik_tasarruf / ((1 + r) ** t)
            
            # En iyi NPV'yi kaydet
            if npv > en_iyi_npv: 
                en_iyi_npv = npv
                en_iyi_onlem = (onlem_adi, onlem)
        
        # Yatırım kararı:  En iyi NPV pozitifse
        if en_iyi_npv > 0:
            self._yatirim_onlemi_kaydet = en_iyi_onlem  # Sonraki adımda kullanmak için
            return "yatirim"
        
        # 3. Kapanma Eşiği:  Net emisyon maliyeti limitini geçerse
        if self.net_emisyon > 0:
            karbon_maliyeti = self. net_emisyon * efektif_fiyat  # Mt × $/ton = Milyon $
            if karbon_maliyeti > self.maliyet_limit:
                return "kapat"
        
        return "bekle"
    
    def _yatirim_baslat(self, karbon_fiyati):
        """En uygun yatırımı başlatır."""
        # Önceki adımda kaydedilen en iyi önlemi kullan
        if hasattr(self, '_yatirim_onlemi_kaydet') and self._yatirim_onlemi_kaydet:
            onlem_adi, onlem = self._yatirim_onlemi_kaydet
        else:
            # Fallback: İlk uygun önlemi seç
            mac_onlemler = self.profil.get("mac_onlemler", {})
            onlem_adi, onlem = None, None
            for adi, o in mac_onlemler.items():
                if o["mac"] < karbon_fiyati: 
                    onlem_adi, onlem = adi, o
                    break
        
        if onlem: 
            self. yatirim_durumu = onlem_adi
            self. kalan_yatirim_suresi = onlem["sure"]
            self.emisyon_azalma_potansiyeli = onlem["potansiyel"]
            self.durum = "Donusum"
        else:
            # MAC'tan uygun önlem yoksa basit dönüşüm
            self.yatirim_durumu = "genel_iyilestirme"
            self.kalan_yatirim_suresi = 3
            self.emisyon_azalma_potansiyeli = 0.20
            self.durum = "Donusum"


class IhracatciAjani(EndustriyelTesis):
    """
    İhracatçı Ajan - CBAM (SKDM) etkisini ve dış ticaret tepkisini modeller.
    
    Bu ajan, AB Sınırda Karbon Düzenleme Mekanizması'nın (CBAM/SKDM)
    Türk ihracatçılarına etkisini simüle eder.
    
    Referanslar:
    - [cite: EU Regulation 2023/956] CBAM kuralları
    - [cite:  OECD 2024] Sınır karbon ayarlaması etkileri
    """
    
    def __init__(self, model, sektor, city="Istanbul"):
        super().__init__(model, sektor, city=city)
        self.ajan_tipi = "IhracatciTesis"
        self.ihracat_payi = self.profil["ihracat_orani"]
        self.cbam_maliyeti = 0.0  # Milyon $/yıl
        self. rekabet_gucu_indeksi = 1.0  # 0-1 arası
        
    def step(self):
        """İhracatçı ajan adımı - CBAM maliyeti hesaplar."""
        if self.durum == "Kapali":
            return
        
        # CBAM Maliyeti Hesaplama
        if self.ihracatci and self.profil["skdm_kapsam"]:
            # CBAM maliyeti = Emisyon × AB SKDM fiyatı
            self.cbam_maliyeti = self.emisyon * self.model.ab_skdm_fiyat  # Milyon $
            
            # Türkiye'deki karbon fiyatı CBAM'dan düşülebilir
            if self.model.karbon_fiyati > 0:
                dusilebilir_miktar = min(self.cbam_maliyeti, 
                                          self.emisyon * self.model.karbon_fiyati)
                self.cbam_maliyeti -= dusilebilir_miktar
            
            # Rekabet gücü indeksini güncelle
            self._rekabet_gucu_hesapla()
        else:
            self.cbam_maliyeti = 0.0
        
        # Üst sınıfın step metodunu çağır
        super().step()
    
    def _rekabet_gucu_hesapla(self):
        """CBAM maliyetine göre rekabet gücü indeksini hesaplar."""
        maliyet_esik = 50  # Milyon $
        if self.cbam_maliyeti > 0:
            self.rekabet_gucu_indeksi = max(0.3, 1.0 - (self.cbam_maliyeti / maliyet_esik) * 0.1)
        else:
            self.rekabet_gucu_indeksi = 1.0


class MRVAjani(Agent):
    """
    MRV (İzleme, Raporlama, Doğrulama) Ajanı - Denetim ve ceza mekanizmasını yönetir.
    
    Bu ajan, ETS sisteminin uyum mekanizmasını simüle eder: 
    - Tesislerin rastgele denetimi
    - Raporlama uyumsuzluğu tespiti
    - Ceza uygulama ve tesislere geri bildirim
    
    Referanslar:
    - [cite: EU ETS Directive] MRV gereksinimleri
    - [cite: Zhou et al. 2016] Uyum mekanizması modellemesi
    """
    
    def __init__(self, model):
        super().__init__(model)
        self.ajan_tipi = "MRV"
        self. denetim_olasiligi = 0.2  # %20 rastgele denetim
        self.ceza_miktari = ETS_PARAMS["CEZA_MIKTARI"]  # $/ton CO₂
        self.toplam_denetim = 0
        self.toplam_ceza = 0.0  # Milyon $
        self. uyumsuz_tesis_sayisi = 0
        
    def step(self):
        """MRV denetim adımı - Tesisleri rastgele denetle ve gerekirse ceza kes."""
        self. uyumsuz_tesis_sayisi = 0
        
        for agent in self.model.agents:
            # Sadece tesis ajanlarını denetle
            if hasattr(agent, 'ajan_tipi') and agent.ajan_tipi in ["Tesis", "IhracatciTesis"]:
                if agent.durum != "Kapali":
                    # Rastgele denetim kontrolü
                    if random.random() < self.denetim_olasiligi: 
                        self.toplam_denetim += 1
                        
                        # Raporlanan vs Gerçek emisyon kontrolü simülasyonu
                        # %5 uyumsuzluk olasılığı (eksik raporlama)
                        if random.random() < 0.05:
                            self.uyumsuz_tesis_sayisi += 1
                            
                            # Ceza hesapla:  Eksik raporlanan emisyon × ceza birim fiyatı
                            eksik_emisyon = agent.emisyon * np.random.uniform(0.05, 0.15)  # Mt
                            ceza = eksik_emisyon * self. ceza_miktari  # Milyon $
                            self.toplam_ceza += ceza
                            
                            # EKLEME: Tesise ceza durumunu bildir
                            agent.ceza_durumu = True
                            agent.ceza_miktari = ceza


class Hanehalki(Agent):
    """
    Hanehalkı Ajanı - Konut enerji tüketimi ve fiyat duyarlılığını modeller.
    
    Referanslar:
    - Labandeira et al. (2017). A meta-analysis on the price elasticity of energy demand
    - [cite: TÜİK 2024] Hanehalkı enerji tüketimi istatistikleri
    """
    
    def __init__(self, model, city="Istanbul"):
        super().__init__(model)
        self.ajan_tipi = "Hanehalki"
        self.city = city
        
        # Gelir grubu ve tüketim parametreleri
        self.gelir_grubu = random.choice(["dusuk", "orta", "yuksek"])
        
        # Gelir grubuna göre elektrik tüketimi (kWh/yıl)
        tuketim_aralik = {
            "dusuk": (1500, 2500),
            "orta": (2500, 4000),
            "yuksek": (4000, 6000)
        }
        min_t, max_t = tuketim_aralik[self.gelir_grubu]
        self. tuketim = np.random.uniform(min_t, max_t)  # kWh/yıl
        
        # Emisyon hesabı:  kWh -> MWh -> ton CO₂
        self.emisyon = (self.tuketim / 1000) * model. EMISYON_FAKTORU_TR  # ton CO₂/yıl
        self.baslangic_emisyon = self.emisyon
        self.durum = "Aktif"
        
        # Fiyat elastikiyesi (Labandeira et al. 2017)
        self.elastikiyet = {
            "dusuk": -0.6,
            "orta": -0.4,
            "yuksek": -0.25
        }[self.gelir_grubu]
    
    def step(self):
        """Hanehalkı tüketim ve emisyon güncelleme adımı."""
        if self. durum != "Aktif":
            return
        
        # Karbon fiyatı etkisi - elastikiyet modeli
        if self.model.karbon_fiyati > 0:
            fiyat_orani = self.model.karbon_fiyati / 100  # 100 $/ton referans
            fiyat_etkisi = max(0.5, 1 + (self.elastikiyet * fiyat_orani))
            
            # Tüketim ve emisyonu güncelle
            self. emisyon = (self.tuketim / 1000) * self.model. EMISYON_FAKTORU_TR * fiyat_etkisi
        else:
            self.emisyon = (self.tuketim / 1000) * self.model.EMISYON_FAKTORU_TR


class ProjeGelistirici(Agent):
    """
    Yenilenebilir Enerji Proje Geliştirici - NPV analizi ile karar verir.
    
    Referanslar:
    - Brealey et al. (2020). Principles of Corporate Finance
    - [cite:  IRENA 2024] Yenilenebilir enerji maliyetleri
    """
    
    def __init__(self, model):
        super().__init__(model)
        self.ajan_tipi = "ProjeGelistirici"
        self.sermaye = np.random.uniform(10e6, 100e6)  # Milyon $
        self.risk_primi = np.random.uniform(0.08, 0.15)
        self.projeler = []
        self.toplam_kapasite = 0  # MW
        
    def step(self):
        """Her yıl için yatırım kararı."""
        karbon_fiyati = self.model.karbon_fiyati
        tesvik = self.model.tesvik_miktari
        
        proje_tipleri = {
            "GES": {"kapasite": 10, "yatirim": 7e5, "kf": 0.18, "omur": 25},  # MW, $/MW, kapasite faktörü, yıl
            "RES": {"kapasite": 20, "yatirim": 1.2e6, "kf": 0.35, "omur": 25}
        }
        
        for proje_tipi, params in proje_tipleri. items():
            toplam_yatirim = params["kapasite"] * params["yatirim"]  # $
            
            if self.sermaye >= toplam_yatirim:
                npv = self._npv_hesapla(params, karbon_fiyati, tesvik)
                
                if npv > 0:
                    self.sermaye -= toplam_yatirim
                    self.toplam_kapasite += params["kapasite"]
                    self.model.yenilenebilir_kapasite += params["kapasite"]
                    self.projeler.append({
                        "tip": proje_tipi,
                        "kapasite": params["kapasite"],
                        "yil": self.model.yil
                    })
    
    def _npv_hesapla(self, params, karbon_fiyati, tesvik):
        """Net Bugünkü Değer hesaplar."""
        kapasite = params["kapasite"]
        yatirim = kapasite * params["yatirim"]
        kf = params["kf"]
        omur = params["omur"]
        
        yillik_uretim = kapasite * kf * 8760  # MWh/yıl
        enerji_fiyati = 80  # $/MWh
        enerji_geliri = yillik_uretim * enerji_fiyati
        karbon_geliri = yillik_uretim * 0.5 * karbon_fiyati  # 0.5 ton CO₂/MWh kaçınılmış
        tesvik_geliri = tesvik * kapasite
        
        yillik_gelir = enerji_geliri + karbon_geliri + tesvik_geliri
        
        npv = -yatirim
        for t in range(1, omur + 1):
            npv += yillik_gelir / ((1 + self.risk_primi) ** t)
        
        return npv


# =============================================================================
# ANA MODEL
# =============================================================================

class TurkiyeETSModel(Model):
    """
    Türkiye ETS Simülasyon Modeli - Düzeltilmiş ve Geliştirilmiş Versiyon
    
    Özellikler:
    -----------
    ✅ PiyasaOperatoru ve MRV agents listesinde
    ✅ Tahsisat ve bankalama mekanizması
    ✅ Ceza geri bildirimi tesislere aktarılıyor
    ✅ NPV hesabı MAC önemleriyle entegre
    ✅ İl bazlı tesis dağılımı
    ✅ 2025-2035 zaman çizelgesi
    
    Referanslar:
    - [cite: Yu et al. 2020] ABM metodolojisi
    - [cite: EU ETS] Cap & Trade kuralları
    """
    
    # Türkiye ortalama emisyon faktörü [Kaynak: Enerji Bakanlığı 2024]
    EMISYON_FAKTORU_TR = 0.442  # ton CO₂/MWh
    
    def __init__(self,
                 n_enerji=40,
                 n_sanayi=30,
                 n_tarim=30,
                 n_yatirimci=15,
                 n_ihracatci=10,
                 n_hanehalki=50,
                 baslangic_cap=80,  # Mt CO₂
                 cap_azalma_orani=0.03,
                 ab_skdm_fiyat=90,  # $/ton
                 tesvik_miktari=50000,  # $/MW
                 vergi_artis_orani=5,  # %
                 senaryo_tipi="Siki_ETS",
                 veritabani_kullan=False,
                 random_seed=None):
        """Model başlatıcı."""
        
        # Random seed
        if random_seed is None:
            random_seed = int(datetime.now().timestamp() * 1000) % 100000
        super().__init__(seed=random_seed)
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        # --- TEMEL PARAMETRELER ---
        self.yil = 2025
        self.karbon_fiyati = 0  # $/ton
        self.ab_skdm_fiyat = ab_skdm_fiyat
        self.tesvik_miktari = tesvik_miktari
        self.vergi_artis_orani = vergi_artis_orani
        self.yenilenebilir_kapasite = 0  # MW
        
        # --- SENARYO YÖNETİMİ ---
        self. senaryo_tipi = senaryo_tipi
        self. ets_aktif = False
        self.acik_artirma_aktif = False
        
        # --- VERİTABANI ENTEGRASYİYONU ---
        self.il_katsayilari = {}
        if veritabani_kullan: 
            self._veritabani_yukle()
        
        # --- İL LİSTESİ ---
        self. iller = list(self.il_katsayilari.keys()) if self.il_katsayilari else [
            "Istanbul", "Ankara", "Izmir", "Bursa", "Kocaeli", "Adana",
            "Gaziantep", "Konya", "Antalya", "Mersin", "Kayseri", "Eskisehir",
            "Sakarya", "Denizli", "Manisa", "Zonguldak", "Hatay", "Samsun"
        ]
        
        # --- 1. PİYASA OPERATÖRÜ (DÜZELTİLMİŞ) ---
        self.piyasa_operatoru = PiyasaOperatoru(self, baslangic_cap, cap_azalma_orani)
        self.agents.add(self.piyasa_operatoru)  # ✅ AGENTS LİSTESİNE EKLENDİ
        
        # --- 2. MRV MERKEZİ (DÜZELTİLMİŞ) ---
        self.mrv_merkezi = MRVAjani(self)
        self.agents.add(self.mrv_merkezi)  # ✅ AGENTS LİSTESİNE EKLENDİ
        
        # --- 3. TESİSLER (İl bazlı dağıtım) ---
        for _ in range(n_enerji):
            city = random.choice(self. iller)
            EndustriyelTesis(self, "Enerji", city=city)
        
        for _ in range(n_sanayi):
            city = random. choice(self.iller)
            EndustriyelTesis(self, "Sanayi", city=city)
        
        for _ in range(n_tarim):
            city = random.choice(self.iller)
            EndustriyelTesis(self, "Tarim", city=city)
        
        # --- 4. İHRACATÇI AJANLAR ---
        for _ in range(n_ihracatci):
            city = random.choice(self.iller)
            IhracatciAjani(self, "Sanayi", city=city)
        
        # --- 5. HANEHALKİ AJANLARI ---
        for _ in range(n_hanehalki):
            city = random.choice(self.iller)
            Hanehalki(self, city=city)
        
        # --- 6. YATIRIMCILAR ---
        for _ in range(n_yatirimci):
            ProjeGelistirici(self)
        
        # --- VERİ TOPLAMA ---
        self.datacollector = DataCollector(
            model_reporters={
                "Yil": lambda m: m.yil,
                "Karbon_Fiyati": lambda m: m. karbon_fiyati,
                "Toplam_Emisyon": lambda m: self._toplam_emisyon(m),
                "Aktif_Tesis": lambda m: self._tesis_sayisi(m, "Aktif"),
                "Donusum_Tesis": lambda m: self._tesis_sayisi(m, "Donusum"),
                "Temiz_Tesis": lambda m:  self._tesis_sayisi(m, "Temiz"),
                "Kapali_Tesis": lambda m: self._tesis_sayisi(m, "Kapali"),
                "Yenilenebilir_Kapasite_MW": lambda m: m.yenilenebilir_kapasite,
                "Cap":  lambda m: m.piyasa_operatoru.cap,
                "Senaryo": lambda m: m. senaryo_tipi,
                "CBAM_Toplam_Maliyet": lambda m: self._cbam_toplam_maliyet(m),
                "MRV_Toplam_Ceza": lambda m: m.mrv_merkezi.toplam_ceza,
                "Ihracatci_Tesis": lambda m: self._ihracatci_sayisi(m),
                "Hanehalki_Sayisi": lambda m: self._hanehalki_sayisi(m),
                "Hanehalki_Emisyon": lambda m: self._hanehalki_emisyon(m)
            }
        )
    
    def _veritabani_yukle(self):
        """SQLite veritabanından il katsayılarını yükler."""
        db_path = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                df_il = pd.read_sql("SELECT * FROM il_katsayilari", conn)
                
                if not df_il.empty and 'Bolge' in df_il.columns:
                    for _, row in df_il.iterrows():
                        self.il_katsayilari[row['Bolge']] = {
                            'enerji': row.get('Enerji_Katsayisi', 1.0),
                            'sanayi': row.get('Sanayi_Katsayisi', 1.0),
                            'tarim': row.get('Tarim_Katsayisi', 1.0)
                        }
                
                conn.close()
                print(f"✅ Veritabanı yüklendi: {len(self.il_katsayilari)} bölge")
                
            except Exception as e: 
                print(f"⚠️ Veritabanı yüklenemedi: {e}")
    
    def _toplam_emisyon(self, model):
        """Toplam emisyonu hesaplar."""
        return sum(
            a.emisyon for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis", "Hanehalki"] 
            and getattr(a, 'durum', 'Aktif') != "Kapali"
        )
    
    def _tesis_sayisi(self, model, durum):
        """Belirli durumdaki tesis sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi in ["Tesis", "IhracatciTesis"] 
            and a.durum == durum
        )
    
    def _cbam_toplam_maliyet(self, model):
        """Toplam CBAM maliyetini hesaplar."""
        return sum(
            a.cbam_maliyeti for a in model.agents
            if hasattr(a, 'cbam_maliyeti')
        )
    
    def _ihracatci_sayisi(self, model):
        """İhracatçı tesis sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "IhracatciTesis"
        )
    
    def _hanehalki_sayisi(self, model):
        """Hanehalkı ajan sayısını hesaplar."""
        return sum(
            1 for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Hanehalki"
        )
    
    def _hanehalki_emisyon(self, model):
        """Hanehalkı toplam emisyonunu hesaplar."""
        return sum(
            a.emisyon for a in model.agents
            if hasattr(a, 'ajan_tipi') and a.ajan_tipi == "Hanehalki"
        )
    
    def step(self):
        """
        Model adımı (bir yıl) - Zaman Çizelgesi Mantığı. 
        
        2025-2035 Türkiye ETS Yol Haritası:
        - 2025: Hazırlık dönemi
        - 2026: Pilot ETS başlangıcı
        - 2028: Tam uygulama ve Açık Artırma
        - 2030: AB CBAM tam uygulama
        - 2035: Hedef yılı
        """
        
        # --- ZAMAN ÇİZELGESİ MANTIĞI ---
        
        # 2026: Pilot ETS Başlangıcı
        if self.yil == 2026:
            if not self.ets_aktif:
                self.ets_aktif = True
                print(f"📢 {self.yil}:  Pilot ETS Başlatıldı - Karbon Fiyatı: ${self.karbon_fiyati}/ton")
        
        # 2028: Tam Uygulama ve Açık Artırma
        elif self.yil == 2028:
            if not self.acik_artirma_aktif:
                self.acik_artirma_aktif = True
                print(f"📢 {self.yil}:  Tam Uygulama ve Açık Artırma (Auction) Devreye Girdi")
        
        # --- VERİ TOPLAMA ---
        self.datacollector.collect(self)
        
        # --- TÜM AJANLARI ÇALIŞTIR ---
        # Not: PiyasaOperatoru ve MRV artık agents listesinde, otomatik çağrılacak
        self.agents.shuffle_do("step")
        
        # --- YILI İLERLET ---
        self.yil += 1
    
    def run_simulation(self, years=11):
        """Simülasyonu çalıştırır."""
        for _ in range(years):
            self.step()
        return self.datacollector.get_model_vars_dataframe()


# =============================================================================
# SENARYO KARŞILAŞTIRMASI
# =============================================================================

def senaryo_karsilastirmasi():
    """Farklı politika senaryolarını karşılaştırır."""
    print("=" * 70)
    print("TR-ZERO:  AJAN TABANLI KARBON PİYASASI SİMÜLASYONU")
    print("v2.1 - Düzeltilmiş Versiyon")
    print("=" * 70)
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("-" * 70)
    
    # Senaryolar (DÜZELTİLMİŞ CAP DEĞERLERİ)
    senaryolar = {
        "BAU": {
            "baslangic_cap": 9999,
            "cap_azalma_orani": 0,
            "tesvik_miktari": 0,
            "ab_skdm_fiyat": 0,
            "renk": "#94a3b8"
        },
        "Yumusak_ETS": {
            "baslangic_cap": 75,
            "cap_azalma_orani": 0.02,
            "tesvik_miktari": 30000,
            "ab_skdm_fiyat": 60,
            "renk": "#3b82f6"
        },
        "Siki_ETS": {
            "baslangic_cap":  60,
            "cap_azalma_orani": 0.04,
            "tesvik_miktari": 50000,
            "ab_skdm_fiyat": 90,
            "renk":  "#22c55e"
        },
        "ETS_Tesvik": {
            "baslangic_cap": 60,
            "cap_azalma_orani": 0.04,
            "tesvik_miktari": 150000,
            "ab_skdm_fiyat": 90,
            "renk": "#8b5cf6"
        }
    }
    
    sonuclar = {}
    
    for senaryo_adi, params in senaryolar.items():
        print(f"\n🔄 {senaryo_adi} senaryosu çalıştırılıyor...")
        
        model = TurkiyeETSModel(
            baslangic_cap=params["baslangic_cap"],
            cap_azalma_orani=params["cap_azalma_orani"],
            tesvik_miktari=params["tesvik_miktari"],
            ab_skdm_fiyat=params["ab_skdm_fiyat"]
        )
        
        df = model.run_simulation(years=11)
        df["Senaryo"] = senaryo_adi
        sonuclar[senaryo_adi] = df
        
        # Sonuç özeti
        son_emisyon = df['Toplam_Emisyon']. iloc[-1]
        son_fiyat = df['Karbon_Fiyati'].iloc[-1]
        temiz_tesis = df['Temiz_Tesis'].iloc[-1]
        
        print(f"   ✅ Tamamlandı:")
        print(f"      • 2035 Emisyon: {son_emisyon:.2f} Mt")
        print(f"      • Karbon Fiyatı:  ${son_fiyat:.0f}/ton")
        print(f"      • Temiz Tesis:  {temiz_tesis:.0f}")
    
    # Özet tablo
    _ozet_tablo_yazdir(sonuclar)
    
    return sonuclar


def _ozet_tablo_yazdir(sonuclar):
    """Özet tablo yazdırır."""
    print("\n" + "=" * 80)
    print("SENARYO KARŞILAŞTIRMA TABLOSU (2035)")
    print("=" * 80)
    print(f"{'Senaryo':<18} {'Emisyon (Mt)':<14} {'Azaltım (%)':<14} {'Fiyat ($/t)':<14} {'Temiz Tesis':<14}")
    print("-" * 80)
    
    bau_emisyon = sonuclar["BAU"]["Toplam_Emisyon"].iloc[-1]
    
    for senaryo_adi, df in sonuclar.items():
        emisyon = df["Toplam_Emisyon"].iloc[-1]
        azaltim = (bau_emisyon - emisyon) / bau_emisyon * 100 if bau_emisyon > 0 else 0
        fiyat = df["Karbon_Fiyati"].iloc[-1]
        temiz = df["Temiz_Tesis"].iloc[-1]
        
        print(f"{senaryo_adi:<18} {emisyon: <14.2f} {azaltim: <14.1f} {fiyat:<14.0f} {int(temiz):<14}")
    
    print("=" * 80)


# =============================================================================
# CSV KAYDETME
# =============================================================================

def csv_kaydet(sonuclar):
    """Dashboard'un beklediği formatta CSV'leri kaydeder."""
    isim_eslesme = {
        "BAU": "bau",
        "Yumusak_ETS": "yumusak_ets",
        "Siki_ETS":  "siki_ets",
        "ETS_Tesvik": "ets_tesvik"
    }
    
    for senaryo_adi, df in sonuclar.items():
        dosya_adi = isim_eslesme.get(senaryo_adi, senaryo_adi. lower())
        csv_path = os.path.join(OUTPUT_DIR, f"senaryo_{dosya_adi}.csv")
        df.to_csv(csv_path, index=False)
        print(f"   📄 {csv_path}")


# =============================================================================
# ANA ÇALIŞTIRMA
# =============================================================================

if __name__ == "__main__": 
    print("\n" + "=" * 70)
    print("🌱 TR-ZERO:  AJAN TABANLI KARBON PİYASASI SİMÜLASYONU")
    print("   Türkiye Emisyon Ticaret Sistemi (2025-2035)")
    print("   v2.1 - Düzeltilmiş Versiyon")
    print("=" * 70)
    
    # Senaryo karşılaştırması
    sonuclar = senaryo_karsilastirmasi()
    
    # CSV kaydet
    print("\n📁 CSV dosyaları kaydediliyor...")
    csv_kaydet(sonuclar)
    
    print(f"\n✅ Tüm sonuçlar '{OUTPUT_DIR}' klasörüne kaydedildi.")
    print("\n🎉 Simülasyon tamamlandı!")
    print("\n💡 Dashboard'u çalıştırmak için:")
    print("   streamlit run src/dashboard_v4.py")