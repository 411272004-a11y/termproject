#測試package

'''
1. 包裹物件是否能正確建立。
2. 包裹的重量、尺寸、距離與申報價值是否能正確儲存。
3. 不同物流服務類型下，包裹是否能正確計算其計費金額
'''



from package import Package
from service import STANDARD_SERVICE
from user import User
from warehouse import Warehouse


def test_package_creation_and_cost():
    Warehouse("W-001", "Main WH", 10)
    user = User("cs", "123", "customer_service")

    pkg = Package(
        customer_id="C001",
        weight=5,
        dimensions=(10, 10, 10),
        declared_value=100,
        description="Test",
        service_type=STANDARD_SERVICE,
        special_services=[],
        distance_km=50,
        created_by=user
    )

    assert pkg.tracking_number is not None
    assert pkg.billing_cost > 0
    assert pkg.current_status == "Shipment Created"
