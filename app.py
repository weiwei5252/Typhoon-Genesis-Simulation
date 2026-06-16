import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="Typhoon Genesis Simulator", layout="wide")
st.title("🌀 Typhoon Genesis Dynamics: Monte Carlo Simulation vs. ERA5 Observations")

# ================= 1. 狀態記憶與連動引擎 (UI 靈魂) =================
default_vals = {'sst': 26.5, 'humid': 70.0, 'shear': 20.0, 'lat': 5.0, 'pres': 1005.0}
for key, val in default_vals.items():
    if key not in st.session_state:
        st.session_state[key] = val
    if f"{key}_slider" not in st.session_state:
        st.session_state[f"{key}_slider"] = val
    if f"{key}_input" not in st.session_state:
        st.session_state[f"{key}_input"] = val
    prev_key = f"prev_{key}"
    if prev_key not in st.session_state:
        st.session_state[prev_key] = val

# 核心魔法：根據「開關」決定要不要牽一髮動全身
def sync_vars(changed_var, widget_type):
    new_val = st.session_state[f"{changed_var}_{widget_type}"]
    old_val = st.session_state[f"prev_{changed_var}"]
    delta = new_val - old_val 

    if delta == 0: return

    # 1. 先更新被你拉動的那個主變數
    st.session_state[changed_var] = new_val

    # 2. 判斷上帝開關：如果「連動模式」有被打開，才去影響別人
    if st.session_state.get('sync_enabled', True):
        if changed_var == 'lat':
            st.session_state.humid = float(np.clip(st.session_state.humid + (delta * 0.8), 40.0, 100.0))
            st.session_state.sst = float(np.clip(st.session_state.sst - (delta * 0.15), 25.0, 35.0))
            st.session_state.pres = float(np.clip(st.session_state.pres - (delta * 0.2), 980.0, 1030.0))
            
        elif changed_var == 'sst':
            st.session_state.pres = float(np.clip(st.session_state.pres - (delta * 2.0), 980.0, 1030.0))
            st.session_state.shear = float(np.clip(st.session_state.shear - (delta * 1.2), 5.0, 30.0))
            st.session_state.humid = float(np.clip(st.session_state.humid - (delta * 1.5), 40.0, 100.0))
            
        elif changed_var == 'shear':
            st.session_state.pres = float(np.clip(st.session_state.pres + (delta * 0.5), 980.0, 1030.0))
            st.session_state.humid = float(np.clip(st.session_state.humid + (delta * 0.5), 40.0, 100.0))
            
        elif changed_var == 'humid':
            st.session_state.pres = float(np.clip(st.session_state.pres - (delta * 0.4), 980.0, 1030.0))
            st.session_state.lat = float(np.clip(st.session_state.lat + (delta * 0.1), 0.0, 30.0))
            
        elif changed_var == 'pres':
            st.session_state.humid = float(np.clip(st.session_state.humid - (delta * 0.8), 40.0, 100.0))
            st.session_state.sst = float(np.clip(st.session_state.sst - (delta * 0.1), 25.0, 35.0))

    # 3. 把最新的數值塞回所有滑桿與輸入框 (就算沒開連動，也要確保左右滑桿輸入框同步)
    for key in default_vals.keys():
        st.session_state[f"{key}_slider"] = st.session_state[key]
        st.session_state[f"{key}_input"] = st.session_state[key]
        st.session_state[f"prev_{key}"] = st.session_state[key]


# ================= 2. 側邊欄 UI =================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3093/3093390.png", width=100)
st.sidebar.title("系統控制中心")

# 🌟 上帝開關 (Toggle)
st.sidebar.markdown("### 實驗模式切換")
st.sidebar.toggle(
    "🔗 啟用大氣變數連動 (Butterfly Effect)", 
    value=True, 
    key="sync_enabled",
    help="【共變異物理引擎】開啟時，調整任一變數將依據 ERA5 歷史相關係數牽動其他變數（模擬真實氣候）。關閉時，可獨立測試單一變數影響（控制變因實驗）。"
)
st.sidebar.markdown("---")
   
with st.sidebar.expander("蒙地卡羅抽樣設定", expanded=True):
    # 樣本數說明
    n_sims = st.slider("隨機生成環境樣本數", 100, 10000, 5000, step=100,
              help="決定蒙地卡羅模擬要生成多少個虛擬環境擾動。樣本數越大，散佈圖分佈越趨近真實大氣統計規律。")

with st.sidebar.expander("熱力學門檻 (Thermodynamic)", expanded=True):
    col1, col2 = st.columns([3, 2]) 
    with col1:
        st.slider("最低海溫門檻 (°C)", 25.0, 35.0, key="sst_slider", on_change=sync_vars, args=('sst', 'slider'),
                  help="【熱力學發動機】現實中低於 26.5°C 極難成颱。本模型已針對低溫設定「一票否決」物理死線。調整此項將引發濕度與氣壓的連鎖反應。")
    with col2:
        st.number_input("SST Input", 25.0, 35.0, step=0.1, key="sst_input", on_change=sync_vars, args=('sst', 'input'), label_visibility="collapsed")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.slider("最低相對濕度 (%)", 40.0, 100.0, key="humid_slider", on_change=sync_vars, args=('humid', 'slider'),
                  help="中低層大氣水氣飽和度。過於乾燥會導致乾空氣逸入，破壞颱風對流結構。在真實數據中與氣壓呈現高度負相關 (-0.43)。")
    with col2:
        st.number_input("Humid Input", 40.0, 100.0, step=1.0, key="humid_input", on_change=sync_vars, args=('humid', 'input'), label_visibility="collapsed")

