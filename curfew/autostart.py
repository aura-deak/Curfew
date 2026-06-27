#!/usr/bin/env python3
import subprocess
import os
import pexpect

SYMLINK_PATH = '/usr/local/bin/curfew'

def get_installed_curfew_path():
    return os.path.expanduser('~/.local/bin/curfew')

def create_symlink():
    try:
        target_path = get_installed_curfew_path()
        
        if not os.path.exists(target_path):
            print(f"curfew 未安装在 {target_path}")
            print("请先运行 'uv tool install --python-preference only-system .' 安装 curfew")
            return False
        
        if os.path.exists(SYMLINK_PATH) or os.path.islink(SYMLINK_PATH):
            try:
                child = pexpect.spawn(f'sudo rm -f {SYMLINK_PATH}')
                child.expect(['password:', pexpect.EOF])
                if 'password:' in child.before.decode():
                    print("需要 sudo 权限删除旧的软链接，请输入密码：")
                    child.sendline(os.environ.get('SUDO_PASSWORD', ''))
                child.expect(pexpect.EOF)
                child.close()
            except pexpect.exceptions.EOF:
                pass
        
        child = pexpect.spawn(f'sudo ln -sf {target_path} {SYMLINK_PATH}')
        child.expect(['password:', pexpect.EOF])
        if 'password:' in child.before.decode():
            print("需要 sudo 权限创建软链接，请输入密码：")
            child.sendline(os.environ.get('SUDO_PASSWORD', ''))
        child.expect(pexpect.EOF)
        child.close()
        
        if child.exitstatus == 0:
            print(f"软链接已创建: {SYMLINK_PATH} -> {target_path}")
            return True
        else:
            print("创建软链接失败")
            return False
    except Exception as e:
        print(f"创建软链接失败: {e}")
        return False

def setup_autostart(autostart_type):
    if autostart_type == 'cron':
        setup_cron()
    else:
        print("请稍后自行设置自启动")

def setup_cron():
    try:
        create_symlink()
        
        cron_command = f'@reboot curfew daemon'
        
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout
        
        if 'curfew daemon' in current_cron:
            print("cron 任务已存在，跳过设置")
            return
        
        new_cron = current_cron + '\n' + cron_command + '\n'
        
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
        
        if process.returncode == 0:
            print("cron 定时任务已设置")
        else:
            print("设置 cron 定时任务失败")
    except Exception as e:
        print(f"设置 cron 定时任务失败: {e}")
