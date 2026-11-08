
import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import io

from datetime import datetime, time
from openpyxl import load_workbook
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# KONFIGURASI APLIKASI
st.set_page_config(
    page_title="Assisten Belajar",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# KONFIGURASI DATABASE GOOGLE DRIVE
FILE_ID = "1ho1H35Wj6yezHW4BdG4H_mu24sXrtteU"

SCOPES = ["https://www.googleapis.com/auth/drive"]

# Lokasi sementara database di Streamlit Cloud
DB_PATH = "/tmp/Database_Assisten_Belajar_Pulih_2.xlsx"


@st.cache_resource
def get_drive_service():
    credentials_info = dict(st.secrets["gcp_service_account"])

    # Mengantisipasi private key yang tersimpan dengan karakter \n
    credentials_info["private_key"] = (
        credentials_info["private_key"].replace("\\n", "\n")
    )

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )

    return build("drive", "v3", credentials=credentials)

# MEMBUAT KONEKSI GOOGLE DRIVE
drive_service = get_drive_service()

# CEK DAFTAR IZIN FILE GOOGLE DRIVE
izin_file = drive_service.permissions().list(
    fileId=FILE_ID,
    fields="permissions(id,type,emailAddress,role)"
).execute()

for izin in izin_file.get("permissions", []):
    st.write({
        "email": izin.get("emailAddress"),
        "role": izin.get("role"),
        "type": izin.get("type")
    })
# MENGUNDUH DATABASE DARI GOOGLE DRIVE
def download_database():
    service = get_drive_service()

    request = service.files().get_media(fileId=FILE_ID)

    with open(DB_PATH, "wb") as file:
        downloader = MediaIoBaseDownload(file, request)
        selesai = False

        while not selesai:
            status, selesai = downloader.next_chunk()

    return DB_PATH


# MENYIMPAN PERUBAHAN DATABASE KE GOOGLE DRIVE
def upload_database():
    service = get_drive_service()

    with open(DB_PATH, "rb") as file:
        media = MediaIoBaseUpload(
            file,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=True
        )

        service.files().update(
            fileId=FILE_ID,
            media_body=media
        ).execute()

    # Hapus cache agar data terbaru langsung terbaca
    load_database.clear()

# AKSES ADMIN
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

if "admin_login" not in st.session_state:
    st.session_state.admin_login = False

if "tutor_login" not in st.session_state:
    st.session_state.tutor_login = False

if "tutor_id_login" not in st.session_state:
    st.session_state.tutor_id_login = None

if "tutor_nama_login" not in st.session_state:
    st.session_state.tutor_nama_login = None

if "menu_aktif" not in st.session_state:
    st.session_state.menu_aktif = "Beranda"

if "menu_sebelumnya" not in st.session_state:
    st.session_state.menu_sebelumnya = None

if "menu_terbuka" not in st.session_state:
    st.session_state.menu_terbuka = False

# DESAIN CSS
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background-color: #F5F7FB;
}

[data-testid="stSidebar"] {
    background-color: #142B4A;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

[data-testid="stSidebar"] .stRadio label {
    font-size: 14px;
}

.main-title {
    font-size: 29px;
    font-weight: 700;
    color: #142B4A;
    margin-bottom: 2px;
    text-align: center;
}

.subtitle {
    text-align: center;
}
}

.subtitle {
    color: #718096;
    font-size: 13px;
    margin-bottom: 25px;
}

.metric-card {
    background: white;
    padding: 21px;
    border-radius: 13px;
    border: 1px solid #E8EDF4;
    box-shadow: 0px 3px 12px rgba(20,43,74,0.04);
    min-height: 125px;
}



.metric-label {
    color: #718096;
    font-size: 13px;
    font-weight: 500;
}

.metric-value {
    color: #142B4A;
    font-size: 29px;
    font-weight: 700;
    margin-top: 8px;
}

.metric-note {
    color: #718096;
    font-size: 11px;
    margin-top: 4px;
}

[data-testid="stMain"] {
    background-color: #F5F7FB !important;
    color: #142B4A !important;
}

[data-testid="stWidgetLabel"] p {
    color: #142B4A !important;
}


/* LABEL FORM DI DALAM MODAL / DIALOG */
[data-testid="stDialog"] [data-testid="stWidgetLabel"] p,
[role="dialog"] [data-testid="stWidgetLabel"] p {
    color: #FFFFFF !important;
    font-weight: 500 !important;
}

/* LABEL FORM DI DALAM MODAL */
[data-testid="stDialog"] label,
[role="dialog"] label {
    color: #FFFFFF !important;
}


.stTextInput input,
.stTextArea textarea,
.stDateInput input {
    background-color: white !important;
    color: #142B4A !important;
    border: 1px solid #D8E0EA !important;
}

.section-title {
    font-size: 17px;
    font-weight: 600;
    color: #142B4A;
    margin-bottom: 12px;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 12px;
    padding: 8px;
    border: 1px solid #E8EDF4;
}

/* 1. Tulisan peringatan paket */
[data-testid="stAlert"] * {
    color: #142B4A !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* 2. Tulisan pilihan jadwal */
[data-testid="stRadio"] label,
[data-testid="stRadio"] label * {
    color: #142B4A !important;
}

/* 3. Placeholder catatan */
[data-testid="stTextArea"] textarea::placeholder {
    color: #8996A8 !important;
    opacity: 1 !important;
}

/* 4. Tombol kirim pendaftaran */
[data-testid="stFormSubmitButton"] button {
    background-color: #142B4A !important;
    color: #FFFFFF !important;
    border: none !important;
}

[data-testid="stFormSubmitButton"] button * {
    color: #FFFFFF !important;
}

/* WARNA TULISAN MENU SIDEBAR */
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stRadio"] label * {
    color: #FFFFFF !important;
}

/* WARNA TULISAN RADIO FORMULIR */
[data-testid="stMain"] [data-testid="stRadio"] label,
[data-testid="stMain"] [data-testid="stRadio"] label * {
    color: #142B4A !important;
}

/* Membuat teks tombol selalu terlihat */
.stButton > button {
    color: #FFFFFF !important;
    background-color: #142B4A !important;
    border: none !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

/* Warna tombol saat disentuh/hover tetap konsisten */
.stButton > button:hover,
.stButton > button:focus,
.stButton > button:active {
    color: #FFFFFF !important;
    background-color: #1D3B60 !important;
    opacity: 1 !important;
}

/* Tombol utama */
.stButton > button[kind="primary"] {
    background-color: #FF4B4B !important;
    color: #FFFFFF !important;
}

/* Ikon menu dan tombol navigasi */
button[kind="header"],
[data-testid="stHeader"] button {
    color: #142B4A !important;
}


/* =================================
   RESPONSIVE UNTUK HP
================================= */

@media screen and (max-width: 768px) {

    [data-testid="stMainBlockContainer"] {
        padding: 1rem 0.8rem !important;
        max-width: 100% !important;
    }

    .main-title {
        font-size: 23px !important;
    }

    h1 {
        font-size: 25px !important;
    }

    h2 {
        font-size: 21px !important;
    }

    h3 {
        font-size: 18px !important;
    }

    /* Kolom konten */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 12px !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* Header pengunjung tetap sejajar */
    .visitor-header [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center !important;
    }

    .visitor-header [data-testid="column"] {
        min-width: 0 !important;
        flex: initial !important;
    }

    /* Kartu dashboard */
    .metric-card {
        min-height: auto !important;
        padding: 16px !important;
    }

    .metric-value {
        font-size: 25px !important;
    }

    [class*="st-key-metric-card-"] {
        min-height: auto !important;
        padding: 16px !important;
    }

    /* Tombol */
    .stButton > button,
    [data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        min-height: 44px !important;
    }

    /* Gambar */
    [data-testid="stImage"] img {
        max-width: 100% !important;
        height: auto !important;
        object-fit: contain !important;
    }

    /* Tabel */
    [data-testid="stDataFrame"] {
        width: 100% !important;
        overflow-x: auto !important;
    }

    /* Grafik */
    [data-testid="stPlotlyChart"] {
        width: 100% !important;
        overflow-x: auto !important;
    }
}

/* WARNA SEMUA TAB PAKET */
[data-testid="stTabs"] [role="tab"],
[data-testid="stTabs"] [role="tab"] *,
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] * {
    color: #142B4A !important;
    -webkit-text-fill-color: #142B4A !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* TAB AKTIF DAN TIDAK AKTIF */
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="false"] {
    color: #142B4A !important;
    background-color: transparent !important;
}

/* SAAT HOVER */
[data-testid="stTabs"] [role="tab"]:hover,
[data-testid="stTabs"] [role="tab"]:focus {
    color: #142B4A !important;
    -webkit-text-fill-color: #142B4A !important;
}

/* Mengurangi jarak kosong di atas halaman */
[data-testid="stMainBlockContainer"] {
    padding-top: 3rem !important;
}

/* =================================
   TOMBOL ADMIN
================================= */

[data-testid="stPopover"] button,
[data-testid="stPopover"] button *,
[data-testid="stPopover"] button p,
[data-testid="stPopover"] button span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

[data-testid="stPopover"] button {
    background-color: #142B4A !important;
    border: 1px solid #142B4A !important;
    border-radius: 10px !important;
    min-height: 42px !important;
    padding: 10px 18px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}


/* ==========================================
   POP-UP KONFIRMASI HAPUS
   ========================================== */

/* Kotak pesan konfirmasi */
[data-testid="stDialog"] [data-testid="stAlert"],
[role="dialog"] [data-testid="stAlert"] {
    background: #172F50 !important;
    background-color: #172F50 !important;
    border: 1px solid #304766 !important;
    border-left: 4px solid #E5B85C !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}

/* Hilangkan background bawaan elemen bagian dalam */
[data-testid="stDialog"] [data-testid="stAlert"] > div,
[role="dialog"] [data-testid="stAlert"] > div {
    background: transparent !important;
    background-color: transparent !important;
}

/* Semua teks pesan */
[data-testid="stDialog"] [data-testid="stAlert"],
[data-testid="stDialog"] [data-testid="stAlert"] *,
[role="dialog"] [data-testid="stAlert"],
[role="dialog"] [data-testid="stAlert"] * {
    color: #FFFFFF !important;
}

/* Ikon pesan */
[data-testid="stDialog"] [data-testid="stAlert"] svg,
[role="dialog"] [data-testid="stAlert"] svg {
    color: #E5B85C !important;
    fill: #E5B85C !important;
}

/* Checkbox konfirmasi */
[data-testid="stDialog"] [data-testid="stCheckbox"] label,
[data-testid="stDialog"] [data-testid="stCheckbox"] label *,
[role="dialog"] [data-testid="stCheckbox"] label,
[role="dialog"] [data-testid="stCheckbox"] label * {
    color: #FFFFFF !important;
}

/* KOTAK PERLU VERIFIKASI */
.st-key-kotak_perlu_verifikasi {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-left: 5px solid #E5B85C !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    margin-top: 8px !important;
    margin-bottom: 12px !important;
    box-shadow: 0px 3px 12px rgba(20,43,74,0.04) !important;
}

/* KOTAK PEMBUNGKUS SELURUH CONTENT HALAMAN */
[class*="st-key-content-"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 16px !important;
    padding: 25px !important;
    margin-top: 15px !important;
    margin-bottom: 25px !important;
    box-shadow: 0 3px 12px rgba(20,43,74,0.05) !important;
}

/* KARTU DASHBOARD ADMIN */
[class*="st-key-metric-card-"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0px 3px 12px rgba(20,43,74,0.04) !important;
    min-height: 110px !important;
    box-sizing: border-box !important;
}

/* RESPONSIVE KARTU DASHBOARD */
@media screen and (max-width: 768px) {
    [class*="st-key-metric-card-"] {
        padding: 14px !important;
        min-height: 110px !important;
    }
}
/* ======================================
   KARTU PAKET & HARGA
====================================== */

[class*="st-key-paket-card-"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    margin-bottom: 4px !important;
    box-shadow: 0 2px 8px rgba(20,43,74,0.04) !important;
}

/* Jarak antar elemen dalam kartu */
[class*="st-key-paket-card-"] [data-testid="stVerticalBlock"] {
    gap: 7px !important;
}

/* Judul paket */
.paket-card-title {
    color: #142B4A;
    font-size: 19px;
    font-weight: 700;
    margin: 0 0 8px 0;
}

/* Informasi paket */
.paket-card-info {
    color: #475569;
    font-size: 13px;
    margin: 3px 0;
    line-height: 1.5;
}

/* Keterangan */
.paket-card-label {
    color: #142B4A;
    font-size: 13px;
    font-weight: 600;
    margin: 7px 0 3px 0;
}

.paket-card-description {
    color: #64748B;
    font-size: 12px;
    line-height: 1.5;
    margin: 0;
}

/* Tombol daftar dalam kartu */
[class*="st-key-paket-card-"] .stButton {
    margin-top: 5px;
}


[data-testid="stPopover"] button:hover {
    background-color: #1D3B60 !important;
    border-color: #1D3B60 !important;
}

</style>
""", unsafe_allow_html=True)

# MEMBACA DATABASE EXCEL DARI GOOGLE DRIVE
@st.cache_data(ttl=10)
def load_database():
    download_database()

    sheets = pd.read_excel(
        DB_PATH,
        sheet_name=None,
        engine="openpyxl"
    )

    return sheets


data = load_database()


def get_data(sheet):
    return data.get(sheet, pd.DataFrame())


murid = get_data("murid")
tutor = get_data("tutor")
paket = get_data("paket")
absensi = get_data("absensi_murid")
absensi_tutor = get_data("absensi_tutor")
def get_data(sheet):
    return data.get(sheet, pd.DataFrame())

murid = get_data("murid")
tutor = get_data("tutor")
paket = get_data("paket")
absensi = get_data("absensi_murid")
absensi_tutor = get_data("absensi_tutor")

# NAVBAR DAN AKSES MENU
if not st.session_state.admin_login and not st.session_state.tutor_login:

    # NAVBAR PENGUNJUNG
    with st.container(key="top_navbar"):

      kiri, tengah, kanan = st.columns([2, 7, 2], vertical_alignment="center")

    with kiri:
        with open("logo.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; align-items:center;">
                <img src="data:image/png;base64,{logo_base64}"
                     style="width:80px; height:80px; object-fit:contain;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with tengah:
        st.write("")

    with kanan:
        with st.popover("Login", use_container_width=True):
            if st.button("Login sebagai Admin", use_container_width=True):
                st.session_state.menu_aktif = "Login Admin"
                st.rerun()

            if st.button("Login sebagai Tutor", use_container_width=True):
                st.session_state.menu_aktif = "Login Tutor"
                st.rerun()

    # LOGIN ADMIN


    if st.session_state.menu_aktif == "Login Admin":


        st.markdown("<h2 style='text-align:center;'>Login Admin</h2>",
                    unsafe_allow_html=True)

        with st.form("form_login_admin"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login = st.form_submit_button("Masuk", use_container_width=True)

            if login:
                if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state.admin_login = True
                    st.session_state.menu_aktif = "Dashboard"
                    st.rerun()
                else:
                    st.error("Username atau password salah.")


    # LOGIN TUTOR
    if st.session_state.menu_aktif == "Login Tutor":

        st.markdown(
            "<h2 style='text-align:center;'>Login Tutor</h2>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<p style='text-align:center;color:#718096;'>"
            "Masuk menggunakan akun tutor yang telah terdaftar."
            "</p>",
            unsafe_allow_html=True
        )

        with st.form("form_login_tutor"):

            username_tutor = st.text_input(
                "Username",
                key="username_login_tutor"
            )

            password_tutor = st.text_input(
                "Password",
                type="password",
                key="password_login_tutor"
            )

            login_tutor = st.form_submit_button(
                "Masuk",
                use_container_width=True
            )

            if login_tutor:

                if not username_tutor.strip() or not password_tutor.strip():
                    st.error("Username dan password wajib diisi.")

                elif tutor.empty:
                    st.error("Data tutor belum tersedia.")

                elif not all(
                    kolom in tutor.columns
                    for kolom in [
                        "tutor_id",
                        "nama_lengkap",
                        "username",
                        "password",
                        "tanggal_selesai"
                    ]
                ):
                    st.error("Kolom akun login tutor belum lengkap di database.")

                else:

                    data_login = tutor[
                        (tutor["username"].fillna("").astype(str).str.strip()
                         == username_tutor.strip())
                        &
                        (tutor["password"].fillna("").astype(str).str.strip()
                         == password_tutor.strip())
                    ]

                    if data_login.empty:
                        st.error("Username atau password salah.")

                    else:
                        akun = data_login.iloc[0]

                        tanggal_selesai = akun["tanggal_selesai"]

                        if (
                            pd.notna(tanggal_selesai)
                            and str(tanggal_selesai).strip() != ""
                        ):
                            st.error(
                                "Akun tutor sudah nonaktif. Silakan hubungi Admin."
                            )

                        else:
                            st.session_state.tutor_login = True
                            st.session_state.tutor_id_login = str(akun["tutor_id"])
                            st.session_state.tutor_nama_login = str(akun["nama_lengkap"])

                            st.session_state.menu_aktif = "Dashboard Tutor"

                            st.rerun()

    menu = st.session_state.menu_aktif

elif st.session_state.tutor_login:

    # NAVBAR TUTOR
    kiri, tengah, kanan = st.columns(
        [1, 6, 1],
        vertical_alignment="center"
    )

    # LOGO KIRI
    with kiri:
        with open("logo.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; align-items:center;">
                <img src="data:image/png;base64,{logo_base64}"
                     style="width:80px; height:80px; object-fit:contain;">
            </div>
            """,
            unsafe_allow_html=True
        )

    # BAGIAN TENGAH DIKOSONGKAN
    with tengah:
        st.write("")

    # PROFIL TUTOR DI KANAN
    with kanan:
        with st.popover("👤 Tutor"):
            st.write(st.session_state.tutor_nama_login)

            if st.button("Keluar", key="keluar_tutor"):
                st.session_state.tutor_login = False
                st.session_state.tutor_id_login = None
                st.session_state.tutor_nama_login = None
                st.session_state.menu_aktif = "Beranda"
                st.session_state.menu_terbuka = False
                st.rerun()
