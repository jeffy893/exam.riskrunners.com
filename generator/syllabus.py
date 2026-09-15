"""
syllabus.py — official SOA topic weightings and question allocation.

Single source of truth for how many of the 30 questions come from each syllabus
topic group, so generated exams mirror the real exam's emphasis instead of
sampling every recipe uniformly.

Weight ranges are transcribed from the current SOA syllabi:
  * Exam FM — 2026-08 syllabus
      https://www.soa.org/globalassets/assets/files/edu/2026/spring/syllabi/2026-08-exam-fm-syllabus.pdf
  * Exam P  — 2026-05 syllabus
      https://www.soa.org/globalassets/assets/files/edu/2026/spring/syllabi/2026-05-exam-p-syllabus.pdf

The SOA notes that on any individual exam the weight of a topic may fall outside
the published range, so we allocate to the RANGE MIDPOINT and then adjust the
rounding remainder toward the largest topics. (Weightings sourced from the SOA
syllabi cited above; content was rephrased for compliance.)
"""

# Each topic group: (published low %, published high %). Midpoint drives allocation.
WEIGHTS = {
    "FM": {
        "Time Value of Money":              (5, 15),
        "Annuities":                        (20, 30),
        "Loans and Amortization":           (15, 25),
        "Bonds":                            (15, 25),
        "General Cash Flows and Portfolios":(20, 30),
    },
    "P": {
        "General Probability":              (23, 30),
        "Univariate Random Variables":      (44, 50),
        "Multivariate Random Variables":    (23, 30),
    },
}

# Map each verifiable LLM recipe (llm_authoring.py) to its syllabus topic group.
RECIPE_GROUPS = {
    "FM": {
        "accumulate": "Time Value of Money",
        "present_value": "Time Value of Money",
        "nominal_from_effective": "Time Value of Money",
        "effective_from_nominal": "Time Value of Money",
        "annuity_immediate_pv": "Annuities",
        "annuity_due_pv": "Annuities",
        "annuity_immediate_fv": "Annuities",
        "annuity_due_fv": "Annuities",
        "perpetuity_immediate": "Annuities",
        "perpetuity_due": "Annuities",
        "loan_payment": "Loans and Amortization",
        "outstanding_balance": "Loans and Amortization",
        "bond_price": "Bonds",
        # General Cash Flows / Portfolios / ALM is authored free-form (no fixed
        # numeric recipe); handled via the template builders + LLM prose. See
        # GENERAL_CF_RECIPES below for recipes reused to fill that group.
    },
    "P": {
        "bayes_two_source": "General Probability",
        "conditional": "General Probability",
        "union": "General Probability",
        "binomial_pmf": "Univariate Random Variables",
        "poisson_pmf": "Univariate Random Variables",
        "geometric_pmf": "Univariate Random Variables",
        "exponential_survival": "Univariate Random Variables",
        "exponential_cdf": "Univariate Random Variables",
        "uniform_variance": "Univariate Random Variables",
        "uniform_mean": "Univariate Random Variables",
        "expected_value_discrete": "Univariate Random Variables",
        "covariance": "Multivariate Random Variables",
        "variance_sum": "Multivariate Random Variables",
    },
}

# Map each template builder function name (content_fm/content_p) to its group,
# so the offline fallback honors the same weighting.
TEMPLATE_GROUPS = {
    "FM": {
        "build_tvm_accumulation": "Time Value of Money",
        "build_tvm_present_value": "Time Value of Money",
        "build_tvm_nominal_rate": "Time Value of Money",
        "build_annuity_immediate_pv": "Annuities",
        "build_annuity_due_fv": "Annuities",
        "build_perpetuity": "Annuities",
        "build_increasing_annuity": "Annuities",
        "build_loan_payment": "Loans and Amortization",
        "build_loan_outstanding_balance": "Loans and Amortization",
        "build_loan_interest_principal": "Loans and Amortization",
        "build_bond_price": "Bonds",
        "build_bond_premium_discount": "Bonds",
        "build_macaulay_duration": "General Cash Flows and Portfolios",
        "build_dollar_weighted_yield": "General Cash Flows and Portfolios",
    },
    "P": {
        "build_bayes": "General Probability",
        "build_inclusion_exclusion": "General Probability",
        "build_conditional": "General Probability",
        "build_binomial": "Univariate Random Variables",
        "build_poisson": "Univariate Random Variables",
        "build_geometric": "Univariate Random Variables",
        "build_exponential": "Univariate Random Variables",
        "build_uniform_variance": "Univariate Random Variables",
        "build_expected_value_discrete": "Univariate Random Variables",
        "build_covariance": "Multivariate Random Variables",
        "build_variance_sum": "Multivariate Random Variables",
    },
}

# For FM's "General Cash Flows, Portfolios & ALM" group there is no closed-form
# verifiable recipe among our set, so when the LLM path needs a question from
# that group we reuse duration/portfolio-flavored recipes that ARE verifiable.
# We approximate it with bond_price (portfolio valuation flavor) + the template
# builders (duration, dollar-weighted yield). Allocation still counts the group.
GENERAL_CF_RECIPES = {
    "FM": ["bond_price"],  # verifiable stand-in; templates cover duration/yield
}


def _midpoint(rng_pair):
    return (rng_pair[0] + rng_pair[1]) / 2.0


def allocate(track, n_questions):
    """Return {group: count} summing to n_questions, proportional to the
    syllabus midpoints, with the rounding remainder given to the largest groups.
    """
    groups = WEIGHTS[track]
    mids = {g: _midpoint(w) for g, w in groups.items()}
    total_mid = sum(mids.values())

    # initial floor allocation
    raw = {g: (mids[g] / total_mid) * n_questions for g in groups}
    alloc = {g: int(raw[g]) for g in groups}
    assigned = sum(alloc.values())
    remaining = n_questions - assigned

    # distribute leftover to groups with the largest fractional parts
    frac_order = sorted(groups, key=lambda g: (raw[g] - int(raw[g])), reverse=True)
    i = 0
    while remaining > 0:
        alloc[frac_order[i % len(frac_order)]] += 1
        remaining -= 1
        i += 1
    return alloc


def weight_label(track, group):
    lo, hi = WEIGHTS[track][group]
    return f"{lo}-{hi}%"
