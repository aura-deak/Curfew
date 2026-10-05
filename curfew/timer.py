#!/usr/bin/env python3
"""主动使用时间计算模块。

get_active_time() 用于估算"自从上次休眠/唤醒以来，机器保持活跃（未挂起）"的秒数。
该函数被主监控循环和 Web 状态接口高频调用，因此加入了轻量缓存，
避免每次调用都启动 journalctl 子进程（开销很大，正是导致总使用时间"走时慢"的元凶）。
"""
import subprocess
import time
from datetime import datetime

_cache_last_epoch = None  # 上次采样到的"最后唤醒时刻"（Unix 秒）
_cache_base_active = None # 采样时刻对应的活跃秒数
_cache_sample_at = 0.0    # 采样时的墙钟时间
_CACHE_TTL = 10.0         # 缓存有效期（秒），避免频繁启动子进程


def _sample_active_seconds() -> int:
    """真正执行采样：调用 journalctl，必要时回退到 /proc/uptime。"""
    # 1. 尝试用 journalctl 获取最后一次唤醒时间
    try:
        result = subprocess.run(
            [
                'journalctl', '-k', '--no-pager', '-g', 'PM: suspend exit',
                '-o', 'short-iso', '-q'
            ],
            capture_output=True,
            text=True,
            check=False,  # 不抛出异常，我们自行处理返回码
            timeout=3,
        )
        output = result.stdout.strip()
        if output:
            # 取最后一行，提取时间戳（第一个字段）
            last_line = output.splitlines()[-1]
            # 时间戳是第一个空格前的部分，例如 "2026-08-08T10:00:00+0800"
            timestamp_str = last_line.split()[0]
            # 转为 Unix 时间戳（秒）
            last_epoch = datetime.fromisoformat(timestamp_str).timestamp()
            now = time.time()
            return int(now - last_epoch)
    except Exception:
        # 如果 journalctl 执行出错（如命令不存在、超时），则直接回退
        pass

    # 2. 回退：从未休眠，读取 /proc/uptime 的第一个值（整数秒）
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = int(float(f.read().split()[0]))
    return uptime_seconds


def get_active_time():
    """返回自上次唤醒以来的活跃秒数（带缓存，开销低）。

    在 TTL 内直接按墙钟时间线性外推，避免每次调用都启动 journalctl 子进程。
    当跨过 TTL 后会重新采样，以校正休眠期间的时间差。
    """
    global _cache_last_epoch, _cache_base_active, _cache_sample_at

    now = time.time()
    if (
        _cache_base_active is not None
        and (now - _cache_sample_at) < _CACHE_TTL
    ):
        # 用上次采样结果按真实墙钟流逝线性外推，保证"走时准确"。
        return int(_cache_base_active + (now - _cache_sample_at))

    # 超出 TTL，重新采样
    base = _sample_active_seconds()
    _cache_base_active = base
    _cache_sample_at = now
    return base


def clear_active_time_cache() -> None:
    """清空缓存（测试或强制刷新时使用）。"""
    global _cache_last_epoch, _cache_base_active, _cache_sample_at
    _cache_last_epoch = None
    _cache_base_active = None
    _cache_sample_at = 0.0

if __name__ == '__main__':
    while True:
        active_seconds = get_active_time()
        print(active_seconds)
        time.sleep(1)

