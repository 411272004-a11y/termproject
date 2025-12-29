import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 核心模組匯入 ---
from package import Package
from user import User
from billing import BillingSystem
from vehicle import Vehicle
from warehouse import Warehouse
from service import STANDARD_SERVICE, EXPRESS_OVERNIGHT
from tracking import TrackingEvent

# ============================================================
# 初始化系統資料
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

db = st.session_state.db

# ============================================================
# 側邊欄權限切換
# ============================================================
with st.sidebar:
    st.title("智流管理系統")
    role_view = st.selectbox(
        "切換登入身分",
        ["客戶查詢端", "寄件與服務受理", "倉儲管理", "配送任務", "系統管理總覽"]
    )
    st.divider()
    st.info(f"當前模式：{role_view}")

# ============================================================
# 各功能模組
# ============================================================

# --- 寄件與服務受理 ---
if role_view == "寄件與服務受理":
    st.header("包裹收件與準備")

    with st.form("order_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 客戶資料紀錄")
            cust_name = st.text_input("客戶姓名/編號", "張先生")
            cust_type = st.selectbox("客戶類型", ["合約客戶 (月結)", "非合約客戶 (現金/信用卡)", "預付客戶"])

        with col2:
            st.write("### 服務分類與定價")
            svc_level = st.selectbox("配送時效", ["隔夜達", "兩日達", "標準速遞", "經濟速遞"])
            weight = st.number_input("重量 (kg)", 0.1, 500.0, 1.0)
            dist = st.number_input("運送距離 (km)", 1, 1000, 50)

        st.write("### 特殊服務標示")
        specials = st.multiselect("勾選項目", ["易碎品", "危險物品", "國際貨件", "超大件"])
        val = st.number_input("申報價值", 0, 100000, 1000)
        desc = st.text_area("內容物描述")

        if st.form_submit_button("建立運單並分配追蹤編號"):
            # 1. 計算費用明細
            base_fee = 100 if "標準" in svc_level else 200  # 基礎費
            weight_fee = weight * 20  # 重量費
            dist_fee = dist * 1.5  # 距離費
            special_fee = len(specials) * 50  # 特殊處理費
            total_amount = base_fee + weight_fee + dist_fee + special_fee

            # 2. 建立包裹實例
            svc = STANDARD_SERVICE if "標準" in svc_level else EXPRESS_OVERNIGHT
            new_p = Package(cust_name, float(weight), "標準箱", float(val), desc, svc, specials, float(dist),
                            db['users']['cs'])

            # 強制更新費用（對齊計算結果）
            new_p.billing_cost = total_amount

            # 3. 系統存檔與連動
            db["packages"].append(new_p)
            db["warehouse"].add_package(new_p.tracking_number)

            # 4. 記錄收款明細 (金錢是如何收到的)
            payment_detail = f"基礎:{base_fee} + 重量:{weight_fee} + 距離:{dist_fee} + 特殊服務:{special_fee}"
            from collections import namedtuple

            M_Cust = namedtuple("M_Cust", ["customer_id"])
            BillingSystem.record_payment(M_Cust(cust_name), new_p, f"結算方式: {cust_type} ({payment_detail})")

            st.success(f"運單建立成功！唯一追蹤編號：{new_p.tracking_number}")
            st.write(f"**總計費用：${total_amount:.2f}**")
            st.balloons()

# --- 客戶查詢端 ---
elif role_view == "客戶查詢端":
    st.header("追蹤與物流查詢")
    search_id = st.text_input("請輸入追蹤編號", placeholder="例如: PKG1234567890")

    if search_id:
        history = TrackingEvent.get_history(search_id)
        if history:
            latest = history[-1]
            st.subheader(f"當前狀態：{latest.status_description}")
            st.write(f"最後更新位置：{latest.location}")

            st.divider()
            st.write("#### 歷史追蹤詳情")
            for e in reversed(history):
                st.write(f"🕒 {e.timestamp.strftime('%Y-%m-%d %H:%M')} | {e.location} | **{e.status_description}**")
        else:
            st.error("查無紀錄，請檢查單號是否輸入正確。")

# --- 倉儲管理區塊 ---
elif role_view == "倉儲管理":
    st.header("倉儲與轉運管理")
    wh = db["warehouse"]
    # ... (前面的進度條代碼)

    stored_items = wh.list_packages()
    for tid in stored_items:
        c1, c2 = st.columns([3, 1])
        c1.write(f"包裹編號：`{tid}`")
        if c2.button("執行分揀出庫", key=tid):
            p = next(x for x in db["packages"] if x.tracking_number == tid)
            # 這裡必須更新為 "In Transit"，以便司機能抓到這筆資料
            p.update_status("In Transit", "物流分揀中心", db['users']['warehouse'])
            wh.remove_package(tid)
            st.success(f"包裹 {tid} 已轉交物流部")
            time.sleep(0.5)
            st.rerun()

# --- 配送任務區塊 ---
elif role_view == "配送任務":
    st.header("運輸載具與配送控制")
    v = db["vehicle"]
    st.write(f"**載具識別碼：** {v.vehicle_id}")

    # 【關鍵修正】：確保這裡過濾的狀態包含 "In Transit"
    # 這樣倉庫一出庫，司機這邊就會立刻跳出該包裹
    tasks = [p for p in db["packages"] if p.current_status in ["In Transit", "Out for Delivery"]]

    if not tasks:
        st.info("目前無待處理的配送任務。")
    else:
        for p in tasks:
            with st.expander(f"訂單：{p.tracking_number} (目前狀態: {p.current_status})"):
                c1, c2 = st.columns(2)
                # 司機點擊「開始配送」後，狀態變為 "Out for Delivery"
                if c1.button("🚚 開始配送", key=f"drive_{p.tracking_number}"):
                    p.update_status("Out for Delivery", "配送卡車中", db['users']['driver'], vehicle=v)
                    st.rerun()
                # 司機點擊「確認簽收」後，狀態變為 "Delivered"
                if c2.button("🏁 確認投遞簽收", key=f"finish_{p.tracking_number}"):
                    p.update_status("Delivered", "客戶目的地", db['users']['driver'], vehicle=v)
                    st.success("簽收完成！")
                    time.sleep(0.5)
                    st.rerun()

# --- 系統管理總覽 ---
elif role_view == "系統管理總覽":
    st.header("管理人員儀表板")

    tab1, tab2 = st.tabs(["財務計費數據", "系統效能與日誌"])

    with tab1:
        st.subheader("歷史計費數據清單")
        all_recs = BillingSystem.list_all_records()
        if all_recs:
            recs_data = []
            for r in all_recs:
                recs_data.append({
                    "單號": r.tracking_number,
                    "總金額": f"${r.amount:.2f}",
                    "付款細節與計算來源": r.method,
                    "時間戳記": r.timestamp.strftime('%Y-%m-%d %H:%M')
                })
            st.table(recs_data)
        else:
            st.write("目前尚無計費紀錄。")

    with tab2:
        st.subheader("效能與安全性紀錄")
        st.write("系統運作時間：99.9%")
        total_p = len(db["packages"])
        st.write(f"總處理包裹量：{total_p} 件")
        # 顯示異常追蹤範例
        exceptions = [p for p in db["packages"] if "遺失" in p.current_status]
        st.write(f"異常包裹統計：{len(exceptions)} 件")