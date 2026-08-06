#!/usr/bin/env python3
"""Curfew 命令行接口"""

import argparse
from importlib.metadata import version

from curfew.config import load_config, AppConfig
from curfew.curfew_main import main
from curfew.uninstaller import uninstall


def run_daemon() -> None:
    """以 daemon 模式启动（前台运行）
    
    原为使用 python-daemon，现改为前台运行，但命名保持为 daemon
    """
    config: AppConfig = load_config()
    main(config)


def run_init() -> None:
    """运行初始化配置向导"""
    import curfew.init as init_module
    init_module.main()


def run_web() -> None:
    """启动 Web 管理界面"""
    import curfew.app as app_module
    app_module.webbrowser.open('http://localhost:8080')
    app_module.app.run(debug=True, port=8080)


def run_uninstall() -> None:
    """卸载应用并清除配置"""
    uninstall()


def get_version() -> str:
    """获取应用版本号
    
    Returns:
        str: 版本号字符串
    """
    try:
        return version('curfew')
    except Exception:
        return '0.0.0'


def cli() -> None:
    """命令行接口主函数"""
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

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}',
        help='显示版本信息'
    )

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