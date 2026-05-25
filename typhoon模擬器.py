import pygame
import numpy as np

# ================= 初始設定 =================
pygame.init()
WIDTH, HEIGHT = 1200, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("蒙地卡羅模擬：可調變數 vs 2000-2024 真實颱風回測")

# 顏色定義
BLACK, WHITE, GRAY = (15, 15, 20), (255, 255, 255), (80, 80, 80)
BLUE, RED, GREEN, YELLOW = (50, 150, 255), (255, 50, 50), (50, 255, 150), (255, 200, 50)

# ================= 變數邊界與雜訊設定 =================
# 依照需求限制範圍
SST_MIN, SST_MAX = 25.0, 30.0
SHEAR_MIN, SHEAR_MAX = 5.0, 25.0
HUMID_MIN, HUMID_MAX = 50.0, 80.0

# 蒙地卡羅常態分佈標準差 (模擬觀測誤差與大氣擾動)
sst_std, shear_std, humid_std = 0.6, 3.0, 5.0

# ================= 資料集 (2000 - 2024) =================
# 左側：可手動調整的「一般熱帶低壓」預設值
sim_sst, sim_shear, sim_humid = 26.0, 22.0, 60.0

# 右側：2000~2024 西北太平洋指標性颱風 (TD時期環境重構數值)
historical_data = {
    pygame.K_1: {"year": 2001, "name": "納莉 (Nari)", "sst": 28.5, "shear": 12.0, "humid": 75.0},
    pygame.K_2: {"year": 2003, "name": "梅米 (Maemi) - 超強颱風", "sst": 29.5, "shear": 8.0, "humid": 78.0},
    pygame.K_3: {"year": 2009, "name": "莫拉克 (Morakot) - 季風槽", "sst": 29.0, "shear": 15.0, "humid": 80.0},
    pygame.K_4: {"year": 2013, "name": "海燕 (Haiyan) - 世紀風暴", "sst": 29.8, "shear": 6.0, "humid": 76.0},
    pygame.K_5: {"year": 2015, "name": "蘇迪勒 (Soudelor)", "sst": 29.2, "shear": 10.0, "humid": 74.0},
    pygame.K_6: {"year": 2016, "name": "莫蘭蒂 (Meranti)", "sst": 29.6, "shear": 7.0, "humid": 77.0},
    pygame.K_7: {"year": 2020, "name": "天鵝 (Goni)", "sst": 29.4, "shear": 8.0, "humid": 73.0},
    pygame.K_8: {"year": 2024, "name": "凱米 (Gaemi)", "sst": 28.8, "shear": 10.0, "humid": 79.0}
}
current_historical = historical_data[pygame.K_8] # 預設顯示最新

# ================= 輔助函數 =================
def map_val(val, min_val, max_val, min_px, max_px):
    return int((val - min_val) / (max_val - min_val) * (max_px - min_px) + min_px)

def check_typhoon(sst, shear, humid):
    # 成颱物理門檻
    return (sst > 26.5) and (shear < 20.0) and (humid > 70.0)

# ================= 主迴圈 =================
clock = pygame.time.Clock()
running = True
stats = {"sim_total": 0, "sim_formed": 0, "real_total": 0, "real_formed": 0}

font_sm = pygame.font.SysFont("Arial", 16)
font_md = pygame.font.SysFont("Arial", 22, bold=True)
font_title = pygame.font.SysFont("Microsoft JhengHei, Arial", 26, bold=True)

