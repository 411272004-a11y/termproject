import uuid
from datetime import datetime, timedelta
from tracking import TrackingEvent
from service import ServiceType
from user import User
from warehouse import Warehouse
from vehicle import Vehicle


class Package:
    """
    Package 模組 — 系統物流流程核心物件
    ------------------------------------------------------------
    ⭐ 自動物流流程包含：
        1. 建立包裹 → 自動進入起始倉庫
        2. update_status():
            - 自動判斷是否出倉 / 進倉
            - 自動處理車輛上車 / 卸貨
            - 自動更新 ETA
            - 自動寫入 TrackingEvent
    ⭐ 完整支援 1.3 / 1.4 / 1.5 需求
    ------------------------------------------------------------
    """

    # 模擬資料庫
    all_packages = {}

    def __init__(
        self,
        customer_id,
        weight,
        dimensions,
        declared_value,
        description,
        service_type: ServiceType,
        special_services: list,
        distance_km,
        created_by: User,
        eta_days=2,
        warehouse_id="W-001"    # ★ 建立包裹時自動進入此倉庫
    ):
        # ------------------------------------------------------------
        # (1) 基本資料
        # ------------------------------------------------------------
        self.tracking_number = str(uuid.uuid4().int)[:10]
        self.customer_id = customer_id
        self.weight = weight
        self.dimensions = dimensions
        self.declared_value = declared_value
        self.description = description
        self.service_type = service_type
        self.special_services = special_services
        self.distance_km = distance_km

        self.current_status = "Shipment Created"
        self.eta = datetime.now() + timedelta(days=eta_days)

        # ★ 包裹當前所在倉庫（None = 不在倉庫）
        self.warehouse_id = warehouse_id

        # ------------------------------------------------------------
        # (2) 計費
        # ------------------------------------------------------------
        self.billing_cost = self._calculate_cost()

        # ------------------------------------------------------------
        # (3) 加入資料庫
        # ------------------------------------------------------------
        Package.all_packages[self.tracking_number] = self

        # ------------------------------------------------------------
        # (4) 自動進倉
        # ------------------------------------------------------------
        try:
            wh = Warehouse.get(warehouse_id)
            if wh:
                wh.add_package(self.tracking_number)
        except Exception as e:
            print(f"[WARNING] 無法進倉：{e}")

        # ------------------------------------------------------------
        # (5) 建立初始事件
        # ------------------------------------------------------------
        TrackingEvent.log_event(
            tracking_number=self.tracking_number,
            location=f"Warehouse {self.warehouse_id}",
            status_description=self.current_status,
            user=created_by,
            event_type="Created",
            warehouse_id=self.warehouse_id,
            eta=self.eta
        )

    # ============================================================
    # (6) 運費計算
    # ============================================================
    def _calculate_cost(self):
        print(f"\n[COST] 計算包裹 {self.tracking_number} 運費...")

        cost = self.service_type.base_rate
        print(f"  > 基礎費用：+{self.service_type.base_rate}")

        weight_cost = self.weight * self.service_type.weight_rate
        cost += weight_cost
        print(f"  > 重量費用：+{weight_cost}")

        distance_cost = self.distance_km * 0.5
        cost += distance_cost
        print(f"  > 距離費用：+{distance_cost}")

        for s in self.special_services:
            if s in self.service_type.special_fees:
                fee = self.service_type.special_fees[s]
                cost += fee
                print(f"  > 特殊服務 {s}：+{fee}")
            else:
                print(f"  > [警告] 特殊服務 {s} 未設定費用")

        insurance_cost = self.declared_value * 0.01
        cost += insurance_cost
        print(f"  > 保險費：+{insurance_cost}")

        cost = round(cost, 2)
        print(f"[TOTAL] 運費：{cost}")
        return cost

    # ============================================================
    # (7) 自動流程：更新包裹狀態
    # ============================================================
    def update_status(
        self,
        new_status,
        location,
        user: User,
        event_type="Transit",
        vehicle: Vehicle = None,
        to_warehouse: Warehouse = None,
        eta=None,
        exception_type=None
    ):
        """
        自動流程完整邏輯：
        ------------------------------------------------------------
        1. 權限檢查
        2. 若包裹在倉庫 → 自動出倉
        3. 若 vehicle 存在：
              - Picked Up / Out for Delivery → 上車
              - Delivered → 卸貨
        4. 若 to_warehouse 存在 → 進倉
        5. 更新狀態 / ETA
        6. 建立 TrackingEvent
        ------------------------------------------------------------
        """

        print(f"\n[STATUS] {self.tracking_number} → {new_status}")

        # ------------------------------------------------------------
        # 1. 權限驗證（對應 1.6）
        # ------------------------------------------------------------
        if not user.can_update_status(new_status):
            raise PermissionError(f"{user.username} 無權更新狀態 {new_status}")

        # ------------------------------------------------------------
        # 2. 包裹出倉（若目前在倉庫）
        # ------------------------------------------------------------
        if self.warehouse_id:
            old_wh = Warehouse.get(self.warehouse_id)
            if old_wh:
                try:
                    old_wh.remove_package(self.tracking_number)
                    print(f"[WAREHOUSE] 離開倉庫：{self.warehouse_id}")
                except:
                    pass
            self.warehouse_id = None

        # ------------------------------------------------------------
        # 3. 車輛自動流程
        # ------------------------------------------------------------
        vehicle_id = None

        if vehicle:
            vehicle_id = vehicle.vehicle_id

            # ⭐ 自動上車
            if new_status in {"Picked Up", "Out for Delivery"}:
                vehicle.load_package(self, user)
                print(f"[VEHICLE] 上車：{vehicle.vehicle_id}")

            # ⭐ Delivered 自動卸車
            if new_status == "Delivered":
                vehicle.unload_package(self, location, user)
                print(f"[VEHICLE] 卸貨：{vehicle.vehicle_id}")

        # ------------------------------------------------------------
        # 4. 進倉（若指定 to_warehouse）
        # ------------------------------------------------------------
        warehouse_id = None
        if to_warehouse:
            to_warehouse.add_package(self.tracking_number)
            warehouse_id = to_warehouse.warehouse_id
            self.warehouse_id = warehouse_id
            print(f"[WAREHOUSE] 進入倉庫：{warehouse_id}")

        # ------------------------------------------------------------
        # 5. 更新狀態 / ETA
        # ------------------------------------------------------------
        self.current_status = new_status
        if eta:
            self.eta = eta

        # ------------------------------------------------------------
        # 6. 建立 TrackingEvent
        # ------------------------------------------------------------
        TrackingEvent.log_event(
            tracking_number=self.tracking_number,
            location=location,
            status_description=new_status,
            user=user,
            event_type=event_type,
            vehicle_id=vehicle_id,
            warehouse_id=self.warehouse_id,
            eta=self.eta,
            exception_type=exception_type
        )

    # ============================================================
    # 查詢
    # ============================================================
    @classmethod
    def find_by_tracking_number(cls, tracking_number):
        return cls.all_packages.get(tracking_number)

    # ============================================================
    # 輸出文字
    # ============================================================
    def __str__(self):
        return (
            f"Package {self.tracking_number} | "
            f"Status={self.current_status} | "
            f"Warehouse={self.warehouse_id} | "
            f"ETA={self.eta.strftime('%Y-%m-%d')} | "
            f"Cost=${self.billing_cost:.2f}"
        )
