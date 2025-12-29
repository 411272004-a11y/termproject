import streamlit as st
import pandas as pd

from package import Package
from user import User
from billing import BillingSystem
from vehicle import Vehicle
from warehouse import Warehouse
from service import STANDARD_SERVICE, EXPRESS_OVERNIGHT
from tracking import TrackingEvent


# ============================================================
# 基本設定
# ============================================================
st.set_page_config(page_title="智慧物流管理系統", layout="wide")
st.title("📦 智慧物流管理系統 Demo（完整展示版｜最新）")


# ============================================================
# 初始化（只跑一次）
# ============================================================
if "db" not in st.session_state:
    admin = User("Admin", "123", "admin")
    cs = User("Customer_Service", "123", "customer_service")
    wh_user = User("Warehouse_Staff", "123", "warehouse")
    driver = User("Driver_Jack", "123", "driver")

    warehouse = Warehouse("WH-001", "台北總倉", capacity=10)
    vehicle = Vehicle("TRUCK-01", "物流卡車", capacity_kg=200)
    vehicle.assign_driver(driver)

    st.session_state.db = {
        "users": {
            "admin": admin,
            "customer_service": cs,
            "warehouse": wh_user,
            "driver": driver
        },
        "packages": [],
        "warehouse": warehouse,
        "vehicle": vehicle
    }

db = st.session_state.db


# ============================================================
# Sidebar：角色入口（像 index.html）
# ============================================================
with st.sidebar:
    st.header("👤 系統角色入口")

    role = st.selectbox(
        "選擇角色",
        ["customer", "customer_service", "warehouse", "driver", "admin"]
    )

    current_user = db["users"].get(role)
    if current_user:
        st.success(f"登入者：{current_user.username}\n角色：{current_user.role}")
    else:
        st.info("Customer（公開查詢，不建立 User）")


# ============================================================
# Customer 顯示：合併里程碑事件（避免訊息洗版）
# ============================================================
def merge_customer_events(events):
    """
    Customer 只看「業務里程碑」：
    Shipment Created / In Transit - Sorting / Out for Delivery / Delivered
    且連續相同狀態只顯示一次，避免 Driver 技術事件洗版。
    """
    visible = {
        "Shipment Created",
        "In Transit - Sorting",
        "Out for Delivery",
        "Delivered"
    }
    merged = []
    last_status = None

    for e in events:
        if e.status_description not in visible:
            continue
        if e.status_description != last_status:
            merged.append(e)
            last_status = e.status_description

    # 若完全沒有里程碑（理論上不該），回傳原始 events 的最後一筆保底
    if not merged and events:
        return [events[-1]]
    return merged


def render_customer_tracking(tracking_number: str):
    history = TrackingEvent.get_history(tracking_number)
    if not history:
        st.error("❌ 查無此包裹")
        return

    pkg = next((p for p in db["packages"] if p.tracking_number == tracking_number), None)
    latest = history[-1]

    # ===== Summary（像 Customer 頁面）=====
    st.subheader("📦 包裹摘要")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("追蹤號碼", tracking_number)
    c2.metric("目前狀態", latest.status_description)
    c3.metric("ETA", pkg.eta.strftime("%Y-%m-%d") if pkg else "-")
    c4.metric("運費", f"${pkg.billing_cost:.2f}" if pkg else "-")

    if pkg:
        st.info(f"🚚 服務：{pkg.service_type.name} ｜ 📏 距離：{pkg.distance_km} km ｜ ⚖️ 重量：{pkg.weight} kg")

    # ===== 進度條（里程碑）=====
    progress_map = {
        "Shipment Created": 0.1,
        "In Transit - Sorting": 0.3,
        "Picked Up": 0.5,          # 可能在後端存在，但 Customer 里程碑顯示時未必出現
        "Out for Delivery": 0.8,
        "Delivered": 1.0,
    }
    st.progress(progress_map.get(latest.status_description, 0.0))

    # ===== 狀態提示 =====
    if latest.status_description == "Delivered":
        st.success("✅ 包裹已送達")
    elif latest.status_description == "Out for Delivery":
        st.warning("🚚 配送中")
    elif latest.status_description == "In Transit - Sorting":
        st.info("🏠 倉庫分揀中")
    else:
        st.info("📦 訂單已建立，等待處理")

    st.divider()

    # ===== Timeline（合併顯示）=====
    st.subheader("📋 配送進度（Customer 里程碑）")
    merged = merge_customer_events(history)

    status_map = {
        "Shipment Created": "包裹已建立",
        "In Transit - Sorting": "倉庫分揀中",
        "Out for Delivery": "配送中",
        "Delivered": "已送達"
    }

    for e in merged:
        ts = e.timestamp.strftime("%Y-%m-%d %H:%M")
        text = status_map.get(e.status_description, e.status_description)
        st.markdown(
            f"""
            **{text}**  
            🕒 {ts}  
            📍 {e.location}
            """
        )
        if e.exception_type:
            st.error(f"⚠️ 配送異常：{e.exception_type}")

    # ===== 額外：若有異常，顯示最後一筆異常（更直覺）=====
    exceptions = [e for e in history if e.exception_type]
    if exceptions:
        st.divider()
        st.subheader("⚠️ 異常紀錄")
        last_exc = exceptions[-1]
        st.error(
            f"最後異常：{last_exc.exception_type} ｜ "
            f"{last_exc.timestamp.strftime('%Y-%m-%d %H:%M')} ｜ {last_exc.location}"
        )


