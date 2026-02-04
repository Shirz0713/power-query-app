import streamlit as st
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data():
    df = pd.read_csv("power_data.csv")
    # 强制校验必要字段
    required_cols = ["station", "year", "month", "power_kwh", "fee_yuan", "price_yuan_per_kwh"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"❌ CSV缺少必要列: {missing}。请按规范补充year/month等字段")
    # 安全年份转换（避免"2023年"等字符串）
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    return df

st.set_page_config(page_title="发电数据查询系统（含年份）", layout="centered")
st.title("⚡ 发电厂站数据查询系统")
st.caption("✅ 已支持年份筛选｜选择场站+年份+月份，精准查询历史数据")

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ 数据加载失败：{str(e)}\n\n📌 请检查：\n1. power_data.csv是否存在\n2. 是否包含year列（整数格式）\n3. 编码是否为UTF-8")
    st.stop()

# === 智能默认值逻辑 ===
current_year = datetime.now().year
current_month = f"{datetime.now().month}月"
valid_years = sorted(df["year"].unique(), reverse=True)
default_year = current_year if current_year in valid_years else valid_years[0]
default_month = current_month if current_month in df["month"].unique() else "1月"

# === 批量选择器 ===
col1, col2, col3 = st.columns(3)
with col1:
    stations = st.multiselect(
        "📍 场站（可多选）",
        options=sorted(df["station"].dropna().unique()),
        default=[sorted(df["station"].dropna().unique())[0]]  # 默认选中第一个场站
    )
with col2:
    years = st.multiselect(
        "🗓️ 年份（可多选）",
        options=valid_years,
        default=[default_year]  # 默认选中当前年份
    )
with col3:
    months = st.multiselect(
        "📅 月份（可多选）",
        options=sorted(
            df["month"].dropna().unique(),
            key=lambda x: int(x.replace("月", ""))
        ),
        default=[default_month]  # 默认选中当前月份
    )

# === 查询与展示 ===
if st.button("🔍 批量查询数据", type="primary", use_container_width=True):
    # 使用 isin 进行批量筛选
    result = df[
        (df["station"].isin(stations)) &
        (df["year"].isin(years)) &
        (df["month"].isin(months))
    ]

    st.divider()
    if result.empty:
        st.warning("⚠️ 未找到符合条件的数据\n\n💡 建议检查筛选条件是否合理")
    else:
        st.subheader("📊 查询结果汇总")
        st.dataframe(result, use_container_width=True)

        # 添加汇总统计
        total_power = result["power_kwh"].sum()
        total_fee = result["fee_yuan"].sum()
        avg_price = total_fee / total_power if total_power > 0 else 0


        st.metric("🔌 总发电量", f"{total_power:,.0f} kWh")
        st.metric("💰 总电费", f"{total_fee:,.0f}元")
        st.metric("🏷️ 平均电价", f"{avg_price:.3f}元/kWh")

        # 数据溯源提示
        st.caption(f"✅ 数据来源：power_data.csv | 共 {len(result)} 条记录")

        # 导出功能
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        csv = convert_df_to_csv(result)
        st.download_button(
            label="📥 下载查询结果 (CSV)",
            data=csv,
            file_name="query_result.csv",
            mime="text/csv"
        )

# === 实用辅助功能===
with st.expander("🔍 数据分布预览（避免查无结果）"):
    st.write("**各场站年份覆盖情况**")
    coverage = df.groupby(['station', 'year']).size().unstack(fill_value=0)
    st.dataframe(coverage, use_container_width=True)
    st.info("💡 提示：若某场站某年份数值<12，说明该年数据不完整")
