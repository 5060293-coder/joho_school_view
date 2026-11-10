import os
import json
import streamlit as st
from PIL import Image

# 0. 画面基本設定
st.set_page_config(
    page_title="校内ストリートビュー",
    page_icon="🏫",
    layout="wide"
)

# 1. 保存用ファイル・フォルダの設定
UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
DATA_FILE = "map_data.json"

# 2. 初期データ構造の定義
INITIAL_MAP_DATA = {
    "entrance_N": {
        "title": "正門（北向き - 校舎入口）",
        "image": "https://picsum.photos/id/1018/800/450",
        "ar_info": "📍 正面：昇降口 / 右手：自転車置き場",
        "forward": "hallway_1f_N",
        "left": "entrance_W",
        "right": "entrance_E",
        "uturn": "entrance_S"
    },
    "entrance_E": {
        "title": "正門（東向き - 体育館方面）",
        "image": "https://picsum.photos/id/1015/800/450",
        "ar_info": "📍 東校舎・体育館エリア",
        "forward": None,
        "left": "entrance_N",
        "right": "entrance_S",
        "uturn": "entrance_W"
    },
    "entrance_S": {
        "title": "正門（南向き - バス停方面）",
        "image": "https://picsum.photos/id/1025/800/450",
        "ar_info": "📍 バス停・駅方面（校外）",
        "forward": None,
        "left": "entrance_E",
        "right": "entrance_W",
        "uturn": "entrance_N"
    },
    "entrance_W": {
        "title": "正門（西向き - グラウンド）",
        "image": "https://picsum.photos/id/1040/800/450",
        "ar_info": "📍 グラウンド・テニスコート",
        "forward": None,
        "left": "entrance_S",
        "right": "entrance_N",
        "uturn": "entrance_E"
    },
    "hallway_1f_N": {
        "title": "1階中央廊下（北向き）",
        "image": "https://picsum.photos/id/1019/800/450",
        "ar_info": "📍 左手：1-A教室 / 右手：職員室",
        "forward": None,
        "left": None,
        "right": None,
        "uturn": "entrance_S"
    }
}

# 3. JSONファイル読み書き関数（永続化機能）
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

# セッション状態の読み込み
if "map_data" not in st.session_state:
    st.session_state["map_data"] = load_map_data()

map_data = st.session_state["map_data"]

# 4. サイドバーによるページ切り替え
st.sidebar.title("🏫 校内ビュー管理")
page = st.sidebar.radio("機能を選択", ["🧭 ナビゲーション", "✏️ データ編集・画像登録"])