# ============================================================
# 主畫面：用 Tabs 做「像你 HTML 各頁」的分區
# （每個角色進來看到屬於自己的 dashboard）
# ============================================================

# ------------------------------------------------------------
# Customer（公開查詢 + 忙線提示）
# ------------------------------------------------------------
if role == "customer":
    st.header("👤 Customer｜包裹查詢")

    tracking = st.text_input("輸入 Tracking Number（例如：建立包裹後會出現 10 碼 tracking）")

    if tracking:
        render_customer_tracking(tracking)

    st.divider()
    col_a, col_b = st.columns(2)
    if col_a.button("💳 查看付款紀錄（展示）"):
        st.info("目前未提供 Customer 綁定帳號，因此付款紀錄由 Admin/財務查看（展示用）。")

    if col_b.button("📞 聯絡客服"):
        st.warning("📵 客服忙線中，請稍後再試（展示用）")


# ------------------------------------------------------------
# Customer Service：建立包裹 + 清單
# ------------------------------------------------------------
elif role == "customer_service":
    st.header("📦 Customer Service｜建立包裹")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("新增包裹")
        with st.form("create_pkg"):
            customer_id = st.text_input("客戶 ID", value="CUST-01")
            weight = st.number_input("重量 (kg)", 0.1, 100.0, 5.0)
            distance = st.slider("距離 (km)", 1, 500, 50)
            svc = st.radio("服務類型", ["標準速遞", "隔夜達", "經濟速遞（展示）"])
            SERVICE_MAP = {
                "標準速遞": STANDARD_SERVICE,
                "隔夜達": EXPRESS_OVERNIGHT,
                "經濟速遞（展示）": STANDARD_SERVICE  # 展示用，不影響後端
            }
            declared_value = st.number_input("申報價值", 0.0, 1000000.0, 1000.0)
            description = st.text_input("描述", value="Demo Package")
            special_ui = st.multiselect(
                "特殊服務（展示/實際進系統）",
                ["易碎品", "危險物品"]
            )
            SPECIAL_MAP = {
                "易碎品": "Fragile",
                "危險物品": "Dangerous"
            }
            special_services = [SPECIAL_MAP[s] for s in special_ui]
            submit = st.form_submit_button("建立包裹並入庫/計費")

            if submit:
                try:
                    service = SERVICE_MAP[svc]

                    pkg = Package(
                        customer_id=customer_id,
                        weight=float(weight),
                        dimensions="30x20x10",
                        declared_value=float(declared_value),
                        description=description,
                        service_type=service,
                        special_services=special_services,
                        distance_km=float(distance),
                        created_by=current_user,
                        warehouse_id=db["warehouse"].warehouse_id
                    )

                    # 計費：你沒 Customer 類別就用 mock
                    from collections import namedtuple
                    MockCustomer = namedtuple("MockCustomer", ["customer_id"])
                    BillingSystem.record_payment(MockCustomer(customer_id), pkg, "Immediate Payment")

                    db["packages"].append(pkg)
                    st.caption(
                        f"費用說明：基礎費 + 重量({weight}kg) + 距離({distance}km)"
                    )
                    st.success(f"✅ 包裹建立成功：{pkg.tracking_number}")
                    st.balloons()

                except Exception as e:
                    st.error(f"建立失敗：{e}")

    with col2:
        st.subheader("📋 已建立包裹清單")
        if db["packages"]:
            st.dataframe(pd.DataFrame([
                {
                    "Tracking": p.tracking_number,
                    "Customer": p.customer_id,
                    "狀態": p.current_status,
                    "在倉": p.warehouse_id if p.warehouse_id else "—",
                    "ETA": p.eta.strftime("%Y-%m-%d"),
                    "運費": p.billing_cost
                } for p in db["packages"]
            ]), use_container_width=True)
        else:
            st.info("尚無包裹")

    st.divider()
    st.subheader("🔎 快速查詢（客服視角：看完整事件）")
    q = st.text_input("輸入 tracking 查詢（客服可看完整事件）", key="cs_query")
    if q:
        events = TrackingEvent.get_history(q)
        if not events:
            st.error("查無此包裹")
        else:
            st.dataframe(pd.DataFrame([{
                "時間": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "狀態": e.status_description,
                "地點": e.location,
                "操作者": e.user.username if e.user else "System",
                "車輛": e.vehicle_id or "",
                "倉庫": e.warehouse_id or "",
                "異常": e.exception_type or ""
            } for e in events]), use_container_width=True)


