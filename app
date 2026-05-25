import streamlit as st
import pandas as pd
import xarray as xr
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Typhoon Genesis: Real vs Sim", layout="wide")
st.title("🌀 Typhoon Genesis: ERA5 vs Monte Carlo Simulation")

# ==========================================
# 1. 核心函數：計算相對濕度 (Magnus Formula)
# ==========================================
def calculate_rh(t2m, d2m):
    # 若下載的是 Kelvin，需先轉為 Celsius
    if t2m > 100: t2m -= 273.15
    if d2m > 100: d2m -= 273.15
    # Magnus formula for Relative Humidity
    e = 6.11 * 10.0 ** (7.5 * d2m / (237.3 + d2m))
    es = 6.11 * 10.0 ** (7.5 * t2m / (237.3 + t2m))
    return (e / es) * 100

# ==========================================
# 2. 資料讀取與對齊 (Data Fusion)
# ==========================================
@st.cache_data
def load_and_merge_data():
    # 讀取 IBTrACS
    ibtracs_path = 'ibtracs.WP.list.v04r01.csv(1)'
    df_ib = pd.read_csv(ibtracs_path, skiprows=[1], low_memory=False)
    df_ib['ISO_TIME'] = pd.to_datetime(df_ib['ISO_TIME'])
    df_ib['USA_WIND'] = pd.to_numeric(df_ib['USA_WIND'], errors='coerce')
    
    # 篩選 2020-2026 年且風速 >= 34 的首次成颱點
    df_ib = df_ib[(df_ib['SEASON'] >= 2020) & (df_ib['USA_WIND'] >= 34)]
    genesis_points = df_ib.groupby('SID').first().reset_index()

    # 讀取 ERA5 (假設你下載的檔案叫 era5_data.nc)
    era5_path = 'era5_data.nc'
    real_data_list = []
    
    if os.path.exists(era5_path):
        ds = xr.open_dataset(era5_path)
        
        # 針對每個真實颱風生成點，去 ERA5 找最近的環境數值
        for _, row in genesis_points.iterrows():
            try:
                # 尋找空間與時間最接近的網格點
                env = ds.sel(
                    time=row['ISO_TIME'], 
                    latitude=row['LAT'], 
                    longitude=row['LON'], 
                    method='nearest'
                )
                
                # 萃取數值 (注意：ERA5 變數名稱可能因下載而異，如 sst, u10, v10, d2m, sp)
                sst = env['sst'].values - 273.15 # Kelvin to Celsius
                u10 = env['u10'].values
                v10 = env['v10'].values
                wind_shear = np.sqrt(u10**2 + v10**2) # 地表風速梯度作為簡化風切
                
                # 計算濕度 (假設以 SST 近似底層氣溫 t2m 計算)
                d2m = env['d2m'].values - 273.15
                rh = calculate_rh(sst, d2m)
                
                real_data_list.append({
                    'Type': 'Real Observation (ERA5)',
                    'SST': float(sst),
                    'Shear': float(wind_shear),
                    'Humidity': float(rh)
                })
            except Exception as e:
                continue # 若超出 ERA5 時間/空間範圍則跳過
                
    return pd.DataFrame(real_data_list)

# ==========================================
# 3. 蒙地卡羅模擬 (Monte Carlo Simulation)
# ==========================================
def generate_simulation(n_sims=2000):
    np.random.seed(42)
    sst = np.random.normal(28.5, 1.5, n_sims)
    shear = np.random.normal(12.0, 5.0, n_sims)
    humid = np.random.normal(75.0, 10.0, n_sims)
    
    valid = (sst >= 26.5) & (shear <= 20) & (humid >= 60)
    z = (0.8 * sst) + (0.1 * humid) - (0.2 * shear) - 25
    prob = np.where(valid, 1 / (1 + np.exp(-z)), 0)
    
    is_typhoon = (np.random.random(n_sims) < prob)
    
    df_sim = pd.DataFrame({'SST': sst[is_typhoon], 'Shear': shear[is_typhoon], 'Humidity': humid[is_typhoon]})
    df_sim['Type'] = 'Simulation (Monte Carlo)'
    return df_sim

# ==========================================
# 4. 儀表板視覺化 (English Labels)
# ==========================================
st.sidebar.header("Data Status")
with st.spinner('Fusing ERA5 and IBTrACS Data...'):
    df_real = load_and_merge_data()
    df_sim = generate_simulation()

if not df_real.empty:
    df_combined = pd.concat([df_real, df_sim], ignore_index=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Real Genesis Records Fused", len(df_real))
    col2.metric("Simulated Genesis Points", len(df_sim))
    
    st.markdown("---")
    
    # 圖 1: Scatter Plot
    fig1 = px.scatter(
        df_combined, x="SST", y="Shear", color="Type",
        color_discrete_map={"Real Observation (ERA5)": "blue", "Simulation (Monte Carlo)": "red"},
        opacity=0.6, title="SST vs Wind Shear (Real vs Sim)",
        labels={"SST": "Sea Surface Temperature (°C)", "Shear": "Surface Wind/Shear Indicator (kt)"}
    )
    fig1.add_vline(x=26.5, line_dash="dash", line_color="green", annotation_text="26.5°C Threshold")
    st.plotly_chart(fig1, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        # 圖 2: Histogram for Humidity
        fig2 = px.histogram(
            df_combined, x="Humidity", color="Type", barmode="overlay",
            title="Distribution of Genesis Humidity",
            labels={"Humidity": "Relative Humidity (%)"}
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    with c2:
        # 圖 3: Boxplot for SST
        fig3 = px.box(
            df_combined, x="Type", y="SST", color="Type",
            title="SST Spread Comparison",
            labels={"SST": "Sea Surface Temperature (°C)"}
        )
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("Please ensure 'era5_data.nc' and 'ibtracs.csv' are in the same folder.")