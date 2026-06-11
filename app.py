import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Typhoon Genesis Simulator", layout="wide")
st.title("🌀 Typhoon Genesis Dynamics: Monte Carlo Simulation vs. ERA5 Observations")

# ================= 1. 側邊欄 UI 升級 =================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3093/3093390.png", width=100)
st.sidebar.title("🌍 系統控制中心")
st.sidebar.markdown("調整大氣物理門檻，透過機率模型過濾虛擬擾動。")

with st.sidebar.expander("🎯 蒙地卡羅抽樣設定", expanded=True):
    n_sims = st.slider("隨機生成環境樣本數", 100, 10000, 5000, step=100)

with st.sidebar.expander("🌡️ 熱力學門檻 (Thermodynamic)", expanded=True):
    t_sst = st.slider("最低海溫門檻 (°C)", 25.0, 35.0, 26.5, 0.1)
    t_humid = st.slider("最低相對濕度 (%)", 40.0, 100.0, 70.0, 1.0)

with st.sidebar.expander("🌪️ 動力學門檻 (Kinematic)", expanded=True):
    t_shear = st.slider("最大垂直風切 (kt)", 5.0, 30.0, 20.0, 1.0)
    t_lat = st.slider("最低生成緯度 (°N)", 0.0, 30.0, 5.0, 1.0)
    t_pres = st.slider("最高海平面氣壓 (hPa)", 980.0, 1030.0, 1005.0, 1.0)

st.sidebar.markdown("---")

# ================= 2. 核心機率與連鎖反應引擎 =================
@st.cache_data
def get_data(n, t_s, t_sh, t_h, t_l, t_p):
    real_file = 'real_genesis_data.csv'
    try:
        df_real = pd.read_csv(real_file)
        if 'Type' not in df_real.columns:
            df_real['Type'] = 'Real Observation'
    except (FileNotFoundError, pd.errors.EmptyDataError):
        df_real = pd.DataFrame()

    np.random.seed(42)
    features_to_learn = ['SST', 'Shear', 'Humidity', 'Lat', 'Lon', 'Pressure']
    
    # 🧠 多變量常態分佈 (學習真實環境的連鎖反應)
    if not df_real.empty and all(f in df_real.columns for f in features_to_learn):
        df_valid = df_real.dropna(subset=features_to_learn)
        means = df_valid[features_to_learn].mean().values
        cov_matrix = df_valid[features_to_learn].cov().values
        
        sim_data = np.random.multivariate_normal(means, cov_matrix, n)
        s_arr, sh_arr, h_arr = sim_data[:, 0], sim_data[:, 1], sim_data[:, 2]
        lat_arr, lon_arr, pres_arr = sim_data[:, 3], sim_data[:, 4], sim_data[:, 5]
    else:
        s_arr = np.random.normal(27.5, 1.5, n)
        sh_arr = np.random.normal(15.0, 5.0, n)
        h_arr = np.random.normal(75.0, 10.0, n)
        lat_arr = np.random.normal(15.0, 5.0, n)
        lon_arr = np.random.normal(135.0, 15.0, n) 
        pres_arr = np.random.normal(1000.0, 8.0, n)
    
    year_arr = np.random.choice(range(2006, 2027), n) 
    
    # 🛡️ 陸地遮罩 (排除中國內陸與中南半島)
    is_inland_china = (lon_arr < 120) & (lat_arr > 22)
    is_indochina = (lon_arr < 109) & (lat_arr > 8) & (lat_arr < 22)
    is_ocean = ~(is_inland_china | is_indochina)

    # 🎲 Sigmoid 機率模糊門檻
    def sigmoid(x, threshold, k=1.0, reverse=False):
        if reverse:
            return 1 / (1 + np.exp(k * (x - threshold)))
        else:
            return 1 / (1 + np.exp(-k * (x - threshold)))

    prob_sst = sigmoid(s_arr, t_s, k=2.0)
    prob_shear = sigmoid(sh_arr, t_sh, k=0.5, reverse=True)
    prob_humid = sigmoid(h_arr, t_h, k=0.2)
    prob_lat = sigmoid(lat_arr, t_l, k=0.5)
    prob_pres = sigmoid(pres_arr, t_p, k=0.5, reverse=True)

    # 綜合生存機率對決大自然亂數
    combined_prob = prob_sst * prob_shear * prob_humid * prob_lat * prob_pres * is_ocean
    random_dice = np.random.random(n)
    is_formed = combined_prob > random_dice
    
    df_sim = pd.DataFrame({
        'SST': s_arr[is_formed], 'Shear': sh_arr[is_formed],
        'Humidity': h_arr[is_formed], 'Lat': lat_arr[is_formed],
        'Lon': lon_arr[is_formed], 'Year': year_arr[is_formed],
        'Pressure': pres_arr[is_formed], 'Type': 'Monte Carlo Simulation'
    })
    return df_real, df_sim, n

df_real, df_sim, total_sampled = get_data(n_sims, t_sst, t_shear, t_humid, t_lat, t_pres)
df_all = pd.concat([df_real, df_sim], ignore_index=True) if not df_real.empty else df_sim