else:

    # NAVBAR ADMIN
    kiri, tengah, kanan = st.columns([1, 6, 1])

    with kiri:
        if st.button("☰", key="menu_admin"):
            st.session_state.menu_terbuka = not st.session_state.menu_terbuka

    with tengah:
        with open("logo.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; align-items:center;">
                <img src="data:image/png;base64,{logo_base64}"
                    style="width:80px; height:80px; object-fit:contain;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with kanan:
        with st.popover("👤 Admin"):
            st.write("Administrator")
            if st.button("Keluar", use_container_width=True):
                st.session_state.admin_login = False
                st.session_state.menu_aktif = "Beranda"
                st.session_state.menu_terbuka = False
                st.rerun()
# ======================================
# SIDEBAR ADMIN RESPONSIVE
# ======================================

posisi_menu = (
    "translateX(0)"
    if st.session_state.menu_terbuka
    else "translateX(-110%)"
)

st.markdown(
    f"""
    <style>

    /* PANEL SIDEBAR */
    .st-key-admin_drawer {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 270px !important;
        max-width: 85vw !important;
        height: 100vh !important;
        height: 100dvh !important;
        z-index: 999999 !important;
        background: #142B4A !important;
        padding: 12px 13px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        box-shadow: 5px 0 20px rgba(0,0,0,0.18) !important;
        border-right: 1px solid #294667 !important;
        box-sizing: border-box !important;
        transform: {posisi_menu} !important;
        transition: transform 0.3s ease-in-out !important;
    }}

    /* JARAK ANTARMENU */
    .st-key-admin_drawer [data-testid="stVerticalBlock"] {{
        gap: 5px !important;
    }}

    /* JUDUL KELOMPOK */
    .st-key-admin_drawer [data-testid="stMarkdownContainer"] p {{
        color: #AFC1D8 !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.6px !important;
        margin: 7px 0 4px 3px !important;
    }}

    /* TOMBOL MENU */
    .st-key-admin_drawer .stButton > button {{
        background: #1C385B !important;
        color: #FFFFFF !important;
        border: 1px solid #294667 !important;
        border-radius: 7px !important;
        min-height: 41px !important;
        height: 41px !important;
        padding: 5px 10px !important;
        margin: 0 !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        text-align: left !important;
        box-shadow: none !important;
    }}

    .st-key-admin_drawer .stButton > button p {{
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }}

    .st-key-admin_drawer .stButton > button:hover {{
        background: #34577E !important;
        border-color: #6D8DB2 !important;
    }}

    /* TOMBOL TUTUP */
    .st-key-admin_drawer .st-key-tutup_menu_admin button {{
        background: #294667 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 7px !important;
        width: 29px !important;
        min-width: 29px !important;
        height: 29px !important;
        min-height: 29px !important;
        padding: 0 !important;
        font-size: 20px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* GARIS PEMISAH */
    .st-key-admin_drawer hr {{
        border-color: rgba(255,255,255,0.15) !important;
        margin: 5px 0 !important;
    }}

    /* TAMPILAN HP */
    @media (max-width: 768px) {{

        .st-key-admin_drawer {{
            width: 245px !important;
            max-width: 82vw !important;
            padding: 9px 10px !important;
        }}

        .st-key-admin_drawer [data-testid="stVerticalBlock"] {{
            gap: 3px !important;
        }}

        .st-key-admin_drawer .stButton > button {{
            min-height: 36px !important;
            height: 36px !important;
            padding: 4px 8px !important;
            font-size: 14px !important;
        }}

        .st-key-admin_drawer .stButton > button p {{
            font-size: 14px !important;
        }}

        .st-key-admin_drawer [data-testid="stMarkdownContainer"] p {{
            font-size: 11px !important;
            margin: 5px 0 3px 3px !important;
        }}

        .st-key-admin_drawer hr {{
            margin: 3px 0 !important;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# ======================================
# PANEL MENU ADMIN
# ======================================
with st.container(key="admin_drawer"):

    # ======================================
    # HEADER DAN TOMBOL TUTUP
    # ======================================
    col1, col2 = st.columns([5, 1])

    with col2:
        if st.button(
            "×",
            key="tutup_menu_admin",
            help="Tutup menu"
        ):
            st.session_state.menu_terbuka = False
            st.rerun()

    # ======================================
    # DASHBOARD
    # ======================================
    if st.button(
        "⌂   Dashboard",
        key="admin_Dashboard",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Dashboard"
        st.session_state.menu_terbuka = False
        st.rerun()

    # ======================================
    # MANAJEMEN MURID
    # ======================================
    st.markdown("MANAJEMEN MURID")

    if st.button(
        "Verifikasi Pendaftaran",
        key="admin_Verifikasi_Pendaftaran",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Verifikasi Pendaftaran"
        st.session_state.menu_terbuka = False
        st.rerun()

    if st.button(
        "Data Murid",
        key="admin_Daftar_Murid",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Daftar Murid"
        st.session_state.menu_terbuka = False
        st.rerun()

    if st.button(
        "Pendaftaran",
        key="admin_Pendaftaran",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Pendaftaran"
        st.session_state.menu_terbuka = False
        st.rerun()

    # ======================================
    # MANAJEMEN TUTOR
    # ======================================
    st.markdown("MANAJEMEN TUTOR")

    if st.button(
        "Pendaftaran Tutor",
        key="admin_Pendaftaran_Tutor",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Pendaftaran Tutor"
        st.session_state.menu_terbuka = False
        st.rerun()

    if st.button(
        "Data Tutor",
        key="admin_Data_Tutor",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Data Tutor"
        st.session_state.menu_terbuka = False
        st.rerun()

    # ======================================
    # MANAJEMEN PEMBELAJARAN
    # ======================================
    st.markdown("MANAJEMEN PEMBELAJARAN")

    if st.button(
        "Paket Belajar",
        key="admin_Paket_Belajar",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Paket Belajar"
        st.session_state.menu_terbuka = False
        st.rerun()

    # ======================================
    # ABSENSI
    # ======================================
    st.markdown("ABSENSI")

    if st.button(
        "Absensi Murid",
        key="admin_Absensi_Murid",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Absensi Murid"
        st.session_state.menu_terbuka = False
        st.rerun()

    if st.button(
        "Absensi Tutor",
        key="admin_Absensi_Tutor",
        use_container_width=True
    ):
        st.session_state.menu_aktif = "Absensi Tutor"
        st.session_state.menu_terbuka = False
        st.rerun()


# ======================================
# MENU AKTIF
# ======================================
menu = st.session_state.menu_aktif

# ======================================
# HALAMAN PUBLIK
# ======================================
if menu == "Beranda":

    st.markdown(
        "<h2 style='text-align:center;color:#142B4A;'>"
        "Selamat Datang</h2>",
        unsafe_allow_html=True
    )

    # ======================================
    # POSTER LANDSCAPE FULL WIDTH
    # ======================================
    st.image(
        "poster.png",
        use_container_width=True
    )

    # ======================================
    # TOMBOL PAKET BELAJAR
    # ======================================
    if st.button(
        "Lihat Paket Belajar",
        use_container_width=True
    ):
        st.session_state.menu_sebelumnya = "Beranda"
        st.session_state.menu_aktif = "Paket & Harga"
        st.rerun()

# ======================================
# PAKET & HARGA (HALAMAN PUBLIK)
# ======================================
elif menu == "Paket & Harga":

    # ======================================
    # TOMBOL KEMBALI
    # ======================================
    if st.button("← Kembali", key="back_paket"):
        st.session_state.menu_aktif = (
            st.session_state.menu_sebelumnya or "Beranda"
        )
        st.session_state.menu_sebelumnya = None
        st.rerun()

    # ======================================
    # JUDUL HALAMAN
    # ======================================
    st.markdown(
        "<h2 style='text-align:center;color:#142B4A;'>"
        "Paket Belajar</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#718096;'>"
        "Pilih paket belajar sesuai kebutuhanmu."
        "</p>",
        unsafe_allow_html=True
    )

    # ======================================
    # STYLE TOMBOL WHATSAPP
    # ======================================
    st.markdown(
        """
        <style>
        div.stLinkButton a {
            background-color: #25D366 !important;
            color: white !important;
            border: 1px solid #25D366 !important;
            font-weight: 600 !important;
        }

        div.stLinkButton a:hover,
        div.stLinkButton a:active,
        div.stLinkButton a:focus,
        div.stLinkButton a:focus-visible {
            background-color: #25D366 !important;
            color: white !important;
            border-color: #25D366 !important;
            box-shadow: none !important;
            outline: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ======================================
    # TOMBOL KONSULTASI WHATSAPP
    # ======================================
    st.markdown(
        "<p style='text-align:center;color:#718096;'>"
        "Masih bingung memilih paket belajar? "
        "Hubungi admin untuk konsultasi."
        "</p>",
        unsafe_allow_html=True
    )

    _, kolom_wa, _ = st.columns([1, 2, 1])

    with kolom_wa:
        st.link_button(
            "💬 Hubungi Admin via WhatsApp",
            "https://wa.me/6285798442580?text=Halo%20Admin%20Assisten%20Belajar%2C%20saya%20ingin%20konsultasi%20mengenai%20paket%20belajar.",
            use_container_width=True
        )

    st.markdown("---")

    # ======================================
    # AMBIL DATA PAKET DARI DATABASE
    # ======================================
    paket = get_data("paket")

    if not paket.empty and "status" in paket.columns:

        # HANYA MENAMPILKAN PAKET AKTIF
        paket_aktif = paket[
            paket["status"].astype(str).str.strip().str.lower() == "aktif"
        ].copy()

        if not paket_aktif.empty:

            kolom = st.columns(3, gap="small")

            for index, (_, item) in enumerate(
                paket_aktif.iterrows()
            ):

                with kolom[index % 3]:

                    # Ambil data paket
                    nama_paket = str(
                        item.get("nama_paket", "Paket Belajar")
                    )

                    durasi_raw = pd.to_numeric(
                        item.get("durasi_menit"),
                        errors="coerce"
                    )

                    durasi = (
                        f"{int(durasi_raw)} Menit"
                        if pd.notna(durasi_raw)
                        else "-"
                    )

                    jenis_raw = item.get("jenis_paket", "-")

                    jenis_kelas = (
                        "-"
                        if pd.isna(jenis_raw)
                        or str(jenis_raw).strip() == ""
                        else str(jenis_raw)
                    )

                    deskripsi_raw = item.get("deskripsi", "-")

                    deskripsi = (
                        "-"
                        if pd.isna(deskripsi_raw)
                        or str(deskripsi_raw).strip() == ""
                        else str(deskripsi_raw)
                    )

                    from html import escape

                    # KARTU PAKET
                    with st.container(
                        key=f"paket-card-{item.get('paket_id')}"
                    ):

                        st.markdown(
                            f"""
                            <div style="text-align:center;">
                                <div style="font-size:27px;">📚</div>
                                <div class="paket-card-title">
                                    {escape(nama_paket)}
                                </div>
                            </div>

                            <div class="paket-card-info">
                                ⏱️ <b>Durasi:</b> {escape(durasi)}
                            </div>

                            <div class="paket-card-info">
                                👥 <b>Jenis Paket:</b> {escape(jenis_kelas)}
                            </div>

                            <div class="paket-card-label">
                                📝 Keterangan Paket
                            </div>

                            <div class="paket-card-description">
                                {escape(deskripsi)}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        if st.button(
                            "Daftar Paket Ini →",
                            key=f"daftar_publik_{item.get('paket_id')}",
                            use_container_width=True
                        ):

                            st.session_state.paket_pilihan = str(
                                item.get("paket_id")
                            )

                            st.session_state.menu_aktif = "Pendaftaran"
                            st.rerun()

        else:

            st.info(
                "Belum ada paket belajar yang tersedia."
            )

    else:

        st.info(
            "Belum ada paket belajar."
        )



# ======================================
# DASHBOARD TUTOR
# ======================================
elif menu == "Dashboard Tutor":

    if not st.session_state.tutor_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    st.markdown(
        '<div class="main-title">Dashboard Tutor</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="subtitle">
            Selamat datang, {st.session_state.tutor_nama_login}.
            Silakan pilih menu untuk mengelola kegiatan belajar.
        </div>
        """,
        unsafe_allow_html=True
    )

    # JARAK ANTARA SAMBUTAN DAN KARTU MENU
    st.markdown(
        "<div style='height:25px;'></div>",
        unsafe_allow_html=True
    )

    # KARTU MENU TUTOR
    kolom1, kolom2 = st.columns(2, gap="large")

    with kolom1:
        with st.container(border=True):
            st.markdown("### 📚 Absensi Murid")
            st.write(
                "Melihat dan mengelola kehadiran murid "
                "yang menjadi tanggung jawabmu."
            )

            if st.button(
                "Buka Absensi Murid →",
                key="btn_absensi_murid_tutor",
                use_container_width=True
            ):
                st.session_state.menu_aktif = "Absensi Murid"
                st.rerun()

    with kolom2:
        with st.container(border=True):
            st.markdown("### 🗓️ Absensi Tutor")
            st.write(
                "Melihat dan mengelola data kehadiranmu sendiri."
            )

            if st.button(
                "Buka Absensi Tutor →",
                key="btn_absensi_tutor_tutor",
                use_container_width=True
            ):
                st.session_state.menu_aktif = "Absensi Tutor"
                st.rerun()

# ======================================
# DASHBOARD ADMIN
# ======================================
elif menu == "Dashboard":

    # JUDUL DASHBOARD
    st.markdown(
        '<h2 style="color:#142B4A; text-align:center; '
        'margin-top:-35px; margin-bottom:5px; padding-top:0px;">'
        'Dashboard Admin</h2>',
        unsafe_allow_html=True
    )

    # DESKRIPSI DASHBOARD
    st.markdown(
        '<p style="color:#718096; text-align:center; '
        'margin-top:-20px; margin-bottom:20px;">'
        'Ringkasan data administrasi Bimbingan Belajar Assisten Belajar.'
        '</p>',
        unsafe_allow_html=True
    )

    # ======================================
    # MEMBACA DATA PENDAFTARAN
    # ======================================
    data_pendaftaran = load_database().get(
        "pendaftaran_murid",
        pd.DataFrame()
    )

    # ======================================
    # MENGHITUNG PENDAFTARAN MENUNGGU
    # ======================================
    if not data_pendaftaran.empty:

        if "status_pendaftaran" not in data_pendaftaran.columns:
            data_pendaftaran["status_pendaftaran"] = "Menunggu"

        data_pendaftaran["status_pendaftaran"] = (
            data_pendaftaran["status_pendaftaran"]
            .fillna("Menunggu")
            .astype(str)
            .str.strip()
        )

        tampil_pendaftaran = data_pendaftaran[
            data_pendaftaran["status_pendaftaran"].str.lower() == "menunggu"
        ].copy()

        total_menunggu = len(tampil_pendaftaran)

    else:
        tampil_pendaftaran = pd.DataFrame()
        total_menunggu = 0

    # ======================================
    # MENGHITUNG TOTAL DATA MURID
    # ======================================
    if not murid.empty and "murid_id" in murid.columns:
        total_murid = murid["murid_id"].dropna().nunique()
    else:
        total_murid = 0

    # ======================================
    # MENGHITUNG TOTAL DATA TUTOR
    # ======================================
    if not tutor.empty and "tutor_id" in tutor.columns:
        total_tutor = tutor["tutor_id"].dropna().nunique()
    else:
        total_tutor = 0

    # ======================================
    # FUNGSI KARTU DASHBOARD
    # ======================================
    def kartu_dashboard(
        judul,
        total,
        deskripsi,
        warna,
        menu_tujuan,
        key
    ):

        with st.container(key=f"metric-card-{key}"):

            kolom_info, kolom_tombol = st.columns(
                [5, 1.5],
                vertical_alignment="center"
            )

            with kolom_info:

                # HTML DIBUAT SATU BARIS AGAR TIDAK TERBACA
                # SEBAGAI BLOK KODE MARKDOWN
                st.markdown(
                    f'<div style="border-left:5px solid {warna}; padding-left:15px;">'
                    f'<div style="font-size:14px; color:#718096; margin-bottom:5px;">'
                    f'{judul}</div>'
                    f'<div style="font-size:30px; font-weight:700; color:#17375E; '
                    f'line-height:1.3; margin-bottom:4px;">{total}</div>'
                    f'<div style="font-size:12px; color:#718096;">'
                    f'{deskripsi}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            with kolom_tombol:

                if st.button(
                    "Lihat Detail →",
                    key=key,
                    use_container_width=True
                ):
                    st.session_state.menu_aktif = menu_tujuan
                    st.session_state.menu_terbuka = False
                    st.rerun()

    # ======================================
    # KARTU 1: MENUNGGU VERIFIKASI
    # ======================================
    kartu_dashboard(
        judul="📋 Total Murid Menunggu Verifikasi",
        total=total_menunggu,
        deskripsi="Jumlah pendaftar yang belum diverifikasi.",
        warna="#E5B85C",
        menu_tujuan="Verifikasi Pendaftaran",
        key="btn_verifikasi_pendaftaran"
    )

    # ======================================
    # KARTU 2: TOTAL DATA MURID
    # ======================================
    kartu_dashboard(
        judul="👨‍🎓 Total Data Murid",
        total=total_murid,
        deskripsi="Jumlah seluruh data murid yang tersimpan.",
        warna="#4A90A4",
        menu_tujuan="Daftar Murid",
        key="btn_data_murid"
    )

    # ======================================
    # KARTU 3: TOTAL DATA TUTOR
    # ======================================
    kartu_dashboard(
        judul="👩‍🏫 Total Data Tutor",
        total=total_tutor,
        deskripsi="Jumlah seluruh data tutor yang tersimpan.",
        warna="#7B8FC4",
        menu_tujuan="Data Tutor",
        key="btn_data_tutor"
    )


# PENDAFTARAN MURID ONLINE
elif menu == "Pendaftaran":

    from openpyxl import load_workbook
    from datetime import datetime

    # TOMBOL KEMBALI
    if st.button("← Kembali", key="kembali_pendaftaran"):

        if st.session_state.admin_login:
            st.session_state.menu_aktif = "Dashboard"

        else:
            st.session_state.menu_aktif = "Beranda"

        st.rerun()


    st.markdown(
        '<div class="main-title">Pendaftaran Murid</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Formulir pendaftaran murid baru Bimbingan Belajar Assisten Belajar</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("Formulir Pendaftaran Online")

    st.markdown("### Identitas Murid")

    with st.form("form_pendaftaran_murid"):

        col1, col2 = st.columns(2)

        with col1:
            nama = st.text_input("Nama Lengkap Murid *")
            nama_panggilan = st.text_input("Nama Panggilan *")
            tempat_lahir = st.text_input("Tempat Lahir")
            tanggal_lahir = st.date_input(
                "Tanggal Lahir",
                value=None,
                min_value=None
            )
            gender = st.selectbox(
                "Jenis Kelamin *",
                ["Pilih", "L", "P"]
            )

        with col2:
            sekolah = st.text_input("Nama Sekolah *")

            kelas = st.selectbox(
                "Kelas *",
                [
                    "Pilih",
                    "TK A", "TK B",
                    "SD 1", "SD 2", "SD 3",
                    "SD 4", "SD 5", "SD 6",
                    "SMP 7", "SMP 8", "SMP 9"
                ]
            )

            kebutuhan = st.selectbox(
                "Kebutuhan Belajar *",
                [
                    "Pilih",
                    "Calistung",
                    "Semua Mata Pelajaran",
                    "Matematika",
                    "Bahasa Inggris"
                ]
            )

        st.markdown("---")
        st.markdown("### Identitas Orang Tua")

        col3, col4 = st.columns(2)

        with col3:
            nama_ayah = st.text_input("Nama Ayah *")
            pekerjaan_ayah = st.text_input("Pekerjaan Ayah")

        with col4:
            nama_ibu = st.text_input("Nama Ibu *")
            pekerjaan_ibu = st.text_input("Pekerjaan Ibu")

        whatsapp = st.text_input(
            "Nomor WhatsApp Orang Tua *",
            placeholder="Contoh: 081234567890"
        )

        alamat = st.text_area("Alamat Lengkap")

        st.markdown("---")
        st.markdown("### Pilihan Paket Belajar")

        # Mengambil paket yang aktif
        if not paket.empty and "status" in paket.columns:
            paket_aktif = paket[
                paket["status"].astype(str).str.lower() == "aktif"
            ]
        else:
            paket_aktif = pd.DataFrame()

        if not paket_aktif.empty:

            daftar_paket = paket_aktif["paket_id"].astype(str).tolist()

            def format_paket(paket_id):
                baris = paket_aktif[
                    paket_aktif["paket_id"].astype(str) == paket_id
                ].iloc[0]

                harga = pd.to_numeric(
                    baris.get("harga", 0),
                    errors="coerce"
                )

                harga = 0 if pd.isna(harga) else harga

                return (
                    f"{baris['nama_paket']} - "
                    f"Rp{harga:,.0f}".replace(",", ".")
                )

            pilihan_paket = st.selectbox(
                "Pilih Paket",
                daftar_paket,
                format_func=format_paket
            )

        else:
            pilihan_paket = ""
            st.warning(
                "Belum ada paket aktif. "
                "Admin perlu menambahkan paket terlebih dahulu."
            )

        st.markdown("### Jadwal Belajar")

        jenis_jadwal = st.radio(
            "Preferensi Hari Belajar",
            ["Setiap Hari", "Hari Tertentu"],
            horizontal=True
        )

        if jenis_jadwal == "Setiap Hari":
            jadwal = "Setiap Hari"
        else:
            hari_dipilih = st.multiselect(
                "Pilih Hari Belajar",
                [
                    "Senin", "Selasa", "Rabu",
                    "Kamis", "Jumat", "Sabtu", "Minggu"
                ]
            )
            jadwal = ", ".join(hari_dipilih)

        catatan = st.text_area(
            "Karakteristik Anak / Catatan Khusus",
            placeholder="Contoh: Anak lebih mudah belajar menggunakan gambar."
        )

        st.markdown("---")

        persetujuan = st.checkbox(
            "Saya menyatakan bahwa data yang diisi sudah benar."
        )

        submit = st.form_submit_button(
            "Kirim Pendaftaran",
            use_container_width=True,
            type="primary"
        )

        if submit:

            if not nama.strip() or not nama_panggilan.strip():
                st.error("Nama lengkap dan nama panggilan wajib diisi.")

            elif gender == "Pilih" or kelas == "Pilih":
                st.error("Silakan pilih jenis kelamin dan kelas.")

            elif kebutuhan == "Pilih":
                st.error("Silakan pilih kebutuhan belajar.")

            elif not sekolah.strip():
                st.error("Nama sekolah wajib diisi.")

            elif not nama_ayah.strip() or not nama_ibu.strip():
                st.error("Nama ayah dan ibu wajib diisi.")

            elif not whatsapp.strip():
                st.error("Nomor WhatsApp wajib diisi.")

            elif not persetujuan:
                st.error("Silakan centang persetujuan data.")

            elif jenis_jadwal == "Hari Tertentu" and not jadwal:
                st.error("Silakan pilih minimal satu hari belajar.")

            else:

                try:

                    # Membuka database Excel
                    download_database()
                    wb = load_workbook(DB_PATH)
                    ws = wb["pendaftaran_murid"]

                    headers = [
                        cell.value for cell in ws[1]
                    ]

                    # ID otomatis berdasarkan ID terakhir
                    nomor_terbesar = 0

                    for row in ws.iter_rows(
                        min_row=2,
                        values_only=True
                    ):
                        nilai = row[0]

                        if nilai and str(nilai).startswith("REG"):
                            try:
                                nomor = int(str(nilai)[3:])
                                nomor_terbesar = max(
                                    nomor_terbesar, nomor
                                )
                            except ValueError:
                                pass

                    pendaftaran_id = (
                        f"REG{nomor_terbesar + 1:04d}"
                    )

                    data_baru = {
                        "pendaftaran_id": pendaftaran_id,
                        "tanggal_daftar": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "nama_lengkap": nama.strip(),
                        "nama_panggilan": nama_panggilan.strip(),
                        "tempat_lahir": tempat_lahir.strip(),
                        "tanggal_lahir": (
                            tanggal_lahir.strftime("%Y-%m-%d")
                            if tanggal_lahir else ""
                        ),
                        "gender": gender,
                        "sekolah": sekolah.strip(),
                        "kelas": kelas,
                        "nama_ayah": nama_ayah.strip(),
                        "nama_ibu": nama_ibu.strip(),
                        "pekerjaan_ayah": pekerjaan_ayah.strip(),
                        "pekerjaan_ibu": pekerjaan_ibu.strip(),
                        "no_whatsapp_orang_tua": whatsapp.strip(),
                        "alamat": alamat.strip(),
                        "kebutuhan_belajar": kebutuhan,
                        "paket_id": pilihan_paket,
                        "jadwal_preferensi": jadwal,
                        "catatan_khusus": catatan.strip(),
                        "status_pendaftaran": "Menunggu",
                        "catatan_admin": ""
                    }

                    ws.append([
                        data_baru.get(kolom, "")
                        for kolom in headers
                    ])

                    wb.save(DB_PATH)
                    wb.close()
                    upload_database()

                    st.cache_data.clear()

                    st.success(
                        "Pendaftaran berhasil dikirim!"
                    )

                    st.info(
                        f"Nomor pendaftaran kamu: {pendaftaran_id}. "
                        "Silakan tunggu konfirmasi dari admin Assisten Belajar."
                    )

                except Exception as e:
                    st.error(
                        f"Gagal menyimpan pendaftaran: {e}"
                    )


# DAFTAR MURID (ADMIN)
elif menu == "Daftar Murid":

    from openpyxl import load_workbook
    from datetime import date

    # TOMBOL KEMBALI
    if st.button("← Kembali", key="kembali_verifikasi"):
        st.session_state.menu_aktif = "Dashboard"
        st.rerun()

    if not st.session_state.admin_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    st.markdown(
        '<div class="main-title">Daftar Murid</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Informasi seluruh murid Bimbingan Belajar Assisten Belajar.</div>',
        unsafe_allow_html=True
    )

    # AMBIL DATA MURID
    data_murid = load_database().get(
        "murid",
        pd.DataFrame()
    )

    # ======================================
    # RINGKASAN DATA MURID
    # ======================================

    total_murid = len(data_murid)

    if not data_murid.empty and "status" in data_murid.columns:

        murid_aktif = (
            data_murid["status"].astype(str).str.lower() == "aktif"
        ).sum()

        murid_nonaktif = total_murid - murid_aktif

    else:
        murid_aktif = 0
        murid_nonaktif = 0

    col1, col2, col3 = st.columns(3)

    metrics = [
        (col1, "Total Murid", total_murid),
        (col2, "Murid Aktif", murid_aktif),
        (col3, "Murid Nonaktif", murid_nonaktif)
    ]

    for col, label, nilai in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{nilai}</div>
            </div>
            """, unsafe_allow_html=True)

    # ======================================
    # FUNGSI CRUD MURID
    # ======================================

    def tanggal_murid(nilai):

        hasil = pd.to_datetime(nilai, errors="coerce")

        if pd.isna(hasil):
            return None

        return hasil.date()

    def simpan_murid(perubahan, murid_id=None):
        download_database()
        wb = load_workbook(DB_PATH)
        ws = wb["murid"]

        headers = [
            cell.value for cell in ws[1]
        ]

        posisi = {
            nama: index + 1
            for index, nama in enumerate(headers)
        }

        kolom_wajib = [
            "murid_id",
            "nama_lengkap",
            "status"
        ]

        for kolom in kolom_wajib:
            if kolom not in posisi:
                wb.close()
                raise ValueError(
                    f"Kolom {kolom} tidak ditemukan di database."
                )

        if murid_id is None:

            nomor_terbesar = 0

            for baris in range(2, ws.max_row + 1):

                nilai = ws.cell(
                    baris,
                    posisi["murid_id"]
                ).value

                if nilai and str(nilai).startswith("MUR"):
                    try:
                        nomor_terbesar = max(
                            nomor_terbesar,
                            int(str(nilai)[3:])
                        )
                    except ValueError:
                        pass

            murid_id = f"MUR{nomor_terbesar + 1:04d}"

            perubahan["murid_id"] = murid_id

            ws.append([
                perubahan.get(kolom, "")
                for kolom in headers
            ])

        else:

            ditemukan = False

            for baris in range(2, ws.max_row + 1):

                id_excel = ws.cell(
                    baris,
                    posisi["murid_id"]
                ).value

                if str(id_excel).strip() == str(murid_id).strip():

                    for kolom, nilai in perubahan.items():

                        if kolom in posisi:
                            ws.cell(
                                baris,
                                posisi[kolom]
                            ).value = nilai

                    ditemukan = True
                    break

            if not ditemukan:
                wb.close()
                raise ValueError("Data murid tidak ditemukan.")

        wb.save(DB_PATH)
        wb.close()
        upload_database()

        st.cache_data.clear()

    # ======================================
    # TAB CRUD
    # ======================================

    tab1, tab2, tab3 = st.tabs([
        "Daftar Murid",
        "Tambah Murid",
        "Edit / Hapus Murid"
    ])


    # ======================================
    # TAB 1 - DAFTAR MURID
    # ======================================
    with tab1:

        st.subheader("Data Seluruh Murid")

        if not data_murid.empty:

            kolom1, kolom2 = st.columns(2)

            with kolom1:
                pencarian = st.text_input(
                    "Cari Nama Murid",
                    placeholder="Masukkan nama murid..."
                )

            with kolom2:
                pilihan_status = st.selectbox(
                    "Filter Status",
                    ["Semua", "Aktif", "Nonaktif"]
                )

            hasil = data_murid.copy()

            if pencarian:
                hasil = hasil[
                    hasil["nama_lengkap"].astype(str)
                    .str.contains(
                        pencarian,
                        case=False,
                        na=False
                    )
                ]

            if pilihan_status != "Semua":
                hasil = hasil[
                    hasil["status"].astype(str).str.lower()
                    == pilihan_status.lower()
                ]

            # ======================================
            # TABEL DATA MURID
            # ======================================
            kolom_tampil = [
                kolom for kolom in [
                    "nama_panggilan",
                    "sekolah",
                    "tanggal_masuk",
                    "status"
                ]
                if kolom in hasil.columns
            ]

            st.dataframe(
                hasil[kolom_tampil],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Menampilkan {len(hasil)} data murid."
            )

            # ======================================
            # DETAIL MURID
            # ======================================
            st.markdown("---")
            st.subheader("Detail Murid")

            if not hasil.empty:

                pilihan_murid = st.selectbox(
                    "Pilih Murid",
                    hasil["murid_id"].astype(str).tolist(),
                    format_func=lambda x: str(
                        hasil.loc[
                            hasil["murid_id"].astype(str) == x,
                            "nama_lengkap"
                        ].iloc[0]
                    )
                )

                detail = hasil[
                    hasil["murid_id"].astype(str) == pilihan_murid
                ].iloc[0]

                # Ambil data paket dari database
                data_paket = get_data("paket")

                # Tampilkan semua kolom kecuali parent_id
                for kolom, nilai in detail.items():

                    if kolom == "parent_id":
                        continue

                    # Ubah paket_id menjadi nama_paket
                    if kolom == "paket_id":

                        nama_paket = "-"

                        if (
                            not data_paket.empty
                            and "paket_id" in data_paket.columns
                            and "nama_paket" in data_paket.columns
                            and pd.notna(nilai)
                        ):
                            hasil_paket = data_paket.loc[
                                data_paket["paket_id"].astype(str).str.strip()
                                == str(nilai).strip(),
                                "nama_paket"
                            ]

                            if not hasil_paket.empty:
                                nama_paket = hasil_paket.iloc[0]

                        nilai = nama_paket
                        nama_kolom = "Nama Paket"

                    else:
                        nama_kolom = kolom.replace("_", " ").title()

                    if pd.isna(nilai):
                        nilai = "-"

                    st.write(
                        f"**{nama_kolom}:** {nilai}"
                    )

            else:
                st.info(
                    "Tidak ada murid yang sesuai dengan pencarian."
                )

        else:
            st.info("Belum ada data murid.")
    # ======================================
    # TAB 2 - TAMBAH MURID
    # ======================================

    with tab2:

        st.subheader("Tambah Murid Baru")

        with st.form("form_tambah_murid"):

            st.markdown("### Identitas Murid")

            col1, col2 = st.columns(2)

            with col1:

                nama = st.text_input(
                    "Nama Lengkap Murid *"
                )

                panggilan = st.text_input(
                    "Nama Panggilan *"
                )

                tempat = st.text_input(
                    "Tempat Lahir"
                )

                lahir = st.date_input(
                    "Tanggal Lahir",
                    value=None,
                    key="tambah_lahir_murid"
                )

                gender = st.selectbox(
                    "Jenis Kelamin *",
                    ["Pilih", "L", "P"]
                )

            with col2:

                sekolah = st.text_input(
                    "Nama Sekolah *"
                )

                kelas = st.selectbox(
                    "Kelas *",
                    [
                        "Pilih",
                        "TK A", "TK B",
                        "SD 1", "SD 2", "SD 3",
                        "SD 4", "SD 5", "SD 6",
                        "SMP 7", "SMP 8", "SMP 9"
                    ]
                )

                kebutuhan = st.selectbox(
                    "Kebutuhan Belajar *",
                    [
                        "Pilih",
                        "Calistung",
                        "Semua Mata Pelajaran",
                        "Matematika",
                        "Bahasa Inggris"
                    ]
                )

            st.markdown("---")
            st.markdown("### Pilihan Paket Belajar")

            # Ambil paket aktif
            data_paket = load_database().get(
                "paket",
                pd.DataFrame()
            )

            if (
                not data_paket.empty
                and "status" in data_paket.columns
            ):

                paket_aktif = data_paket[
                    data_paket["status"].astype(str).str.lower()
                    == "aktif"
                ]

            else:
                paket_aktif = pd.DataFrame()

            if not paket_aktif.empty:

                daftar_paket = (
                    paket_aktif["paket_id"].astype(str).tolist()
                )

                def format_paket_murid(paket_id):

                    baris = paket_aktif[
                        paket_aktif["paket_id"].astype(str)
                        == paket_id
                    ].iloc[0]

                    harga = pd.to_numeric(
                        baris.get("harga", 0),
                        errors="coerce"
                    )

                    harga = 0 if pd.isna(harga) else harga

                    return (
                        f"{baris['nama_paket']} - "
                        f"Rp{harga:,.0f}".replace(",", ".")
                    )

                pilihan_paket = st.selectbox(
                    "Pilih Paket *",
                    daftar_paket,
                    format_func=format_paket_murid
                )

            else:

                pilihan_paket = ""

                st.warning(
                    "Belum ada paket aktif. "
                    "Admin perlu menambahkan paket terlebih dahulu."
                )

            st.markdown("---")
            st.markdown("### Informasi Tambahan")

            tanggal_masuk = st.date_input(
                "Tanggal Masuk *",
                value=date.today(),
                key="tambah_masuk_murid"
            )

            status = st.selectbox(
                "Status Murid",
                ["Aktif", "Nonaktif"]
            )

            kebutuhan_catatan = st.text_area(
                "Kebutuhan Belajar Tambahan",
                placeholder="Tambahkan penjelasan kebutuhan belajar jika diperlukan."
            )

            catatan = st.text_area(
                "Catatan Khusus",
                placeholder="Contoh: Anak lebih mudah belajar menggunakan gambar."
            )

            st.markdown("---")

            simpan = st.form_submit_button(
                "Simpan Data Murid",
                use_container_width=True,
                type="primary"
            )

            if simpan:

                if not nama.strip() or not panggilan.strip():

                    st.error(
                        "Nama lengkap dan nama panggilan wajib diisi."
                    )

                elif gender == "Pilih":

                    st.error(
                        "Silakan pilih jenis kelamin."
                    )

                elif not sekolah.strip():

                    st.error(
                        "Nama sekolah wajib diisi."
                    )

                elif kelas == "Pilih":

                    st.error(
                        "Silakan pilih kelas."
                    )

                elif kebutuhan == "Pilih":

                    st.error(
                        "Silakan pilih kebutuhan belajar."
                    )

                elif not pilihan_paket:

                    st.error(
                        "Belum ada paket belajar aktif."
                    )

                else:

                    try:

                        simpan_murid({
                            "parent_id": "",
                            "nama_lengkap": nama.strip(),
                            "nama_panggilan": panggilan.strip(),
                            "tempat_lahir": tempat.strip(),
                            "tanggal_lahir": lahir or "",
                            "gender": gender,
                            "sekolah": sekolah.strip(),
                            "kelas": kelas,
                            "kebutuhan_belajar": (
                                kebutuhan
                                + (
                                    " - " + kebutuhan_catatan.strip()
                                    if kebutuhan_catatan.strip()
                                    else ""
                                )
                            ),
                            "paket_id": pilihan_paket,
                            "catatan_khusus": catatan.strip(),
                            "tanggal_masuk": tanggal_masuk,
                            "status": status
                        })

                        st.success(
                            "Data murid berhasil ditambahkan."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Gagal menyimpan data: {e}"
                        )

    # ======================================
    # TAB 3 - EDIT / HAPUS MURID
    # ======================================

    with tab3:

        st.subheader("Edit atau Hapus Murid")

        if (
            not data_murid.empty
            and "murid_id" in data_murid.columns
        ):

            pilihan_id = st.selectbox(
                "Pilih Murid",
                data_murid["murid_id"].astype(str).tolist(),
                format_func=lambda x: str(
                    data_murid.loc[
                        data_murid["murid_id"].astype(str) == x,
                        "nama_lengkap"
                    ].iloc[0]
                ),
                key="pilih_murid_edit"
            )

            item = data_murid[
                data_murid["murid_id"].astype(str) == pilihan_id
            ].iloc[0]

            with st.form("form_edit_murid"):

                col1, col2 = st.columns(2)

                with col1:

                    nama_edit = st.text_input(
                        "Nama Lengkap *",
                        value=str(item.get("nama_lengkap", "") or "")
                    )

                    panggilan_edit = st.text_input(
                        "Nama Panggilan",
                        value=str(item.get("nama_panggilan", "") or "")
                    )

                    tempat_edit = st.text_input(
                        "Tempat Lahir",
                        value=str(item.get("tempat_lahir", "") or "")
                    )

                    lahir_edit = st.date_input(
                        "Tanggal Lahir",
                        value=tanggal_murid(
                            item.get("tanggal_lahir")
                        ),
                        key="edit_lahir_murid"
                    )

                    gender_edit = st.selectbox(
                        "Jenis Kelamin",
                        ["Laki-laki", "Perempuan"],
                        index=(
                            1 if str(item.get("gender", "")).lower()
                            == "perempuan" else 0
                        )
                    )

                with col2:

                    sekolah_edit = st.text_input(
                        "Nama Sekolah",
                        value=str(item.get("sekolah", "") or "")
                    )

                    kelas_edit = st.text_input(
                        "Kelas",
                        value=str(item.get("kelas", "") or "")
                    )

                    paket_edit = st.text_input(
                        "ID Paket Belajar",
                        value=str(item.get("paket_id", "") or "")
                    )

                    masuk_edit = st.date_input(
                        "Tanggal Masuk",
                        value=(
                            tanggal_murid(item.get("tanggal_masuk"))
                            or date.today()
                        ),
                        key="edit_masuk_murid"
                    )

                    status_edit = st.selectbox(
                        "Status Murid",
                        ["Aktif", "Nonaktif"],
                        index=(
                            1 if str(item.get("status", "")).lower()
                            == "nonaktif" else 0
                        )
                    )

                kebutuhan_edit = st.text_area(
                    "Kebutuhan Belajar",
                    value=str(
                        item.get("kebutuhan_belajar", "") or ""
                    )
                )

                catatan_edit = st.text_area(
                    "Catatan Khusus",
                    value=str(
                        item.get("catatan_khusus", "") or ""
                    )
                )

                update = st.form_submit_button(
                    "Simpan Perubahan",
                    use_container_width=True
                )

            if update:

                if not nama_edit.strip():

                    st.error(
                        "Nama lengkap wajib diisi."
                    )

                else:

                    try:

                        simpan_murid({
                            "nama_lengkap": nama_edit.strip(),
                            "nama_panggilan": panggilan_edit.strip(),
                            "tempat_lahir": tempat_edit.strip(),
                            "tanggal_lahir": lahir_edit or "",
                            "gender": gender_edit,
                            "sekolah": sekolah_edit.strip(),
                            "kelas": kelas_edit.strip(),
                            "kebutuhan_belajar": kebutuhan_edit.strip(),
                            "paket_id": paket_edit.strip(),
                            "catatan_khusus": catatan_edit.strip(),
                            "tanggal_masuk": masuk_edit,
                            "status": status_edit
                        }, murid_id=pilihan_id)

                        st.success(
                            "Data murid berhasil diperbarui."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Gagal memperbarui data: {e}"
                        )

            st.markdown("---")
            st.markdown("### Hapus Murid")

            konfirmasi = st.checkbox(
                f"Saya yakin ingin menghapus {item.get('nama_lengkap', pilihan_id)}",
                key="hapus_murid"
            )

            if st.button(
                "Hapus Murid",
                disabled=not konfirmasi,
                use_container_width=True
            ):

                wb = None

                try:
                    download_database()
                    wb = load_workbook(DB_PATH)
                    ws = wb["murid"]

                    headers = [
                        cell.value for cell in ws[1]
                    ]

                    if "murid_id" not in headers:
                        raise ValueError(
                            "Kolom murid_id tidak ditemukan."
                        )

                    kolom_id = headers.index("murid_id") + 1
                    ditemukan = False

                    for baris in range(2, ws.max_row + 1):

                        id_excel = ws.cell(
                            baris,
                            kolom_id
                        ).value

                        if str(id_excel).strip() == pilihan_id.strip():

                            ws.delete_rows(baris, 1)
                            ditemukan = True
                            break

                    if not ditemukan:
                        raise ValueError(
                            "Data murid tidak ditemukan."
                        )

                    wb.save(DB_PATH)
                    wb.close()
                    wb = None
                    upload_database()

                    st.cache_data.clear()

                    st.success(
                        "Data murid berhasil dihapus."
                    )

                    st.rerun()

                except Exception as e:

                    if wb is not None:
                        wb.close()

                    st.error(
                        f"Gagal menghapus murid: {e}"
                    )

        else:

            st.info("Belum ada data murid.")
# ======================================
# PENDAFTARAN TUTOR (ADMIN)
# ======================================
elif menu == "Pendaftaran Tutor":

    from datetime import date

    if not st.session_state.admin_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    if st.button(
        "← Kembali",
        key="kembali_pendaftaran_tutor"
    ):
        st.session_state.menu_aktif = "Dashboard"
        st.rerun()

    st.markdown(
        '<div class="main-title">Pendaftaran Tutor</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Daftarkan calon tutor baru Assisten Belajar.'
        '</div>',
        unsafe_allow_html=True
    )

    # FORM PENDAFTARAN TUTOR
    with st.form("form_pendaftaran_tutor"):

        st.subheader("Formulir Data Calon Tutor")

        col1, col2 = st.columns(2)

        with col1:
            nama = st.text_input("Nama Lengkap *")
            panggilan = st.text_input("Nama Panggilan")
            tempat = st.text_input("Tempat Lahir")
            lahir = st.date_input(
                "Tanggal Lahir",
                value=None
            )

        with col2:
            pendidikan = st.text_input("Pendidikan Terakhir")
            whatsapp = st.text_input("Nomor WhatsApp *")

        alamat = st.text_area("Alamat")

        st.markdown("### Akun Login Tutor")

        col3, col4 = st.columns(2)

        with col3:
            username = st.text_input("Username Login *")

        with col4:
            password = st.text_input("Password Login *")

        st.markdown("### Masa Kerja")

        tanggal_masuk = st.date_input(
            "Tanggal Masuk *",
            value=date.today()
        )

        tanggal_keluar = st.date_input(
            "Tanggal Keluar (Opsional)",
            value=None
        )

        simpan = st.form_submit_button(
            "Daftarkan Tutor",
            use_container_width=True
        )

        if simpan:

            if not nama.strip():
                st.error("Nama lengkap wajib diisi.")

            elif not whatsapp.strip():
                st.error("Nomor WhatsApp wajib diisi.")

            elif not username.strip():
                st.error("Username wajib diisi.")

            elif not password.strip():
                st.error("Password wajib diisi.")

            elif (
                tanggal_keluar is not None
                and tanggal_keluar < tanggal_masuk
            ):
                st.error("Tanggal keluar tidak boleh sebelum tanggal masuk.")

            else:
                try:
                    simpan_tutor({
                        "username": username.strip(),
                        "password": password.strip(),
                        "nama_lengkap": nama.strip(),
                        "nama_panggilan": panggilan.strip(),
                        "tempat_lahir": tempat.strip(),
                        "tanggal_lahir": lahir or "",
                        "pendidikan_terakhir": pendidikan.strip(),
                        "no_whatsapp": whatsapp.strip(),
                        "alamat": alamat.strip(),
                        "tanggal_mulai": tanggal_masuk,
                        "tanggal_selesai": tanggal_keluar or ""
                    })

                    st.success("Pendaftaran tutor berhasil disimpan.")
                    st.cache_data.clear()
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menyimpan pendaftaran: {e}")

# CRUD DATA TUTOR (ADMIN)
elif menu == "Data Tutor":

    from openpyxl import load_workbook
    from datetime import date

    # CEK LOGIN ADMIN
    if not st.session_state.admin_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    # TOMBOL KEMBALI KE DASHBOARD ADMIN
    if st.button("← Kembali", key="kembali_data_tutor"):
        st.session_state.menu_aktif = "Dashboard"
        st.rerun()

    st.markdown(
        '<div class="main-title">Data Tutor</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Kelola informasi tutor Assisten Belajar.</div>',
        unsafe_allow_html=True
    )

    data_tutor = load_database().get("tutor", pd.DataFrame())


    # ======================================
    # RINGKASAN DATA TUTOR
    # ======================================

    total_tutor = len(data_tutor)

    if not data_tutor.empty and "tanggal_selesai" in data_tutor.columns:

        tutor_nonaktif = (
            data_tutor["tanggal_selesai"].notna()
            & (data_tutor["tanggal_selesai"].astype(str).str.strip() != "")
        ).sum()

        tutor_aktif = total_tutor - tutor_nonaktif

    else:
        tutor_aktif = total_tutor
        tutor_nonaktif = 0

    col1, col2, col3 = st.columns(3)

    metrics = [
        (col1, "Total Tutor", total_tutor),
        (col2, "Tutor Aktif", tutor_aktif),
        (col3, "Tutor Nonaktif", tutor_nonaktif)
    ]

    for col, label, nilai in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{nilai}</div>
            </div>
            """, unsafe_allow_html=True)


    def tanggal_tutor(nilai):
        hasil = pd.to_datetime(nilai, errors="coerce")
        return date.today() if pd.isna(hasil) else hasil.date()

    def simpan_tutor(perubahan, tutor_id=None):
        download_database()
        wb = load_workbook(DB_PATH)
        ws = wb["tutor"]
        headers = [cell.value for cell in ws[1]]

        posisi = {
            nama: index + 1
            for index, nama in enumerate(headers)
        }

        if tutor_id is None:

            nomor_terbesar = 0

            for baris in range(2, ws.max_row + 1):
                nilai = ws.cell(
                    baris, posisi["tutor_id"]
                ).value

                if nilai and str(nilai).startswith("TTR"):
                    try:
                        nomor_terbesar = max(
                            nomor_terbesar,
                            int(str(nilai)[3:])
                        )
                    except ValueError:
                        pass

            tutor_id = f"TTR{nomor_terbesar + 1:04d}"
            perubahan["tutor_id"] = tutor_id

            ws.append([
                perubahan.get(kolom, "")
                for kolom in headers
            ])

        else:

            ditemukan = False

            for baris in range(2, ws.max_row + 1):

                if str(
                    ws.cell(baris, posisi["tutor_id"]).value
                ) == str(tutor_id):

                    for kolom, nilai in perubahan.items():
                        if kolom in posisi:
                            ws.cell(
                                baris, posisi[kolom]
                            ).value = nilai

                    ditemukan = True
                    break

            if not ditemukan:
                wb.close()
                raise ValueError("Data tutor tidak ditemukan.")

        wb.save(DB_PATH)
        wb.close()
        upload_database()
        st.cache_data.clear()

    tab1, tab2, tab3 = st.tabs([
        "Daftar Tutor",
        "Tambah Tutor",
        "Edit / Hapus Tutor"
    ])

    # TAB 1 - DAFTAR TUTOR
    with tab1:

        st.subheader("Daftar Seluruh Tutor")

        if not data_tutor.empty:

            pencarian = st.text_input(
                "Cari Nama Tutor",
                placeholder="Masukkan nama tutor..."
            )

            hasil = data_tutor.copy()

            if pencarian:
                hasil = hasil[
                    hasil["nama_lengkap"].astype(str)
                    .str.contains(pencarian, case=False, na=False)
                ]

            kolom = [
                c for c in [
                    "nama_lengkap",
                    "pendidikan_terakhir",
                    "no_whatsapp",
                    "tanggal_mulai",
                    "tanggal_selesai"
                ] if c in hasil.columns
            ]

            st.dataframe(
                hasil[kolom],
                use_container_width=True,
                hide_index=True
            )

            st.caption(f"Total {len(hasil)} tutor.")

            st.markdown("---")
            st.subheader("Detail Tutor")

            pilihan = st.selectbox(
                "Pilih Tutor",
                hasil["tutor_id"].astype(str).tolist(),
                format_func=lambda x: str(
                    hasil.loc[
                        hasil["tutor_id"].astype(str) == x,
                        "nama_lengkap"
                    ].iloc[0]
                )
            )

            detail = hasil[
                hasil["tutor_id"].astype(str) == pilihan
            ].iloc[0]

            for kolom in [
                "nama_lengkap",
                "nama_panggilan",
                "username",
                "password",
                "tempat_lahir",
                "tanggal_lahir",
                "pendidikan_terakhir",
                "no_whatsapp",
                "alamat",
                "tanggal_mulai",
                "tanggal_selesai"
            ]:
                if kolom in detail.index:
                    st.write(
                        f"**{kolom.replace('_', ' ').title()}:** "
                        f"{detail[kolom]}"
                    )

        else:
            st.info("Belum ada data tutor.")

    # TAB 2 - TAMBAH TUTOR
    with tab2:

        st.subheader("Tambah Tutor Baru")

        with st.form("form_tambah_tutor"):

            col1, col2 = st.columns(2)

            with col1:
                nama = st.text_input("Nama Lengkap *")
                panggilan = st.text_input("Nama Panggilan")
                tempat = st.text_input("Tempat Lahir")
                lahir = st.date_input(
                    "Tanggal Lahir",
                    value=None
                )

            with col2:
                pendidikan = st.text_input("Pendidikan Terakhir")
                whatsapp = st.text_input(
                    "Nomor WhatsApp *",
                    placeholder="081234567890"
                )

            alamat = st.text_area("Alamat")

            st.markdown("### Akun Login Tutor")

            col3, col4 = st.columns(2)

            with col3:
                username = st.text_input(
                    "Username Login *",
                    placeholder="Contoh: tutor.andini"
                )

            with col4:
                password = st.text_input(
                    "Password Login *",
                    placeholder="Masukkan password tutor"
                )

            st.markdown("### Masa Kerja")
            tanggal_masuk = st.date_input(
                "Tanggal Masuk *",
                value=date.today()
            )

            tanggal_keluar = st.date_input(
            "Tanggal Keluar (Opsional)",
            value=None,
            key="tambah_keluar_tutor"
        )

            simpan = st.form_submit_button(
                "Simpan Data Tutor",
                use_container_width=True
            )

            if simpan:

                if not nama.strip():
                    st.error("Nama lengkap wajib diisi.")

                elif not whatsapp.strip():
                    st.error("Nomor WhatsApp wajib diisi.")

                elif not username.strip():
                    st.error("Username login wajib diisi.")

                elif not password.strip():
                    st.error("Password login wajib diisi.")

                elif (
                    tanggal_keluar is not None
                    and tanggal_keluar < tanggal_masuk
                ):
                    st.error(
                        "Tanggal keluar tidak boleh sebelum tanggal masuk."
                    )

                else:

                    try:
                        simpan_tutor({
                            "username": username.strip(),
                            "password": password.strip(),
                            "nama_lengkap": nama.strip(),
                            "nama_panggilan": panggilan.strip(),
                            "tempat_lahir": tempat.strip(),
                            "tanggal_lahir": lahir or "",
                            "pendidikan_terakhir": pendidikan.strip(),
                            "no_whatsapp": whatsapp.strip(),
                            "alamat": alamat.strip(),
                            "tanggal_mulai": tanggal_masuk,
                            "tanggal_selesai": tanggal_keluar or ""
                        })

                        st.success("Data tutor berhasil ditambahkan.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Gagal menyimpan data: {e}")

    # TAB 3 - EDIT / HAPUS TUTOR
    with tab3:

        st.subheader("Edit atau Hapus Tutor")

        if (
            not data_tutor.empty
            and "tutor_id" in data_tutor.columns
        ):

            pilihan_id = st.selectbox(
                "Pilih Tutor",
                data_tutor["tutor_id"].astype(str).tolist(),
                format_func=lambda x: str(
                    data_tutor.loc[
                        data_tutor["tutor_id"].astype(str) == x,
                        "nama_lengkap"
                    ].iloc[0]
                ),
                key="pilih_tutor_edit"
            )

            item = data_tutor[
                data_tutor["tutor_id"].astype(str) == pilihan_id
            ].iloc[0]

            with st.form("form_edit_tutor"):

                col1, col2 = st.columns(2)

                with col1:
                    nama_edit = st.text_input(
                        "Nama Lengkap *",
                        value=str(item.get("nama_lengkap", "") or "")
                    )

                    panggilan_edit = st.text_input(
                        "Nama Panggilan",
                        value=str(item.get("nama_panggilan", "") or "")
                    )

                    tempat_edit = st.text_input(
                        "Tempat Lahir",
                        value=str(item.get("tempat_lahir", "") or "")
                    )

                    lahir_lama = item.get("tanggal_lahir")
                    lahir_edit = st.date_input(
                        "Tanggal Lahir",
                        value=tanggal_tutor(lahir_lama),
                        key="edit_lahir_tutor"
                    )

                with col2:
                    pendidikan_edit = st.text_input(
                        "Pendidikan Terakhir",
                        value=str(item.get("pendidikan_terakhir", "") or "")
                    )

                    whatsapp_edit = st.text_input(
                        "Nomor WhatsApp *",
                        value=str(item.get("no_whatsapp", "") or "")
                    )

                alamat_edit = st.text_area(
                    "Alamat",
                    value=str(item.get("alamat", "") or "")
                )

                st.markdown("### Akun Login Tutor")

                username_edit = st.text_input(
                    "Username Login *",
                    value="" if pd.isna(item.get("username")) else str(item.get("username")),
                    key=f"username_edit_tutor_{pilihan_id}"
                )

                password_edit = st.text_input(
                    "Password Login *",
                    value="" if pd.isna(item.get("password")) else str(item.get("password")),
                    key=f"password_edit_tutor_{pilihan_id}"
                )

                masuk_edit = st.date_input(
                    "Tanggal Masuk",
                    value=tanggal_tutor(item.get("tanggal_mulai")),
                    key="edit_masuk_tutor"
                )

                keluar_lama = item.get("tanggal_selesai")

                keluar_edit = st.date_input(
                "Tanggal Keluar (Opsional)",
                value=(
                    pd.to_datetime(keluar_lama).date()
                    if pd.notna(keluar_lama) and str(keluar_lama).strip() != ""
                    else None
                ),
                key="edit_keluar_tutor"
            )

                update = st.form_submit_button(
                    "Simpan Perubahan",
                    use_container_width=True
                )

            if update:

                if not nama_edit.strip():
                    st.error("Nama lengkap wajib diisi.")

                elif not whatsapp_edit.strip():
                    st.error("Nomor WhatsApp wajib diisi.")

                elif not username_edit.strip():
                    st.error("Username login wajib diisi.")

                elif not password_edit.strip():
                    st.error("Password login wajib diisi.")

                elif (
                    keluar_edit is not None
                    and keluar_edit < masuk_edit
                ):
                    st.error(
                        "Tanggal keluar tidak boleh sebelum tanggal masuk."
                    )

                else:

                    try:
                        simpan_tutor({
                            "username": username_edit.strip(),
                            "password": password_edit.strip(),
                            "nama_lengkap": nama_edit.strip(),
                            "nama_panggilan": panggilan_edit.strip(),
                            "tempat_lahir": tempat_edit.strip(),
                            "tanggal_lahir": lahir_edit,
                            "pendidikan_terakhir": pendidikan_edit.strip(),
                            "no_whatsapp": whatsapp_edit.strip(),
                            "alamat": alamat_edit.strip(),
                            "tanggal_mulai": masuk_edit,
                            "tanggal_selesai": keluar_edit or ""
                        }, tutor_id=pilihan_id)

                        st.success("Data tutor berhasil diperbarui.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Gagal memperbarui data: {e}")

            st.markdown("---")
            st.markdown("### Hapus Tutor")

            konfirmasi = st.checkbox(
                f"Saya yakin ingin menghapus {item.get('nama_lengkap', pilihan_id)}",
                key="hapus_tutor"
            )

            if st.button(
                "Hapus Tutor",
                disabled=not konfirmasi,
                use_container_width=True
            ):

                try:
                    download_database()
                    wb = load_workbook(DB_PATH)
                    ws = wb["tutor"]
                    headers = [cell.value for cell in ws[1]]
                    kolom_id = headers.index("tutor_id") + 1

                    for baris in range(2, ws.max_row + 1):
                        if str(
                            ws.cell(baris, kolom_id).value
                        ) == pilihan_id:
                            ws.delete_rows(baris, 1)
                            break

                    wb.save(DB_PATH)
                    wb.close()
                    upload_database()
                    st.cache_data.clear()

                    st.success("Data tutor berhasil dihapus.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menghapus tutor: {e}")

        else:
            st.info("Belum ada data tutor.")


# ABSENSI TUTOR (ADMIN)
elif menu == "Absensi Tutor":

    # TOMBOL KEMBALI
    if st.button("← Kembali", key="kembali_absensi_murid"):
        if st.session_state.tutor_login:
            st.session_state.menu_aktif = "Dashboard Tutor"
        else:
            st.session_state.menu_aktif = "Dashboard"

        st.rerun()

    from openpyxl import load_workbook
    from datetime import date, datetime

    if not (
        st.session_state.admin_login
        or st.session_state.tutor_login
    ):
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    st.markdown(
        '<div class="main-title">Absensi Tutor</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Catat kehadiran tutor dan murid yang diajar.</div>',
        unsafe_allow_html=True
    )

    # Ambil database terbaru
    database = load_database()

    data_tutor = database.get("tutor", pd.DataFrame())
    data_murid = database.get("murid", pd.DataFrame())
    data_absensi = database.get("absensi_tutor", pd.DataFrame())
    data_detail = database.get("detail_absensi_tutor", pd.DataFrame())

    tab1, tab2 = st.tabs(["Input Absensi", "Riwayat Absensi"])

    # ======================================
    # TAB 1 - INPUT ABSENSI
    # ======================================

    with tab1:

        st.subheader("Formulir Absensi Tutor")

        if data_tutor.empty:
            st.warning("Belum ada data tutor.")

        elif data_murid.empty:
            st.warning("Belum ada data murid. Tambahkan murid terlebih dahulu.")

        elif not {"tutor_id", "nama_lengkap"}.issubset(data_tutor.columns):
            st.error("Kolom tutor_id dan nama_lengkap tidak ditemukan.")

        elif not {"murid_id", "nama_lengkap"}.issubset(data_murid.columns):
            st.error("Kolom murid_id dan nama_lengkap tidak ditemukan.")

        else:

            # Daftar tutor
            daftar_tutor = data_tutor.dropna(
                subset=["tutor_id"]
            )["tutor_id"].astype(str).tolist()

            pilihan_tutor = st.selectbox(
                "Pilih Tutor",
                daftar_tutor,
                format_func=lambda x: data_tutor.loc[
                    data_tutor["tutor_id"].astype(str) == x,
                    "nama_lengkap"
                ].iloc[0],
                key="pilih_tutor_absensi"
            )

            tanggal_absensi = st.date_input(
                "Tanggal Absensi",
                value=date.today(),
                key="tanggal_input_absensi_tutor"
            )

            # Filter murid aktif
            murid_aktif = data_murid.copy()

            if "status" in murid_aktif.columns:
                murid_aktif = murid_aktif[
                    murid_aktif["status"].astype(str).str.strip().str.lower()
                    == "aktif"
                ]

            # Cari absensi yang sudah ada
            absensi_lama = pd.DataFrame()

            if not data_absensi.empty and {
                "tutor_id", "tanggal"
            }.issubset(data_absensi.columns):

                tanggal_data = pd.to_datetime(
                    data_absensi["tanggal"],
                    errors="coerce"
                ).dt.date

                absensi_lama = data_absensi[
                    (data_absensi["tutor_id"].astype(str) == pilihan_tutor)
                    & (tanggal_data == tanggal_absensi)
                ]

            id_absensi_lama = (
                str(absensi_lama.iloc[0]["absensi_tutor_id"])
                if not absensi_lama.empty else None
            )

            # Ambil murid yang sudah dipilih sebelumnya
            murid_terpilih_lama = []

            if (
                id_absensi_lama
                and not data_detail.empty
                and {"absensi_tutor_id", "murid_id"}.issubset(data_detail.columns)
            ):
                murid_terpilih_lama = data_detail.loc[
                    data_detail["absensi_tutor_id"].astype(str)
                    == id_absensi_lama,
                    "murid_id"
                ].astype(str).tolist()

            st.markdown("---")
            st.subheader("Daftar Murid yang Diajar")

            st.caption(
                "Centang murid yang mengikuti pembelajaran bersama tutor ini."
            )

            if murid_aktif.empty:
                st.info("Belum ada murid aktif.")
                daftar_id_murid = []

            else:
                daftar_id_murid = []

                # Tabel pilihan murid dengan checkbox
                semua_murid = murid_aktif.reset_index(drop=True)

                for nomor, murid_item in semua_murid.iterrows():

                    murid_id = str(murid_item["murid_id"])
                    nama_murid = str(murid_item["nama_lengkap"])

                    sudah_dipilih = (
                        murid_id in murid_terpilih_lama
                    )

                    col1, col2 = st.columns([5, 1])

                    with col1:
                        st.write(f"**{nomor + 1}. {nama_murid}**")

                    with col2:
                        dipilih = st.checkbox(
                            "Pilih",
                            value=sudah_dipilih,
                            key=f"absen_murid_{pilihan_tutor}_{tanggal_absensi}_{murid_id}",
                            label_visibility="collapsed"
                        )

                    if dipilih:
                        daftar_id_murid.append(murid_id)

                    st.divider()

            st.subheader("Status Kehadiran Tutor")

            status_default = (
                str(absensi_lama.iloc[0]["status_kehadiran"])
                if not absensi_lama.empty
                else "Hadir"
            )

            daftar_status = ["Hadir", "Izin", "Sakit", "Alpa"]

            status_kehadiran = st.selectbox(
                "Status Kehadiran",
                daftar_status,
                index=(
                    daftar_status.index(status_default)
                    if status_default in daftar_status else 0
                ),
                key=f"status_tutor_{pilihan_tutor}_{tanggal_absensi}"
            )

            keterangan_default = (
                str(absensi_lama.iloc[0].get("keterangan", "") or "")
                if not absensi_lama.empty else ""
            )

            keterangan = st.text_area(
                "Keterangan (Opsional)",
                value=keterangan_default,
                key=f"keterangan_tutor_{pilihan_tutor}_{tanggal_absensi}"
            )

            tombol_simpan = st.button(
                "Simpan Absensi Tutor",
                use_container_width=True,
                type="primary"
            )

            if tombol_simpan:

                try:
                    download_database()
                    wb = load_workbook(DB_PATH)

                    # Buat sheet absensi tutor jika belum ada
                    if "absensi_tutor" not in wb.sheetnames:
                        ws = wb.create_sheet("absensi_tutor")
                        ws.append([
                            "absensi_tutor_id",
                            "tutor_id",
                            "tanggal",
                            "status_kehadiran",
                            "keterangan",
                            "diinput_oleh",
                            "updated_at"
                        ])
                    else:
                        ws = wb["absensi_tutor"]

                    headers = [cell.value for cell in ws[1]]

                    kolom_wajib = [
                        "absensi_tutor_id",
                        "tutor_id",
                        "tanggal",
                        "status_kehadiran",
                        "keterangan",
                        "diinput_oleh",
                        "updated_at"
                    ]

                    for kolom in kolom_wajib:
                        if kolom not in headers:
                            headers.append(kolom)
                            ws.cell(1, len(headers)).value = kolom

                    posisi = {
                        nama: index + 1
                        for index, nama in enumerate(headers)
                    }

                    # Cari data absensi lama
                    baris_lama = None

                    for baris in range(2, ws.max_row + 1):

                        id_tutor = str(
                            ws.cell(baris, posisi["tutor_id"]).value
                        )

                        tanggal_lama = pd.to_datetime(
                            ws.cell(baris, posisi["tanggal"]).value,
                            errors="coerce"
                        )

                        if (
                            id_tutor == pilihan_tutor
                            and pd.notna(tanggal_lama)
                            and tanggal_lama.date() == tanggal_absensi
                        ):
                            baris_lama = baris
                            break

                    # Update atau buat ID baru
                    if baris_lama is not None:

                        absensi_id = str(
                            ws.cell(
                                baris_lama,
                                posisi["absensi_tutor_id"]
                            ).value
                        )

                    else:

                        nomor_terbesar = 0

                        for baris in range(2, ws.max_row + 1):
                            nilai = ws.cell(
                                baris,
                                posisi["absensi_tutor_id"]
                            ).value

                            if nilai and str(nilai).startswith("ATT"):
                                try:
                                    nomor_terbesar = max(
                                        nomor_terbesar,
                                        int(str(nilai)[3:])
                                    )
                                except ValueError:
                                    pass

                        absensi_id = f"ATT{nomor_terbesar + 1:04d}"
                        baris_lama = ws.max_row + 1

                    data_baru = {
                        "absensi_tutor_id": absensi_id,
                        "tutor_id": pilihan_tutor,
                        "tanggal": tanggal_absensi,
                        "status_kehadiran": status_kehadiran,
                        "keterangan": keterangan.strip(),
                        "diinput_oleh": (
                            "Admin"
                            if st.session_state.admin_login
                            else st.session_state.tutor_nama_login
                        ),
                        "updated_at": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    }

                    for kolom, nilai in data_baru.items():
                        ws.cell(
                            baris_lama,
                            posisi[kolom]
                        ).value = nilai

                    # Buat sheet detail murid jika belum ada
                    if "detail_absensi_tutor" not in wb.sheetnames:
                        ws_detail = wb.create_sheet("detail_absensi_tutor")
                        ws_detail.append([
                            "detail_id",
                            "absensi_tutor_id",
                            "murid_id"
                        ])
                    else:
                        ws_detail = wb["detail_absensi_tutor"]

                    header_detail = [
                        cell.value for cell in ws_detail[1]
                    ]

                    for kolom in [
                        "detail_id",
                        "absensi_tutor_id",
                        "murid_id"
                    ]:
                        if kolom not in header_detail:
                            header_detail.append(kolom)
                            ws_detail.cell(
                                1, len(header_detail)
                            ).value = kolom

                    posisi_detail = {
                        nama: index + 1
                        for index, nama in enumerate(header_detail)
                    }

                    # Hapus daftar murid lama untuk absensi ini
                    for baris in range(ws_detail.max_row, 1, -1):
                        if str(
                            ws_detail.cell(
                                baris,
                                posisi_detail["absensi_tutor_id"]
                            ).value
                        ) == absensi_id:
                            ws_detail.delete_rows(baris, 1)

                    # Tambahkan murid yang dipilih
                    nomor_detail = 0

                    for baris in range(2, ws_detail.max_row + 1):
                        nilai = ws_detail.cell(
                            baris,
                            posisi_detail["detail_id"]
                        ).value

                        if nilai and str(nilai).startswith("DATT"):
                            try:
                                nomor_detail = max(
                                    nomor_detail,
                                    int(str(nilai)[4:])
                                )
                            except ValueError:
                                pass

                    for murid_id in daftar_id_murid:
                        nomor_detail += 1

                        data_detail_baru = {
                            "detail_id": f"DATT{nomor_detail:04d}",
                            "absensi_tutor_id": absensi_id,
                            "murid_id": murid_id
                        }

                        ws_detail.append([
                            data_detail_baru.get(kolom, "")
                            for kolom in header_detail
                        ])

                    wb.save(DB_PATH)
                    wb.close()
                    upload_database()

                    st.cache_data.clear()

                    st.success(
                        f"Absensi tutor berhasil disimpan. ID: {absensi_id}"
                    )

                    st.rerun()

                except Exception as e:
                    st.error(f"Gagal menyimpan absensi: {e}")

    # ======================================
    # TAB 2 - RIWAYAT ABSENSI
    # ======================================
    with tab2:

        st.subheader("Riwayat Absensi Tutor")

        database = load_database()

        data_absensi = database.get(
            "absensi_tutor",
            pd.DataFrame()
        )

        data_tutor = database.get(
            "tutor",
            pd.DataFrame()
        )

        data_murid = database.get(
            "murid",
            pd.DataFrame()
        )

        data_detail = database.get(
            "detail_absensi_tutor",
            pd.DataFrame()
        )

        if data_absensi.empty:

            st.info("Belum ada riwayat absensi tutor.")

        else:

            riwayat = data_absensi.copy()

            # ======================================
            # GABUNGKAN NAMA TUTOR
            # ======================================
            if (
                not data_tutor.empty
                and {"tutor_id", "nama_lengkap"}.issubset(data_tutor.columns)
            ):

                riwayat = riwayat.merge(
                    data_tutor[["tutor_id", "nama_lengkap"]],
                    on="tutor_id",
                    how="left"
                )

                riwayat = riwayat.rename(
                    columns={"nama_lengkap": "nama_tutor"}
                )

            else:
                riwayat["nama_tutor"] = "-"

            riwayat["nama_tutor"] = (
                riwayat["nama_tutor"].fillna("-")
            )

            # ======================================
            # KONVERSI TANGGAL DAN STATUS
            # ======================================
            from datetime import datetime

            riwayat["tanggal"] = pd.to_datetime(
                riwayat["tanggal"],
                errors="coerce"
            )

            riwayat["status_normal"] = (
                riwayat["status_kehadiran"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # ======================================
            # FILTER BULAN DAN TAHUN
            # ======================================
            st.markdown("### Filter Periode Absensi")

            daftar_bulan = [
                "Januari", "Februari", "Maret", "April",
                "Mei", "Juni", "Juli", "Agustus",
                "September", "Oktober", "November", "Desember"
            ]

            col1, col2 = st.columns(2)

            with col1:

                bulan_pilihan = st.selectbox(
                    "Pilih Bulan",
                    range(1, 13),
                    index=datetime.now().month - 1,
                    format_func=lambda x: daftar_bulan[x - 1],
                    key="filter_bulan_riwayat_tutor"
                )

            with col2:

                tahun_pilihan = st.selectbox(
                    "Pilih Tahun",
                    range(2025, datetime.now().year + 1),
                    index=datetime.now().year - 2025,
                    key="filter_tahun_riwayat_tutor"
                )

            # FILTER DATA BERDASARKAN BULAN DAN TAHUN
            riwayat_bulan = riwayat[
                (riwayat["tanggal"].dt.month == bulan_pilihan)
                &
                (riwayat["tanggal"].dt.year == tahun_pilihan)
            ].copy()

            # ======================================
            # REKAP KEHADIRAN PER TUTOR
            # ======================================
            st.markdown("---")
            st.markdown("### Rekap Kehadiran Per Tutor")

            if riwayat_bulan.empty:

                st.info(
                    "Belum ada data absensi pada bulan dan tahun yang dipilih."
                )

            else:

                # Kelompokkan berdasarkan tutor
                rekap = (
                    riwayat_bulan
                    .groupby(
                        ["tutor_id", "nama_tutor"],
                        dropna=False
                    )["status_normal"]
                    .value_counts()
                    .unstack(fill_value=0)
                    .reset_index()
                )

                # Pastikan semua kolom status tersedia
                for status in ["hadir", "izin", "sakit", "alpa"]:

                    if status not in rekap.columns:
                        rekap[status] = 0

                # Susun kolom rekap
                rekap = rekap[
                    [
                        "tutor_id",
                        "nama_tutor",
                        "hadir",
                        "izin",
                        "sakit",
                        "alpa"
                    ]
                ]

                # Ubah nama kolom
                rekap = rekap.rename(
                    columns={
                        "tutor_id": "ID Tutor",
                        "nama_tutor": "Nama Tutor",
                        "hadir": "Hadir",
                        "izin": "Izin",
                        "sakit": "Sakit",
                        "alpa": "Alpa"
                    }
                )

                # Pastikan jumlah berupa integer
                kolom_jumlah = [
                    "Hadir",
                    "Izin",
                    "Sakit",
                    "Alpa"
                ]

                rekap[kolom_jumlah] = (
                    rekap[kolom_jumlah].astype(int)
                )

                # Urutkan berdasarkan nama tutor
                rekap = rekap.sort_values(
                    "Nama Tutor"
                )

                st.dataframe(
                    rekap,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    f"Total {len(rekap)} tutor memiliki data absensi "
                    f"pada {daftar_bulan[bulan_pilihan - 1]} {tahun_pilihan}."
                )

            # ======================================
            # RIWAYAT DETAIL ABSENSI
            # ======================================
            st.markdown("---")
            st.markdown("### Detail Riwayat Absensi")

            riwayat_detail = riwayat_bulan.copy()

            # ======================================
            # GABUNGKAN DAFTAR MURID YANG DIAJAR
            # ======================================
            if (
                not data_detail.empty
                and not data_murid.empty
                and {"absensi_tutor_id", "murid_id"}.issubset(data_detail.columns)
                and {"murid_id", "nama_lengkap"}.issubset(data_murid.columns)
            ):

                detail_nama = data_detail.merge(
                    data_murid[["murid_id", "nama_lengkap"]],
                    on="murid_id",
                    how="left"
                )

                daftar_nama_murid = (
                    detail_nama
                    .groupby("absensi_tutor_id")["nama_lengkap"]
                    .apply(
                        lambda x: ", ".join(
                            x.dropna().astype(str)
                        )
                    )
                    .reset_index(name="murid_diajar")
                )

                riwayat_detail = riwayat_detail.merge(
                    daftar_nama_murid,
                    on="absensi_tutor_id",
                    how="left"
                )

            else:

                riwayat_detail["murid_diajar"] = "-"

            riwayat_detail["murid_diajar"] = (
                riwayat_detail["murid_diajar"].fillna("-")
            )

            # ======================================
            # FILTER TUTOR
            # ======================================
            daftar_nama = ["Semua Tutor"] + sorted(
                riwayat_detail["nama_tutor"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filter_tutor = st.selectbox(
                "Filter Tutor",
                daftar_nama,
                key="filter_riwayat_absensi_tutor"
            )

            if filter_tutor != "Semua Tutor":

                riwayat_detail = riwayat_detail[
                    riwayat_detail["nama_tutor"].astype(str)
                    == filter_tutor
                ]

            # ======================================
            # FILTER STATUS
            # ======================================
            filter_status = st.selectbox(
                "Filter Status",
                ["Semua Status", "Hadir", "Izin", "Sakit", "Alpa"],
                key="filter_status_absensi_tutor"
            )

            if filter_status != "Semua Status":

                riwayat_detail = riwayat_detail[
                    riwayat_detail["status_normal"]
                    == filter_status.lower()
                ]

            # ======================================
            # URUTKAN BERDASARKAN TANGGAL
            # ======================================
            riwayat_detail = riwayat_detail.sort_values(
                "tanggal",
                ascending=False
            )

            # ======================================
            # TAMPILKAN RIWAYAT
            # ======================================
            kolom_tampil = [
                kolom for kolom in [
                    "absensi_tutor_id",
                    "tanggal",
                    "tutor_id",
                    "nama_tutor",
                    "murid_diajar",
                    "status_kehadiran",
                    "keterangan",
                    "diinput_oleh",
                    "updated_at"
                ]
                if kolom in riwayat_detail.columns
            ]

            st.dataframe(
                riwayat_detail[kolom_tampil],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Total {len(riwayat_detail)} data absensi."
            )

# ABSENSI MURID (ADMIN)
elif menu == "Absensi Murid":

    from openpyxl import load_workbook
    from datetime import date, datetime

    # TOMBOL KEMBALI
    if st.button("← Kembali", key="kembali_absensi_murid"):
        if st.session_state.tutor_login:
            st.session_state.menu_aktif = "Dashboard Tutor"
        else:
            st.session_state.menu_aktif = "Dashboard"

        st.rerun()

    if not (
        st.session_state.admin_login
        or st.session_state.tutor_login
    ):
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    st.markdown(
        '<div class="main-title">Absensi Murid</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Kelola kehadiran murid bimbingan belajar.</div>',
        unsafe_allow_html=True
    )

    # Ambil database terbaru
    database = load_database()

    data_murid = database.get("murid", pd.DataFrame())
    data_absensi = database.get("absensi_murid", pd.DataFrame())

    tab1, tab2 = st.tabs(["Input Absensi", "Riwayat Absensi"])

    # TAB 1 - INPUT ABSENSI
    with tab1:

        st.subheader("Formulir Absensi Murid")

        if data_murid.empty:
            st.warning("Belum ada data murid.")

        elif not {"murid_id", "nama_lengkap"}.issubset(data_murid.columns):
            st.error("Kolom murid_id dan nama_lengkap tidak ditemukan.")

        else:

            # Filter murid aktif
            murid_aktif = data_murid.dropna(
                subset=["murid_id", "nama_lengkap"]
            ).copy()

            if "status" in murid_aktif.columns:
                murid_aktif = murid_aktif[
                    murid_aktif["status"].astype(str).str.strip().str.lower()
                    == "aktif"
                ]

            if murid_aktif.empty:
                st.info("Belum ada murid aktif.")

            else:

                # Daftar murid
                daftar_murid = murid_aktif[
                    "murid_id"
                ].astype(str).tolist()

                pilihan_murid = st.selectbox(
                    "Pilih Murid",
                    daftar_murid,
                    format_func=lambda x: murid_aktif.loc[
                        murid_aktif["murid_id"].astype(str) == x,
                        "nama_lengkap"
                    ].iloc[0],
                    key="pilih_murid_absensi"
                )

                tanggal_absensi = st.date_input(
                    "Tanggal Absensi",
                    value=date.today(),
                    key="tanggal_input_absensi_murid"
                )

                # Cari absensi yang sudah ada
                absensi_lama = pd.DataFrame()

                if not data_absensi.empty and {
                    "murid_id", "tanggal"
                }.issubset(data_absensi.columns):

                    tanggal_data = pd.to_datetime(
                        data_absensi["tanggal"],
                        errors="coerce"
                    ).dt.date

                    absensi_lama = data_absensi[
                        (
                            data_absensi["murid_id"].astype(str)
                            == pilihan_murid
                        )
                        & (tanggal_data == tanggal_absensi)
                    ]

                # Status sebelumnya
                status_default = (
                    str(absensi_lama.iloc[0]["status_kehadiran"])
                    if (
                        not absensi_lama.empty
                        and "status_kehadiran" in absensi_lama.columns
                    )
                    else "Hadir"
                )

                st.markdown("---")
                st.subheader("Status Kehadiran")

                daftar_status = ["Hadir", "Izin", "Sakit", "Alpa"]

                status_kehadiran = st.selectbox(
                    "Status Kehadiran Murid",
                    daftar_status,
                    index=(
                        daftar_status.index(status_default)
                        if status_default in daftar_status else 0
                    ),
                    key=f"status_murid_{pilihan_murid}_{tanggal_absensi}"
                )

                keterangan_default = (
                    str(absensi_lama.iloc[0].get("keterangan", "") or "")
                    if not absensi_lama.empty else ""
                )

                keterangan = st.text_area(
                    "Keterangan (Opsional)",
                    value=keterangan_default,
                    key=f"keterangan_murid_{pilihan_murid}_{tanggal_absensi}"
                )

                tombol_simpan = st.button(
                    "Simpan Absensi Murid",
                    use_container_width=True,
                    type="primary"
                )

                if tombol_simpan:

                    try:
                        download_database()
                        wb = load_workbook(DB_PATH)

                        # Buat sheet jika belum tersedia
                        if "absensi_murid" not in wb.sheetnames:
                            ws = wb.create_sheet("absensi_murid")
                            ws.append([
                                "absensi_id",
                                "murid_id",
                                "tanggal",
                                "status_kehadiran",
                                "keterangan",
                                "diinput_oleh",
                                "updated_at"
                            ])
                        else:
                            ws = wb["absensi_murid"]

                        headers = [
                            cell.value for cell in ws[1]
                        ]

                        kolom_wajib = [
                            "absensi_id",
                            "murid_id",
                            "tanggal",
                            "status_kehadiran",
                            "keterangan",
                            "diinput_oleh",
                            "updated_at"
                        ]

                        for kolom in kolom_wajib:
                            if kolom not in headers:
                                headers.append(kolom)
                                ws.cell(
                                    1, len(headers)
                                ).value = kolom

                        posisi = {
                            nama: index + 1
                            for index, nama in enumerate(headers)
                        }

                        # Cari absensi lama berdasarkan murid dan tanggal
                        baris_lama = None

                        for baris in range(2, ws.max_row + 1):

                            id_murid_lama = str(
                                ws.cell(
                                    baris,
                                    posisi["murid_id"]
                                ).value
                            )

                            tanggal_lama = pd.to_datetime(
                                ws.cell(
                                    baris,
                                    posisi["tanggal"]
                                ).value,
                                errors="coerce"
                            )

                            if (
                                id_murid_lama == pilihan_murid
                                and pd.notna(tanggal_lama)
                                and tanggal_lama.date() == tanggal_absensi
                            ):
                                baris_lama = baris
                                break

                        # Update data lama atau buat ID baru
                        if baris_lama is not None:

                            absensi_id = str(
                                ws.cell(
                                    baris_lama,
                                    posisi["absensi_id"]
                                ).value
                            )

                            if not absensi_id or absensi_id == "None":
                                absensi_id = "ABM" + uuid.uuid4().hex[:8].upper()

                            # Pertahankan admin yang pertama kali menginput
                            admin_input = ws.cell(
                                baris_lama,
                                posisi["diinput_oleh"]
                            ).value

                            if not admin_input:
                                admin_input = "Admin"

                        else:

                            nomor_terbesar = 0

                            for baris in range(2, ws.max_row + 1):

                                nilai = ws.cell(
                                    baris,
                                    posisi["absensi_id"]
                                ).value

                                if nilai and str(nilai).startswith("ABM"):
                                    try:
                                        nomor_terbesar = max(
                                            nomor_terbesar,
                                            int(str(nilai)[3:])
                                        )
                                    except ValueError:
                                        pass

                            absensi_id = f"ABM{nomor_terbesar + 1:04d}"
                            baris_lama = ws.max_row + 1
                            admin_input = (
                                              "Admin"
                                              if st.session_state.admin_login
                                              else st.session_state.tutor_nama_login
                                          )

                        # Data absensi
                        data_baru = {
                            "absensi_id": absensi_id,
                            "murid_id": pilihan_murid,
                            "tanggal": tanggal_absensi,
                            "status_kehadiran": status_kehadiran,
                            "keterangan": keterangan.strip(),
                            "diinput_oleh": admin_input,
                            "updated_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        }

                        for kolom, nilai in data_baru.items():
                            ws.cell(
                                baris_lama,
                                posisi[kolom]
                            ).value = nilai

                        wb.save(DB_PATH)
                        wb.close()
                        upload_database()

                        st.cache_data.clear()

                        st.success(
                            f"Absensi murid berhasil disimpan. ID: {absensi_id}"
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(f"Gagal menyimpan absensi: {e}")
    # ======================================
    # TAB 2 - RIWAYAT ABSENSI
    # ======================================
    with tab2:

        st.subheader("Riwayat Absensi Murid")

        database = load_database()

        data_absensi = database.get(
            "absensi_murid",
            pd.DataFrame()
        )

        data_murid = database.get(
            "murid",
            pd.DataFrame()
        )

        if data_absensi.empty:

            st.info("Belum ada riwayat absensi murid.")

        else:

            riwayat = data_absensi.copy()

            # ======================================
            # GABUNGKAN DATA NAMA MURID
            # ======================================
            if (
                not data_murid.empty
                and {"murid_id", "nama_lengkap"}.issubset(data_murid.columns)
            ):

                riwayat = riwayat.merge(
                    data_murid[["murid_id", "nama_lengkap"]],
                    on="murid_id",
                    how="left"
                )

                riwayat = riwayat.rename(
                    columns={"nama_lengkap": "nama_murid"}
                )

            else:
                riwayat["nama_murid"] = "-"

            riwayat["nama_murid"] = (
                riwayat["nama_murid"].fillna("-")
            )

            # ======================================
            # KONVERSI TANGGAL DAN STATUS
            # ======================================
            from datetime import datetime

            riwayat["tanggal"] = pd.to_datetime(
                riwayat["tanggal"],
                errors="coerce"
            )

            riwayat["status_normal"] = (
                riwayat["status_kehadiran"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
            )

            # ======================================
            # FILTER BULAN DAN TAHUN
            # ======================================
            st.markdown("### Filter Periode Absensi")

            daftar_bulan = [
                "Januari", "Februari", "Maret", "April",
                "Mei", "Juni", "Juli", "Agustus",
                "September", "Oktober", "November", "Desember"
            ]

            col1, col2 = st.columns(2)

            with col1:

                bulan_pilihan = st.selectbox(
                    "Pilih Bulan",
                    range(1, 13),
                    index=datetime.now().month - 1,
                    format_func=lambda x: daftar_bulan[x - 1],
                    key="filter_bulan_riwayat_murid"
                )

            with col2:

                tahun_pilihan = st.selectbox(
                    "Pilih Tahun",
                    range(2025, datetime.now().year + 1),
                    index=datetime.now().year - 2025,
                    key="filter_tahun_riwayat_murid"
                )

            # FILTER DATA BERDASARKAN BULAN DAN TAHUN
            riwayat_bulan = riwayat[
                (riwayat["tanggal"].dt.month == bulan_pilihan)
                &
                (riwayat["tanggal"].dt.year == tahun_pilihan)
            ].copy()

            # ======================================
            # REKAP KEHADIRAN PER MURID
            # ======================================
            st.markdown("---")
            st.markdown("### Rekap Kehadiran Per Murid")

            if riwayat_bulan.empty:

                st.info(
                    "Belum ada data absensi pada bulan dan tahun yang dipilih."
                )

            else:

                # Kelompokkan berdasarkan murid
                rekap = (
                    riwayat_bulan
                    .groupby(
                        ["murid_id", "nama_murid"],
                        dropna=False
                    )["status_normal"]
                    .value_counts()
                    .unstack(fill_value=0)
                    .reset_index()
                )

                # Pastikan semua kolom status tersedia
                for status in ["hadir", "izin", "sakit", "alpa"]:
                    if status not in rekap.columns:
                        rekap[status] = 0

                # Susun kolom rekap
                rekap = rekap[
                    [
                        "murid_id",
                        "nama_murid",
                        "hadir",
                        "izin",
                        "sakit",
                        "alpa"
                    ]
                ]

                # Ubah nama kolom
                rekap = rekap.rename(
                    columns={
                        "murid_id": "ID Murid",
                        "nama_murid": "Nama Murid",
                        "hadir": "Hadir",
                        "izin": "Izin",
                        "sakit": "Sakit",
                        "alpa": "Alpa"
                    }
                )

                # Pastikan jumlah berupa integer
                kolom_jumlah = [
                    "Hadir", "Izin", "Sakit", "Alpa"
                ]

                rekap[kolom_jumlah] = (
                    rekap[kolom_jumlah].astype(int)
                )

                # Urutkan berdasarkan nama murid
                rekap = rekap.sort_values(
                    "Nama Murid"
                )

                st.dataframe(
                    rekap,
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    f"Total {len(rekap)} murid memiliki data absensi "
                    f"pada {daftar_bulan[bulan_pilihan - 1]} {tahun_pilihan}."
                )

            # ======================================
            # RIWAYAT DETAIL ABSENSI
            # ======================================
            st.markdown("---")
            st.markdown("### Detail Riwayat Absensi")

            # Filter murid
            daftar_nama = ["Semua Murid"] + sorted(
                riwayat_bulan["nama_murid"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            filter_murid = st.selectbox(
                "Filter Murid",
                daftar_nama,
                key="filter_riwayat_absensi_murid"
            )

            riwayat_detail = riwayat_bulan.copy()

            if filter_murid != "Semua Murid":

                riwayat_detail = riwayat_detail[
                    riwayat_detail["nama_murid"].astype(str)
                    == filter_murid
                ]

            # Filter status
            filter_status = st.selectbox(
                "Filter Status Kehadiran",
                ["Semua Status", "Hadir", "Izin", "Sakit", "Alpa"],
                key="filter_status_absensi_murid"
            )

            if filter_status != "Semua Status":

                riwayat_detail = riwayat_detail[
                    riwayat_detail["status_normal"]
                    == filter_status.lower()
                ]

            # Urutkan berdasarkan tanggal
            riwayat_detail = riwayat_detail.sort_values(
                "tanggal",
                ascending=False
            )

            # Kolom yang ditampilkan
            kolom_tampil = [
                kolom for kolom in [
                    "absensi_id",
                    "murid_id",
                    "tanggal",
                    "nama_murid",
                    "status_kehadiran",
                    "keterangan",
                    "diinput_oleh",
                    "updated_at"
                ]
                if kolom in riwayat_detail.columns
            ]

            st.dataframe(
                riwayat_detail[kolom_tampil],
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"Total {len(riwayat_detail)} data absensi."
            )


# ======================================
# VERIFIKASI PENDAFTARAN MURID ADMIN
# ======================================

elif menu == "Verifikasi Pendaftaran":

    from openpyxl import load_workbook

    # TOMBOL KEMBALI
    if st.button("← Kembali", key="kembali_verifikasi"):
        st.session_state.menu_aktif = "Dashboard"
        st.rerun()

    # ======================================
    # KEAMANAN ADMIN
    # ======================================

    if not st.session_state.admin_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    # ======================================
    # JUDUL HALAMAN
    # ======================================

    st.markdown("""
        <div style="text-align:center; margin-top:5px; margin-bottom:18px;">
            <div style="
                font-size:28px;
                font-weight:700;
                color:#17375E;
            ">
                Verifikasi Pendaftaran Murid
            </div>
            <div style="
                font-size:13px;
                color:#718096;
                margin-top:5px;
            ">
                Periksa data calon murid dan tentukan status penerimaannya.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ======================================
    # MEMBACA DATA PENDAFTARAN
    # ======================================

    data_pendaftaran = load_database().get(
        "pendaftaran_murid",
        pd.DataFrame()
    )

    # ======================================
    # FILTER KHUSUS STATUS MENUNGGU
    # ======================================

    if not data_pendaftaran.empty:

        if "status_pendaftaran" not in data_pendaftaran.columns:
            data_pendaftaran["status_pendaftaran"] = "Menunggu"

        data_pendaftaran["status_pendaftaran"] = (
            data_pendaftaran["status_pendaftaran"]
            .fillna("Menunggu")
            .astype(str)
            .str.strip()
        )

        tampil_pendaftaran = data_pendaftaran[
            data_pendaftaran["status_pendaftaran"] == "Menunggu"
        ].copy()

    else:
        tampil_pendaftaran = pd.DataFrame()

    # ======================================
    # JUMLAH PENDAFTAR MENUNGGU
    # ======================================

    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            border-left:5px solid #E5B85C;
            border-radius:12px;
            padding:16px 20px;
            margin-bottom:18px;
        ">
            <div style="font-size:13px; color:#718096;">
                Total Murid Menunggu Verifikasi
            </div>
            <div style="
                font-size:28px;
                font-weight:700;
                color:#17375E;
            ">
                {len(tampil_pendaftaran)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================================
    # TABEL DAFTAR CALON MURID
    # ======================================

    st.subheader("Daftar Calon Murid")

    if not tampil_pendaftaran.empty:

        kolom_daftar = [
            kolom for kolom in [
                "nama_lengkap",
                "tanggal_daftar",
                "kelas",
                "sekolah",
                "no_whatsapp_orang_tua",
                "status_pendaftaran"
            ]
            if kolom in tampil_pendaftaran.columns
        ]

        st.dataframe(
            tampil_pendaftaran[kolom_daftar],
            use_container_width=True,
            hide_index=True
        )

        # ======================================
        # PILIH MURID UNTUK VERIFIKASI
        # ======================================

        st.subheader("Proses Verifikasi")

        daftar_id = (
            tampil_pendaftaran["pendaftaran_id"]
            .dropna()
            .astype(str)
            .tolist()
        )

        pilihan_id = st.selectbox(
            "Pilih Calon Murid",
            daftar_id,
            format_func=lambda x: (
                f"{x} - "
                f"{tampil_pendaftaran.loc[
                    tampil_pendaftaran['pendaftaran_id'].astype(str) == x,
                    'nama_lengkap'
                ].iloc[0]}"
            ),
            key="pilihan_verifikasi_murid"
        )

        item = tampil_pendaftaran[
            tampil_pendaftaran["pendaftaran_id"].astype(str) == pilihan_id
        ].iloc[0]

        # ======================================
        # DETAIL MURID
        # ======================================

        with st.expander("Lihat Detail Pendaftaran", expanded=False):

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Nama Lengkap:**", item.get("nama_lengkap", "-"))
                st.write("**Nama Panggilan:**", item.get("nama_panggilan", "-"))
                st.write("**Tempat Lahir:**", item.get("tempat_lahir", "-"))
                st.write("**Tanggal Lahir:**", item.get("tanggal_lahir", "-"))
                st.write("**Jenis Kelamin:**", item.get("gender", "-"))
                st.write("**Sekolah:**", item.get("sekolah", "-"))
                st.write("**Kelas:**", item.get("kelas", "-"))

            with col2:
                st.write("**Nama Ayah:**", item.get("nama_ayah", "-"))
                st.write("**Pekerjaan Ayah:**", item.get("pekerjaan_ayah", "-"))
                st.write("**Nama Ibu:**", item.get("nama_ibu", "-"))
                st.write("**Pekerjaan Ibu:**", item.get("pekerjaan_ibu", "-"))
                st.write("**WhatsApp:**", item.get("no_whatsapp_orang_tua", "-"))
                st.write("**Alamat:**", item.get("alamat", "-"))

            st.write(
                "**Kebutuhan Belajar:**",
                item.get("kebutuhan_belajar", "-")
            )

            # Ambil nama paket berdasarkan ID paket
            data_paket = get_data("paket")
            id_paket = str(item.get("paket_id", "")).strip()
            nama_paket = "-"

            if not data_paket.empty:
                hasil_paket = data_paket[
                    data_paket["paket_id"].astype(str).str.strip() == id_paket
                ]

                if not hasil_paket.empty:
                    nama_paket = hasil_paket.iloc[0]["nama_paket"]

            st.write(
                "**Paket:**",
                nama_paket
            )

            st.write(
                "**Jadwal Preferensi:**",
                item.get("jadwal_preferensi", "-")
            )

            st.write(
                "**Catatan Khusus:**",
                item.get("catatan_khusus", "-")
            )
        # ======================================
        # FORM UBAH STATUS
        # ======================================

        st.markdown("**Ubah Status Pendaftaran**")

        with st.form("form_verifikasi_murid"):

            status_baru = st.radio(
                "Keputusan Admin",
                ["Diterima", "Ditolak"],
                horizontal=True
            )
            tanggal_masuk = st.date_input(
                "Tanggal Masuk",
                format="DD-MM-YYYY"
            )

            catatan_lama = item.get("catatan_admin", "")

            if pd.isna(catatan_lama):
                catatan_lama = ""

            catatan_admin = st.text_area(
                "Catatan Admin",
                value=str(catatan_lama),
                placeholder="Tambahkan catatan jika diperlukan."
            )

            simpan_status = st.form_submit_button(
                "Simpan Perubahan Status",
                use_container_width=True
            )

        # ======================================
        # SIMPAN PERUBAHAN KE EXCEL
        # ======================================

        if simpan_status:

            wb = None

            try:
                download_database()
                wb = load_workbook(DB_PATH)

                ws_daftar = wb["pendaftaran_murid"]
                ws_murid = wb["murid"]

                # ======================================
                # HEADER DATABASE
                # ======================================

                header_daftar = [
                    cell.value for cell in ws_daftar[1]
                ]

                header_murid = [
                    cell.value for cell in ws_murid[1]
                ]

                posisi_daftar = {
                    nama: index + 1
                    for index, nama in enumerate(header_daftar)
                }

                posisi_murid = {
                    nama: index + 1
                    for index, nama in enumerate(header_murid)
                }

                if (
                    "pendaftaran_id" not in posisi_daftar
                    or "status_pendaftaran" not in posisi_daftar
                ):
                    raise ValueError(
                        "Kolom pendaftaran tidak ditemukan."
                    )

                # ======================================
                # CARI DATA PENDAFTARAN
                # ======================================

                baris_pendaftaran = None

                for baris in range(2, ws_daftar.max_row + 1):

                    id_excel = ws_daftar.cell(
                        baris,
                        posisi_daftar["pendaftaran_id"]
                    ).value

                    if str(id_excel).strip() == pilihan_id.strip():
                        baris_pendaftaran = baris
                        break

                if baris_pendaftaran is None:
                    raise ValueError(
                        "Data pendaftaran tidak ditemukan."
                    )

                # ======================================
                # JIKA DITERIMA
                # ======================================

                murid_id_baru = None

                if status_baru == "Diterima":

                    if "murid_id" not in posisi_murid:
                        raise ValueError(
                            "Kolom murid_id tidak ditemukan."
                        )

                    # Cek apakah murid sudah pernah dimasukkan
                    nama_murid = str(
                        item.get("nama_lengkap", "")
                    ).strip().lower()

                    murid_sudah_ada = False

                    for baris in range(2, ws_murid.max_row + 1):

                        nama_lama = ws_murid.cell(
                            baris,
                            posisi_murid["nama_lengkap"]
                        ).value if "nama_lengkap" in posisi_murid else ""

                        if str(nama_lama).strip().lower() == nama_murid:
                            murid_sudah_ada = True
                            break

                    if not murid_sudah_ada:

                        # Buat ID murid otomatis
                        nomor_terbesar = 0

                        for baris in range(2, ws_murid.max_row + 1):

                            id_lama = ws_murid.cell(
                                baris,
                                posisi_murid["murid_id"]
                            ).value

                            if id_lama and str(id_lama).startswith("MUR"):
                                try:
                                    nomor = int(str(id_lama)[3:])
                                    nomor_terbesar = max(
                                        nomor_terbesar,
                                        nomor
                                    )
                                except ValueError:
                                    pass

                        murid_id_baru = (
                            f"MUR{nomor_terbesar + 1:04d}"
                        )

                        # Data murid sesuai kolom Excel
                        data_baru = {
                            "murid_id": murid_id_baru,
                            "parent_id": "",
                            "nama_lengkap": item.get("nama_lengkap", ""),
                            "nama_panggilan": item.get("nama_panggilan", ""),
                            "tempat_lahir": item.get("tempat_lahir", ""),
                            "tanggal_lahir": item.get("tanggal_lahir", ""),
                            "gender": item.get("gender", ""),
                            "sekolah": item.get("sekolah", ""),
                            "kelas": item.get("kelas", ""),
                            "kebutuhan_belajar": item.get("kebutuhan_belajar", ""),
                            "paket_id": item.get("paket_id", ""),
                            "catatan_khusus": item.get("catatan_khusus", ""),
                            "tanggal_masuk": tanggal_masuk.strftime("%Y-%m-%d"),
                            "status": "Aktif"
                        }

                        # Tambahkan baris ke sheet murid
                        baris_baru = ws_murid.max_row + 1

                        for kolom, nilai in data_baru.items():

                            if kolom in posisi_murid:
                                ws_murid.cell(
                                    baris_baru,
                                    posisi_murid[kolom]
                                ).value = nilai

                # ======================================
                # PERBARUI STATUS PENDAFTARAN
                # ======================================

                ws_daftar.cell(
                    baris_pendaftaran,
                    posisi_daftar["status_pendaftaran"]
                ).value = status_baru

                if "catatan_admin" in posisi_daftar:
                    ws_daftar.cell(
                        baris_pendaftaran,
                        posisi_daftar["catatan_admin"]
                    ).value = catatan_admin

                # ======================================
                # SIMPAN DATABASE
                # ======================================

                wb.save(DB_PATH)
                wb.close()
                wb = None
                upload_database()

                st.cache_data.clear()

                if status_baru == "Diterima":
                    st.success(
                        "Pendaftaran berhasil diterima dan "
                        "data murid sudah ditambahkan ke Daftar Murid."
                    )
                else:
                    st.success(
                        "Pendaftaran berhasil ditolak."
                    )

                st.rerun()

            except Exception as e:

                if wb is not None:
                    wb.close()

                st.error(
                    f"Gagal menyimpan perubahan: {e}"
                )

# ======================================
# CRUD PAKET BELAJAR (ADMIN)
# ======================================

elif menu == "Paket Belajar":

    from openpyxl import load_workbook

    # ======================================
    # TOMBOL KEMBALI
    # ======================================
    if st.button("← Kembali", key="kembali_verifikasi"):
        st.session_state.menu_aktif = "Dashboard"
        st.rerun()

    if not st.session_state.admin_login:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()

    st.markdown(
        '<div class="main-title">Manajemen Paket Belajar</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Tambah, lihat, edit, dan hapus paket serta harga belajar.</div>',
        unsafe_allow_html=True
    )

    # ======================================
    # MEMBACA DATA PAKET TERBARU
    # ======================================
    paket = load_database().get("paket", pd.DataFrame())

    tab1, tab2, tab3 = st.tabs([
        "Daftar Paket",
        "Tambah Paket",
        "Edit / Hapus Paket"
    ])

    # ======================================
    # TAB 1 - DAFTAR PAKET
    # ======================================
    with tab1:
        # ======================================
        # AMBIL DATA PAKET DARI DATABASE
        # ======================================
        paket = get_data("paket")

        if not paket.empty:

            kolom = st.columns(3, gap="small")

            for index, (_, item) in enumerate(paket.iterrows()):

                with kolom[index % 3]:

                    # Ambil data paket
                    nama_paket = str(
                        item.get("nama_paket", "Paket Belajar")
                    )

                    harga_raw = pd.to_numeric(
                        item.get("harga"),
                        errors="coerce"
                    )

                    harga = (
                        f"Rp{int(harga_raw):,}".replace(",", ".")
                        if pd.notna(harga_raw)
                        else "-"
                    )

                    durasi_raw = pd.to_numeric(
                        item.get("durasi_menit"),
                        errors="coerce"
                    )

                    durasi = (
                        f"{int(durasi_raw)} Menit"
                        if pd.notna(durasi_raw)
                        else "-"
                    )

                    jenis_raw = item.get("jenis_paket", "-")

                    jenis_kelas = (
                        "-"
                        if pd.isna(jenis_raw)
                        or str(jenis_raw).strip() == ""
                        else str(jenis_raw)
                    )

                    deskripsi_raw = item.get("deskripsi", "-")

                    deskripsi = (
                        "-"
                        if pd.isna(deskripsi_raw)
                        or str(deskripsi_raw).strip() == ""
                        else str(deskripsi_raw)
                    )

                    status_raw = item.get("status", "-")

                    status = (
                        "-"
                        if pd.isna(status_raw)
                        or str(status_raw).strip() == ""
                        else str(status_raw)
                    )

                    from html import escape

                    # ======================================
                    # KARTU PAKET
                    # ======================================
                    with st.container(
                        key=f"paket-card-{item.get('paket_id')}"
                    ):

                        st.markdown(
                            f"""
                            <div style="text-align:center;">
                                <div style="font-size:27px;">📚</div>
                                <div class="paket-card-title">
                                    {escape(nama_paket)}
                                </div>
                            </div>

                            <div class="paket-card-info">
                                💰 <b>Harga:</b> {escape(harga)}
                            </div>

                            <div class="paket-card-info">
                                ⏱️ <b>Durasi:</b> {escape(durasi)}
                            </div>

                            <div class="paket-card-info">
                                👥 <b>Jenis Paket:</b> {escape(jenis_kelas)}
                            </div>

                            <div class="paket-card-label">
                                📝 Keterangan Paket
                            </div>

                            <div class="paket-card-description">
                                {escape(deskripsi)}
                            </div>

                            <div class="paket-card-info">
                                🔖 <b>Status:</b> {escape(status)}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        else:

            st.info(
                "Belum ada paket belajar."
            )

    # ======================================
    # TAB 2 - TAMBAH PAKET
    # ======================================
    with tab2:

        st.subheader("Tambah Paket Baru")

        with st.form("form_tambah_paket"):

            nama_paket = st.text_input(
                "Nama Paket *"
            )

            harga_input = st.text_input(
                "Harga Paket (Rp) *",
                placeholder="Contoh: 150000"
            )

            durasi = st.selectbox(
                "Durasi Belajar",
                ["60 Menit", "90 Menit"]
            )

            jenis_kelas = st.selectbox(
                "Jenis Paket",
                ["Private", "Semi-Private", "Reguler"]
            )

            deskripsi = st.text_area(
                "Keterangan Paket",
                placeholder="Masukkan keterangan paket belajar."
            )

            status = st.selectbox(
                "Status Paket",
                ["Aktif", "Nonaktif"]
            )

            simpan = st.form_submit_button(
                "Simpan Paket",
                use_container_width=True
            )

            if simpan:

                if not nama_paket.strip():

                    st.error("Nama paket wajib diisi.")

                else:

                    try:

                        # MENGUBAH INPUT HARGA MENJADI ANGKA
                        harga = int(
                            harga_input.replace("Rp", "")
                            .replace(".", "")
                            .replace(",", "")
                            .replace(" ", "")
                        )

                        if harga <= 0:

                            st.error(
                                "Harga paket harus lebih dari 0."
                            )

                        else:
                            download_database()
                            wb = load_workbook(DB_PATH)
                            ws = wb["paket"]

                            headers = [
                                cell.value for cell in ws[1]
                            ]

                            nomor_terbesar = 0

                            for row in ws.iter_rows(
                                min_row=2,
                                values_only=True
                            ):

                                nilai = row[0]

                                if nilai and str(nilai).startswith("PKT"):

                                    try:
                                        nomor = int(str(nilai)[3:])

                                        nomor_terbesar = max(
                                            nomor_terbesar,
                                            nomor
                                        )

                                    except ValueError:
                                        pass

                            paket_id = (
                                f"PKT{nomor_terbesar + 1:04d}"
                            )

                            # ======================================
                            # DATA PAKET BARU
                            # ======================================
                            data_baru = {
                                "paket_id": paket_id,
                                "nama_paket": nama_paket.strip(),
                                "durasi_menit": int(durasi.split()[0]),
                                "jenis_paket": jenis_kelas,
                                "harga": harga,
                                "deskripsi": deskripsi.strip(),
                                "status": status
                            }

                            # MENYIMPAN SESUAI HEADER EXCEL
                            ws.append([
                                data_baru.get(kolom, "")
                                for kolom in headers
                            ])

                            wb.save(DB_PATH)
                            wb.close()
                            upload_database()

                            st.cache_data.clear()

                            st.success(
                                f"Paket berhasil ditambahkan dengan ID {paket_id}."
                            )

                            st.rerun()

                    except ValueError:

                        st.error(
                            "Harga harus berupa angka. Contoh: 150000"
                        )

                    except Exception as e:

                        st.error(
                            f"Gagal menambahkan paket: {e}"
                        )

    # ======================================
    # TAB 3 - EDIT / HAPUS PAKET
    # ======================================
    with tab3:

        st.subheader("Edit atau Hapus Paket")

        if not paket.empty and "paket_id" in paket.columns:

            daftar_id = paket["paket_id"].astype(str).tolist()

            pilihan_id = st.selectbox(
                "Pilih Paket",
                daftar_id,
                format_func=lambda x: str(
                    paket.loc[
                        paket["paket_id"].astype(str) == x,
                        "nama_paket"
                    ].iloc[0]
                )
            )

            item = paket[
                paket["paket_id"].astype(str) == pilihan_id
            ].iloc[0]

            st.markdown("**Edit Informasi Paket**")

            with st.form("form_edit_paket"):

                nama_edit = st.text_input(
                    "Nama Paket",
                    value=str(item.get("nama_paket", ""))
                )

                # ======================================
                # HARGA
                # ======================================
                harga_lama = pd.to_numeric(
                    item.get("harga", 0),
                    errors="coerce"
                )

                harga_lama = (
                    0 if pd.isna(harga_lama)
                    else int(harga_lama)
                )

                harga_edit = st.text_input(
                    "Harga Paket (Rp)",
                    value=str(harga_lama),
                    placeholder="Contoh: 150000"
                )

                # ======================================
                # DURASI
                # ======================================
                durasi_lama = pd.to_numeric(
                    item.get("durasi_menit", 60),
                    errors="coerce"
                )

                durasi_lama = (
                    int(durasi_lama)
                    if pd.notna(durasi_lama)
                    else 60
                )

                daftar_durasi = [
                    "60 Menit",
                    "90 Menit"
                ]

                durasi_edit = st.selectbox(
                    "Durasi Belajar",
                    daftar_durasi,
                    index=(
                        daftar_durasi.index(
                            f"{durasi_lama} Menit"
                        )
                        if f"{durasi_lama} Menit" in daftar_durasi
                        else 0
                    )
                )

                # ======================================
                # JENIS KELAS
                # ======================================
                daftar_jenis = [
                    "Private",
                    "Semi-Private",
                    "Reguler"
                ]

                jenis_lama = str(
                    item.get("jenis_paket", "Private")
                )

                jenis_edit = st.selectbox(
                    "Jenis Paket",
                    daftar_jenis,
                    index=(
                        daftar_jenis.index(jenis_lama)
                        if jenis_lama in daftar_jenis
                        else 0
                    )
                )

                # ======================================
                # KETERANGAN
                # ======================================
                deskripsi_edit = st.text_area(
                    "Keterangan Paket",
                    value=(
                        ""
                        if pd.isna(item.get("deskripsi"))
                        else str(item.get("deskripsi"))
                    )
                )

                # ======================================
                # STATUS
                # ======================================
                daftar_status = [
                    "Aktif",
                    "Nonaktif"
                ]

                status_lama = str(
                    item.get("status", "Aktif")
                )

                status_edit = st.selectbox(
                    "Status Paket",
                    daftar_status,
                    index=(
                        daftar_status.index(status_lama)
                        if status_lama in daftar_status
                        else 0
                    )
                )

                update = st.form_submit_button(
                    "Simpan Perubahan",
                    use_container_width=True
                )

            # ======================================
            # PROSES SIMPAN EDIT
            # ======================================
            if update:

                if not nama_edit.strip():

                    st.error(
                        "Nama paket tidak boleh kosong."
                    )

                else:

                    try:

                        harga_bersih = int(
                            harga_edit.replace("Rp", "")
                            .replace(".", "")
                            .replace(",", "")
                            .replace(" ", "")
                        )

                        if harga_bersih <= 0:

                            st.error(
                                "Harga paket harus lebih dari 0."
                            )

                        else:
                            download_database()
                            wb = load_workbook(DB_PATH)
                            ws = wb["paket"]

                            headers = [
                                cell.value for cell in ws[1]
                            ]

                            posisi = {
                                nama: index + 1
                                for index, nama in enumerate(headers)
                            }

                            for nomor_baris in range(
                                2,
                                ws.max_row + 1
                            ):

                                if str(
                                    ws.cell(
                                        nomor_baris,
                                        posisi["paket_id"]
                                    ).value
                                ) == pilihan_id:

                                    perubahan = {
                                        "nama_paket": nama_edit.strip(),
                                        "durasi_menit": int(
                                            durasi_edit.split()[0]
                                        ),
                                        "jenis_paket": jenis_edit,
                                        "harga": harga_bersih,
                                        "deskripsi": deskripsi_edit.strip(),
                                        "status": status_edit
                                    }

                                    for kolom, nilai in perubahan.items():

                                        if kolom in posisi:

                                            ws.cell(
                                                nomor_baris,
                                                posisi[kolom]
                                            ).value = nilai

                                    break

                            wb.save(DB_PATH)
                            wb.close()
                            upload_database()

                            st.cache_data.clear()

                            st.success(
                                "Paket berhasil diperbarui."
                            )

                            st.rerun()

                    except ValueError:

                        st.error(
                            "Harga harus berupa angka. Contoh: 150000"
                        )

                    except Exception as e:

                        st.error(
                            f"Gagal memperbarui paket: {e}"
                        )

            # ======================================
            # PROSES HAPUS PAKET
            # ======================================
            st.markdown("---")
            st.markdown("**Hapus Paket**")

            konfirmasi_hapus = st.checkbox(
                f"Saya yakin ingin menghapus paket {item.get('nama_paket', pilihan_id)}",
                key="konfirmasi_hapus_paket"
            )

            if st.button(
                "Hapus Paket",
                type="primary",
                use_container_width=True,
                disabled=not konfirmasi_hapus
            ):

                try:
                    download_database()
                    wb = load_workbook(DB_PATH)
                    ws = wb["paket"]

                    headers = [
                        cell.value for cell in ws[1]
                    ]

                    kolom_id = headers.index("paket_id") + 1

                    for nomor_baris in range(
                        2,
                        ws.max_row + 1
                    ):

                        if str(
                            ws.cell(
                                nomor_baris,
                                kolom_id
                            ).value
                        ) == pilihan_id:

                            ws.delete_rows(nomor_baris, 1)
                            break

                    wb.save(DB_PATH)
                    wb.close()
                    upload_database()

                    st.cache_data.clear()

                    st.success(
                        "Paket berhasil dihapus."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Gagal menghapus paket: {e}"
                    )

        else:

            st.info(
                "Belum ada paket yang bisa diedit atau dihapus."
            )


# MENU ADMIN LAINNYA
else:

    daftar_menu_admin = [
        "Dashboard",
        "Verifikasi Pendaftaran",
        "Pendaftaran",
        "Daftar Murid",
        "Pendaftaran Tutor",
        "Data Tutor",
        "Absensi Murid",
        "Absensi Tutor",
        "Paket Belajar",
    ]

    if menu in daftar_menu_admin:

        if not st.session_state.admin_login:
            st.session_state.menu_aktif = "Beranda"
            st.rerun()

        else:
            st.markdown(
                f'<div class="main-title">{menu}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="subtitle">'
                'Sistem Administrasi Bimbingan Belajar Assisten Belajar'
                '</div>',
                unsafe_allow_html=True
            )

            st.info(f"Halaman {menu} siap dibangun.")

    elif menu not in ["Login Admin", "Login Tutor"]:
        st.session_state.menu_aktif = "Beranda"
        st.rerun()
