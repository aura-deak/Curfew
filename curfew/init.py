#!/usr/bin/env python3
"""初始化配置的命令行工具"""

from typing import List

from curfew.autostart import setup_autostart
from curfew.config import (
    get_config_file,
    load_config,
    save_config,
    create_default_config,
    AppConfig,
)


def setup_config() -> AppConfig:
    """交互式设置配置
    
    Returns:
        AppConfig: 用户配置的配置对象
    """
    # 获取关机命令
    shutdown_input = input("关机（1）或睡眠（2）: ").strip()
    shutdown_command: List[str] = (
        ["shutdown", "now"] if shutdown_input == "1"
        else ["systemctl", "suspend"]
    )
    
    # 获取自启动类型
    autostart_input = input("使用 systemd 服务吗？ (Y/n): ").strip().lower()
    autostart_type = "systemd" if autostart_input != "n" else "manual"
    
    # 使用 create_default_config 创建 AppConfig 对象
    config = create_default_config(
        autostart_type=autostart_type,
        shutdown_command=shutdown_command
    )
    
    # 保存配置（必须使用 AppConfig 对象）
    config_file = get_config_file()
    save_config(config)
    print(f"配置已保存到 {config_file}")
    
    print("\n提示：")
    print("- 您尚未配置禁用时段")
    print("- 请运行 curfew web 来添加和管理禁用时段")
    
    if autostart_type != "manual":
        setup_autostart(autostart_type)
    
    return config


def main() -> None:
    """主程序入口"""
    config_file = get_config_file()
    
    try:
        load_config()
        print("配置已存在，重新初始化配置...")
    except FileNotFoundError:
        print("首次启动，开始配置")
    
    setup_config()


if __name__ == "__main__":
    main()