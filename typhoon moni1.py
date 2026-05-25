import pygame
import numpy as np
import sys

# ================= 1. 初始化與全域設定 =================
pygame.init()
WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("颱風生成蒙地卡羅模擬器：手動設定 vs 真實歷史")

# 顏色定義
BLACK = (20, 20, 25)
WHITE = (240, 240, 240)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 50)
BLUE = (60, 140, 255)   # 未成颱
RED = (255, 60, 60)     # 成颱
GREEN = (50, 220, 100)  # 輔助線與提示
YELLOW = (255, 200, 50)

# 字體設定 (Windows 優先使用微軟正黑體，Mac/Linux 會自動降級尋找可用字體)
try:
    font_title = pygame.font.SysFont("Microsoft JhengHei", 28, bold=True)
    font_md = pygame.font.SysFont("Microsoft JhengHei", 20)
    font_sm = pygame.font.SysFont("Arial", 16)
except:
    font_title = pygame.font.Font(None, 36)
    font_md = pygame.font.Font(None, 28)
    font_sm = pygame.font.Font(None, 20)

# ================= 2. 變數範圍與物理門檻 =================
SST_MIN, SST_MAX = 25.0, 30.0
SHEAR_MIN, SHEAR_MAX = 5.0, 30.0
HUMID_MIN, HUMID_MAX = 50.0, 100.0

# 成颱門檻
THRES_SST = 26.5
THRES_SHEAR = 20.0
THRES_HUMID = 70.0

# 雜訊標準差
STD_SST, STD_SHEAR, STD_HUMID = 0.6, 3.0, 5.0

# ================= 3. 資料庫設定 =================
historical_db = {
    pygame.K_1: {"year": 2001, "name": "納莉 (Nari)", "sst": 28.5, "shear": 12.0, "humid": 75.0},
    pygame.K_2: {"year": 2003, "name": "梅米 (Maemi)", "sst": 29.5, "shear": 8.0, "humid": 78.0},
    pygame.K_3: {"year": 2009, "name": "莫拉克 (Morakot)", "sst": 29.0, "shear": 15.0, "humid": 80.0},
    pygame.K_4: {"year": 2013, "name": "海燕 (Haiyan)", "sst": 29.8, "shear": 6.0, "humid": 76.0},
    pygame.K_5: {"year": 2015, "name": "蘇迪勒 (Soudelor)", "sst": 29.2, "shear": 10.0, "humid": 74.0},
    pygame.K_6: {"year": 2020, "name": "天鵝 (Goni)", "sst": 29.4, "shear": 8.0, "humid": 73.0},
    pygame.K_7: {"year": 2024, "name": "凱米 (Gaemi)", "sst": 28.8, "shear": 10.0, "humid": 79.0}
}

# 初始狀態
sim_state = {"sst": 26.0, "shear": 22.0, "humid": 60.0}
hist_key = pygame.K_7 # 預設顯示凱米

# 暫存運算結果的列表
points_sim = []
points_hist = []
prob_sim = 0.0
prob_hist = 0.0

# ================= 4. 核心運算函數 =================
def map_pixel(val, min_val, max_val, min_px, max_px):
    """將數值轉換為螢幕上的像素座標"""
    return int((val - min_val) / (max_val - min_val) * (max_px - min_px) + min_px)

def run_simulation(mean_sst, mean_shear, mean_humid, n=10000):
    """執行 10000 次蒙地卡羅抽樣，回傳點陣列與機率"""
    points = []
    formed_count = 0
    
    for _ in range(n):
        s = np.clip(np.random.normal(mean_sst, STD_SST), SST_MIN, SST_MAX)
        sh = np.clip(np.random.normal(mean_shear, STD_SHEAR), SHEAR_MIN, SHEAR_MAX)
        h = np.clip(np.random.normal(mean_humid, STD_HUMID), HUMID_MIN, HUMID_MAX)
        
        is_formed = (s > THRES_SST) and (sh < THRES_SHEAR) and (h > THRES_HUMID)
        if is_formed:
            formed_count += 1
            
        points.append({"sst": s, "shear": sh, "formed": is_formed})
        
    return points, (formed_count / n) * 100

def update_data():
    """重新計算兩邊的數據"""
    global points_sim, prob_sim, points_hist, prob_hist
    points_sim, prob_sim = run_simulation(sim_state["sst"], sim_state["shear"], sim_state["humid"])
    
    hd = historical_db[hist_key]
    points_hist, prob_hist = run_simulation(hd["sst"], hd["shear"], hd["humid"])

# 啟動時先算一次
update_data()

# ================= 5. 主迴圈 =================
clock = pygame.time.Clock()
running = True

# 版面邊界設定
UI_HEIGHT = 160
PLOT_TOP = UI_HEIGHT + 20
PLOT_BOTTOM = HEIGHT - 40
LEFT_MID = WIDTH // 2

