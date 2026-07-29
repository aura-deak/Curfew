#!/usr/bin/env python3
import logging
import subprocess
import threading

"""
妈的，收个信号这么麻烦，就为了解决个suspend的问题
虽然是ai代劳，但还是觉得很烦
代码看着极其不优雅，奈何我自己的优雅写法死活跑不起来
我已经不想搞了，我已经在这个问题上浪费了一下午了
What can I say
"""

logger = logging.getLogger(__name__)

# 系统从睡眠恢复时的 uptime（秒）
_uptime_when_suspend = 0.0
_lock = threading.Lock()


def _get_uptime():
    """从 /proc/uptime 获取系统运行秒数"""
    try:
        with open('/proc/uptime', 'r') as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0


def _record_suspend_wake():
    """记录从睡眠恢复时的 uptime"""
    global _uptime_when_suspend
    uptime = _get_uptime()
    with _lock:
        _uptime_when_suspend = uptime
    logger.info(f"系统从睡眠恢复，记录 uptime_when_suspend = {uptime:.1f}s")


def _listen_prepare_for_sleep():
    """后台线程：通过 dbus-monitor 监听 PrepareForSleep(false) 信号"""
    try:
        proc = subprocess.Popen(
            ['dbus-monitor', '--system',
             "type='signal',sender='org.freedesktop.login1',interface='org.freedesktop.login1.Manager',member='PrepareForSleep'"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        expecting_value = False
        for line in proc.stdout:
            stripped = line.strip()
            # 检测到 PrepareForSleep 信号头，下一行是参数值
            if 'PrepareForSleep' in stripped:
                expecting_value = True
                continue
            if expecting_value and stripped == 'boolean false':
                _record_suspend_wake()
            expecting_value = False
    except FileNotFoundError:
        logger.warning("dbus-monitor 不可用，无法监听 PrepareForSleep 信号")
    except Exception as e:
        logger.error(f"监听 PrepareForSleep 信号出错: {e}")


def _start_listener():
    """启动 dbus 监听线程（守护线程，随主进程退出）"""
    t = threading.Thread(target=_listen_prepare_for_sleep, daemon=True)
    t.start()
    logger.info("已启动 PrepareForSleep 信号监听")


def get_active_time():
    """
    获取当前使用秒数。
    计算方式：当前 uptime - 上次从睡眠恢复时记录的 uptime。
    如果从未收到过 PrepareForSleep(false)，则返回当前 uptime（即开机以来的全部时间）。
    """
    current_uptime = _get_uptime()
    with _lock:
        return int(current_uptime - _uptime_when_suspend)


# 模块导入时自动启动监听
_start_listener()

if __name__ == '__main__':
    while True:
        active_seconds = get_active_time()
        print(active_seconds)

