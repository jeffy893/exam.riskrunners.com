# Actuarial Context — FM & P Scenario and Methodology Reference

**Repo:** exam.riskrunners.com
**Source:** 2 FM (Financial Mathematics) + 2 P (Probability) practice exams under `data/fm/` and `data/p/` (30 questions each, LLM-generated for the RiskRunners club at University of Arizona).
**Purpose:** This file distills the *types of scenarios* the actuarial exams pose and the *solution methodologies* used to solve them, so those methods can be pulled into real-world contexts where they fit — procurement fulfillment, ISO 31010 risk management, and structured deal negotiation.

> This is not a study guide for passing the exams. It is a *lens library*. Each method below is a way of converting an uncertain real-world situation into a number you can act on. The through-line that makes this useful outside of exam-taking is the actuary's core equation: **Premium = Rate × Exposure**, where *Rate* is the financial-mathematics side (FM) and *Exposure* is the probability side (P). Everything here feeds one of those two terms.

---

## How to use this file

1. **Recognize the scenario.** Each method has a "You'll see this when…" trigger. Match your real situation to the trigger.
2. **Apply the recipe.** Each method has a compact, hand-computable recipe (the same one the exam solutions use).
3. **Convert to a decision.** Map the output to a rate, a reserve, a probability of ruin, a price, or an option value.
4. **Cross-reference ISO 31010.** Where a Street Math / ISO 31010 technique overlaps (Monte Carlo, Decision Tree, Markov), it is noted. The actuarial method is the *closed-form* version; the ISO technique is the *simulated* version. Use closed-form to sanity-check the simulation.

---

# PART I — FM (Financial Mathematics)

FM is the **Rate** side of `Premium = Rate × Exposure`. It answers: *what is a stream of money worth, moved through time?* Every FM scenario is a cash-flow-timing problem in disguise.

**Master variables**
- `i` = effective interest rate per period
- `v = 1/(1+i)` = discount factor (one period)
- `d = i/(1+i)` = discount rate (used for annuities-due)
- `n` = number of periods
- `a(n|i) = (1 - v^n)/i` = PV of an annuity-immediate (payments at period *end*)
- `s(n|i) = ((1+i)^n - 1)/i` = FV of an annuity-immediate
- Annuity-**due** (payments at period *start*): multiply the immediate factor by `(1+i)`

---

## FM-1. Time Value of Money

**You'll see this when…** a single lump sum must be moved forward or backward in time, or a quoted rate must be converted between compounding conventions.

**Scenario framings in the exams:** a data center saving today for a server replacement in 5 years; a car buyer converting a quoted effective annual rate to a nominal-monthly rate.

**Recipes**
- Present value of a future amount: `PV = FV · (1+i)^(-n)`
- Future value: `FV = PV · (1+i)^n`
- Nominal ↔ effective: `(1 + i) = (1 + i^(m)/m)^m`, so `i^(m) = m·[(1+i)^(1/m) − 1]`.

**Converts to:** the discount factor you apply to any deferred cash flow. This is the atomic operation behind every other FM method.

---

## FM-2. Annuities (Immediate, Due, Perpetuities)

**You'll see this when…** a *level* stream of payments occurs at regular intervals — a lease, a subscription, a scholarship, a maintenance obligation, a savings plan.

**Scenario framings:** monthly lease payments on a delivery fleet; quarterly reserve-fund deposits; a university scholarship paid at the start of each year (annuity-due); perpetual subscription revenue or perpetual maintenance cost (perpetuity).

**Recipes**
- PV annuity-immediate: `PV = PMT · a(n|i)`
- FV annuity-immediate: `FV = PMT · s(n|i)`
- Annuity-due: multiply the immediate result by `(1+i)`
- Perpetuity-immediate: `PV = PMT / i`
- Perpetuity-due: `PV = PMT · (1+i)/i`
- **Sub-annual timing:** convert the rate to the payment period first (`i_month = i^(12)/12`, or `i_month = (1+i)^(1/12) − 1` for an effective annual rate).

**Converts to:** the fair upfront price of any recurring commitment. In procurement, this is how you value a multi-period supply contract or a financing schedule.

---

## FM-3. Loans and Amortization

**You'll see this when…** a borrowed principal is retired by level payments, and you need either the payment, the remaining balance, or the split between interest and principal.

**Scenario framings:** a fleet financed over 6 years; a pension plan amortizing an unfunded liability; a retiree drawing down a fund over 25 years; an insurer's reserve depleted by benefit payments.

**Recipes**
- Level payment: `PMT = Loan / a(n|i)`
- **Outstanding balance (prospective — preferred):** `OB_k = PMT · a(n−k|i)` = PV of the *remaining* payments.
- **Outstanding balance (retrospective):** `OB_k = Loan·(1+i)^k − PMT·s(k|i)`.
- Interest in payment k+1: `OB_k · i`. Principal repaid: `PMT − OB_k·i`.

