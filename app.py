import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px

# 页面基础配置
st.set_page_config(
    page_title="📱 空间拯救计划 - 每日内存清理打卡",
    page_icon="💾",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 数据存储文件名
DATA_FILE = "storage_checkin_data.csv"

# 初始化数据加载
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            # 确保有“删除密码”列
            if "删除密码" not in df.columns:
                df["删除密码"] = ""
            # 填充空密码
            df["删除密码"] = df["删除密码"].fillna("").astype(str)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=["日期", "打卡人", "清理设备", "清理大小(GB)", "清理类型", "打卡心得", "删除密码"])

# 保存数据
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# 加载数据
df = load_data()

# 侧边栏：关于与统计
with st.sidebar:
    st.markdown("# 💾 空间拯救计划")
    st.markdown("这是一个专门用来记录你和朋友每天清理手机、平板等设备内存（存储空间）的打卡小工具。相互监督，拒绝空间焦虑！")
    st.divider()
    
    if not df.empty:
        st.markdown("### 🏆 累计战报")
        total_gb = df["清理大小(GB)"].sum()
        st.metric(label="双人累计拯救空间", value=f"{total_gb:.2f} GB")
        
        # 每个人清理的量
        st.markdown("### 👥 个人战绩")
        member_stats = df.groupby("打卡人")["清理大小(GB)"].sum()
        for name, gb in member_stats.items():
            st.write(f"**{name}**: 已累计清理 `{gb:.2f} GB`")
    else:
        st.info("暂无打卡数据，快去提交今天的打卡吧！")

# 主页面
st.title("📱 内存与存储清理打卡")

# 创建标签页
tab_checkin, tab_dashboard, tab_history = st.tabs(["✍️ 今日打卡", "📊 统计看板", "📋 历史明细"])

