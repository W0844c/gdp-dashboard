import requests
from lxml import etree
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

count = 1
data_list = []  # 用来存放爬取出来的数据

def get_data(page):
    global count, data_list
    url = "http://www.xinfadi.com.cn/getPriceData.html"
    h = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0',
        'referer': 'http://www.xinfadi.com.cn/priceDetail.html'
    }
    data_post = {
        "limit": 20,
        "current": page,
        "pubDateStartTime": "2024/01/01",
        "pubDateEndTime": "",
        "prodPcatid": "",
        "prodCatid": "",
        "prodName": "土豆"
    }
    resp = requests.post(url, headers=h, data=data_post)
    res_json = resp.json()
    item_list = res_json["list"]

    html_str = "<html><body><table id='table1' border='1'>"
    # 表头在这里（html表格的表头，浏览器打开html才能看见）
    html_str += "<tr style='background:#73b869;color:white;'>" \
                "<th><strong>一级分类</strong></th>" \
                "<th><strong>品名</strong></th>" \
                "<th><strong>最低价</strong></th>" \
                "<th><strong>平均价</strong></th>" \
                "<th><strong>最高价</strong></th>" \
                "<th><strong>规格</strong></th>" \
                "<th><strong>产地</strong></th>" \
                "<th><strong>单位</strong></th>" \
                "<th><strong>发布日期</strong></th></tr>"
    for item in item_list:
        row = {
            "一级分类": item["prodCat"],
            "品名": item["prodName"],
            "最低价": item["lowPrice"],
            "平均价": item["avgPrice"],
            "最高价": item["highPrice"],
            "规格": item["specInfo"] if item["specInfo"] else "-",
            "产地": item["place"] if item["place"] else "-",
            "单位": item["unitInfo"] if item["unitInfo"] else "-",
            "发布日期": item["pubDate"] if item["pubDate"] else "-"
        }
        html_str += (f"<tr><td>{row['一级分类']}</td>"
                     f"<td>{row['品名']}</td>"
                     f"<td>{row['最低价']}</td>"
                     f"<td>{row['平均价']}</td>"
                     f"<td>{row['最高价']}</td>"
                     f"<td>{row['规格']}</td>"
                     f"<td>{row['产地']}</td>"
                     f"<td>{row['单位']}</td>"
                     f"<td>{row['发布日期']}</td></tr>")
    html_str += "</table></body></html>"

    content = etree.HTML(html_str)
    rows = content.xpath('//table[@id="table1"]/tr')[1:]
    for row in rows:
        # 容错写法，取不到就给 "-"
        def get_text(xpath_exp):
            res = row.xpath(xpath_exp)
            return res[0] if res else "-"

        cat1 = get_text('./td[1]/text()')
        name = get_text('./td[2]/text()')
        low = get_text('./td[3]/text()')
        avg = get_text('./td[4]/text()')
        high = get_text('./td[5]/text()')
        spec = get_text('./td[6]/text()')
        place = get_text('./td[7]/text()')
        unit = get_text('./td[8]/text()')
        pubdate = get_text('./td[9]/text()')

        print(count, cat1, name, low, avg, high, spec, place, unit, pubdate)
        count += 1
        # 存入列表，价格转浮点，方便后续计算绘图
        data_list.append({
            "一级分类": cat1,
            "品名": name,
            "最低价": float(low) if low != "-" else None,
            "平均价": float(avg) if avg != "-" else None,
            "最高价": float(high) if high != "-" else None,
            "规格": spec,
            "产地": place,
            "单位": unit,
            "发布日期": pubdate
        })

if __name__ == '__main__':
    # 如果你想要控制台第一行直接打印表头，加上这句：
    print("序号 一级分类 品名 最低价 平均价 最高价 规格 产地 单位 发布日期")
    for i in range(3):
        get_data(i + 1)

# ========== Streamlit土豆看板部分 ==========
df = pd.DataFrame(data_list)
# 只保留土豆数据（兜底过滤）
df = df[df["品名"] == "土豆"]
# 删掉价格为空的脏数据
df = df.dropna(subset=["最低价","平均价","最高价"])
df["发布日期"] = pd.to_datetime(df["发布日期"])

# ----------------------交互筛选----------------------
col1, col2 = st.columns([1,1])
with col1:
    start_date, end_date = st.date_input("选择时间范围", [df["发布日期"].min(), df["发布日期"].max()])
with col2:
    place_list = df["产地"].unique()
    select_place = st.multiselect("选择产地", place_list, default=place_list)

filter_df = df[(df["发布日期"] >= pd.to_datetime(start_date)) &
               (df["发布日期"] <= pd.to_datetime(end_date)) &
               (df["产地"].isin(select_place))]

# ----------------------指标卡片----------------------
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("土豆均价均值", round(filter_df["平均价"].mean(),3))
c2.metric("土豆最低价格", filter_df["最低价"].min())
c3.metric("土豆最高价格", filter_df["最高价"].max())
c4.metric("土豆数据条数", len(filter_df))

# ----------------------折线图：平均价实线，最高价、最低价虚线，普通直线 + 数字日期----------------------
st.subheader("📈 土豆价格随时间变化趋势")
fig_line = go.Figure()
for place in filter_df["产地"].unique():
    sub_df = filter_df[filter_df["产地"] == place].sort_values("发布日期")
    # 最低价 虚线
    fig_line.add_trace(go.Scatter(
        x=sub_df["发布日期"],
        y=sub_df["最低价"],
        mode="lines+markers",
        name=f"{place}-最低价",
        line_shape="linear",
        line_dash="dash"
    ))
    # 平均价 实线
    fig_line.add_trace(go.Scatter(
        x=sub_df["发布日期"],
        y=sub_df["平均价"],
        mode="lines+markers",
        name=f"{place}-平均价",
        line_shape="linear"
    ))
    # 最高价 虚线
    fig_line.add_trace(go.Scatter(
        x=sub_df["发布日期"],
        y=sub_df["最高价"],
        mode="lines+markers",
        name=f"{place}-最高价",
        line_shape="linear",
        line_dash="dash"
    ))
fig_line.update_layout(title="土豆每日价格走势")
# 关键：X轴设置为数字格式 YYYY-MM-DD
fig_line.update_xaxes(tickformat="%Y-%m-%d")
st.plotly_chart(fig_line, use_container_width=True)

# ----------------------柱状图：不同产地土豆平均价对比----------------------
st.subheader("📊 不同产地土豆平均价对比")
bar_df = filter_df.groupby("产地")["平均价"].mean().reset_index()
fig_bar = go.Figure(go.Bar(x=bar_df["产地"], y=bar_df["平均价"], marker_color="#73b869"))
fig_bar.update_layout(title="各产地土豆平均价格")
st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------原始数据表----------------------
st.subheader("📋 土豆明细数据")
st.dataframe(filter_df, use_container_width=True)
