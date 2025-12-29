#測試warehouse
'''
1. 倉庫物件是否能正確建立。
2. 倉庫容量是否能被正確設定與管理。
3. 系統是否能正確追蹤與使用已建立的倉庫資料。
'''


import pytest
from warehouse import Warehouse


def test_warehouse_capacity_limit():
    wh = Warehouse("W-TEST", "Test", capacity=1)

    wh.add_package("PKG-1")

    with pytest.raises(ValueError):
        wh.add_package("PKG-2")
