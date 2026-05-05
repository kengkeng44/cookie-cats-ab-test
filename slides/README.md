# Slides

13 頁 PM 面試簡報,把整個 A/B 測試評估濃縮成可口語講述的版本。

## 編譯

```powershell
npm install -g @marp-team/marp-cli
marp slides/portfolio.md -o slides/portfolio.pdf --allow-local-files
marp slides/portfolio.md -o slides/portfolio.pptx --allow-local-files
```

## 結構

| 頁 | 主題 |
|---|---|
| 1 | 封面 |
| 2 | 業務情境 — 實驗設計 |
| 3 | 🚨 SRM 異常 — 為何先檢查實驗本身 |
| 4 | 方法 1: Frequentist z-test |
| 5 | 方法 2: Bootstrap 重抽 |
| 6 | 方法 3: Bayesian Beta-Binomial |
| 7 | 三方法收斂同一結論 |
| 8 | PM 決策:不要 ship |
| 9 | 為什麼直覺錯了 — 三個假設 |
| 10 | 下一個實驗該怎麼設計 |
| 11 | 從這個案子學到什麼 |
| 12 | 我的差異化 vs 多數 PM portfolio |
| 13 | Q&A |

## 講述時間

- 標準版 15 分鐘:每頁 ~70 秒
- 電梯版 5 分鐘:1 → 3 (SRM) → 8 (PM 決策) → 13
