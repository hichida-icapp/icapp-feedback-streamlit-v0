import io
import streamlit as st
import dropbox

# 1ページPDFを画像として表示（ChromeのPDF埋め込みブロック回避）
import fitz  # PyMuPDF
from PIL import Image

st.set_page_config(page_title="Dropbox PDF Viewer", layout="wide")
st.title("PDFビューアー （iCaPP Feed back Sheet）")


def get_dbx():
    app_key = st.secrets["DROPBOX_APP_KEY"]
    app_secret = st.secrets["DROPBOX_APP_SECRET"]
    refresh_token = st.secrets["DROPBOX_REFRESH_TOKEN"]

    return dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )


def list_pdfs_in_folder(dbx: dropbox.Dropbox, folder_path: str):
    # 直下だけ（再帰しない）
    res = dbx.files_list_folder(folder_path, recursive=False)

    entries = []
    for e in res.entries:
        if isinstance(e, dropbox.files.FileMetadata) and e.name.lower().endswith(".pdf"):
            entries.append(e)

    # nameでソート
    entries.sort(key=lambda x: x.name)
    return entries


def download_file_bytes(dbx: dropbox.Dropbox, path_lower: str):
    md, resp = dbx.files_download(path_lower)
    return resp.content


def show_pdf_first_page_as_image(pdf_bytes: bytes, zoom: float = 2.0):
    """PDFの1ページ目だけを画像化して表示（1ページ前提）"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png")))

    st.image(img, use_container_width=True)


folder_path = st.text_input(
    "Dropboxフォルダパス（直下のPDFを一覧表示）",
    value="",
    placeholder=" /PDF 　を入力してください．",
)

if folder_path:
    dbx = get_dbx()

    with st.spinner("PDF一覧を取得中..."):
        pdfs = list_pdfs_in_folder(dbx, folder_path)

    if not pdfs:
        st.warning("PDFが見つかりませんでした（フォルダパスと権限を確認）。")
        st.stop()

    name_to_entry = {e.name: e for e in pdfs}
    selected_name = st.selectbox("表示するPDF", list(name_to_entry.keys()))
    entry = name_to_entry[selected_name]

    with st.spinner("PDFを取得中..."):
        pdf_bytes = download_file_bytes(dbx, entry.path_lower)

    st.download_button(
        "ダウンロード",
        data=pdf_bytes,
        file_name=selected_name,
        mime="application/pdf",
    )

    show_pdf_first_page_as_image(pdf_bytes)