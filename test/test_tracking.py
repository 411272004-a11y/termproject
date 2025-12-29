#測試tracking
'''
1. 是否能正確建立追蹤事件紀錄。
2. 追蹤事件是否能依時間順序正確儲存。
3. 針對同一追蹤編號，是否能正確取得完整的追蹤歷史。
'''


from tracking import TrackingEvent
from datetime import datetime, timedelta


def test_tracking_history_order():
    TrackingEvent.all_events.clear()

    t = "TRACK-001"
    e1 = TrackingEvent.log_event(t, "A", "Created")
    e2 = TrackingEvent.log_event(t, "B", "Transit")
    e3 = TrackingEvent.log_event(t, "C", "Delivered")

    e1.timestamp = datetime.now()
    e2.timestamp = e1.timestamp + timedelta(minutes=1)
    e3.timestamp = e2.timestamp + timedelta(minutes=1)

    history = TrackingEvent.get_history(t)

    assert history == [e1, e2, e3]
    assert TrackingEvent.get_current_status(t) == "Delivered"