> **Exam caution:** several exam "solutions" show arithmetic that drifts from the stated answer key. Trust the *method*, recompute the number. The prospective and retrospective methods must agree — if they don't, you made a rounding or period-count error.

**Converts to:** the true carrying cost of financed inventory or equipment, and the payoff figure at any point (useful when you want to exit a financed position early).

---

## FM-4. Bonds

**You'll see this when…** an instrument pays periodic coupons and returns a redemption value at maturity, priced to a required yield.

**Scenario framings:** equipment financed via a bond redeemable at 103% of face; a scholarship trust valuing a bond; a convertible bond priced to an investor's required yield.

**Recipe**
- Price: `P = (Fr) · a(n|i) + C · v^n`
  - `Fr` = coupon per period = face × coupon-rate/period
  - `C` = redemption value (e.g. `1.03 × face`)
  - `i` = yield per period (semiannual coupons → `i = annual_yield/2`, `n = years×2`)
- Premium/discount: if coupon rate > yield → priced at a **premium**; if <, at a **discount**.

**Converts to:** the mechanics of pricing *any* fixed-claim-plus-terminal-value asset. A procurement contract with periodic deliveries and a final settlement is structurally a bond.

---

## FM-5. General Cash Flows, Portfolios & Duration

**You'll see this when…** cash flows are irregular, or you need the *timing sensitivity* of a stream, or a fund's realized yield.

**Scenario framings:** Macaulay duration of a level cash-flow stream; dollar-weighted (money-weighted) yield of a fund that took a mid-year deposit.

**Recipes**
- **Macaulay duration:** `D = [Σ t·v^t·CF_t] / [Σ v^t·CF_t]` — the PV-weighted average time to payment. It is the stream's "center of mass" in time and its first-order sensitivity to rate changes.
- **Dollar-weighted yield (simple interest):** `i = I / (A + Σ C_t·(1−t))`, where `I = End − Begin − ΣDeposits`, `A` = starting balance, `C_t` = contribution at time `t` (fraction of year).
- **Time-weighted yield:** chain the sub-period growth factors; strips out the timing of external cash flows.

**Converts to:** *duration* is the bridge to reserving — it tells you how exposed a liability schedule is to rate movement, and how to immunize it by matching asset duration. *Dollar-weighted yield* is how you score the actual return on capital you deployed into a deal.

---

# PART II — P (Probability)

P is the **Exposure** side of `Premium = Rate × Exposure`. It answers: *how likely, and how variable, is the event?* Every P scenario is about quantifying uncertainty before it is priced.

**Master ideas**
- Discrete PMF sums to 1; continuous PDF integrates to 1.
- `E[X]` = long-run average; `Var(X) = E[X²] − (E[X])²` = spread.
- Conditioning updates a probability given new information.

---

## P-1. General Probability (Unions, Conditional, Bayes')

**You'll see this when…** you combine events, or you update a belief after observing evidence, or you back out a source given an outcome.

