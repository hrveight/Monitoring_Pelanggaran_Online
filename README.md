# Monitoring_Pelanggaran_Online
**Sistem Monitoring & Pengawasan Sumber Daya Kelautan dan Perikanan**

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Status](https://img.shields.io/badge/Status-Active-green)

Aplikasi ini dikembangkan untuk membantu PSDKP dalam melakukan patroli siber guna mendeteksi aktivitas perdagangan ilegal di sektor kelautan dan perikanan pada platform digital (Marketplace & Media Sosial).

---

## 📋 Fitur Utama

### 1. 🌐 Multi-Platform Dorking (DuckDuckGo Engine)
Mesin pencari jejak digital menggunakan teknik **Google Dorking** (via DuckDuckGo) untuk memindai indikasi pelanggaran di platform seperti Facebook, Instagram, Tokopedia, Shopee, dll.
* **Strict Mode:** Filter ketat untuk mengurangi *false positive* (sampah).
* **Custom Keyword:** Pengguna bisa menambahkan kata kunci sendiri secara dinamis.
* **Manual Query Generator:** Menyediakan *syntax* siap salin jika hasil otomatis tidak ditemukan.

### 2. 🛒 OLX Deep Scraping
Modul khusus untuk memindai platform OLX secara mendalam berdasarkan wilayah provinsi (termasuk ID wilayah spesifik).
* **Kalkulasi Skor Pelanggaran:** Sistem otomatis memberikan skor risiko pada setiap temuan.
* **Deteksi Usia Iklan:** Mengetahui kapan iklan diposting (Hari ini, Kemarin, dll).

### 3. 🗺️ Fokus Wilayah & Kategori
* **Wilayah:** Prioritas pada Kalimantan (Utara, Timur, Selatan, Barat, Tengah) dan kota-kota besar lainnya.
* **Kategori Pelanggaran:**
    * Ikan Invasif (Aligator, Arapaima, Piranha, dll).
    * Biota Dilindungi (Penyu, Kima, Hiu Koboi, Akar Bahar, dll).
    * Alat Tangkap Dilarang (Setrum, Potas, Bom Ikan).

### 4. ✅ Verifikasi & Manajemen Data
* **Human-in-the-Loop:** Fitur untuk memvalidasi temuan (Valid/False Positive).
* **Database:** Penyimpanan riwayat temuan menggunakan SQLite.
* **Export:** Unduh laporan hasil patroli ke format CSV.

### 5. 📊 Dashboard Analitik
Ringkasan statistik temuan harian dan sebaran platform pelanggaran.

---

## 🛠️ Teknologi yang Digunakan

* **Python 3.x**: Bahasa pemrograman utama.
* **Streamlit**: Framework untuk antarmuka web interaktif.
* **DuckDuckGo Search**: Library untuk melakukan pencarian dorking tanpa limitasi API key berbayar.
* **Pandas**: Manipulasi dan analisis data tabular.
* **SQLite**: Database ringan untuk menyimpan hasil temuan.
* **Plotly**: Visualisasi grafik interaktif.

---

## ☁️ Deployment

Link streamlit dapat diakses pada x

**⚠️ Catatan Penting untuk Cloud:**
Karena aplikasi ini menggunakan SQLite (`psdkp_hybrid.db`), data yang disimpan akan **ter-reset** setiap kali aplikasi di-*reboot* oleh server Streamlit Cloud (sifat *ephemeral*). Untuk penggunaan demo/presentasi, ini tidak masalah. Untuk penggunaan jangka panjang permanen, disarankan menghubungkan ke Google Sheets atau Cloud Database.
