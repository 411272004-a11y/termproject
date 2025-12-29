import hashlib
import uuid
from datetime import datetime


class User:
    """
    User 系統（對應 1.6 安全與權限）

    支援功能：
    - 密碼雜湊
    - 登入紀錄（含鎖定機制）
    - 角色權限表（可更新哪些包裹狀態）
    """

    VALID_ROLES = {"customer_service", "warehouse", "driver", "admin"}

    # -----------------------------------------------------------
    # 1.6 角色權限：每個角色能更新哪些包裹狀態
    # -----------------------------------------------------------
    STATUS_PERMISSIONS = {
        "customer_service": {"Shipment Created"},
        "warehouse": {"In Transit", "In Transit - Sorting", "Out for Delivery"},
        "driver": {"Picked Up", "Out for Delivery", "Delivered"},
        "admin": "ALL",
    }

    def __init__(self, username, password, role):
        if role not in User.VALID_ROLES:
            raise ValueError(f"Invalid role: {role}")

        self.user_id = str(uuid.uuid4())
        self.username = username
        self.password_hash = self._hash_password(password)
        self.role = role

        self.is_active = True
        self.failed_attempts = 0
        self.login_history = []
        self.last_login = None

    # -----------------------------------------------------------
    # 密碼處理
    # -----------------------------------------------------------
    @staticmethod
    def _hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password):
        return self.password_hash == self._hash_password(password)

    # -----------------------------------------------------------
    # 登入流程（含教學 print）
    # -----------------------------------------------------------
    def login(self, password):
        print(f"\n[LOGIN] User: {self.username}")

        if not self.is_active:
            print("  > 帳號已停用，禁止登入")
            raise PermissionError("帳號已停用")

        if self.verify_password(password):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.last_login = timestamp
            self.login_history.append(timestamp)
            self.failed_attempts = 0

            print(f"  > 登入成功！時間：{timestamp}")
            return True

        # 登入失敗
        self.failed_attempts += 1
        print(f"  > 密碼錯誤！目前錯誤次數：{self.failed_attempts}/5")

        if self.failed_attempts >= 5:
            self.is_active = False
            print("  > 已達錯誤上限！帳號自動停用！")
            raise PermissionError("密碼錯誤超過次數，帳號已停用")

        return False

    # -----------------------------------------------------------
    # 角色權限檢查（對應 1.6）
    # -----------------------------------------------------------
    def can_update_status(self, new_status):
        print(f"[PERMISSION] {self.username} 嘗試更新狀態 → {new_status}")

        if self.role == "admin":
            print("  > 管理者權限：允許")
            return True

        allowed = User.STATUS_PERMISSIONS.get(self.role, set())

        if allowed == "ALL":
            print("  > ALL 權限：允許")
            return True

        if new_status in allowed:
            print("  > 已授權：允許此狀態變更")
            return True

        print("  > 未授權：拒絕此狀態變更")
        return False

    # -----------------------------------------------------------
    # 建立包裹權限（客服 + 管理員）
    # -----------------------------------------------------------
    def can_create_package(self):
        return self.role in {"customer_service", "admin"}

    # -----------------------------------------------------------
    # 查詢所有包裹（只有 admin）
    # -----------------------------------------------------------
    def can_view_all_packages(self):
        return self.role == "admin"

    # -----------------------------------------------------------
    # 👉👉 新增：一般員工能查客戶包裹（未來 customer 登入會改）
    # -----------------------------------------------------------
    def can_view_customer_packages(self):
        return self.role in {"customer_service", "warehouse", "driver", "admin"}

    def __repr__(self):
        status = "Active" if self.is_active else "Disabled"
        return (
            f"<User {self.username} (role={self.role}, status={status}, "
            f"last_login={self.last_login})>"
        )