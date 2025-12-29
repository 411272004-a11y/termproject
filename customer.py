# customer.py
from billing import BillingSystem


class Customer:
    """
    Customer 客戶類別
    ------------------------------------------------------------
    支援需求（對應 1.1、1.5）：
    - 客戶資料（ID / 地址 / 聯絡資訊）
    - 客戶類型：Non-Contract / Prepaid / Contract
    - billing_preference：付款偏好（信用卡 / 現金 / 月結）
    - 查詢付款紀錄
    - 統一付款流程 pay_for_package()

    all_customers：模擬資料庫，customer_id → Customer 物件
    """

    all_customers = {}

    def __init__(self, customer_id, name, address, phone, email,
                 customer_type, billing_preference):
        # 基本資料
        self.customer_id = customer_id
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email

        # 客戶類型（決定付款方式）
        self.customer_type = customer_type            # Non-Contract / Prepaid / Contract
        self.billing_preference = billing_preference  # Credit / Monthly / ...

        # 已付款紀錄（BillingRecord）
        self.payment_records = []

        Customer.all_customers[customer_id] = self

    # ------------------------------------------------------------
    # 類型判斷
    # ------------------------------------------------------------
    def is_prepaid(self):
        """是否為預付客戶（建立包裹時已付費）"""
        return self.customer_type == "Prepaid"

    def is_contract(self):
        """是否為合約客戶（月結）"""
        return self.customer_type == "Contract"

    # ------------------------------------------------------------
    # 統一付款流程（最重要）
    # ------------------------------------------------------------
    def pay_for_package(self, package):
        """
        根據客戶類型自動分流：
        --------------------------------------------------------
        Prepaid → BillingSystem.prepaid()
        Contract → BillingSystem.add_to_monthly_bill()
        Non-Contract → BillingSystem.pay_now()
        --------------------------------------------------------
        並將紀錄加入 self.payment_records
        """

        print(f"\n[PAYMENT] {self.name} 的付款流程開始...")

        # 1. 預付客戶 → 不收費，但仍需建立紀錄
        if self.is_prepaid():
            record = BillingSystem.prepaid(self, package)

        # 2. 合約客戶 → 月結帳單
        elif self.is_contract():
            record = BillingSystem.add_to_monthly_bill(self, package)

        # 3. 一般客戶 → 即時付款
        else:
            record = BillingSystem.pay_now(self, package)

        self.payment_records.append(record)
        return record

    # ------------------------------------------------------------
    # 查詢付款紀錄
    # ------------------------------------------------------------
    def list_payments(self):
        """印出並回傳所有付款紀錄"""
        if not self.payment_records:
            print(f"\n[PAYMENT] {self.name} 尚無付款紀錄")
            return []
        for p in self.payment_records:
            print(p)
        return self.payment_records

    def __str__(self):
        return (
            f"[{self.customer_type}] "
            f"ID: {self.customer_id}, Name: {self.name}, "
            f"Billing: {self.billing_preference}"
        )


# ------------------------------------------------------------
# 合約客戶（Contract Customer）→ 固定 customer_type="Contract"
# ------------------------------------------------------------
class ContractCustomer(Customer):
    """
    ContractCustomer（月結客戶）
    ------------------------------------------------------------
    customer_type 自動固定為 Contract
    billing_preference 自動為 Monthly
    其他邏輯由父類別 Customer 處理
    """

    def __init__(self, customer_id, name, address, phone, email):
        super().__init__(
            customer_id,
            name,
            address,
            phone,
            email,
            customer_type="Contract",
            billing_preference="Monthly"
        )
