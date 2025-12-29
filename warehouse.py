# warehouse.py
from tracking import TrackingEvent


class Warehouse:
    """
    Warehouse 倉儲管理模組（Warehouse Management）
    ------------------------------------------------------------
    功能：
        ✔ 倉庫基本資料（ID / 地點 / 容量）
        ✔ 管理包裹進出倉（add/remove）
        ✔ 倉庫狀態（ACTIVE / FULL / CLOSED）
        ✔ 追蹤此倉庫相關的 TrackingEvent
        ✔ 提供 Warehouse.get() 給 Package 自動流程使用
        ✔ 全域倉庫註冊（all_warehouses）
    ------------------------------------------------------------
    """

    # ------------------------------------------------------------
    # 全域倉庫資料（模擬 DB）
    # ------------------------------------------------------------
    all_warehouses = {}

    VALID_STATUS = {"ACTIVE", "FULL", "CLOSED"}

    def __init__(self, warehouse_id: str, location: str, capacity: int):
        self.warehouse_id = warehouse_id
        self.location = location
        self.capacity = capacity
        self.stored_packages = set()      # 目前在倉庫的包裹 tracking number
        self.status = "ACTIVE"

        # ★ 自動註冊到全域列表
        Warehouse.all_warehouses[self.warehouse_id] = self

    # ============================================================
    # 取得倉庫（供 Package 自動流程用）
    # ============================================================
    @classmethod
    def get(cls, warehouse_id: str):
        """根據 warehouse_id 取回倉庫物件"""
        return cls.all_warehouses.get(warehouse_id)

    # ============================================================
    # 倉庫狀態管理
    # ============================================================
    def mark_status(self, status: str):
        """更新倉庫狀態"""
        if status not in Warehouse.VALID_STATUS:
            raise ValueError("無效的倉庫狀態")
        self.status = status

    def is_full(self):
        """倉庫是否滿載"""
        return len(self.stored_packages) >= self.capacity

    # ============================================================
    # 包裹進出倉
    # ============================================================
    def add_package(self, tracking_number: str):
        """包裹進倉"""
        if self.is_full():
            self.status = "FULL"
            raise ValueError(f"倉庫 {self.warehouse_id} 已滿，無法進倉")

        self.stored_packages.add(tracking_number)
        print(f"[WAREHOUSE] {tracking_number} 進入倉庫 {self.warehouse_id}")

    def remove_package(self, tracking_number: str):
        """包裹離倉"""
        if tracking_number in self.stored_packages:
            self.stored_packages.remove(tracking_number)
            print(f"[WAREHOUSE] {tracking_number} 離開倉庫 {self.warehouse_id}")

        if not self.is_full():
            self.status = "ACTIVE"

    # ============================================================
    # 事件查詢
    # ============================================================
    def list_warehouse_events(self):
        """查詢所有與此倉庫相關的追蹤事件"""
        return TrackingEvent.search_by_warehouse(self.warehouse_id)

    def list_packages(self):
        """查詢目前在此倉庫內的包裹列表（排序後輸出）"""
        return sorted(self.stored_packages)

    # ============================================================
    # Debug 友善輸出
    # ============================================================
    def __repr__(self):
        return (
            f"<Warehouse {self.warehouse_id} @ {self.location} | "
            f"{len(self.stored_packages)}/{self.capacity} stored | "
            f"Status={self.status}>"
        )
