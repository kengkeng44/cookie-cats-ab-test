# Cookie Cats A/B Test — Should we move the level gate?

**English** · **[繁體中文](README.zh-TW.md)**

> Tactile Games moved Cookie Cats' progression gate from level 30 to level 40 to test the effect on retention.
> Analyzed 90,189 players with **Frequentist + Bootstrap + Bayesian** three approaches and delivered a clear ship / no-ship recommendation.

**🚀 [Interactive Dashboard (Streamlit)](https://cookie-cats-jenho.streamlit.app/)** · **📑 [Interview Deck (PDF)](slides/portfolio.pdf)** · **📊 [Sister project: Olist E-commerce Analysis](https://github.com/kengkeng44/olist-project)**

**TL;DR**
1. 🚨 **Experiment has an SRM (Sample Ratio Mismatch) violation, p=0.0086** — strictly speaking the result should not be trusted; ask engineering to investigate the randomization first
2. **If we read it anyway**: gate_40 (treatment) is significantly worse on 7-day retention (-0.82pp, p=0.0016, Bayesian P(better)=0.001) → **do not ship**
3. The intuition "move the gate later → less stuck → better retention" **is overturned** — the gate may be acting as a commitment device

---

## 1. Why this case?

PM-targeted data analysis on resumes usually stops at descriptive statistics (RFM, retention distributions). This project demonstrates **experiment design and evaluation**.

**And I deliberately picked a case that fails SRM.**

6–10% of online experiments in the industry fail SRM (Microsoft Experimentation Platform paper, Fabijan et al. 2019) — this isn't a fringe scenario, it's a daily PM reality. Picking a clean dataset only demonstrates "can run t-tests." Picking a problematic dataset demonstrates:

1. **I catch SRM** — most PM resumes jump straight to p-values; I check experiment validity first
2. **I handle the SRM-fail decision** — I don't hide or ignore it; I flag the limitation and provide a contingency plan
3. **I can still demonstrate three statistical methods** — Frequentist / Bootstrap / Bayesian triangulation rather than freezing when SRM fails

These three behaviors are, in my view, the real watershed for senior PM work.

I deliberately picked gaming as the domain (vs. e-commerce in my [Olist project](https://github.com/kengkeng44/olist-project)) to broaden the portfolio.

---

## 2. Data source

| Item | Details |
|---|---|
| Source | [Mobile Games A/B Testing (Kaggle)](https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing) |
| Company | Tactile Games (Danish mobile gaming) |
| Game | Cookie Cats (match-3 puzzler, > 100M downloads) |
| Sample | 90,189 players |
| Observation window | 14 days post-install |

| Column | Description |
|---|---|
| `userid` | Player ID |
| `version` | `gate_30` (control) / `gate_40` (treatment) |
| `sum_gamerounds` | Rounds played in first 14 days |
| `retention_1` | Returned to play on day 1 |
| `retention_7` | Returned to play on day 7 |

**Experiment design**: move the first progression gate from level 30 to level 40. When gated, players must wait or pay to continue.

**Business hypothesis (pre-experiment intuition)**: fewer gating events → retention improves.

---

## 3. 🚨 Step one: experiment integrity check (SRM)

When any A/B test result comes in, **the first thing to do is not look at the metric — it's check the experiment itself**.

### Sample Ratio Mismatch (SRM) test

In theory, 50/50 random allocation. In practice:

| Group | Players | Share |
|---|---:|---:|
| gate_30 (control) | 44,700 | 49.56% |
| gate_40 (treatment) | 45,489 | 50.44% |

Chi-square test against 50/50: **χ²=6.90, p=0.0086 < 0.01 → SRM violation**

### Why this is serious

SRM violations typically indicate **a bug in randomization**, for example:
- A specific device / region / version only routes into one arm (sample bias)
- Bot traffic isn't filtered cleanly (affects one arm)
- Routing logic race condition (early requests don't reach one arm)

**Industry standard** (Microsoft, Google, Airbnb, etc.): **experiments with SRM p-value < 0.01 should not be trusted** until the root cause is found.

### What a PM should do

1. Ask engineering to debug the randomization service / SDK
2. Until SRM is fixed, **don't share results with leadership** (avoid decisions on broken data)
3. If the root cause is "a specific cohort got excluded," consider a sub-population analysis (only the stable subgroup)

---

## 4. If we ignore SRM and analyze anyway: three methods

### Method 1 — Frequentist 2-proportion z-test

| Metric | Control (gate_30) | Treatment (gate_40) | Diff | p-value | 95% CI | Cohen's h |
|---|---:|---:|---:|---:|---|---:|
| Day 1 retention | 44.82% | 44.23% | **-0.59pp** | 0.074 | [-1.24, +0.06] | -0.012 |
| Day 7 retention | 19.02% | 18.20% | **-0.82pp** | **0.0016** | [-1.33, -0.31] | -0.021 |

- **Day 1**: borderline non-significant (p=0.074), 95% CI contains 0
- **Day 7**: **statistically significant** (p=0.0016), 95% CI entirely below 0
- Cohen's h indicates "tiny effect" (< 0.2) for both, but with large samples even tiny effects can reach significance

### Method 2 — Bootstrap resampling (10,000 iterations)

Non-parametric, no distributional assumption. Resample 10,000 times and compute the difference for each metric:

![bootstrap](output/bootstrap_dist.png)

| Metric | Mean diff | 95% Bootstrap CI | P(gate_40 worse) |
|---|---:|---|---:|
| Day 1 retention | -0.59pp | [-1.23, +0.05]pp | **96.3%** |
| Day 7 retention | -0.82pp | [-1.33, -0.31]pp | **100%** |

**All 10,000 Day-7 bootstrap iterations show gate_40 worse** — this result is highly robust.

### Method 3 — Bayesian Beta-Binomial

Jeffreys prior `Beta(0.5, 0.5)`, 200,000 posterior samples:

![posterior](output/posterior.png)

| Metric | P(gate_40 better) | 95% Credible Interval |
|---|---:|---|
| Day 1 retention | **3.7%** | [-1.24, +0.06]pp |
| Day 7 retention | **0.1%** | [-1.33, -0.31]pp |

Bayesian gives the **direct probability** that "gate_40 is better" (Frequentist cannot interpret p-values this way).
**Day 7 has only a 0.1% probability that gate_40 is better** — for business decisions, this is effectively certainty: do not ship.

---

## 5. Retention comparison

![retention compare](output/retention_compare.png)

Caveat: "visually it looks like a small gap" can mislead. At Cookie Cats' scale (~100K daily installs, 1pp retention difference = 30,000 players/month), -0.82pp is not small at all.

---

## 6. Power Analysis (post-hoc)

| Metric | Observed power | MDE (80% power) |
|---|---:|---:|
| Day 1 retention | 0.43 (under-powered) | ±0.93pp |
| Day 7 retention | 0.89 (sufficient) | ±0.74pp |

- **Day 1 is under-powered** (only 43% chance to detect a 0.59pp difference) — its "non-significant" conclusion is likely a sample-size issue
- **Day 7 power is sufficient** → conclusion is trustworthy

For a future similar experiment, if PM wants to detect ±0.5pp, the sample needs at least **180,000 players per arm** (4× current).

---

## 7. PM decision recommendations

### For this experiment
1. **Don't ship gate_40**: 7-day retention is significantly worse, Bayesian P(better)=0.001
2. **Fix SRM**: go back, find the randomization bug, rerun after the fix
3. **Quadruple the sample on rerun**: only then does the experiment have power to detect 1pp-scale Day-1 differences

### On "why does moving the gate later make things worse"

The result contradicts business intuition, worth digging into with the PM / design team:

| Hypothesis | Why it might hold | How to validate |
|---|---|---|
| **The gate is a commitment device** | Being stuck creates "unfinished business," players return to continue | Compare long-term retention: gated players vs. non-gated players |
| **The gate is an IAP trigger point** | Level 30 is the prime "willing-to-pay" moment; moving to 40 misses the conversion | Look at ARPU / paid conversion rate (data not provided) |
| **The gate is a viral catalyst** | Stuck players go look up walkthroughs / ask friends → engagement lift | Check social activity / walkthrough search volume (data not provided) |

### Recommendations for the next experiment

1. **Test gate_35** — see if there's a sweet spot (linear extrapolation 30 → 40 got worse; 35 might also be wrong but needs to be tested)
2. **Test "remove the gate but add daily quests"** — replace forced gating with daily quests, preserve commitment without frustration
3. **Add cohort segmentation** — new players (Day 1-3) vs. veteran players may respond differently
4. **Add revenue metrics** — bad retention but high ARPU could still ship; current data doesn't allow this judgment

---

## 8. Why this project belongs on a resume

| What a PM hiring manager wants to see | How this project demonstrates it |
|---|---|
| Picks hard problems rather than hiding them | **Deliberately picked an SRM-fail case** to demo "can catch + can handle + can decide" |
| Questions the experiment design instead of trusting results blindly | Opens with SRM check, p=0.0086 |
| Cross-validates with multiple methods | Frequentist + Bootstrap + Bayesian triangulation |
| Distinguishes statistical significance from business significance | Cohen's h, MDE, Power all considered together |
| Treats overturned intuition as a gift, not a threat | Three hypotheses about "gate as commitment device" + validation paths |
| Provides executable next steps | gate_35, remove-gate + quests, segment analysis |

---

## 9. Limitations (honest disclosure)

1. **Only 14-day observation window** — 30/90-day retention effects untested
2. **Revenue not quantified** — if gate_40 retention is worse but ARPU is higher, the conclusion could reverse
3. **No segment analysis** — new vs. veteran players, free vs. paying users may respond differently
4. **`sum_gamerounds` has extreme outliers** (max=49,854 — clearly a bot or stress test) — this is why no t-test on gamerounds in this iteration
5. **Bayesian prior is Jeffreys (Beta(0.5, 0.5))** — uninformative; if historical priors are available, an informative prior would improve convergence

---

## 10. Technology stack

`Python` · `pandas` · `scipy.stats` · `statsmodels` · `numpy.random` · `matplotlib`

Statistical methods:
- `proportions_ztest` — 2-proportion z-test
- `proportion_confint` — Wilson score CI
- `bootstrap resampling` — np.random.choice (10K iterations)
- `Beta-Binomial conjugate` — Bayesian posterior with Jeffreys prior
- `Cohen's h` — standardized effect size for proportions
- `chi-square goodness-of-fit` — SRM check
- `zt_ind_solve_power` — power analysis for 2-proportion test

---

## How to run

```powershell
# 1. Clone repo
git clone https://github.com/kengkeng44/cookie-cats-ab-test.git
cd cookie-cats-ab-test

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download data from Kaggle (requires Kaggle API token)
kaggle datasets download -d yufengsui/mobile-games-ab-testing -p data --unzip

# 4. Run the analysis
python notebook/analysis.py
```

Outputs in `output/`:
- `summary.csv` — main statistical results
- `retention_compare.png` — D1/D7 retention comparison
- `bootstrap_dist.png` — Bootstrap difference distribution
- `posterior.png` — Bayesian posterior
- `gamerounds_dist.png` — game rounds distribution
- `decision.md` — PM decision document

---

## Data license

Source: [Mobile Games A/B Testing (Kaggle)](https://www.kaggle.com/datasets/yufengsui/mobile-games-ab-testing) · license status unknown (per Kaggle)
Project purpose: portfolio / educational, non-commercial

---

## Further reading

- [Diagnosing Sample Ratio Mismatch in Online Controlled Experiments — Microsoft Research](https://www.microsoft.com/en-us/research/group/experimentation-platform-exp/articles/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments/)
- [Trustworthy Online Controlled Experiments (book)](https://experimentguide.com/) — Kohavi, Tang, Xu
- [Bayesian A/B Testing — Evan's Awesome A/B Tools](https://www.evanmiller.org/bayesian-ab-testing.html)
- [My Olist e-commerce portfolio project](https://github.com/kengkeng44/olist-project)
