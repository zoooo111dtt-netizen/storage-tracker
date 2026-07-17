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

# 密码哈希
def pwd_hash(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

# ③ 智能单位换算器
def format_storage(gb):
    if gb < 0.001:
        return "0 MB"
    if gb < 1:
        return f"{gb*1024:.0f} MB"
    if gb < 1024:
        return f"{gb:.2f} GB"
    return f"{gb/1024:.2f} TB"

# ⑤ 勋章与称号配置
MEDALS = [
    {"limit": 0, "title": "🌱 空间整理新人"},
    {"limit": 1, "title": "🟢 空间整理能手"},
    {"limit": 10, "title": "🔵 缓存终结者"},
    {"limit": 30, "title": "🟣 数字生活达人"},
    {"limit": 60, "title": "🟠 数字极简大师"},
    {"limit": 100, "title": "👑 Digital Clean Legend"}
]

def get_medal_info(gb):
    current_title = MEDALS[0]["title"]
    next_title = "已封顶"
    remaining = 0.0
    
    for i in range(len(MEDALS)):
        if gb >= MEDALS[i]["limit"]:
            current_title = MEDALS[i]["title"]
            if i + 1 < len(MEDALS):
                next_title = MEDALS[i+1]["title"]
                remaining = MEDALS[i+1]["limit"] - gb
            else:
                next_title = "已达最高荣誉"
                remaining = 0
    return current_title, next_title, remaining

# ① 智能加载与旧数据结构兼容
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            
            # 兼容旧字段映射
            if "释放空间(GB)" not in df.columns and "清理大小(GB)" in df.columns:
                df["释放空间(GB)"] = df["清理大小(GB)"]
            if "整理内容" not in df.columns and "清理类型" in df.columns:
                df["整理内容"] = df["清理类型"]
            if "断舍离心得" not in df.columns and "打卡心得" in df.columns:
                df["断舍离心得"] = df["打卡心得"]
                
            # 补齐缺少的安全字段
            for col in ["ID", "删除密码", "公开属性"]:
                if col not in df.columns:
                    df[col] = ""
                    
            if "释放空间(GB)" in df.columns:
                df["释放空间(GB)"] = pd.to_numeric(df["释放空间(GB)"], errors='coerce').fillna(0.0)
                
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"]).dt.date
                
            df["删除密码"] = df["删除密码"].fillna("").astype(str)
            df["公开属性"] = df["公开属性"].fillna("公开").astype(str)
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

# 样式美化
st.markdown("""
<style>
.card{ padding:22px; border-radius:18px; background:#ffffff; box-shadow:0 4px 15px rgba(0,0,0,0.06); text-align:center; }
.big{ font-size:32px; font-weight:bold; color:#1E1E1E; margin-top:5px;}
.rank-box { padding:15px; border-radius:12px; margin:10px 0; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.04); }
</style>
""", unsafe_allow_html=True)

st.title("🧹 数字断舍离")
st.caption("Digital Clean · 每一次整理，都是一次数字空间的诗意释放")

# ③ 首页三个数字自动转换单位
total_gb = df["释放空间(GB)"].sum() if not df.empty else 0
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="card"><div>💾 累计释放空间</div><div class="big">{format_storage(total_gb)}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="card"><div>💰 创造空间价值</div><div class="big">¥ {total_gb*STORAGE_VALUE_PER_GB:.2f}</div></div>', unsafe_allow_html=True)
with c3:
    people = df["打卡人"].nunique() if not df.empty else 0
    st.markdown(f'<div class="card"><div>👥 参与玩家人数</div><div class="big">{people} 人</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🧹 今日断舍离", "📊 数据洞察", "📋 历史记录", "⚙️ 管理记录"])

# ---- Tab 1: 今日断舍离 ----
with tab1:
    st.subheader("记录今天的数字整理")
    with st.form("checkin"):
        col_name, col_device = st.columns(2)
        with col_name:
            name = st.text_input("打卡人", placeholder="请输入你的名字/昵称")
        with col_device:
            device = st.selectbox("设备", ["手机", "平板", "电脑", "其他"])
            
        col_size, col_unit = st.columns([3, 1])
        with col_size:
            size_val = st.number_input("释放空间", min_value=0.01, value=1.0, step=0.1)
        with col_unit:
            unit = st.selectbox("单位", ["GB", "MB"])
            
        types = st.multiselect("整理内容", ["📷照片", "🎬视频", "💬聊天缓存", "🗑系统垃圾", "📦APP整理", "📄文件"])
        note = st.text_area("断舍离心得")
        pwd = st.text_input("删除/查看密码（必填）", type="password")
        public = st.radio("可见性", ["公开", "私密"], horizontal=True)
        submit = st.form_submit_button("完成断舍离")

    if submit:
        if not name.strip() or not pwd.strip():
            st.error("⚠️ 请输入打卡人姓名和密码！")
        else:
            size_in_gb = size_val if unit == "GB" else size_val / 1024.0
            new_id = str(uuid.uuid4())
            new = pd.DataFrame([{
                "ID": new_id, "日期": datetime.date.today(), "打卡人": name.strip(), "清理设备": device,
                "释放空间(GB)": round(size_in_gb, 4), "整理内容": ",".join(types) if types else "常规整理",
                "断舍离心得": note if note else "数字断舍离，身心舒畅！", "删除密码": pwd_hash(pwd.strip()), "公开属性": public
            }])
            df = pd.concat([df, new], ignore_index=True)
            save_data(df)
            
            # ④ 高级感满满的打卡成功反馈
            current_streak = streak(df, name.strip())
            user_total = df[df["打卡人"] == name.strip()]["释放空间(GB)"].sum()
            
            st.success(f"🎉 🧹 断舍离成功记录！")
            c_eff1, c_eff2, c_eff3 = st.columns(3)
            with c_eff1:
                st.info(f"🔥 已连续打卡: **{current_streak}** 天")
            with c_eff2:
                st.info(f"📦 本次释放: **{format_storage(size_in_gb)}**")
            with c_eff3:
                st.info(f"💰 累计贡献: **{format_storage(user_total)}** (价值 ¥{user_total*STORAGE_VALUE_PER_GB:.2f})")
            st.balloons()
            st.rerun()

# ---- Tab 2: 数据洞察与排行榜 ----
with tab2:
    if not df.empty:
        # 📱 数字断舍离排行榜模块
        st.subheader("🏆 数字断舍离大奖赛")
        
        # 基础周期计算准备
        df_time = df.copy()
        df_time["日期_dt"] = pd.to_datetime(df_time["日期"])
        today = datetime.datetime.now()
        this_week_users = df_time[df_time["日期_dt"].dt.isocalendar().week == today.isocalendar()[1]]
        this_month_users = df_time[df_time["日期_dt"].dt.month == today.month]
        
        r_c1, r_c2, r_c3 = st.columns(3)
        with r_c1:
            st.markdown("<h5 style='text-align:center;'>🥇 总榜总冠军</h5>", unsafe_allow_html=True)
            rank_all = df.groupby("打卡人")["释放空间(GB)"].sum().reset_index().sort_values(by="释放空间(GB)", ascending=False)
            if len(rank_all) >= 1:
                st.markdown(f'<div class="rank-box" style="background:#FFF3CD; border:1px solid #FFEBAA;">👑 <b>{rank_all.iloc[0]["打卡人"]}</b><br>{format_storage(rank_all.iloc[0]["释放空间(GB)"])}</div>', unsafe_allow_html=True)
        with r_c2:
            st.markdown("<h5 style='text-align:center;'>⚡ 本周冠军</h5>", unsafe_allow_html=True)
            if not this_week_users.empty:
                rank_week = this_week_users.groupby("打卡人")["释放空间(GB)"].sum().reset_index().sort_values(by="释放空间(GB)", ascending=False)
                st.markdown(f'<div class="rank-box" style="background:#E2F0D9;">🏃 <b>{rank_week.iloc[0]["打卡人"]}</b><br>{format_storage(rank_week.iloc[0]["释放空间(GB)"])}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="rank-box" style="background:#F2F2F2; color:#8C8C8C;">本周暂无打卡</div>', unsafe_allow_html=True)
        with r_c3:
            st.markdown("<h5 style='text-align:center;'>📅 本月冠军</h5>", unsafe_allow_html=True)
            if not this_month_users.empty:
                rank_month = this_month_users.groupby("打卡人")["释放空间(GB)"].sum().reset_index().sort_values(by="释放空间(GB)", ascending=False)
                st.markdown(f'<div class="rank-box" style="background:#DEEBF7;">🏅 <b>{rank_month.iloc[0]["打卡人"]}</b><br>{format_storage(rank_month.iloc[0]["释放空间(GB)"])}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="rank-box" style="background:#F2F2F2; color:#8C8C8C;">本月暂无打卡</div>', unsafe_allow_html=True)
                
        st.divider()
        
        # ⑤ 勋章荣誉查询系统
        st.subheader("🏅 玩家成就勋章查询")
        query_name = st.selectbox("选择要查看的玩家", df["打卡人"].unique())
        if query_name:
            user_space = df[df["打卡人"] == query_name]["释放空间(GB)"].sum()
            c_title, n_title, rem_gb = get_medal_info(user_space)
            
            mc1, mc2 = st.columns([1, 2])
            with mc1:
                st.metric("当前最高称号", c_title)
            with mc2:
                if n_title != "已封顶":
                    st.info(f"🌟 升级进度：距离获得称号 **【{n_title}】** 还需努力释放 **{format_storage(rem_gb)}** 空间！")
                else:
                    st.success("🎉 恭喜！你已达到数字极简的最高荣誉殿堂！")
                    
        st.divider()

        # 图表展示
        st.subheader("📊 空间趋势与多维图表")
        trend = df.copy()
        trend["日期显示"] = pd.to_datetime(trend["日期"]).dt.strftime('%Y-%m-%d')
        trend_grouped = trend.groupby(["日期显示", "打卡人"])["释放空间(GB)"].sum().reset_index().sort_values(by="日期显示")

        fig = px.line(trend_grouped, x="日期显示", y="释放空间(GB)", color="打卡人", markers=True, title="每日释放趋势")
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            device_df = df.groupby("清理设备")["释放空间(GB)"].sum().reset_index()
            fig = px.pie(device_df, names="清理设备", values="释放空间(GB)", title="设备整理比例", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # ⑦ 更直观的累计释放柱状图
            people_df = df.groupby("打卡人")["释放空间(GB)"].sum().reset_index().sort_values(by="释放空间(GB)", ascending=True)
            fig_bar = px.bar(people_df, x="释放空间(GB)", y="打卡人", orientation='h', title="成员历史累计释放空间 (GB)",
                             color="打卡人", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("暂无数据，打卡后即可查看图表看板。")

# ---- Tab 3: 历史记录（包含多维筛选） ----
with tab3:
    st.subheader("📋 历史记录明细")
    if not df.empty:
        public_df = df[df["公开属性"] == "公开"].copy()
        show_private = False
        private_df = pd.DataFrame()
        
        with st.expander("🔐 解锁我自己的私密记录"):
            v_name = st.text_input("打卡名字", key="view_name")
            v_pwd = st.text_input("查看密码", type="password", key="view_pwd")
            if v_name and v_pwd:
                private_df = df[(df["打卡人"] == v_name.strip()) & (df["删除密码"] == pwd_hash(v_pwd.strip())) & (df["公开属性"] == "私密")].copy()
                if not private_df.empty:
                    st.success(f"🔓 已成功并入属于你的私密记录！")
                    show_private = True
                else:
                    st.warning("未找到匹配的私密记录。")

        display_df = pd.concat([public_df, private_df]).drop_duplicates().reset_index(drop=True) if show_private else public_df

        if not display_df.empty:
            # ⑥ 历史记录的高级过滤器筛选
            st.write("### 🔍 联动数据筛选")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_device = st.multiselect("筛选清理设备", options=list(display_df["清理设备"].unique()), default=list(display_df["清理设备"].unique()))
            with f_col2:
                filter_pub = st.multiselect("筛选可见性", options=list(display_df["公开属性"].unique()), default=list(display_df["公开属性"].unique()))
                
            # 执行过滤
            filtered_df = display_df[
                (display_df["清理设备"].isin(filter_device)) & 
                (display_df["公开属性"].isin(filter_pub))
            ].copy()
            
            show_table = filtered_df.drop(columns=["删除密码", "ID"], errors="ignore").sort_values(by="日期", ascending=False)
            st.dataframe(show_table, use_container_width=True)
        else:
            st.info("暂无可见的打卡记录。")
    else:
        st.info("暂无历史记录。")

# ---- Tab 4: 管理记录（完全盲删防护机制） ----
with tab4:
    st.subheader("⚙️ 身份验证与安全管理")
    st.write("💡 *为了全员隐私安全，系统不会默认列出历史打卡，请输入您的账号进行双因子匹配：*")
    
    # ② 输入名字和密码
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        auth_name = st.text_input("您的打卡姓名", placeholder="确认要管理谁的记录")
    with col_v2:
        auth_pwd = st.text_input("您的安全密码", type="password", placeholder="输入密码以解锁管理面板")
        
    if auth_name and auth_pwd:
        hashed_input = pwd_hash(auth_pwd.strip())
        # 筛选此人名下且密码正确的记录
        my_records = df[(df["打卡人"] == auth_name.strip()) & (df["删除密码"] == hashed_input)]
        
        if not my_records.empty:
            st.success(f"🔓 身份验证成功！检测到您名下共有 {len(my_records)} 条可编辑数据。")
            
            # 将 ID 包装成人类可读的选择框
            record_map = {}
            options = []
            for idx, row in my_records.iterrows():
                label = f"【{row['日期']}】 整理了 {format_storage(row['释放空间(GB)'])} | 内容: {row['整理内容']} [{row['公开属性']}]"
                record_map[label] = row["ID"]
                options.append(label)
                
            selected_label = st.selectbox("选择一条由您创建的错误记录进行清除：", options)
            target_id = record_map[selected_label]
            
            if st.button("❌ 确认执行物理删除", type="primary"):
                df = df[df["ID"] != target_id].reset_index(drop=True)
                save_data(df)
                st.success("🎉 数据销毁成功，正在更新视图...")
                st.rerun()
        else:
            st.error("❌ 身份校验失败：未找到对应的打卡账号，或安全密码不匹配。")
    else:
        st.info("🔒 请完整填写上方凭证以调取属于您的可管辖数据。")
