# Applicable Scenarios — Where the Actuarial Context Lives in the Real World

**Companion to:** `context.md`
**Purpose:** A working list of real-world scenarios where the FM/P methodologies distilled from the exams are the right lens. Organized so you can scan for a situation you're actually in, then jump to the method that solves it.

> Trying to enumerate *every* scenario is, as you said, in vain — the point is not an exhaustive list, it's a **starter map** you extend as you meet each one. Each entry names the situation, the actuarial method, and the decision it produces. The organizing spine is `Premium = Rate × Exposure`: FM methods price the *Rate*, P methods size the *Exposure*.

---

## A. Procurement Fulfillment (the Item Assure pilot)

These are the scenarios that show up when you're standing up the procurement-fulfillment business — finding demand, pricing a fill, and deciding whether to put money down.

| # | Real-world scenario | Method (context.md ref) | Decision it produces |
|---|---|---|---|
| A1 | You front cash to a manufacturer today; goods deliver and sell over the next N months. | TVM + Annuities (FM-1, FM-2) | Is the discounted sell-through worth more than the cash out today? |
| A2 | A supply contract pays you on a delivery schedule with a final settlement. | Bond pricing (FM-4) — coupons = deliveries, redemption = settlement | Fair price to pay for the contract at your required yield. |
| A3 | You finance inventory or equipment to fulfill a large order. | Loan amortization + outstanding balance (FM-3) | Payment size, true carrying cost, and early-exit payoff. |
| A4 | How often will a supplier miss a delivery window this quarter? | Poisson / exponential (P-2) | Expected slips → buffer stock and penalty-clause sizing. |
| A5 | Out of a production run, how many units come back defective? | Binomial (P-2) | Expected defect count → return reserve and QC gate. |
| A6 | A defective (or late) unit arrived — which of two suppliers is it more likely from? | Bayes' (P-1) | Updated supplier reliability → where to tighten inspection. |
| A7 | You source two products (or two suppliers) and want the risk of the combined book. | Covariance / Var-of-sum (P-3) | Prefer low/negative-covariance pairs; size combined buffer. |
| A8 | "How many units will actually sell?" from a rough range. | Continuous Uniform / expected value (P-2) | Center + spread of sell-through for the go/no-go. |
| A9 | Which prospect/RFP converts first if you pursue them in sequence? | Geometric (P-2) | Expected number of pursuits before the first win → pipeline sizing. |
| A10 | Timing sensitivity of a multi-delivery contract to financing-rate moves. | Macaulay duration (FM-5) | How exposed the deal is to rate changes; whether to lock financing. |
| A11 | What return did I actually earn on the capital I deployed into a fill? | Dollar-weighted yield (FM-5) | Realized IRR-style score to compare deals (ties to value.riskrunners.com). |

---

## B. Option-Structured Deals (the Cashflow board-game mechanic, applied)

Your Cashflow negotiations are option structures. Formalized, they price cleanly. Each is `Premium` today for a `right` at a `strike` before an `expiry` — `Premium = Rate × Exposure`.

| # | Cashflow-style move | Option form | Actuarial handle |
|---|---|---|---|
| B1 | "I forward you $100k premium to buy 20,000 units at $5; I hold the right to buy them back at a guaranteed $10." | **Call option on inventory** | Exposure = P(market clears above strike); Rate = discount the payoff. |
| B2 | "You put the down payment with my premium; I hold a call on the property/asset at a strike." | Call on a financed asset (the duplex deal) | Value the guaranteed spread as PV of a contingent cash flow (FM-1). |
| B3 | "I'm obligated to buy what you sell me if you exercise" (you took the premium). | **Sold put** — you're the risk-taker | Reserve = strike × P(assigned). This is *literally underwriting*. |
| B4 | "I have the right to sell to you at a set price" (hoping price drops). | **Bought put** — downside hedge | Insurance on your own inventory value. |
| B5 | Back-to-back: buy a call from one party, sell an identical call to another. | Immunized/offset book | The `2·Cov` intuition (P-3): matched legs net the exposure to zero, you keep the spread. |

