#!/usr/bin/env python3
import os
import time
import webbrowser
from datetime import date, datetime

from flask import Flask, render_template, jsonify, request

from curfew.config import (
    load_config,
    save_config,
    AppConfig,
    get_daily_override,
    set_daily_override,
    delete_daily_override,
)

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))


@app.route('/')
def dashboard():
    """仪表板页面"""
    return render_template('dashboard.html')


@app.route('/schedule')
def schedule_page():
    """时间表页面"""
    return render_template('schedule.html')


@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置的 API 端点"""
    try:
        config = load_config()
        # 使用 model_dump() 将 Pydantic 模型转换为字典
        return jsonify(config.model_dump())
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f"获取配置失败: {str(e)}"}), 500


@app.route('/api/config', methods=['POST'])
def api_save_config():
    """保存配置的 API 端点"""
    try:
        raw_data = request.json
        # 今日累计使用数据由守护进程维护，前端提交的配置里可能带着
        # 页面加载时的旧快照，直接写入会把计时器"拨回去"（更新慢/倒退的根因之一）。
        # 这里以磁盘上的最新值为准，覆盖请求中的累计字段。
        try:
            current = load_config()
            if isinstance(raw_data, dict):
                raw_data['total_usage_seconds'] = current.total_usage_seconds
                raw_data['total_usage_date'] = current.total_usage_date
                raw_data['total_usage_saved_at'] = current.total_usage_saved_at
        except Exception:
            pass
        # Pydantic 会自动验证和解析数据
        config = AppConfig(**raw_data)
        save_config(config)
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': f"配置格式错误: {str(e)}"}), 400
    except Exception as e:
        return jsonify({'error': f"保存配置失败: {str(e)}"}), 500


@app.route('/api/status', methods=['GET'])
def api_get_status():
    """获取当前状态的 API 端点"""
    try:
        from curfew.date_type import get_date_type
        from curfew.curfew_main import (
            get_effective_schedules_for_date,
            _is_in_slots_now,
        )
        from curfew.timer import get_active_time

        config = load_config()

        date_type = get_date_type()
        # 使用 config.restricted_hours 访问 RestrictedHours 对象
        # 今日生效限制：单日设定优先，否则日期类型
        eff_slots, eff_continuous, eff_total, eff_source = get_effective_schedules_for_date(
            config, datetime.now().date()
        )
        is_in_curfew = _is_in_slots_now(eff_slots)
        now = datetime.now().strftime('%H:%M:%S')
        consecutive_seconds = get_active_time()

        banned_until = config.banned_until
        is_banned = False
        ban_remaining_seconds = 0
        if banned_until:
            banned_dt = datetime.fromisoformat(banned_until)
            if datetime.now() < banned_dt:
                is_banned = True
                ban_remaining_seconds = int((banned_dt - datetime.now()).total_seconds())

        # ---- 今日总使用时间：实时外推 ----
        # 持久化的 total_usage_seconds 每隔几秒才落盘一次。为了让仪表板
        # "更新及时"，这里用上次落盘的时间戳，按真实墙钟流逝线性外推。
        total_usage = config.total_usage_seconds
        today_str = datetime.now().strftime('%Y-%m-%d')
        if config.total_usage_date == today_str and config.total_usage_saved_at > 0:
            elapsed = int(time.time() - config.total_usage_saved_at)
            if elapsed > 0:
                total_usage = config.total_usage_seconds + elapsed
        else:
            # 配置还没记录今天（守护进程未运行或跨天），今天从 0 开始
            total_usage = 0

        data = jsonify({
            'date_type': date_type,
            'effective_source': eff_source,  # 'override' 表示今日命中单日设定
            'continuous_usage_limit': eff_continuous,
            'is_in_curfew': is_in_curfew,
            'current_time': now,
            'consecutive_seconds': consecutive_seconds,
            'banned_until': banned_until,
            'is_banned': is_banned,
            'ban_remaining_seconds': ban_remaining_seconds,
            'total_usage_seconds': total_usage,
            'total_usage_limit': eff_total,
            'total_usage_remaining_seconds': max(0, eff_total * 60 - total_usage)
        })
        return data
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f"获取状态失败: {str(e)}"}), 500


@app.route('/api/daily/calendar', methods=['GET'])
def api_get_daily_calendar():
    """获取某月的日历信息（含节假日提示），供单日设定日历渲染。"""
    from curfew.date_type import get_month_calendar
    try:
        year = request.args.get('year', type=int, default=date.today().year)
        month = request.args.get('month', type=int, default=date.today().month)
        days = get_month_calendar(year, month)
        return jsonify({'year': year, 'month': month, 'days': days})
    except Exception as e:
        return jsonify({'error': f"获取日历失败: {str(e)}"}), 500


@app.route('/api/daily', methods=['GET'])
def api_list_daily_overrides():
    """列出全部单日设定。"""
    try:
        config = load_config()
        return jsonify([o.model_dump() for o in config.daily_overrides])
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f"获取单日设定失败: {str(e)}"}), 500


@app.route('/api/daily/<date_str>', methods=['GET'])
def api_get_daily_override(date_str):
    """获取某日的单日设定；无则返回空对象。"""
    try:
        override = get_daily_override(date_str)
        if override is None:
            return jsonify({'date': date_str, 'time_ranges': [],
                            'continuous_limit_minutes': 0,
                            'daily_total_limit_minutes': 0, 'exists': False})
        return jsonify({**override, 'exists': True})
    except Exception as e:
        return jsonify({'error': f"获取单日设定失败: {str(e)}"}), 500


@app.route('/api/daily', methods=['POST'])
def api_save_daily_override():
    """新增或覆盖某日的单日设定。"""
    try:
        data = request.json
        if not data or not data.get('date'):
            return jsonify({'error': "缺少 date 字段"}), 400
        ok = set_daily_override(data)
        if not ok:
            return jsonify({'error': "保存单日设定失败"}), 400
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': f"单日设定格式错误: {str(e)}"}), 400
    except Exception as e:
        return jsonify({'error': f"保存单日设定失败: {str(e)}"}), 500


@app.route('/api/daily/<date_str>', methods=['DELETE'])
def api_delete_daily_override(date_str):
    """删除某日的单日设定。"""
    try:
        ok = delete_daily_override(date_str)
        if not ok:
            return jsonify({'error': "该日期没有单日设定或删除失败"}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': f"删除单日设定失败: {str(e)}"}), 500


if __name__ == '__main__':
    webbrowser.open('http://localhost:8080')
    app.run(debug=True, port=8080)
