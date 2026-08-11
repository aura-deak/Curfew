#!/usr/bin/env python3
"""Curfew 主逻辑 - 监控和执行定时关机/睡眠"""

import datetime
import signal
import sys
import time
from datetime import timedelta

import plyer

from curfew.config import load_config, save_config, AppConfig
from curfew.date_type import get_date_type
from curfew.shutdown import shutdown
from curfew.timer import get_active_time


def _compute_banned_until(ban_duration_minutes: int) -> str:
    """计算禁用到期时间的 ISO 格式字符串"""
    return (datetime.datetime.now() + timedelta(minutes=ban_duration_minutes)).isoformat()


def _is_banned_period_active(banned_until_str: str) -> bool:
    """判断禁用期是否仍在活跃状态"""
    return datetime.datetime.now() < datetime.datetime.fromisoformat(banned_until_str)


def signal_handler(signum: int, frame) -> None:
    """信号处理器"""
    print(f"收到信号 {signum}，准备退出...")
    sys.exit(0)


def is_in_restricted_hours(
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int
) -> bool:
    """判断当前时间是否在指定的时间段内
    
    Args:
        start_hour: 开始小时
        start_minute: 开始分钟
        end_hour: 结束小时
        end_minute: 结束分钟
        
    Returns:
        bool: 是否在时间段内
    """
    now = datetime.datetime.now().time()
    start_time = datetime.time(start_hour, start_minute)
    end_time = datetime.time(end_hour, end_minute)

    if start_time < end_time:
        return start_time <= now <= end_time
    else:
        return now >= start_time or now <= end_time


def is_in_restricted_hours_for_today(restricted_hours) -> bool:
    """判断当前时间是否在今天的禁用时段内
    
    Args:
        restricted_hours: RestrictedHours 对象或字典
        
    Returns:
        bool: 是否在禁用时段内
    """
    date_type = get_date_type()

    # 支持 RestrictedHours 对象
    if hasattr(restricted_hours, date_type):
        hours_list = getattr(restricted_hours, date_type, [])
    # 支持字典格式（向后兼容）
    elif isinstance(restricted_hours, dict):
        if date_type not in restricted_hours:
            return False
        hours_list = restricted_hours.get(date_type, [])
    else:
        return False

    for period in hours_list:
        # 支持 TimeSlot 对象
        if hasattr(period, 'start_hour'):
            start_hour = period.start_hour
            start_minute = period.start_minute
            end_hour = period.end_hour
            end_minute = period.end_minute
        # 支持字典格式（向后兼容）
        else:
            start_hour = period['start_hour']
            start_minute = period['start_minute']
            end_hour = period['end_hour']
            end_minute = period['end_minute']
        
        if is_in_restricted_hours(start_hour, start_minute, end_hour, end_minute):
            return True
    return False


def is_within_five_minutes_of_restricted_time(
    start_hour: int,
    start_minute: int
) -> bool:
    """判断当前时间是否在禁用时段开始前 5 分钟内
    
    Args:
        start_hour: 禁用时段开始小时
        start_minute: 禁用时段开始分钟
        
    Returns:
        bool: 是否在 5 分钟内
    """
    now = datetime.datetime.now().time()
    start_time = datetime.time(start_hour, start_minute)
    five_minutes_later = (
        datetime.datetime.combine(datetime.date.today(), start_time) + 
        datetime.timedelta(minutes=5)
    ).time()
    return start_time <= now <= five_minutes_later


