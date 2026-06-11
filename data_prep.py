import pandas as pd
import xarray as xr
import numpy as np
import glob

def extract_real_data():
    print("1. 從 NOAA 官方伺服器直接下載最新 IBTrACS 軌跡資料...")
    url = 'https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.WP.list.v04r01.csv'
    
    try:
        df_ib = pd.read_csv(url, skiprows=[1], low_memory=False, na_values=[' ', ''])
    except Exception as e:
        print(f"網路讀取失敗: {e}")
        return

    print("資料下載成功！開始清洗...")
    df_ib['ISO_TIME'] = pd.to_datetime(df_ib['ISO_TIME'])
    df_ib['USA_WIND'] = pd.to_numeric(df_ib['USA_WIND'], errors='coerce')
    df_ib['LAT'] = pd.to_numeric(df_ib['LAT'], errors='coerce')
    df_ib['LON'] = pd.to_numeric(df_ib['LON'], errors='coerce')
    
    df_storm = df_ib[(df_ib['SEASON'] >= 2006) & (df_ib['USA_WIND'] >= 34)]
    genesis_points = df_storm.groupby('SID').first().reset_index()
    print(f"Found {len(genesis_points)} real typhoon genesis points.")

    print("2. Loading ERA5 NetCDF files...")
    nc_files = glob.glob('*era5.nc')
    if not nc_files:
        print("錯誤：找不到 era5.nc 檔案。")
        return
        
    ds = xr.open_mfdataset(nc_files, combine='by_coords')
    results = []
    print("3. Fusing spatial-temporal data...")
    
    genesis_points['LON_ERA5'] = np.where(genesis_points['LON'] < 0, genesis_points['LON'] + 360, genesis_points['LON'])

    error_count = 0
    for _, row in genesis_points.iterrows():
        try:
            # 【破案關鍵 1】：將 time 改成 valid_time
            env = ds.sel(
                valid_time=row['ISO_TIME'], 
                latitude=row['LAT'], 
                longitude=row['LON_ERA5'], 
                method='nearest'
            )
            
            # 【破案關鍵 2】：加入 np.nanmean 吸收 expver 帶來的陣列問題，強制轉為單一數字
            sst = np.nanmean(env['sst'].values) - 273.15
            u10 = np.nanmean(env['u10'].values)
            v10 = np.nanmean(env['v10'].values)
            d2m = np.nanmean(env['d2m'].values) - 273.15
            mslp = np.nanmean(env['msl'].values) / 100
            
            wind_shear = np.sqrt(u10**2 + v10**2)
            e = 6.11 * 10.0 ** (7.5 * d2m / (237.3 + d2m))
            es = 6.11 * 10.0 ** (7.5 * sst / (237.3 + sst))
            rh = (e / es) * 100
            
            results.append({
                'Name': row['NAME'],
                'Year': row['SEASON'],
                'Lat': row['LAT'],
                'SST': float(sst),
                'Shear': float(wind_shear),
                'Humidity': float(rh),
                'Pressure': float(mslp),
                'Type': 'Real Observation'
            })
        except Exception as e:
            error_count += 1
            continue 

    df_final = pd.DataFrame(results)
    df_final.to_csv('real_genesis_data.csv', index=False)
    print(f"Success! Data exported to 'real_genesis_data.csv' ({len(df_final)} records).")
    if error_count > 0:
        print(f"⚠️ 有 {error_count} 筆資料因為超出你下載的網格邊界而跳過。")

if __name__ == "__main__":
    extract_real_data()