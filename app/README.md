# Cookie Cats Streamlit Dashboard

5 分頁互動式 dashboard,把 A/B 測試評估整理成可口語走過的版本。

## 本機執行

```powershell
pip install -r requirements.txt
streamlit run app/Home.py
```

## 部署到 Streamlit Cloud

1. 確認 repo 已 push 到 GitHub
2. 進 [share.streamlit.io](https://share.streamlit.io) → 用 GitHub 帳號登入
3. **New app** → 選 `kengkeng44/cookie-cats-ab-test`
4. **Main file path** 填 `app/Home.py`
5. **Custom subdomain** 自訂(例:`cookie-cats-jenho`)
6. 點 **Deploy**

每次 push 到 master 自動重新部署。

## 結構

```
app/
├── Home.py                # 入口:headline metric + SRM 警示 + 三方法概覽
└── pages/
    ├── 1_🚨_SRM檢查.py     # Sample Ratio Mismatch test + 互動樣本量計算
    ├── 2_📊_Frequentist.py # 2-proportion z-test + Cohen's h + 留存對照
    ├── 3_🎲_Bootstrap.py   # 10K 重抽分布 + 互動信賴水準
    ├── 4_🔮_Bayesian.py    # Beta-Binomial 後驗 + 互動 prior 比較
    └── 5_🎯_PM決策.py       # Ship/no-ship 推論 + 三個假設 + 下一個實驗
```

## 互動亮點

- **SRM 頁**:互動式 power calculator,拖滑桿看不同效應/power 需要多大樣本
- **Bootstrap 頁**:換信賴水準看 CI 是否包含 0
- **Bayesian 頁**:換不同 prior(從弱資訊到強烈信念)看 posterior 變化
- 所有圖:點右上角下載 PNG / CSV
