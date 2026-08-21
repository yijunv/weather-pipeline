"""
数据库模块
职责：
1. 初始化 SQLite 数据库和表结构
2. 提供写入（insert）和查询（query）的通用函数
这样 fetch_weather.py 和 dashboard.py 都可以复用这一份逻辑，不用各写各的 SQL。
"""

import sqlite3
from contextlib import contextmanager
from config import DB_PATH


@contextmanager
def get_connection():
    """
    用 context manager 包一层，保证连接用完自动关闭、
    出异常时自动 rollback，避免每处都写 try/finally。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以像 dict 一样按列名取值
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    创建 weather_records 表（如果不存在）。
    用 (city, timestamp) 作为唯一约束，防止同一小时的数据被重复插入。
    """
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT NOT NULL,      -- 天气对应的时间点（预报小时）
                temperature REAL,
                humidity REAL,
                precipitation REAL,
                wind_speed REAL,
                weather_code INTEGER,
                fetched_at TEXT NOT NULL,     -- 数据被抓取入库的时间
                UNIQUE(city, timestamp)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_city_timestamp ON weather_records(city, timestamp)"
        )


def insert_records(records: list[dict]):
    """
    批量插入天气记录。
    用 INSERT OR IGNORE：如果 (city, timestamp) 已存在就跳过，
    这样重复运行爬虫也不会产生重复数据（幂等）。
    返回本次实际插入的行数。
    """
    if not records:
        return 0

    with get_connection() as conn:
        cursor = conn.executemany(
            """
            INSERT OR IGNORE INTO weather_records
                (city, latitude, longitude, timestamp, temperature,
                 humidity, precipitation, wind_speed, weather_code, fetched_at)
            VALUES
                (:city, :latitude, :longitude, :timestamp, :temperature,
                 :humidity, :precipitation, :wind_speed, :weather_code, :fetched_at)
            """,
            records,
        )
        return cursor.rowcount


def query_records(city: str | None = None, start: str | None = None, end: str | None = None):
    """
    按条件查询，给 Streamlit dashboard 用。
    city 为 None 时查询全部城市；start/end 为 'YYYY-MM-DD' 格式的日期字符串。
    """
    sql = "SELECT * FROM weather_records WHERE 1=1"
    params = {}

    if city:
        sql += " AND city = :city"
        params["city"] = city
    if start:
        sql += " AND timestamp >= :start"
        params["start"] = start
    if end:
        sql += " AND timestamp <= :end"
        params["end"] = end

    sql += " ORDER BY timestamp ASC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_distinct_cities():
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT city FROM weather_records ORDER BY city").fetchall()
        return [row["city"] for row in rows]


def get_record_count():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS cnt FROM weather_records").fetchone()
        return row["cnt"]


if __name__ == "__main__":
    # 直接运行这个文件可以单独初始化数据库，方便调试
    init_db()
    print(f"数据库已初始化：{DB_PATH}")
    print(f"当前记录数：{get_record_count()}")
