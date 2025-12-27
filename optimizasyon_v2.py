"""
TR-ZERO: Basit Politika Etki Simülasyonu (Mesa 3.x Uyumlu)
=========================================================

Bu modül, karbon vergisi ve teşvik politikalarının sektörel
dönüşüm üzerindeki etkisini simüle eder. 

Kaynaklar:
----------
[1] Yu et al. (2020).  Modeling the ETS from an agent-based perspective.
[2] AB SKDM Regulation 2023/956

Yazar: [Adınız Soyadınız]
Tarih: Aralık 2024
"""

from mesa import Agent, Model
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
import pandas as pd
import random
import os

# Çıktı klasörü
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


class UniversalAgent(Agent):
    """
    Evrensel Sektör Ajanı (Enerji + Sanayi + Tarım)
     
    SKDM mantığı dahil edilmiştir: İhracatçı firmalar
    AB sınır vergisini de dikkate alır. 
    """
     
    def __init__(self, model, sektor):
        super().__init__(model)
        self.sektor = sektor
        self.durum = "Kirleten"
        self.ajan_tipi = "Firma"
        
        # SKDM: Sanayici %40 ihtimalle ihracatçıdır
        self.ihracatci = True if random.random() < 0.4 and sektor in ["Enerji", "Sanayi"] else False
        
        # Sektörel Parametreler
        if sektor == "Enerji":
            self.limit = 90
            self.yatirim_bedeli = 200
            self.duyarli_oldugu = "Vergi"
        elif sektor == "Sanayi":
            self.limit = 110
            self.yatirim_bedeli = 250
            self.duyarli_oldugu = "Vergi"
        elif sektor == "Tarım":
            self.limit = 999
            self.yatirim_bedeli = 300
            self.duyarli_oldugu = "Teşvik"
        else:
            self.limit = 100
            self.yatirim_bedeli = 200
            self.duyarli_oldugu = "Vergi"
        
        self.yatirim_taksiti = self.yatirim_bedeli / 10

    def step(self):
        """Her yıl için ajan karar adımı."""
        # 1. VERGİ YÜKÜ (SKDM Dahil)
        if self.ihracatci:
            vergi_yuku = max(self.model.tax, self.model.ab_tax)
        else:
            vergi_yuku = self.model.tax
        
        devlet_destegi = self.model.tesvik
        
        # 2.  KARAR ALGORİTMASI (MAC Analizi)
        if self.duyarli_oldugu == "Vergi":
            maliyet_eski = 40 + (0.9 * vergi_yuku)
            maliyet_yeni = 40 + (0.2 * vergi_yuku) + self.yatirim_taksiti
            
            if self.durum == "Kirleten":
                if maliyet_yeni < maliyet_eski and maliyet_yeni < self.limit:
                    self.durum = "Temiz"
                elif maliyet_eski >= self.limit:
                    self.durum = "Kapalı"
                    
        elif self.duyarli_oldugu == "Teşvik":
            # Tarım sadece Teşvik yeterliyse dönüşür
            if devlet_destegi >= (self.yatirim_bedeli * 0.6):
                self.durum = "Temiz"


class EkonomiModeli(Model):
    """
    Ekonomi Simülasyon Modeli (Mesa 3.x Uyumlu)
     
    Karbon vergisi, AB SKDM ve teşvik politikalarının
    sektörel dönüşüm üzerindeki etkisini simüle eder.
    """
     
    def __init__(self, rate=5, ab_tax=90, tesvik=200, seed=42):
        """
        Model başlatıcı.
         
        Args:
            rate: Yıllık vergi artış oranı ($/yıl)
            ab_tax: AB SKDM fiyatı ($/ton)
            tesvik: Tarım teşvik miktarı ($)
            seed: Rastgelelik tohumu
        """
        super().__init__(seed=seed)
        
        self.tax = 0
        self.rate = rate
        self.ab_tax = ab_tax
        self.tesvik = tesvik
        
        # Ajan dağılımı
        for _ in range(40):
            UniversalAgent(self, "Enerji")
        for _ in range(30):
            UniversalAgent(self, "Sanayi")
        for _ in range(30):
            UniversalAgent(self, "Tarım")
        
        # Veri toplama
        self.dc = DataCollector(model_reporters={
            "Vergi": lambda m: m.tax,
            "Enerji_Kirleten": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Enerji" and a.durum == "Kirleten"),
            "Enerji_Temiz": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Enerji" and a.durum == "Temiz"),
            "Sanayi_Kirleten": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Sanayi" and a.durum == "Kirleten"),
            "Sanayi_Temiz": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Sanayi" and a.durum == "Temiz"),
            "Sanayi_Kapali": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Sanayi" and a.durum == "Kapalı"),
            "Tarim_Temiz": lambda m: sum(1 for a in m.agents if hasattr(a, 'sektor') and a.sektor == "Tarım" and a.durum == "Temiz"),
            "Toplam_Donusen": lambda m: sum(1 for a in m.agents if hasattr(a, 'durum') and a.durum == "Temiz")
        })

    def step(self):
        """Model adımı (bir yıl)."""
        self.dc.collect(self)
        self.tax += self.rate
        
        # Mesa 3.x: shuffle_do kullanımı
        self.agents.shuffle_do("step")


