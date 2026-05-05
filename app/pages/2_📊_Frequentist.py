"""Frequentist 2-proportion z-test."""

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = ROOT / "output"
PRIMARY = "#1a1a2e"
ACCENT = "#e63946"
NAVY_LIGHT = "#94a3b8"

st.set_page_config(page_title="Frequentist · Cookie Cats", page_icon="📊", layout="wide")
st.title("📊 Frequentist 2-Proportion z-test")
st.caption("傳統頻率學派假設檢定 + Cohen's h 效應量")

@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")

agg = load("aggregates.csv")
summary = load("summary.csv")
g30 = agg[agg["version"] == "gate_30"].iloc[0]
g40 = agg[agg["version"] == "gate_40"].iloc[0]

st.subheader("結果摘要")

display = summary[["metric", "p30", "p40", "diff_pp", "pvalue",
                   "ci_low_pp", "ci_high_pp", "cohens_h"]].copy()
display.columns = ["指標", "對照率", "實驗率", "差異 (pp)", "p-value",
                   "95% CI 下界", "95% CI 上界", "Cohen's h"]
display["對照率"] = display["對照率"].apply(lambda v: f"{v*100:.2f}%")
display["實驗率"] = display["實驗率"].apply(lambda v: f"{v*100:.2f}%")
display["差異 (pp)"] = display["差異 (pp)"].apply(lambda v: f"{v:+.2f}")
display["p-value"] = display["p-value"].apply(lambda v: f"{v:.4f}")
display["95% CI 下界"] = display["95% CI 下界"].apply(lambda v: f"{v:+.2f}")
display["95% CI 上界"] = display["95% CI 上界"].apply(lambda v: f"{v:+.2f}")
display["Cohen's h"] = display["Cohen's h"].apply(lambda v: f"{v:+.4f}")
st.dataframe(display, hide_index=True, use_container_width=True)

st.divider()

st.subheader("留存對照圖")
c1, c2 = st.columns(2)

for col, metric, title in zip([c1, c2],
                               ["retention_1", "retention_7"],
                               ["1 日留存 (Day 1)", "7 日留存 (Day 7)"]):
    p30 = g30[f"{metric}_rate"] * 100
    p40 = g40[f"{metric}_rate"] * 100
    row = summary[summary["metric"] == metric].iloc[0]

    fig = go.Figure(go.Bar(
        x=["gate_30 (對照)", "gate_40 (實驗)"], y=[p30, p40],
        marker_color=[NAVY_LIGHT, ACCENT],
        text=[f"{p30:.2f}%", f"{p40:.2f}%"],
        textposition="outside", width=0.55,
    ))
    fig.update_layout(
        height=350, plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="留存率 (%)",
        yaxis=dict(range=[0, max(p30, p40) * 1.2]),
    )
    col.markdown(f"**{title}**")
    col.markdown(f"Δ = {row['diff_pp']:+.2f}pp · p = {row['pvalue']:.4f} · "
                 f"95% CI [{row['ci_low_pp']:+.2f}, {row['ci_high_pp']:+.2f}]")
    col.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("📐 怎麼解讀?")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        **Day 1 留存 (p = 0.0744)**
        - 邊緣不顯著(α=0.05 標準下不能 reject H0)
        - 95% CI 跨 0:[-1.24, +0.06]pp
        - **不代表沒差異** — 可能是樣本不夠 (post-hoc power 只有 0.43)

        **Day 7 留存 (p = 0.0016)**
        - **顯著** (p < 0.01)
        - 95% CI 完全在 0 以下:[-1.33, -0.31]pp
        - 結論可信(power 0.89)
        """
    )
with c2:
    st.markdown(
        """
        **Cohen's h 效應量**

        | h 值 | 標籤 | 兩個比例舉例 |
        |---|---|---|
        | 0.2 | 小 | 50% vs 60% |
        | 0.5 | 中 | 50% vs 75% |
        | 0.8 | 大 | 50% vs 90% |

        本案 h ≈ 0.02,**統計上微小但業務上不微小** —
        Cookie Cats 規模(每日新裝 ~10 萬)下,
        D7 留存差 0.82pp = 30,000 玩家/月。
        """
    )

st.error(
    "⚠️ **常見陷阱:p < 0.05 ≠ ship,p > 0.05 ≠ no ship**。"
    "PM 該看的是「差異大小、信賴區間、決策成本、業務情境」整體判斷,而不是 p-value 跨過某個門檻。"
)
