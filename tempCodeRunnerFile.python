import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="成颱機率模擬與真實對比", layout="wide")
st.title("🌀 熱帶性低氣壓成颱機率：模擬預測 vs 真實歷史")

# ================= 1. 側邊欄設定 =================
st.sidebar.header("環境變數設定 (蒙地卡羅)")
mean_sst = st.sidebar.slider("平均海溫 (°C)", 24.0, 32.0, 28.0, 0.1)
mean_shear = st.sidebar.slider("平均垂直風切 (kt)", 0.0, 30.0, 10.0, 1.0)
n_sims = st.sidebar.number_input("模擬次數", 1000, 50000, 10000)

# ================= 2. 模擬數據生成 (加入絕對物理門檻) =================
def generate_simulation():
    np.random.seed(42)
    sst = np.random.normal(mean_sst, 1.5, n_sims)
    shear = np.random.normal(mean_shear, 5.0, n_sims)
    humid = np.random.normal(75, 10.0, n_sims)
    
    # 物理絕對門檻 (硬限制)
    valid_threshold = (sst >= 26.5) & (shear <= 20) & (humid >= 60)
    
    # 公式轉換機率 (只計算符合門檻的)
    z = (0.8 * sst) + (0.1 * humid) - (0.2 * shear) - 25
    prob = np.where(valid_threshold, 1 / (1 + np.exp(-z)), 0) # 沒過門檻機率直接為0
    
    is_typhoon = (np.random.random(n_sims) < prob).astype(int)
    
    df = pd.DataFrame({'SST': sst, 'Shear': shear, 'Humidity': humid, 'Is_Typhoon': is_typhoon})
    df['Label'] = df['Is_Typhoon'].map({1: '成颱', 0: '未成颱'})
    return df

df_sim = generate_simulation()

# ================= 3. 讀取真實 IBTrACS 資料 =================
@st.cache_data # 快取資料避免每次拉動滑桿都重新讀取大檔案
def load_ibtracs():
    file_path = 'ibtracs.WP.list.v04r01.csv'
    if os.path.exists(file_path):
        # 略過第二行單位列，指定讀取需要的欄位以節省記憶體
        df = pd.read_csv(file_path, skiprows=[1], usecols=['SEASON', 'NAME', 'LAT', 'LON', 'USA_WIND', 'USA_PRES'], low_memory=False)
        # 篩選出有風速紀錄且大於等於34節(輕颱標準)的資料
        df['USA_WIND'] = pd.to_numeric(df['USA_WIND'], errors='coerce')
        df_typhoon = df[df['USA_WIND'] >= 34].dropna(subset=['LAT', 'LON'])
        return df_typhoon
    return None

df_real = load_ibtracs()

# ================= 4. 儀表板視覺化 =================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 左腦：蒙地卡羅模擬結果")
    st.metric("模擬整體成颱率", f"{(df_sim['Is_Typhoon'].sum() / n_sims)*100:.2f} %")
    
    # 改用 Plotly 畫散佈圖 (解決亂碼，且支援互動)
    fig_sim = px.scatter(df_sim.sample(min(2000, n_sims)), x="SST", y="Shear", color="Label",
                         color_discrete_map={"成颱": "red", "未成颱": "lightgray"},
                         title="模擬：海溫 vs 風切 (注意 26.5度 門檻切線)",
                         labels={"SST": "海溫 (°C)", "Shear": "垂直風切 (kt)"})
    fig_sim.add_vline(x=26.5, line_dash="dash", line_color="green", annotation_text="26.5°C 門檻")
    st.plotly_chart(fig_sim, use_container_width=True)
    
    # 新增箱型圖 (Box plot) 顯示分佈
    fig_box = px.box(df_sim, x="Label", y="Humidity", color="Label", title="模擬：中低層濕度分佈差異")
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    st.subheader("🌎 右腦：真實 IBTrACS 歷史對比")
    if df_real is not None:
        st.metric("歷史成颱資料筆數", f"{len(df_real):,} 筆 (USA_WIND >= 34)")
        
        # 繪製真實歷史成颱的熱區圖 (Hexbin) 或 散佈圖
        fig_real = px.density_mapbox(df_real, lat='LAT', lon='LON', z='USA_WIND', radius=5,
                                     center=dict(lat=15, lon=135), zoom=2,
                                     mapbox_style="carto-positron",
                                     title="真實：西北太平洋歷史颱風生成位置熱區")
        st.plotly_chart(fig_real, use_container_width=True)
        
        # 繪製真實風速分佈圖 (直方圖)
        fig_hist = px.histogram(df_real, x="USA_WIND", nbins=50, title="真實：歷史颱風最大風速分佈 (kt)", color_discrete_sequence=['indianred'])
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning("⚠️ 找不到 `ibtracs.WP.list.v04r01.csv`，請確認檔案是否放在同一資料夾！")