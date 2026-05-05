"""Bayesian Beta-Binomial 後驗."""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = ROOT / "output"
PRIMARY = "#1a1a2e"
ACCENT = "#e63946"
NAVY_LIGHT = "#94a3b8"

st.set_page_config(page_title="Bayesian · Cookie Cats", page_icon="🔮", layout="wide")
st.title("🔮 Bayesian Beta-Binomial 分析")
st.caption("Jeffreys prior · 200,000 後驗抽樣 · 直接給「比較好的機率」")

@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")

post = load("posterior_samples.csv")
agg = load("aggregates.csv")
g30 = agg[agg["version"] == "gate_30"].iloc[0]
g40 = agg[agg["version"] == "gate_40"].iloc[0]

c1, c2 = st.columns(2)

for col, metric, title in zip([c1, c2],
                               ["retention_1", "retention_7"],
                               ["1 日留存", "7 日留存"]):
    p30 = post[f"{metric}_p30"].values
    p40 = post[f"{metric}_p40"].values
    diff = post[f"{metric}_diff_pp"].values
    p_better = (diff > 0).mean() * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=p30, nbinsx=70, marker_color=NAVY_LIGHT,
        opacity=0.6, name="gate_30 (對照)", histnorm="probability density",
    ))
    fig.add_trace(go.Histogram(
        x=p40, nbinsx=70, marker_color=ACCENT,
        opacity=0.6, name="gate_40 (實驗)", histnorm="probability density",
    ))
    fig.update_layout(
        height=380, plot_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="留存率 (%)",
        yaxis_title="後驗密度",
        legend=dict(orientation="h", y=-0.15),
        title=f"P(gate_40 better) = {p_better:.2f}%",
    )
    col.markdown(f"**{title}**")
    col.markdown(f"95% Credible Interval: [{np.percentile(diff, 2.5):+.2f}, "
                 f"{np.percentile(diff, 97.5):+.2f}] pp")
    col.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🎯 直接的機率語言")

c1, c2 = st.columns(2)
for col, metric, title in zip([c1, c2], ["retention_1", "retention_7"],
                               ["Day 1 retention", "Day 7 retention"]):
    diff = post[f"{metric}_diff_pp"].values
    p_better = (diff > 0).mean() * 100
    p_worse = (diff < 0).mean() * 100
    p_lift_1pp = (diff > 1).mean() * 100
    p_loss_1pp = (diff < -1).mean() * 100

    col.markdown(f"**{title}**")
    col.markdown(f"""
    - P(gate_40 比較好) = **{p_better:.2f}%**
    - P(gate_40 比較差) = **{p_worse:.2f}%**
    - P(gate_40 提升超過 1pp) = {p_lift_1pp:.2f}%
    - P(gate_40 損失超過 1pp) = {p_loss_1pp:.2f}%
    """)

st.divider()

st.subheader("🧠 為什麼選 Bayesian?")

st.markdown(
    """
    **Frequentist 的死穴**:p-value 是「假設沒差異的條件下,看到這個或更極端結果的機率」。
    跟業務需要的「gate_40 比較好的機率」**完全是兩回事**。
    PM 講「p=0.001」業務聽不懂,講「P(better) = 0.001」業務馬上就懂。

    **Bayesian 的優點**
    - 直接給「假設為真的機率」(posterior),語言對齊業務直覺
    - 樣本小也能用(只是不確定性會很大)
    - 可以加入歷史先驗(prior),讓結果更精準

    **Jeffreys prior `Beta(0.5, 0.5)` 是什麼**
    - 一個「弱資訊」prior,對未知比例幾乎不假設任何事
    - 跟 Frequentist 在大樣本下會收斂到相同結果
    - 適合「我沒有可靠歷史資料」的情境
    """
)

st.divider()

st.subheader("🔬 互動:換不同 prior 結果會怎麼變?")

st.markdown(
    "如果你**強烈相信** gate_40 應該更好(例如業務 leader 一直推這個改動),"
    "用 informative prior 看對結果的影響。"
)

c1, c2 = st.columns(2)
with c1:
    prior_belief = st.selectbox(
        "Prior 信念",
        ["Jeffreys (弱資訊)", "Uniform Beta(1,1)", "Beta(20, 80) — 預期 D7 ~20%",
         "Beta(50, 50) — 強烈相信 50%", "Beta(1, 99) — 強烈相信 ~1%"],
    )
with c2:
    n_users = st.slider("假設樣本大小 (每組)", 100, 50_000, int(g30["n_users"]), step=100)

priors = {
    "Jeffreys (弱資訊)": (0.5, 0.5),
    "Uniform Beta(1,1)": (1, 1),
    "Beta(20, 80) — 預期 D7 ~20%": (20, 80),
    "Beta(50, 50) — 強烈相信 50%": (50, 50),
    "Beta(1, 99) — 強烈相信 ~1%": (1, 99),
}
a0, b0 = priors[prior_belief]
# 7-day retention 為例
p_obs_30 = g30["retention_7_rate"]
p_obs_40 = g40["retention_7_rate"]
s30 = int(p_obs_30 * n_users)
s40 = int(p_obs_40 * n_users)

rng = np.random.default_rng(42)
post30 = rng.beta(a0 + s30, b0 + (n_users - s30), 50_000)
post40 = rng.beta(a0 + s40, b0 + (n_users - s40), 50_000)
diff = post40 - post30
p_better_new = (diff > 0).mean() * 100

st.metric(f"P(gate_40 better) — D7 留存,prior = Beta({a0}, {b0})",
          f"{p_better_new:.2f}%")

if a0 + b0 > 50:
    st.warning(
        "⚠️ Prior 很「自信」(Beta 加總 > 50),對 posterior 影響大。"
        "不確定的時候用弱資訊 prior(Jeffreys)比較保險。"
    )
else:
    st.info("ℹ️ 這是弱資訊 prior,結果跟 Frequentist 會接近。")
