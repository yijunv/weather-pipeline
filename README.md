# 天气数据采集与分析 Pipeline

一个端到端的小型数据工程项目：定时爬取天气 API → 清洗入库 SQLite → Streamlit 可视化。

## 项目结构

```
weather_pipeline/
├── config.py          # 配置：城市列表、API地址、调度间隔
├── database.py         # SQLite 建表 / 写入 / 查询
├── fetch_weather.py     # 调用 Open-Meteo API 抓取数据（"爬虫"部分）
├── scheduler.py         # 用 schedule 库定时执行采集
├── dashboard.py          # Streamlit 可视化界面
├── requirements.txt
└── logs/                 # 运行日志
```

## 快速开始（在 VSCode 终端里执行）

```bash
# 1. 建议先建一个虚拟环境
python -m venv venv
source venv/bin/activate      # Windows 用 venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
(第二步之后需要手动创建一个文件)#命令是：mkdir logs

# 3. 手动跑一次采集，验证能否正常抓取数据、写入数据库
python fetch_weather.py

# 4. 打开 dashboard 看看效果
streamlit run dashboard.py

# 5. 想要定时持续采集，就运行调度器（会一直占用这个终端）
python scheduler.py
```

跑完第 3 步后，目录下会多出一个 `weather.db` 文件，用 SQLite 相关插件（VSCode 的 "SQLite Viewer" 插件）
就能直接打开看表结构和数据。

---

## 5 天开发计划

### Day 1：环境 + 打通爬虫链路
- 装好 Python 环境、VSCode 插件（Python、SQLite Viewer）
- 跑通 `fetch_weather.py`，理解 Open-Meteo 返回的 JSON 结构
- 重点搞懂 `_parse_response` 这个函数：为什么要把"按字段分组"的数据转成"按小时一条记录"

### Day 2：数据库设计
- 理解 `database.py` 里的表结构设计：为什么用 `(city, timestamp)` 做唯一约束（幂等性，防重复抓取产生脏数据）
- 试着自己加一个字段，比如 `weather_description`（把 weather_code 映射成文字描述）
- 用 DB Browser for SQLite 或 VSCode 插件打开 `weather.db`，直接看数据

### Day 3：调度
- 跑通 `scheduler.py`，理解 `schedule` 库的工作原理（本质是个死循环 + 时间判断）
- 可以把 `SCHEDULE_INTERVAL_MINUTES` 改小（比如 1 分钟）方便测试观察效果
- 想一想：如果程序意外崩溃/电脑关机，数据会断，生产环境怎么解决？（这是简历面试常问的延伸问题，可以提前想好答案：比如用 cron + 系统重启自启动，或迁移到 Airflow）

### Day 4：可视化
- 跑通 `dashboard.py`，熟悉 Streamlit 的基本用法（`st.line_chart`、`st.selectbox`、`st.dataframe`）
- 尝试自己加一个新图表，比如"每日最高/最低温度对比"
- 尝试加一个新的筛选条件，比如按天气类型（weather_code）筛选
