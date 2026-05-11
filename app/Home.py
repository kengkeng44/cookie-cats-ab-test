"""Cookie Cats A/B Test — Streamlit Dashboard.

Run locally:   streamlit run app/Home.py
Deploy:        push to GitHub, deploy from share.streamlit.io
"""

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"

st.set_page_config(
    page_title="Cookie Cats A/B Test",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1a1a2e"
ACCENT = "#e63946"
MUTED = "#94a3b8"


@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")


st.markdown(
    f"""
    <div style='background: linear-gradient(135deg, {PRIMARY} 0%, #16213e 100%);
                padding: 2rem; border-radius: 12px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0; font-size: 2.4rem;'>
            🎮 Cookie Cats A/B 測試評估
        </h1>
        <p style='color: #b8c5d6; margin-top: 0.5rem; font-size: 1.1rem;'>
            把卡關門檻從第 30 關移到第 40 關 ——
            <strong style='color: {ACCENT};'>該不該 ship?</strong>
        </p>
        <p style='color: #94a3b8; margin-top: 0.3rem; font-size: 0.9rem;'>
            90,189 玩家 · Frequentist + Bootstrap + Bayesian 三角驗證 · Tactile Games
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

agg = load("aggregates.csv")
srm = load("srm.csv").iloc[0]
summary = load("summary.csv")

g30 = agg[agg["version"] == "gate_30"].iloc[0]
g40 = agg[agg["version"] == "gate_40"].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("總樣本數", f"{int(g30['n_users']+g40['n_users']):,}")
c2.metric("D1 留存差異", f"{(g40['retention_1_rate']-g30['retention_1_rate'])*100:+.2f}pp",
          delta_color="inverse")
c3.metric("D7 留存差異", f"{(g40['retention_7_rate']-g30['retention_7_rate'])*100:+.2f}pp",
          delta_color="inverse")
c4.metric("SRM Test", srm["verdict"], f"p={srm['p_value']:.4f}",
          delta_color="inverse" if srm["verdict"] == "FAIL" else "normal")

st.divider()

st.error(
    f"### 🚨 第一個發現:**SRM 異常 (p={srm['p_value']:.4f})**\n\n"
    f"理論 50/50 隨機分配,實際 {int(g30['n_users']):,} vs {int(g40['n_users']):,} —— "
    f"**chi-square test p-value = {srm['p_value']:.4f} < 0.01** = 業界標準會擋下這個實驗。\n\n"
    f"**任何 A/B 測試結果出來,第一件事不是看指標,是檢查實驗本身**。"
    f" SRM 違規通常代表 randomization 有 bug,結果不該採信。"
)
st.markdown(
    f"<a href='/SRM檢查' target='_self' style='color:{ACCENT}; text-decoration:none;'>"
    f"→ 進 SRM 檢查頁看詳細分析</a>",
    unsafe_allow_html=True,
)

with st.expander("💡 為什麼我刻意保留 SRM fail 的分析在 portfolio?"):
    st.markdown(
        """
        業界 **6-10% 的線上實驗會 SRM fail**(Microsoft Exp 平台 paper, Fabijan et al. 2019),
        這不是冷門狀況,是 PM 日常。挑乾淨數據集只能 demo「會跑 t-test」——
        挑會出問題的數據集才能 demo 三件事:

        1. **我會抓 SRM** — 多數 PM 履歷直接看 p-value,我第一步先檢查實驗效度
        2. **我會處理 SRM fail 的決策** — 不藏不忽略,明確標註 limitation
        3. **同時還能 demo 三種統計方法** — 而非因 SRM fail 就停手什麼都不做

        這三件事在我看來才是 senior PM 的真正分水嶺。
        """
    )

st.divider()

st.subheader("🔬 若忽略 SRM 強行分析:三種方法都指向同一結論")
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <div style='color: {ACCENT}; font-size: 0.85rem; font-weight: bold;'>方法 1 — Frequentist</div>
            <h3 style='margin: 0.3rem 0; color: {PRIMARY};'>2-proportion z-test</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                D7 留存差異 <strong>p = 0.0016</strong><br>
                95% CI <strong>[-1.33, -0.31] pp</strong>
            </p>
            <a href='/Frequentist' target='_self' style='color:{ACCENT};'>→ 看 z-test 細節</a>
        </div>
        """, unsafe_allow_html=True)

with m2:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <div style='color: {ACCENT}; font-size: 0.85rem; font-weight: bold;'>方法 2 — Bootstrap</div>
            <h3 style='margin: 0.3rem 0; color: {PRIMARY};'>10K 重抽</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                D7 全部 <strong>10,000 次重抽</strong><br>
                100% 顯示 gate_40 更差
            </p>
            <a href='/Bootstrap' target='_self' style='color:{ACCENT};'>→ 看分布圖</a>
        </div>
        """, unsafe_allow_html=True)

with m3:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <div style='color: {ACCENT}; font-size: 0.85rem; font-weight: bold;'>方法 3 — Bayesian</div>
            <h3 style='margin: 0.3rem 0; color: {PRIMARY};'>Beta-Binomial</h3>
            <p style='color: #64748b; font-size: 0.95rem;'>
                P(gate_40 better) = <strong>0.001</strong><br>
                Jeffreys prior · 200K samples
            </p>
            <a href='/Bayesian' target='_self' style='color:{ACCENT};'>→ 看 posterior</a>
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.subheader("🎯 PM 決策建議")
st.warning(
    "**不要 ship gate_40**。直覺「移後門檻 → 玩家不被卡 → 留存提升」**被推翻**。\n\n"
    "可能原因:門檻可能扮演**承諾機制 (commitment device)**,卡關產生「未完成感」反而促使玩家回來。"
)
st.markdown(
    f"<a href='/PM決策' target='_self' style='color:{ACCENT};'>"
    f"→ 進 PM 決策頁看完整推論 + 三個假設 + 下一個實驗建議</a>",
    unsafe_allow_html=True,
)

st.divider()

with st.expander("ℹ️ 關於這份分析"):
    st.markdown(
        """
        **資料來源**:[Mobile Games A/B Testing (Kaggle)](https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing)
        Tactile Games 旗下 Cookie Cats(連連看 + 解謎,> 1 億下載量),90,189 玩家。

        **方法論**
        - SRM 檢測作為實驗效度的第一道關卡(業界標準, Microsoft / Google / Airbnb 都這樣做)
        - Frequentist (z-test) + Bootstrap 重抽 + Bayesian (Beta-Binomial) 三角驗證
        - Power analysis 揭露 Day 1 underpowered (0.43)

        **完整文件**:[GitHub repo](https://github.com/kengkeng44/cookie-cats-ab-test)
        含 `notebook/analysis.py` 完整可重現腳本。
        """
    )

st.sidebar.markdown(
    """
    ### Cookie Cats A/B

    **作者**:jenho.cheng
    **GitHub**:[kengkeng44/cookie-cats-ab-test](https://github.com/kengkeng44/cookie-cats-ab-test)
    **姊妹作**:[Olist 巴西電商分析](https://github.com/kengkeng44/olist-project)

    ---

    **分頁說明**
    - 🚨 SRM 檢查 — 為何這個實驗結果不該採信
    - 📊 Frequentist — 2-proportion z-test
    - 🎲 Bootstrap — 10K 重抽分布
    - 🔮 Bayesian — Beta-Binomial 後驗
    - 🎯 PM 決策 — Ship/no-ship + 三個假設
    """
)