# ------------------------------------------------------------
# Warehouse：庫存/狀態 + 交付司機（會更新狀態，Customer 看得到）
# ------------------------------------------------------------
elif role == "warehouse":
    st.header("🏠 Warehouse｜倉庫管理")

    wh = db["warehouse"]

    c1, c2, c3 = st.columns(3)
    c1.metric("倉庫容量", wh.capacity)
    c2.metric("在倉包裹", len(wh.stored_packages))
    c3.metric("倉庫狀態", wh.status)

    st.progress(len(wh.stored_packages) / wh.capacity)

    st.divider()
    st.subheader("📦 在倉包裹清單（可交付司機）")

    pkgs_in_wh = wh.list_packages()
    if pkgs_in_wh:
        for t in pkgs_in_wh:
            colA, colC = st.columns([4, 1])
            colA.write(f"**{t}**")

            if colC.button("🚚 交付司機", key=f"handoff_{t}"):
                try:
                    pkg = next((p for p in db["packages"] if p.tracking_number == t), None)
                    if not pkg:
                        st.error("找不到對應 Package 物件（可能未加入 db['packages']）")
                    else:
                        # 對 Customer 可理解的唯一里程碑
                        pkg.update_status(
                            "In Transit - Sorting",
                            "Warehouse Dispatch Area",
                            current_user
                        )
                        wh.remove_package(t)  # 離開倉庫
                        st.success(f"{t} 已交付司機（離開倉庫）")
                        st.rerun()
                except Exception as e:
                    st.error(f"交付失敗：{e}")

    else:
        st.info("倉庫目前無包裹")

    st.divider()
    st.subheader("📑 倉庫事件（Warehouse 可看完整事件）")
    wh_events = wh.list_warehouse_events()
    if wh_events:
        st.dataframe(pd.DataFrame([{
            "時間": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Tracking": e.tracking_number,
            "狀態": e.status_description,
            "地點": e.location,
            "操作者": e.user.username if e.user else "System",
            "異常": e.exception_type or ""
        } for e in wh_events]), use_container_width=True)
    else:
        st.info("目前沒有倉庫相關事件")


# ------------------------------------------------------------
# Driver：載重/容量 + 成功配送 + 配送失敗（異常）
# ------------------------------------------------------------
elif role == "driver":
    st.header("🚛 Driver｜配送任務")

    v = db["vehicle"]

    col_v1, col_v2 = st.columns(2)
    col_v1.metric("目前載重", f"{v.current_load:.2f} kg")
    col_v2.metric("剩餘容量", f"{(v.capacity_kg - v.current_load):.2f} kg")

    st.divider()
    st.subheader("📦 可處理包裹（未 Delivered）")

    active_pkgs = [
        p for p in db["packages"]
        if p.current_status in {
            "In Transit - Sorting",
            "Picked Up",
            "Out for Delivery"
        }
    ]
    if not active_pkgs:
        st.info("目前沒有待配送包裹")
    else:
        for pkg in active_pkgs:
            st.write(f"**{pkg.tracking_number}** ｜ 狀態：{pkg.current_status} ｜ 在倉：{pkg.warehouse_id or '—'}")

            c_ok, c_fail = st.columns(2)

            # ✅ 成功配送（完整流程：Picked Up -> Out -> Delivered）
            if c_ok.button(f"✅ 成功配送 {pkg.tracking_number}", key=f"ok_{pkg.tracking_number}"):
                try:
                    pkg.update_status("Picked Up", "Warehouse Dock", current_user, vehicle=v)
                    pkg.update_status("Out for Delivery", "On the Road", current_user, vehicle=v)
                    pkg.update_status("Delivered", "Customer Address", current_user, vehicle=v)
                    st.success("配送完成")
                    st.rerun()
                except Exception as e:
                    st.error(f"配送失敗：{e}")

            # ❌ 配送失敗（不 Delivered，只記錄異常，允許之後再成功）
            if c_fail.button(f"❌ 配送失敗 {pkg.tracking_number}", key=f"fail_{pkg.tracking_number}"):
                try:
                    pkg.update_status(
                        new_status="Out for Delivery",
                        location="Customer Address",
                        user=current_user,
                        exception_type="Customer Not Available"
                    )
                    st.warning("已回報配送失敗（可稍後重新配送）")
                    st.rerun()
                except Exception as e:
                    st.error(f"回報失敗：{e}")

    st.divider()
    st.subheader("🧾 車輛事件（Driver 可看完整事件）")
    veh_events = v.vehicle_activity()
    if veh_events:
        st.dataframe(pd.DataFrame([{
            "時間": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Tracking": e.tracking_number,
            "狀態": e.status_description,
            "地點": e.location,
            "操作者": e.user.username if e.user else "System",
            "異常": e.exception_type or ""
        } for e in veh_events]), use_container_width=True)
    else:
        st.info("目前沒有車輛相關事件")


