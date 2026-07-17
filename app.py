
import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import plotly.express as px

st.set_page_config(
    page_title="🧹 数字断舍离 - Digital Clean",
    page_icon="🧹",
    layout="wide"
)

DATA_FILE = "digital_clean_data.csv"
STORAGE_VALUE_PER_GB = 0.6


def pwd_hash(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "日期" in df:
            df["日期"] = pd.to_datetime(df["日期"]).dt.date
        return df

    return pd.DataFrame(columns=[
        "ID", "日期", "打卡人", "清理设备",
        "释放空间(GB)", "整理内容",
        "断舍离心得", "删除密码", "公开属性"
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


df = load_data()

st.markdown("""
<style>
.card{
padding:25px;
border-radius:20px;
background:#ffffff;
box-shadow:0 4px 15px rgba(0,0,0,0.08);
text-align:center;
}
.big{
font-size:38px;
font-weight:bold;
}
</style>
""", unsafe_allow_html=True)


st.title("🧹 数字断舍离")
st.caption("Digital Clean · 每一次整理，都是一次数字空间释放")


total = df["释放空间(GB)"].sum() if not df.empty else 0

c1,c2,c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="card"><div>💾累计释放</div><div class="big">{total:.2f} GB</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="card"><div>💰空间价值</div><div class="big">¥{total*STORAGE_VALUE_PER_GB:.2f}</div></div>', unsafe_allow_html=True)
with c3:
    people = df["打卡人"].nunique() if not df.empty else 0
    st.markdown(f'<div class="card"><div>👥参与人数</div><div class="big">{people}</div></div>', unsafe_allow_html=True)


tab1, tab2, tab3, tab4 = st.tabs(
    ["🧹 今日断舍离", "📊 数据洞察", "📋 历史记录", "⚙️ 管理记录"]
)


with tab1:
    st.subheader("记录今天的数字整理")

    with st.form("checkin"):
        name = st.text_input("打卡人")
        device = st.selectbox("设备", ["手机","平板","电脑","其他"])
        size = st.number_input("释放空间(GB)", min_value=0.01, value=1.0)
        types = st.multiselect(
            "整理内容",
            ["📷照片","🎬视频","💬聊天缓存","🗑系统垃圾","📦APP整理","📄文件"]
        )
        note = st.text_area("断舍离心得")
        pwd = st.text_input("删除密码", type="password")
        public = st.radio("可见性", ["公开","私密"])

        submit = st.form_submit_button("完成断舍离")

    if submit:
        if name and pwd:
            import uuid
            new = pd.DataFrame([{
                "ID": str(uuid.uuid4()),
                "日期": datetime.date.today(),
                "打卡人": name,
                "清理设备": device,
                "释放空间(GB)": size,
                "整理内容": ",".join(types),
                "断舍离心得": note,
                "删除密码": pwd_hash(pwd),
                "公开属性": public
            }])
            df = pd.concat([df,new],ignore_index=True)
            save_data(df)
            st.success("🧹 数字断舍离完成")
            st.rerun()


with tab2:
    st.subheader("📊 数据洞察")

    if not df.empty:
        trend = df.groupby(["日期","打卡人"])["释放空间(GB)"].sum().reset_index()
        trend["日期显示"] = trend["日期"].astype(str)

        fig = px.line(
            trend,
            x="日期显示",
            y="释放空间(GB)",
            color="打卡人",
            markers=True,
            title="每日释放趋势"
        )
        st.plotly_chart(fig,use_container_width=True)

        col1,col2 = st.columns(2)

        with col1:
            device = df.groupby("清理设备")["释放空间(GB)"].sum().reset_index()
            fig = px.pie(
                device,
                names="清理设备",
                values="释放空间(GB)",
                title="设备整理比例",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            people = df.groupby("打卡人")["释放空间(GB)"].sum().reset_index()
            fig = px.pie(
                people,
                names="打卡人",
                values="释放空间(GB)",
                title="成员贡献比例",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig,use_container_width=True)

        value = df.copy()
        value["价值"] = value["释放空间(GB)"]*STORAGE_VALUE_PER_GB
        value=value.groupby("打卡人")["价值"].sum().reset_index()

        fig=px.pie(
            value,
            names="打卡人",
            values="价值",
            title="成员价值贡献比例",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig,use_container_width=True)


with tab3:
    st.subheader("📋 历史记录")
    if not df.empty:
        show=df[df["公开属性"]=="公开"].drop(columns=["删除密码"])
        st.dataframe(show,use_container_width=True)


with tab4:
    st.subheader("⚙️ 删除记录")

    if not df.empty:
        rid=st.selectbox(
            "选择记录",
            df["ID"]
        )

        pwd=st.text_input("输入密码",type="password")

        if st.button("删除"):
            index=df[
                (df["ID"]==rid) &
                (df["删除密码"]==pwd_hash(pwd))
            ].index

            if len(index):
                df=df.drop(index)
                save_data(df)
                st.success("删除成功")
                st.rerun()
            else:
                st.error("密码错误")
