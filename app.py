
import streamlit as st
import pandas as pd
import datetime
import hashlib
import os
import plotly.express as px

st.set_page_config(
    page_title="🧹 数字断舍离 - Digital Clean",
    page_icon="🧹",
    layout="centered"
)

DATA_FILE = "digital_clean_data.csv"
STORAGE_VALUE_PER_GB = 0.6


def encrypt_password(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            df["日期"] = pd.to_datetime(df["日期"]).dt.date
        return df
    return pd.DataFrame(columns=[
        "日期", "打卡人", "清理设备", "释放空间(GB)",
        "整理内容", "断舍离心得", "删除密码", "公开属性"
    ])


def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def streak(df, name):
    dates = sorted(df[df["打卡人"] == name]["日期"].tolist())
    if not dates:
        return 0
    s = 1
    for i in range(len(dates)-1, 0, -1):
        if (dates[i]-dates[i-1]).days == 1:
            s += 1
        else:
            break
    return s


def badges(gb, days):
    result = []
    if gb >= 1:
        result.append("🌱 数字整理新手")
    if gb >= 20:
        result.append("🎖 缓存清理专家")
    if gb >= 100:
        result.append("🏆 数字极简主义者")
    if days >= 7:
        result.append("🔥 连续整理达人")
    if days >= 30:
        result.append("👑 断舍离大师")
    return result or ["✨ 初次整理"]


st.markdown("""
<style>
.main {
    background:#fafafa;
}
.card {
    padding:20px;
    border-radius:20px;
    background:white;
    box-shadow:0 4px 16px rgba(0,0,0,.08);
    text-align:center;
}
.big {
    font-size:38px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

df = load_data()

st.title("🧹 数字断舍离")
st.caption("Digital Clean · 记录每一次数字空间整理")

if not df.empty:
    total = df["释放空间(GB)"].sum()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="card"><div>💾累计释放</div><div class="big">{total:.2f} GB</div></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="card"><div>价值估算</div><div class="big">¥{total*STORAGE_VALUE_PER_GB:.2f}</div></div>',
            unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3 = st.tabs(["🧹 今日整理", "🏆 我的成长", "📊 数据统计"])

with tab1:
    with st.form("clean"):
        name = st.text_input("昵称")
        device = st.selectbox("设备", ["手机", "平板", "电脑", "其他"])
        size = st.number_input("释放空间(GB)", min_value=0.01, value=1.0)
        content = st.multiselect(
            "整理内容",
            ["📷 照片", "🎬 视频", "💬 聊天缓存", "🗑 系统垃圾", "📦 APP", "📄 文件"]
        )
        note = st.text_area("今日心得")
        pwd = st.text_input("删除密码", type="password")
        public = st.radio("可见性", ["公开", "私密"])
        submit = st.form_submit_button("完成断舍离")

    if submit:
        if name and pwd:
            new = pd.DataFrame([{
                "日期": datetime.date.today(),
                "打卡人": name,
                "清理设备": device,
                "释放空间(GB)": size,
                "整理内容": ",".join(content),
                "断舍离心得": note,
                "删除密码": encrypt_password(pwd),
                "公开属性": public
            }])
            df = pd.concat([df, new], ignore_index=True)
            save_data(df)
            st.success("🧹 断舍离完成！")
            st.rerun()

with tab2:
    if not df.empty:
        for n, g in df.groupby("打卡人"):
            total = g["释放空间(GB)"].sum()
            d = streak(df, n)
            st.subheader(n)
            st.write(f"累计释放：{total:.2f}GB")
            st.write(f"连续整理：🔥 {d}天")
            st.write("获得徽章：")
            st.write(" ".join(badges(total, d)))
    else:
        st.info("还没有记录")

with tab3:
    if not df.empty:
        chart = px.line(
            df.sort_values("日期"),
            x="日期",
            y="释放空间(GB)",
            color="打卡人",
            markers=True
        )
        st.plotly_chart(chart, use_container_width=True)

        pie = px.pie(
            df,
            names="清理设备",
            values="释放空间(GB)"
        )
        st.plotly_chart(pie, use_container_width=True)

st.caption("Digital Clean · Small cleanup, big difference.")
