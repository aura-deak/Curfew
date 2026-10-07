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


def _time_slots_to_dicts(slots) -> list:
    """把 TimeSlot 对象列表或字典列表统一为字典列表。"""
    result = []
    for p in slots:
        if hasattr(p, 'start_hour'):
            result.append({
                'start_hour': p.start_hour,
                'start_minute': p.start_minute,
                'end_hour': p.end_hour,
                'end_minute': p.end_minute,
            })
        else:
            result.append({
                'start_hour': p['start_hour'],
                'start_minute': p['start_minute'],
                'end_hour': p['end_hour'],
                'end_minute': p['end_minute'],
            })
    return result


def _is_in_slots_now(slots: list, now_time=None) -> bool:
    """判断当前时间是否落在任意限制时段内。"""
    if now_time is None:
        now_time = datetime.datetime.now().time()
    for p in slots:
        start_time = datetime.time(p['start_hour'], p['start_minute'])
        end_time = datetime.time(p['end_hour'], p['end_minute'])
        if start_time < end_time:
            if start_time <= now_time <= end_time:
                return True
        else:
            if now_time >= start_time or now_time <= end_time:
                return True
    return False


def _is_within_five_minutes_of_slots_now(slots: list, now_time=None) -> bool:
    """判断当前时间是否在任一限制时段开始前 5 分钟内。"""
    if now_time is None:
        now_time = datetime.datetime.now().time()
    for p in slots:
        start_time = datetime.time(p['start_hour'], p['start_minute'])
        five_later = (
            datetime.datetime.combine(datetime.date.today(), start_time)
            + datetime.timedelta(minutes=5)
        ).time()
        if start_time <= now_time <= five_later:
            return True
    return False


def _ov_get(override, key, default=None):
    """读取单日设定字段，同时兼容 DailyOverride 模型与原始字典。"""
    if isinstance(override, dict):
        return override.get(key, default)
    return getattr(override, key, default)


