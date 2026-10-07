#!/usr/bin/env python3
"""单日设定（daily_overrides）功能测试"""

import datetime
import json
import os

import pytest

from curfew.config import (
    AppConfig,
    DailyOverride,
    TimeSlot,
    create_default_config,
    delete_daily_override,
    get_daily_override,
    load_config,
    save_config,
    set_daily_override,
)
from curfew.curfew_main import get_effective_schedules_for_date
from curfew.date_type import get_calendar_day_info, get_month_calendar


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """把配置文件指向 tmp_path，隔离每个测试。"""
    config_file = tmp_path / "curfew.json"
    monkeypatch.setenv("CURFEW_CONFIG", str(config_file))
    save_config(create_default_config())
    yield config_file


def _make_config_with_workday_rules():
    config = load_config()
    config.restricted_hours.workday = [
        TimeSlot(start_hour=9, start_minute=0, end_hour=12, end_minute=0)
    ]
    config.continuous_usage_limits.workday = 30
    config.total_usage_limits.workday = 120
    save_config(config)
    return load_config()


# ========== 配置模型与读写 ==========

def test_default_config_has_empty_daily_overrides():
    assert load_config().daily_overrides == []


def test_old_config_without_daily_overrides_still_loads():
    """旧版配置（无 daily_overrides 字段）应正常加载并回退为空列表。"""
    raw = {
        "autostart_type": "manual",
        "shutdown_command": ["systemctl", "suspend"],
        "restricted_hours": {"workday": [], "weekend": [], "holiday": []},
        "continuous_usage_limits": {"workday": 0, "weekend": 0, "holiday": 0},
        "total_usage_limits": {"workday": 0, "weekend": 0, "holiday": 0},
        "ban_duration_minutes": 5,
        "banned_until": "",
        "debug": False,
    }
    with open(os.environ["CURFEW_CONFIG"], "w", encoding="utf-8") as f:
        json.dump(raw, f)
    config = load_config()
    assert config.daily_overrides == []


def test_set_get_delete_daily_override():
    assert get_daily_override("2026-11-11") is None

    ok = set_daily_override({
        "date": "2026-11-11",
        "time_ranges": [{"start_hour": 22, "start_minute": 30, "end_hour": 6, "end_minute": 0}],
        "continuous_limit_minutes": 45,
        "daily_total_limit_minutes": 180,
    })
    assert ok is True

    got = get_daily_override("2026-11-11")
    assert got["continuous_limit_minutes"] == 45
    assert got["daily_total_limit_minutes"] == 180
    assert got["time_ranges"][0]["start_hour"] == 22

    assert delete_daily_override("2026-11-11") is True
    assert get_daily_override("2026-11-11") is None
    # 删除不存在的日期返回 False
    assert delete_daily_override("2026-11-11") is False


def test_set_daily_override_replaces_same_date():
    payload = {"date": "2026-11-11", "time_ranges": [], "continuous_limit_minutes": 10,
               "daily_total_limit_minutes": 0}
    set_daily_override(payload)
    set_daily_override({**payload, "continuous_limit_minutes": 99})
    config = load_config()
    assert len(config.daily_overrides) == 1
    assert config.daily_overrides[0].continuous_limit_minutes == 99


def test_daily_override_validation_rejects_bad_fields():
    with pytest.raises(Exception):
        DailyOverride(date="2026-11-11", continuous_limit_minutes=-5)
    with pytest.raises(Exception):
        DailyOverride(**{"date": "2026-11-11",
                         "time_ranges": [{"start_hour": 99, "start_minute": 0,
                                          "end_hour": 0, "end_minute": 0}]})


# ========== 生效优先级 ==========

def test_effective_schedules_fall_back_to_date_type():
    config = _make_config_with_workday_rules()
    # 2026-10-08 是工作日（调休后普通周四）
    slots, cont, total, src = get_effective_schedules_for_date(config, datetime.date(2026, 10, 8))
    assert src == "workday"
    assert cont == 30 and total == 120
    assert slots[0]["start_hour"] == 9


