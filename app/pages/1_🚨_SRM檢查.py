"""SRM (Sample Ratio Mismatch) 檢查."""

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = ROOT / "output"
PRIMARY = "#1a1a2e"
ACCENT = "#e63946"
NAVY_LIGHT = "#94a3b8"

st.set_page_config(page_title="SRM 檢查 · Cookie Cats", page_icon="🚨", layout="wide")
st.title("🚨 Sample Ratio Mismatch (SRM) 檢查")
st.caption("業界標準:任何 A/B 測試結果出來,先檢查實驗本身,再看指標")

@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")

agg = load("aggregates.csv")
srm = load("srm.csv").iloc[0]

g30 = agg[agg["version"] == "gate_30"].iloc[0]
g40 = agg[agg["version"] == "gate_40"].iloc[0]
total = int(g30["n_users"] + g40["n_users"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("總樣本", f"{total:,}")
c2.metric("gate_30", f"{int(g30['n_users']):,}", f"{g30['n_users']/total*100:.2f}%")
c3.metric("gate_40", f"{int(g40['n_users']):,}", f"{g40['n_users']/total*100:.2f}%")
c4.metric("Chi-square p", f"{srm['p_value']:.4f}",
          srm["verdict"], delta_color="inverse")

st.divider()

st.subheader("📊 觀察 vs 預期")

obs = [int(g30["n_users"]), int(g40["n_users"])]
exp = [(g30["n_users"]+g40["n_users"])/2] * 2

fig = go.Figure()
fig.add_trace(go.Bar(name="觀察值", x=["gate_30", "gate_40"], y=obs,
                     marker_color=ACCENT,
                     text=[f"{n:,}" for n in obs], textposition="outside"))
fig.add_trace(go.Bar(name="50/50 預期", x=["gate_30", "gate_40"], y=exp,
                     marker_color=NAVY_LIGHT, opacity=0.6,
                     text=[f"{n:,.0f}" for n in exp], textposition="outside"))
fig.update_layout(
    barmode="group", height=400, plot_bgcolor="white",
    margin=dict(l=10, r=10, t=10, b=10),
    yaxis_title="玩家數",
    legend=dict(orientation="h", y=-0.15),
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("🧮 Chi-square Goodness-of-Fit Test")

st.code(f"""H0: 觀察樣本來自 50/50 分配
H1: 樣本比例非 50/50

scipy.stats.chisquare(
    f_obs=[44700, 45489],     # 觀察值
    f_exp=[45094.5, 45094.5], # 50/50 預期
)

→ chi2 = {srm['chi2']:.4f}
→ p-value = {srm['p_value']:.4f}
→ 結論:p < 0.01 → REJECT H0 → SRM violation""", language="python")

st.divider()

if srm["verdict"] == "FAIL":
    st.error(
        f"### ❌ SRM FAIL (p = {srm['p_value']:.4f} < 0.01)\n\n"
        "業界標準(Microsoft, Google, Airbnb):**SRM p-value < 0.01 的實驗結果不該採信**,要先找出 root cause。"
    )
else:
    st.success(f"### ✅ SRM PASS (p = {srm['p_value']:.4f})")

st.subheader("🔍 為什麼這很嚴重?")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        **常見的 SRM 原因**

        - 某種裝置 / 地區 / 版本只進其中一組(造成樣本偏差)
        - Bot 流量沒過濾乾淨(影響某組)
        - 分流邏輯 race condition(早期請求進不到一組)
        - Cookie 過期 / 用戶清 cache 被重新分配
        - 某些用戶使用 ad-blocker 阻擋 SDK
        """
    )
with c2:
    st.markdown(
        """
        **PM 該怎麼做**

        1. 先請工程 debug randomization service / SDK
        2. 結果先別 share 給 leadership(避免根據錯資料下決策)
        3. 若 root cause 是「特定 cohort 被排除」,可考慮做 sub-population 分析
        4. 修好後重跑實驗,並把樣本量加大以彌補
        5. 把這個案例寫進 team 的 experiment review checklist
        """
    )

st.divider()

st.subheader("💡 互動:如果 SRM 修了,要多大樣本才能檢驗 0.5pp 差異?")

target_diff = st.slider("想偵測的 D7 留存差異 (pp)", 0.1, 2.0, 0.5, 0.1)
power = st.slider("Statistical power", 0.5, 0.99, 0.8, 0.01)
alpha = st.slider("Significance level (α)", 0.01, 0.10, 0.05, 0.01)

import numpy as np
from statsmodels.stats.power import zt_ind_solve_power

p_baseline = g30["retention_7_rate"]
p_new = p_baseline - target_diff/100
h = abs(2*np.arcsin(np.sqrt(p_new)) - 2*np.arcsin(np.sqrt(p_baseline)))
n_per_arm = zt_ind_solve_power(effect_size=h, alpha=alpha, power=power, ratio=1.0)

c1, c2, c3 = st.columns(3)
c1.metric("Baseline D7 留存", f"{p_baseline*100:.2f}%")
c2.metric("Cohen's h", f"{h:.4f}")
c3.metric("每組需樣本", f"{int(np.ceil(n_per_arm)):,}",
          f"vs 目前 ~{int(g30['n_users']):,}")

multiplier = n_per_arm / g30["n_users"]
if multiplier > 1.5:
    st.warning(f"💡 重跑時樣本量需要加大 **{multiplier:.1f} 倍**")
else:
    st.success(f"✅ 現有樣本量已足夠(現有是需求的 {1/multiplier:.1f} 倍)")
