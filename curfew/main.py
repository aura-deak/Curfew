#!/usr/bin/env python3
from .config import load_config, save_config, get_config_file
from .autostart import setup_autostart
import sys
import os

def setup_config():

    if input("关机（1）或睡眠（2）: ") == '1':
        shutdown_command = ['shutdown', 'now']
    else:
        shutdown_command = ['systemctl', 'suspend']
    
    if input("使用 systemd 服务吗？ (Y/n): ").lower() != 'n':
        autostart_type = 'systemd'
    else:
        autostart_type = 'manual'
    
    config = {
        'autostart_type': autostart_type,
        'shutdown_command': shutdown_command,
        'restricted_hours': {
            'workday': [],
            'weekend': [],
            'holiday': []
        },
        'continuous_usage_limits': {
            'workday': 0,
            'weekend': 0,
            'holiday': 0
        },
        'debug': False
    }
    
    config_file = get_config_file()
    save_config(config)
    print(f"配置已保存到 {config_file}")
    
    print("\n提示：")
    print("- 您尚未配置禁用时段")
    print("- 请运行 curfew web 来添加和管理禁用时段")
    
    if autostart_type != 'manual':
        setup_autostart(autostart_type)

def main():
    get_config_file()
    try:
        load_config()
        print("配置已存在，重新初始化配置...")
    except FileNotFoundError:
        print("首次启动，开始配置")
    
    setup_config()

if __name__ == "__main__":
    main()