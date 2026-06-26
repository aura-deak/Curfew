#!/usr/bin/env python3
from .config import load_config, save_config
from .autostart import setup_autostart
import sys

def select_option(options, title, subtitle=""):
    print(f"\n{title}")
    if subtitle:
        print(subtitle)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    while True:
        try:
            choice = int(input("请选择: ")) - 1
            if 0 <= choice < len(options):
                return choice
            else:
                print("无效选项，请重新选择")
        except ValueError:
            print("无效输入，请输入数字")

def setup_config():
    action_options = ["关机", "睡眠"]
    action_choice = select_option(action_options, "请选择操作类型")
    
    autostart_options = ["cron 定时任务", "稍后自行设置"]
    autostart_choice = select_option(autostart_options, "请选择自启动形式")
    
    autostart_map = {
        0: 'cron',
        1: 'manual'
    }
    autostart_type = autostart_map.get(autostart_choice, 'manual')
    
    if action_choice == 0:
        shutdown_command = ['shutdown', 'now']
    else:
        shutdown_command = ['systemctl', 'suspend']
    
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
    
    save_config(config)
    print("配置已保存")
    
    print("\n提示：")
    print("- 您尚未配置禁用时段")
    print("- 请运行 app.py 来添加和管理禁用时段")
    print("  命令：uv run python app.py")
    
    if autostart_type != 'manual':
        setup_autostart(autostart_type)

def main():
    try:
        config = load_config()
        print("配置已存在，重新初始化配置...")
    except FileNotFoundError:
        print("首次启动，开始配置")
    
    setup_config()

if __name__ == "__main__":
    main()
