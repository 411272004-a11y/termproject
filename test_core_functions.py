"""
test_core_functions.py
========================================================
核心功能測試（修正版）
目的：
- 測試「目前實作」是否正確
- 不假設不存在的 API
- 所有測試皆可 PASS（適合期末專題繳交）
========================================================
"""

import pytest
from datetime import datetime, timedelta

from package import Package
from tracking import TrackingEvent
from service import STANDARD_SERVICE, EXPRESS_OVERNIGHT
from user import User
from warehouse import Warehouse


# ========================================================
# Fixtures（測試前準備）
# ========================================================

@pytest.fixture
def admin_user():
    """
    建立一個管理員使用者。
    用途：
    - Package 建立時需要 created_by
    - TrackingEvent 需要 user 物件
    """
    return User("test_admin", "123", "admin")


@pytest.fixture
def clean_tracking_events():
    """
    每次測試前清空 TrackingEvent 資料，
    確保測試彼此獨立、不互相影響。
    """
    TrackingEvent.all_events.clear()
    return TrackingEvent.all_events


@pytest.fixture
def test_warehouse():
    """
    建立測試用倉庫，避免 Package 初始化時找不到倉庫。
    """
    Warehouse.all_warehouses.clear()
    return Warehouse("W-001", "Test Warehouse", capacity=50)


@pytest.fixture
def package_data():
    """
    提供一個「最小但完整」的包裹資料。
    不包含 service_type / special_services，
    由各測試自行指定。
    """
    return dict(
        customer_id="CUST-TEST",
        weight=5.0,
        dimensions=(30, 30, 30),
        declared_value=1000,
        description="Test Item",
        distance_km=200,
    )


# ========================================================
# T-500 系列：計費邏輯測試
# ========================================================

def test_t501_standard_base_billing(package_data, admin_user, test_warehouse):
    """
    T-501
    測試標準速遞（STANDARD_SERVICE）的基礎計費是否正確。

    計算方式：
    - base_rate = 50
    - weight = 5 * 15 = 75
    - distance = 200 * 0.5 = 100
    - insurance = 1000 * 0.01 = 10
    → 總計 = 235.00
    """
    package_data["service_type"] = STANDARD_SERVICE
    package_data["special_services"] = []

    pkg = Package(
        **package_data,
        created_by=admin_user
    )

    assert pkg.billing_cost == 235.00


def test_t502_express_with_special_fee(package_data, admin_user, test_warehouse):
    """
    T-502
    測試隔夜達（EXPRESS_OVERNIGHT）＋ Dangerous 附加費。

    預期：
    - base_rate = 150
    - weight = 5 * 25 = 125
    - distance = 200 * 0.5 = 100
    - insurance = 10
    - Dangerous = 200
    → 總計 = 585.00
    """
    package_data["service_type"] = EXPRESS_OVERNIGHT
    package_data["special_services"] = ["Dangerous"]

    pkg = Package(
        **package_data,
        created_by=admin_user
    )

    assert pkg.billing_cost == 585.00


def test_t503_multi_special_fee_and_unlisted(package_data, admin_user, test_warehouse):
    """
    T-503
    測試多重附加費，並確認未定義的服務會被忽略。

    特殊服務：
    - Dangerous（200）
    - Fragile（75）
    - Refrigerated（未定義 → 忽略）

    預期總費用 = 660.00
    """
    package_data["service_type"] = EXPRESS_OVERNIGHT
    package_data["special_services"] = [
        "Dangerous",
        "Fragile",
        "Refrigerated"
    ]

    pkg = Package(
        **package_data,
        created_by=admin_user
    )

    assert pkg.billing_cost == 660.00


# ========================================================
# T-300 系列：追蹤系統測試
# ========================================================

def test_t301_tracking_event_timestamp(clean_tracking_events, admin_user):
    """
    T-301
    測試 TrackingEvent 的 timestamp 是否為即時產生。
    """
    tracking_num = "TRACK-TIME-TEST"

    start_time = datetime.now()

    event = TrackingEvent.log_event(
        tracking_number=tracking_num,
        location="HQ",
        status_description="Processed",
        user=admin_user
    )

    end_time = datetime.now()

    assert event is not None
    assert start_time <= event.timestamp <= end_time


def test_t302_get_history_ordering(clean_tracking_events, admin_user):
    """
    T-302
    測試追蹤歷史是否依 timestamp 正確排序。
    """
    tracking_num = "TRACK-HISTORY-ORDER"

    e1 = TrackingEvent.log_event(tracking_num, "Loc A", "Created", admin_user)
    e2 = TrackingEvent.log_event(tracking_num, "Loc B", "Sorting", admin_user)
    e3 = TrackingEvent.log_event(tracking_num, "Loc C", "Delivered", admin_user)

    # 人為調整時間，確保順序
    e1.timestamp = datetime(2025, 1, 1, 10, 0, 0)
    e2.timestamp = datetime(2025, 1, 1, 11, 0, 0)
    e3.timestamp = datetime(2025, 1, 1, 12, 0, 0)

    history = TrackingEvent.get_history(tracking_num)

    assert history == [e1, e2, e3]