# ==========================================
# ページ1: ナビゲーション画面
# ==========================================
if page == "🧭 ナビゲーション":
    
    current_id = st.query_params.get("node", "entrance_N")
    
    if current_id not in map_data:
        if map_data:
            current_id = list(map_data.keys())[0]
        else:
            current_id = "entrance_N"
        st.query_params["node"] = current_id
        
    current_node = map_data.get(current_id, {})

    st.title("🏫 校内ストリートビュー")
    if current_node:
        st.subheader(current_node.get("title", ""))
        st.info(f"💡 ARガイド: {current_node.get('ar_info', '')}")

        # CSSスタイルの定義（白背景・灰色の枠線・端固定配置）
        st.markdown("""
            <style>
            .overlay-container {
                position: relative;
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
            }
            .overlay-container img {
                width: 100%;
                border-radius: 8px;
                display: block;
            }
            .arrow-overlay-btn {
                position: absolute;
                background-color: #ffffff;
                color: #333333 !important;
                border: 2px solid #888888;
                border-radius: 50%;
                width: 52px;
                height: 52px;
                font-size: 26px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.25);
                transition: all 0.2s ease-in-out;
                text-decoration: none !important;
                z-index: 10;
            }
            .arrow-overlay-btn:hover {
                background-color: #f0f0f0;
                border-color: #444444;
            }
            /* 上下左右の端固定位置 */
            .arrow-btn-forward {
                top: 15px;
                left: 50%;
                transform: translateX(-50%);
            }
            .arrow-btn-forward:hover {
                transform: translateX(-50%) scale(1.1);
            }
            .arrow-btn-uturn {
                bottom: 15px;
                left: 50%;
                transform: translateX(-50%);
            }
            .arrow-btn-uturn:hover {
                transform: translateX(-50%) scale(1.1);
            }
            .arrow-btn-left {
                top: 50%;
                left: 15px;
                transform: translateY(-50%);
            }
            .arrow-btn-left:hover {
                transform: translateY(-50%) scale(1.1);
            }
            .arrow-btn-right {
                top: 50%;
                right: 15px;
                transform: translateY(-50%);
            }
            .arrow-btn-right:hover {
                transform: translateY(-50%) scale(1.1);
            }
            </style>
        """, unsafe_allow_html=True)

        _, img_center, _ = st.columns([1, 3, 1])
        
        with img_center:
            buttons_html = ""
            arrow_configs = [
                ("forward", "↑", current_node.get("forward"), "arrow-btn-forward"),
                ("uturn", "↓", current_node.get("uturn"), "arrow-btn-uturn"),
                ("left", "←", current_node.get("left"), "arrow-btn-left"),
                ("right", "→", current_node.get("right"), "arrow-btn-right")
            ]

            for key, arrow_symbol, target, class_name in arrow_configs:
                if target is not None and target in map_data:
                    buttons_html += f'<a href="?node={target}" target="_self" class="arrow-overlay-btn {class_name}" title="{key}">{arrow_symbol}</a>'

            html_str = f'<div class="overlay-container"><img src="{current_node.get("image", "")}" />{buttons_html}</div>'
            st.markdown(html_str, unsafe_allow_html=True)
    else:
        st.warning("登録されている地点がありません。『データ編集・画像登録』ページから追加してください。")

    if st.sidebar.button("🔄 スタート位置に戻る"):
        st.query_params["node"] = "entrance_N"
        st.rerun()

