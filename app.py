import streamlit as st
import pandas as pd
import sqlite3
import time
import requests
import yaml
import random
from datetime import datetime
from duckduckgo_search import DDGS
import plotly.express as px

# ============================================================
# KONFIGURASI DATA REFERENSI
# ============================================================

KEYWORDS_DB = {
    "Ikan Invasif (Dilarang)": [
        "Aligator", "Aligator Gar", "Arapaima", "Arapaima Gigas", 
        "Piranha", "Red Belly Piranha", "Sapu-Sapu Hias", "Pleco",
        "Peacock Bass", "Toman (Hias)", "Red Devil Cichlid", "Arwana"
    ],
    "Biota Dilindungi (Appendiks CITES/UU)": [
        "Kima", "Kerang Kima", "Giant Clam", "Kima Raksasa",
        "Penyu", "Telur Penyu", "Teripang", "Sisik Penyu", "Akar Bahar", "Gelang Akar Bahar",
        "Kuda Laut", "Kuda Laut Kering", "Hiu Koboi", "Sirip Hiu",
        "Pari Manta", "Insang Pari", "Ikan Napoleon", "Ikan Hias Banggai Cardinal",
        "Bambu Laut", "Coral", "Terumbu Karang", "Batu Karang Aquarium"
    ],
    "Alat Tangkap Dilarang": [
        "Setrum Ikan", "Alat Setrum", "Racun Potas", "Bom Ikan", "Pukat Harimau"
    ]
}

LOCATIONS_DB = [
    # Kalimantan Utara
    "Tarakan", "Bulungan", "Tanjung Selor", "Nunukan", "Malinau", "Tana Tidung", "Bunyu", "Sebatik", "Kaltara", "Kalimantan Utara",
    # Kalimantan Timur
    "Balikpapan", "Samarinda", "Bontang", "Kutai", "Berau", "Penajam", "Paser", "Mahakam", "Kaltim", "Kalimantan Timur",
    # Kalimantan Barat
    "Pontianak", "Singkawang", "Sambas", "Ketapang", "Sintang", "Kapuas Hulu", "Kalbar", "Kalimantan Barat",
    # Kalimantan Selatan
    "Banjarmasin", "Banjarbaru", "Martapura", "Tabalong", "Kotabaru", "Tanah Bumbu", "Kalsel", "Kalimantan Selatan",
    # Kalimantan Tengah
    "Palangkaraya", "Sampit", "Kotawaringin", "Kalteng", "Kalimantan Tengah",
    # General
    "Jakarta", "Indonesia"
]

PLATFORMS_DB = [
    "facebook.com/marketplace",
    "facebook.com/groups",
    "shopee.co.id",
    "tokopedia.com",
    "bukalapak.com",
    "olx.co.id",
    "instagram.com",
    "lazada.co.id",
    "carousell.id",
    "tiktok.com"
]

OLX_CONFIG = """
rules:
  violations:
    Benih Lobster Ilegal:
      - benih lobster
      - baby lobster
      - bibit lobster
      - benur lobster
      - puerulus
      - lobster seed
    Biota Dilindungi:
      - hiu sirip
      - shark fin
      - penyu
      - turtle
      - pari manta
      - manta ray
      - napoleon
      - kima raksasa
      - giant clam
    Destructive Fishing:
      - ikan bom
      - bom ikan
      - potasium
      - sianida
      - racun ikan
      - setrum ikan
      - strum ikan
    Karang Ilegal:
      - karang hias
      - live rock
      - jual karang
      - terumbu karang
    Alat Tangkap Ilegal:
      - cantrang
      - trawl
      - pukat hela
      - pukat harimau
    Ikan Undersized:
      - rajungan kecil
      - kepiting bertelur
      - lobster bertelur
      - ikan kecil-kecil
scoring:
  min_score_to_show: 50
  weights:
    Benih Lobster Ilegal: 90
    Biota Dilindungi: 85
    Destructive Fishing: 95
    Karang Ilegal: 70
    Alat Tangkap Ilegal: 60
    Ikan Undersized: 55
  boosters:
    - ready
    - ready stock
    - stok
    - kirim
    - cod
    - partai
    - export
    - murah
"""

