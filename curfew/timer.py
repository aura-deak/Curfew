#!/usr/bin/env python3
import subprocess
import time
from datetime import datetime

def get_active_time():
    # 1. 尝试用 journalctl 获取最后一次唤醒时间
    try:
        # 执行 journalctl 命令，捕获输出
        result = subprocess.run(
            [
                'journalctl', '-k', '--no-pager', '-g', 'PM: suspend exit',
                '-o', 'short-iso', '-q'
            ],
            capture_output=True,
            text=True,
            check=False  # 不抛出异常，我们自行处理返回码
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
        # 如果 journalctl 执行出错（如命令不存在），则直接回退
        pass

    # 2. 回退：从未休眠，读取 /proc/uptime 的第一个值（整数秒）
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = int(float(f.read().split()[0]))
    return uptime_seconds

if __name__ == '__main__':
    while True:
        active_seconds = get_active_time()
        print(active_seconds)

