#!/usr/bin/env python3
import subprocess

def shutdown(shutdown_command, test_mode=False, debug=False):
    print(f"执行关机命令: {shutdown_command}")
    
    if not debug and not test_mode:
        subprocess.run(shutdown_command, check=True)
    else:
        print("测试模式: 未执行实际关机操作")
