import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(page_title="Typhoon Genesis Simulator", layout="wide")
st.title("🌀 Typhoon Genesis Dynamics: Monte Carlo Simulation vs. ERA5 Observations")


st.sidebar.header("⚙️ Simulation Thresholds")
n_sims = st.sidebar.slider("Monte Carlo Samples", 100, 10000, 5000, step=100)
t_sst = st.sidebar.slider("Min Sea Surface Temp (°C)", 25.0, 35.0, 26.5, 0.1)
t_shear = st.sidebar.slider("Max Wind Shear Proxy (kt)", 5.0, 30.0, 20.0, 1.0)
t_humid = st.sidebar.slider("Min Relative Humidity (%)", 40.0, 100.0, 70.0, 1.0)
t_lat = st.sidebar.slider("Min Latitude (°N) [Coriolis]", 0.0, 30.0, 0.0, 1.0)
t_pres = st.sidebar.slider("Max MSLP (hPa)", 980.0, 1030.0, 1005.0, 1.0)


@st.cache_data
def get_data(n, t_s, t_sh, t_h, t_l, t_p):
   
    real_file = 'real_genesis_data.csv'
    try:
        df_real = pd.read_csv(real_file)
        if 'Type' not in df_real.columns:
            df_real['Type'] = 'Real Observation'
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # 如果找不到檔案，或是檔案是空的，就給一個空的資料表，不讓網頁崩潰
        df_real = pd.DataFrame()

    # 執行蒙地卡羅模擬
    np.random.seed(42)
    s_arr = np.random.normal(27.5, 1.5, n)
    sh_arr = np.random.normal(15.0, 5.0, n)
    h_arr = np.random.normal(75.0, 10.0, n)
    lat_arr = np.random.normal(15.0, 5.0, n)
    pres_arr = np.random.normal(1000.0, 8.0, n)
    
    # 物理門檻判定
    is_formed = (s_arr > t_s) & (sh_arr < t_sh) & (h_arr > t_h) & (lat_arr > t_l) & (pres_arr < t_p)
    
    df_sim = pd.DataFrame({
        'SST': s_arr[is_formed], 'Shear': sh_arr[is_formed],
        'Humidity': h_arr[is_formed], 'Lat': lat_arr[is_formed],
        'Pressure': pres_arr[is_formed], 'Type': 'Monte Carlo Simulation'
    })
    return df_real, df_sim, n

df_real, df_sim, total_sampled = get_data(n_sims, t_sst, t_shear, t_humid, t_lat, t_pres)
df_all = pd.concat([df_real, df_sim], ignore_index=True) if not df_real.empty else df_sim

# ================= 3. 頂部數據儀表板 =================
c1, c2, c3 = st.columns(3)
c1.metric("Total Simulated Environments", f"{total_sampled:,}")
c2.metric("Simulated Typhoons Formed", f"{len(df_sim):,} ({len(df_sim)/total_sampled*100:.1f}%)")
c3.metric("Real ERA5 Observations", f"{len(df_real):,} points")
st.markdown("---")

if df_real.empty:
    st.error("⚠️ 找不到 `real_genesis_data.csv`！請確認檔案在同一資料夾內。")

# ================= 4. 高階互動圖表繪製 =================
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