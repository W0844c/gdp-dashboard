import streamlit as st
import plotly.express as px
import pandas as pd
import requests

st.set_page_config(page_title="GDP over time", layout="wide")
st.title("GDP over time")

# 国家编码映射
country_list = {
    "BRA": "Brazil",
    "DEU": "Germany",
    "FRA": "France",
    "GBR": "United Kingdom",
    "JPN": "Japan",
    "MEX": "Mexico"
}
codes = list(country_list.keys())

# 加载世界银行 GDP 数据
@st.cache_data
def load_gdp_data():
    url = "http://api.worldbank.org/v2/country/" + ";".join(codes) + "/indicator/NY.GDP.MKTP.CD?format=json&per_page=300&date=1960:2022"
    resp = requests.get(url, timeout=20)
    data = resp.json()[1]
    rows = []
    for item in data:
        rows.append({
            "Country Code": item["countryiso3code"],
            "Year": int(item["date"]),
            "GDP": item["value"]
        })
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["GDP"])
    df["GDP"] = df["GDP"].astype(float)
    return df

df = load_gdp_data()

# 绘制多国家折线，和示例样式对齐
fig = px.line(
    df,
    x="Year",
    y="GDP",
    color="Country Code",
    markers=True,
    title="GDP over time"
)
fig.update_layout(
    height=600,
    xaxis_title="Year",
    yaxis_title="GDP",
    legend_title="Country Code"
)
fig.update_xaxes(tickformat="%Y")
st.plotly_chart(fig, use_container_width=True)