# ==========================================
# ページ2: データ編集・画像登録画面
# ==========================================
elif page == "✏️ データ編集・画像登録":
    st.title("✏️ マップデータの編集・画像登録")
    st.write("各地点の画像や案内テキスト、および**上下左右の移動先**を設定・削除できます。")

    node_list = list(map_data.keys())
    selected_option = st.selectbox("編集する地点を選択（または新規作成）", ["➕ 新しい地点を追加"] + node_list)

    if selected_option == "➕ 新しい地点を追加":
        target_id = st.text_input("地点ID（英数字で入力 例: library_1f_N）", value="")
        target_node = {
            "title": "",
            "image": "",
            "ar_info": "",
            "forward": None,
            "left": None,
            "right": None,
            "uturn": None
        }
    else:
        target_id = selected_option
        target_node = map_data[target_id]

    if target_id or selected_option != "➕ 新しい地点を追加":
        st.write("---")
        
        new_title = st.text_input("場所のタイトル", value=target_node.get("title", ""), key=f"title_{target_id}")
        new_ar_info = st.text_input("ARガイドテキスト", value=target_node.get("ar_info", ""), key=f"ar_{target_id}")

        st.subheader("🖼️ 画像の変更")
        image_path = target_node.get("image", "")
        if image_path:
            st.image(image_path, caption="現在の画像", width=300)

        uploaded_file = st.file_uploader("新しい写真ファイルをアップロード (JPG / PNG)", type=["jpg", "jpeg", "png"], key=f"file_{target_id}")
        
        if uploaded_file is not None:
            save_path = os.path.join(UPLOAD_DIR, f"{target_id}_{uploaded_file.name}")
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_path = save_path
            st.success(f"画像をアップロードしました: {save_path}")

        st.subheader("🧭 各方向（上下左右）の移動先設定")
        
        all_ids = [None] + list(map_data.keys())
        if target_id not in all_ids and target_id != "":
            all_ids.append(target_id)

        col_f, col_u, col_l, col_r = st.columns(4)
        
        with col_f:
            st.markdown("#### ↑ 上 (前進)")
            new_forward = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("forward")) if target_node.get("forward") in all_ids else 0, key=f"edit_fwd_{target_id}")

        with col_u:
            st.markdown("#### ↓ 下 (Uターン)")
            new_uturn = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("uturn")) if target_node.get("uturn") in all_ids else 0, key=f"edit_uturn_{target_id}")

        with col_l:
            st.markdown("#### ← 左 (左折)")
            new_left = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("left")) if target_node.get("left") in all_ids else 0, key=f"edit_left_{target_id}")

        with col_r:
            st.markdown("#### → 右 (右折)")
            new_right = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("right")) if target_node.get("right") in all_ids else 0, key=f"edit_right_{target_id}")

        # データ更新用構造
        updated_node_data = {
            "title": new_title,
            "image": image_path,
            "ar_info": new_ar_info,
            "forward": new_forward,
            "left": new_left,
            "right": new_right,
            "uturn": new_uturn
        }
        
        if target_id and target_id != "":
            st.session_state["map_data"][target_id] = updated_node_data
            save_map_data(st.session_state["map_data"])

        st.subheader("🎯 移動先設定のプレビュー")
        
        # プレビュー用スタイル
        st.markdown("""
            <style>
            .preview-container {
                position: relative;
                width: 100%;
                max-width: 500px;
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
                width: 38px;
                height: 38px;
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
                z-index: 10;
            }
            .p-btn-forward { top: 10px; left: 50%; transform: translateX(-50%); }
            .p-btn-uturn { bottom: 10px; left: 50%; transform: translateX(-50%); }
            .p-btn-left { top: 50%; left: 10px; transform: translateY(-50%); }
            .p-btn-right { top: 50%; right: 10px; transform: translateY(-50%); }
            </style>
        """, unsafe_allow_html=True)

        preview_html = ""
        preview_arrows = [
            (new_forward, "↑", "p-btn-forward"),
            (new_uturn, "↓", "p-btn-uturn"),
            (new_left, "←", "p-btn-left"),
            (new_right, "→", "p-btn-right")
        ]

        for target, symbol, class_name in preview_arrows:
            if target is not None:
                preview_html += f'<div class="preview-arrow-btn {class_name}">{symbol}</div>'

        if image_path:
            preview_container = f'<div class="preview-container"><img src="{image_path}" />{preview_html}</div>'
            st.markdown(preview_container, unsafe_allow_html=True)

        st.write("---")

        col_btn_save, col_btn_del = st.columns([3, 1])

        # 保存ボタン
        with col_btn_save:
            if st.button("💾 この内容で保存・変更する", type="primary", key=f"save_{target_id}", use_container_width=True):
                if not target_id:
                    st.error("地点IDを入力してください。")
                else:
                    st.session_state["map_data"][target_id] = updated_node_data
                    save_map_data(st.session_state["map_data"])
                    st.success("✅ 保存しました！")
                    st.toast("✅ 保存しました！")

        # 地点削除ボタン
        with col_btn_del:
            if selected_option != "➕ 新しい地点を追加":
                if st.button("🗑️ この地点を削除", key=f"del_{target_id}", use_container_width=True):
                    for nid, node in st.session_state["map_data"].items():
                        for k in ["forward", "left", "right", "uturn"]:
                            if node.get(k) == target_id:
                                node[k] = None

                    st.session_state["map_data"].pop(target_id, None)
                    save_map_data(st.session_state["map_data"])
                    st.toast(f"🗑️ 地点『{target_id}』を削除しました")
                    st.success(f"🗑️ 地点『{target_id}』を削除しました！")
                    st.rerun()