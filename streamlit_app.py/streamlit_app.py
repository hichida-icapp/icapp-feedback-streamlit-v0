import io
import base64
import streamlit as st
import dropbox

st.set_page_config(page_title="Dropbox PDF Viewer", layout="wide")
st.title("Dropbox PDFビューア（リフレッシュトークン）")


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


def show_pdf_bytes(pdf_bytes: bytes):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.components.v1.html(
        f"""
        <iframe
            src=\"data:application/pdf;base64,{b64}\"
            width=\"100%\"
            height=\"900\"
            style=\"border: none;\"></iframe>
        """,
        height=900,
        scrolling=True,
    )


folder_path = st.text_input(
    "Dropboxフォルダパス（直下のPDFを一覧表示）",
    value="",
    placeholder="例: /Apps/StreamlitCloud_99/PDF",
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

    show_pdf_bytes(pdf_bytes)