"""
Streamlit Dashboard（简历上的"可视化"部分）
运行方式：streamlit run dashboard.py

功能：
- 侧边栏选择城市、日期范围
- 展示温度/湿度/降水/风速的时间序列图
- 展示原始数据表，支持下载 CSV
"""

import pandas as pd
import streamlit as st

from database import init_db, query_records, get_distinct_cities, get_record_count

st.set_page_config(page_title="天气数据 Dashboard", layout="wide")

init_db()  # 确保表存在，避免第一次直接运行 dashboard 时报错

st.title("🌤️ 天气时间序列数据 Dashboard")
st.caption("数据来源：Open-Meteo 免费公开 API ｜ 存储：SQLite ｜ 采集：Python 定时爬虫")

# ---------- 侧边栏筛选 ----------
st.sidebar.header("筛选条件")

total = get_record_count()
if total == 0:
    st.warning(
        "数据库里还没有数据。请先运行 `python fetch_weather.py` 抓取一次数据，"
        "或运行 `python scheduler.py` 开启定时采集。"
    )
    st.stop()

cities = get_distinct_cities()
selected_city = st.sidebar.selectbox("选择城市", options=["全部"] + cities)

date_range = st.sidebar.date_input(
    "选择日期范围",
    value=(),
    help="不选则默认展示全部日期",
)

# ---------- 查询数据 ----------
city_filter = None if selected_city == "全部" else selected_city
start_str, end_str = None, None
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_str, end_str = str(date_range[0]), str(date_range[1])

records = query_records(city=city_filter, start=start_str, end=end_str)
df = pd.DataFrame(records)

if df.empty:
    st.info("当前筛选条件下没有数据，请调整筛选条件。")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])

# ---------- 顶部指标卡 ----------
col1, col2, col3, col4 = st.columns(4)
col1.metric("记录总数（全库）", total)
col2.metric("当前筛选记录数", len(df))
col3.metric("平均气温 (°C)", round(df["temperature"].mean(), 1))
col4.metric("平均湿度 (%)", round(df["humidity"].mean(), 1))

st.divider()

# ---------- 时间序列图 ----------
st.subheader("气温变化趋势")
if selected_city == "全部":
    # 多城市对比：把数据透视成"每列一个城市"，方便 st.line_chart 直接画多条线
    pivot = df.pivot_table(index="timestamp", columns="city", values="temperature")
    st.line_chart(pivot)
else:
    st.line_chart(df.set_index("timestamp")["temperature"])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("湿度变化")
    if selected_city == "全部":
        pivot_h = df.pivot_table(index="timestamp", columns="city", values="humidity")
        st.line_chart(pivot_h)
    else:
        st.line_chart(df.set_index("timestamp")["humidity"])

with col_b:
    st.subheader("降水量")
    if selected_city == "全部":
        pivot_p = df.pivot_table(index="timestamp", columns="city", values="precipitation")
        st.bar_chart(pivot_p)
    else:
        st.bar_chart(df.set_index("timestamp")["precipitation"])

st.subheader("风速变化")
if selected_city == "全部":
    pivot_w = df.pivot_table(index="timestamp", columns="city", values="wind_speed")
    st.line_chart(pivot_w)
else:
    st.line_chart(df.set_index("timestamp")["wind_speed"])

st.divider()

# ---------- 原始数据表 + 下载 ----------
st.subheader("原始数据")
st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("下载当前筛选数据为 CSV", data=csv, file_name="weather_export.csv", mime="text/csv")
