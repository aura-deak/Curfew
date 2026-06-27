#!/usr/bin/env python3
import time
import signal
import sys
import subprocess
import argparse
from importlib.metadata import version
from .config import load_config
from .time_check import is_in_restricted_hours_for_today
from .shutdown import shutdown
from .date_type import get_date_type
from .uninstaller import uninstall

def get_uptime_seconds():
    try:
        result = subprocess.run(['bash', '-c', 'uptime -r | awk \'{print int($2)}\''], capture_output=True, text=True)
        return int(result.stdout.strip())
    except Exception:
        return 0

def signal_handler(signum, frame):
    print(f"收到信号 {signum}，准备退出...")
    sys.exit(0)

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
        else:
            current_date_type = get_date_type()
            current_limit = continuous_usage_limits.get(current_date_type, 0)
            
            if current_limit > 0:
                uptime_seconds = get_uptime_seconds()
                if uptime_seconds >= current_limit * 60:
                    print(f"连续使用时间超过限制（{current_limit}分钟），当前运行时间: {uptime_seconds // 60}分钟")
                    break
            
            print(f"当前时间不在禁用时段内（{date_type_names[current_date_type]}），1秒后再次检测")
            time.sleep(check_interval)
    
    print("准备执行关机命令")
    shutdown(config['shutdown_command'], debug=debug)
    
    print("Curfew 退出")

def run_daemon():
    config = load_config()
    if config.get('debug', False):
        main(config)
    else:
        from daemon import DaemonContext
        with DaemonContext():
            main(config)

def run_init():
    from . import main as main_module
    main_module.main()

def run_web():
    from . import app as app_module
    app_module.webbrowser.open('http://localhost:8080')
    app_module.app.run(debug=True, port=8080)

def run_uninstall():
    uninstall()

def get_version():
    try:
        v = version('curfew')
        if v != '0.0.0':
            return v
    except Exception:
        pass
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(['git', 'describe', '--tags'], capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return '0.0.0'

def cli():
    __version__ = get_version()
    
    parser = argparse.ArgumentParser(
        prog='curfew',
        description='Curfew - 电脑定时关机/睡眠工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''示例用法:
  curfew              以 daemon 模式启动（默认）
  curfew daemon       以 daemon 模式启动
  curfew init         初始化配置
  curfew web          启动 Web 管理界面
  curfew uninstall    卸载并清除配置
  curfew -v           显示版本信息
  curfew -h           显示帮助信息'''
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}', help='显示版本信息')
    
    subparsers = parser.add_subparsers(dest='command', help='可用子命令')
    
    subparsers.add_parser('daemon', help='以 daemon 模式启动（默认）')
    subparsers.add_parser('init', help='初始化配置，执行配置向导')
    subparsers.add_parser('web', help='启动 Web 管理界面')
    subparsers.add_parser('uninstall', help='卸载并清除系统配置')
    
    args = parser.parse_args()
    
    if args.command is None or args.command == 'daemon':
        run_daemon()
    elif args.command == 'init':
        run_init()
    elif args.command == 'web':
        run_web()
    elif args.command == 'uninstall':
        run_uninstall()

if __name__ == "__main__":
    cli()