def test_daily_override_fully_replaces_date_type():
    config = _make_config_with_workday_rules()
    set_daily_override({
        "date": "2026-10-08",
        "time_ranges": [{"start_hour": 22, "start_minute": 0, "end_hour": 6, "end_minute": 0}],
        "continuous_limit_minutes": 45,
        "daily_total_limit_minutes": 180,
    })
    config = load_config()
    slots, cont, total, src = get_effective_schedules_for_date(config, datetime.date(2026, 10, 8))
    assert src == "override"
    assert cont == 45 and total == 180
    # 完全替代：日期类型的工作日时段 9:00 不应出现
    assert slots == [{"start_hour": 22, "start_minute": 0, "end_hour": 6, "end_minute": 0}]


def test_daily_override_zero_means_disabled():
    config = _make_config_with_workday_rules()
    set_daily_override({"date": "2026-10-08", "time_ranges": [],
                        "continuous_limit_minutes": 0, "daily_total_limit_minutes": 0})
    config = load_config()
    slots, cont, total, src = get_effective_schedules_for_date(config, datetime.date(2026, 10, 8))
    assert src == "override"
    assert slots == [] and cont == 0 and total == 0


def test_delete_override_restores_date_type():
    config = _make_config_with_workday_rules()
    set_daily_override({"date": "2026-10-08", "time_ranges": [],
                        "continuous_limit_minutes": 45, "daily_total_limit_minutes": 0})
    delete_daily_override("2026-10-08")
    config = load_config()
    slots, cont, total, src = get_effective_schedules_for_date(config, datetime.date(2026, 10, 8))
    assert src == "workday" and cont == 30


# ========== 日历信息 ==========

def test_calendar_day_info_holiday():
    info = get_calendar_day_info(datetime.date(2026, 10, 1))
    assert info["mark"] == "休"
    assert info["date_type"] == "holiday"
    assert info["holiday_name"] == "国庆节"
    assert info["is_rest_day"] is True


def test_calendar_day_info_adjusted_workday():
    # 节假日后的周六上班（调休补班）应标记为「班」
    info = get_calendar_day_info(datetime.date(2026, 10, 10))
    assert info["mark"] == "班"
    assert info["date_type"] == "workday"
    assert info["is_rest_day"] is False


def test_calendar_day_info_plain_workday():
    info = get_calendar_day_info(datetime.date(2026, 10, 8))
    assert info["mark"] == ""
    assert info["date_type"] == "workday"


def test_month_calendar_length():
    days = get_month_calendar(2026, 10)
    assert len(days) == 31
    assert days[0]["date"] == "2026-10-01"
    assert days[-1]["date"] == "2026-10-31"


# ========== Web API ==========

@pytest.fixture
def client():
    from curfew.app import app
    app.config["TESTING"] = True
    return app.test_client()


def test_api_calendar(client):
    resp = client.get("/api/daily/calendar?year=2026&month=10")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["year"] == 2026 and data["month"] == 10
    assert len(data["days"]) == 31


def test_api_daily_crud(client):
    payload = {"date": "2026-11-11", "time_ranges": [
        {"start_hour": 23, "start_minute": 0, "end_hour": 6, "end_minute": 0}],
        "continuous_limit_minutes": 20, "daily_total_limit_minutes": 100}
    assert client.post("/api/daily", json=payload).status_code == 200

    got = client.get("/api/daily/2026-11-11").get_json()
    assert got["exists"] is True
    assert got["continuous_limit_minutes"] == 20

    listed = client.get("/api/daily").get_json()
    assert any(o["date"] == "2026-11-11" for o in listed)

    assert client.delete("/api/daily/2026-11-11").status_code == 200
    assert client.get("/api/daily/2026-11-11").get_json()["exists"] is False
    assert client.delete("/api/daily/2026-11-11").status_code == 404


def test_api_daily_post_validation(client):
    assert client.post("/api/daily", json={"time_ranges": []}).status_code == 400
    assert client.post("/api/daily", json={"date": "2026-11-11",
                                           "continuous_limit_minutes": -1}).status_code == 400


def test_api_status_reflects_override(client):
    today = datetime.date.today().strftime("%Y-%m-%d")
    set_daily_override({"date": today, "time_ranges": [],
                        "continuous_limit_minutes": 15, "daily_total_limit_minutes": 30})
    status = client.get("/api/status").get_json()
    assert status["effective_source"] == "override"
    assert status["continuous_usage_limit"] == 15
    assert status["total_usage_limit"] == 30
