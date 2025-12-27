"""
TR-ZERO: Ulusal İklim Karar Destek Sistemi Dashboard (v4.0 - Sunum Versiyonu)
==============================================================================

Premium, sunum odaklı, animasyonlu ve interaktif dashboard.

Yeni Özellikler:
----------------
- Animasyonlu KPI Kartları (Count-up efekti)
- Dark/Light Tema Toggle
- Sankey Emisyon Akış Diyagramı
- NDC Timeline Görselleştirmesi
- Gauge/Speedometer Charts
- PDF Rapor Export
- Dinamik Marquee Banner

Yazar: İbrahim Hakkı Keleş, Oğuz Gökdemir, Melis Mağden
Ders: Endüstri Mühendisliği Bitirme Tezi
Danışman: Deniz Efendioğlu
Tarih: Aralık 2025
Versiyon: 4.0 (Sunum Versiyonu)
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
from datetime import datetime

# =============================================================================
# PROJE AYARLARI
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

DB_PATH = os.path.join(PROJECT_ROOT, "iklim_veritabani.sqlite")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

# =============================================================================
# SAYFA YAPILANDIRMASI
# =============================================================================

st.set_page_config(
    page_title="TR-ZERO | Ulusal İklim Karar Destek Sistemi",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "TR-ZERO v4.0: Türkiye Sera Gazı Emisyon Analiz ve Projeksiyon Sistemi - Sunum Versiyonu"
    }
)

# =============================================================================
# TEMA YÖNETİMİ
# =============================================================================

if 'tema' not in st.session_state:
    st.session_state.tema = 'light'

# tema_degistir() fonksiyonu kaldırıldı - toggle widget zaten hallediyor

# Tema renkleri - Apple tarzı minimalist
TEMA_RENKLERI = {
    'light': {
        'bg_primary': '#ffffff',
        'bg_secondary': '#fbfbfd',
        'bg_tertiary': '#f5f5f7',
        'bg_gradient': 'linear-gradient(180deg, #ffffff 0%, #fbfbfd 100%)',
        'text_primary': '#1d1d1f',
        'text_secondary': '#86868b',
        'text_tertiary': '#6e6e73',
        'border': 'rgba(0, 0, 0, 0.08)',
        'card_shadow': '0 2px 12px rgba(0, 0, 0, 0.08)',
        'card_shadow_hover': '0 8px 30px rgba(0, 0, 0, 0.12)',
        'accent': '#0071e3',
        'accent_hover': '#0077ed',
        'success': '#34c759',
        'warning': '#ff9500',
        'danger': '#ff3b30',
    },
    'dark': {
        'bg_primary': '#000000',
        'bg_secondary': '#1d1d1f',
        'bg_tertiary': '#2d2d2d',
        'bg_gradient': 'linear-gradient(180deg, #000000 0%, #1d1d1f 100%)',
        'text_primary': '#f5f5f7',
        'text_secondary': '#a1a1a6',
        'text_tertiary': '#86868b',
        'border': 'rgba(255, 255, 255, 0.1)',
        'card_shadow': '0 2px 12px rgba(0, 0, 0, 0.4)',
        'card_shadow_hover': '0 8px 30px rgba(0, 0, 0, 0.6)',
        'accent': '#2997ff',
        'accent_hover': '#0077ed',
        'success': '#30d158',
        'warning': '#ff9f0a',
        'danger': '#ff453a',
    }
}

tema = TEMA_RENKLERI[st.session_state.tema]

# =============================================================================
# APPLE TARZI MİNİMALİST CSS TASARIMI
# =============================================================================

st.markdown(f"""
<style>
    /* ===== FONT İMPORTLARI ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
    
    /* ===== GENEL RESET VE TEMA ===== */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    
    .stApp {{
        background: {tema['bg_primary']};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* ===== ANİMASYONLAR - APPLE TARZI YUMUŞAK ===== */
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes scaleIn {{
        from {{
            opacity: 0;
            transform: scale(0.95);
        }}
        to {{
            opacity: 1;
            transform: scale(1);
        }}
    }}
    
    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}
    
    /* ===== HERO HEADER - APPLE TARZI ===== */
    .hero-header {{
        background: {tema['bg_secondary']};
        padding: 80px 40px;
        border-radius: 24px;
        margin-bottom: 40px;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: fadeIn 1s ease-out;
        border: 1px solid {tema['border']};
    }}
    
    .hero-header h1 {{
        color: {tema['text_primary']};
        font-size: 56px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .hero-header .subtitle {{
        color: {tema['text_secondary']};
        font-size: 21px;
        margin-top: 12px;
        font-weight: 400;
        letter-spacing: -0.01em;
    }}
    
    .hero-header .version-badge {{
        display: inline-block;
        background: {tema['bg_tertiary']};
        padding: 8px 16px;
        border-radius: 980px;
        font-size: 14px;
        font-weight: 500;
        color: {tema['text_secondary']};
        margin-top: 20px;
        border: 1px solid {tema['border']};
    }}
    
    /* ===== MARQUEE BANNER - MİNİMALİST ===== */
    .marquee-container {{
        background: {tema['bg_tertiary']};
        padding: 14px 0;
        border-radius: 12px;
        margin-bottom: 32px;
        overflow: hidden;
        border: 1px solid {tema['border']};
    }}
    
    .marquee-content {{
        display: flex;
        animation: marquee 40s linear infinite;
        white-space: nowrap;
    }}
    
    @keyframes marquee {{
        0% {{ transform: translateX(0%); }}
        100% {{ transform: translateX(-50%); }}
    }}
    
    .marquee-item {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: {tema['text_secondary']};
        font-weight: 500;
        padding: 0 32px;
        font-size: 14px;
    }}
    
    .marquee-item .value {{
        font-weight: 600;
        color: {tema['text_primary']};
    }}
    
    /* ===== METRİK KARTLARI - APPLE TARZI ===== */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-bottom: 40px;
    }}
    
    .animated-metric {{
        background: {tema['bg_secondary']};
        border-radius: 20px;
        padding: 28px;
        box-shadow: {tema['card_shadow']};
        border: 1px solid {tema['border']};
        transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
        animation: fadeInUp 0.6s ease-out backwards;
        position: relative;
        overflow: hidden;
    }}
    
    .animated-metric:nth-child(1) {{ animation-delay: 0.05s; }}
    .animated-metric:nth-child(2) {{ animation-delay: 0.1s; }}
    .animated-metric:nth-child(3) {{ animation-delay: 0.15s; }}
    .animated-metric:nth-child(4) {{ animation-delay: 0.2s; }}
    
    .animated-metric:hover {{
        transform: scale(1.02);
        box-shadow: {tema['card_shadow_hover']};
    }}
    
    .animated-metric::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 20px 20px 0 0;
    }}
    
    .animated-metric.teal::before {{ background: {tema['accent']}; }}
    .animated-metric.blue::before {{ background: #5856d6; }}
    .animated-metric.amber::before {{ background: {tema['warning']}; }}
    .animated-metric.emerald::before {{ background: {tema['success']}; }}
    
    .metric-icon-wrapper {{
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
        background: {tema['bg_tertiary']};
    }}
    
    .metric-value {{
        font-size: 36px;
        font-weight: 700;
        color: {tema['text_primary']};
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    
    .metric-label {{
        font-size: 14px;
        color: {tema['text_secondary']};
        font-weight: 500;
        margin-top: 8px;
    }}
    
    .metric-delta {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        padding: 6px 12px;
        border-radius: 980px;
        margin-top: 12px;
        font-weight: 600;
    }}
    
    .metric-delta.positive {{
        background: rgba(52, 199, 89, 0.12);
        color: {tema['success']};
    }}
    
    .metric-delta.negative {{
        background: rgba(255, 59, 48, 0.12);
        color: {tema['danger']};
    }}
    
    /* ===== SECTION HEADERS - APPLE TARZI ===== */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 48px 0 24px 0;
        animation: fadeIn 0.5s ease-out;
    }}
    
    .section-header .icon-box {{
        width: 44px;
        height: 44px;
        background: {tema['accent']};
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }}
    
    .section-header h2 {{
        color: {tema['text_primary']};
        font-size: 28px;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.02em;
    }}
    
    /* ===== CHART KARTLARI - APPLE TARZI ===== */
    .chart-card {{
        background: {tema['bg_secondary']};
        border-radius: 20px;
        padding: 28px;
        box-shadow: {tema['card_shadow']};
        border: 1px solid {tema['border']};
        margin-bottom: 24px;
        transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
    }}
    
    .chart-card:hover {{
        box-shadow: {tema['card_shadow_hover']};
    }}
    
    .chart-card h3 {{
        color: {tema['text_primary']};
        font-size: 19px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        letter-spacing: -0.01em;
    }}
    
    /* ===== TIMELINE - APPLE TARZI ===== */
    .timeline-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 40px;
        background: {tema['bg_secondary']};
        border-radius: 20px;
        margin: 24px 0;
        position: relative;
        box-shadow: {tema['card_shadow']};
        border: 1px solid {tema['border']};
    }}
    
    .timeline-line {{
        position: absolute;
        top: 50%;
        left: 12%;
        right: 12%;
        height: 2px;
        background: linear-gradient(90deg, {tema['accent']} 0%, {tema['success']} 100%);
        border-radius: 1px;
        z-index: 1;
    }}
    
    .timeline-point {{
        position: relative;
        z-index: 2;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
    }}
    
    .timeline-dot {{
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: {tema['accent']};
        box-shadow: 0 0 0 4px {tema['bg_secondary']};
    }}
    
    .timeline-dot.active {{
        width: 20px;
        height: 20px;
        background: {tema['success']};
        box-shadow: 0 0 0 4px {tema['bg_secondary']}, 0 0 0 8px rgba(52, 199, 89, 0.2);
    }}
    
    .timeline-year {{
        font-size: 17px;
        font-weight: 600;
        color: {tema['text_primary']};
    }}
    
    .timeline-label {{
        font-size: 13px;
        color: {tema['text_secondary']};
        text-align: center;
        max-width: 100px;
    }}
    
    .timeline-value {{
        font-size: 15px;
        font-weight: 600;
        color: {tema['accent']};
    }}
    
    /* ===== SIDEBAR - APPLE TARZI ===== */
    [data-testid="stSidebar"] {{
        background: {tema['bg_secondary']};
        border-right: 1px solid {tema['border']};
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 24px;
    }}
    
    .sidebar-header {{
        text-align: center;
        padding: 24px 16px;
        margin: 8px;
        background: {tema['bg_tertiary']};
        border-radius: 16px;
        border: 1px solid {tema['border']};
    }}
    
    .sidebar-header .logo {{
        font-size: 48px;
    }}
    
    .sidebar-header h2 {{
        color: {tema['text_primary']};
        font-size: 22px;
        font-weight: 600;
        margin: 12px 0 0 0;
        letter-spacing: -0.02em;
    }}
    
    .sidebar-section {{
        background: {tema['bg_tertiary']};
        border-radius: 12px;
        padding: 16px;
        margin: 8px;
        margin-bottom: 16px;
        border: 1px solid {tema['border']};
    }}
    
    .sidebar-section h4 {{
        color: {tema['text_secondary']};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }}
    
    /* ===== TABS - APPLE TARZI ===== */
    .stTabs [data-baseweb="tab-list"] {{
        background: {tema['bg_tertiary']};
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid {tema['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 14px;
        color: {tema['text_secondary']};
        border: none;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {tema['bg_secondary']};
        color: {tema['text_primary']} !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: {tema['text_primary']};
    }}
    
    /* ===== BUTONLAR - APPLE TARZI ===== */
    .stButton > button {{
        background: {tema['accent']};
        color: #ffffff;
        border: none;
        border-radius: 980px;
        padding: 12px 24px;
        font-weight: 500;
        font-size: 15px;
        transition: all 0.2s ease;
        box-shadow: none;
    }}
    
    .stButton > button:hover {{
        background: {tema['accent_hover']};
        transform: scale(1.02);
    }}
    
    .stButton > button:active {{
        transform: scale(0.98);
    }}
    
    /* ===== INPUT ALANLARI ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {{
        background: {tema['bg_tertiary']};
        border: 1px solid {tema['border']};
        border-radius: 10px;
        color: {tema['text_primary']};
    }}
    
    .stSlider > div > div > div {{
        background: {tema['accent']};
    }}
    
    /* ===== INFO BOXES - APPLE TARZI ===== */
    .info-box {{
        background: {tema['bg_tertiary']};
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid {tema['accent']};
        margin: 16px 0;
    }}
    
    .info-box p {{
        color: {tema['text_primary']};
        margin: 0;
        font-size: 15px;
        line-height: 1.6;
    }}
    
    .warning-box {{
        background: rgba(255, 149, 0, 0.1);
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid {tema['warning']};
        margin: 16px 0;
    }}
    
    .warning-box p {{
        color: {tema['text_primary']};
        margin: 0;
        font-size: 15px;
    }}
    
    /* ===== FOOTER - APPLE TARZI ===== */
    .footer {{
        background: {tema['bg_secondary']};
        border-radius: 20px;
        padding: 40px;
        margin-top: 60px;
        text-align: center;
        border: 1px solid {tema['border']};
    }}
    
    .footer-logo {{
        font-size: 40px;
        margin-bottom: 16px;
    }}
    
    .footer p {{
        color: {tema['text_secondary']};
        font-size: 14px;
        margin: 6px 0;
    }}
    
    .footer a {{
        color: {tema['accent']};
        text-decoration: none;
        font-weight: 500;
    }}
    
    .footer a:hover {{
        text-decoration: underline;
    }}
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 1200px) {{
        .metric-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .hero-header h1 {{
            font-size: 42px;
        }}
    }}
    
    @media (max-width: 768px) {{
        .hero-header {{
            padding: 48px 24px;
        }}
        .hero-header h1 {{
            font-size: 32px;
        }}
        .metric-grid {{
            grid-template-columns: 1fr;
        }}
        .metric-value {{
            font-size: 28px;
        }}
    }}
    
    /* ===== SCROLLBAR - APPLE TARZI ===== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {tema['text_secondary']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {tema['text_tertiary']};
    }}
    
    /* ===== DATA TABLES ===== */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {tema['border']};
    }}
    
    /* ===== METRICS ===== */
    [data-testid="stMetricValue"] {{
        color: {tema['text_primary']};
        font-weight: 600;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {tema['text_secondary']};
    }}
    
    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {{
        background: {tema['bg_tertiary']};
        border-radius: 12px;
        border: 1px solid {tema['border']};
    }}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# RENK PALETİ - APPLE TARZI
