#!/usr/bin/env python3
import datetime
import sys

from chinese_calendar import get_holiday_detail, is_workday

# 节假日英文名 → 中文名（chinese_calendar 返回的是英文名，日历上展示中文）
_HOLIDAY_CN = {
    "New Year's Day": "元旦",
    "Spring Festival": "春节",
    "Tomb-sweeping Day": "清明节",
    "Labour Day": "劳动节",
    "Dragon Boat Festival": "端午节",
    "Mid-autumn Festival": "中秋节",
    "National Day": "国庆节",
}

try:  # 较新版本的 chinese_calendar 提供节假日名称接口
    from chinese_calendar.constants import holidays as _HOLIDAY_NAMES
except ImportError:  # pragma: no cover
    _HOLIDAY_NAMES = {}


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


def get_calendar_day_info(date: datetime.date) -> dict:
    """获取日历单日展示信息（类型、角标、节假日名称）。

    Returns:
        dict: {
            'date_type': 'workday' | 'weekend' | 'holiday',
            'mark': '休' | '班' | '',   # 日历角标：休=放假，班=调休上班
            'holiday_name': str,        # 节假日名称，如 '国庆节'，无则空串
            'is_rest_day': bool,        # 是否放假（含周末与法定节假日）
        }
    """
    date_type = get_date_type(date)
    is_holiday_flag, holiday_name = get_holiday_detail(date)

    holiday_name_str = _HOLIDAY_CN.get(
        holiday_name or _HOLIDAY_NAMES.get(date, '') or '', ''
    ) or ''

    # 角标逻辑与官方放假安排一致：
    #   放假的日子（法定节假日/周末）→ 休；因调休而在周末上班的日子 → 班
    try:
        is_rest = not is_workday(date)
    except NotImplementedError:  # pragma: no cover - 超出数据年份
        is_rest = date.weekday() >= 5

    if is_rest:
        mark = '休'
    elif date.weekday() >= 5 and not is_holiday_flag:
        # 周末但需要上班（调休补班）
        mark = '班'
    else:
        mark = ''

    return {
        'date_type': date_type,
        'mark': mark,
        'holiday_name': holiday_name_str,
        'is_rest_day': is_rest,
    }


def get_month_calendar(year: int, month: int) -> list:
    """获取某月全部日期的日历信息列表，供 Web 面板渲染日历。"""
    days = []
    probe = datetime.date(year, month, 1)
    while probe.month == month:
        info = get_calendar_day_info(probe)
        days.append({'date': probe.strftime('%Y-%m-%d'), 'weekday': probe.weekday(), **info})
        probe += datetime.timedelta(days=1)
    return days

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
