"""
数据采集模块（这就是简历上写的"爬虫"部分）
调用 Open-Meteo 免费公开 API，按城市抓取逐小时天气预报数据，
清洗成统一格式后写入 SQLite。

Open-Meteo 文档：https://open-meteo.com/en/docs
特点：完全免费、不需要注册、不需要 API Key，非常适合练手项目。
"""

import logging
from datetime import datetime, timezone

import requests

from config import (
    CITIES,
    FORECAST_API_URL,
    HOURLY_FIELDS,
    REQUEST_TIMEOUT,
    LOG_FILE,
)
from database import init_db, insert_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def fetch_city_weather(city: str, lat: float, lon: float, retries: int = 3) -> list[dict]:
    """
    请求单个城市的天气数据，返回清洗好的记录列表。
    加了简单的重试逻辑：网络请求这种 I/O 操作很容易偶发失败，
    重试是爬虫类项目里必备的健壮性设计，写在简历里也是加分点。
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_FIELDS),
        "timezone": "auto",
        "forecast_days": 3,  # 只取未来 3 天，避免单次数据量太大
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(FORECAST_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            return _parse_response(city, lat, lon, data)
        except (requests.RequestException, ValueError) as e:
            last_error = e
            logger.warning(f"[{city}] 第 {attempt}/{retries} 次请求失败：{e}")

    logger.error(f"[{city}] 请求最终失败，跳过该城市：{last_error}")
    return []


def _parse_response(city: str, lat: float, lon: float, data: dict) -> list[dict]:
    """
    把 Open-Meteo 返回的"按字段分组的列表"结构，
    转换成"每小时一条记录"的扁平结构，方便存数据库和后续分析。

    Open-Meteo 原始返回大概是这样：
    {
        "hourly": {
            "time": ["2026-08-21T00:00", "2026-08-21T01:00", ...],
            "temperature_2m": [22.1, 21.8, ...],
            "relative_humidity_2m": [80, 82, ...],
            ...
        }
    }
    """
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    fetched_at = datetime.now(timezone.utc).isoformat()

    records = []
    for i, ts in enumerate(times):
        records.append(
            {
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "timestamp": ts,
                "temperature": _safe_get(hourly, "temperature_2m", i),
                "humidity": _safe_get(hourly, "relative_humidity_2m", i),
                "precipitation": _safe_get(hourly, "precipitation", i),
                "wind_speed": _safe_get(hourly, "wind_speed_10m", i),
                "weather_code": _safe_get(hourly, "weather_code", i),
                "fetched_at": fetched_at,
            }
        )
    return records


def _safe_get(hourly: dict, field: str, index: int):
    """防止某个字段缺失或长度不一致时直接报错"""
    values = hourly.get(field, [])
    return values[index] if index < len(values) else None


def run_once():
    """
    完整跑一轮：初始化数据库 -> 遍历所有城市 -> 抓取 -> 写库。
    这个函数会被 scheduler.py 定时调用，也可以手动执行来测试。
    """
    init_db()
    total_fetched = 0
    total_inserted = 0

    for city, (lat, lon) in CITIES.items():
        logger.info(f"开始抓取 {city} 的天气数据...")
        records = fetch_city_weather(city, lat, lon)
        inserted = insert_records(records)
        total_fetched += len(records)
        total_inserted += inserted
        logger.info(f"{city}：获取 {len(records)} 条，新写入 {inserted} 条（重复的已自动跳过）")

    logger.info(f"本轮完成。共获取 {total_fetched} 条，新增 {total_inserted} 条。")
    return total_inserted


if __name__ == "__main__":
    run_once()
