import argparse
from importlib.metadata import version

from curfew.config import load_config
from curfew.curfew_main import main
from curfew.uninstaller import uninstall


def run_daemon():
    """
    这里原有是使用daemon，现在改为前台运行，仍然叫daemon是遗留。
    """
    config = load_config()
    main(config)


def run_init():
    import curfew.init as main_module
    main_module.main()


def run_web():
    import curfew.app as app_module
    app_module.webbrowser.open('http://localhost:8080')
    app_module.app.run(debug=True, port=8080)


def run_uninstall():
    uninstall()


def get_version():
    try:
        return version('curfew')
    except Exception:
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