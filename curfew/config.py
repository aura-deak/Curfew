#!/usr/bin/env python3
"""
配置管理模块 - 使用 Pydantic v2 进行类型安全的配置管理

所有配置文件的读取、修改、存储都在本模块进行。
其他模块只需导入 load_config() 和 save_config() 以及相关类型注解。
"""

import json
import os
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


# ========== 时间段模型 ==========
class TimeSlot(BaseModel):
    """表示一个时间段"""
    start_hour: int = Field(..., ge=0, le=23, description="开始小时")
    start_minute: int = Field(default=0, ge=0, le=59, description="开始分钟")
    end_hour: int = Field(..., ge=0, le=23, description="结束小时")
    end_minute: int = Field(default=0, ge=0, le=59, description="结束分钟")


# ========== 限制时段配置 ==========
class RestrictedHours(BaseModel):
    """限制时段配置 - 分工作日、周末、节假日"""
    workday: List[TimeSlot] = Field(default_factory=list, description="工作日禁用时段")
    weekend: List[TimeSlot] = Field(default_factory=list, description="周末禁用时段")
    holiday: List[TimeSlot] = Field(default_factory=list, description="节假日禁用时段")


# ========== 连续使用限制配置 ==========
class ContinuousUsageLimits(BaseModel):
    """连续使用限制 - 分工作日、周末、节假日"""
    workday: int = Field(default=0, ge=0, description="工作日连续使用限制（分钟）")
    weekend: int = Field(default=0, ge=0, description="周末连续使用限制（分钟）")
    holiday: int = Field(default=0, ge=0, description="节假日连续使用限制（分钟）")


# ========== 主配置模型 ==========
class AppConfig(BaseModel):
    """应用主配置模型"""
    autostart_type: Literal["systemd", "upstart", "launchd", "manual"] = Field(
        default="manual",
        description="自启动类型"
    )
    shutdown_command: List[str] = Field(
        default_factory=lambda: ["systemctl", "suspend"],
        description="关机/睡眠命令"
    )
    restricted_hours: RestrictedHours = Field(
        default_factory=RestrictedHours,
        description="禁用时段配置"
    )
    continuous_usage_limits: ContinuousUsageLimits = Field(
        default_factory=ContinuousUsageLimits,
        description="连续使用限制"
    )
    debug: bool = Field(default=False, description="调试模式")

    @field_validator("shutdown_command")
    @classmethod
    def validate_shutdown_command(cls, v: List[str]) -> List[str]:
        """验证关机命令非空"""
        if not v or not isinstance(v, list):
            raise ValueError("shutdown_command 必须是非空列表")
        return v


# ========== 全局单例（缓存当前配置实例）==========
_current_config: AppConfig | None = None


# ========== 核心函数：文件路径 ==========
def get_config_file() -> str:
    """获取配置文件路径
    
    优先级：
    1. 环境变量 CURFEW_CONFIG
    2. $XDG_CONFIG_HOME/curfew.json
    3. ~/.config/curfew.json
    """
    if os.environ.get("CURFEW_CONFIG"):
        return os.environ["CURFEW_CONFIG"]
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "curfew.json"
    )


def get_systemd_service_file() -> str:
    """获取 systemd 服务文件路径"""
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "systemd/user/curfew.service"
    )


# ========== 核心函数：加载配置 ==========
def load_config() -> AppConfig:
    """从文件加载配置并缓存
    
    Returns:
        AppConfig: 解析后的配置对象
        
    Raises:
        FileNotFoundError: 配置文件不存在时抛出
        ValueError: 配置格式错误时抛出
    """
    global _current_config
    
    config_file = get_config_file()
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件不存在: {config_file}\n请先运行 curfew init 进行配置")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # Pydantic 会自动验证所有字段和类型
        config = AppConfig(**raw_data)
        _current_config = config
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"配置文件格式错误（JSON 解析失败）: {e}")
    except TypeError as e:
        raise ValueError(f"配置文件内容与模型不匹配: {e}")


# ========== 核心函数：保存配置 ==========
def save_config(config: AppConfig) -> None:
    """保存配置到文件
    
    Args:
        config: AppConfig 实例
        
    Raises:
        IOError: 文件写入失败时抛出
    """
    global _current_config
    
    config_file = get_config_file()
    dir_path = os.path.dirname(config_file)
    
    # 创建目录
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    try:
        # 使用 model_dump_json() 序列化为 JSON 字符串
        json_str = config.model_dump_json(indent=2, exclude_none=False)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        _current_config = config
    except IOError as e:
        raise IOError(f"无法保存配置文件: {e}")


# ========== 便捷函数：获取缓存的配置 ==========
def get_cached_config() -> AppConfig | None:
    """获取缓存的配置对象（可能为 None）
    
    Returns:
        缓存的 AppConfig 对象或 None
    """
    return _current_config


# ========== 便捷函数：创建默认配置 ==========
def create_default_config(
    autostart_type: str = "manual",
    shutdown_command: List[str] | None = None
) -> AppConfig:
    """创建一个默认配置对象（不自动保存）
    
    Args:
        autostart_type: 自启动类型，默认为 "manual"
        shutdown_command: 关机命令，默认为 ["systemctl", "suspend"]
        
    Returns:
        AppConfig: 默认配置对象
    """
    return AppConfig(
        autostart_type=autostart_type,
        shutdown_command=shutdown_command or ["systemctl", "suspend"],
        restricted_hours=RestrictedHours(),
        continuous_usage_limits=ContinuousUsageLimits(),
        debug=False
    )
