# Save this file as app.py
import streamlit as st
import pandas as pd
import datetime
import os
import hashlib
import plotly.express as px
import uuid

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
        try:
            df = pd.read_csv(DATA_FILE)
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"]).dt.date
            # 确保老数据结构兼容
            for col in ["ID", "删除密码", "公开属性"]:
                if col not in df.columns:
                    df[col] = ""
            return df
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "ID", "日期", "打卡人", "清理设备",
        "释放空间(GB)", "整理内容",
        "断舍离心得", "删除密码", "公开属性"
    ])


def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def streak(df, name):
    user_df = df[df["打卡人"] == name]
    if user_df.empty:
        return 0
    dates = sorted(list(set(user_df["日期"].tolist())))
    
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    
    if dates[-1] != today and dates[-1] != yesterday:
        return 0
        
    s = 1
    for i in range(len(dates)-1, 0, -1):
        if (dates[i] - dates[i-1]).days == 1:
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

c1, c2, c3 = st.columns(3)
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

# ---- Tab 1: 今日断舍离 ----
with tab1:
    st.subheader("记录今天的数字整理")

    with st.form("checkin"):
        name = st.text_input("打卡人", placeholder="请输入你的名字/昵称")
        device = st.selectbox("设备", ["手机", "平板", "电脑", "其他"])
        size = st.number_input("释放空间(GB)", min_value=0.01, value=1.0, step=0.1)
        types = st.multiselect(
            "整理内容",
            ["📷照片", "🎬视频", "💬聊天缓存", "🗑系统垃圾", "📦APP整理", "📄文件"]
        )
        note = st.text_area("断舍离心得")
        pwd = st.text_input("删除/查看密码", type="password", help="后续删除记录或查看私密记录时的凭证")
        public = st.radio("可见性", ["公开", "私密"], horizontal=True)

        submit = st.form_submit_button("完成断舍离")

    if submit:
        if not name.strip() or not pwd.strip():
            st.error("⚠️ 请输入打卡人姓名和密码！")
        else:
            new_id = str(uuid.uuid4())
            new = pd.DataFrame([{
                "ID": new_id,
                "日期": datetime.date.today(),
                "打卡人": name.strip(),
                "清理设备": device,
                "释放空间(GB)": size,
                "整理内容": ",".join(types) if types else "常规整理",
                "断舍离心得": note if note else "数字断舍离，身心舒畅！",
                "删除密码": pwd_hash(pwd.strip()),
                "公开属性": public
            }])
            df = pd.concat([df, new], ignore_index=True)
            save_data(df)
            
            current_streak = streak(df, name.strip())
            st.success(f"🧹 数字断舍离完成！你已连续打卡 {current_streak} 天，继续坚持哦！")
            st.balloons()
            st.rerun()

# ---- Tab 2: 数据洞察 ----
with tab2:
    st.subheader("📊 数据洞察")

    if not df.empty:
        trend = df.copy()
        trend["日期显示"] = trend["日期"].astype(str)
        trend_grouped = trend.groupby(["日期显示", "打卡人"])["释放空间(GB)"].sum().reset_index()

        fig = px.line(
            trend_grouped,
            x="日期显示",
            y="释放空间(GB)",
            color="打卡人",
            markers=True,
            title="每日释放趋势"
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            device_df = df.groupby("清理设备")["释放空间(GB)"].sum().reset_index()
            fig = px.pie(
                device_df,
                names="清理设备",
                values="释放空间(GB)",
                title="设备整理比例",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            people_df = df.groupby("打卡人")["释放空间(GB)"].sum().reset_index()
            fig = px.pie(
                people_df,
                names="打卡人",
                values="释放空间(GB)",
                title="成员贡献比例",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)

        value = df.copy()
        value["价值"] = value["释放空间(GB)"] * STORAGE_VALUE_PER_GB
        value = value.groupby("打卡人")["价值"].sum().reset_index()

        fig = px.pie(
            value,
            names="打卡人",
            values="价值",
            title="成员价值贡献比例",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无数据，打卡后即可查看图表看板。")

# ---- Tab 3: 历史记录 ----
with tab3:
    st.subheader("📋 历史记录")
    if not df.empty:
        public_df = df[df["公开属性"] == "公开"].copy()
        
        show_private = False
        private_df = pd.DataFrame()
        
        with st.expander("🔐 输入密码查看我自己的私密记录"):
            v_name = st.text_input("打卡名字", key="view_name")
            v_pwd = st.text_input("打卡密码", type="password", key="view_pwd")
            if v_name and v_pwd:
                private_df = df[
                    (df["打卡人"] == v_name.strip()) & 
                    (df["删除密码"] == pwd_hash(v_pwd.strip())) & 
                    (df["公开属性"] == "私密")
                ].copy()
                
                if not private_df.empty:
                    st.success(f"🔓 成功解锁了属于你的 {len(private_df)} 条私密打卡记录！")
                    show_private = True
                else:
                    st.warning("未找到匹配的私密记录，请确认名字和密码。")

        if show_private:
            display_df = pd.concat([public_df, private_df]).drop_duplicates().reset_index(drop=True)
        else:
            display_df = public_df

        if not display_df.empty:
            show_table = display_df.drop(columns=["删除密码", "ID"], errors="ignore").sort_values(by="日期", ascending=False)
            st.dataframe(show_table, use_container_width=True)
        else:
            st.info("暂无可见的打卡记录。")
    else:
        st.info("暂无历史记录。")

# ---- Tab 4: 管理记录 ----
with tab4:
    st.subheader("⚙️ 删除记录")

    if not df.empty:
        record_map = {}
        options = []
        for idx, row in df.iterrows():
            label = f"{row['日期']} | {row['打卡人']} 清理了 {row['释放空间(GB)']}GB [{row['公开属性']}]"
            record_map[label] = row["ID"]
            options.append(label)

        selected_label = st.selectbox("选择要删除的记录", options)
        target_id = record_map[selected_label]

        del_pwd = st.text_input("输入该记录的密码", type="password", key="delete_pwd")

        if st.button("确认删除", type="primary"):
            index = df[
                (df["ID"] == target_id) &
                (df["删除密码"] == pwd_hash(del_pwd.strip()))
            ].index

            if len(index) > 0:
                df = df.drop(index).reset_index(drop=True)
                save_data(df)
                st.success("🎉 记录删除成功！")
                st.rerun()
            else:
                st.error("❌ 密码错误，删除失败！")
    else:
        st.info("暂无数据，无法进行管理。")