def get_effective_schedules_for_date(config: AppConfig, date: datetime.date):
    """获取某日生效的限制设定。

    单日设定（daily_overrides）优先级最高：命中该日期时，限制时段 / 连续使用限制 /
    每日总限制全部以单日设定为准，完全替代日期类型设定。未命中则回退到日期类型
    （工作日/周末/节假日）。

    Returns:
        (time_slots, continuous_limit_minutes, total_limit_minutes, source)
        time_slots: 字典列表 [{start_hour, start_minute, end_hour, end_minute}]
        source: 'override' 表示命中单日设定，否则为日期类型名（workday/weekend/holiday）
    """
    date_str = date.strftime('%Y-%m-%d')
    for o in config.daily_overrides:
        if _ov_get(o, 'date') == date_str:
            return (
                _time_slots_to_dicts(_ov_get(o, 'time_ranges', []) or []),
                _ov_get(o, 'continuous_limit_minutes', 0) or 0,
                _ov_get(o, 'daily_total_limit_minutes', 0) or 0,
                'override',
            )
    dt = get_date_type(date)
    return (
        _time_slots_to_dicts(getattr(config.restricted_hours, dt)),
        getattr(config.continuous_usage_limits, dt),
        getattr(config.total_usage_limits, dt),
        dt,
    )


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
    restricted_hours = config.restricted_hours
    continuous_usage_limits = config.continuous_usage_limits
    total_usage_limits = config.total_usage_limits
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
    total_remind_times = 0

    # 连续使用计时的本地基线：以"墙钟流逝时间"累加，而不是按循环次数 +1。
    # 旧实现每循环一次固定 +check_interval 秒，但循环体本身耗时（journalctl 子进程、
    # 磁盘读写）会让每轮实际耗时 > 1 秒，导致总使用时间比真实时间"走时慢"。
    local_total_base = config.total_usage_seconds
    total_baseline_mono = time.monotonic()
    save_interval = 5.0            # 周期性落盘间隔（秒），降低磁盘写放大
    last_saved_mono = 0.0
    last_saved_at = 0.0            # 上次成功落盘时的墙钟时间
    last_saved_value = None        # 上次由本进程写入的累计值（用于识别外部修改）

    def _persist(total_seconds: int, extra: dict | None = None) -> bool:
        """把累计使用时间写回配置文件，返回是否写入成功。

        通过重新加载最新配置再写入，尽量避免覆盖 Web界面刚保存的配置修改。
        """
        nonlocal last_saved_mono, last_saved_at, last_saved_value
        try:
            fresh = load_config()
            fresh.total_usage_seconds = total_seconds
            fresh.total_usage_saved_at = time.time()
            if fresh.total_usage_date != datetime.datetime.now().strftime('%Y-%m-%d'):
                fresh.total_usage_date = datetime.datetime.now().strftime('%Y-%m-%d')
            if extra:
                for key, value in extra.items():
                    setattr(fresh, key, value)
            save_config(fresh)
            last_saved_mono = time.monotonic()
            last_saved_at = time.time()
            last_saved_value = total_seconds
            return True
        except Exception as exc:
            print(f"保存累计使用时间失败: {exc}")
            return False

    while True:
        config = load_config()
        restricted_hours = config.restricted_hours
        continuous_usage_limits = config.continuous_usage_limits
        total_usage_limits = config.total_usage_limits
        debug = config.debug

        today_str = datetime.datetime.now().strftime('%Y-%m-%d')

        if config.banned_until:
            if _is_banned_period_active(config.banned_until):
                break
            else:
                config.banned_until = ""
                save_config(config)
                continue

        # 今天生效的限制：优先单日设定，其次日期类型
        effective_slots, effective_continuous, effective_total, effective_source = (
            get_effective_schedules_for_date(config, datetime.datetime.now().date())
        )

        if _is_in_slots_now(effective_slots):
            print("检测到当前时间在禁用时段内")
            if not config.banned_until:
                config.banned_until = _compute_banned_until(config.ban_duration_minutes)
                save_config(config)
            break
        elif _is_within_five_minutes_of_slots_now(effective_slots):
            plyer.notification.notify(
                title="Curfew 提醒",
                message="距离禁用时段开始还有不到 5 分钟，请保存工作并准备关机。",
                timeout=10
            )
            print("距离禁用时段开始还有不到 5 分钟")
        else:
            current_date_type = get_date_type()
            current_limit = effective_continuous
            uptime_seconds = get_active_time()

            if current_limit > 0:
                if uptime_seconds >= current_limit * 60:
                    print(f"连续使用时间超过限制（{current_limit}分钟），当前运行时间: {uptime_seconds // 60}分钟")
                    if not config.banned_until:
                        banned = _compute_banned_until(config.ban_duration_minutes)
                        config.banned_until = banned
                        _persist(local_total_base + int(time.monotonic() - total_baseline_mono),
                                 {"banned_until": banned})
                    break
                elif uptime_seconds >= (current_limit - 5) * 60 and remind_times == 0:
                    plyer.notification.notify(
                        title="Curfew 提醒",
                        message=f"距离连续使用时间限制结束还有不到 5 分钟，请保存工作并准备关机。",
                        timeout=10
                    )
                    remind_times = 1
                    print(f"距离连续使用时间限制结束还有不到 5 分钟")
            
            total_limit = effective_total

            # ---- 总使用时间：按墙钟流逝时间累加，不随循环耗时漂移 ----
            if config.total_usage_date != today_str:
                # 跨天（或首次运行）：重置为新的一天
                local_total_base = 0
                total_baseline_mono = time.monotonic()
                _persist(0)
            elif (
                config.total_usage_seconds != last_saved_value
            ):
                # 外部（如 Web 界面保存配置或手动改文件）修改了累计值：
                # 以外部值为准重新对齐基线，避免相互覆盖。
                local_total_base = config.total_usage_seconds
                total_baseline_mono = time.monotonic()

            total_usage_now = local_total_base + int(time.monotonic() - total_baseline_mono)

            now_mono = time.monotonic()
            if total_usage_now != config.total_usage_seconds and (
                now_mono - last_saved_mono >= save_interval
                or total_usage_now >= (total_limit * 60 if total_limit > 0 else float('inf'))
            ):
                _persist(total_usage_now)
            
            if total_limit > 0:
                total_limit_seconds = total_limit * 60
                if total_usage_now >= total_limit_seconds:
                    print(f"总使用时间超过限制（{total_limit}分钟），当前累计: {total_usage_now // 60}分钟")
                    if not config.banned_until:
                        passed = {
                            "banned_until": _compute_banned_until(config.ban_duration_minutes),
                            "total_usage_seconds": total_usage_now,
                            "total_usage_date": today_str,
                        }
                        _persist(total_usage_now, passed)
                    break
                elif total_usage_now >= (total_limit - 5) * 60 and total_remind_times == 0:
                    plyer.notification.notify(
                        title="Curfew 提醒",
                        message=f"距离每日总使用时间限制结束还有不到 5 分钟，请保存工作并准备关机。",
                        timeout=10
                    )
                    total_remind_times = 1
                    print(f"距离每日总使用时间限制结束还有不到 5 分钟")
            
            total_limit_val = getattr(total_usage_limits, current_date_type)
            total_info = f", 今日累计: {total_usage_now // 60}分钟" if total_limit_val > 0 else ""
            print(f"当前时间不在禁用时段内（{date_type_names[current_date_type]}），连续使用时间: {uptime_seconds // 60}分钟，总使用时间: {total_usage_now // 60}分钟，1秒后再次检测{total_info}")
            time.sleep(check_interval)
    
    if config.banned_until and _is_banned_period_active(config.banned_until):
        print("仍在禁用期内，执行关机...")
    
    print("准备执行关机命令")
    shutdown(config.shutdown_command, debug=debug)
    
    print("Curfew 退出")


if __name__ == "__main__":
    config = load_config()
    main(config)