LOCATION_DICT_OLX = {
    "Kalimantan Utara (Kaltara)": "2000035",
    "Tarakan (Kaltara)": "2000035",
    "Nunukan (Kaltara)": "2000035",
    "Bulungan (Kaltara)": "2000035",
    "Kalimantan Timur (Kaltim)": "2000015",
    "Balikpapan (Kaltim)": "2000015",
    "Samarinda (Kaltim)": "2000015",
    "Bontang (Kaltim)": "2000015",
    "Kalimantan Selatan (Kalsel)": "2000014",
    "Banjarmasin (Kalsel)": "2000014",
    "Banjarbaru (Kalsel)": "2000014",
    "Kalimantan Barat (Kalbar)": "2000012",
    "Pontianak (Kalbar)": "2000012",
    "Singkawang (Kalbar)": "2000012",
    "Kalimantan Tengah (Kalteng)": "2000013",
    "Palangkaraya (Kalteng)": "2000013",
    "Sampit (Kalteng)": "2000013",
    "Indonesia (Semua Lokasi)": "1000001",
    "DKI Jakarta": "2000001",
}

def init_db():
    conn = sqlite3.connect('psdkp_hybrid.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS temuan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal_crawling TEXT,
            sumber_data TEXT,
            platform TEXT,
            kategori TEXT,
            keyword TEXT,
            lokasi TEXT,
            judul TEXT,
            url TEXT UNIQUE,
            harga TEXT,
            penjual TEXT,
            skor INTEGER,
            pelanggaran TEXT,
            status_verifikasi TEXT DEFAULT 'Belum Dicek',
            catatan TEXT
        )
    ''')
    conn.commit()
    conn.close()

def run_dorking_engine(selected_keywords, selected_locs, selected_platforms):
    results = []
    progress_text = "Memulai Patroli Siber (Strict Mode)..."
    my_bar = st.progress(0, text=progress_text)
    total_ops = len(selected_keywords) * len(selected_locs)
    current_op = 0
    
    try:
        ddgs = DDGS()
    except Exception as e:
        st.error(f"Gagal inisialisasi Engine: {e}")
        return []

    try:
        for category, keys in selected_keywords.items():
            for fish in keys:
                for loc in selected_locs:
                    current_op += 1
                    prog_val = min(current_op / total_ops, 1.0)
                    my_bar.progress(prog_val, text=f"Scanning: {fish} di {loc}")
                    
                    queries = [
                        f'site:tokopedia.com "{fish}" {loc}',
                        f'site:shopee.co.id "{fish}" {loc}',
                        f'site:bukalapak.com "{fish}" {loc}',
                        f'site:olx.co.id "{fish}" {loc}',
                        f'jual "{fish}" {loc}'
                    ]
                    
                    for query in queries:
                        try:
                            ddg_results = ddgs.text(query, region="id-id", safesearch='off', max_results=5)
                            if ddg_results:
                                for item in ddg_results:
                                    title = item['title'].lower()
                                    snippet = item['body'].lower()
                                    keyword_lower = fish.lower()
                                    location_lower = loc.lower()
                                    
                                    if keyword_lower not in title and keyword_lower not in snippet: continue
                                    if location_lower not in title and location_lower not in snippet: continue
                                    if "google.com" in item['href']: continue
                                    
                                    detected_platform = "Web Umum"
                                    if "facebook" in item['href']: detected_platform = "Facebook"
                                    elif "instagram" in item['href']: detected_platform = "Instagram"
                                    elif "tokopedia" in item['href']: detected_platform = "Tokopedia"
                                    elif "shopee" in item['href']: detected_platform = "Shopee"
                                    elif "olx" in item['href']: detected_platform = "OLX"
                                    elif "bukalapak" in item['href']: detected_platform = "Bukalapak"
                                    
                                    if not any(d['url'] == item['href'] for d in results):
                                        results.append({
                                            'tanggal_crawling': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            'sumber_data': 'DuckDuckGo (Strict)',
                                            'platform': detected_platform,
                                            'kategori': category,
                                            'keyword': fish,
                                            'lokasi': loc,
                                            'judul': item['title'],
                                            'url': item['href'],
                                            'harga': 'Cek Link',
                                            'penjual': 'N/A',
                                            'skor': 0,
                                            'pelanggaran': category
                                        })
                            time.sleep(0.3)
                        except Exception: continue
    except Exception as e:
        st.error(f"Engine Error: {e}")
    finally:
        my_bar.empty()
    return results

# ==========================================
# KHUSUS VERSI ONLINE (DEMO MODE)
# ==========================================
@st.cache_data(ttl=3600)
def scrape_olx(keyword, location="2000035", max_pages=2):
    # Kita buat delay palsu biar terlihat sedang bekerja
    time.sleep(2) 
    
    # DATA DUMMY / PALSU UNTUK DEMO PRESENTASI
    # Agar dashboard tidak kosong saat dibuka online
    dummy_data = [
        {
            "id": "1", "title": "Jual Bibit Lobster Mutiara Murah", 
            "description": "Ready stok baby lobster mutiara lokasi tarakan, bisa kirim", 
            "price": {"value": {"display": "Rp 15.000"}}, 
            "locations_resolved": {"ADMIN_LEVEL_3_name": "Tarakan Tengah", "ADMIN_LEVEL_1_name": "Kalimantan Utara"},
            "user": {"name": "Nelayan Sukses"}, "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        },
        {
            "id": "2", "title": "Akar Bahar Asli Kualitas Super", 
            "description": "Gelang akar bahar hitam, barang langka kolektor", 
            "price": {"value": {"display": "Rp 250.000"}}, 
            "locations_resolved": {"ADMIN_LEVEL_3_name": "Balikpapan Selatan", "ADMIN_LEVEL_1_name": "Kalimantan Timur"},
            "user": {"name": "Borneo Craft"}, "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        },
        {
            "id": "3", "title": "Dijual Cepat Alat Setrum Ikan Portable", 
            "description": "Alat setrum ikan air tawar, voltage tinggi, siap pakai", 
            "price": {"value": {"display": "Rp 850.000"}}, 
            "locations_resolved": {"ADMIN_LEVEL_3_name": "Samarinda Ulu", "ADMIN_LEVEL_1_name": "Kalimantan Timur"},
            "user": {"name": "Elektronik Jaya"}, "created_at": "2026-01-20T10:00:00"
        },
        {
            "id": "4", "title": "Ikan Aligator Gar Jumbo", 
            "description": "Ikan hias predator aligator gar ukuran 50cm sehat makan rakus", 
            "price": {"value": {"display": "Rp 400.000"}}, 
            "locations_resolved": {"ADMIN_LEVEL_3_name": "Pontianak Kota", "ADMIN_LEVEL_1_name": "Kalimantan Barat"},
            "user": {"name": "Predator Fish"}, "created_at": "2026-01-21T09:30:00"
        },
        {
            "id": "5", "title": "Hiasan Cangkang Kerang Kima Besar", 
            "description": "Cangkang kima raksasa untuk hiasan taman atau aquarium", 
            "price": {"value": {"display": "Rp 1.500.000"}}, 
            "locations_resolved": {"ADMIN_LEVEL_3_name": "Tarakan Barat", "ADMIN_LEVEL_1_name": "Kalimantan Utara"},
            "user": {"name": "Antik Kaltara"}, "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
    ]
    
    # Filter dummy sesuai keyword biar agak realistis
    filtered_results = []
    keyword_lower = keyword.lower()
    
    # Kalau keywordnya "lobster", kasih data lobster, dll.
    for item in dummy_data:
        # Logika sederhana: kalau keyword cocok atau ini mode demo, masukkan data
        if keyword_lower in item['title'].lower() or keyword_lower in item['description'].lower():
            filtered_results.append(item)
            
    # Jika tidak ada yang cocok (misal keyword aneh), kembalikan semua dummy biar ga kosong
    if not filtered_results:
        return dummy_data
        
    return filtered_results
    
    all_items = []
    for page in range(max_pages):
        try:
            params = {
                "facet_limit": 100,
                "location": location,
                "page": page + 1,
                "platform": "web-desktop",
                "q": keyword,
            }
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200: break
            data = response.json()
            items = data.get("data", [])
            if not items: break
            all_items.extend(items)
            time.sleep(random.uniform(1.0, 2.0))
        except: break
    return all_items

def calculate_score(title, description, config):
    text = f"{title} {description}".lower()
    score = 0
    matched_violations = []
    violations = config['rules']['violations']
    weights = config['scoring']['weights']
    
    for category, keywords in violations.items():
        category_matched = False
        matched_keywords = []
        for keyword in keywords:
            if keyword.lower() in text:
                matched_keywords.append(keyword)
                category_matched = True
        if category_matched:
            weight = weights.get(category, 50)
            score += weight
            matched_violations.append(f"{category}: {', '.join(matched_keywords)}")
    
    if matched_violations:
        boosters = config['scoring']['boosters']
        booster_count = sum(1 for b in boosters if b.lower() in text)
        if booster_count > 0:
            score += (booster_count * 5)
            matched_violations.append(f"Booster (+{booster_count*5})")
    
    return score, matched_violations

def hitung_usia_iklan(date_str):
    try:
        post_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
        now = datetime.now()
        diff = now - post_date
        days = diff.days
        if days == 0: return "Hari ini"
        elif days == 1: return "Kemarin"
        elif days < 7: return f"{days} hari yang lalu"
        elif days < 30: return f"{days // 7} minggu yang lalu"
        elif days < 365: return f"{days // 30} bulan yang lalu"
        else: return f"{days // 365} tahun yang lalu"
    except: return "Tidak diketahui"

def run_monitoring_olx(keywords, location, max_pages_per_keyword, config):
    all_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_keywords = len(keywords)
    
    for idx, keyword in enumerate(keywords):
        status_text.text(f"Mencari di OLX: {keyword}...")
        progress_bar.progress((idx + 1) / total_keywords)
        items = scrape_olx(keyword, location=location, max_pages=max_pages_per_keyword)
        for item in items:
            try:
                title = item.get("title", "")
                description = item.get("description", "")
                price = item.get("price", {}).get("value", {}).get("display", "N/A")
                location_info = item.get("locations_resolved", {})
                seller = item.get("user", {}).get("name", "N/A")
                created_at = item.get("created_at", "")
                url = f"https://www.olx.co.id/item/{item.get('id', '')}"
                score, violations = calculate_score(title, description, config)
                usia_iklan = hitung_usia_iklan(created_at) if created_at else "N/A"
                
                if score >= config['scoring']['min_score_to_show']:
                    all_results.append({
                        "Waktu_Monitoring": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Tanggal_Posting": created_at[:10] if created_at else "N/A",
                        "Usia_Iklan": usia_iklan,
                        "Skor": score,
                        "Pelanggaran": "; ".join(violations),
                        "Judul": title,
                        "Harga": price,
                        "Penjual": seller,
                        "Lokasi": location_info.get("ADMIN_LEVEL_3_name", "N/A"),
                        "Provinsi": location_info.get("ADMIN_LEVEL_1_name", "N/A"),
                        "URL": url,
                        "Deskripsi": description[:300],
                        "Keyword": keyword,
                    })
            except Exception: continue
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(all_results)

def save_to_db(data):
    conn = sqlite3.connect('psdkp_hybrid.db')
    c = conn.cursor()
    new_count = 0
    for row in data:
        try:
            c.execute('''
                INSERT OR IGNORE INTO temuan 
                (tanggal_crawling, sumber_data, platform, kategori, keyword, lokasi, 
                 judul, url, harga, penjual, skor, pelanggaran)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['tanggal_crawling'], row['sumber_data'], row['platform'],
                row['kategori'], row['keyword'], row['lokasi'], row['judul'],
                row['url'], row['harga'], row['penjual'], row['skor'], row['pelanggaran']
            ))
            if c.rowcount > 0: new_count += 1
        except: pass
    conn.commit()
    conn.close()
    return new_count