with st.sidebar.expander("動力學門檻 (Kinematic)", expanded=True):
    col1, col2 = st.columns([3, 2])
    with col1:
        st.slider("最大垂直風切 (kt)", 5.0, 30.0, key="shear_slider", on_change=sync_vars, args=('shear', 'slider'),
                  help="【颱風最大殺手】高低空風速差異。過大會直接撕裂氣旋暖心結構。本模型對此變數極度敏感（機器學習權重佔比高達 44.5%）。")
    with col2:
        st.number_input("Shear Input", 5.0, 30.0, step=1.0, key="shear_input", on_change=sync_vars, args=('shear', 'input'), label_visibility="collapsed")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.slider("最低生成緯度 (°N)", 0.0, 30.0, key="lat_slider", on_change=sync_vars, args=('lat', 'slider'),
                  help="科氏力來源與氣候區位。調整此數值，系統將自動模擬該緯度真實應有的海溫下降與風切增強（緯度越高，環境越惡劣）。")
    with col2:
        st.number_input("Lat Input", 0.0, 30.0, step=0.1, key="lat_input", on_change=sync_vars, args=('lat', 'input'), label_visibility="collapsed")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.slider("最高海平面氣壓 (hPa)", 980.0, 1030.0, key="pres_slider", on_change=sync_vars, args=('pres', 'slider'),
                  help="反映熱帶擾動的初始強度。氣壓數值越低，代表中心對流越旺盛，越容易吸引周圍水氣輻合。")
    with col2:
        st.number_input("Pres Input", 980.0, 1030.0, step=1.0, key="pres_input", on_change=sync_vars, args=('pres', 'input'), label_visibility="collapsed")

