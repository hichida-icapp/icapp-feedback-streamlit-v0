import re
import base64
import streamlit as st
import gdown

st.set_page_config(page_title="Drive PDF Viewer", layout="wide")
st.title("Google Drive（公開フォルダ）PDFビューア")


def extract_folder_id(folder_url: str):
    # 例: https://drive.google.com/drive/folders/<FOLDER_ID>?usp=sharing
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", folder_url)
    return m.group(1) if m else None


def show_pdf_bytes(pdf_bytes: bytes):
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    html = f"""
    <iframe
        src=\"data:application/pdf;base64,{b64}\"
        width=\"100%\"
        height=\"900\"
        style=\"border: none;\">
    </iframe>
    """
    st.components.v1.html(html, height=900, scrolling=True)


# --- 設定の外出し（別ファイル②：.streamlit/secrets.toml）---
# Streamlit Community Cloud では Secrets が標準で使えます。
# ローカルでも同じ構成で動きます。
#
# .streamlit/secrets.toml（例）
# DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/<FOLDER_ID>?usp=sharing"
DEFAULT_FOLDER_URL = st.secrets.get("DRIVE_FOLDER_URL", "")

folder_url = st.text_input(
    "Google DriveフォルダURL（公開）",
    value=DEFAULT_FOLDER_URL,
    placeholder="https://drive.google.com/drive/folders/...",
)

if folder_url:
    folder_id = extract_folder_id(folder_url)
    if not folder_id:
        st.error("フォルダURLからフォルダIDを抽出できませんでした。/folders/〜 の形式か確認してください。")
        st.stop()

    with st.spinner("フォルダ内のPDF一覧を取得中..."):
        # 公開フォルダ前提：use_cookies=False
        local_paths = gdown.download_folder(
            id=folder_id,
            quiet=True,
            use_cookies=False,
            remaining_ok=True,  # 途中で失敗しても残りを続行（環境差対策）
        )

    if not local_paths:
        st.warning("ファイルを取得できませんでした。フォルダが公開されているか確認してください。")
        st.stop()

    pdf_paths = [p for p in local_paths if isinstance(p, str) and p.lower().endswith(".pdf")]

    if not pdf_paths:
        st.warning("PDFが見つかりませんでした。")
        st.stop()

    # 表示名（ファイル名）だけにする
    name_to_path = {p.split("/")[-1]: p for p in pdf_paths}
    selected_name = st.selectbox("表示するPDF", sorted(name_to_path.keys()))
    selected_path = name_to_path[selected_name]

    with open(selected_path, "rb") as f:
        pdf_bytes = f.read()

    cols = st.columns([1, 1, 6])
    with cols[0]:
        st.download_button(
            "ダウンロード",
            data=pdf_bytes,
            file_name=selected_name,
            mime="application/pdf",
        )
    with cols[1]:
        st.caption(f"{len(pdf_bytes)/1024/1024:.2f} MB")

    show_pdf_bytes(pdf_bytes)