"""Bootstrap 重抽分布."""

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

st.set_page_config(page_title="Bootstrap · Cookie Cats", page_icon="🎲", layout="wide")
st.title("🎲 Bootstrap 重抽分布 (10,000 次)")
st.caption("非參數方法,不假設分布形狀,直接用資料估計差異的不確定性")

@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")

boot = load("bootstrap_samples.csv")

c1, c2 = st.columns(2)

for col, metric, title in zip(
    [c1, c2],
    ["retention_1", "retention_7"],
    ["1 日留存差異", "7 日留存差異"],
):
    diffs = boot[f"{metric}_diff_pp"].values
    mean = diffs.mean()
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
    p_worse = (diffs < 0).mean() * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=diffs, nbinsx=60, marker_color=NAVY_LIGHT,
        opacity=0.75, name="重抽差異",
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="black",
                  annotation_text="無差異", annotation_position="top")
    fig.add_vline(x=mean, line_color=ACCENT, line_width=2.5,
                  annotation_text=f"平均 {mean:+.2f}pp",
                  annotation_position="top")
    fig.add_vrect(x0=ci_low, x1=ci_high, fillcolor=ACCENT, opacity=0.15,
                  line_width=0, annotation_text="95% CI",
                  annotation_position="bottom left")
    fig.update_layout(
        height=380, plot_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="gate_40 - gate_30 (百分點)",
        yaxis_title="重抽次數",
        showlegend=False,
        title=f"P(gate_40 更差) = {p_worse:.1f}%",
    )
    col.markdown(f"**{title}**")
    col.markdown(f"95% Bootstrap CI:[{ci_low:+.2f}, {ci_high:+.2f}]pp")
    col.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("🧪 互動:換不同百分位數看信賴區間")

confidence = st.slider("信賴水準 (%)", 80, 99, 95, 1)
alpha = (100 - confidence) / 2

c1, c2 = st.columns(2)
for col, metric, title in zip([c1, c2], ["retention_1", "retention_7"],
                               ["Day 1 retention", "Day 7 retention"]):
    diffs = boot[f"{metric}_diff_pp"].values
    lo, hi = np.percentile(diffs, [alpha, 100-alpha])
    contains_zero = lo <= 0 <= hi

    col.markdown(f"**{title}**")
    if contains_zero:
        col.warning(f"{confidence}% CI = [{lo:+.2f}, {hi:+.2f}]pp · "
                   f"包含 0 → 不顯著")
    else:
        col.error(f"{confidence}% CI = [{lo:+.2f}, {hi:+.2f}]pp · "
                  f"不包含 0 → 顯著差異")

st.divider()

st.subheader("🤔 Bootstrap vs Frequentist 差在哪?")

st.markdown(
    """
    | 比較 | Frequentist (z-test) | Bootstrap |
    |---|---|---|
    | 假設 | 樣本服從常態分布 | 不需要假設 |
    | 公式 | 有解析解 | 用模擬 |
    | 樣本小怎麼辦 | 不可信 | 仍可用 |
    | 結果直觀度 | p-value(難解讀) | 「P(更差) = 96%」(直覺) |
    | 計算成本 | 秒級 | 慢(本案 10K 重抽 ~20 秒) |

    **何時用 Bootstrap**:樣本小、分布偏態、想要直觀的「機率語言」(向 PM/業務溝通)。
    **何時用 Frequentist**:樣本大、需要快速 ad-hoc 計算、有 industry standard 要對齊。

    **本案兩種方法結論完全一致**,反映結論 robust。
    """
)