# =============================================================================

RENKLER = {
    'birincil': tema['accent'],
    'ikincil': tema.get('accent_hover', '#0077ed'),
    'vurgu': tema['success'],
    'uyari': tema['warning'],
    'tehlike': tema['danger'],
    'basari': tema['success'],
    'bilgi': tema['accent'],
    'mor': '#5856d6',
    'pembe': '#ff2d55',
    'metin': tema['text_primary'],
    'acik_metin': tema['text_secondary'],
    'arka_plan': tema['bg_primary'],
    'kart': tema['bg_secondary'],
    'grafik': [tema['accent'], '#5856d6', tema['warning'], tema['danger'], tema['success'], '#ff2d55', '#af52de']
}

SEKTOR_RENKLERI = {
    'Enerji': tema['accent'],
    'Endüstri': '#5856d6',
    'Tarım': tema['warning'],
    'Atık': tema['danger'],
    'LULUCF': tema['success']
}

# =============================================================================
# VERİ FONKSİYONLARI
# =============================================================================

@st.cache_data(ttl=3600)
def veri_yukle():
    """Veritabanından verileri yükler."""
    if not os.path.exists(DB_PATH):
        return None, None
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df_envanter = pd.read_sql("SELECT * FROM ulusal_envanter", conn)
        df_il = pd.read_sql("SELECT * FROM il_katsayilari", conn)
        return df_envanter, df_il
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return None, None
    finally:
        conn.close()

