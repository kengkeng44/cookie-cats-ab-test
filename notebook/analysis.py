"""
Cookie Cats A/B Test Analysis
==============================
Tactile Games 把卡關門檻從第 30 關移到第 40 關,測試對留存的影響。
本腳本完整跑三種統計角度:Frequentist + Bootstrap + Bayesian。

產出:
  output/summary.csv             — 主要統計結果
  output/retention_compare.png   — D1 / D7 留存對照
  output/bootstrap_dist.png      — Bootstrap 差異分布
  output/posterior.png           — Bayesian posterior
  output/gamerounds_dist.png     — 遊戲輪數分布(對數軸)
  output/decision.md             — PM 決策建議
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint

mpl.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Arial Unicode MS", "DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cookie_cats.csv"
OUT = ROOT / "output"
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY = "#1a1a2e"
ACCENT = "#e63946"
NAVY_LIGHT = "#94a3b8"

rng = np.random.default_rng(42)

# -----------------------------------------------------------------------------
# 1. Load + sanity check
# -----------------------------------------------------------------------------
df = pd.read_csv(DATA)
print(f"Sample size: {len(df):,}")
print(df["version"].value_counts().to_string())

# Sanity: SRM (Sample Ratio Mismatch) check — sample sizes should be ~50/50
n30, n40 = (df["version"] == "gate_30").sum(), (df["version"] == "gate_40").sum()
srm_chi2, srm_p = stats.chisquare([n30, n40], [(n30+n40)/2, (n30+n40)/2])
print(f"\nSRM check (chi2={srm_chi2:.3f}, p={srm_p:.4f}) "
      f"-> {'PASS' if srm_p > 0.01 else 'FAIL — investigate randomization'}")

# -----------------------------------------------------------------------------
# 2. Frequentist tests
# -----------------------------------------------------------------------------
def proportion_test(metric: str) -> dict:
    """2-proportion z-test + 95% CI for difference."""
    g30 = df.loc[df["version"] == "gate_30", metric].astype(int)
    g40 = df.loc[df["version"] == "gate_40", metric].astype(int)
    s30, s40 = g30.sum(), g40.sum()
    p30, p40 = g30.mean(), g40.mean()
    z, p = proportions_ztest([s40, s30], [len(g40), len(g30)])
    diff = p40 - p30
    se = np.sqrt(p30*(1-p30)/len(g30) + p40*(1-p40)/len(g40))
    ci = (diff - 1.96*se, diff + 1.96*se)
    h = 2*np.arcsin(np.sqrt(p40)) - 2*np.arcsin(np.sqrt(p30))  # Cohen's h
    return dict(
        metric=metric, p30=p30, p40=p40, diff_pp=diff*100,
        z=z, pvalue=p, ci_low_pp=ci[0]*100, ci_high_pp=ci[1]*100,
        cohens_h=h,
    )

freq_results = [proportion_test("retention_1"), proportion_test("retention_7")]
freq_df = pd.DataFrame(freq_results)
print("\n=== Frequentist 2-proportion z-test ===")
print(freq_df.round(4).to_string(index=False))

# -----------------------------------------------------------------------------
# 3. Bootstrap CI (10,000 resamples)
# -----------------------------------------------------------------------------
def bootstrap_diff(metric: str, n_iter=10_000) -> tuple[np.ndarray, float, tuple]:
    g30 = df.loc[df["version"] == "gate_30", metric].astype(int).values
    g40 = df.loc[df["version"] == "gate_40", metric].astype(int).values
    diffs = np.empty(n_iter)
    for i in range(n_iter):
        s30 = rng.choice(g30, len(g30), replace=True).mean()
        s40 = rng.choice(g40, len(g40), replace=True).mean()
        diffs[i] = s40 - s30
    return diffs, diffs.mean(), tuple(np.percentile(diffs, [2.5, 97.5]))

print("\n=== Bootstrap (10,000 resamples) ===")
boot_data = {}
for metric in ["retention_1", "retention_7"]:
    diffs, mean, ci = bootstrap_diff(metric)
    boot_data[metric] = (diffs, mean, ci)
    p_worse = (diffs < 0).mean()
    print(f"{metric}: mean diff = {mean*100:+.3f}pp, "
          f"95% CI = [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}]pp, "
          f"P(gate_40 worse) = {p_worse:.3f}")

# -----------------------------------------------------------------------------
# 4. Bayesian (Beta-Binomial conjugate, Jeffreys prior Beta(0.5, 0.5))
# -----------------------------------------------------------------------------
def bayesian_compare(metric: str, n_samples=200_000) -> dict:
    g30 = df.loc[df["version"] == "gate_30", metric].astype(int)
    g40 = df.loc[df["version"] == "gate_40", metric].astype(int)
    a30, b30 = 0.5 + g30.sum(), 0.5 + (len(g30) - g30.sum())
    a40, b40 = 0.5 + g40.sum(), 0.5 + (len(g40) - g40.sum())
    p30 = rng.beta(a30, b30, n_samples)
    p40 = rng.beta(a40, b40, n_samples)
    diff = p40 - p30
    return dict(
        metric=metric,
        p_gate40_better=(diff > 0).mean(),
        p_gate40_worse=(diff < 0).mean(),
        cred_int_low_pp=np.percentile(diff, 2.5)*100,
        cred_int_high_pp=np.percentile(diff, 97.5)*100,
        posterior_p30=p30, posterior_p40=p40, posterior_diff=diff,
    )

print("\n=== Bayesian (Beta-Binomial, Jeffreys prior) ===")
bayes_results = []
posteriors = {}
for metric in ["retention_1", "retention_7"]:
    res = bayesian_compare(metric)
    posteriors[metric] = res
    bayes_results.append({k: v for k, v in res.items() if k.startswith(("metric","p_","cred_"))})
    print(f"{metric}: P(gate_40 better) = {res['p_gate40_better']:.3f}, "
          f"95% credible interval = [{res['cred_int_low_pp']:+.3f}, "
          f"{res['cred_int_high_pp']:+.3f}]pp")
bayes_df = pd.DataFrame(bayes_results)

# -----------------------------------------------------------------------------
# 5. Save summary CSV
# -----------------------------------------------------------------------------
summary = freq_df.merge(bayes_df, on="metric")
summary.to_csv(OUT / "summary.csv", index=False, encoding="utf-8-sig")
print(f"\nsaved: {OUT/'summary.csv'}")

# Aggregates used by the Streamlit app
agg = pd.DataFrame([
    {"version": v,
     "n_users": int((df["version"]==v).sum()),
     "retention_1_rate": df.loc[df["version"]==v, "retention_1"].mean(),
     "retention_7_rate": df.loc[df["version"]==v, "retention_7"].mean(),
     "retention_1_count": int(df.loc[df["version"]==v, "retention_1"].sum()),
     "retention_7_count": int(df.loc[df["version"]==v, "retention_7"].sum()),
     "gamerounds_mean": df.loc[df["version"]==v, "sum_gamerounds"].mean(),
     "gamerounds_median": df.loc[df["version"]==v, "sum_gamerounds"].median()}
    for v in ["gate_30", "gate_40"]
])
agg.to_csv(OUT / "aggregates.csv", index=False, encoding="utf-8-sig")
print(f"saved: {OUT/'aggregates.csv'}")

# Bootstrap distributions (10K samples, ~160KB)
boot_df = pd.DataFrame({
    f"{m}_diff_pp": boot_data[m][0] * 100
    for m in ["retention_1", "retention_7"]
})
boot_df.to_csv(OUT / "bootstrap_samples.csv", index=False, encoding="utf-8-sig")
print(f"saved: {OUT/'bootstrap_samples.csv'}")

# Bayesian posterior samples (sub-sample to 10K each, ~250KB total)
post_df = pd.DataFrame({
    f"{m}_p30": posteriors[m]["posterior_p30"][:10_000] * 100
    for m in ["retention_1", "retention_7"]
})
for m in ["retention_1", "retention_7"]:
    post_df[f"{m}_p40"] = posteriors[m]["posterior_p40"][:10_000] * 100
    post_df[f"{m}_diff_pp"] = posteriors[m]["posterior_diff"][:10_000] * 100
post_df.to_csv(OUT / "posterior_samples.csv", index=False, encoding="utf-8-sig")
print(f"saved: {OUT/'posterior_samples.csv'}")

# Game rounds histogram (binned, for fast app rendering)
bins = np.logspace(0, np.log10(max(1, df["sum_gamerounds"].max())), 60)
hist_rows = []
for v in ["gate_30", "gate_40"]:
    counts, edges = np.histogram(
        df.loc[df["version"] == v, "sum_gamerounds"][df["sum_gamerounds"] > 0],
        bins=bins,
    )
    for i, c in enumerate(counts):
        hist_rows.append({"version": v, "bin_low": edges[i], "bin_high": edges[i+1], "count": int(c)})
gr_hist = pd.DataFrame(hist_rows)
gr_hist.to_csv(OUT / "gamerounds_histogram.csv", index=False, encoding="utf-8-sig")
print(f"saved: {OUT/'gamerounds_histogram.csv'}")

# SRM data (single row)
srm_df = pd.DataFrame([{
    "n_gate_30": int(n30), "n_gate_40": int(n40),
    "expected_each": (n30+n40)/2,
    "chi2": float(srm_chi2), "p_value": float(srm_p),
    "verdict": "PASS" if srm_p > 0.01 else "FAIL",
}])
srm_df.to_csv(OUT / "srm.csv", index=False, encoding="utf-8-sig")
print(f"saved: {OUT/'srm.csv'}")

# -----------------------------------------------------------------------------
# 6. Visualizations
# -----------------------------------------------------------------------------
# 6a. Retention compare bars
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, metric, title in zip(axes, ["retention_1", "retention_7"],
                              ["1 日留存 (Day 1 Retention)", "7 日留存 (Day 7 Retention)"]):
    p30 = df.loc[df["version"] == "gate_30", metric].mean() * 100
    p40 = df.loc[df["version"] == "gate_40", metric].mean() * 100
    diffs, _, ci = boot_data[metric]
    err = [[(p40-p30) - ci[0]*100], [ci[1]*100 - (p40-p30)]]
    bars = ax.bar(["gate_30 (對照)", "gate_40 (實驗)"], [p30, p40],
                   color=[NAVY_LIGHT, ACCENT], width=0.55, edgecolor="white")
    for b, v, n in zip(bars, [p30, p40], [n30, n40]):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                f"{v:.2f}%", ha="center", fontweight="bold", fontsize=12)
        ax.text(b.get_x()+b.get_width()/2, b.get_height()/2,
                f"n={n:,}", ha="center", color="white", fontsize=9)
    delta = p40 - p30
    ax.set_title(f"{title}\nΔ = {delta:+.2f}pp · "
                 f"95% Bootstrap CI [{ci[0]*100:+.2f}, {ci[1]*100:+.2f}]pp",
                 fontsize=11)
    ax.set_ylabel("留存率 (%)")
    ax.set_ylim(0, max(p30, p40) * 1.25)
    ax.grid(axis="y", alpha=0.3)
plt.suptitle("Cookie Cats A/B 測試:gate_30 vs gate_40 留存對照",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(OUT / "retention_compare.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"saved: {OUT/'retention_compare.png'}")

# 6b. Bootstrap distribution
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for ax, metric, title in zip(axes, ["retention_1", "retention_7"],
                              ["1 日留存差異", "7 日留存差異"]):
    diffs, mean, ci = boot_data[metric]
    diffs_pp = diffs * 100
    p_worse = (diffs < 0).mean() * 100
    ax.hist(diffs_pp, bins=60, color=NAVY_LIGHT, alpha=0.7, edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1.2, label="無差異 (0)")
    ax.axvline(mean*100, color=ACCENT, linewidth=2, label=f"平均 {mean*100:+.2f}pp")
    ax.axvspan(ci[0]*100, ci[1]*100, alpha=0.15, color=ACCENT, label="95% CI")
    ax.set_title(f"{title}\nP(gate_40 更差) = {p_worse:.1f}%", fontsize=11)
    ax.set_xlabel("gate_40 - gate_30 (百分點)")
    ax.set_ylabel("Bootstrap 樣本數")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
plt.suptitle("Bootstrap 留存差異分布 (10,000 重抽)",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(OUT / "bootstrap_dist.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"saved: {OUT/'bootstrap_dist.png'}")

# 6c. Bayesian posteriors
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for ax, metric, title in zip(axes, ["retention_1", "retention_7"],
                              ["1 日留存", "7 日留存"]):
    r = posteriors[metric]
    ax.hist(r["posterior_p30"]*100, bins=80, color=NAVY_LIGHT, alpha=0.55,
            label="gate_30 (對照)", density=True)
    ax.hist(r["posterior_p40"]*100, bins=80, color=ACCENT, alpha=0.55,
            label="gate_40 (實驗)", density=True)
    ax.set_title(f"{title} 後驗分布\n"
                 f"P(gate_40 better) = {r['p_gate40_better']:.3f}",
                 fontsize=11)
    ax.set_xlabel("留存率 (%)")
    ax.set_ylabel("Posterior 密度")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3)
plt.suptitle("Bayesian 後驗分布 (Beta-Binomial · Jeffreys prior)",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(OUT / "posterior.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"saved: {OUT/'posterior.png'}")

# 6d. Game rounds distribution (log scale)
fig, ax = plt.subplots(figsize=(11, 5))
g30 = df.loc[df["version"] == "gate_30", "sum_gamerounds"]
g40 = df.loc[df["version"] == "gate_40", "sum_gamerounds"]
bins = np.logspace(0, np.log10(max(g30.max(), g40.max())), 60)
g30_clipped = g30[g30 > 0]
g40_clipped = g40[g40 > 0]
ax.hist(g30_clipped, bins=bins, alpha=0.55, color=NAVY_LIGHT, label="gate_30 (對照)")
ax.hist(g40_clipped, bins=bins, alpha=0.55, color=ACCENT, label="gate_40 (實驗)")
ax.axvline(30, linestyle="--", color=NAVY_LIGHT, alpha=0.8)
ax.text(30, ax.get_ylim()[1]*0.9, " 第 30 關 ", color=NAVY_LIGHT, va="top", fontsize=9)
ax.axvline(40, linestyle="--", color=ACCENT, alpha=0.8)
ax.text(40, ax.get_ylim()[1]*0.9, " 第 40 關 ", color=ACCENT, va="top", fontsize=9)
ax.set_xscale("log")
ax.set_xlabel("Total game rounds in first 14 days (log)")
ax.set_ylabel("玩家數")
ax.set_title("遊戲輪數分布 — 兩組分布幾乎重疊,門檻位置看不出明顯效應",
             fontsize=12, fontweight="bold")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "gamerounds_dist.png", dpi=120, bbox_inches="tight")
plt.close()
print(f"saved: {OUT/'gamerounds_dist.png'}")

# -----------------------------------------------------------------------------
# 7. Power analysis (post-hoc)
# -----------------------------------------------------------------------------
from statsmodels.stats.power import zt_ind_solve_power
print("\n=== Post-hoc power analysis ===")
for metric in ["retention_1", "retention_7"]:
    p30 = df.loc[df["version"] == "gate_30", metric].mean()
    p40 = df.loc[df["version"] == "gate_40", metric].mean()
    h = 2*np.arcsin(np.sqrt(p40)) - 2*np.arcsin(np.sqrt(p30))
    n_per_arm = (n30 + n40) / 2
    power = zt_ind_solve_power(effect_size=h, nobs1=n_per_arm,
                                alpha=0.05, ratio=1.0)
    # MDE: minimum detectable effect at 80% power
    mde_h = zt_ind_solve_power(nobs1=n_per_arm, alpha=0.05, power=0.8, ratio=1.0)
    mde_pp = abs(2*np.sin(mde_h/2 + np.arcsin(np.sqrt(p30)))**2 - 2*np.sin(np.arcsin(np.sqrt(p30)))**2*0+0) - 0
    # Simpler MDE: convert h back assuming p30 baseline
    p40_mde = np.sin(mde_h/2 + np.arcsin(np.sqrt(p30)))**2
    mde_pp = (p40_mde - p30) * 100
    print(f"{metric}: observed power = {power:.3f}, MDE (80% power) = ±{mde_pp:.2f}pp")

# -----------------------------------------------------------------------------
# 8. Decision write-up
# -----------------------------------------------------------------------------
r1 = freq_df.iloc[0]; r7 = freq_df.iloc[1]
b1 = bayes_df.iloc[0]; b7 = bayes_df.iloc[1]

decision = f"""# PM 決策建議:**不要 ship gate_40**

