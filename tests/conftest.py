#!/usr/bin/env python3
"""pytest 公共配置。

单元测试不应依赖外部网络：默认禁用网络时间同步，让所有时间走本地时间，
保证用例结果稳定、可复现。如需在测试中验证网络时间逻辑，
可显式设置环境变量 CURFEW_NO_NETWORK_TIME=0。
"""
import os

os.environ.setdefault("CURFEW_NO_NETWORK_TIME", "1")
