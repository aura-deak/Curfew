#!/usr/bin/env python3
import os
import subprocess
import json
import pexpect

CONFIG_FILE = os.environ.get('CURFEW_CONFIG', 'config.json')
STATUS_FILE = os.environ.get('CURFEW_STATUS', 'status.json')
SYMLINK_PATH = '/usr/local/bin/curfew'

def remove_config_file(filepath):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"已删除配置文件: {filepath}")
            return True
        except Exception as e:
            print(f"删除配置文件失败 {filepath}: {e}")
            return False
    else:
        print(f"配置文件不存在: {filepath}")
        return True

def remove_cron_job():
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("未找到 crontab，跳过移除 cron 任务")
            return True
        
        current_cron = result.stdout
        if not current_cron:
            print("crontab 为空，跳过移除")
            return True
        
        lines = current_cron.strip().split('\n')
        new_lines = [line for line in lines if 'curfew' not in line]
        
        if len(new_lines) == len(lines):
            print("未找到 curfew cron 任务，跳过移除")
            return True
        
        new_cron = '\n'.join(new_lines) + '\n'
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print("已移除 curfew cron 任务")
            return True
        else:
            print("移除 cron 任务失败")
            return False
    except Exception as e:
        print(f"移除 cron 任务失败: {e}")
        return False

def remove_symlink():
    try:
        if not os.path.exists(SYMLINK_PATH) and not os.path.islink(SYMLINK_PATH):
            print("软链接不存在，跳过移除")
            return True
        
        child = pexpect.spawn(f'sudo rm -f {SYMLINK_PATH}')
        child.expect(['password:', pexpect.EOF])
        if 'password:' in child.before.decode():
            print("需要 sudo 权限删除软链接，请输入密码：")
            child.sendline(os.environ.get('SUDO_PASSWORD', ''))
        child.expect(pexpect.EOF)
        child.close()
        
        if child.exitstatus == 0:
            print(f"已删除软链接: {SYMLINK_PATH}")
            return True
        else:
            print("删除软链接失败")
            return False
    except Exception as e:
        print(f"删除软链接失败: {e}")
        return False

def uninstall():
    print("开始卸载 Curfew...")
    
    success = True
    success &= remove_config_file(CONFIG_FILE)
    success &= remove_config_file(STATUS_FILE)
    success &= remove_cron_job()
    success &= remove_symlink()
    
    if success:
        print("\n卸载完成！")
        print("Curfew 配置已清除，包括：")
        print("- 配置文件")
        print("- 状态文件")
        print("- cron 定时任务")
        print("- 软链接")
    else:
        print("\n卸载过程中部分操作失败，请检查上述错误信息")
        return False
    
    return True