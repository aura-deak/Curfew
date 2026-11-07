#!/usr/bin/env python3
"""网络时间模块。

统一对外提供"当前时间"：优先使用互联网时间（NTP，失败时回退到 HTTP 时间接口）
进行校准，互联网不可用时自动回退到本地系统时间。

其它模块一律通过本模块获取当前时间，而不要直接调用
``datetime.datetime.now()`` / ``time.time()``：一旦分散调用，用户只要篡改本地
系统时钟即可绕过限制，且各处时间口径也可能不一致。

实现要点：
- 维护"网络时间 - 本地时间"的偏移量（offset），对外时间 = 本地时间 + offset，
  因此本地时间即为互联网不可用时的天然回退。
- 网络请求在后台守护线程中完成，``now()`` 等接口只做内存计算，绝不阻塞调用方。
- 通过"墙钟时间 vs 单调时钟"的差值检测本地时钟是否被改动（或休眠唤醒），
  一旦发现跳变就立刻触发重新同步，缩短被篡改的时间窗口。

对外接口：
    now()     -> datetime.datetime  当前时间（已按网络时间校准的本地时间）
    today()   -> datetime.date      当前日期
    epoch()   -> float              当前 Unix 时间戳（秒）
    sync()    -> bool               立即同步一次网络时间，返回是否成功
    get_offset() -> float           当前"网络时间 - 本地时间"偏移（秒）
    is_synced()  -> bool            是否已取得来自网络的偏移量
"""
import datetime
import json
import os
import socket
import struct
import threading
import time as _time
import urllib.request

# ========== 可配置项 ==========
# NTP 服务器，按顺序尝试；覆盖国内外常见地址以提高可达性
_NTP_SERVERS = (
    "ntp.aliyun.com",
    "time.windows.com",
    "pool.ntp.org",
    "time.google.com",
)
# HTTP 时间接口（NTP 被防火墙/网络策略拦截时兜底）
_HTTP_TIME_URLS = (
    # 淘宝时间接口，返回毫秒时间戳 {"data": {"t": "1699xxxxxxx000"}}
    "https://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp",
    # 通用接口，返回 {"unixtime": 1699xxxxxx}
    "https://worldtimeapi.org/api/ip",
)
_REQUEST_TIMEOUT = 3.0        # 单次网络请求超时（秒）
_SYNC_INTERVAL = 600.0        # 同步成功后的重新同步间隔（秒）
_RETRY_INTERVAL = 30.0        # 同步失败后的重试间隔（秒）
_CLOCK_JUMP_THRESHOLD = 30.0  # 本地时钟跳变判定阈值（秒）

# NTP 时间戳以 1900-01-01 为起点，Unix 时间戳以 1970-01-01 为起点
_NTP_UNIX_DELTA = 2208988800

# ========== 内部状态 ==========
_lock = threading.Lock()
_offset = 0.0        # 网络时间 - 本地时间（秒）
_ref_local = 0.0     # 计算偏移时的本地墙钟时间（epoch 秒）
_ref_mono = 0.0      # 计算偏移时的单调时钟时间（秒）
_synced = False      # 是否已取得来自网络的偏移量
_refresher = None    # 后台刷新线程
_wake = threading.Event()


def _network_disabled() -> bool:
    """是否禁用网络时间（仅使用本地时间）。

    通过环境变量 CURFEW_NO_NETWORK_TIME 控制，便于测试与离线场景。
    """
    value = os.environ.get("CURFEW_NO_NETWORK_TIME", "").strip().lower()
    return value not in ("", "0", "false", "no")


# ========== 网络时间获取 ==========
def _query_ntp(server: str) -> float:
    """通过 SNTP 协议向服务器请求当前 Unix 时间戳（秒）。失败时抛出异常。"""
    packet = b"\x1b" + 47 * b"\0"  # LI=0, VN=3, Mode=3（客户端请求）
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(_REQUEST_TIMEOUT)
        sock.sendto(packet, (server, 123))
        data, _ = sock.recvfrom(1024)
    if len(data) < 48:
        raise ValueError(f"NTP 响应过短: {len(data)} 字节")
    # 第 40~47 字节为 transmit timestamp：前 4 字节为整秒，后 4 字节为小数部分
    seconds, fraction = struct.unpack("!II", data[40:48])
    return seconds + fraction / 2 ** 32 - _NTP_UNIX_DELTA