@st.cache_data(ttl=3600)
def senaryo_sonuclari_yukle():
    """Senaryo sonuçlarını yükler."""
    sonuclar = {}
    senaryo_isimleri = {
        "bau": "Referans Senaryo (BAU)",
        "yumusak_ets": "Yumuşak ETS",
        "siki_ets": "Sıkı ETS",
        "ets_tesvik": "ETS + Teşvik"
    }
    
    for dosya_adi, gorunen_isim in senaryo_isimleri.items():
        dosya_yolu = os.path.join(OUTPUT_DIR, f"senaryo_{dosya_adi}.csv")
        if os.path.exists(dosya_yolu):
            sonuclar[gorunen_isim] = pd.read_csv(dosya_yolu)
    
    return sonuclar if sonuclar else None

def sutun_adini_bul(df, adaylar):
    """DataFrame'de mevcut olan sütun adını bulur."""
    for aday in adaylar:
        if aday in df.columns:
            return aday
    return None

# =============================================================================
# GAUGE CHART FONKSİYONU - APPLE TARZI
# =============================================================================

def gauge_chart_olustur(deger, maksimum, baslik, birim="Mt", renk_skalasi=None):
    """
    Apple tarzı minimal gauge chart oluşturur.
    
    NOT: Varsayılan maksimum değer (800 Mt) Türkiye'nin 2030 BAU senaryosu 
    projeksiyonudur [Kaynak: Climate Action Tracker 2024].
    """
    if renk_skalasi is None:
        renk_skalasi = [[0, tema['success']], [0.5, tema['warning']], [1, tema['danger']]]
    
    oran = min(deger / maksimum, 1)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=deger,
        number={'suffix': f' {birim}', 'font': {'size': 32, 'family': 'Inter', 'color': tema['text_primary'], 'weight': 600}},
        title={'text': baslik, 'font': {'size': 14, 'color': tema['text_secondary'], 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, maksimum], 'tickwidth': 1, 'tickcolor': tema['border'], 'tickfont': {'color': tema['text_tertiary'], 'size': 10}},
            'bar': {'color': tema['accent'], 'thickness': 0.8},
            'bgcolor': tema['bg_tertiary'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, maksimum * 0.33], 'color': 'rgba(52, 199, 89, 0.1)'},
                {'range': [maksimum * 0.33, maksimum * 0.66], 'color': 'rgba(255, 149, 0, 0.1)'},
                {'range': [maksimum * 0.66, maksimum], 'color': 'rgba(255, 59, 48, 0.1)'}
            ],
            'threshold': {
                'line': {'color': tema['danger'], 'width': 3},
                'thickness': 0.8,
                'value': maksimum * 0.85
            }
        }
    ))
    
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': tema['text_primary'], 'family': 'Inter'}
    )
    
    return fig

# =============================================================================
# SANKEY DİYAGRAMI FONKSİYONU - APPLE TARZI
# =============================================================================

