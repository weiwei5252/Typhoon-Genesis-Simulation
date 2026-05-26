import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 解決 Matplotlib 中文顯示問題
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="成颱機率蒙地卡羅模擬", layout="wide")

st.title("🌀 熱帶性低氣壓成颱機率模擬器")
st.markdown("基於海溫、風切、濕度與緯度(科氏力)的蒙地卡羅模擬")

# ================= 1. 側邊欄：手動設定環境變數 =================
st.sidebar.header("環境變數設定")
mean_sst = st.sidebar.slider("平均海溫 (SST, °C)", 24.0, 32.0, 28.0, 0.1)
mean_shear = st.sidebar.slider("平均垂直風切 (kt)", 0.0, 30.0, 10.0, 1.0)
mean_humid = st.sidebar.slider("平均中低層濕度 (%)", 50.0, 100.0, 75.0, 1.0)
mean_lat = st.sidebar.slider("平均緯度 (Latitude, °)", 0.0, 40.0, 15.0, 1.0)
n_sims = st.sidebar.number_input("模擬次數", min_value=1000, max_value=50000, value=10000, step=1000)

# ================= 2. 核心模擬邏輯 =================
def run_simulation(sst_m, shear_m, humid_m, lat_m, n):
    np.random.seed(42) # 固定亂數種子讓結果穩定
    
    # 產生常態分佈的樣本
    sst = np.random.normal(sst_m, 1.0, n)
    shear = np.random.normal(shear_m, 5.0, n)
    humid = np.random.normal(humid_m, 8.0, n)
    lat = np.random.normal(lat_m, 3.0, n)
    
    # 限制合理範圍
    shear = np.clip(shear, 0, None)
    humid = np.clip(humid, 0, 100)
    lat = np.clip(lat, 0, 90)
    
    # 科氏力因子 (5~25度最容易成颱，赤道與高緯度不利)
    lat_factor = np.where((lat > 5) & (lat < 25), 1.0, 
                 np.where(lat <= 5, lat / 5.0, np.maximum(0, 1 - (lat - 25) / 10.0)))
    
    # 計算 Z 值 (自定義公式)
    z = (0.8 * sst) + (0.1 * humid) - (0.2 * shear) - 25
    z = z * lat_factor # 加入緯度懲罰
    
    # 轉換為機率
    prob = 1 / (1 + np.exp(-z))
    
    # 判定是否成颱
    is_typhoon = (np.random.random(n) < prob).astype(int)
    
    return pd.DataFrame({
        'SST': sst, 'Shear': shear, 'Humidity': humid, 
        'Latitude': lat, 'Probability': prob, 'Is_Typhoon': is_typhoon
    })

df = run_simulation(mean_sst, mean_shear, mean_humid, mean_lat, n_sims)
typhoon_count = df['Is_Typhoon'].sum()
typhoon_rate = typhoon_count / n_sims * 100

# ================= 3. Dashboard 數據顯示 =================
# 最上方大數據指標
col1, col2, col3 = st.columns(3)
col1.metric("總模擬次數", f"{n_sims:,}")
col2.metric("生成颱風數", f"{typhoon_count:,}")
col3.metric("整體成颱率", f"{typhoon_rate:.2f} %")

st.divider()

# ================= 4. 繪製多圖表 =================
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 圖 1：海溫 vs 風切 散佈圖
df_sample = df.sample(min(2000, n_sims)) # 抽樣畫圖才不會卡
sns.scatterplot(data=df_sample, x='SST', y='Shear', hue='Is_Typhoon', 
                palette={0: 'gray', 1: 'red'}, alpha=0.5, ax=axes[0])
axes[0].set_title('海溫 vs 垂直風切')
axes[0].axvline(26.5, color='green', linestyle='--', alpha=0.5) # 26.5度輔助線

# 圖 2：緯度分佈圖 (呈現科氏力影響)
sns.histplot(data=df, x='Latitude', hue='Is_Typhoon', multiple="stack", 
             palette={0: 'gray', 1: 'red'}, bins=30, ax=axes[1])
axes[1].set_title('緯度分佈與成颱關係')

# 圖 3：機率密度圖
sns.kdeplot(data=df, x='Probability', hue='Is_Typhoon', 
            fill=True, palette={0: 'gray', 1: 'red'}, ax=axes[2])
axes[2].set_title('模型判定機率分佈')

plt.tight_layout()
st.pyplot(fig)

# 顯示前幾筆原始資料供檢視
st.subheader("模擬資料預覽")
st.dataframe(df.head(10))