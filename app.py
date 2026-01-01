import streamlit as st
import pandas as pd
from datetime import datetime
import time
import uuid

# --- 核心模組匯入 ---
from package import Package
from user import User
from billing import BillingSystem
from vehicle import Vehicle
from warehouse import Warehouse
from service import STANDARD_SERVICE, EXPRESS_OVERNIGHT
from tracking import TrackingEvent

# ============================================================
# 1. 系統初始化與登入控管
# ============================================================
if "db" not in st.session_state:
    st.session_state.db = {
        "users": {
            "admin": User("管理經理", "123", "admin"),
            "cs": User("受理人員", "123", "customer_service"),
            "warehouse": User("倉庫專員", "123", "warehouse"),
            "driver": User("配送司機", "123", "driver")
        },
        "packages": [],
        "warehouse": Warehouse("WH-001", "台北轉運中心", capacity=50),
        "vehicle": Vehicle("TRUCK-A1", "物流貨車", capacity_kg=1000)
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_role = None

db = st.session_state.db

# --- 登入頁面 ---
if not st.session_state.logged_in:
    st.title("🚚 智流物流管理系統")
    with st.form("login_panel"):
        role_input = st.selectbox("選擇職位身分", ["admin", "customer_service", "warehouse", "driver"])
        pwd_input = st.text_input("密碼", type="password")
        if st.form_submit_button("進入系統"):
            if pwd_input == "123":
                st.session_state.logged_in = True
                st.session_state.current_role = role_input
                st.rerun()
            else:
                st.error("密碼錯誤")
    st.stop()

# ============================================================
# 2. 側邊欄權限
# ============================================================
with st.sidebar:
    st.title("功能選單")
    st.write(f"當前使用者：**{st.session_state.current_role}**")

    menu_map = {
        "admin": ["系統管理總覽", "客戶查詢端"],
        "customer_service": ["寄件與服務受理", "客戶查詢端"],
        "warehouse": ["倉儲管理", "客戶查詢端"],
        "driver": ["配送任務", "客戶查詢端"]
    }

    available_menus = menu_map.get(st.session_state.current_role, ["客戶查詢端"])
    role_view = st.radio("前往項目", available_menus)

    if st.button("安全登出"):
        st.session_state.logged_in = False
        st.rerun()

# ============================================================
# 3. 功能區塊
# ============================================================

# --- 1.1 / 1.2 / 1.3 寄件與服務受理 (全面擴充) ---
if role_view == "寄件與服務受理":
    st.header("📦 包裹收件與運單準備")

    with st.form("comprehensive_order_form"):
        # --- 1.1 客戶管理 ---
        st.subheader("👤 客戶資料 (Requirement 1.1)")
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            cust_name = st.text_input("客戶姓名", "張先生")
            cust_phone = st.text_input("電話號碼", "0912-345-678")
        with c_col2:
            cust_email = st.text_input("電子郵件", "client@example.com")
            cust_address = st.text_input("聯絡地址", "台北市信義區忠孝東路五段1號")

        c_type = st.selectbox("客戶類型", ["合約客戶 (月結)", "非合約客戶 (現金/信用卡)", "預付客戶 (第三方支付)"])
        billing_pref = st.radio("帳單偏好設定", ["月結帳單", "貨到付款", "預付"], horizontal=True)

        st.divider()

        # --- 1.2 包裹服務分類 ---
        st.subheader("🚚 服務分類與定價 (Requirement 1.2)")
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            pkg_type = st.selectbox("包裹類型", ["平郵信封", "小型箱", "中型箱", "大型箱"])
            svc_level = st.selectbox("配送時效", ["隔夜達", "兩日達", "標準速遞", "經濟速遞"])
        with s_col2:
            weight = st.number_input("重量 (kg)", 0.1, 500.0, 1.0)
            dimensions = st.text_input("尺寸 (長x寬x高 cm)", "30x20x10")

        specials = st.multiselect("特殊服務標示", ["危險物品", "易碎品", "國際貨件要求", "貴重品保價"])

        st.divider()

        # --- 1.3 包裹屬性紀錄 ---
        st.subheader("📝 包裹詳細屬性 (Requirement 1.3)")
        declared_val = st.number_input("申報價值 (TWD)", 0, 1000000, 1000)
        dist = st.number_input("預估配送距離 (km)", 1, 2000, 50)
        content_desc = st.text_area("內容物描述", placeholder="請輸入包裹內含物品詳細說明...")

        if st.form_submit_button("✅ 生成唯一追蹤編號並建立運單"):
            if not cust_address or not content_desc:
                st.error("請填寫完整地址與內容物描述！")
            else:
                # 建立包裹物件
                svc = STANDARD_SERVICE if "標準" in svc_level else EXPRESS_OVERNIGHT
                new_p = Package(cust_name, float(weight), dimensions, float(declared_val),
                                content_desc, svc, specials, float(dist), db['users']['cs'])

                # 擴充屬性賦值 (動態組態管理)
                new_p.target_address = cust_address
                new_p.customer_type = c_type
                new_p.billing_preference = billing_pref
                new_p.customer_phone = cust_phone

                # 計算最終費用 (模擬定價規則掛鉤)
                base_price = {"平郵信封": 50, "小型箱": 100, "中型箱": 200, "大型箱": 400}
                svc_multiplier = {"隔夜達": 2.0, "兩日達": 1.5, "標準速遞": 1.0, "經濟速遞": 0.8}
                final_cost = base_price[pkg_type] * svc_multiplier[svc_level] + (weight * 15) + (len(specials) * 100)
                new_p.billing_cost = final_cost

                db["packages"].append(new_p)
                db["warehouse"].add_package(new_p.tracking_number)

                st.success(f"🚀 運單建立成功！追蹤編號：{new_p.tracking_number}")
                st.balloons()

                # 顯示摘要
                st.info(f"**客戶：** {cust_name} ({c_type}) | **費用：** ${final_cost:.2f}")

# --- 配送任務 (顯示詳細地址) ---
elif role_view == "配送任務":
    st.header("🚛 配送任務控制")
    v = db["vehicle"]
    tasks = [p for p in db["packages"] if p.current_status in ["In Transit", "Out for Delivery"]]

    if not tasks:
        st.success("目前暫無待配送任務！")
    else:
        for p in tasks:
            with st.expander(f"📦 單號：{p.tracking_number} | 目的地：{p.target_address}"):
                st.write(f"**內容物：** {p.description}")
                st.write(f"**特殊服務：** {', '.join(p.special_services) if p.special_services else '無'}")

                c1, c2 = st.columns(2)
                if p.current_status == "In Transit":
                    if c1.button("🚀 開始配送", key=f"s_{p.tracking_number}"):
                        p.update_status("Out for Delivery", "配送卡車中", db['users']['driver'], vehicle=v)
                        st.rerun()
                else:
                    c1.success("✅ 配送中...")

                if c2.button("🏁 確認投遞簽收", key=f"f_{p.tracking_number}"):
                    # 1. 更新包裹狀態
                    p.update_status("Delivered", "客戶目的地", db['users']['driver'], vehicle=v)

                    # 2. 獲取該包裹在下單時計算好的金額
                    # 確保 package 物件裡有 billing_cost 這個屬性
                    final_amount = getattr(p, "billing_cost", 0.0)

                    # 3. 觸發財務入帳 (傳入正確的金額)
                    from collections import namedtuple

                    M_Cust = namedtuple("M_Cust", ["customer_id"])

                    # 關鍵修正：確保傳入 p (包裹物件) 以讓 BillingSystem 讀取金額
                    BillingSystem.record_payment(
                        M_Cust(p.customer_id),
                        p,
                        f"已結清 - 方式: {getattr(p, 'billing_preference', '現金')}"
                    )

                    st.success(f"簽收成功！金額 ${final_amount} 已入帳。")
                    time.sleep(0.5)
                    st.rerun()

# --- 倉儲管理 ---
elif role_view == "倉儲管理":
    st.header("庫存監控")
    wh = db["warehouse"]
    st.metric("當前在庫", f"{len(wh.stored_packages)} / {wh.capacity}")
    for tid in wh.list_packages():
        col1, col2 = st.columns([3, 1])
        col1.write(f"單號：`{tid}`")
        if col2.button("出庫", key=tid):
            p = next(x for x in db["packages"] if x.tracking_number == tid)
            p.update_status("In Transit", "分揀中心", db['users']['warehouse'])
            wh.remove_package(tid)
            st.rerun()

# --- 系統管理總覽 修正版 ---
elif role_view == "系統管理總覽":
    st.header("管理員財務數據")
    recs = BillingSystem.list_all_records()

    if recs:
        df_list = []
        for r in recs:
            # r 應該包含 tracking_number 和 amount 屬性
            df_list.append({
                "運單單號": r.tracking_number,
                "客戶 ID": r.customer_id,
                "結算金額": f"${getattr(r, 'amount', 0.0):.2f}",  # 確保抓取金額
                "備註事項": r.method,
                "時間": r.timestamp.strftime('%m-%d %H:%M')
            })
        st.table(pd.DataFrame(df_list))
    else:
        st.info("尚未有任何簽收結算資料。")

# --- 客戶查詢端 ---
elif role_view == "客戶查詢端":
    st.header("快遞追蹤")
    track_id = st.text_input("輸入單號查詢")
    if track_id:
        h = TrackingEvent.get_history(track_id)
        if h:
            for e in reversed(h):
                st.write(f"● {e.timestamp.strftime('%m-%d %H:%M')} | {e.location} | {e.status_description}")
        else:
            st.error("查無此編號")