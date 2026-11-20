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

# 画面の余白を詰めて表示領域を広げるCSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 96%;
    }
    </style>
""", unsafe_allow_html=True)

# 1. 保存用ファイル・フォルダの設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATA_FILE = os.path.join(BASE_DIR, "map_data.json")
CONFIG_FILE = os.path.join(BASE_DIR, "app_config.json")

# 2. 初期データ構造の定義
INITIAL_MAP_DATA = {
    "entrance_N": {
        "title": "正門（北向き - 校舎入口）",
        "image": "https://picsum.photos/id/1018/1280/720",
        "left": "entrance_W",
        "forward": "hallway_1f_N",
        "uturn": "entrance_S",
        "right": "entrance_E"
    },
    "entrance_E": {
        "title": "正門（東向き - 体育館方面）",
        "image": "https://picsum.photos/id/1015/1280/720",
        "left": "entrance_N",
        "forward": None,
        "uturn": "entrance_W",
        "right": "entrance_S"
    },
    "entrance_S": {
        "title": "正門（南向き - バス停方面）",
        "image": "https://picsum.photos/id/1025/1280/720",
        "left": "entrance_E",
        "forward": None,
        "uturn": "entrance_N",
        "right": "entrance_W"
    },
    "entrance_W": {
        "title": "正門（西向き - グラウンド）",
        "image": "https://picsum.photos/id/1040/1280/720",
        "left": "entrance_S",
        "forward": None,
        "uturn": "entrance_E",
        "right": "entrance_N"
    },
    "hallway_1f_N": {
        "title": "1階中央廊下（北向き）",
        "image": "https://picsum.photos/id/1019/1280/720",
        "left": None,
        "forward": None,
        "uturn": "entrance_S",
        "right": None
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

# スタート位置設定の読み書き関数
def load_start_node(data):
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                start_id = cfg.get("start_node")
                if start_id and start_id in data:
                    return start_id
        except Exception:
            pass
    if "entrance_N" in data:
        return "entrance_N"
    return list(data.keys())[0] if data else ""

def save_start_node(node_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"start_node": node_id}, f, ensure_ascii=False, indent=2)

# アップロード画像の最適化保存関数
def save_uploaded_image(uploaded_file, node_id):
    timestamp = int(time.time() * 1000)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(node_id)) or "spot"
    filename = f"{safe_id}_{timestamp}.jpg"
    save_path = os.path.join(UPLOAD_DIR, filename)

    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    max_width = 1600
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

    img.save(save_path, format="JPEG", quality=88)
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
if "start_node" not in st.session_state:
    st.session_state["start_node"] = load_start_node(st.session_state["map_data"])
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0
if "reset_counter" not in st.session_state:
    st.session_state["reset_counter"] = 0

map_data = st.session_state["map_data"]

# スタート位置が削除等で存在しなくなっていた場合の補正
if map_data and st.session_state["start_node"] not in map_data:
    st.session_state["start_node"] = list(map_data.keys())[0]
    save_start_node(st.session_state["start_node"])

# 4. サイドバーによるページ切り替え
st.sidebar.title("🏫 校内ビュー管理")
page = st.sidebar.radio("機能を選択", ["🧭 ナビゲーション", "✏️ データ編集・画像登録"])

# ==========================================
# ページ1: ナビゲーション画面（大型表示＋全体画面対応）
# ==========================================
if page == "🧭 ナビゲーション":
    st.title("🏫 校内ストリートビュー")

    nodes_for_js = {}
    for node_id, node in map_data.items():
        nodes_for_js[node_id] = {
            "id": node_id,
            "title": node.get("title") or node_id,
            "image": get_image_src(node.get("image", "")),
            "left": node.get("left"),
            "forward": node.get("forward"),
            "uturn": node.get("uturn"),
            "right": node.get("right")
        }

    if nodes_for_js:
        start_id = st.session_state["start_node"]
        if start_id not in nodes_for_js:
            start_id = list(nodes_for_js.keys())[0]

        start_title = nodes_for_js[start_id]["title"]
        st.sidebar.caption(f"🚩 現在のスタート位置:\n**{start_title}** (`{start_id}`)")

        if st.sidebar.button("🔄 スタート位置に戻る"):
            st.session_state["reset_counter"] += 1
            st.rerun()

        nodes_json = json.dumps(nodes_for_js, ensure_ascii=False)
        start_id_json = json.dumps(start_id, ensure_ascii=False)
        reset_token = st.session_state["reset_counter"]

        viewer_html = f"""
        <!DOCTYPE html>
        <!-- reset_token: {reset_token} -->
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: transparent;
            }}
            .viewer-wrapper {{
                width: 100%;
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding: 0 4px;
            }}
            .node-title {{
                font-size: 24px;
                font-weight: 700;
                color: #1f2937;
                margin: 0;
            }}
            .node-badge {{
                font-size: 13px;
                color: #6b7280;
                background: #f3f4f6;
                padding: 4px 12px;
                border-radius: 12px;
                font-family: monospace;
            }}
            .overlay-container {{
                position: relative;
                width: 100%;
                height: 640px;
                background-color: #111827;
                border-radius: 10px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .overlay-container img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
                user-select: none;
            }}
            /* 全体画面（フルスクリーン）時のスタイル */
            .overlay-container:fullscreen,
            .overlay-container:-webkit-full-screen,
            .overlay-container.pseudo-fullscreen {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                max-width: none !important;
                max-height: none !important;
                background-color: #000000 !important;
                border-radius: 0 !important;
                z-index: 999999 !important;
            }}
            .overlay-container:fullscreen img,
            .overlay-container:-webkit-full-screen img,
            .overlay-container.pseudo-fullscreen img {{
                width: 100vw !important;
                height: 100vh !important;
                object-fit: contain !important;
            }}
            .no-image-msg {{
                color: #9ca3af;
                font-size: 16px;
            }}
            /* 画像左上のタイトルオーバーレイ（全体画面時にも場所名を表示） */
            .fs-title-badge {{
                position: absolute;
                top: 16px;
                left: 16px;
                background-color: rgba(0, 0, 0, 0.65);
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 600;
                z-index: 20;
                pointer-events: none;
                display: none;
            }}
            .overlay-container:fullscreen .fs-title-badge,
            .overlay-container:-webkit-full-screen .fs-title-badge,
            .overlay-container.pseudo-fullscreen .fs-title-badge {{
                display: block;
            }}
            /* 右上の全体画面切り替えボタン */
            .fullscreen-btn {{
                position: absolute;
                top: 16px;
                right: 16px;
                background-color: rgba(255, 255, 255, 0.92);
                color: #222222;
                border: 2px solid #888888;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.3);
                transition: background-color 0.15s, transform 0.15s;
                z-index: 25;
                user-select: none;
            }}
            .fullscreen-btn:hover {{
                background-color: #ffffff;
                border-color: #444444;
                transform: scale(1.04);
            }}
            /* 矢印ボタン（白背景・灰色の縁・上下左右の端固定） */
            .arrow-overlay-btn {{
                position: absolute;
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #888888;
                border-radius: 50%;
                width: 58px;
                height: 58px;
                font-size: 28px;
                font-weight: bold;
                display: none;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.35);
                transition: background-color 0.15s, border-color 0.15s, transform 0.15s;
                user-select: none;
                z-index: 20;
            }}
            .arrow-overlay-btn:hover {{
                background-color: #f0f0f0;
                border-color: #444444;
            }}
            .arrow-btn-left {{
                top: 50%;
                left: 18px;
                transform: translateY(-50%);
            }}
            .arrow-btn-left:hover {{
                transform: translateY(-50%) scale(1.1);
            }}
            .arrow-btn-forward {{
                top: 18px;
                left: 50%;
                transform: translateX(-50%);
            }}
            .arrow-btn-forward:hover {{
                transform: translateX(-50%) scale(1.1);
            }}
            .arrow-btn-uturn {{
                bottom: 18px;
                left: 50%;
                transform: translateX(-50%);
            }}
            .arrow-btn-uturn:hover {{
                transform: translateX(-50%) scale(1.1);
            }}
            .arrow-btn-right {{
                top: 50%;
                right: 18px;
                transform: translateY(-50%);
            }}
            .arrow-btn-right:hover {{
                transform: translateY(-50%) scale(1.1);
            }}
        </style>
        </head>
        <body>
            <div class="viewer-wrapper">
                <div class="header-row">
                    <h2 id="node-title" class="node-title"></h2>
                    <span id="node-id-badge" class="node-badge"></span>
                </div>
                <div id="fullscreen-target" class="overlay-container">
                    <div id="fs-title-badge" class="fs-title-badge"></div>
                    <button type="button" id="btn-fullscreen" class="fullscreen-btn" onclick="toggleFullscreen()">⛶ 全体画面</button>
                    <img id="view-image" src="" alt="校内ビュー" />
                    <div id="no-image" class="no-image-msg" style="display:none;">画像が未登録です</div>
                    <button type="button" id="btn-left" class="arrow-overlay-btn arrow-btn-left" title="左へ移動">←</button>
                    <button type="button" id="btn-forward" class="arrow-overlay-btn arrow-btn-forward" title="上（前）へ移動">↑</button>
                    <button type="button" id="btn-uturn" class="arrow-overlay-btn arrow-btn-uturn" title="下（後ろ）へ移動">↓</button>
                    <button type="button" id="btn-right" class="arrow-overlay-btn arrow-btn-right" title="右へ移動">→</button>
                </div>
            </div>

            <script>
                const nodes = {nodes_json};
                let currentId = {start_id_json};
                const container = document.getElementById("fullscreen-target");
                const fsBtn = document.getElementById("btn-fullscreen");

                function renderNode(nodeId) {{
                    const node = nodes[nodeId];
                    if (!node) return;
                    currentId = nodeId;

                    document.getElementById("node-title").textContent = node.title;
                    document.getElementById("fs-title-badge").textContent = node.title;
                    document.getElementById("node-id-badge").textContent = "ID: " + node.id;

                    const imgEl = document.getElementById("view-image");
                    const noImgEl = document.getElementById("no-image");
                    if (node.image) {{
                        imgEl.style.display = "block";
                        imgEl.src = node.image;
                        noImgEl.style.display = "none";
                    }} else {{
                        imgEl.style.display = "none";
                        imgEl.src = "";
                        noImgEl.style.display = "block";
                    }}

                    setupButton("btn-left", node.left);
                    setupButton("btn-forward", node.forward);
                    setupButton("btn-uturn", node.uturn);
                    setupButton("btn-right", node.right);
                }}

                function setupButton(btnId, targetId) {{
                    const btn = document.getElementById(btnId);
                    if (targetId && nodes[targetId]) {{
                        btn.style.display = "flex";
                        btn.onclick = function() {{
                            renderNode(targetId);
                        }};
                    }} else {{
                        btn.style.display = "none";
                        btn.onclick = null;
                    }}
                }}

                function updateFsButtonState(isFs) {{
                    fsBtn.textContent = isFs ? "✕ 元に戻す" : "⛶ 全体画面";
                }}

                function toggleFullscreen() {{
                    const isNativeFs = !!(document.fullscreenElement || document.webkitFullscreenElement);
                    const isPseudoFs = container.classList.contains("pseudo-fullscreen");

                    if (!isNativeFs && !isPseudoFs) {{
                        if (container.requestFullscreen) {{
                            container.requestFullscreen().then(() => {{
                                updateFsButtonState(true);
                            }}).catch(() => {{
                                container.classList.add("pseudo-fullscreen");
                                updateFsButtonState(true);
                            }});
                        }} else if (container.webkitRequestFullscreen) {{
                            container.webkitRequestFullscreen();
                            updateFsButtonState(true);
                        }} else {{
                            container.classList.add("pseudo-fullscreen");
                            updateFsButtonState(true);
                        }}
                    }} else {{
                        if (document.fullscreenElement) {{
                            document.exitFullscreen();
                        }} else if (document.webkitFullscreenElement) {{
                            document.webkitExitFullscreen();
                        }}
                        container.classList.remove("pseudo-fullscreen");
                        updateFsButtonState(false);
                    }}
                }}

                document.addEventListener("fullscreenchange", () => {{
                    updateFsButtonState(!!document.fullscreenElement);
                }});
                document.addEventListener("webkitfullscreenchange", () => {{
                    updateFsButtonState(!!document.webkitFullscreenElement);
                }});

                // キーボード操作（矢印キー移動・Fキーで全体画面・Escで解除）
                document.addEventListener("keydown", function(e) {{
                    const node = nodes[currentId];
                    if (!node) return;
                    if (e.key === "ArrowLeft" && node.left && nodes[node.left]) renderNode(node.left);
                    if (e.key === "ArrowUp" && node.forward && nodes[node.forward]) renderNode(node.forward);
                    if (e.key === "ArrowDown" && node.uturn && nodes[node.uturn]) renderNode(node.uturn);
                    if (e.key === "ArrowRight" && node.right && nodes[node.right]) renderNode(node.right);
                    if (e.key === "f" || e.key === "F") toggleFullscreen();
                    if (e.key === "Escape" && container.classList.contains("pseudo-fullscreen")) {{
                        container.classList.remove("pseudo-fullscreen");
                        updateFsButtonState(false);
                    }}
                }});

                renderNode(currentId);
            </script>
        </body>
        </html>
        """

        components.html(viewer_html, height=700)
    else:
        st.warning("登録されている地点がありません。『データ編集・画像登録』ページから追加してください。")

# ==========================================
# ページ2: データ編集・画像登録画面（スタート位置設定あり）
# ==========================================
elif page == "✏️ データ編集・画像登録":
    st.title("✏️ マップデータの編集・画像登録")
    st.write("スタート位置の設定、および各地点のタイトル・画像・**← ↑ ↓ → の移動先ID**を設定できます。")

    node_list = list(map_data.keys())

    # ------------------------------------------
    # スタート位置（初期地点）の設定セクション
    # ------------------------------------------
    if node_list:
        with st.container(border=True):
            st.subheader("🚩 スタート位置（最初に表示する地点）の設定")
            current_start = st.session_state["start_node"]
            if current_start not in node_list:
                current_start = node_list[0]

            col_start_sel, col_start_btn = st.columns([3, 1], vertical_alignment="bottom")
            with col_start_sel:
                selected_start = st.selectbox(
                    "スタート地点を選択",
                    node_list,
                    index=node_list.index(current_start),
                    format_func=lambda nid: f"{map_data[nid].get('title') or nid}  ({nid})",
                    key="select_start_node"
                )
            with col_start_btn:
                if st.button("🚩 スタート位置を保存", use_container_width=True):
                    st.session_state["start_node"] = selected_start
                    save_start_node(selected_start)
                    st.toast(f"🚩 スタート位置を『{selected_start}』に設定しました！")
                    st.rerun()

    st.write("---")

    # ------------------------------------------
    # 各地点の編集・新規作成セクション
    # ------------------------------------------
    selected_option = st.selectbox("編集する地点を選択（または新規作成）", ["➕ 新しい地点を追加"] + node_list)

    if selected_option == "➕ 新しい地点を追加":
        default_new_id = f"spot_{len(node_list) + 1}"
        while default_new_id in map_data:
            default_new_id = f"spot_{int(time.time())}"
        target_id = st.text_input("地点ID（英数字で入力 例: library_1f_N）", value=default_new_id)
        target_node = {
            "title": "",
            "image": "",
            "left": None,
            "forward": None,
            "uturn": None,
            "right": None
        }
    else:
        target_id = selected_option
        target_node = map_data[target_id]

    st.write("---")

    new_title = st.text_input("場所のタイトル", value=target_node.get("title", ""), key=f"title_{target_id}")

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

    st.subheader("🧭 各方向（← ↑ ↓ →）の移動先ID設定")

    all_ids = [None] + list(map_data.keys())
    clean_preview_id = target_id.strip()
    if clean_preview_id and clean_preview_id not in all_ids:
        all_ids.append(clean_preview_id)

    col_l, col_f, col_u, col_r = st.columns(4)

    with col_l:
        st.markdown("#### ← 左")
        cur_left = target_node.get("left")
        new_left = st.selectbox(
            "移動先ID",
            all_ids,
            index=all_ids.index(cur_left) if cur_left in all_ids else 0,
            key=f"edit_left_{target_id}"
        )

    with col_f:
        st.markdown("#### ↑ 上（前）")
        cur_fwd = target_node.get("forward")
        new_forward = st.selectbox(
            "移動先ID",
            all_ids,
            index=all_ids.index(cur_fwd) if cur_fwd in all_ids else 0,
            key=f"edit_fwd_{target_id}"
        )

    with col_u:
        st.markdown("#### ↓ 下（後ろ）")
        cur_uturn = target_node.get("uturn")
        new_uturn = st.selectbox(
            "移動先ID",
            all_ids,
            index=all_ids.index(cur_uturn) if cur_uturn in all_ids else 0,
            key=f"edit_uturn_{target_id}"
        )

    with col_r:
        st.markdown("#### → 右")
        cur_right = target_node.get("right")
        new_right = st.selectbox(
            "移動先ID",
            all_ids,
            index=all_ids.index(cur_right) if cur_right in all_ids else 0,
            key=f"edit_right_{target_id}"
        )

    # 画像と矢印配置のプレビュー表示
    preview_src = get_image_src(display_image_path)
    if preview_src:
        st.subheader("🎯 プレビュー")
        st.markdown("""
            <style>
            .preview-container {
                position: relative;
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
            }
            .preview-container img {
                width: 100%;
                border-radius: 8px;
                display: block;
            }
            .preview-arrow-btn {
                position: absolute;
                background-color: #ffffff;
                color: #333333;
                border: 2px solid #888888;
                border-radius: 50%;
                width: 42px;
                height: 42px;
                font-size: 20px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
                z-index: 10;
            }
            .p-btn-left { top: 50%; left: 12px; transform: translateY(-50%); }
            .p-btn-forward { top: 12px; left: 50%; transform: translateX(-50%); }
            .p-btn-uturn { bottom: 12px; left: 50%; transform: translateX(-50%); }
            .p-btn-right { top: 50%; right: 12px; transform: translateY(-50%); }
            </style>
        """, unsafe_allow_html=True)

        preview_html = ""
        preview_arrows = [
            (new_left, "←", "p-btn-left"),
            (new_forward, "↑", "p-btn-forward"),
            (new_uturn, "↓", "p-btn-uturn"),
            (new_right, "→", "p-btn-right")
        ]
        for target, symbol, class_name in preview_arrows:
            if target is not None:
                preview_html += f'<div class="preview-arrow-btn {class_name}">{symbol}</div>'

        preview_container = f'<div class="preview-container"><img src="{preview_src}" />{preview_html}</div>'
        st.markdown(preview_container, unsafe_allow_html=True)
    elif display_image_path:
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
                    "left": new_left,
                    "forward": new_forward,
                    "uturn": new_uturn,
                    "right": new_right
                }
                save_map_data(st.session_state["map_data"])
                if not st.session_state["start_node"] or st.session_state["start_node"] not in st.session_state["map_data"]:
                    st.session_state["start_node"] = clean_id
                    save_start_node(clean_id)
                st.session_state["uploader_version"] += 1
                st.toast("✅ 保存しました！")
                st.rerun()

    # 地点削除ボタン
    with col_btn_del:
        if selected_option != "➕ 新しい地点を追加":
            if st.button("🗑️ この地点を削除", key=f"del_{target_id}", use_container_width=True):
                for nid, node in st.session_state["map_data"].items():
                    for k in ["left", "forward", "uturn", "right"]:
                        if node.get(k) == target_id:
                            node[k] = None

                st.session_state["map_data"].pop(target_id, None)
                save_map_data(st.session_state["map_data"])

                # 削除された地点がスタート位置だった場合は残っている先頭地点へ更新
                if st.session_state["start_node"] == target_id:
                    remaining = list(st.session_state["map_data"].keys())
                    new_start = remaining[0] if remaining else ""
                    st.session_state["start_node"] = new_start
                    save_start_node(new_start)

                st.toast(f"🗑️ 地点『{target_id}』を削除しました")
                st.rerun()