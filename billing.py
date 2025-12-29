# billing.py
from datetime import datetime


class BillingRecord:
    """
    BillingRecord（付款紀錄資料結構）
    ------------------------------------------------------------
    一筆付款紀錄包含：
    - customer_id：付款客戶
    - tracking_number：對應包裹編號
    - amount：金額（refund 時為負數）
    - method：付款方式（Immediate / Prepaid / Monthly / Refund）
    - timestamp：紀錄建立時間
    - is_refund：是否為退款
    ------------------------------------------------------------
    此類別主要用於：
    - BillingSystem.all_records 的統一格式
    - 放進 MonthlyStatement 的明細
    """

    def __init__(self, customer_id, tracking_number, amount, method, is_refund=False):
        self.customer_id = customer_id
        self.tracking_number = tracking_number
        self.amount = amount
        self.method = method
        self.is_refund = is_refund
        self.timestamp = datetime.now()

    def __str__(self):
        tag = "（退款）" if self.is_refund else ""
        return (
            f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{self.method}{tag} - 客戶 {self.customer_id} - 包裹 {self.tracking_number} - 金額 {self.amount:.2f}"
        )


class MonthlyStatement:
    """
    MonthlyStatement（月結帳單）
    ------------------------------------------------------------
    - 一位合約客戶（Contract Customer）一個帳單實例
    - records：BillingRecord 的集合
    - created_date：帳單建立時間

    用途：
    - BillingSystem.monthly_statements 使用 customer_id → MonthlyStatement 映射
    - 顯示月結支出、金額加總（total_amount）
    """

    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.records = []
        self.created_date = datetime.now()

    @property
    def total_amount(self):
        """計算所有非退款（is_refund=False）的金額總和"""
        return sum(r.amount for r in self.records if not r.is_refund)

    def add_record(self, record):
        """加入一筆 BillingRecord"""
        self.records.append(record)

    def __str__(self):
        lines = [
            f"===== 月結帳單：客戶 {self.customer_id} =====",
            f"建立日期：{self.created_date.strftime('%Y-%m-%d')}",
            "明細："
        ]
        # 印出所有紀錄
        lines += [f" - {r}" for r in self.records]

        lines.append(f"\n總金額：{self.total_amount:.2f}")
        lines.append("===============================\n")

        return "\n".join(lines)


class BillingSystem:
    """
    BillingSystem（計費系統核心）
    ------------------------------------------------------------
    功能：
    (1) pay_now：非合約客戶 → 立即付款
    (2) prepaid：預付客戶 → 不收費但紀錄
    (3) add_to_monthly_bill：合約客戶 → 加入帳單
    (4) refund：退款功能（is_refund = True）
    (5) record_payment：統一付款 API（Customer.pay_for_package() 用）
    (6) 查詢功能：list_customer_records / get_monthly_statement
    ------------------------------------------------------------
    全域資料：
    - all_records：所有 BillingRecord，包含三類付款 + 退款
    - monthly_statements：customer_id → MonthlyStatement
    """

    all_records = []  # 保存所有付款紀錄
    monthly_statements = {}  # customer_id → MonthlyStatement

    # ------------------------------------------------------------
    # (A) 通用付款 API（由 Customer 呼叫）
    # ------------------------------------------------------------
    @classmethod
    def record_payment(cls, customer, package, method):
        """
        建立一筆統一格式的付款紀錄。
        用途：Customer.pay_for_package() 統一呼叫此方法。
        """
        record = BillingRecord(
            customer_id=customer.customer_id,
            tracking_number=package.tracking_number,
            amount=package.billing_cost,
            method=method
        )
        cls.all_records.append(record)
        return record

    # ------------------------------------------------------------
    # (B) 非合約客戶 → 即時付款
    # ------------------------------------------------------------
    @classmethod
    def pay_now(cls, customer, package):
        print("\n=== 即時付款（非合約客戶）===")
        record = cls.record_payment(customer, package, "Immediate Payment")
        print(record)
        return record

    # ------------------------------------------------------------
    # (C) 預付客戶 → 不收費（amount = 0）
    # ------------------------------------------------------------
    @classmethod
    def prepaid(cls, customer, package):
        print("\n=== 預付客戶：不收費 ===")

        record = BillingRecord(
            customer_id=customer.customer_id,
            tracking_number=package.tracking_number,
            amount=0.0,
            method="Prepaid"
        )

        cls.all_records.append(record)
        print(record)
        return record

    # ------------------------------------------------------------
    # (D) 合約客戶 → 月結帳單
    # ------------------------------------------------------------
    @classmethod
    def add_to_monthly_bill(cls, customer, package):
        print("\n=== 月結帳戶：加入帳單 ===")

        record = BillingRecord(
            customer_id=customer.customer_id,
            tracking_number=package.tracking_number,
            amount=package.billing_cost,
            method="Monthly Billing"
        )

        cls.all_records.append(record)

        # 若客戶沒有月結帳單 → 自動建立
        if customer.customer_id not in cls.monthly_statements:
            cls.monthly_statements[customer.customer_id] = MonthlyStatement(customer.customer_id)

        # 加入帳單明細
        cls.monthly_statements[customer.customer_id].add_record(record)

        print(record)
        return record

    # ------------------------------------------------------------
    # (E) 退款功能（Bonus）
    # ------------------------------------------------------------
    @classmethod
    def refund(cls, customer, package, amount):
        """
        建立一筆退款紀錄（amount 通常為負值）
        """
        print("\n=== 處理退款 ===")

        record = BillingRecord(
            customer_id=customer.customer_id,
            tracking_number=package.tracking_number,
            amount=-abs(amount),
            method="Refund",
            is_refund=True
        )

        cls.all_records.append(record)
        print(record)
        return record

    # ------------------------------------------------------------
    # (F) 查詢功能
    # ------------------------------------------------------------
    @classmethod
    def list_customer_records(cls, customer_id):
        """列出某客戶所有付款紀錄"""
        return [r for r in cls.all_records if r.customer_id == customer_id]

    @classmethod
    def list_all_records(cls):
        """列出系統中所有付款紀錄"""
        return list(cls.all_records)

    @classmethod
    def get_monthly_statement(cls, customer_id):
        """取得某客戶的月結帳單"""
        return cls.monthly_statements.get(customer_id)