# ---- 标签页 1：今日打卡 ----
with tab_checkin:
    st.subheader("记录今天的清理成果")
    
    with st.form("checkin_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("打卡人", placeholder="请输入你的名字/昵称", max_chars=15)
            device = st.selectbox("清理设备", ["手机", "平板", "电脑", "其他"])
        with col2:
            clean_value = st.number_input("清理大小", min_value=0.01, max_value=2048.0, value=1.0, step=0.1)
            unit = st.selectbox("单位", ["GB", "MB"])
            
        clean_type = st.multiselect(
            "清理内容 (可多选)",
            ["微信/聊天软件缓存", "系统垃圾", "相册照片/视频", "卸载无用APP", "浏览器缓存", "音乐/视频离线文件", "其他"]
        )
        
        comment = st.text_area("打卡心得 / 吐槽", placeholder="今天删了2000张过期的表情包，神清气爽！", max_chars=150)
        
        # 新增：删除密码设置
        del_pwd = st.text_input("设置删除密码 (必填，用于以后自助删除错误记录)", type="password", max_chars=20, help="如果以后发现这条记录记错了，需要凭此密码删除。")
        
        submit_btn = st.form_submit_button("🚀 提交今日打卡")
        
    if submit_btn:
        # 校验
        if not name.strip():
            st.error("⚠️ 请输入打卡人名字后再提交！")
        elif not del_pwd.strip():
            st.error("⚠️ 为了防止别人误删你的记录，请务必设置一个“删除密码”！")
        else:
            # 单位换算为GB
            size_in_gb = clean_value if unit == "GB" else clean_value / 1024.0
            today = datetime.date.today()
            
            # 格式化清理类型
            type_str = ", ".join(clean_type) if clean_type else "日常清理"
            
            new_record = {
                "日期": today,
                "打卡人": name.strip(),
                "清理设备": device,
                "清理大小(GB)": round(size_in_gb, 4),
                "清理类型": type_str,
                "打卡心得": comment if comment else "坚持打卡！",
                "删除密码": del_pwd.strip()
            }
            
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            save_data(df)
            st.success(f"🎉 打卡成功！{name.strip()} 今天成功拯救了 {clean_value} {unit} 的空间！")
            st.balloons()
            # 重新加载以更新图表
            st.rerun()

# ---- 标签页 2：统计看板 ----
with tab_dashboard:
    st.subheader("📈 数据可视化看板")
    if not df.empty:
        # 数据按日期排序
        df_sorted = df.sort_values(by="日期")
        
        # 1. 每日清理趋势折线图
        fig_trend = px.line(
            df_sorted.groupby(["日期", "打卡人"])["清理大小(GB)"].sum().reset_index(),
            x="日期",
            y="清理大小(GB)",
            color="打卡人",
            title="每日空间释放趋势 (GB)",
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # 2. 饼图：清理类型分布与设备分布
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_device = px.pie(
                df, 
                names="清理设备", 
                values="清理大小(GB)", 
                title="不同设备的清理比例"
            )
            st.plotly_chart(fig_device, use_container_width=True)
        with col_chart2:
            fig_member = px.pie(
                df, 
                names="打卡人", 
                values="清理大小(GB)", 
                title="贡献度 PK (GB)"
            )
            st.plotly_chart(fig_member, use_container_width=True)
            
    else:
        st.info("还没有数据哦，完成第一次打卡后将在此处展示图表。")

# ---- 标签页 3：历史明细 ----
with tab_history:
    st.subheader("📋 历史打卡明细")
    if not df.empty:
        # 在前端展示时，把“删除密码”这一列隐藏，防止密码泄露
        display_df = df.copy()
        if "删除密码" in display_df.columns:
            display_df = display_df.drop(columns=["删除密码"])
            
        # 倒序显示，最新打卡的在最上面
        st.dataframe(
            display_df.sort_values(by="日期", ascending=False),
            use_container_width=True,
            column_config={
                "清理大小(GB)": st.column_config.NumberColumn(format="%.3f GB")
            }
        )
        
        st.divider()
        
        # ---- 新增：自主删除错误记录功能 ----
        st.subheader("⚠️ 删除错误记录")
        st.write("如果你不小心记错了，可以在下方自主删除你自己的记录：")
        
        # 给每条记录生成一个唯一的展示标签 (带上索引，方便准确定位)
        record_options = []
        for idx, row in df.iterrows():
            record_options.append(f"【ID: {idx}】 {row['日期']} - {row['打卡人']} 清理了 {row['清理大小(GB)']:.3f} GB")
            
        selected_record_str = st.selectbox("选择要删除的记录", record_options)
        
        if selected_record_str:
            # 解析出选中的行索引 (idx)
            selected_idx = int(selected_record_str.split("【ID: ")[1].split("】")[0])
            target_row = df.loc[selected_idx]
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                input_name = st.text_input("请输入打卡人姓名以验证", placeholder="必须与记录中的名字一致", key="del_name")
            with col_del2:
                input_pwd = st.text_input("请输入该条记录的删除密码", type="password", key="del_pwd")
                
            if st.button("❌ 确认删除这条记录", type="primary"):
                # 校验名字 and 密码
                correct_name = str(target_row["打卡人"]).strip()
                correct_pwd = str(target_row["删除密码"]).strip()
                
                if input_name.strip() != correct_name:
                    st.error("❌ 验证失败：输入的打卡人名字不正确！")
                elif input_pwd.strip() != correct_pwd:
                    st.error("❌ 验证失败：删除密码不正确！")
                else:
                    # 执行删除
                    df = df.drop(selected_idx).reset_index(drop=True)
                    save_data(df)
                    st.success("🎉 记录删除成功！正在刷新网页...")
                    st.rerun()
        
        st.divider()
        
        # 提供CSV下载
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 导出全部打卡数据为 CSV",
            data=csv_data,
            file_name="storage_checkin_data.csv",
            mime="text/csv"
        )
    else:
        st.info("暂无历史记录。")
