import os
import json
import time
import base64
import mimetypes
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps

# 0. 画面基本設定
st.set_page_config(
    page_title="校内ストリートビュー",
    page_icon="🏫",
    layout="wide"
)

# 1. 保存用ファイル・フォルダの設定（app.pyのあるフォルダを基準に固定）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATA_FILE = os.path.join(BASE_DIR, "map_data.json")

# 2. 初期データ構造の定義
INITIAL_MAP_DATA = {
    "entrance_N": {
        "title": "正門（北向き - 校舎入口）",
        "image": "https://picsum.photos/id/1018/800/450",
        "ar_info": "📍 正面：昇降口 / 右手：自転車置き場"
    },
    "entrance_E": {
        "title": "正門（東向き - 体育館方面）",
        "image": "https://picsum.photos/id/1015/800/450",
        "ar_info": "📍 東校舎・体育館エリア"
    },
    "entrance_S": {
        "title": "正門（南向き - バス停方面）",
        "image": "https://picsum.photos/id/1025/800/450",
        "ar_info": "📍 バス停・駅方面（校外）"
    },
    "entrance_W": {
        "title": "正門（西向き - グラウンド）",
        "image": "https://picsum.photos/id/1040/800/450",
        "ar_info": "📍 グラウンド・テニスコート"
    },
    "hallway_1f_N": {
        "title": "1階中央廊下（北向き）",
        "image": "https://picsum.photos/id/1019/800/450",
        "ar_info": "📍 左手：1-A教室 / 右手：職員室"
    }
}

# 3. JSONファイル読み書き関数
def load_map_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_map_data(INITIAL_MAP_DATA)
    return INITIAL_MAP_DATA

def save_map_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# アップロード画像の最適化保存関数（向き補正・リサイズ・キャッシュ回避）
def save_uploaded_image(uploaded_file, node_id):
    timestamp = int(time.time() * 1000)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(node_id)) or "spot"
    filename = f"{safe_id}_{timestamp}.jpg"
    save_path = os.path.join(UPLOAD_DIR, filename)

    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # 横幅最大1280pxに縮小して表示負荷を軽減
    max_width = 1280
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    img.save(save_path, format="JPEG", quality=85)
    return os.path.join("uploaded_images", filename)

