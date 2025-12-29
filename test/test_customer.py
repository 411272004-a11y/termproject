#測試customer

"""
1. Customer 物件是否能正確建立。
2. 顧客資料（如 ID、名稱、聯絡方式等）是否能正確儲存。
3. 不同顧客類型（如合約 / 非合約）是否能被正確辨識。
"""





import pytest
from customer import Customer
from billing import BillingSystem
from service import STANDARD_SERVICE
from package import Package
from user import User
from warehouse import Warehouse


@pytest.fixture(autouse=True)
def clean_billing():
    BillingSystem.all_records.clear()
    BillingSystem.monthly_statements.clear()


def create_test_package():
    Warehouse("W-001", "Test WH", 10)
    user = User("cs", "123", "customer_service")
    return Package(
        customer_id="C001",
        weight=5,
        dimensions=(10, 10, 10),
        declared_value=100,
        description="Test",
        service_type=STANDARD_SERVICE,
        special_services=[],
        distance_km=10,
        created_by=user
    )


def test_prepaid_customer_payment():
    cust = Customer("C001", "Alice", "Addr", "123", "a@mail", "Prepaid", "Prepaid")
    pkg = create_test_package()

    record = cust.pay_for_package(pkg)

    assert record.amount == 0
    assert record.method == "Prepaid"


def test_contract_customer_monthly_bill():
    cust = Customer("C002", "Bob", "Addr", "123", "b@mail", "Contract", "Monthly")
    pkg = create_test_package()

    record = cust.pay_for_package(pkg)

    assert record.method == "Monthly Billing"
    assert BillingSystem.get_monthly_statement("C002") is not None
