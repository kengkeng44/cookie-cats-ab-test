"""PM 決策建議 + 三個假設 + 下一個實驗."""

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = ROOT / "output"
PRIMARY = "#1a1a2e"
ACCENT = "#e63946"

st.set_page_config(page_title="PM 決策 · Cookie Cats", page_icon="🎯", layout="wide")
st.title("🎯 PM 決策建議")
st.caption("Ship/no-ship 推論 + 三個可驗證假設 + 下一個實驗設計")

@st.cache_data
def load(name): return pd.read_csv(OUTPUT / name, encoding="utf-8-sig")

agg = load("aggregates.csv")
srm = load("srm.csv").iloc[0]
summary = load("summary.csv")

st.error("## 🚫 不要 ship gate_40")
st.markdown(
    f"""
    **三層理由**

    1. 🚨 **實驗本身有 SRM 異常 (p={srm['p_value']:.4f})** —
       業界標準會擋下這個實驗,結果嚴格來說不該採信。**先修 randomization**。
    2. 📉 **若強行解讀**:Day 7 留存 -0.82pp,Frequentist p=0.0016,
       Bayesian P(better)=0.001,Bootstrap 100% 重抽顯示更差 — 三種方法一致
    3. 🎯 **效應小但業務上不小**:Cookie Cats 規模(每日新裝 10 萬)下,
       D7 留存 -0.82pp = 30,000 玩家/月流失
    """
)

st.divider()

st.subheader("🤔 為什麼直覺錯了?三個可驗證假設")

st.markdown("**業務直覺**:玩家少被卡 → 留存提升")
st.markdown("**實際結果**:gate_40 反而 **更差**")
st.markdown("**啟示**:門檻可能不是「障礙」,而是某種**正向機制**。三個可驗證假設:")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <h4 style='color: {ACCENT};'>假設 1<br>承諾機制</h4>
            <p>卡關產生「未完成感」,玩家會回來繼續 — 跟 Zeigarnik effect 一致(未完成的事更容易被記住)</p>
            <p><strong>怎麼驗</strong>:比較卡關玩家 vs 未卡關玩家的長期留存</p>
        </div>
        """, unsafe_allow_html=True)

with c2:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <h4 style='color: {ACCENT};'>假設 2<br>IAP 觸發</h4>
            <p>第 30 關是「願付費」的最佳時機(剛投入時間),移到 40 關錯失轉換</p>
            <p><strong>怎麼驗</strong>:看 ARPU / 付費轉換率(本資料集未提供,需內部數據)</p>
        </div>
        """, unsafe_allow_html=True)

with c3:
    st.markdown(
        f"""
        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                    border: 1px solid #e2e8f0; height: 100%;'>
            <h4 style='color: {ACCENT};'>假設 3<br>社群催化</h4>
            <p>卡在某關的玩家會去查攻略 / 找朋友問 → 提升黏著與分享</p>
            <p><strong>怎麼驗</strong>:社群行為 / 攻略搜尋量 / 邀請次數</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

st.subheader("🔬 下一個實驗建議")

st.markdown(
    """
    1. **測 gate_35** — 看是否有甜蜜點(線性外推:gate_30 → gate_40 變差,但 35 可能更好或更差,要驗)
    2. **測「移除 gate 但加每日任務」** — 用每日任務取代強制卡關,維持承諾感但減少挫折
    3. **加 segment 分析** — 新手 (Day 1-3) vs 老玩家可能反應不同,做 sub-population 才看得出真相
    4. **加營收指標** — 留存差但 ARPU 高也可能 ship,目前資料不足以判斷
    5. **重跑時樣本量加大 4 倍** — Day 1 power 只有 0.43,需要更大樣本才能定論
    """
)

st.divider()

st.subheader("🎓 從這個案子學到什麼")

c1, c2 = st.columns(2)
with c1:
    st.success(
        "✅ **A/B 測試的存在就是為了破除直覺** —— "
        "如果結果都跟直覺一樣,那花錢做測試就沒意義了"
    )
    st.success(
        "✅ **第一件事是檢查實驗本身**(SRM、樣本量、power),"
        "再看指標"
    )
with c2:
    st.info(
        "🎯 **三種方法交叉驗證** = 結論 robust。"
        "單一方法可能受假設侷限,多角度才安心"
    )
    st.info(
        "📐 **效應大小 vs 統計顯著** 要分開看 —— "
        "p < 0.05 不代表業務上重要,p > 0.05 不代表沒差異"
    )

st.divider()

with st.expander("🔍 完整 PM 決策文件"):
    st.markdown(
        """
        本頁是濃縮版。完整 markdown 文件在 repo 的 `output/decision.md`,
        含每個指標的逐項計算、限制聲明、後續實驗的詳細設計。

        **重現整個分析**:
        ```bash
        git clone https://github.com/kengkeng44/cookie-cats-ab-test
        cd cookie-cats-ab-test
        pip install -r requirements.txt
        kaggle datasets download -d yufengsui/mobile-games-ab-testing -p data --unzip
        python notebook/analysis.py
        ```
        """
    )