**Scenario framings:** a visitor who carts *or* subscribes (union); default given high-risk classification (conditional); which supplier/portfolio a defective unit or adequate reserve came from (Bayes').

**Recipes**
- Union: `P(A∪B) = P(A) + P(B) − P(A∩B)`
- Conditional: `P(A|B) = P(A∩B) / P(B)`; so `P(A∩B) = P(A|B)·P(B)`
- Law of total probability: `P(D) = Σ P(D|Hᵢ)·P(Hᵢ)`
- **Bayes':** `P(Hⱼ|D) = P(D|Hⱼ)·P(Hⱼ) / Σ P(D|Hᵢ)·P(Hᵢ)`

**Converts to:** *supplier/source reliability updating* — given a defect or a late delivery, what's the probability it came from supplier A vs B? This is directly a procurement quality-control lens and mirrors ISO 31010 Bayesian analysis.

---

## P-2. Univariate Random Variables

**You'll see this when…** a single uncertain quantity follows a recognizable pattern — counts, waiting times, successes-in-trials, or a bounded uniform range.

### Key distributions and their triggers

| Distribution | Trigger | PMF / PDF | E[X] | Var(X) |
|---|---|---|---|---|
| **Poisson(λ)** | count of events in a fixed interval (orders/hour, complaints/day) | `P(X=k)=e^(−λ)λ^k/k!` | λ | λ |
| **Binomial(n,p)** | count of successes in n independent trials (defaults among bonds, premium orders among customers) | `C(n,k)p^k(1−p)^(n−k)` | np | np(1−p) |
| **Geometric(p)** | trial of the *first* success (first accepted offer, month funding lands) | `(1−p)^(k−1)·p` | 1/p | (1−p)/p² |
| **Exponential(θ)** | waiting time / time-to-event; **memoryless** (time to first repair, time between calls) | pdf `(1/θ)e^(−t/θ)`; `P(T>t)=e^(−t/θ)` | θ | θ² |
| **Continuous Uniform[a,b]** | equally likely over a bounded range (rod lengths, time between calls) | `1/(b−a)` | (a+b)/2 | (b−a)²/12 |

**Recipes for common asks**
- Expected value of a discrete cost: `E[Cost] = Σ (value · probability)`, or `E[cX] = c·E[X]`.
- Exponential memorylessness: `P(T>s+t | T>s) = P(T>t)` — a stated "given no event in the first s minutes" clause is often a red herring.
- Exponential CDF (probability event happens *by* t): `F(t) = 1 − e^(−t/θ)`.

**Converts to:** the frequency and timing side of loss modeling — how often does a machine fail, a contract slip, a supplier miss? Poisson/exponential are the workhorses of failure-rate and arrival modeling (and connect to ISO 31010 Markov/queuing techniques).

---

## P-3. Multivariate Random Variables (Covariance, Correlation, Variance of Sums)

**You'll see this when…** two uncertain quantities move together and you need the risk of their *combination*.

**Scenario framings:** total variance of two claim reserves; variance of combined maintenance cost across vehicle types; covariance of rental income across two neighborhoods; correlation between loan amount and term.

**Recipes**
- Covariance: `Cov(X,Y) = E[XY] − E[X]·E[Y]`
- `Cov(X,Y) = ρ · SD(X) · SD(Y)`  (from a correlation ρ)
- **Variance of a sum:** `Var(X+Y) = Var(X) + Var(Y) + 2·Cov(X,Y)`
- Difference: `Var(X−Y) = Var(X) + Var(Y) − 2·Cov(X,Y)`
- Standard deviation of the total = `√Var(X+Y)`.

> **The single most important line for portfolio thinking:** the `2·Cov` term is where diversification lives. Negative covariance shrinks combined risk; positive covariance amplifies it. This is why you source interoperable/uncorrelated products, and why a captive that pools uncorrelated risks needs less capital than the sum of parts.

**Converts to:** portfolio and pooling logic — the mathematical reason a captive insurer or a diversified procurement book is less risky than its components, and the reason to prefer products whose demand shocks are uncorrelated.

---

# PART III — The Synthesis Layer (why these methods travel)

The exams are toy scenarios, but their *methods* are the conversion machinery between a modeled risk and a dollar figure. Mapped onto the RiskRunners / Integral Mass ecosystem:

| Actuarial method | Feeds the term… | Real-world home |
|---|---|---|
| Annuities, bonds, TVM | **Rate** | pricing a multi-period supply/financing contract |
| Loan amortization, duration | **Rate** | carrying cost of financed inventory; immunizing a liability schedule |
| Poisson / exponential | **Exposure** | supplier failure & delivery-slip frequency |
| Binomial / geometric | **Exposure** | how many units defect; when the first win lands |
| Bayes' | **Exposure** | updating supplier reliability from observed defects |
| Covariance / Var-of-sum | **Exposure** | portfolio pooling; diversifying a procurement book or a captive |

**The bridge that was missing:** *risk modeling* (ISO 31010, in `value.integralmass.com`) identifies and structures the risk factors qualitatively; *actuarial FM/P* converts those structured factors into a **rate** (FM) applied to a quantified **exposure** (P), producing a **premium/price**. `Premium = Rate × Exposure` is the exchange rate between the risk-management world and the finance world.

**Relationship to the ISO 31010 techniques (Street Math):**
- Actuarial closed-form ↔ ISO 31010 simulation are two views of the same estimate. Use Monte Carlo (ISO) when the distribution is messy; use the closed-form annuity/expected-value formula (actuarial) to sanity-check the simulation's center.
- Markov / queuing (ISO) generalizes the Poisson/exponential arrival models (P).
- Decision Tree / Game Theory (ISO) is where option-style, negotiate-within-constraints thinking (below) becomes a computable payoff.

**Relationship to options (the Cashflow board-game mechanic):**
An option is `Premium` paid today for the `right` (not obligation) to transact at a `strike` before an `expiry`. That is `Premium = Rate × Exposure` with the exposure being the probability the option finishes in-the-money and the rate being the discounting of the eventual payoff. Every "I forward you the money as a premium, and I hold the right to buy the product at a guaranteed price" structure in procurement is a **call option on inventory**. See `scenarios.md` for the concrete mappings.

---

*Maintained for exam.riskrunners.com. Companion file: `scenarios.md` (real-world applications of this context).*