while running:
    screen.fill(BLACK)
    
    # ---------------- 事件監聽 ----------------
    need_update = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # 切換歷史資料 (1~7)
            if event.key in historical_db:
                hist_key = event.key
                need_update = True
                
            # 手動調整左側參數 (WASD QE)
            if event.key == pygame.K_d: 
                sim_state["sst"] = min(SST_MAX, sim_state["sst"] + 0.5); need_update = True
            if event.key == pygame.K_a: 
                sim_state["sst"] = max(SST_MIN, sim_state["sst"] - 0.5); need_update = True
            if event.key == pygame.K_w: 
                sim_state["shear"] = min(SHEAR_MAX, sim_state["shear"] + 1.0); need_update = True
            if event.key == pygame.K_s: 
                sim_state["shear"] = max(SHEAR_MIN, sim_state["shear"] - 1.0); need_update = True
            if event.key == pygame.K_e: 
                sim_state["humid"] = min(HUMID_MAX, sim_state["humid"] + 2.0); need_update = True
            if event.key == pygame.K_q: 
                sim_state["humid"] = max(HUMID_MIN, sim_state["humid"] - 2.0); need_update = True
            
            # 按下空白鍵強制重新抽樣
            if event.key == pygame.K_SPACE:
                need_update = True

    if need_update:
        update_data()

    # ---------------- 繪製散佈圖 (1000個點) ----------------
    # 繪製左側 (手動模擬)
    for p in points_sim:
        x = map_pixel(p["sst"], SST_MIN, SST_MAX, 60, LEFT_MID - 40)
        y = map_pixel(p["shear"], SHEAR_MIN, SHEAR_MAX, PLOT_BOTTOM, PLOT_TOP)
        color = RED if p["formed"] else BLUE
        # 畫半透明小圓點 (Pygame 不支援直接畫帶 alpha 的圓，改用 Surface 或直接畫小矩形/實心圓)
        pygame.draw.circle(screen, color, (x, y), 3)

    # 繪製右側 (歷史數據)
    for p in points_hist:
        x = map_pixel(p["sst"], SST_MIN, SST_MAX, LEFT_MID + 40, WIDTH - 40)
        y = map_pixel(p["shear"], SHEAR_MIN, SHEAR_MAX, PLOT_BOTTOM, PLOT_TOP)
        color = RED if p["formed"] else BLUE
        pygame.draw.circle(screen, color, (x, y), 3)

    # ---------------- 繪製圖表框架與輔助線 ----------------
    pygame.draw.line(screen, DARK_GRAY, (LEFT_MID, UI_HEIGHT), (LEFT_MID, HEIGHT), 2) # 中央分隔線
    
    for offset in [0, LEFT_MID]:
        # X軸與Y軸線
        px_left = 40 + offset
        px_right = (LEFT_MID - 20) + offset
        pygame.draw.line(screen, GRAY, (px_left, PLOT_BOTTOM), (px_right, PLOT_BOTTOM), 2) # X軸
        pygame.draw.line(screen, GRAY, (px_left + 20, PLOT_TOP), (px_left + 20, PLOT_BOTTOM), 2) # Y軸
        
        # 門檻十字輔助線 (SST=26.5, Shear=20)
        sst_line_x = map_pixel(THRES_SST, SST_MIN, SST_MAX, px_left + 20, px_right)
        shear_line_y = map_pixel(THRES_SHEAR, SHEAR_MIN, SHEAR_MAX, PLOT_BOTTOM, PLOT_TOP)
        pygame.draw.line(screen, GREEN, (sst_line_x, PLOT_TOP), (sst_line_x, PLOT_BOTTOM), 1)
        pygame.draw.line(screen, GREEN, (px_left + 20, shear_line_y), (px_right, shear_line_y), 1)

        # 標籤
        screen.blit(font_sm.render(f"25°C", True, GRAY), (px_left + 15, PLOT_BOTTOM + 5))
        screen.blit(font_sm.render(f"30°C", True, GRAY), (px_right - 20, PLOT_BOTTOM + 5))
        screen.blit(font_sm.render(f"5 kt", True, GRAY), (px_left - 10, PLOT_BOTTOM - 10))
        screen.blit(font_sm.render(f"25 kt", True, GRAY), (px_left - 15, PLOT_TOP))

    # ---------------- 繪製上方 UI 資訊面板 ----------------
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, UI_HEIGHT))
    pygame.draw.line(screen, WHITE, (0, UI_HEIGHT), (WIDTH, UI_HEIGHT), 2)
    
    # [左側 UI]
    screen.blit(font_title.render("手動環境測試區 (Manual Test)", True, WHITE), (40, 15))
    screen.blit(font_title.render(f"成颱機率: {prob_sim:.1f}%", True, RED), (40, 55))
    
    screen.blit(font_md.render(f"[A/D] 海溫 (SST): {sim_state['sst']:.1f} °C", True, YELLOW), (40, 95))
    screen.blit(font_md.render(f"[W/S] 風切 (Shear): {sim_state['shear']:.1f} kt", True, YELLOW), (40, 125))
    screen.blit(font_md.render(f"[Q/E] 濕度 (Humid): {sim_state['humid']:.1f} %", True, YELLOW), (280, 95))
    screen.blit(font_sm.render(f" (Space) re-sample", True, GREEN), (280, 130))

    # [右側 UI]
    hd = historical_db[hist_key]
    screen.blit(font_title.render(f"真實歷史回測: {hd['year']} {hd['name']}", True, WHITE), (LEFT_MID + 40, 15))
    screen.blit(font_title.render(f"成颱機率: {prob_hist:.1f}%", True, RED), (LEFT_MID + 40, 55))
    
    screen.blit(font_md.render(f"海溫: {hd['sst']} °C", True, WHITE), (LEFT_MID + 40, 95))
    screen.blit(font_md.render(f"風切: {hd['shear']} kt", True, WHITE), (LEFT_MID + 40, 125))
    screen.blit(font_md.render(f"濕度: {hd['humid']} %", True, WHITE), (LEFT_MID + 220, 95))
    screen.blit(font_sm.render(f"press [1]~[7] switch to different historical typhoons", True, GREEN), (LEFT_MID + 220, 130))

    pygame.display.flip()
    clock.tick(60) # 限制偵數避免過度耗電

pygame.quit()
sys.exit()