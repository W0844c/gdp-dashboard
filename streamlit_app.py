    st.subheader("📈 土豆价格随时间变化趋势（总体）")
    daily_agg = valid_df.groupby("发布日期").agg({
        "最低价": "min",
        "平均价": "mean",
        "最高价": "max"
    }).reset_index()

    d_start = daily_agg["发布日期"].min()
    d_end = pd.to_datetime(datetime.now().date())
    full_dates = pd.date_range(d_start, d_end, freq="D")
    daily_agg = daily_agg.set_index("发布日期").reindex(full_dates).reset_index()
    daily_agg.rename(columns={"index": "发布日期"}, inplace=True)

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["最低价"],
        mode="lines",
        name="总体最低价",
        line=dict(dash="dash"),
        connectgaps=False
    ))
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["平均价"],
        mode="lines",
        name="总体平均价",
        connectgaps=False
    ))
    fig_line.add_trace(go.Scatter(
        x=daily_agg["发布日期"],
        y=daily_agg["最高价"],
        mode="lines",
        name="总体最高价",
        line=dict(dash="dash"),
        connectgaps=False
    ))
    fig_line.update_layout(
        title="土豆每日总体价格走势",
        height=450,
        xaxis_title="日期",
        yaxis_title="价格"
    )
    fig_line.update_xaxes(tickformat="%Y-%m-%d")
    st.plotly_chart(fig_line, use_container_width=True)