st.sidebar.markdown("---")
# ================= 3. 核心機率引擎 =================
# ================= 3. 核心機率引擎 =================
# ================= 3. 核心機率引擎 =================
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
    
    # 🌍 第一刀：收縮變異數，讓局部天氣更穩定、更集中
    s_arr = np.random.normal(t_s, 1.0, n)       # std 從 1.5 降到 1.0
    sh_arr = np.random.normal(t_sh, 3.5, n)     # std 從 5.0 降到 3.5
    h_arr = np.random.normal(t_h, 5.0, n)       # std 從 8.0 降到 5.0
    lat_arr = np.random.normal(t_l, 4.0, n)
    lon_arr = np.random.normal(135.0, 15.0, n) 
    pres_arr = np.random.normal(t_p, 5.0, n)
    year_arr = np.random.choice(range(2006, 2027), n)

    h_arr = np.clip(h_arr, 0, 100)
    
    is_inland_china = (lon_arr < 120) & (lat_arr > 22)
    is_indochina = (lon_arr < 109) & (lat_arr > 8) & (lat_arr < 22)
    is_ocean = ~(is_inland_china | is_indochina)
    # ==========================================
    # 🏔️ 新增：地形破壞機制 (Topographic Penalty)
    # 定義高山島嶼的經緯度結界
    is_taiwan = (lon_arr >= 119.5) & (lon_arr <= 122.5) & (lat_arr >= 21.5) & (lat_arr <= 25.5)
    is_philippines = (lon_arr >= 117.0) & (lon_arr <= 126.0) & (lat_arr >= 5.0) & (lat_arr <= 19.0)

    # 預設大洋上的地形存活率為 1.0 (無干擾)
    topo_survival = np.ones(n)
    # 撞到台灣中央山脈，結構被嚴重破壞，存活率剩 10%
    topo_survival[is_taiwan] = 0.1       
    # 撞到菲律賓群島，結構受損，存活率剩 30%
    topo_survival[is_philippines] = 0.3  
    # ==========================================
    def sigmoid(x, threshold, k=1.0, reverse=False):
        if reverse:
            return 1 / (1 + np.exp(k * (x - threshold)))
        else:
            return 1 / (1 + np.exp(-k * (x - threshold)))

    # ⚖️ 大自然鐵律 (不隨拉桿改變)
    NATURE_SST = 26.5
    NATURE_SHEAR = 20.0
    NATURE_HUMID = 70.0
    NATURE_LAT = 5.0
    NATURE_PRES = 1005.0

    # 📉 第二刀：提高 k 值，讓評分標準變得極度嚴苛 (沒達標就直接給低分)
    prob_sst = sigmoid(s_arr, NATURE_SST, k=2.0)              # k 從 1.5 提升到 2.0
    prob_shear = sigmoid(sh_arr, NATURE_SHEAR, k=0.8, reverse=True) # k 從 0.3 提升到 0.8
    prob_humid = sigmoid(h_arr, NATURE_HUMID, k=0.3)            # k 從 0.15 提升到 0.3
    prob_lat = sigmoid(lat_arr, NATURE_LAT, k=0.4)
    prob_pres = sigmoid(pres_arr, NATURE_PRES, k=0.5, reverse=True) # k 從 0.3 提升到 0.5

    # ==========================================
    #  第一層：動態機器學習潛勢指數 (Dynamic ML GPI)
    # 取代原本寫死的權重，讓 Random Forest 直接對生成的虛擬環境打分數
    
    # 1. 建立輕量化訓練集 (真實觀測 = 1, 背景雜訊 = 0)
    if not df_real.empty:
        features = ['SST', 'Shear', 'Humidity', 'Pressure', 'Lat']
        df_valid = df_real.dropna(subset=features)
        X_real_train = df_valid[features]
        y_real_train = np.ones(len(X_real_train))
        
        bg_n = len(X_real_train)
        X_bg_train = pd.DataFrame({
            'SST': np.random.normal(26.0, 1.5, bg_n),
            'Shear': np.random.normal(25.0, 5.0, bg_n),
            'Humidity': np.random.normal(60.0, 10.0, bg_n),
            'Pressure': np.random.normal(1010.0, 8.0, bg_n),
            'Lat': np.random.normal(15.0, 5.0, bg_n)
        })
        y_bg_train = np.zeros(bg_n)
        
        X_train = pd.concat([X_real_train, X_bg_train])
        y_train = np.concatenate([y_real_train, y_bg_train])
        
        # 2. 訓練輕量化決策樹模型
        rf_core = RandomForestClassifier(n_estimators=30, random_state=42)
        rf_core.fit(X_train, y_train)
        
        # 3. 
        df_sim_pool = pd.DataFrame({
            'SST': s_arr, 'Shear': sh_arr, 'Humidity': h_arr, 
            'Pressure': pres_arr, 'Lat': lat_arr
        })
        # 取出判定為颱風(Class 1)的機率，當作新的 gpi
        gpi = rf_core.predict_proba(df_sim_pool)[:, 1] 
    else:
        gpi = np.zeros(n) # 防呆：如果沒資料就給 0
    # ==========================================
    # ==========================================
    # 🛑 第二層：柔性指數懲罰 (Soft Veto) - 貫徹「隨機性」核心精神
    # 取消非黑即白的 0/1 死線。未達標的環境不再直接判死刑，
    # 而是給予「指數級」的機率衰減，保留大自然極端異常的長尾機率。
    
    # 海溫若低於 26.0，每低 1 度，存活率呈指數暴跌 (例如 25.0 度只剩 5% 存活加權)
    veto_sst = np.where(s_arr >= 26.0, 1.0, np.exp(3.0 * (s_arr - 26.0))) 
    
    # 風切若大於 22.0，每高 1 kt，存活率呈指數暴跌
    veto_shear = np.where(sh_arr <= 22.0, 1.0, np.exp(-0.5 * (sh_arr - 22.0)))
    
    # 濕度若低於 55.0，每低 1%，存活率呈指數暴跌
    veto_humid = np.where(h_arr >= 55.0, 1.0, np.exp(0.2 * (h_arr - 55.0)))
    # ==========================================
    
    # 綜合生存機率 = 潛勢指數 * 否決遮罩 * 陸地遮罩 * 地形破壞率
    combined_prob = gpi * veto_sst * veto_shear * veto_humid * is_ocean * topo_survival
    
    random_dice = np.random.random(n)
    is_formed = combined_prob > random_dice
    
    df_sim = pd.DataFrame({
        'SST': s_arr[is_formed], 'Shear': sh_arr[is_formed],
        'Humidity': h_arr[is_formed], 'Lat': lat_arr[is_formed],
        'Lon': lon_arr[is_formed], 'Year': year_arr[is_formed],
        'Pressure': pres_arr[is_formed], 'Type': 'Monte Carlo Simulation'
    })
    return df_real, df_sim, n

df_real, df_sim, total_sampled = get_data(
    n_sims, 
    st.session_state.sst, 
    st.session_state.shear, 
    st.session_state.humid, 
    st.session_state.lat, 
    st.session_state.pres
)
df_all = pd.concat([df_real, df_sim], ignore_index=True) if not df_real.empty else df_sim

# (前面 get_data 的呼叫保持不變)
df_real, df_sim, total_sampled = get_data(
    n_sims, 
    st.session_state.sst, 
    st.session_state.shear, 
    st.session_state.humid, 
    st.session_state.lat, 
    st.session_state.pres
)
df_all = pd.concat([df_real, df_sim], ignore_index=True) if not df_real.empty else df_sim

# ⬇️ 從這裡開始，替換成下面這份乾淨的代碼 ⬇️

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
    # 【完美保留】隨著拉桿連動的門檻輔助線
    fig1.add_vline(x=st.session_state.sst, line_dash="dot", line_color="gray")
    fig1.add_hline(y=st.session_state.shear, line_dash="dot", line_color="gray")
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