# ================= 3. 儀表板與基礎圖表 =================
c1, c2, c3 = st.columns(3)
c1.metric("Total Simulated Environments", f"{total_sampled:,}")
c2.metric("Simulated Typhoons Formed", f"{len(df_sim):,} ({len(df_sim)/total_sampled*100:.1f}%)")
c3.metric("Real ERA5 Observations", f"{len(df_real):,} points")
st.markdown("---")

if df_real.empty:
    st.error("⚠️ 找不到 `real_genesis_data.csv`！請確認檔案在同一資料夾內。")

color_map = {"Real Observation": "#1F77B4", "Monte Carlo Simulation": "#FF7F0E"}

r1_c1, r1_c2 = st.columns(2)
with r1_c1:
    fig1 = px.scatter(df_all, x="SST", y="Shear", color="Type", opacity=0.7, color_discrete_map=color_map, title="SST vs. Wind Shear (Thermodynamic vs Kinematic)")
    fig1.add_vline(x=t_sst, line_dash="dot", line_color="gray")
    fig1.add_hline(y=t_shear, line_dash="dot", line_color="gray")
    st.plotly_chart(fig1, use_container_width=True)

with r1_c2:
    if 'Pressure' in df_all.columns:
        fig2 = px.scatter(df_all, x="Lat", y="Pressure", color="Type", opacity=0.7, color_discrete_map=color_map, title="Latitude vs. MSLP (Coriolis vs Dynamics)")
        st.plotly_chart(fig2, use_container_width=True)

r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    fig3 = px.histogram(df_all, x="Humidity", color="Type", barmode="overlay", color_discrete_map=color_map, title="Relative Humidity Distribution")
    st.plotly_chart(fig3, use_container_width=True)

with r2_c2:
    fig4 = px.box(df_all, x="Type", y="SST", color="Type", color_discrete_map=color_map, title="SST Statistical Spread Comparison")
    st.plotly_chart(fig4, use_container_width=True)

# ================= 4. 進階大氣物理與機器學習分析 =================
st.markdown("---")
st.title("🌟 進階大氣物理與機器學習分析")

tab1, tab2, tab3 = st.tabs(["📊 機器學習特徵權重", "🔗 大氣變數連鎖反應", "🌍 歷史颱風動態雲圖"])

df_real_only = df_all[df_all['Type'] == 'Real Observation'].copy()
features = ['SST', 'Shear', 'Humidity', 'Pressure', 'Lat']

with tab1:
    st.subheader("Random Forest 機器學習：成颱關鍵變數影響力占比")
    if not df_real_only.empty and all(f in df_real_only.columns for f in features):
        X_real = df_real_only[features]
        y_real = np.ones(len(X_real))
        
        np.random.seed(42)
        bg_n = len(X_real)
        X_bg = pd.DataFrame({
            'SST': np.random.normal(27.5, 1.5, bg_n),
            'Shear': np.random.normal(15.0, 5.0, bg_n),
            'Humidity': np.random.normal(75.0, 10.0, bg_n),
            'Pressure': np.random.normal(1000.0, 8.0, bg_n),
            'Lat': np.random.normal(15.0, 5.0, bg_n)
        })
        y_bg = np.zeros(bg_n)
        
        X_train = pd.concat([X_real, X_bg])
        y_train = np.concatenate([y_real, y_bg])
        
        rf = RandomForestClassifier(random_state=42)
        rf.fit(X_train, y_train)
        importances = rf.feature_importances_
        
        fig_pie = px.pie(names=features, values=importances, hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.subheader("大氣環境熱力圖 (Correlation Heatmap)")
    if not df_real_only.empty and all(f in df_real_only.columns for f in features):
        corr_matrix = df_real_only[features].corr()
        fig_heatmap = px.imshow(corr_matrix, text_auto=".2f", aspect="auto",
                                color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
        st.plotly_chart(fig_heatmap, use_container_width=True)

with tab3:
    st.subheader("太平洋颱風生成大戰：真實觀測 vs 蒙地卡羅模擬 (2006 - 2026)")
    st.write("藍點為大自然真實生成的颱風，橘點為依據機率模型與地型遮罩所存活下來的虛擬颱風。")
    
    if 'Lon' in df_all.columns and 'Year' in df_all.columns:
        df_map = df_all.dropna(subset=['Lon', 'Lat', 'Year']).sort_values(by='Year')
        
        fig_map = px.scatter_geo(
            df_map, 
            lat='Lat', lon='Lon', 
            color='Type', 
            color_discrete_map=color_map,
            hover_name='Type',
            size='SST', 
            size_max=12,
            animation_frame='Year', 
            projection='natural earth',
            opacity=0.7
        )
        
        fig_map.update_geos(
            center=dict(lon=135, lat=20),
            projection_scale=3.5,
            showcoastlines=True, coastlinecolor="Black",
            showland=True, landcolor="lightgrey",
            showocean=True, oceancolor="aliceblue"
        )
        st.plotly_chart(fig_map, use_container_width=True)