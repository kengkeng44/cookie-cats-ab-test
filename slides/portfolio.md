---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-family: "Microsoft JhengHei", "Helvetica Neue", sans-serif;
    padding: 60px 70px;
  }
  section.lead {
    text-align: center;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #e8e8e8;
  }
  section.lead h1 { font-size: 2.6em; margin-bottom: 0.3em; }
  section.lead h2 { font-weight: 300; color: #b8c5d6; }
  section.lead p { color: #94a3b8; font-size: 0.9em; }
  h1 { color: #1a1a2e; border-bottom: 3px solid #e63946; padding-bottom: 0.2em; }
  h2 { color: #1a1a2e; }
  strong { color: #e63946; }
  blockquote { border-left: 4px solid #e63946; color: #555; }
  table { font-size: 0.85em; }
  th { background: #1a1a2e; color: white; }
  tr:nth-child(even) { background: #f5f5f5; }
---

<!-- _class: lead -->

# Cookie Cats A/B 測試評估

## 該不該把卡關門檻從第 30 關移到第 40 關?

jenho.cheng · PM Portfolio · 2026

`Python` · `scipy` · `statsmodels` · `Bayesian` · `Streamlit`

---

## 業務情境

**Tactile Games** 旗下 *Cookie Cats* — 連連看 + 解謎手遊,> 1 億下載量

**實驗設計**:把首次卡關門檻從第 **30** 關移到第 **40** 關
- **gate_30** (對照組):44,700 玩家
- **gate_40** (實驗組):45,489 玩家
- 觀察期:安裝後 14 天

**業務假設**:玩家少被卡 → 留存應該提升 → ship gate_40

**問題**:這個假設成立嗎?

---

## 🚨 第一件事 — 不是看指標,是檢查實驗本身

| 組別 | 玩家數 | 比例 |
|---|---:|---:|
| gate_30 | 44,700 | 49.56% |
| gate_40 | 45,489 | 50.44% |

理論 50/50,實際 chi-square test → **p = 0.0086**

**= SRM (Sample Ratio Mismatch) 異常**

> **業界標準** (Microsoft / Google / Airbnb):SRM p < 0.01 的實驗結果不該採信。
> 通常代表 randomization 有 bug — 某裝置/地區/版本只進其中一組,結果失真。

**PM 行動**:不 share 結果給 leadership,先請工程 debug randomization

---

## 若忽略 SRM 強行分析:三種方法 vs 同一結論

### 方法 1 — Frequentist 2-proportion z-test

| 指標 | 對照 | 實驗 | 差異 | p-value | 95% CI |
|---|---:|---:|---:|---:|---|
| Day 1 留存 | 44.82% | 44.23% | -0.59pp | 0.074 | [-1.24, +0.06] |
| **Day 7 留存** | **19.02%** | **18.20%** | **-0.82pp** | **0.0016** | **[-1.33, -0.31]** |

D7 顯著差異(p < 0.01),95% CI 完全在 0 以下。

D1 邊緣不顯著,但 **post-hoc power 只有 0.43** — under-powered,不能因此 conclude「沒差異」。

---

## 方法 2 — Bootstrap 重抽 10K 次

| 指標 | 平均差異 | 95% Bootstrap CI | P(gate_40 更差) |
|---|---:|---|---:|
| Day 1 留存 | -0.59pp | [-1.23, +0.05]pp | **96.3%** |
| Day 7 留存 | -0.82pp | [-1.33, -0.31]pp | **100%** |

**Day 7 全部 10,000 次重抽都顯示 gate_40 更差** — 結論非常 robust

> Bootstrap 不假設分布形狀,不需要常態假設,直接用資料估計不確定性。
> 比 Frequentist 更直觀:不講 p-value,直接給「比較差的機率」。

---

## 方法 3 — Bayesian Beta-Binomial

Jeffreys prior `Beta(0.5, 0.5)`,200,000 次後驗抽樣

| 指標 | P(gate_40 better) | 95% Credible Interval |
|---|---:|---|
| Day 1 留存 | **3.7%** | [-1.24, +0.06]pp |
| Day 7 留存 | **0.1%** | [-1.33, -0.31]pp |

> Bayesian 給的是 **「假設為真的直接機率」**,不像 Frequentist 的 p-value 那樣繞口。
> P(gate_40 better) = 0.001 → 業務語言:**「gate_40 比較好的機率約 1/1000,等於確定不該 ship」**。

---

## 三方法都指向同一結論

| 方法 | 結論 |
|---|---|
| Frequentist | D7 顯著更差 (p=0.0016) |
| Bootstrap | D7 100% 重抽顯示更差 |
| Bayesian | D7 P(better) = 0.001 |

**為什麼用三種方法?**
- 單一方法可能受假設侷限(Frequentist 假設常態、Bayesian 受 prior 影響)
- 三角驗證 = 結論 robust
- 對不同受眾講不同語言:技術人聽 p-value,業務聽機率

---

## 🎯 PM 決策:不要 ship gate_40

**三層理由**

1. 🚨 **SRM 異常 (p=0.0086)** — 業界標準會擋下這個實驗,先修 randomization
2. 📉 **若強行解讀**:Day 7 留存 -0.82pp,三種方法一致
3. 🎯 **業務上不小**:Cookie Cats 規模(每日新裝 10 萬)→ -0.82pp = **30,000 玩家/月流失**

---

## 為什麼直覺錯了?三個假設

| 假設 | 為什麼可能成立 | 怎麼驗證 |
|---|---|---|
| **承諾機制** | 卡關產生「未完成感」(Zeigarnik effect)促玩家回來 | 比較卡關玩家 vs 未卡關的長期留存 |
| **IAP 觸發點** | 第 30 關是「願付費」最佳時機,40 關錯失轉換 | 看 ARPU / 付費轉換率 |
| **社群催化** | 卡關玩家會去查攻略 / 找朋友 → 提升黏著 | 看社群行為 / 攻略搜尋量 |

**啟示**:門檻不是「障礙」,是某種**正向機制**。下次設計實驗前要先想「這個 feature 在做什麼」,而不只是「移除它應該更好」。

---

## 下一個實驗該怎麼設計

1. **測 gate_35** — 找甜蜜點(線性外推不一定成立,要驗)
2. **測「移除 gate 但加每日任務」** — 用每日任務取代強制卡關,維持承諾感
3. **加 segment 分析** — 新手 vs 老玩家可能反應不同
4. **加營收指標** — 留存差但 ARPU 高也可能 ship,目前資料不足
5. **重跑時樣本量加大 4 倍** — D1 power 0.43,需更大樣本才能定論

---

## 從這個案子學到什麼

✅ **A/B 測試的存在就是為了破除直覺** — 結果跟直覺一樣的實驗就是浪費錢

✅ **第一件事是檢查實驗本身**(SRM、樣本量、power),再看指標

✅ **三種方法交叉驗證** = 結論 robust,單一方法可能有死穴

✅ **效應大小 vs 統計顯著要分開看** — p < 0.05 不代表業務上重要

---

## 我的差異化 vs 多數 PM portfolio

| 多數 PM 履歷的 A/B 案例 | 我的做法 |
|---|---|
| 看 p-value < 0.05 就 conclude | 先檢查 SRM,業界標準作法 |
| 只用 t-test 或只用 Bayesian | 三方法交叉驗證 |
| 不算 power | post-hoc power 0.43 → 知道哪個結論不可信 |
| 結論 = ship/no-ship | 結論 = ship/no-ship + 為什麼 + 下個實驗 |
| 不質疑業務假設 | 直覺被推翻時提出三個可驗證假設 |

---

<!-- _class: lead -->

# Q&A

**🚀 互動 Dashboard**: cookie-cats-jenho.streamlit.app

**Repo**: github.com/kengkeng44/cookie-cats-ab-test

**姊妹作 (電商分析)**: olist-jenho.streamlit.app · github.com/kengkeng44/olist-project

**重現**: `python notebook/analysis.py`

> Thank you.
