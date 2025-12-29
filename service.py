class ServiceType:
    """
    1.2 包裹服務分類與定價規則（教學版）

    支援資訊：
    - 服務類型(1.2.4:配送時效）
    - 基礎運費(base_rate)
    - 重量費率(weight_rate)
    - 特殊費用(1.2.6)
    """

    def __init__(self, service_id, name, speed, base_rate, weight_rate, special_fees=None):
        print(f"\n[SERVICE] 建立服務類型：{name}")

        self.service_id = service_id
        self.name = name
        self.speed = speed  # 隔夜達、標準、經濟…（1.2.4）

        # 基礎運費與計價（1.2.5）
        self.base_rate = base_rate
        self.weight_rate = weight_rate

        # 特殊費用（危險物、易碎、超大件等）（1.2.6）
        self.special_fees = special_fees if special_fees is not None else {}

        print(f"  > 配送時效：{self.speed}")
        print(f"  > 基礎費用：{self.base_rate}")
        print(f"  > 重量費率：{self.weight_rate}")
        print(f"  > 附加費用表：{self.special_fees}")

    def __str__(self):
        return (
            f"[Service {self.name}] Speed={self.speed}, Base={self.base_rate}, "
            f"WeightRate={self.weight_rate}, Specials={self.special_fees}"
        )


# --------------------------------------------------------------
# 內建服務類型（可自行擴充）
# --------------------------------------------------------------

STANDARD_SERVICE = ServiceType(
    service_id="STD",
    name="標準速遞",
    speed="Standard",
    base_rate=50.0,
    weight_rate=15.0,
    special_fees={
        'Oversize': 100.0,
        'Fragile': 20.0
    }
)

EXPRESS_OVERNIGHT = ServiceType(
    service_id="OVN",
    name="隔夜達",
    speed="Overnight",
    base_rate=150.0,
    weight_rate=25.0,
    special_fees={
        'Dangerous': 200.0,
        'Fragile': 75.0
    }
)
