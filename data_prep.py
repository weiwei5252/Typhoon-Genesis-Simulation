import pandas as pd
import xarray as xr
import numpy as np
import glob

def extract_real_data():
    print("1. Loading IBTrACS data...")
    # 讀取 IBTrACS 軌跡
    try:
        df_ib = pd.read_csv('ibtracs.WP.list.v04r01.csv', skiprows=[1], low_memory=False)
    except FileNotFoundError:
        print("錯誤：找不到 IBTrACS 檔案，請確認檔名是否為 ibtracs.WP.list.v04r01(1).csv")
        return

    df_ib['ISO_TIME'] = pd.to_datetime(df_ib['ISO_TIME'])
    df_ib['USA_WIND'] = pd.to_numeric(df_ib['USA_WIND'], errors='coerce')
    df_ib['LAT'] = pd.to_numeric(df_ib['LAT'], errors='coerce')
    df_ib['LON'] = pd.to_numeric(df_ib['LON'], errors='coerce')
    
    # 篩選 2020-2026 年，且風速大於等於 34 節的初次成颱點
    df_storm = df_ib[(df_ib['SEASON'] >= 2020) & (df_ib['USA_WIND'] >= 34)]
    genesis_points = df_storm.groupby('SID').first().reset_index()
    print(f"Found {len(genesis_points)} real typhoon genesis points.")

    print("2. Loading ERA5 NetCDF files (This might take a moment)...")
    # 使用萬用字元抓取所有年份的 ERA5 檔案 (2020era5.nc ~ 2026era5.nc)
    nc_files = glob.glob('*era5.nc')
    if not nc_files:
        print("錯誤：找不到任何以 'era5.nc' 結尾的檔案。請確認檔名和路徑。")
        return
    print(f"找到 {len(nc_files)} 個 ERA5 檔案，開始合併...")    
    
    # 使用 open_mfdataset 一次讀取所有檔案
    ds = xr.open_mfdataset(nc_files, combine='by_coords')
    
    results = []
    print("3. Fusing spatial-temporal data...")
    
    # 修正經度範圍：ERA5 可能是 0~360，IBTrACS 是 -180~180
    # 我們將 IBTrACS 的負經度轉換為 0~360 的格式，以防對齊失敗
    genesis_points['LON_ERA5'] = np.where(genesis_points['LON'] < 0, genesis_points['LON'] + 360, genesis_points['LON'])

    for _, row in genesis_points.iterrows():
        try:
            # 根據時間與經緯度，找到最接近的網格點
            env = ds.sel(
                time=row['ISO_TIME'], 
                latitude=row['LAT'], 
                longitude=row['LON_ERA5'], 
                method='nearest'
            )
            
            # 變數萃取 (根據你截圖下載的變數)
            sst = env['sst'].values - 273.15           # 海溫 (K 轉 C)
            u10 = env['u10'].values                    # U 風
            v10 = env['v10'].values                    # V 風
            d2m = env['d2m'].values - 273.15           # 露點溫度 (K 轉 C)
            mslp = env['msl'].values / 100             # 海平面氣壓 (Pa 轉 hPa)
            
            # 專題替代運算：以底層風速梯度作為風切指標
            wind_shear = np.sqrt(u10**2 + v10**2)
            
            # 專題替代運算：以 SST 逼近底層氣溫，套用 Magnus 公式算相對濕度
            e = 6.11 * 10.0 ** (7.5 * d2m / (237.3 + d2m))
            es = 6.11 * 10.0 ** (7.5 * sst / (237.3 + sst))
            rh = (e / es) * 100
            
            results.append({
                'Name': row['NAME'],
                'Year': row['SEASON'],
                'Lat': row['LAT'],          # 緯度代表科氏力
                'SST': float(sst),          # 海溫
                'Shear': float(wind_shear), # 風切
                'Humidity': float(rh),      # 濕度
                'Pressure': float(mslp),    # 氣壓
                'Type': 'Real Observation'
            })
        except Exception as e:
            # print(f"Skipped {row['NAME']} at {row['ISO_TIME']}: {e}")
            continue # 超出下載範圍的點直接跳過

    # 輸出提煉後的微型資料集
    df_final = pd.DataFrame(results)
    df_final.to_csv('real_genesis_data.csv', index=False)
    print(f"Success! Data exported to 'real_genesis_data.csv' ({len(df_final)} records).")

if __name__ == "__main__":
    extract_real_data()