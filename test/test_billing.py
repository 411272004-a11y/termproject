#單純測試billing

'''
1確定各種資料的情況下能不能建立付款紀錄
2付完錢後，是否正確儲存紀錄
3付款金額是否與billing_cost一樣
'''



from billing import BillingSystem
from customer import Customer
from service import STANDARD_SERVICE
from package import Package
from user import User
from warehouse import Warehouse


def setup_package():
    Warehouse("W-001", "Test", 10)
    user = User("admin", "123", "admin")
    return Package(
        customer_id="C100",
        weight=10,
        dimensions=(10, 10, 10),
        declared_value=200,
        description="Billing Test",
        service_type=STANDARD_SERVICE,
        special_services=[],
        distance_km=20,
        created_by=user
    )


def test_pay_now_record_created():
    BillingSystem.all_records.clear()

    cust = Customer("C100", "Tom", "Addr", "123", "t@mail", "Non-Contract", "Cash")
    pkg = setup_package()

    record = BillingSystem.pay_now(cust, pkg)

    assert record in BillingSystem.all_records
    assert record.amount == pkg.billing_cost