# ------------------------------------------------------------
# Admin：總覽 + 財務 + 健康狀態（視覺化，不直接印 dict）
# ------------------------------------------------------------
elif role == "admin":
    st.header("🧑‍💼 Admin｜系統總覽")

    # ===== 系統概況 metrics =====
    total_pkgs = len(db["packages"])
    in_wh = len(db["warehouse"].stored_packages)
    billing_cnt = len(BillingSystem.all_records)

    col1, col2, col3 = st.columns(3)
    col1.metric("包裹總數", total_pkgs)
    col2.metric("在倉數量", in_wh)
    col3.metric("計費筆數", billing_cnt)

    st.divider()

    # ===== 包裹狀態統計（像 admin.html 那種表格）=====
    st.subheader("📦 包裹狀態總覽")
    if db["packages"]:
        status_counts = {}
        for p in db["packages"]:
            status_counts[p.current_status] = status_counts.get(p.current_status, 0) + 1
        st.dataframe(pd.DataFrame([
            {"狀態": k, "數量": v} for k, v in sorted(status_counts.items(), key=lambda x: x[0])
        ]), use_container_width=True)
    else:
        st.info("尚無包裹資料")

    st.divider()

    # ===== 財務紀錄（完整）=====
    st.subheader("💰 財務收支明細（BillingSystem.all_records）")
    records = BillingSystem.list_all_records()
    if records:
        st.dataframe(pd.DataFrame([{
            "時間": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "單號": r.tracking_number,
            "金額": r.amount,
            "方式": r.method,
            "退款": "是" if getattr(r, "is_refund", False) else "否"
        } for r in records]), use_container_width=True)
    else:
        st.info("目前尚無計費紀錄。")

    st.divider()

    # ===== 健康狀態（視覺化，像 Customer summary）=====
    st.subheader("🩺 系統健康狀態（視覺化）")
    health = TrackingEvent.health_status()

    h1, h2, h3 = st.columns(3)

    if health["system"] == "UP":
        h1.success("系統狀態：正常")
        st.info("所有服務皆可正常使用")
    elif health["system"] == "DEGRADED":
        h1.warning("系統狀態：部分異常")
        st.info("部分功能可能延遲，建議留意錯誤數量")
    else:
        h1.error("系統狀態：異常")
        st.warning("系統異常，請檢查錯誤紀錄")

    h2.metric("事件總數", health["event_count"])
    h3.metric("錯誤數量", health["error_count"])

    # last_event 友善顯示
    st.write("最後事件時間：", health["last_event"].strftime("%Y-%m-%d %H:%M:%S") if health["last_event"] else "—")

    # （可選）顯示錯誤 log（你 tracking.py 有 error_logs）
    with st.expander("查看系統錯誤紀錄（error_logs）"):
        if TrackingEvent.error_logs:
            st.dataframe(pd.DataFrame([{
                "時間": x["time"].strftime("%Y-%m-%d %H:%M:%S"),
                "Tracking": x["tracking_number"],
                "訊息": x["msg"]
            } for x in TrackingEvent.error_logs]), use_container_width=True)
        else:
            st.info("目前沒有錯誤紀錄")