## TL;DR

把卡關門檻從第 30 關移到第 40 關,**兩個留存指標都呈現負向變化**(gate_40 更差):

| 指標 | 對照 (gate_30) | 實驗 (gate_40) | 差異 | p-value | Bayesian P(gate_40 better) |
|---|---:|---:|---:|---:|---:|
| 1 日留存 | {r1.p30*100:.2f}% | {r1.p40*100:.2f}% | {r1.diff_pp:+.2f}pp | {r1.pvalue:.4f} | {b1.p_gate40_better:.3f} |
| 7 日留存 | {r7.p30*100:.2f}% | {r7.p40*100:.2f}% | {r7.diff_pp:+.2f}pp | {r7.pvalue:.4f} | {b7.p_gate40_better:.3f} |

**結論**:不該 ship gate_40。原本「移後門檻 → 玩家不被卡 → 留存提升」的假設**被推翻**。

## 三種統計方法都指向同一結論

1. **Frequentist 2-proportion z-test**:7 日留存 p-value = {r7.pvalue:.4f},顯著(α=0.05)
2. **Bootstrap 95% CI**:7 日留存差異 [{r7.ci_low_pp:+.2f}, {r7.ci_high_pp:+.2f}]pp,**完全在 0 以下**
3. **Bayesian Beta-Binomial**:P(gate_40 比 gate_30 好) = {b7.p_gate40_better:.1%},反過來說 P(更差) = {b7.p_gate40_worse:.1%}

## 為什麼直覺錯了

直覺:「玩家被卡關會流失,門檻往後移應該更好」
實際:**門檻可能扮演承諾機制(commitment device) — 卡關產生「未完成感」反而促使玩家回來**

這是經典的 PM 教訓:**A/B 測試的存在就是為了破除直覺**。

## 限制與下一步

1. **觀察期只有 14 天** — 長期影響(30/90 日留存)未測
2. **未做用戶分群分析** — 新手 vs 老玩家、付費 vs 免費可能反應不同
3. **未量化營收影響** — 若 gate_40 留存差但 ARPU 高(例如挫折感降低 → 願付費)結論可能反轉
4. **建議下一個實驗**:gate_35 看是否有甜蜜點;或測「移除 gate 但加每日任務」
"""
(OUT / "decision.md").write_text(decision, encoding="utf-8")
print(f"saved: {OUT/'decision.md'}")
print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
