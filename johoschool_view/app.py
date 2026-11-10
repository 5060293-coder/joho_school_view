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
        "uturn": "entrance_S",
        "pos": {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        }
    },
    "entrance_E": {
        "title": "正門（東向き - 体育館方面）",
        "image": "https://picsum.photos/id/1015/800/450",
        "ar_info": "📍 東校舎・体育館エリア",
        "forward": None,
        "left": "entrance_N",
        "right": "entrance_S",
        "uturn": "entrance_W",
        "pos": {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        }
    },
    "entrance_S": {
        "title": "正門（南向き - バス停方面）",
        "image": "https://picsum.photos/id/1025/800/450",
        "ar_info": "📍 バス停・駅方面（校外）",
        "forward": None,
        "left": "entrance_E",
        "right": "entrance_W",
        "uturn": "entrance_N",
        "pos": {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        }
    },
    "entrance_W": {
        "title": "正門（西向き - グラウンド）",
        "image": "https://picsum.photos/id/1040/800/450",
        "ar_info": "📍 グラウンド・テニスコート",
        "forward": None,
        "left": "entrance_S",
        "right": "entrance_N",
        "uturn": "entrance_E",
        "pos": {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        }
    },
    "hallway_1f_N": {
        "title": "1階中央廊下（北向き）",
        "image": "https://picsum.photos/id/1019/800/450",
        "ar_info": "📍 左手：1-A教室 / 右手：職員室",
        "forward": None,
        "left": None,
        "right": None,
        "uturn": "entrance_S",
        "pos": {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        }
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
        # 地点が削除されたなどの理由で存在しない場合は最初の地点に戻す
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
                transform: translate(-50%, -50%);
                background-color: rgba(30, 30, 30, 0.45);
                color: #ffffff !important;
                border: 1.5px solid rgba(255, 255, 255, 0.7);
                border-radius: 50%;
                width: 54px;
                height: 54px;
                font-size: 26px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0px 4px 10px rgba(0,0,0,0.25);
                backdrop-filter: blur(5px);
                transition: all 0.2s ease-in-out;
                text-decoration: none !important;
            }
            .arrow-overlay-btn:hover {
                background-color: rgba(0, 0, 0, 0.85);
                transform: translate(-50%, -50%) scale(1.15);
            }
            </style>
        """, unsafe_allow_html=True)

        _, img_center, _ = st.columns([1, 3, 1])
        
        with img_center:
            pos_data = current_node.get("pos", {
                "left": {"x": 15, "y": 50},
                "forward": {"x": 50, "y": 25},
                "right": {"x": 85, "y": 50},
                "uturn": {"x": 50, "y": 80}
            })

            buttons_html = ""
            arrow_configs = [
                ("left", "←", current_node.get("left")),
                ("forward", "↑", current_node.get("forward")),
                ("right", "→", current_node.get("right")),
                ("uturn", "↓", current_node.get("uturn"))
            ]

            for key, arrow_symbol, target in arrow_configs:
                if target is not None and target in map_data:
                    px = pos_data.get(key, {}).get("x", 50)
                    py = pos_data.get(key, {}).get("y", 50)
                    buttons_html += f'<a href="?node={target}" target="_self" class="arrow-overlay-btn" style="left: {px}%; top: {py}%;" title="{key}">{arrow_symbol}</a>'

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
    st.write("各地点の画像や案内テキスト、つながる移動先、および**矢印アイコン（← ↑ → ↓）の位置**を設定・削除できます。")

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
            "uturn": None,
            "pos": {
                "left": {"x": 15, "y": 50},
                "forward": {"x": 50, "y": 25},
                "right": {"x": 85, "y": 50},
                "uturn": {"x": 50, "y": 80}
            }
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

        st.subheader("🧭 各方向の移動先と【矢印（← ↑ → ↓）の位置（%）】設定")
        
        all_ids = [None] + list(map_data.keys())
        if target_id not in all_ids and target_id != "":
            all_ids.append(target_id)

        curr_pos = target_node.get("pos", {
            "left": {"x": 15, "y": 50},
            "forward": {"x": 50, "y": 25},
            "right": {"x": 85, "y": 50},
            "uturn": {"x": 50, "y": 80}
        })

        col_l, col_f, col_r, col_u = st.columns(4)
        
        with col_l:
            st.markdown("#### ← (左折)")
            new_left = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("left")) if target_node.get("left") in all_ids else 0, key=f"edit_left_{target_id}")
            left_x = st.slider("横位置 X (%)", 0, 100, curr_pos.get("left", {}).get("x", 15), key=f"lx_{target_id}")
            left_y = st.slider("縦位置 Y (%)", 0, 100, curr_pos.get("left", {}).get("y", 50), key=f"ly_{target_id}")

        with col_f:
            st.markdown("#### ↑ (前進)")
            new_forward = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("forward")) if target_node.get("forward") in all_ids else 0, key=f"edit_fwd_{target_id}")
            fwd_x = st.slider("横位置 X (%)", 0, 100, curr_pos.get("forward", {}).get("x", 50), key=f"fx_{target_id}")
            fwd_y = st.slider("縦位置 Y (%)", 0, 100, curr_pos.get("forward", {}).get("y", 25), key=f"fy_{target_id}")

        with col_r:
            st.markdown("#### → (右折)")
            new_right = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("right")) if target_node.get("right") in all_ids else 0, key=f"edit_right_{target_id}")
            right_x = st.slider("横位置 X (%)", 0, 100, curr_pos.get("right", {}).get("x", 85), key=f"rx_{target_id}")
            right_y = st.slider("縦位置 Y (%)", 0, 100, curr_pos.get("right", {}).get("y", 50), key=f"ry_{target_id}")

        with col_u:
            st.markdown("#### ↓ (Uターン)")
            new_uturn = st.selectbox("移動先ID", all_ids, index=all_ids.index(target_node.get("uturn")) if target_node.get("uturn") in all_ids else 0, key=f"edit_uturn_{target_id}")
            uturn_x = st.slider("横位置 X (%)", 0, 100, curr_pos.get("uturn", {}).get("x", 50), key=f"ux_{target_id}")
            uturn_y = st.slider("縦位置 Y (%)", 0, 100, curr_pos.get("uturn", {}).get("y", 80), key=f"uy_{target_id}")

        # スライダー等の操作時にデータ構造を同期
        updated_node_data = {
            "title": new_title,
            "image": image_path,
            "ar_info": new_ar_info,
            "forward": new_forward,
            "left": new_left,
            "right": new_right,
            "uturn": new_uturn,
            "pos": {
                "left": {"x": left_x, "y": left_y},
                "forward": {"x": fwd_x, "y": fwd_y},
                "right": {"x": right_x, "y": right_y},
                "uturn": {"x": uturn_x, "y": uturn_y}
            }
        }
        
        if target_id and target_id != "":
            st.session_state["map_data"][target_id] = updated_node_data
            save_map_data(st.session_state["map_data"])

        st.subheader("🎯 矢印位置のリアルタイムプレビュー")
        preview_html = ""
        preview_arrows = [
            (new_left, "←", left_x, left_y),
            (new_forward, "↑", fwd_x, fwd_y),
            (new_right, "→", right_x, right_y),
            (new_uturn, "↓", uturn_x, uturn_y)
        ]

        for target, symbol, px, py in preview_arrows:
            if target is not None:
                preview_html += f'<div style="position: absolute; left: {px}%; top: {py}%; transform: translate(-50%, -50%); background: rgba(30,30,30,0.45); color: #ffffff; border: 1.5px solid rgba(255,255,255,0.7); border-radius: 50%; width: 40px; height: 40px; font-size: 20px; font-weight: bold; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px);">{symbol}</div>'

        if image_path:
            preview_container = f'<div style="position: relative; width: 100%; max-width: 500px; margin: 0 auto;"><img src="{image_path}" style="width: 100%; border-radius: 8px;" />{preview_html}</div>'
            st.markdown(preview_container, unsafe_allow_html=True)

        st.write("---")

        # ［保存］と［削除］ボタンのレイアウト設定
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

        # 地点削除ボタン（既存の地点が選択されている場合のみ表示）
        with col_btn_del:
            if selected_option != "➕ 新しい地点を追加":
                if st.button("🗑️ この地点を削除", key=f"del_{target_id}", use_container_width=True):
                    # 他の地点の移動先リンクからこの地点を外す
                    for nid, node in st.session_state["map_data"].items():
                        for k in ["forward", "left", "right", "uturn"]:
                            if node.get(k) == target_id:
                                node[k] = None

                    # 対象の地点を削除
                    st.session_state["map_data"].pop(target_id, None)
                    save_map_data(st.session_state["map_data"])
                    st.toast(f"🗑️ 地点『{target_id}』を削除しました")
                    st.success(f"🗑️ 地点『{target_id}』を削除しました！")
                    st.rerun()