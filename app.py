import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import pandas as pd

# ==============================================================================
# CONFIG CONFIGURATION UTAMA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Analisis Omzet & Mismatch Model - PGI",
    page_icon="PGI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEM LOGIN AKSES (PASSWORD PROTECTED) ---
def check_password():
    """Mengembalikan True jika pengguna memasukkan password yang benar."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.center = st.columns([1, 2, 1])
    with st.center[1]:
        st.title("🔒 Akses Terbatas")
        st.write("Silakan masukkan password untuk mengakses Dashboard PGI.")
        
        user_password = st.text_input("Password", type="password", placeholder="Masukkan password di sini")
        
        if st.button("Masuk"):
            if user_password == "1juta$":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Password salah! Silakan hubungi Mukhammad Rekza Mufti (081536175933)- Data Analyst - Divisi Bisnis - Pusat Gadai Indonesia.")
                
        return False

if check_password():

    # --- FUNGSI LOADING DATABASE LANGSUNG DARI GOOGLE SHEETS ---
    @st.cache_data
    def load_data():
        # Menggunakan link ekspor CSV dari Google Sheets Anda
        sheet_url = "https://docs.google.com/spreadsheets/d/15cug7vGihg3Pf2oTRl2EX_ySB55orD43a3A3-_6o7qo/export?format=csv&gid=784346653"
        df = pd.read_csv(sheet_url)
        return df
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Gagal memuat database dari Google Sheets. Detail: {e}")
        st.stop()
    
    # --- TAMPILAN SIDEBAR & KONTROL FILTER ---
    st.sidebar.title("Navigasi & Filter")
    st.sidebar.markdown("Ketik nama cabang di bawah ini. Jika dikosongkan, peta otomatis menampilkan **seluruh cabang**.")
    
    search_cabang = st.sidebar.text_input("Ketik Nama Cabang:", value="", placeholder="Contoh: BDG009")
    
    if search_cabang.strip() != "":
        df_filtered = df[df['nama_cabang'].str.contains(search_cabang, case=False, na=False)]
        if df_filtered.empty:
            st.sidebar.warning(f"Cabang '{search_cabang}' tidak ditemukan. Menampilkan seluruh cabang.")
            df_filtered = df
    else:
        df_filtered = df
    
    # --- HEADER UTAMA ---
    st.title("Dashboard Klasifikasi Omzet & Validasi Mismatch Model Prediksi")
    st.markdown("Spasial interaktif untuk memetakan performa aktual kantor cabang PGI serta mengevaluasi akurasi prediksi model OLS, Random Forest, dan GWR.")
    
    # --- TAMPILAN METRIK (Menyesuaikan Nama Kolom Original di Sheet) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Cabang Ditampilkan", value=f"{len(df_filtered)} Cabang")
    with col2:
        m_ols_count = len(df_filtered[df_filtered['Mismatch_OLS'] != 'Match']) if 'Mismatch_OLS' in df_filtered.columns else 0
        st.metric(label="OLS Mismatch", value=f"{m_ols_count} Kasus", delta="Akurasi: 70.10%", delta_color="off")
    with col3:
        m_rf_count = len(df_filtered[df_filtered['Mismatch_RF'] != 'Match']) if 'Mismatch_RF' in df_filtered.columns else 0
        st.metric(label="Random Forest Mismatch", value=f"{m_rf_count} Kasus", delta="Akurasi: 85.12%", delta_color="normal")
    with col4:
        m_gwr_count = len(df_filtered[df_filtered['Mismatch_GWR'] != 'Match']) if 'Mismatch_GWR' in df_filtered.columns else 0
        st.metric(label="GWR Mismatch", value=f"{m_gwr_count} Kasus", delta="Akurasi: 72.85%", delta_color="off")
    
    st.markdown("---")
    
    # --- PEMBUATAN PETA INTERAKTIF FOLIUM ---
    def generate_map(dataframe):
        def get_color(kategori):
            if kategori == 'Tinggi': return '#2ca02c'
            elif kategori == 'Sedang': return '#ff7f0e'
            elif kategori == 'Rendah': return '#d62728'
            else: return '#7f7f7f'
    
        if dataframe.empty or pd.isna(dataframe['latitude'].mean()):
            map_center = [-2.548926, 118.014863]
            zoom_init = 5
        else:
            map_center = [dataframe['latitude'].mean(), dataframe['longitude'].mean()]
            zoom_init = 11 if len(dataframe) == 1 else 10
    
        m = folium.Map(location=map_center, zoom_start=zoom_init, tiles='OpenStreetMap')
    
        layer_aktual = folium.FeatureGroup(name=' Performa Aktual Cabang (K-Means)', show=True)
        layer_ols = folium.FeatureGroup(name=' Prediksi OLS (70.10%)', show=False)
        layer_rf = folium.FeatureGroup(name=' Prediksi Random Forest (85.12%)', show=False)
        layer_gwr = folium.FeatureGroup(name=' Prediksi GWR (72.85%)', show=False)
    
        layer_aktual.add_to(m)
        layer_ols.add_to(m)
        layer_rf.add_to(m)
        layer_gwr.add_to(m)
    
        mismatch_types_ols = sorted([t for t in dataframe['Mismatch_OLS'].unique() if t != 'Match']) if 'Mismatch_OLS' in dataframe.columns else []
        mismatch_types_rf  = sorted([t for t in dataframe['Mismatch_RF'].unique() if t != 'Match']) if 'Mismatch_RF' in dataframe.columns else []
        mismatch_types_gwr = sorted([t for t in dataframe['Mismatch_GWR'].unique() if t != 'Match']) if 'Mismatch_GWR' in dataframe.columns else []
    
        sub_layers_ols = {t: folium.FeatureGroup(name=f"{t} (OLS)", show=False) for t in mismatch_types_ols}
        sub_layers_rf  = {t: folium.FeatureGroup(name=f"{t} (RF)", show=False) for t in mismatch_types_rf}
        sub_layers_gwr = {t: folium.FeatureGroup(name=f"{t} (GWR)", show=False) for t in mismatch_types_gwr}
    
        for sub in sub_layers_ols.values(): sub.add_to(m)
        for sub in sub_layers_rf.values():  sub.add_to(m)
        for sub in sub_layers_gwr.values(): sub.add_to(m)
    
        for index, row in dataframe.iterrows():
            if pd.isna(row['latitude']) or pd.isna(row['longitude']):
                continue
    
            # --- PROTEKSI PEMANGGILAN KOLOM (Menggunakan Huruf Besar Sesuai Sheet) ---
            omzet_act = int(row['Omzet_Actual']) if 'Omzet_Actual' in row and pd.notna(row['Omzet_Actual']) else 0
            pred_ols = int(row['Prediksi_Omzet_OLS']) if 'Prediksi_Omzet_OLS' in row and pd.notna(row['Prediksi_Omzet_OLS']) else 0
            pred_rf = int(row['Prediksi_Omzet_RF']) if 'Prediksi_Omzet_RF' in row and pd.notna(row['Prediksi_Omzet_RF']) else 0
            pred_gwr = int(row['Prediksi_Omzet_GWR']) if 'Prediksi_Omzet_GWR' in row and pd.notna(row['Prediksi_Omzet_GWR']) else 0
            
            pop_penduduk = int(row['penduduk']) if 'penduduk' in row and pd.notna(row['penduduk']) else 0
            ump_umk = int(row['umk']) if 'umk' in row and pd.notna(row['umk']) else 0
            toko_ponsel = int(row['jumlah_toko_ponsel']) if 'jumlah_toko_ponsel' in row and pd.notna(row['jumlah_toko_ponsel']) else 0
            comp = row['jumlah_kompetitor'] if 'jumlah_kompetitor' in row and pd.notna(row['jumlah_kompetitor']) else 0
    
            tabel_html = f"""
            <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 2px solid #eee;">Cabang: {row['nama_cabang']}</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <tr style="background-color: #f8f9fa;">
                    <th style="text-align: left; padding: 5px;">Data</th>
                    <th style="text-align: right; padding: 5px;">Nominal (Rp)</th>
                    <th style="text-align: center; padding: 5px;">Kategori</th>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>Aktual</b></td>
                    <td style="text-align: right; padding: 5px;">{omzet_act:,}</td>
                    <td style="text-align: center; padding: 5px;"><span style="color: {get_color(row.get('Kategori_Omzet_Actual', ''))}; font-weight: bold;">{row.get('Kategori_Omzet_Actual', '-')}</span></td>
                </tr>
                <tr>
                    <td style="padding: 5px;">Prediksi OLS</td>
                    <td style="text-align: right; padding: 5px;">{pred_ols:,}</td>
                    <td style="text-align: center; padding: 5px;">{row.get('Kategori_Prediksi_OLS', '-')}</td>
                </tr>
                <tr style="border-top: 1px solid #eee;">
                    <td style="padding: 5px;">Prediksi RF</td>
                    <td style="text-align: right; padding: 5px;">{pred_rf:,}</td>
                    <td style="text-align: center; padding: 5px;">{row.get('Kategori_Prediksi_RF', '-')}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;">Prediksi GWR</td>
                    <td style="text-align: right; padding: 5px;">{pred_gwr:,}</td>
                    <td style="text-align: center; padding: 5px;">{row.get('Kategori_Prediksi_GWR', '-')}</td>
                </tr>
            </table>
            <div style="margin-top: 10px; font-size: 11px; color: #666; background: #f5f5f5; padding: 5px; border-radius: 4px; border-left: 3px solid #ccc;">
                <b>Detail Wilayah:</b><br>
                Populasi: {pop_penduduk:,} jiwa<br>
                Kompetitor: {comp} ruko<br>
                UMP: {ump_umk:,}<br>
                Toko Ponsel: {toko_ponsel:,} ruko
            </div>
            """
    
            popup_aktual = f'<div style="font-family: Arial, sans-serif; width: 300px; padding: 10px;">{tabel_html}<div style="margin-top: 5px; font-size: 11px; background: #eceff1; padding: 5px; border-radius: 4px;">Status OLS: <b>{row.get("Mismatch_OLS", "Match")}</b></div></div>'
            popup_rf     = f'<div style="font-family: Arial, sans-serif; width: 300px; padding: 10px;">{tabel_html}<div style="margin-top: 5px; font-size: 11px; background: #fffde7; padding: 5px; border-radius: 4px;">Status RF: <b>{row.get("Mismatch_RF", "Match")}</b></div></div>'
            popup_gwr    = f'<div style="font-family: Arial, sans-serif; width: 300px; padding: 10px;">{tabel_html}<div style="margin-top: 5px; font-size: 11px; background: #e8f5e9; padding: 5px; border-radius: 4px;">Status GWR: <b>{row.get("Mismatch_GWR", "Match")}</b></div></div>'
    
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']], radius=6, color=get_color(row.get('Kategori_Omzet_Actual', '')),
                fill=True, fill_color=get_color(row.get('Kategori_Omzet_Actual', '')), fill_opacity=0.7,
                popup=folium.Popup(popup_aktual, max_width=350), tooltip=f"{row['nama_cabang']} (Aktual)"
            ).add_to(layer_aktual)
    
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']], radius=6, color=get_color(row.get('Kategori_Prediksi_OLS', '-')),
                fill=True, fill_color=get_color(row.get('Kategori_Prediksi_OLS', '-')), fill_opacity=0.7,
                popup=folium.Popup(popup_aktual, max_width=350), tooltip=f"{row['nama_cabang']} (Prediksi OLS)"
            ).add_to(layer_ols)
    
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']], radius=6, color=get_color(row.get('Kategori_Prediksi_RF', '-')),
                fill=True, fill_color=get_color(row.get('Kategori_Prediksi_RF', '-')), fill_opacity=0.7,
                popup=folium.Popup(popup_rf, max_width=350), tooltip=f"{row['nama_cabang']} (Prediksi RF)"
            ).add_to(layer_rf)
    
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']], radius=6, color=get_color(row.get('Kategori_Prediksi_GWR', '-')),
                fill=True, fill_color=get_color(row.get('Kategori_Prediksi_GWR', '-')), fill_opacity=0.7,
                popup=folium.Popup(popup_gwr, max_width=350), tooltip=f"{row['nama_cabang']} (Prediksi GWR)"
            ).add_to(layer_gwr)
    
            m_ols = row.get('Mismatch_OLS', 'Match')
            if m_ols != 'Match' and m_ols in sub_layers_ols:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    icon=folium.Icon(color='red', icon='times', prefix='fa'),
                    popup=folium.Popup(popup_aktual, max_width=350), tooltip=f" OLS Mismatch: {row['nama_cabang']}"
                ).add_to(sub_layers_ols[m_ols])
    
            m_rf = row.get('Mismatch_RF', 'Match')
            if m_rf != 'Match' and m_rf in sub_layers_rf:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    icon=folium.Icon(color='orange', icon='times', prefix='fa'),
                    popup=folium.Popup(popup_rf, max_width=350), tooltip=f" RF Mismatch: {row['nama_cabang']}"
                ).add_to(sub_layers_rf[m_rf])
    
            m_gwr = row.get('Mismatch_GWR', 'Match')
            if m_gwr != 'Match' and m_gwr in sub_layers_gwr:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    icon=folium.Icon(color='darkred', icon='times', prefix='fa'),
                    popup=folium.Popup(popup_gwr, max_width=350), tooltip=f" GWR Mismatch: {row['nama_cabang']}"
                ).add_to(sub_layers_gwr[m_gwr])
    
        grouped_layers = {
            "Model Utama": [layer_aktual, layer_ols, layer_rf, layer_gwr],
            " Mismatch OLS": list(sub_layers_ols.values()),
            " Mismatch Random Forest": list(sub_layers_rf.values()),
            " Mismatch GWR": list(sub_layers_gwr.values())
        }
        plugins.GroupedLayerControl(grouped_layers, collapsed=False, exclusive_groups=False).add_to(m)
    
        css_fix = '''
        <style>
            .leaflet-control-layers-group { font-size: 10.5px !important; margin-bottom: 3px !important; padding: 2px 0 !important; }
            .leaflet-control-layers-group-name { font-size: 11px !important; font-weight: bold !important; margin-bottom: 2px !important; }
            .leaflet-control-layers-selector { width: 11px !important; height: 11px !important; vertical-align: middle !important; margin-top: -2px !important; }
            .leaflet-control-layers { padding: 6px 10px !important; max-height: 280px !important; overflow-y: auto !important; box-shadow: 0px 1px 4px rgba(0,0,0,0.3) !important; border-radius: 6px !important; }
        </style>
        '''
        m.get_root().header.add_child(folium.Element(css_fix))
    
        legend_html = '''
             <div style="position: fixed; bottom: 25px; left: 25px; width: 255px; height: 165px; border: 1px solid #bbb; z-index:9999; font-size:10.5px; font-family: Arial, sans-serif; background-color: white; opacity: 0.95; padding: 10px; border-radius: 6px; box-shadow: 1px 1px 4px rgba(0,0,0,0.15);">
             <b style="font-size: 11.5px; display: block; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 2px;">Kriteria Omzet Cabang PGI</b>
             <div style="margin-bottom: 3px;"><i class="fa fa-circle" style="color:#2ca02c; font-size: 11px;"></i> <b>Tinggi:</b> Rp 1.140.741.667 - Rp 2.209.908.333</div>
             <div style="margin-bottom: 3px;"><i class="fa fa-circle" style="color:#ff7f0e; font-size: 11px;"></i> <b>Sedang:</b> Rp 549.500.000 - Rp 1.097.925.000</div>
             <div style="margin-bottom: 5px;"><i class="fa fa-circle" style="color:#d62728; font-size: 11px;"></i> <b>Rendah:</b> Rp 99.725.000 - Rp 547.475.000</div>
             <hr style="margin: 4px 0; border: 0; border-top: 1px solid #eee;">
             <div style="margin-top: 4px; font-size: 9.5px; color: #555; background: #fffde7; padding: 3px; border-radius: 3px; border-left: 2px solid #fbc02d;"><b style="color: #333;">Simbol Mismatch:</b> <i class="fa fa-times" style="color:red; font-weight:bold;"></i> (Tanda Silang)</div>
             </div>
             '''
        m.get_root().html.add_child(folium.Element(legend_html))
        return m
    
    # --- RENDER MAP PADA STREAMLIT CONTAINER ---
    st.subheader(" Pemetaan Spasial Interaktif")
    peta_folium = generate_map(df_filtered)
    st_folium(peta_folium, width="100%", height=650, returned_objects=[])
    
    # --- BAGIAN FOOTER / DATA VIEW ---
    st.markdown("---")
    with st.expander("Lihat Detail Database Cabang PGI"):
        kolom_tabel = ['nama_cabang', 'Omzet_Actual', 'Kategori_Omzet_Actual', 'Mismatch_OLS', 'Mismatch_RF', 'Mismatch_GWR']
        kolom_eksis = [c for c in kolom_tabel if c in df_filtered.columns]
        st.dataframe(df_filtered[kolom_eksis], use_container_width=True)