def simulasyonu_baslat():
    """Ana simülasyon fonksiyonu."""
    print("=" * 60)
    print("TR-ZERO: POLİTİKA ETKİ SİMÜLASYONU")
    print("SKDM & Tarım Teşviki Dahil")
    print("=" * 60)
    
    # Senaryo parametreleri
    print("\n📋 Senaryo Parametreleri:")
    print("   • Yıllık Vergi Artışı: 5 $/yıl")
    print("   • AB SKDM Fiyatı: 90 $/ton")
    print("   • Tarım Teşviki: 200 $")
    print("-" * 60)
    
    # Modeli çalıştır
    model = EkonomiModeli(rate=5, ab_tax=90, tesvik=200)
    
    for i in range(25):
        model.step()
    
    df = model.dc.get_model_vars_dataframe()
    
    print("\n✅ Simülasyon tamamlandı!")
    print(f"\n📊 Sonuçlar (25. Yıl):")
    print(f"   • Karbon Vergisi: {df['Vergi'].iloc[-1]:.0f} $/ton")
    print(f"   • Toplam Dönüşen Tesis: {df['Toplam_Donusen'].iloc[-1]:.0f}")
    print(f"   • Enerji Sektörü (Temiz): {df['Enerji_Temiz'].iloc[-1]:.0f}/40")
    print(f"   • Sanayi Sektörü (Temiz): {df['Sanayi_Temiz'].iloc[-1]:.0f}/30")
    print(f"   • Tarım Sektörü (Temiz): {df['Tarim_Temiz'].iloc[-1]:.0f}/30")
    
    # Grafik 1: Sektörel Dönüşüm
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1 = axes[0]
    ax1.plot(df.index, df["Enerji_Temiz"], label="Enerji (Temiz)", linewidth=2, color='#3b82f6')
    ax1.plot(df.index, df["Sanayi_Temiz"], label="Sanayi (Temiz)", linewidth=2, color='#22c55e')
    ax1.plot(df.index, df["Tarim_Temiz"], label="Tarım (Temiz)", linewidth=2, color='#f59e0b', linestyle='--')
    ax1.set_xlabel("Yıl")
    ax1.set_ylabel("Dönüşen Tesis Sayısı")
    ax1.set_title("Sektörel Yeşil Dönüşüm")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Grafik 2: Vergi ve Dönüşüm İlişkisi
    ax2 = axes[1]
    ax2_twin = ax2.twinx()
    
    ax2.plot(df.index, df["Vergi"], label="Karbon Vergisi", linewidth=2, color='#ef4444')
    ax2_twin.plot(df.index, df["Toplam_Donusen"], label="Toplam Dönüşen", linewidth=2, color='#22c55e', linestyle='--')
    
    ax2.set_xlabel("Yıl")
    ax2.set_ylabel("Karbon Vergisi ($/ton)", color='#ef4444')
    ax2_twin.set_ylabel("Dönüşen Tesis Sayısı", color='#22c55e')
    ax2.set_title("Vergi vs Dönüşüm İlişkisi")
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle("TR-ZERO: Politika Etki Analizi (Vergi vs. Teşvik)", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Kaydet
    output_path = os.path.join(OUTPUT_DIR, "politika_etki_analizi.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ Grafik kaydedildi: {output_path}")
    
    # CSV kaydet
    csv_path = os.path.join(OUTPUT_DIR, "politika_etki_sonuclari.csv")
    df.to_csv(csv_path, index=True)
    print(f"✅ CSV kaydedildi: {csv_path}")
    
    plt.show()
    
    return df


if __name__ == "__main__":
    df = simulasyonu_baslat()