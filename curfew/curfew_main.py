#!/usr/bin/env python3
import datetime
import signal
import sys
import time

import plyer

from curfew.config import load_config
from curfew.date_type import get_date_type
from curfew.shutdown import shutdown
from curfew.timer import get_active_time


def signal_handler(signum, frame):
    print(f"收到信号 {signum}，准备退出...")
    sys.exit(0)


def is_in_restricted_hours(start_hour, start_minute, end_hour, end_minute):
    now = datetime.datetime.now().time()
    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)

    if start_time < end_time:
        return start_time <= now <= end_time
    else:
        return now >= start_time or now <= end_time

def is_in_restricted_hours_for_today(restricted_hours_dict):
    date_type = get_date_type()

    if date_type not in restricted_hours_dict:
        return False

    hours_list = restricted_hours_dict.get(date_type, [])

    for period in hours_list:
        if is_in_restricted_hours(
                period['start_hour'],
                period['start_minute'],
                period['end_hour'],
                period['end_minute']
        ):
            return True
    return False

def is_within_five_minutes_of_restricted_time(start_hour, start_minute):
    now = datetime.datetime.now().time()
    start_time = datetime.time(start_hour, start_minute)
    five_minutes_later = (
                 datetime.datetime.combine(datetime.date.today(), start_time) + datetime.timedelta(minutes=5)).time()
    return start_time <= now <= five_minutes_later

def is_is_within_five_minutes_of_restricted_time_for_today(restricted_hours_dict):
    date_type = get_date_type()

    if date_type not in restricted_hours_dict:
        return False

    hours_list = restricted_hours_dict.get(date_type, [])

    for period in hours_list:
        if is_within_five_minutes_of_restricted_time(
                period['start_hour'],
                period['start_minute'],
        ):
            return True
    return False

def main(config):
    restricted_hours_dict = config.get('restricted_hours', {})

    continuous_usage_limits = config.get('continuous_usage_limits', {})
    check_interval = 1
    debug = config.get('debug', False)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Curfew 启动，开始检测禁用时段")
    print("检测间隔: 1 秒")

    date_type_names = {
        'workday': '工作日',
        'weekend': '周末',
        'holiday': '节假日'
    }

    print("连续使用时间限制:")
    for date_type in ['workday', 'weekend', 'holiday']:
        limit = continuous_usage_limits.get(date_type, 0)
        print(f"  {date_type_names[date_type]}: {limit} 分钟")
    
    for date_type in ['workday', 'weekend', 'holiday']:
        hours_list = restricted_hours_dict.get(date_type, [])
        print(f"{date_type_names[date_type]}禁用时段:")
        if hours_list:
            for i, period in enumerate(hours_list, 1):
                print(f"  {i}. {period['start_hour']}:{period['start_minute']:02d} - {period['end_hour']}:{period['end_minute']:02d}")
        else:
            print("  无")
    
    current_date_type = get_date_type()
    print(f"\n当前日期类型: {date_type_names[current_date_type]}")
    
    while True:
        if is_in_restricted_hours_for_today(restricted_hours_dict):
            print("检测到当前时间在禁用时段内")
            break
        elif is_is_within_five_minutes_of_restricted_time_for_today(restricted_hours_dict):
            plyer.notification.notify(
                title="Curfew 提醒",
                message="距离禁用时段开始还有不到 5 分钟，请保存工作并准备关机。",
                timeout=10
            )
            print("距离禁用时段开始还有不到 5 分钟")
        else:
            current_date_type = get_date_type()
            current_limit = continuous_usage_limits.get(current_date_type, 0)
            
            if current_limit > 0:
                uptime_seconds = get_active_time()
                if uptime_seconds >= current_limit * 60:
                    print(f"连续使用时间超过限制（{current_limit}分钟），当前运行时间: {uptime_seconds // 60}分钟")
                    break
                elif uptime_seconds >= (current_limit - 5) * 60 :
                    plyer.notification.notify(
                        title="Curfew 提醒",
                        message=f"距离连续使用时间限制结束还有不到 5 分钟，请保存工作并准备关机。",
                        timeout=10
                    )
                    print(f"距离连续使用时间限制结束还有不到 5 分钟")
            
            print(f"当前时间不在禁用时段内（{date_type_names[current_date_type]}），1秒后再次检测")
            time.sleep(check_interval)
    
    print("准备执行关机命令")
    shutdown(config['shutdown_command'], debug=debug)
    
    print("Curfew 退出")

if __name__ == "__main__":
    config = load_config()
    main(config)