def is_is_within_five_minutes_of_restricted_time_for_today(restricted_hours) -> bool:
    """判断当前时间是否在今天禁用时段开始前 5 分钟内
    
    Args:
        restricted_hours: RestrictedHours 对象或字典
        
    Returns:
        bool: 是否在 5 分钟内
    """
    date_type = get_date_type()

    # 支持 RestrictedHours 对象
    if hasattr(restricted_hours, date_type):
        hours_list = getattr(restricted_hours, date_type, [])
    # 支持字典格式（向后兼容）
    elif isinstance(restricted_hours, dict):
        if date_type not in restricted_hours:
            return False
        hours_list = restricted_hours.get(date_type, [])
    else:
        return False

    for period in hours_list:
        # 支持 TimeSlot 对象
        if hasattr(period, 'start_hour'):
            start_hour = period.start_hour
            start_minute = period.start_minute
        # 支持字典格式（向后兼容）
        else:
            start_hour = period['start_hour']
            start_minute = period['start_minute']
        
        if is_within_five_minutes_of_restricted_time(start_hour, start_minute):
            return True
    return False


def main(config: AppConfig) -> None:
    """主监控循环
    
    Args:
        config: AppConfig 配置对象
    """
    # 直接从 config 对象访问属性，有完整的类型提示
    restricted_hours = config.restricted_hours
    continuous_usage_limits = config.continuous_usage_limits
    check_interval = 1
    debug = config.debug

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
        limit = getattr(continuous_usage_limits, date_type)
        print(f"  {date_type_names[date_type]}: {limit} 分钟")
    
    for date_type in ['workday', 'weekend', 'holiday']:
        hours_list = getattr(restricted_hours, date_type)
        print(f"{date_type_names[date_type]}禁用时段:")
        if hours_list:
            for i, period in enumerate(hours_list, 1):
                print(f"  {i}. {period.start_hour}:{period.start_minute:02d} - {period.end_hour}:{period.end_minute:02d}")
        else:
            print("  无")
    
    current_date_type = get_date_type()
    print(f"\n当前日期类型: {date_type_names[current_date_type]}")

    if config.banned_until:
        if _is_banned_period_active(config.banned_until):
            print("仍在禁用期内，执行关机...")
            shutdown(config.shutdown_command, debug=debug)
            return
        else:
            config.banned_until = ""
            save_config(config)

    remind_times = 0

    while True:
        if config.banned_until:
            if _is_banned_period_active(config.banned_until):
                break
            else:
                config.banned_until = ""
                save_config(config)
                continue

        if is_in_restricted_hours_for_today(restricted_hours):
            print("检测到当前时间在禁用时段内")
            if not config.banned_until:
                config.banned_until = _compute_banned_until(config.ban_duration_minutes)
                save_config(config)
            break
        elif is_is_within_five_minutes_of_restricted_time_for_today(restricted_hours):
            plyer.notification.notify(
                title="Curfew 提醒",
                message="距离禁用时段开始还有不到 5 分钟，请保存工作并准备关机。",
                timeout=10
            )
            print("距离禁用时段开始还有不到 5 分钟")
        else:
            current_date_type = get_date_type()
            current_limit = getattr(continuous_usage_limits, current_date_type)
            
            if current_limit > 0:
                uptime_seconds = get_active_time()
                if uptime_seconds >= current_limit * 60:
                    print(f"连续使用时间超过限制（{current_limit}分钟），当前运行时间: {uptime_seconds // 60}分钟")
                    if not config.banned_until:
                        config.banned_until = _compute_banned_until(config.ban_duration_minutes)
                        save_config(config)
                    break
                elif uptime_seconds >= (current_limit - 5) * 60 and remind_times == 0:
                    plyer.notification.notify(
                        title="Curfew 提醒",
                        message=f"距离连续使用时间限制结束还有不到 5 分钟，请保存工作并准备关机。",
                        timeout=10
                    )
                    remind_times = 1
                    print(f"距离连续使用时间限制结束还有不到 5 分钟")
            
            print(f"当前时间不在禁用时段内（{date_type_names[current_date_type]}），1秒后再次检测")
            time.sleep(check_interval)
    
    if config.banned_until and _is_banned_period_active(config.banned_until):
        print("仍在禁用期内，执行关机...")
    
    print("准备执行关机命令")
    shutdown(config.shutdown_command, debug=debug)
    
    print("Curfew 退出")


if __name__ == "__main__":
    config = load_config()
    main(config)