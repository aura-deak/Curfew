#!/usr/bin/env python3
import datetime
import sys
from chinese_calendar import get_holiday_detail, is_workday

def get_date_type(date=None):
    if date is None:
        date = datetime.datetime.now().date()

    if is_workday(date):
        return 'workday'

    is_holiday, holiday_name = get_holiday_detail(date)

    if holiday_name is not None:
        return 'holiday'

    weekday = date.weekday()
    if weekday in (4, 5, 6):
        return 'weekend'

    return 'workday'

if __name__ == "__main__":
    date_type_names = {
        'workday': '工作日',
        'weekend': '周末',
        'holiday': '节假日'
    }

    if len(sys.argv) > 1:
        try:
            date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        except ValueError:
            print(f"无效的日期格式，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    else:
        date = datetime.datetime.now().date()

    result = get_date_type(date)
    print(f"{date} ({date.strftime('%A')}): {date_type_names[result]}")

    if len(sys.argv) > 1:
        is_holiday, holiday_name = get_holiday_detail(date)
        print(f"  is_workday: {is_workday(date)}")
        print(f"  is_holiday: {is_holiday}, name: {holiday_name}")
        print(f"  weekday: {date.weekday()} (0=Monday, ..., 6=Sunday)")
