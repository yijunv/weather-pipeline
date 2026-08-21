"""
项目全局配置
"""

# 要抓取的城市及经纬度（可自行增删）
# Open-Meteo 不需要 API Key，直接用经纬度查询
CITIES = {
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
    "Chengdu": (30.5728, 104.0668),
}

# SQLite 数据库文件路径
DB_PATH = "weather.db"

# Open-Meteo 预报接口（未来 7 天，逐小时数据）
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

# 每次请求要拉取的逐小时字段
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]

# 请求超时时间（秒）
REQUEST_TIMEOUT = 15

# 调度间隔（分钟）—— 每隔多久抓一次数据
SCHEDULE_INTERVAL_MINUTES = 60

# 日志文件路径
LOG_FILE = "logs/pipeline.log"
