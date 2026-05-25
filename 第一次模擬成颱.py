import random
import math

# ----------- 參數設定 -----------
N = 10000  # 模擬次數

# ----------- 標準化函數 -----------
def normalize(T, W, H):
    T_p = (T - 25) / 6      # 25~31 -> 0~1
    W_p = W / 20            # 0~20 -> 0~1
    H_p = (H - 50) / 50     # 50~100 -> 0~1
    return T_p, W_p, H_p

# ----------- 機率公式（Logistic）-----------
def calc_probability(T_p, W_p, H_p):
    x = 0.8*T_p - 0.6*W_p + 0.4*H_p - 1
    P = 1 / (1 + math.exp(-x))
    return P

# ----------- 主模擬 -----------
typhoon_count = 0

for _ in range(N):
    # 1️⃣ 隨機產生環境
    T = random.uniform(25, 31)   # °C
    W = random.uniform(0, 20)    # m/s
    H = random.uniform(50, 100)  # %

    # 2️⃣ 標準化
    T_p, W_p, H_p = normalize(T, W, H)

    # 3️⃣ 算機率
    P = calc_probability(T_p, W_p, H_p)

    # 4️⃣ 隨機決定結果
    r = random.random()
    if r < P:
        typhoon_count += 1

# ----------- 結果 -----------
print("模擬次數:", N)
print("成颱次數:", typhoon_count)
print("成颱機率:", typhoon_count / N)