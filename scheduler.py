"""
调度模块（简历上的"调度"部分）
用 schedule 库定时触发 fetch_weather.run_once()。
思路很简单：一个死循环，每秒检查一次"有没有到该执行任务的时间"。

生产环境更常见的做法是用 crontab / Airflow / APScheduler，
但对于练手项目，schedule 库足够展示"你理解数据管道需要定时调度"这个概念，
而且代码量小、容易看懂、容易在简历面试时讲清楚原理。
"""

import time
import logging

import schedule

from config import SCHEDULE_INTERVAL_MINUTES, LOG_FILE
from fetch_weather import run_once

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def job():
    logger.info("=== 定时任务触发 ===")
    try:
        run_once()
    except Exception:
        # 任务内部任何异常都要 catch 住，否则一次失败会导致整个调度进程崩溃退出
        logger.exception("定时任务执行出错")


def main():
    logger.info(f"调度器启动，每 {SCHEDULE_INTERVAL_MINUTES} 分钟抓取一次数据。按 Ctrl+C 停止。")

    # 启动时先立刻跑一次，不用等到第一个整点周期
    job()

    schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