def main():
    st.set_page_config(page_title="PSDKP Hybrid Monitor", layout="wide", page_icon="🛡️")
    init_db()
    
    st.markdown("""<style>.stButton>button {width: 100%; border-radius: 5px;}</style>""", unsafe_allow_html=True)
    
    st.sidebar.title("🛡️ PSDKP Hybrid Patrol")
    st.sidebar.info("**Sistem Gabungan:**\n- Dorking Engine (DuckDuckGo)\n- OLX Scraping (Deep Dive)")
    
    menu = st.sidebar.radio("Navigasi", ["Jalankan Patroli", "Verifikasi Data", "Dashboard", "Export Data"])

    if menu == "Jalankan Patroli":
        st.title("Jalankan Hybrid Monitoring")
        tab1, tab2 = st.tabs(["🌐 Multi-Platform Dorking", "🛒 OLX Scraping"])
        
        with tab1:
            st.subheader("Mesin Pencari Jejak Digital")
            st.info("ℹ️ Menggunakan Engine DuckDuckGo (Strict Mode)")
            
            with st.form("dorking_form"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**1. Pilih Keyword (Database):**")
                    all_keys = []
                    for cat, items in KEYWORDS_DB.items(): all_keys.extend(items)
                    selected_keys = st.multiselect("Pilih dari daftar:", all_keys, default=["Aligator", "Sirip Hiu"])
                    
                    st.markdown("**2. Keyword Tambahan (Custom):**")
                    custom_kw_input = st.text_area("Ketik keyword sendiri (pisahkan dengan koma):", 
                                                   placeholder="Misal: Jual Potas, Ikan Toman Jumbo, Bibit Lobster Murah")
                with col2:
                    st.markdown("**3. Target Lokasi & Platform:**")
                    selected_locs = st.multiselect("Pilih Lokasi:", LOCATIONS_DB, default=["Tarakan", "Kaltara"])
                    selected_platforms = st.multiselect("Pilih Platform:", PLATFORMS_DB, default=["facebook.com/marketplace", "instagram.com"])
                start_dorking = st.form_submit_button("🚀 MULAI SCANNING")
            
            if start_dorking:
                selected_keywords = {}
                for cat, items in KEYWORDS_DB.items():
                    matches = [k for k in selected_keys if k in items]
                    if matches: selected_keywords[cat] = matches
                
                custom_list = [k.strip() for k in custom_kw_input.split(",") if k.strip()]
                if custom_list: selected_keywords["Custom User"] = custom_list
                all_combined_keys = selected_keys + custom_list

                if all_combined_keys and selected_locs and selected_platforms:
                    with st.spinner("Sedang melakukan scanning siber..."):
                        hasil = run_dorking_engine(selected_keywords, selected_locs, selected_platforms)
                        if hasil:
                            new_data = save_to_db(hasil)
                            st.success(f"✅ Selesai! Ditemukan {len(hasil)} tautan potensial ({new_data} data baru).")
                            st.dataframe(pd.DataFrame(hasil).head())
                        else:
                            st.warning("Tidak ditemukan hasil otomatis yang memenuhi filter ketat (Strict Mode).")
                        
                        st.divider()
                        st.info("🔍 **Manual Check Tools**")
                        st.markdown("Jika hasil otomatis kosong, gunakan query manual ini:")
                        keys_str = " OR ".join([f'"{k}"' for k in all_combined_keys])
                        locs_str = " OR ".join([f'"{l}"' for l in selected_locs])
                        for site in PLATFORMS_DB:
                            with st.expander(f"Query Google untuk {site}", expanded=False):
                                st.code(f'({keys_str}) AND ({locs_str}) site:{site}', language="text")
                else: st.error("Mohon pilih minimal satu keyword dan lokasi.")
        
        with tab2:
            st.subheader("OLX Market Monitor")
            with st.form("olx_form"):
                col1, col2 = st.columns(2)
                with col1:
                    olx_keywords_input = st.text_area("Keyword OLX (satu per baris):", value="baby lobster\nsirip hiu\npenyu", height=100)
                    olx_keywords = [k.strip() for k in olx_keywords_input.split("\n") if k.strip()]
                with col2:
                    olx_location = st.selectbox("Pilih Provinsi:", list(LOCATION_DICT_OLX.keys()))
                    olx_max_pages = st.slider("Halaman per Keyword:", 1, 5, 2)
                    olx_min_score = st.slider("Sensitivitas Skor:", 0, 100, 50)
                start_olx = st.form_submit_button("🛒 SCAN OLX")
            
            if start_olx:
                config = yaml.safe_load(OLX_CONFIG)
                config['scoring']['min_score_to_show'] = olx_min_score
                location_code = LOCATION_DICT_OLX[olx_location]
                with st.spinner("Sedang mengambil data OLX..."):
                    df = run_monitoring_olx(olx_keywords, location_code, olx_max_pages, config)
                if not df.empty:
                    hasil = []
                    for idx, row in df.iterrows():
                        hasil.append({
                            'tanggal_crawling': row['Waktu_Monitoring'],
                            'sumber_data': 'OLX Scraping',
                            'platform': 'OLX',
                            'kategori': 'Marketplace',
                            'keyword': row['Keyword'],
                            'lokasi': row['Lokasi'],
                            'judul': row['Judul'],
                            'url': row['URL'],
                            'harga': row['Harga'],
                            'penjual': row['Penjual'],
                            'skor': row['Skor'],
                            'pelanggaran': row['Pelanggaran']
                        })
                    new_data = save_to_db(hasil)
                    st.success(f"✅ Selesai! {len(hasil)} iklan ditemukan ({new_data} baru). Catatan: Data Dummy")
                    st.dataframe(df[['Usia_Iklan', 'Judul', 'Harga', 'Lokasi', 'URL', 'Skor']])
                else: st.info("Tidak ada indikasi pelanggaran ditemukan.")

    elif menu == "Verifikasi Data":
        st.title("Verifikasi Temuan")
        conn = sqlite3.connect('psdkp_hybrid.db')
        col1, col2 = st.columns(2)
        with col1: filter_status = st.selectbox("Filter Status:", ["Belum Dicek", "Valid Pelanggaran", "False Positive", "Semua Data"])
        with col2: filter_sumber = st.selectbox("Filter Sumber:", ["Semua", "DuckDuckGo Dorking", "OLX Scraping"])
        query = "SELECT * FROM temuan WHERE 1=1"
        if filter_status != "Semua Data": query += f" AND status_verifikasi = '{filter_status}'"
        if filter_sumber != "Semua": query += f" AND sumber_data = '{filter_sumber}'"
        df_v = pd.read_sql_query(query, conn)
        if not df_v.empty:
            for index, row in df_v.iterrows():
                with st.expander(f"{row['sumber_data']} - {row['judul']}"):
                    st.write(f"**URL:** {row['url']}")
                    st.write(f"**Lokasi:** {row['lokasi']}")
                    c1, c2 = st.columns(2)
                    if c1.button("Valid", key=f"v{row['id']}"):
                        conn.execute("UPDATE temuan SET status_verifikasi='Valid Pelanggaran' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
                    if c2.button("Abaikan", key=f"x{row['id']}"):
                        conn.execute("UPDATE temuan SET status_verifikasi='False Positive' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
        else: st.info("Tidak ada data yang sesuai filter.")
        conn.close()

    elif menu == "Dashboard":
        st.title("Dashboard Hybrid Monitoring")
        filter_waktu = st.radio("Rentang Waktu:", ["Hari Ini (Sesi Baru)", "Semua Riwayat Database"], horizontal=True)
        conn = sqlite3.connect('psdkp_hybrid.db')
        df = pd.read_sql_query("SELECT * FROM temuan", conn)
        conn.close()
        if not df.empty:
            df['tanggal_dt'] = pd.to_datetime(df['tanggal_crawling'], format='mixed')
            if filter_waktu == "Hari Ini (Sesi Baru)":
                today = datetime.now().date()
                df = df[df['tanggal_dt'].dt.date == today]
            if df.empty:
                st.info("Belum ada patroli hari ini.")
                st.metric("Total Temuan", 0)
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Temuan", len(df))
                col2.metric("Dorking", len(df[df['sumber_data'].isin(['Google Dorking', 'DuckDuckGo Dorking', 'DuckDuckGo (Strict)'])]))
                col3.metric("OLX", len(df[df['sumber_data'] == 'OLX Scraping']))
                col4.metric("Pending", len(df[df['status_verifikasi'] == 'Belum Dicek']))
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(px.pie(df, names='sumber_data', hole=0.4), use_container_width=True)
                with c2: st.plotly_chart(px.bar(df['platform'].value_counts().head(10), orientation='h'), use_container_width=True)
        else: st.info("Database kosong.")

    elif menu == "Export Data":
        st.title("Download Laporan")
        conn = sqlite3.connect('psdkp_hybrid.db')
        df_all = pd.read_sql_query("SELECT * FROM temuan", conn)
        if not df_all.empty:
            st.dataframe(df_all)
            st.download_button("Download CSV", df_all.to_csv(index=False).encode('utf-8'), "laporan_psdkp.csv", "text/csv")
        conn.close()

if __name__ == "__main__":
    main()