def _query_http(url: str) -> float:
    """通过 HTTP 时间接口请求当前 Unix 时间戳（秒）。失败时抛出异常。"""
    request = urllib.request.Request(url, headers={"User-Agent": "curfew"})
    with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("HTTP 时间接口返回格式不支持")
    data = payload.get("data")
    if isinstance(data, dict):
        if "unixtime" in data:
            return float(data["unixtime"])
        if "t" in data:  # 淘宝接口返回的是毫秒
            return float(data["t"]) / 1000.0
    if "unixtime" in payload:
        return float(payload["unixtime"])
    raise ValueError("HTTP 时间接口返回中未找到时间字段")


def _fetch_network_epoch():
    """依次尝试所有时间源，返回首个成功的 Unix 时间戳；全部失败返回 None。"""
    for server in _NTP_SERVERS:
        try:
            return _query_ntp(server)
        except Exception:
            continue
    for url in _HTTP_TIME_URLS:
        try:
            return _query_http(url)
        except Exception:
            continue
    return None


def _apply(net_epoch: float) -> None:
    """用一次成功的网络时间结果更新偏移量。"""
    global _offset, _ref_local, _ref_mono, _synced
    local = _time.time()
    with _lock:
        _offset = net_epoch - local
        _ref_local = local
        _ref_mono = _time.monotonic()
        _synced = True


def sync() -> bool:
    """立即向互联网同步一次时间，返回是否成功。

    成功时更新"网络时间 - 本地时间"偏移量；失败时保留上一次的偏移量
    （若从未成功过，偏移量保持 0，即等同于使用本地时间）。
    """
    if _network_disabled():
        return False
    net_epoch = _fetch_network_epoch()
    if net_epoch is None:
        return False
    _apply(net_epoch)
    return True


# ========== 后台刷新 ==========
def _refresher_loop() -> None:
    """后台线程：周期性重新同步；被唤醒时立即重新同步。"""
    while True:
        ok = sync()
        _wake.wait(_SYNC_INTERVAL if ok else _RETRY_INTERVAL)
        _wake.clear()


def _ensure_refresher() -> None:
    """确保后台刷新线程已启动（懒启动，只启动一次）。"""
    global _refresher
    if _network_disabled():
        return
    if _refresher is not None and _refresher.is_alive():
        return
    with _lock:
        if _refresher is None or not _refresher.is_alive():
            _refresher = threading.Thread(
                target=_refresher_loop, name="curfew-network-time", daemon=True
            )
            _refresher.start()


def _check_clock_jump() -> None:
    """检测本地时钟是否被改动或休眠唤醒，若是则请求立即重新同步。"""
    global _ref_local, _ref_mono
    if not _synced:
        return
    # 单调时钟不受系统时间调整影响，用它推算"本地墙钟本应是多少"
    now_local = _time.time()
    now_mono = _time.monotonic()
    expected_local = _ref_local + (now_mono - _ref_mono)
    if abs(now_local - expected_local) > _CLOCK_JUMP_THRESHOLD:
        # 以当前时刻为新基准，避免每次调用都重复误报（否则网络不可用时会
        # 陷入持续重试），同时立刻唤醒后台线程重新同步。
        with _lock:
            _ref_local = now_local
            _ref_mono = now_mono
        _wake.set()


# ========== 对外接口 ==========
def now() -> datetime.datetime:
    """返回当前时间（已按网络时间校准的本地时间）。"""
    if _network_disabled():
        return datetime.datetime.now()
    _ensure_refresher()
    _check_clock_jump()
    return datetime.datetime.fromtimestamp(_time.time() + _offset)


def today() -> datetime.date:
    """返回当前日期（已按网络时间校准）。"""
    return now().date()


def epoch() -> float:
    """返回当前 Unix 时间戳（秒，已按网络时间校准）。"""
    if _network_disabled():
        return _time.time()
    _ensure_refresher()
    _check_clock_jump()
    return _time.time() + _offset


def get_offset() -> float:
    """返回当前"网络时间 - 本地时间"偏移（秒）。"""
    return _offset


def is_synced() -> bool:
    """返回是否已取得来自网络的偏移量。"""
    return _synced


def reset() -> None:
    """重置同步状态（供测试使用）。

    .. warning:: 不会停止后台刷新线程，线程下一次同步仍会写回偏移量。
    """
    global _offset, _ref_local, _ref_mono, _synced
    with _lock:
        _offset = 0.0
        _ref_local = 0.0
        _ref_mono = 0.0
        _synced = False


if __name__ == "__main__":
    ok = sync()
    print(f"同步结果: {'成功' if ok else '失败（回退本地时间）'}")
    print(f"网络时间 - 本地时间偏移: {get_offset():.3f} 秒")
    print(f"当前时间: {now().isoformat()}")