# ローカル画像パスをHTML表示用のBase64データURLに変換する関数
def get_image_src(image_path):
    if not image_path:
        return ""
    if image_path.startswith(("http://", "https://", "data:")):
        return image_path

    candidates = [
        image_path,
        os.path.join(BASE_DIR, image_path),
        os.path.join(UPLOAD_DIR, os.path.basename(image_path))
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.isfile(path):
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type:
                mime_type = "image/jpeg"
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
    return ""

# セッション状態の初期化
if "map_data" not in st.session_state:
    st.session_state["map_data"] = load_map_data()
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

map_data = st.session_state["map_data"]

# 4. サイドバーによるページ切り替え
st.sidebar.title("🏫 校内ビュー管理")
page = st.sidebar.radio("機能を選択", ["🧭 ナビゲーション", "✏️ データ編集・画像登録"])

# ==========================================
# ページ1: ナビゲーション画面（リロードなしで画像のみ切り替え）
# ==========================================
if page == "🧭 ナビゲーション":
    st.title("🏫 校内ストリートビュー")

    slides = []
    for node_id, node in map_data.items():
        img_src = get_image_src(node.get("image", ""))
        if img_src:
            slides.append({
                "id": node_id,
                "title": node.get("title") or node_id,
                "ar_info": node.get("ar_info", ""),
                "image": img_src
            })

    if slides:
        slides_json = json.dumps(slides, ensure_ascii=False)
        show_arrows = "flex" if len(slides) > 1 else "none"

        viewer_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: transparent;
            }}
            .viewer-wrapper {{
                max-width: 800px;
                margin: 0 auto;
            }}
            .header-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }}
            .node-title {{
                font-size: 22px;
                font-weight: 600;
                color: #1f2937;
                margin: 0;
            }}
            .page-counter {{
                font-size: 14px;
                color: #6b7280;
                background: #f3f4f6;
                padding: 4px 10px;
                border-radius: 12px;
            }}
            .ar-box {{
                background-color: #e8f4fd;
                color: #0c5460;
                padding: 12px 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                font-size: 15px;
            }}
            .overlay-container {{
                position: relative;
                width: 100%;
                background-color: #111827;
                border-radius: 8px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .overlay-container img {{
                width: 100%;
                max-height: 480px;
                object-fit: contain;
                display: block;
                user-select: none;
            }}
            .arrow-overlay-btn {{
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #888888;
                border-radius: 50%;
                width: 52px;
                height: 52px;
                font-size: 26px;
                font-weight: bold;
                display: {show_arrows};
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.25);
                transition: background-color 0.15s, border-color 0.15s, transform 0.15s;
                user-select: none;
                z-index: 10;
            }}
            .arrow-overlay-btn:hover {{
                background-color: #f0f0f0;
                border-color: #444444;
                transform: translateY(-50%) scale(1.1);
            }}
            .arrow-overlay-btn:active {{
                transform: translateY(-50%) scale(0.95);
            }}
            .arrow-btn-left {{
                left: 15px;
            }}
            .arrow-btn-right {{
                right: 15px;
            }}
        </style>
        </head>
        <body>
            <div class="viewer-wrapper">
                <div class="header-row">
                    <h2 id="node-title" class="node-title"></h2>
                    <span id="page-counter" class="page-counter"></span>
                </div>
                <div id="ar-info" class="ar-box"></div>
                <div class="overlay-container">
                    <img id="view-image" src="" alt="校内ビュー" />
                    <button type="button" class="arrow-overlay-btn arrow-btn-left" onclick="prevSlide()" title="前の画像">←</button>
                    <button type="button" class="arrow-overlay-btn arrow-btn-right" onclick="nextSlide()" title="次の画像">→</button>
                </div>
            </div>

            <script>
                const slides = {slides_json};
                let currentIndex = 0;

                function renderSlide() {{
                    const item = slides[currentIndex];
                    document.getElementById("node-title").textContent = item.title;
                    document.getElementById("page-counter").textContent = (currentIndex + 1) + " / " + slides.length;
                    
                    const arBox = document.getElementById("ar-info");
                    if (item.ar_info) {{
                        arBox.style.display = "block";
                        arBox.textContent = "💡 ARガイド: " + item.ar_info;
                    }} else {{
                        arBox.style.display = "none";
                    }}

                    document.getElementById("view-image").src = item.image;
                }}

                function prevSlide() {{
                    currentIndex = (currentIndex - 1 + slides.length) % slides.length;
                    renderSlide();
                }}

                function nextSlide() {{
                    currentIndex = (currentIndex + 1) % slides.length;
                    renderSlide();
                }}

                document.addEventListener("keydown", function(e) {{
                    if (slides.length <= 1) return;
                    if (e.key === "ArrowLeft") prevSlide();
                    if (e.key === "ArrowRight") nextSlide();
                }});

                renderSlide();
            </script>
        </body>
        </html>
        """

        components.html(viewer_html, height=620)
    else:
        st.warning("表示できる地点がありません。『データ編集・画像登録』ページから画像を登録してください。")

    if st.sidebar.button("🔄 最初の画像に戻る"):
        st.rerun()

# ==========================================
# ページ2: データ編集・画像登録画面
# ==========================================
elif page == "✏️ データ編集・画像登録":
    st.title("✏️ マップデータの編集・画像登録")
    st.write("各地点のタイトル・案内テキスト・画像を登録および削除できます。ナビゲーション画面では登録順に切り替わります。")

    node_list = list(map_data.keys())
    selected_option = st.selectbox("編集する地点を選択（または新規作成）", ["➕ 新しい地点を追加"] + node_list)

    if selected_option == "➕ 新しい地点を追加":
        default_new_id = f"spot_{len(node_list) + 1}"
        while default_new_id in map_data:
            default_new_id = f"spot_{int(time.time())}"
        target_id = st.text_input("地点ID（英数字で入力 例: library_1f_N）", value=default_new_id)
        target_node = {
            "title": "",
            "image": "",
            "ar_info": ""
        }
    else:
        target_id = selected_option
        target_node = map_data[target_id]

    st.write("---")

    new_title = st.text_input("場所のタイトル", value=target_node.get("title", ""), key=f"title_{target_id}")
    new_ar_info = st.text_input("ARガイドテキスト", value=target_node.get("ar_info", ""), key=f"ar_{target_id}")

    st.subheader("🖼️ 画像の変更")
    current_saved_image = target_node.get("image", "")

    uploaded_file = st.file_uploader(
        "新しい写真ファイルをアップロード (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        key=f"file_{target_id}_{st.session_state['uploader_version']}"
    )

    display_image_path = current_saved_image
    if uploaded_file is not None:
        display_image_path = save_uploaded_image(uploaded_file, target_id)
        st.info("🆕 新しい画像を選択中です。下の「保存・変更する」ボタンを押すと確定します。")

    if display_image_path:
        img_for_st = display_image_path
        if not img_for_st.startswith(("http://", "https://")):
            abs_candidate = os.path.join(BASE_DIR, img_for_st)
            if os.path.exists(abs_candidate):
                img_for_st = abs_candidate
        if img_for_st.startswith(("http://", "https://")) or os.path.exists(img_for_st):
            st.image(img_for_st, caption="現在の画像プレビュー", width=350)
        else:
            st.warning("画像ファイルが見つかりません。新しい画像をアップロードしてください。")

    st.write("---")

    col_btn_save, col_btn_del = st.columns([3, 1])

    # 保存ボタン
    with col_btn_save:
        if st.button("💾 この内容で保存・変更する", type="primary", key=f"save_{target_id}", use_container_width=True):
            clean_id = target_id.strip()
            if not clean_id:
                st.error("地点IDを入力してください。")
            else:
                st.session_state["map_data"][clean_id] = {
                    "title": new_title,
                    "image": display_image_path,
                    "ar_info": new_ar_info
                }
                save_map_data(st.session_state["map_data"])
                st.session_state["uploader_version"] += 1
                st.toast("✅ 保存しました！")
                st.rerun()

    # 地点削除ボタン
    with col_btn_del:
        if selected_option != "➕ 新しい地点を追加":
            if st.button("🗑️ この地点を削除", key=f"del_{target_id}", use_container_width=True):
                st.session_state["map_data"].pop(target_id, None)
                save_map_data(st.session_state["map_data"])
                st.toast(f"🗑️ 地点『{target_id}』を削除しました")
                st.rerun()