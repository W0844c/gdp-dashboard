import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="新发地土豆价格看板", layout="wide")

def fetch_tato_price(page: int, keyword: str = "土豆", start_time: str = "2024/01/01"):
    url = "http://www.xinfadi.com.cn/getPriceData.html"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0",
        "referer": "http://www.xinfadi.com.cn/priceDetail.html"
    }
    post_data = {
        "limit": 20,
        "current": page,
        "pubDateStartTime": start_time,
        "pubDateEndTime": "",
        "prodPcatid": "",
        "prodCatid": "",
        "prodName": keyword
    }
    try:
        resp = requests.post(url, headers=headers, data=post_data, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.warning(f"第 {page} 页请求失败：{e}")
        return None

@st.cache_data(ttl=3600)
def load_data(max_page: int = 100):
    data_list = []
    for page in range(1, max_page + 1):
        res_json = fetch_tato_price(page)
        if res_json is None:
            time.sleep(0.3)
            continue
        item_list = res_json.get("list", [])
        if not item_list:
            st.info(f"爬到第 {page} 页，数据源已经没有更多数据，提前停止翻页")
            break
        for item in item_list:
            low = item.get("lowPrice")
            avg = item.get("avgPrice")
            high = item.get("highPrice")
            data_list.append({
                "一级分类": item.get("prodCat", "-"),
                "品名": item.get("prodName", "-"),
                "最低价": float(low) if low not in ("", None) else None,
                "平均价": float(avg) if avg not in ("", None) else None,
                "最高价": float(high) if high not in ("", None) else None,
                "规格": item.get("specInfo", "-") or "-",
                "产地": item.get("place", "-") or "-",
                "单位": item.get("unitInfo", "-") or "-",
                "发布日期": item.get("pubDate", "-") or "-"
            })
        time.sleep(0.3)
    df = pd.DataFrame(data_list)
    df = df[df["品名"] == "土豆"]
    df = df.dropna(subset=["最低价", "平均价", "最高价"])
    df["发布日期"] = pd.to_datetime(df["发布日期"], errors="coerce")
    df = df.dropna(subset=["发布日期"])
    return df

# ========== Streamlit 主界面 ==========
st.title("🥔 新发地土豆价格监控看板")

with st.spinner("正在爬取新发地数据……"):
    df = load_data(max_page=100)

if df.empty:
    st.error("没有获取到土豆价格数据，请稍后重试！")
else:
    # 筛选
    col1, col2 = st.columns([1, 1])
    with col1:
        min_dt, max_dt = df["发布日期"].min(), df["发布日期"].max()
        start_date, end_date = st.date_input(
            "选择时间范围",
            value=[min_dt, max_dt],
            min_value=min_dt,
            max_value=max_dt
        )
    with col2:
        place_list = sorted(df["产地"].unique().tolist())
        select_place = st.multiselect("选择产地", place_list, default=place_list)

    filter_df = df[
        (df["发布日期"] >= pd.to_datetime(start_date)) &
        (df["发布日期"] <= pd.to_datetime(end_date)) &
        (df["产地"].isin(select_place))
    ]

    st.divider()
    valid_df = filter_df.dropna(subset=["平均价"])
    if not valid_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("土豆均价均值", round(valid_df["平均价"].mean(), 3))
        c2.metric("土豆最低价格", valid_df["最低价"].min())
        c3.metric("土豆最高价格", valid_df["最高价"].max())
        c4.metric("土豆数据条数", len(valid_df))
    else:
        st.warning("所选时间段没有有效价格数据！")

    st.subheader("📈 土豆价格随时间变化趋势（总体）")
    # 按日期聚合：当日全部选中产地的整体最低、平均、最高
    daily_agg = valid_df.groupby("发布日期").agg({
        "最低价": "min",
        "平均价": "mean",
        "最高价": "max"
    }).reset_index()

    # 生成连续日期，补齐直到今天
    d_start = daily_agg["发布日期"].min()
    d_end = pd.to_datetime(datetime.now().date())
    full_dates = pd.date_range(d_start, d_end, freq="D")
    daily_agg = daily_agg.set_index("发布日期").reindex(full_dates).reset_index()
    daily_agg.rename(columns={"index": "发布日期"}, inplace=True)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["最低价"],
        mode="lines+markers",
        name="总体最低价",
        line_dash="dash",
        connectgaps=False
    ))
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["平均价"],
        mode="lines+markers",
        name="总体平均价",
        connectgaps=False
    ))
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["最高价"],
        mode="lines+markers",
        name="总体最高价",
        line_dash="dash",
        connectgaps=False
    ))
    fig_line.update_layout(title="土豆每日总体价格走势", height=450)
    fig_line.update_xaxes(tickformat="%Y-%m-%d")
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("📊 不同产地土豆平均价对比")
    bar_df = valid_df.groupby("产地")["平均价"].mean().reset_index()
    fig_bar = go.Figure(go.Bar(
        x=bar_df["产地"],
        y=bar_df["平均价"],
        marker_color="#73b869"
    ))
    fig_bar.update_layout(title="各产地土豆平均价格", height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 土豆明细数据")
    st.dataframe(filter_df, use_container_width=True)

# ========== 如果直接运行脚本，控制台打印原始数据 ==========
if __name__ == "__main__":
    raw_df = load_data(100)
    print("序号\t一级分类\t品名\t最低价\t平均价\t最高价\t规格\t产地\t单位\t发布日期")
    show_df = raw_df.dropna(subset=["平均价"])
    for idx, row in show_df.iterrows():
        print(
            idx + 1,
            row["产地"],
            "土豆",
            row["最低价"],
            row["平均价"],
            row["最高价"],
            "-",
            row["产地"],
            "-",
            row["发布日期"]
        )