while running:
    screen.fill(BLACK)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # 切換歷史資料 (按 1~8)
            if event.key in historical_data:
                current_historical = historical_data[event.key]
                stats["real_total"], stats["real_formed"] = 0, 0
            
            # 手動調整左側參數 (嚴格限制在給定範圍內)
            if event.key == pygame.K_a: sim_sst = max(SST_MIN, sim_sst - 0.5)
            if event.key == pygame.K_d: sim_sst = min(SST_MAX, sim_sst + 0.5)
            if event.key == pygame.K_w: sim_shear = min(SHEAR_MAX, sim_shear + 1.0)
            if event.key == pygame.K_s: sim_shear = max(SHEAR_MIN, sim_shear - 1.0)
            if event.key == pygame.K_q: sim_humid = max(HUMID_MIN, sim_humid - 2.0)
            if event.key == pygame.K_e: sim_humid = min(HUMID_MAX, sim_humid + 2.0)
            
            if event.key in [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_q, pygame.K_e]:
                stats["sim_total"], stats["sim_formed"] = 0, 0

    # 蒙地卡羅抽樣 (每幀 10 次)
    for _ in range(10):
        # 左側抽樣
        s_sst = np.clip(np.random.normal(sim_sst, sst_std), SST_MIN, SST_MAX)
        s_shear = np.clip(np.random.normal(sim_shear, shear_std), SHEAR_MIN, SHEAR_MAX)
        s_humid = np.clip(np.random.normal(sim_humid, humid_std), HUMID_MIN, HUMID_MAX)
        
        is_t_sim = check_typhoon(s_sst, s_shear, s_humid)
        stats["sim_total"] += 1
        if is_t_sim: stats["sim_formed"] += 1
        
        s_x = map_val(s_sst, SST_MIN, SST_MAX, 50, WIDTH//2 - 50)
        s_y = map_val(s_shear, SHEAR_MIN, SHEAR_MAX, HEIGHT - 50, 150)
        pygame.draw.circle(screen, RED if is_t_sim else BLUE, (s_x, s_y), 3, 1 if not is_t_sim else 0)

        # 右側抽樣
        r_sst = np.clip(np.random.normal(current_historical["sst"], sst_std), SST_MIN, SST_MAX)
        r_shear = np.clip(np.random.normal(current_historical["shear"], shear_std), SHEAR_MIN, SHEAR_MAX)
        r_humid = np.clip(np.random.normal(current_historical["humid"], humid_std), HUMID_MIN, HUMID_MAX)
        
        is_t_real = check_typhoon(r_sst, r_shear, r_humid)
        stats["real_total"] += 1
        if is_t_real: stats["real_formed"] += 1
        
        r_x = map_val(r_sst, SST_MIN, SST_MAX, WIDTH//2 + 50, WIDTH - 50)
        r_y = map_val(r_shear, SHEAR_MIN, SHEAR_MAX, HEIGHT - 50, 150)
        pygame.draw.circle(screen, RED if is_t_real else BLUE, (r_x, r_y), 3, 1 if not is_t_real else 0)

    # 繪製 UI 與格線
    pygame.draw.line(screen, GRAY, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 2)
    
    # 門檻十字線
    for offset in [0, WIDTH//2]:
        sst_line_x = map_val(26.5, SST_MIN, SST_MAX, 50 + offset, WIDTH//2 - 50 + offset)
        shear_line_y = map_val(20.0, SHEAR_MIN, SHEAR_MAX, HEIGHT - 50, 150)
        pygame.draw.line(screen, GREEN, (sst_line_x, 150), (sst_line_x, HEIGHT-50), 1)
        pygame.draw.line(screen, GREEN, (50 + offset, shear_line_y), (WIDTH//2 - 50 + offset, shear_line_y), 1)

    pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 130)) # 頂部文字遮罩
    
    # 左側文字
    sim_prob = (stats["sim_formed"] / stats["sim_total"] * 100) if stats["sim_total"] > 0 else 0
    screen.blit(font_title.render("Manual Tropical Depression", True, WHITE), (50, 10))
    screen.blit(font_md.render(f"Prob: {sim_prob:.1f}%", True, RED), (50, 45))
    screen.blit(font_sm.render(f"[A/D] SST: {sim_sst:.1f}°C", True, YELLOW), (50, 75))
    screen.blit(font_sm.render(f"[W/S] Shear: {sim_shear:.1f} kt", True, YELLOW), (200, 75))
    screen.blit(font_sm.render(f"[Q/E] Humid: {sim_humid:.1f}%", True, YELLOW), (350, 75))

    # 右側文字
    real_prob = (stats["real_formed"] / stats["real_total"] * 100) if stats["real_total"] > 0 else 0
    screen.blit(font_title.render(f"{current_historical['year']} {current_historical['name']}", True, WHITE), (WIDTH//2 + 50, 10))
    screen.blit(font_md.render(f"Prob: {real_prob:.1f}%", True, RED), (WIDTH//2 + 50, 45))
    screen.blit(font_sm.render(f"SST: {current_historical['sst']}°C", True, GRAY), (WIDTH//2 + 50, 75))
    screen.blit(font_sm.render(f"Shear: {current_historical['shear']} kt", True, GRAY), (WIDTH//2 + 200, 75))
    screen.blit(font_sm.render(f"Humid: {current_historical['humid']}%", True, GRAY), (WIDTH//2 + 350, 75))
    screen.blit(font_sm.render("Press [1]-[8] to select historical data (2000-2024)", True, GREEN), (WIDTH//2 + 50, 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()