def sankey_diagram_olustur(df_envanter, son_yil):
    """
    Apple tarzı minimal Sankey diyagramı oluşturur.
    
    NOT: Kaynak payları IEA Türkiye Enerji İstatistikleri 2023'ten uyarlanmıştır.
    - Fosil yakıt payı: ~%85
    - Yenilenebilir enerji: ~%5  
    - Endüstriyel kullanım: ~%10
    
    Referanslar:
    - [IEA 2023] Turkey Energy Statistics
    - [NIR 2024] Turkish Greenhouse Gas Inventory
    """
    son_veri = df_envanter[df_envanter['Year'] == son_yil].iloc[0]
    
    # Sütun adlarını bul
    enerji = sutun_adini_bul(df_envanter, ['Enerji_Toplam', 'Enerji'])
    ippu = sutun_adini_bul(df_envanter, ['IPPU_Toplam', 'Endustriyel_Islemler'])
    tarim = sutun_adini_bul(df_envanter, ['Tarim_Toplam', 'Tarim'])
    atik = sutun_adini_bul(df_envanter, ['Atik_Toplam', 'Atik'])
    
    # Düğümler
    labels = [
        "Fosil Yakıtlar", "Yenilenebilir", "Sanayi Prosesleri", "Hayvancılık", "Katı Atık",
        "Enerji Sektörü", "Endüstri Sektörü", "Tarım Sektörü", "Atık Sektörü",
        "Toplam Emisyon", "Atmosfer"
    ]
    
    # Değerler
    enerji_deger = son_veri[enerji] if enerji else 0
    ippu_deger = son_veri[ippu] if ippu else 0
    tarim_deger = son_veri[tarim] if tarim else 0
    atik_deger = son_veri[atik] if atik else 0
    
    # Kaynak payları [IEA Türkiye Enerji İstatistikleri 2023]
    FOSIL_PAYI = 0.85       # Enerji sektöründe fosil yakıt payı (~%85)
    ENDUSTRI_PAYI = 0.10    # Endüstriyel kullanım (~%10)
    YENILENEBILIR_PAYI = 0.05  # Yenilenebilir enerji (~%5)
    
    # Bağlantılar
    source = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    target = [5, 6, 5, 6, 7, 8, 9, 9, 9, 9, 10]
    value = [
        enerji_deger * FOSIL_PAYI,          # Fosil -> Enerji
        enerji_deger * ENDUSTRI_PAYI,       # Fosil -> Endüstri
        enerji_deger * YENILENEBILIR_PAYI,  # Yenilenebilir -> Enerji
        ippu_deger,                         # Sanayi Prosesleri -> Endüstri
        tarim_deger,                        # Hayvancılık -> Tarım
        atik_deger,                         # Katı Atık -> Atık
        enerji_deger,                       # Enerji -> Toplam
        ippu_deger,                         # Endüstri -> Toplam
        tarim_deger,                        # Tarım -> Toplam
        atik_deger,                         # Atık -> Toplam
        enerji_deger + ippu_deger + tarim_deger + atik_deger  # Toplam -> Atmosfer
    ]
    
    # Apple tarzı renkler
    node_colors = [
        tema['text_tertiary'], tema['success'], '#5856d6', tema['warning'], tema['danger'],
        tema['accent'], '#5856d6', tema['warning'], tema['danger'],
        tema['text_primary'], tema['text_secondary']
    ]
    
    link_colors = [
        f"rgba(134, 134, 139, 0.3)", f"rgba(134, 134, 139, 0.3)",
        f"rgba(52, 199, 89, 0.3)",
        f"rgba(88, 86, 214, 0.3)",
        f"rgba(255, 149, 0, 0.3)",
        f"rgba(255, 59, 48, 0.3)",
        f"rgba(0, 113, 227, 0.4)", f"rgba(88, 86, 214, 0.4)",
        f"rgba(255, 149, 0, 0.4)", f"rgba(255, 59, 48, 0.4)",
        f"rgba(134, 134, 139, 0.4)"
    ]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=25,
            thickness=20,
            line=dict(color=tema['border'], width=0.5),
            label=labels,
            color=node_colors,
            hovertemplate='%{label}<br>%{value:.1f} Mt CO₂eq<extra></extra>'
        ),
        textfont=dict(color=tema['text_primary'], size=13, family='Inter'),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value:.1f} Mt CO₂eq<extra></extra>'
        )
    )])
    
    fig.update_layout(
        title=dict(
            text="Emisyon Akış Diyagramı",
            font=dict(size=17, color=tema['text_primary'], family='Inter', weight=600),
            x=0.5,
            xanchor='center'
        ),
        font=dict(size=12, color=tema['text_primary'], family='Inter'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=420,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

# =============================================================================
# VERİ YÜKLEME
# =============================================================================

df_envanter, df_il = veri_yukle()

if df_envanter is None:
    st.markdown("""
    <div class="hero-header">
        <h1>🌱 TR-ZERO</h1>
        <p class="subtitle">Türkiye Ulusal İklim Karar Destek Sistemi</p>
        <span class="version-badge">v4.0 Sunum Versiyonu</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.error("⚠️ Veritabanı bulunamadı. Lütfen önce kurulum dosyasını çalıştırın.")
    st.code("python src/database_setup_v2.py", language="bash")
    st.stop()

# Sütun adlarını belirle
toplam_sutun = sutun_adini_bul(df_envanter, ['Toplam_LULUCF_Haric', 'Toplam'])
enerji_sutun = sutun_adini_bul(df_envanter, ['Enerji_Toplam', 'Enerji'])
ippu_sutun = sutun_adini_bul(df_envanter, ['IPPU_Toplam', 'Endustriyel_Islemler'])
tarim_sutun = sutun_adini_bul(df_envanter, ['Tarim_Toplam', 'Tarim'])
atik_sutun = sutun_adini_bul(df_envanter, ['Atik_Toplam', 'Atik'])

# Son yıl verileri
son_yil = int(df_envanter['Year'].max())
son_veri = df_envanter[df_envanter['Year'] == son_yil].iloc[0]
ilk_veri = df_envanter[df_envanter['Year'] == df_envanter['Year'].min()].iloc[0]

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="logo">🌱</div>
        <h2>TR-ZERO</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Tema Toggle
    st.markdown("#### 🎨 Tema")
    tema_secim = st.toggle("Karanlık Tema", value=(st.session_state.tema == 'dark'), key="tema_toggle")
    if tema_secim != (st.session_state.tema == 'dark'):
        st.session_state.tema = 'dark' if tema_secim else 'light'
        st.rerun()
    
    st.markdown("---")
    
    # Analiz Dönemi
    st.markdown("#### 📅 Analiz Dönemi")
    yil_baslangic, yil_bitis = st.slider(
        "Yıl Aralığı",
        min_value=int(df_envanter['Year'].min()),
        max_value=2050,
        value=(2015, 2035),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Senaryo Seçimi
    st.markdown("#### 📊 Senaryo Seçimi")
    senaryo_secenekleri = ["Referans Senaryo (BAU)", "Yumuşak ETS", "Sıkı ETS", "ETS + Teşvik"]
    secili_senaryolar = st.multiselect(
        "Karşılaştırılacak Senaryolar",
        senaryo_secenekleri,
        default=["Referans Senaryo (BAU)", "Sıkı ETS"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # ETS Parametreleri
    st.markdown("#### ⚙️ ETS Parametreleri")
    
    karbon_fiyati = st.number_input(
        "Başlangıç Karbon Fiyatı ($/ton)",
        min_value=10,
        max_value=200,
        value=25,
        step=5
    )
    
    cap_azalma = st.slider(
        "Yıllık Tavan Azalma Oranı (%)",
        min_value=1.0,
        max_value=5.0,
        value=2.1,
        step=0.1
    )
    
    tesvik_miktari = st.number_input(
        "Yenilenebilir Teşviği ($/MW)",
        min_value=0,
        max_value=200000,
        value=50000,
        step=10000
    )
    
    st.markdown("---")
    
    # Çalıştır Butonu
    simule_et = st.button("🚀 Simülasyonu Çalıştır", use_container_width=True)
    
    st.markdown("---")
    
    # Proje Bilgisi
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; font-size: 0.8rem; color: {tema['text_secondary']};">
        <strong>Bitirme Tezi</strong><br>
        Endüstri Mühendisliği<br>
        Aralık 2025
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# HERO HEADER - APPLE TARZI
# =============================================================================

st.markdown(f"""
<div class="hero-header">
    <h1>🌱 TR-ZERO</h1>
    <p class="subtitle">Türkiye Ulusal İklim Karar Destek Sistemi</p>
    <span class="version-badge">v4.0 Sunum Versiyonu</span>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# MARQUEE BANNER - CANLI İSTATİSTİKLER
# =============================================================================

toplam_emisyon = son_veri[toplam_sutun]
enerji_payi = (son_veri[enerji_sutun] / toplam_emisyon) * 100
yillik_degisim = toplam_emisyon - df_envanter[df_envanter['Year'] == son_yil - 1][toplam_sutun].values[0]

st.markdown(f"""
<div class="marquee-container">
    <div class="marquee-content">
        <span class="marquee-item">📊 Toplam Emisyon: <span class="value">{toplam_emisyon:.1f} Mt CO₂eq</span></span>
        <span class="marquee-item">⚡ Enerji Sektörü Payı: <span class="value">%{enerji_payi:.1f}</span></span>
        <span class="marquee-item">📈 Yıllık Değişim: <span class="value">{yillik_degisim:+.1f} Mt</span></span>
        <span class="marquee-item">🎯 NDC 2030 Hedefi: <span class="value">695 Mt</span></span>
        <span class="marquee-item">🌍 Net Sıfır Hedefi: <span class="value">2053</span></span>
        <span class="marquee-item">🏭 ETS Başlangıcı: <span class="value">2026</span></span>
        <span class="marquee-item">📊 Toplam Emisyon: <span class="value">{toplam_emisyon:.1f} Mt CO₂eq</span></span>
        <span class="marquee-item">⚡ Enerji Sektörü Payı: <span class="value">%{enerji_payi:.1f}</span></span>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# NDC TIMELINE - STREAMLIT NATIVE
# =============================================================================

st.subheader("🎯 Türkiye İklim Hedefleri Yol Haritası")

# Timeline için Streamlit columns kullan
col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)

with col_t1:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="width: 20px; height: 20px; background: {tema['accent']}; border-radius: 50%; margin: 0 auto 12px auto;"></div>
        <div style="font-size: 18px; font-weight: 600; color: {tema['text_primary']};">1990</div>
        <div style="font-size: 13px; color: {tema['text_secondary']}; margin-top: 4px;">Baz Yıl</div>
        <div style="font-size: 15px; font-weight: 600; color: {tema['accent']}; margin-top: 8px;">{ilk_veri[toplam_sutun]:.0f} Mt</div>
    </div>
    """, unsafe_allow_html=True)

with col_t2:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="width: 24px; height: 24px; background: {tema['success']}; border-radius: 50%; margin: 0 auto 12px auto; box-shadow: 0 0 0 6px rgba(52, 199, 89, 0.2);"></div>
        <div style="font-size: 18px; font-weight: 600; color: {tema['text_primary']};">{son_yil}</div>
        <div style="font-size: 13px; color: {tema['text_secondary']}; margin-top: 4px;">Güncel</div>
        <div style="font-size: 15px; font-weight: 600; color: {tema['success']}; margin-top: 8px;">{toplam_emisyon:.0f} Mt</div>
    </div>
    """, unsafe_allow_html=True)

with col_t3:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="width: 20px; height: 20px; background: {tema['accent']}; border-radius: 50%; margin: 0 auto 12px auto;"></div>
        <div style="font-size: 18px; font-weight: 600; color: {tema['text_primary']};">2026</div>
        <div style="font-size: 13px; color: {tema['text_secondary']}; margin-top: 4px;">ETS Başlangıcı</div>
        <div style="font-size: 15px; font-weight: 600; color: {tema['accent']}; margin-top: 8px;">Piyasa Açılışı</div>
    </div>
    """, unsafe_allow_html=True)

with col_t4:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="width: 20px; height: 20px; background: {tema['accent']}; border-radius: 50%; margin: 0 auto 12px auto;"></div>
        <div style="font-size: 18px; font-weight: 600; color: {tema['text_primary']};">2030</div>
        <div style="font-size: 13px; color: {tema['text_secondary']}; margin-top: 4px;">NDC Hedefi</div>
        <div style="font-size: 15px; font-weight: 600; color: {tema['accent']}; margin-top: 8px;">695 Mt</div>
    </div>
    """, unsafe_allow_html=True)

with col_t5:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="width: 20px; height: 20px; background: {tema['accent']}; border-radius: 50%; margin: 0 auto 12px auto;"></div>
        <div style="font-size: 18px; font-weight: 600; color: {tema['text_primary']};">2053</div>
        <div style="font-size: 13px; color: {tema['text_secondary']}; margin-top: 4px;">Net Sıfır</div>
        <div style="font-size: 15px; font-weight: 600; color: {tema['success']}; margin-top: 8px;">0 Mt</div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# ANİMASYONLU KPI KARTLARI - STREAMLIT NATIVE
# =============================================================================

st.subheader("📊 Temel Performans Göstergeleri")

onceki_emisyon = df_envanter[df_envanter['Year'] == son_yil - 1][toplam_sutun].values[0]
degisim = toplam_emisyon - onceki_emisyon
artis_orani = ((toplam_emisyon - ilk_veri[toplam_sutun]) / ilk_veri[toplam_sutun]) * 100
ndc_hedef = 695
kalan = ndc_hedef - toplam_emisyon

# KPI Kartları için Streamlit columns
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric(
        label=f"Toplam Emisyon ({son_yil})",
        value=f"{toplam_emisyon:.1f} Mt",
        delta=f"{degisim:+.1f} Mt yıllık",
        delta_color="inverse"
    )

with col_kpi2:
    st.metric(
        label="Enerji Sektörü Payı",
        value=f"%{enerji_payi:.1f}",
        delta=f"{son_veri[enerji_sutun]:.1f} Mt",
        delta_color="off"
    )

with col_kpi3:
    st.metric(
        label="1990'dan Bu Yana",
        value=f"+%{artis_orani:.0f}",
        delta=f"+{toplam_emisyon - ilk_veri[toplam_sutun]:.0f} Mt",
        delta_color="inverse"
    )

with col_kpi4:
    st.metric(
        label="NDC 2030 Hedefi",
        value=f"{ndc_hedef} Mt",
        delta=f"{kalan:.0f} Mt boşluk" if kalan > 0 else f"{abs(kalan):.0f} Mt aşım",
        delta_color="normal" if kalan > 0 else "inverse"
    )

# =============================================================================
# GAUGE CHARTS - HEDEF TAKİP (APPLE TARZI)
# =============================================================================

st.subheader("🎯 Hedef Takip Göstergeleri")

col_gauge1, col_gauge2, col_gauge3 = st.columns(3)

with col_gauge1:
    fig_gauge1 = gauge_chart_olustur(
        deger=toplam_emisyon,
        maksimum=800,
        baslik="Mevcut vs Kapasite",
        birim="Mt"
    )
    st.plotly_chart(fig_gauge1, use_container_width=True)

with col_gauge2:
    ndc_ilerleme = ((toplam_emisyon - ilk_veri[toplam_sutun]) / (ndc_hedef - ilk_veri[toplam_sutun])) * 100
    fig_gauge2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(100, 100 - (toplam_emisyon - ndc_hedef) / ndc_hedef * 100),
        number={'suffix': '%', 'font': {'size': 32, 'family': 'Inter', 'color': tema['text_primary'], 'weight': 600}},
        title={'text': "NDC Hedefe Yakınlık", 'font': {'size': 14, 'color': tema['text_secondary'], 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'color': tema['text_tertiary'], 'size': 10}},
            'bar': {'color': tema['success'], 'thickness': 0.8},
            'bgcolor': tema['bg_tertiary'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, 33], 'color': 'rgba(255, 59, 48, 0.1)'},
                {'range': [33, 66], 'color': 'rgba(255, 149, 0, 0.1)'},
                {'range': [66, 100], 'color': 'rgba(52, 199, 89, 0.1)'}
            ]
        }
    ))
    fig_gauge2.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'})
    st.plotly_chart(fig_gauge2, use_container_width=True)

with col_gauge3:
    fig_gauge3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=enerji_payi,
        number={'suffix': '%', 'font': {'size': 32, 'family': 'Inter', 'color': tema['text_primary'], 'weight': 600}},
        title={'text': "Enerji Sektörü Baskınlığı", 'font': {'size': 14, 'color': tema['text_secondary'], 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'color': tema['text_tertiary'], 'size': 10}},
            'bar': {'color': tema['warning'], 'thickness': 0.8},
            'bgcolor': tema['bg_tertiary'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, 50], 'color': 'rgba(52, 199, 89, 0.1)'},
                {'range': [50, 75], 'color': 'rgba(255, 149, 0, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(255, 59, 48, 0.1)'}
            ]
        }
    ))
    fig_gauge3.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'family': 'Inter'})
    st.plotly_chart(fig_gauge3, use_container_width=True)

# =============================================================================
# TABLAR
# =============================================================================

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Mevcut Durum",
    "🔄 Emisyon Akışı",
    "🤖 AI Projeksiyonu",
    "🏭 Piyasa Simülasyonu",
    "🗺️ Bölgesel Analiz",
    "📋 Rapor"
])

# =============================================================================
# TAB 1: MEVCUT DURUM
# =============================================================================

with tab1:
    st.subheader("📈 Sektörel Emisyon Analizi")
    
    col_grafik1, col_grafik2 = st.columns([3, 2])
    
    with col_grafik1:
        st.caption("📊 Sektörel Emisyon Trendi (1990-Günümüz)")
        
        # Çizgi grafiği - Apple tarzı
        fig_trend = go.Figure()
        
        sektor_verileri = [
            (enerji_sutun, 'Enerji', RENKLER['grafik'][0]),
            (ippu_sutun, 'Endüstri', RENKLER['grafik'][1]),
            (tarim_sutun, 'Tarım', RENKLER['grafik'][2]),
            (atik_sutun, 'Atık', RENKLER['grafik'][3])
        ]
        
        for sutun, isim, renk in sektor_verileri:
            if sutun and sutun in df_envanter.columns:
                fig_trend.add_trace(go.Scatter(
                    x=df_envanter['Year'],
                    y=df_envanter[sutun],
                    mode='lines',
                    name=isim,
                    line=dict(color=renk, width=2.5, shape='spline'),
                    hovertemplate=f'<b>{isim}</b><br>Yıl: %{{x}}<br>Emisyon: %{{y:.1f}} Mt<extra></extra>'
                ))
        
        fig_trend.update_layout(
            xaxis_title="Yıl",
            yaxis_title="Emisyon (Mt CO₂ eşdeğeri)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12, family='Inter', color=tema['text_primary'])
            ),
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=420,
            margin=dict(l=60, r=30, t=30, b=60),
            xaxis=dict(gridcolor=tema['border'], zerolinecolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
            yaxis=dict(gridcolor=tema['border'], zerolinecolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
            font=dict(color=tema['text_primary'], family='Inter')
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_grafik2:
        st.caption(f"🥧 Sektörel Dağılım ({son_yil})")
        
        # Pasta grafiği verileri
        sektor_degerleri = []
        sektor_isimleri = []
        sektor_renkleri = []
        
        for sutun, isim, renk in sektor_verileri:
            if sutun and sutun in df_envanter.columns:
                deger = son_veri[sutun]
                sektor_degerleri.append(deger)
                sektor_isimleri.append(isim)
                sektor_renkleri.append(renk)
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=sektor_isimleri,
            values=sektor_degerleri,
            hole=0.6,
            marker=dict(colors=sektor_renkleri, line=dict(color=tema['bg_secondary'], width=2)),
            textinfo='percent',
            textfont=dict(size=13, color=tema['text_primary'], family='Inter'),
            hovertemplate='<b>%{label}</b><br>Emisyon: %{value:.1f} Mt<br>Oran: %{percent}<extra></extra>',
            pull=[0.02, 0.02, 0.02, 0.02]
        )])
        
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=11, family='Inter', color=tema['text_primary'])),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=420,
            margin=dict(l=20, r=20, t=20, b=60),
            annotations=[dict(
                text=f'<b>{toplam_emisyon:.0f}</b><br><span style="font-size:12px">Mt CO₂eq</span>',
                x=0.5, y=0.5,
                font=dict(size=24, color=tema['text_primary'], family='Inter'),
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Stacked Area Chart
    st.caption("📊 Yığılmış Alan Grafiği - Toplam Emisyon Dağılımı")
    
    fig_area = go.Figure()
    
    for sutun, isim, renk in reversed(sektor_verileri):
        if sutun and sutun in df_envanter.columns:
            fig_area.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=df_envanter[sutun],
                name=isim,
                mode='lines',
                stackgroup='one',
                line=dict(width=0, color=renk, shape='spline'),
                fillcolor=renk,
                hovertemplate=f'{isim}: %{{y:.1f}} Mt<extra></extra>'
            ))
    
    fig_area.update_layout(
        xaxis_title="Yıl",
        yaxis_title="Emisyon (Mt CO₂ eşdeğeri)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(family='Inter', color=tema['text_primary'])),
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=380,
        xaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
        yaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
        font=dict(color=tema['text_primary'], family='Inter')
    )
    
    st.plotly_chart(fig_area, use_container_width=True)
    
    st.info("📌 **Not:** Veriler, Türkiye Ulusal Envanter Raporu (NIR 2024) ve TÜİK resmi istatistiklerinden derlenmiştir. Emisyon değerleri LULUCF sektörü hariç tutularak hesaplanmıştır.")

# =============================================================================
# TAB 2: EMİSYON AKIŞI (SANKEY)
# =============================================================================

with tab2:
    st.subheader("🔄 Emisyon Akış Diyagramı (Sankey)")
    
    st.info("🔄 **Sankey Diyagramı:** Bu görselleştirme, sera gazı emisyonlarının kaynaklardan sektörlere ve oradan atmosfere akışını göstermektedir. Bağlantıların kalınlığı emisyon miktarıyla orantılıdır.")
    
    fig_sankey = sankey_diagram_olustur(df_envanter, son_yil)
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    # Sektör detayları - Streamlit metrics
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    with col_s1:
        st.metric(
            label="⚡ Enerji",
            value=f"{son_veri[enerji_sutun]:.1f} Mt",
            delta=f"%{(son_veri[enerji_sutun]/toplam_emisyon*100):.1f} pay"
        )
    
    with col_s2:
        st.metric(
            label="🏭 Endüstri",
            value=f"{son_veri[ippu_sutun]:.1f} Mt",
            delta=f"%{(son_veri[ippu_sutun]/toplam_emisyon*100):.1f} pay"
        )
    
    with col_s3:
        st.metric(
            label="🌾 Tarım",
            value=f"{son_veri[tarim_sutun]:.1f} Mt",
            delta=f"%{(son_veri[tarim_sutun]/toplam_emisyon*100):.1f} pay"
        )
    
    with col_s4:
        st.metric(
            label="🗑️ Atık",
            value=f"{son_veri[atik_sutun]:.1f} Mt",
            delta=f"%{(son_veri[atik_sutun]/toplam_emisyon*100):.1f} pay"
        )

# =============================================================================
# TAB 3: YAPAY ZEKA PROJEKSİYONU
# =============================================================================

with tab3:
    st.subheader("🤖 Yapay Zeka Destekli Emisyon Projeksiyonu")
    
    col_ayar, col_sonuc = st.columns([1, 3])
    
    with col_ayar:
        st.caption("⚙️ Model Ayarları")
        
        hedef_sektor = st.selectbox(
            "Sektör Seçimi",
            ["Toplam Emisyon", "Enerji", "Endüstri", "Tarım", "Atık"],
            index=0
        )
        
        sektor_sutun_map = {
            "Toplam Emisyon": toplam_sutun,
            "Enerji": enerji_sutun,
            "Endüstri": ippu_sutun,
            "Tarım": tarim_sutun,
            "Atık": atik_sutun
        }
        secili_sutun = sektor_sutun_map[hedef_sektor]
        
        model_derece = st.radio(
            "Model Tipi",
            ["Doğrusal (1. derece)", "Kuadratik (2. derece)", "Kübik (3. derece)"],
            index=1
        )
        derece_map = {"Doğrusal (1. derece)": 1, "Kuadratik (2. derece)": 2, "Kübik (3. derece)": 3}
        derece = derece_map[model_derece]
        
        hedef_yil = st.slider(
            "Projeksiyon Yılı",
            min_value=2025,
            max_value=2053,
            value=2035
        )
        
        tahmin_btn = st.button("📊 Projeksiyonu Hesapla", use_container_width=True)
    
    with col_sonuc:
        if tahmin_btn or True:
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error
            
            X = df_envanter['Year'].values.reshape(-1, 1)
            y = df_envanter[secili_sutun].values
            
            poly = PolynomialFeatures(degree=derece)
            X_poly = poly.fit_transform(X)
            model = LinearRegression()
            model.fit(X_poly, y)
            
            y_pred = model.predict(X_poly)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            gelecek_yillar = np.arange(son_yil + 1, hedef_yil + 1).reshape(-1, 1)
            gelecek_poly = poly.transform(gelecek_yillar)
            gelecek_tahmin = model.predict(gelecek_poly)
            
            ndc_yillar = np.arange(son_yil + 1, 2031)
            ndc_tahmin = np.linspace(y[-1], 695, len(ndc_yillar))
            
            st.caption(f"📈 {hedef_sektor} - Projeksiyon Sonuçları")
            
            fig = go.Figure()
            
            # Gerçekleşen veriler
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y,
                mode='markers',
                name='Gerçekleşen',
                marker=dict(color=RENKLER['birincil'], size=10, symbol='circle'),
                hovertemplate='Yıl: %{x}<br>Emisyon: %{y:.1f} Mt<extra></extra>'
            ))
            
            # Model trendi
            fig.add_trace(go.Scatter(
                x=df_envanter['Year'],
                y=y_pred,
                mode='lines',
                name='Model Trendi',
                line=dict(color=RENKLER['bilgi'], width=2),
            ))
            
            # BAU projeksiyonu
            fig.add_trace(go.Scatter(
                x=gelecek_yillar.flatten(),
                y=gelecek_tahmin,
                mode='lines',
                name='Referans Senaryo (BAU)',
                line=dict(color=RENKLER['tehlike'], width=3, dash='dash'),
            ))
            
            # NDC hedefi
            if hedef_sektor == "Toplam Emisyon":
                fig.add_trace(go.Scatter(
                    x=ndc_yillar,
                    y=ndc_tahmin,
                    mode='lines',
                    name='NDC Hedef Yörüngesi',
                    line=dict(color=RENKLER['basari'], width=3, dash='dot'),
                ))
                
                fig.add_trace(go.Scatter(
                    x=[2030],
                    y=[695],
                    mode='markers+text',
                    name='NDC 2030',
                    marker=dict(color=RENKLER['basari'], size=16, symbol='star'),
                    text=['695 Mt'],
                    textposition='top center',
                    textfont=dict(size=12, color=RENKLER['basari'])
                ))
            
            hedef_tahmin = model.predict(poly.transform([[hedef_yil]]))[0]
            fig.add_trace(go.Scatter(
                x=[hedef_yil],
                y=[hedef_tahmin],
                mode='markers+text',
                name=f'{hedef_yil} Tahmini',
                marker=dict(color=RENKLER['uyari'], size=16, symbol='diamond'),
                text=[f'{hedef_tahmin:.0f} Mt'],
                textposition='top center',
                textfont=dict(size=12, color=RENKLER['uyari'])
            ))
            
            fig.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂ eşdeğeri)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=tema['text_primary'])),
                hovermode="x unified",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=450,
                xaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                yaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                font=dict(color=tema['text_primary'])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrikler
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("R² Skoru", f"{r2:.4f}", help="Model uyum kalitesi (1'e yakın = iyi)")
            with col_m2:
                st.metric("Ortalama Hata", f"{mae:.1f} Mt", help="Ortalama Mutlak Hata")
            with col_m3:
                st.metric(f"{hedef_yil} Tahmini", f"{hedef_tahmin:.0f} Mt")
            with col_m4:
                if hedef_sektor == "Toplam Emisyon":
                    fark = hedef_tahmin - 695
                    st.metric("NDC'den Sapma", f"{fark:+.0f} Mt", delta_color="inverse")

# =============================================================================
# TAB 4: PİYASA SİMÜLASYONU
# =============================================================================

with tab4:
    st.subheader("🏭 Ajan Tabanlı Piyasa Simülasyonu")
    
    senaryo_sonuclari = senaryo_sonuclari_yukle()
    
    if senaryo_sonuclari:
        st.success("✅ Senaryo sonuçları başarıyla yüklendi. Aşağıda farklı politika senaryolarının karşılaştırmalı analizi yer almaktadır.")
        
        col_sim1, col_sim2 = st.columns(2)
        
        with col_sim1:
            st.caption("📉 Emisyon Karşılaştırması")
            
            fig_emisyon = go.Figure()
            
            renk_map = {
                "Referans Senaryo (BAU)": '#94a3b8',
                "Yumuşak ETS": '#3b82f6',
                "Sıkı ETS": '#22c55e',
                "ETS + Teşvik": '#8b5cf6'
            }
            
            for senaryo_adi, df in senaryo_sonuclari.items():
                if senaryo_adi in secili_senaryolar or not secili_senaryolar:
                    fig_emisyon.add_trace(go.Scatter(
                        x=df['Yil'],
                        y=df['Toplam_Emisyon'],
                        mode='lines+markers',
                        name=senaryo_adi,
                        line=dict(color=renk_map.get(senaryo_adi, '#666'), width=3),
                        marker=dict(size=6)
                    ))
            
            fig_emisyon.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Emisyon (Mt CO₂eq)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=tema['text_primary'])),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                yaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                font=dict(color=tema['text_primary'])
            )
            
            st.plotly_chart(fig_emisyon, use_container_width=True)
        
        with col_sim2:
            st.caption("💰 Karbon Fiyatı Gelişimi")
            
            fig_fiyat = go.Figure()
            
            for senaryo_adi, df in senaryo_sonuclari.items():
                if senaryo_adi in secili_senaryolar or not secili_senaryolar:
                    fig_fiyat.add_trace(go.Scatter(
                        x=df['Yil'],
                        y=df['Karbon_Fiyati'],
                        mode='lines+markers',
                        name=senaryo_adi,
                        line=dict(color=renk_map.get(senaryo_adi, '#666'), width=3),
                        marker=dict(size=6)
                    ))
            
            fig_fiyat.update_layout(
                xaxis_title="Yıl",
                yaxis_title="Fiyat ($/ton CO₂)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=tema['text_primary'])),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                yaxis=dict(gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
                font=dict(color=tema['text_primary'])
            )
            
            st.plotly_chart(fig_fiyat, use_container_width=True)
        
        # Radar Chart - Senaryo Karşılaştırma
        st.caption("🎯 Senaryo Performans Karşılaştırması")
        
        kategoriler = ['Emisyon Azaltımı', 'Maliyet Etkinliği', 'Uygulama Kolaylığı', 'Sosyal Kabul', 'Çevresel Etki']
        
        fig_radar = go.Figure()
        
        radar_verileri = {
            "Referans Senaryo (BAU)": [20, 90, 100, 80, 20],
            "Yumuşak ETS": [50, 70, 70, 60, 50],
            "Sıkı ETS": [80, 50, 40, 40, 80],
            "ETS + Teşvik": [90, 60, 50, 70, 95]
        }
        
        for senaryo, degerler in radar_verileri.items():
            if senaryo in secili_senaryolar or not secili_senaryolar:
                fig_radar.add_trace(go.Scatterpolar(
                    r=degerler + [degerler[0]],
                    theta=kategoriler + [kategoriler[0]],
                    fill='toself',
                    name=senaryo,
                    line=dict(color=renk_map.get(senaryo, '#666'), width=2),
                    opacity=0.7
                ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor=tema['border'], tickfont=dict(color=tema['text_secondary'])),
                angularaxis=dict(tickfont=dict(color=tema['text_primary'])),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color=tema['text_primary'])),
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=tema['text_primary'])
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Özet Tablo
        st.caption("📋 Senaryo Karşılaştırma Tablosu (2035)")
        
        bau_emisyon = senaryo_sonuclari.get("Referans Senaryo (BAU)", pd.DataFrame({'Toplam_Emisyon': [0]}))['Toplam_Emisyon'].iloc[-1]
        
        tablo_verileri = []
        for senaryo_adi, df in senaryo_sonuclari.items():
            emisyon = df['Toplam_Emisyon'].iloc[-1]
            azaltim = ((bau_emisyon - emisyon) / bau_emisyon * 100) if bau_emisyon > 0 else 0
            tablo_verileri.append({
                'Senaryo': senaryo_adi,
                'Emisyon (2035)': f"{emisyon:.1f} Mt",
                'Azaltım (BAU\'ya göre)': f"%{azaltim:.1f}",
                'Karbon Fiyatı': f"${df['Karbon_Fiyati'].iloc[-1]:.0f}/ton",
                'Dönüşen Tesis': f"{int(df['Temiz_Tesis'].iloc[-1]) if 'Temiz_Tesis' in df.columns else '-'}"
            })
        
        st.dataframe(
            pd.DataFrame(tablo_verileri),
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.warning("⚠️ Senaryo sonuçları bulunamadı. Lütfen simülasyonu çalıştırın:")
        st.code("python src/piyasa_simulasyonu_v2.py", language="bash")

# =============================================================================
# TAB 5: BÖLGESEL ANALİZ
# =============================================================================

with tab5:
    st.subheader("🗺️ Bölgesel Karbon Maliyeti ve Emisyon Haritası")
    
    if df_il is not None and not df_il.empty:
        
        # İl koordinatları (genişletilmiş liste)
        il_koordinatlar = {
            'Istanbul': (41.0082, 28.9784),
            'Ankara': (39.9334, 32.8597),
            'Izmir': (38.4192, 27.1287),
            'Bursa': (40.1885, 29.0610),
            'Kocaeli': (40.8533, 29.8815),
            'Adana': (37.0000, 35.3213),
            'Gaziantep': (37.0662, 37.3833),
            'Zonguldak': (41.4564, 31.7987),
            'Hatay': (36.4018, 36.3498),
            'Manisa': (38.6191, 27.4289),
            'Tekirdag': (40.9833, 27.5167),
            'Kahramanmaras': (37.5858, 36.9371),
            'Konya': (37.8746, 32.4932),
            'Antalya': (36.8969, 30.7133),
            'Mersin': (36.8121, 34.6415),
            'Kayseri': (38.7312, 35.4787),
            'Eskisehir': (39.7767, 30.5206),
            'Sakarya': (40.7569, 30.3781),
            'Denizli': (37.7833, 29.0947),
            'Samsun': (41.2867, 36.33)
        }
        
        # --- SİMÜLASYON VERİSİ ENTEGRASYONU ---
        # Seçili senaryonun karbon fiyatını al
        mevcut_fiyat = karbon_fiyati  # Sidebar'dan gelen değer
        
        if senaryo_sonuclari:
            # En son senaryo sonucundan fiyat al
            for senaryo_adi in secili_senaryolar:
                if senaryo_adi in senaryo_sonuclari:
                    secili_df = senaryo_sonuclari[senaryo_adi]
                    mevcut_fiyat = secili_df['Karbon_Fiyati'].iloc[-1]
                    break
        
        # Harita verisini hazırla
        df_harita = df_il.copy()
        
        # Simülasyondan gelen toplam emisyonu kullan
        toplam_sim_emisyon = toplam_emisyon  # Mevcut yıl emisyonu
        if senaryo_sonuclari and secili_senaryolar:
            for senaryo_adi in secili_senaryolar:
                if senaryo_adi in senaryo_sonuclari:
                    toplam_sim_emisyon = senaryo_sonuclari[senaryo_adi]['Toplam_Emisyon'].iloc[-1]
                    break
        
        # İl bazlı emisyon ve karbon maliyeti hesapla
        df_harita['Simule_Emisyon'] = df_harita['Sanayi_Payi'] * toplam_sim_emisyon
        df_harita['Karbon_Maliyeti_Milyon_USD'] = (df_harita['Simule_Emisyon'] * mevcut_fiyat) / 1e6
        
        # Risk skoru hesapla (0-100 arası)
        max_maliyet = df_harita['Karbon_Maliyeti_Milyon_USD'].max()
        df_harita['Risk_Skoru'] = (df_harita['Karbon_Maliyeti_Milyon_USD'] / max_maliyet * 100).fillna(0)
        
        # Koordinatları ekle
        df_harita['lat'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[0])
        df_harita['lon'] = df_harita['Il_Adi'].map(lambda x: il_koordinatlar.get(x, (39.0, 35.0))[1])
        
        # Bilgi kutusu
        st.markdown(f"""
        <div class="info-box">
            <p>📊 <strong>Harita Parametreleri:</strong> Karbon Fiyatı: <strong>${mevcut_fiyat:.0f}/ton</strong> | 
            Toplam Emisyon: <strong>{toplam_sim_emisyon:.1f} Mt</strong> | 
            Senaryo: <strong>{secili_senaryolar[0] if secili_senaryolar else 'Varsayılan'}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- ANA HARİTA: Ekonomik Risk ve Emisyon Dağılımı ---
        fig_map = px.scatter_mapbox(
            df_harita,
            lat='lat',
            lon='lon',
            size='Simule_Emisyon',
            color='Karbon_Maliyeti_Milyon_USD',
            hover_name='Il_Adi',
            hover_data={
                'Simule_Emisyon': ':.2f',
                'Karbon_Maliyeti_Milyon_USD': ':.3f',
                'Risk_Skoru': ':.1f',
                'Bolge': True,
                'lat': False,
                'lon': False
            },
            title="İllere Göre Ekonomik Risk ve Emisyon Dağılımı",
            color_continuous_scale=px.colors.sequential.Reds,
            size_max=60,
            zoom=5,
            center={"lat": 39.0, "lon": 35.0}
        )
        
        fig_map.update_layout(
            mapbox_style="carto-positron",
            height=550,
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title="Karbon Maliyeti<br>(Milyon $)",
                tickformat=".2f"
            ),
            title=dict(
                font=dict(size=17, color=tema['text_primary'], family='Inter'),
                x=0.5,
                xanchor='center'
            )
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        
        # --- ÖZET METRİKLER ---
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric(
                label="💰 Toplam Karbon Maliyeti",
                value=f"${df_harita['Karbon_Maliyeti_Milyon_USD'].sum():.1f}M",
                delta=f"Fiyat: ${mevcut_fiyat}/ton"
            )
        
        with col_m2:
            en_riskli_il = df_harita.loc[df_harita['Risk_Skoru'].idxmax(), 'Il_Adi']
            st.metric(
                label="⚠️ En Riskli İl",
                value=en_riskli_il,
                delta=f"Risk: {df_harita['Risk_Skoru'].max():.0f}/100"
            )
        
        with col_m3:
            st.metric(
                label="🏭 Analiz Edilen İl",
                value=f"{len(df_harita)}",
                delta="Sanayi bölgesi"
            )
        
        with col_m4:
            ortalama_maliyet = df_harita['Karbon_Maliyeti_Milyon_USD'].mean()
            st.metric(
                label="📊 Ortalama Maliyet",
                value=f"${ortalama_maliyet:.2f}M",
                delta="İl başına"
            )
        
        # --- BAR CHART: İl Bazlı Sıralama ---
        st.caption("📊 İl Bazlı Karbon Maliyeti Sıralaması")
        
        df_goster = df_harita[['Il_Adi', 'Bolge', 'Simule_Emisyon', 'Karbon_Maliyeti_Milyon_USD', 'Risk_Skoru']].copy()
        df_goster = df_goster.sort_values('Karbon_Maliyeti_Milyon_USD', ascending=True)
        
        fig_bar = px.bar(
            df_goster,
            x='Karbon_Maliyeti_Milyon_USD',
            y='Il_Adi',
            orientation='h',
            color='Risk_Skoru',
            color_continuous_scale=['#d1fae5', '#fbbf24', '#dc2626'],
            hover_data={
                'Simule_Emisyon': ':.2f',
                'Bolge': True,
                'Risk_Skoru': ':.1f'
            },
            labels={
                'Karbon_Maliyeti_Milyon_USD': 'Karbon Maliyeti (Milyon $)',
                'Il_Adi': '',
                'Risk_Skoru': 'Risk Skoru'
            }
        )
        
        fig_bar.update_layout(
            xaxis_title="Karbon Maliyeti (Milyon $)",
            yaxis_title="",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=tema['text_primary']),
            showlegend=False,
            xaxis=dict(tickfont=dict(color=tema['text_secondary']), title=dict(font=dict(color=tema['text_primary']))),
            yaxis=dict(tickfont=dict(color=tema['text_primary'])),
            coloraxis_colorbar=dict(title="Risk<br>Skoru")
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # --- BİLGİ NOTU ---
        st.markdown(f"""
        <div class="warning-box">
            <p>⚠️ <strong>Yorumlama Notu:</strong> Bu harita, her ilin sanayi payı ve simülasyondaki karbon fiyatına göre 
            tahmini karbon vergisi yükünü göstermektedir. Yüksek riskli iller (kırmızı), ETS uygulamasından 
            en çok etkilenecek bölgelerdir. Karbon fiyatı ${mevcut_fiyat}/ton olarak hesaplanmıştır.</p>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.warning("Bölgesel veri bulunamadı.")

# =============================================================================
# TAB 6: RAPOR VE İNDİRME
# =============================================================================

with tab6:
    st.subheader("📋 Analiz Raporu ve Veri İndirme")
    
    st.markdown("""
    ### 📊 Yönetici Özeti
    
    Bu rapor, Türkiye'nin sera gazı emisyonlarının mevcut durumunu, gelecek projeksiyonlarını ve 
    farklı politika senaryolarının karşılaştırmalı analizini sunmaktadır.
    """)
    
    col_ozet1, col_ozet2 = st.columns(2)
    
    with col_ozet1:
        st.markdown(f"""
        #### 📈 Mevcut Durum
        - **Toplam Emisyon ({son_yil}):** {toplam_emisyon:.1f} Mt CO₂eq
        - **Enerji Sektörü Payı:** %{enerji_payi:.1f}
        - **1990'dan Bu Yana Artış:** +%{artis_orani:.0f}
        - **Yıllık Değişim:** {degisim:+.1f} Mt
        """)
    
    with col_ozet2:
        st.markdown("""
        #### 🎯 Hedefler ve Taahhütler
        - **NDC 2030 Hedefi:** 695 Mt CO₂eq
        - **Net Sıfır Hedef Yılı:** 2053
        - **ETS Başlangıcı:** 2026
        - **Paris Anlaşması:** Onaylandı ✅
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 📚 Metodoloji
    
    Bu çalışmada üç temel metodoloji kullanılmıştır:
    
    1. **Polinom Regresyon Analizi:** Geçmiş verilere dayalı trend tahmini
    2. **Ajan Tabanlı Modelleme (ABM):** Firma davranışlarının simülasyonu
    3. **Senaryo Analizi:** Farklı politika seçeneklerinin değerlendirilmesi
    
    ### 📖 Kaynak Referansları
    
    - IPCC (2006). Guidelines for National Greenhouse Gas Inventories
    - T.C. Çevre Bakanlığı (2024). Turkish NIR 1990-2022
    - Yu et al. (2020). Modeling the ETS from an agent-based perspective
    - Climate Action Tracker (2024). Türkiye Country Assessment
    """)
    
    # İndirme bölümü
    st.caption("📥 Veri İndirme")
    
    col_indir1, col_indir2, col_indir3 = st.columns(3)
    
    with col_indir1:
        envanter_csv = df_envanter.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📊 Envanter Verileri (CSV)",
            data=envanter_csv,
            file_name="tr_zero_envanter_verileri.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col_indir2:
        if senaryo_sonuclari:
            tum_senaryolar = pd.concat([
                df.assign(Senaryo=isim) for isim, df in senaryo_sonuclari.items()
            ])
            senaryo_csv = tum_senaryolar.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="🏭 Senaryo Sonuçları (CSV)",
                data=senaryo_csv,
                file_name="tr_zero_senaryo_sonuclari.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col_indir3:
        if df_il is not None:
            il_csv = df_il.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="🗺️ Bölgesel Veriler (CSV)",
                data=il_csv,
                file_name="tr_zero_bolgesel_veriler.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.info("📄 **PDF Rapor:** Tam raporu PDF formatında indirmek için tarayıcınızın yazdırma fonksiyonunu (Ctrl+P / Cmd+P) kullanarak 'PDF olarak kaydet' seçeneğini tercih edebilirsiniz.")

# =============================================================================
# FOOTER
# =============================================================================

st.divider()
col_footer = st.columns([1, 3, 1])
with col_footer[1]:
    st.markdown("### 🌱 TR-ZERO")
    st.markdown("**Ulusal İklim Karar Destek Sistemi v4.0**")
    st.caption("İbrahim Hakkı Keleş • Oğuz Gökdemir • Melis Mağden")
    st.caption("Endüstri Mühendisliği Bitirme Tezi | Aralık 2025")
    st.caption("Veri Kaynakları: UNFCCC NIR 2024 • TÜİK • IEA • Climate Action Tracker")
    st.caption(f"Son Güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