> **The insight to keep:** selling an option is underwriting. You collect a premium now and hold a contingent obligation. Sizing that obligation — `strike × probability of exercise`, discounted — is exactly reserving. This is the tangible game you were looking for: **you can practice being the underwriter in procurement deals the same way you practice negotiating in Cashflow.**

---

## C. ISO 31010 Risk Management → Rate (the value.integralmass.com clients)

Where the Street Math sessions modeled risk qualitatively, these scenarios convert that structured risk into a number. The ~10 client sessions (Scott, Ken, Neel, Zac, and others) each produced a risk structure; actuarial math turns the structure into a rate/reserve.

| # | From a client's risk model… | Actuarial conversion | Output |
|---|---|---|---|
| C1 | A Bow Tie identified failure modes with rough frequencies. | Poisson/exponential frequency + expected loss (P-2) | Expected annual loss → the pure premium. |
| C2 | A Monte Carlo produced a loss distribution. | Closed-form E[X], Var(X) sanity check (P-2/P-3) | Confirm the sim's center/spread; derive a loaded rate. |
| C3 | A client faces two correlated risks. | Covariance / Var-of-sum (P-3) | Combined reserve; diversification credit. |
| C4 | A decision tree with staged, discounted payoffs. | TVM discounting of each branch (FM-1) | Risk-adjusted NPV per branch. |
| C5 | "Given the loss happened, what most likely caused it?" | Bayes' (P-1) | Posterior over causes → where to spend on controls. |
| C6 | A liability that pays out over years. | Annuity PV + duration (FM-2, FM-5) | Present value of the liability and its rate sensitivity → how to fund/immunize it. |

---

## D. The Captive Insurance End-Game

Your stated long arc: build a ~$1M-revenue business, then form a captive to capture its risk and hire an actuary, a captive manager, and an administrator. These scenarios are the actuary's job you'd be commissioning — and understanding them is what lets you *direct* that actuary rather than defer to them.

| # | Captive scenario | Method | Why it matters to you |
|---|---|---|---|
| D1 | Set the premium the operating business pays the captive. | `Premium = Rate × Exposure` (all of FM + P) | The core transfer price; must be defensible. |
| D2 | Hold reserves for claims that may arrive. | Expected value + variance loading (P-2/P-3) | How much capital the captive must hold. |
| D3 | Pool multiple uncorrelated business risks. | Covariance / Var-of-sum (P-3) | The diversification that makes a captive efficient. |
| D4 | Invest reserves to match liability timing. | Duration matching / immunization (FM-5) | Asset-liability management; avoid rate mismatch. |
| D5 | Value the stream of premiums vs. expected claims. | Annuity/bond PV (FM-2, FM-4) | Whether the captive is solvent and worth it. |

---

## E. The Financial-Advising Software You're Leading

The tool that reports *probability of financial success* without giving SEC-regulated advice is a direct P-application.

| # | Scenario | Method | Output |
|---|---|---|---|
| E1 | "What's the probability this person hits their goal?" | Distribution modeling + CDF (P-2) | A probability, not advice — stays on the right side of the line. |
| E2 | Runway: months of survival at an uncertain burn rate. | Exponential / expected value (P-2) | P(survive past month t) — exactly the "startup runway" exam scenario. |
| E3 | Combining income and expense uncertainty. | Var-of-sum (P-3) | Spread of net cash flow → confidence bands. |

---

## How to extend this list

When you hit a new real situation, ask two questions:
1. **What's uncertain, and does it look like a known distribution?** (count → Poisson/Binomial; waiting → exponential; range → uniform) → that sizes **Exposure**.
2. **What's the money, and when does it move?** (level stream → annuity; principal + terminal → bond; single sum → TVM) → that prices the **Rate**.

Multiply them. Add a new row to the table above. Over time this file becomes your personal `Premium = Rate × Exposure` playbook — the "little intelligent investor, but for procurement" you described.

---

*Maintained for exam.riskrunners.com. Companion file: `context.md` (methodology reference).*
