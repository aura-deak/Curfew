#!/usr/bin/env python3
"""Curfew Flask 应用自动化测试"""

import requests
import time
import sys

BASE_URL = 'http://localhost:8080'

def test_dashboard():
    """测试仪表盘页面"""
    try:
        response = requests.get(f'{BASE_URL}/')
        assert response.status_code == 200, f"仪表盘页面失败: {response.status_code}"
        assert 'Curfew 系统' in response.text, "仪表盘页面内容不正确"
        assert '仪表盘' in response.text, "仪表盘页面内容不正确"
        print("✅ 仪表盘页面测试通过")
        return True
    except Exception as e:
        print(f"❌ 仪表盘页面测试失败: {e}")
        return False

def test_config():
    """测试配置页面"""
    try:
        response = requests.get(f'{BASE_URL}/config')
        assert response.status_code == 200, f"配置页面失败: {response.status_code}"
        assert '系统配置' in response.text, "配置页面内容不正确"
        print("✅ 配置页面测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置页面测试失败: {e}")
        return False

def test_schedule():
    """测试时段管理页面"""
    try:
        response = requests.get(f'{BASE_URL}/schedule')
        assert response.status_code == 200, f"时段管理页面失败: {response.status_code}"
        assert '时段管理' in response.text, "时段管理页面内容不正确"
        print("✅ 时段管理页面测试通过")
        return True
    except Exception as e:
        print(f"❌ 时段管理页面测试失败: {e}")
        return False

def test_api_status():
    """测试状态 API"""
    try:
        response = requests.get(f'{BASE_URL}/api/status')
        assert response.status_code == 200, f"状态 API 失败: {response.status_code}"
        data = response.json()
        assert 'date_type' in data, "状态 API 缺少 date_type"
        assert 'is_in_curfew' in data, "状态 API 缺少 is_in_curfew"
        assert 'current_time' in data, "状态 API 缺少 current_time"
        print("✅ 状态 API 测试通过")
        return True
    except Exception as e:
        print(f"❌ 状态 API 测试失败: {e}")
        return False

def test_api_config():
    """测试配置 API"""
    try:
        response = requests.get(f'{BASE_URL}/api/config')
        assert response.status_code == 200, f"配置 API 失败: {response.status_code}"
        data = response.json()
        assert 'restricted_hours' in data, "配置 API 缺少 restricted_hours"
        print("✅ 配置 API 测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置 API 测试失败: {e}")
        return False

def test_api_config_post():
    """测试配置保存 API"""
    try:
        config = {
            'autostart_type': 'manual',
            'shutdown_command': ['shutdown', 'now'],
            'restricted_hours': {
                'workday': [],
                'weekend': [],
                'holiday': []
            },
            'debug': False
        }
        response = requests.post(f'{BASE_URL}/api/config', json=config)
        assert response.status_code == 200, f"配置保存 API 失败: {response.status_code}"
        data = response.json()
        assert data.get('success') == True, "配置保存失败"
        print("✅ 配置保存 API 测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置保存 API 测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始自动化测试...\n")
    
    # 等待服务器启动
    max_wait = 30
    wait_interval = 2
    waited = 0
    
    print(f"等待服务器启动...")
    while waited < max_wait:
        try:
            response = requests.get(f'{BASE_URL}/')
            if response.status_code == 200:
                print("服务器已启动！")
                break
        except:
            pass
        time.sleep(wait_interval)
        waited += wait_interval
    
    if waited >= max_wait:
        print("❌ 服务器启动超时！")
        return
    
    tests = [
        test_dashboard,
        test_config,
        test_schedule,
        test_api_status,
        test_api_config,
        test_api_config_post
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*50)
    print(f"📊 测试结果: {passed}/{len(tests)} 通过")
    if failed > 0:
        print(f"❌ {failed} 个测试失败")
        sys.exit(1)
    else:
        print("🎉 所有测试通过！")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()