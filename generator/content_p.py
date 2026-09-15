"""
Content bank + problem builders for the SOA Exam P (Probability).

Same builder contract as content_fm.py: each function takes a random.Random and
returns a dict with topic / stem / correct / unit / round / solution. The
generator converts `correct` into 5 lettered choices.

Topics follow the SOA P syllabus:
  - General Probability (sets, conditional probability, Bayes)
  - Univariate Random Variables (discrete + continuous, moments)
  - Multivariate Random Variables (joint, covariance)
"""

import math
from math import comb, exp, factorial


def _fmt(x, nd=2):
    return f"{x:,.{nd}f}"


# --------------------------------------------------------------------------
# General Probability
# --------------------------------------------------------------------------
def build_bayes(rng):
    # Two machines producing items with defect rates
    p1 = rng.choice([0.4, 0.5, 0.6, 0.7])
    p2 = round(1 - p1, 2)
    d1 = rng.choice([0.02, 0.03, 0.04, 0.05])
    d2 = rng.choice([0.06, 0.08, 0.10, 0.12])
    num = p1 * d1
    denom = p1 * d1 + p2 * d2
    post = num / denom
    return {
        "topic": "General Probability",
        "stem": (
            f"Machine A produces {p1*100:.0f}% of a factory's output with a defect rate "
            f"of {d1*100:.0f}%. Machine B produces the remaining {p2*100:.0f}% with a "
            f"defect rate of {d2*100:.0f}%. An item selected at random is found to be "
            f"defective. Calculate the probability that it came from Machine A."
        ),
        "correct": post,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"By Bayes' Theorem, P(A|D) = P(A)P(D|A) / [P(A)P(D|A) + P(B)P(D|B)].\n"
            f"Numerator = {p1:.2f} x {d1:.2f} = {_fmt(num,5)}\n"
            f"Denominator = {p1:.2f} x {d1:.2f} + {p2:.2f} x {d2:.2f} = {_fmt(denom,5)}\n"
            f"P(A|D) = {_fmt(num,5)} / {_fmt(denom,5)} = {_fmt(post,4)}."
        ),
    }


def build_inclusion_exclusion(rng):
    pa = rng.choice([0.3, 0.4, 0.5, 0.55])
    pb = rng.choice([0.3, 0.35, 0.45, 0.5])
    pab = rng.choice([0.1, 0.15, 0.2, 0.25])
    p_union = pa + pb - pab
    return {
        "topic": "General Probability",
        "stem": (
            f"For events A and B, P(A) = {pa:.2f}, P(B) = {pb:.2f}, and "
            f"P(A and B) = {pab:.2f}. Calculate P(A or B)."
        ),
        "correct": p_union,
        "unit": "probability",
        "round": 3,
        "solution": (
            f"By inclusion-exclusion, P(A or B) = P(A) + P(B) - P(A and B).\n"
            f"P(A or B) = {pa:.2f} + {pb:.2f} - {pab:.2f} = {_fmt(p_union,3)}."
        ),
    }


def build_conditional(rng):
    pab = rng.choice([0.12, 0.15, 0.2, 0.24])
    pb = rng.choice([0.3, 0.4, 0.5, 0.6])
    cond = pab / pb
    return {
        "topic": "General Probability",
        "stem": (
            f"For events A and B, P(A and B) = {pab:.2f} and P(B) = {pb:.2f}. "
            f"Calculate P(A | B)."
        ),
        "correct": cond,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"By definition, P(A|B) = P(A and B) / P(B).\n"
            f"P(A|B) = {pab:.2f} / {pb:.2f} = {_fmt(cond,4)}."
        ),
    }


# --------------------------------------------------------------------------
# Discrete distributions
# --------------------------------------------------------------------------
def build_binomial(rng):
    n = rng.randint(6, 12)
    p = rng.choice([0.2, 0.25, 0.3, 0.4, 0.5])
    k = rng.randint(2, n - 2)
    prob = comb(n, k) * p ** k * (1 - p) ** (n - k)
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"A random variable X follows a binomial distribution with n = {n} trials "
            f"and success probability p = {p:.2f}. Calculate P(X = {k})."
        ),
        "correct": prob,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"For a binomial, P(X=k) = C(n,k) p^k (1-p)^(n-k).\n"
            f"P(X={k}) = C({n},{k}) x {p:.2f}^{k} x {1-p:.2f}^{n-k}\n"
            f"= {comb(n,k)} x {_fmt(p**k,6)} x {_fmt((1-p)**(n-k),6)} = {_fmt(prob,4)}."
        ),
    }


def build_poisson(rng):
    lam = rng.choice([1.5, 2, 2.5, 3, 4, 5])
    k = rng.randint(1, 5)
    prob = exp(-lam) * lam ** k / factorial(k)
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"The number of claims X in a month follows a Poisson distribution with "
            f"mean {lam:.1f}. Calculate P(X = {k})."
        ),
        "correct": prob,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"For a Poisson, P(X=k) = e^(-lambda) lambda^k / k!.\n"
            f"P(X={k}) = e^(-{lam:.1f}) x {lam:.1f}^{k} / {k}!\n"
            f"= {_fmt(exp(-lam),6)} x {_fmt(lam**k,4)} / {factorial(k)} = {_fmt(prob,4)}."
        ),
    }


def build_geometric(rng):
    p = rng.choice([0.2, 0.25, 0.3, 0.4])
    k = rng.randint(2, 5)
    # P(first success on trial k) = (1-p)^(k-1) p
    prob = (1 - p) ** (k - 1) * p
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"Independent trials each succeed with probability {p:.2f}. Calculate the "
            f"probability that the first success occurs on trial {k}."
        ),
        "correct": prob,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"For a geometric distribution, P(X=k) = (1-p)^(k-1) p.\n"
            f"P(X={k}) = {1-p:.2f}^{k-1} x {p:.2f} = {_fmt((1-p)**(k-1),6)} x {p:.2f} "
            f"= {_fmt(prob,4)}."
        ),
    }


# --------------------------------------------------------------------------
# Continuous distributions & moments
# --------------------------------------------------------------------------
def build_exponential(rng):
    mean = rng.choice([2, 3, 4, 5, 10])
    t = rng.randint(1, mean)
    prob = exp(-t / mean)
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"The lifetime of a component (in years) follows an exponential distribution "
            f"with mean {mean}. Calculate the probability that the component lasts more "
            f"than {t} year(s)."
        ),
        "correct": prob,
        "unit": "probability",
        "round": 4,
        "solution": (
            f"For an exponential with mean theta, P(X > t) = e^(-t/theta).\n"
            f"P(X > {t}) = e^(-{t}/{mean}) = {_fmt(prob,4)}."
        ),
    }


def build_uniform_variance(rng):
    a = rng.choice([0, 1, 2, 5])
    b = a + rng.choice([4, 6, 8, 10, 12])
    var = (b - a) ** 2 / 12
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"A random variable X is uniformly distributed on the interval "
            f"[{a}, {b}]. Calculate the variance of X."
        ),
        "correct": var,
        "unit": "number",
        "round": 4,
        "solution": (
            f"For a uniform on [a, b], Var(X) = (b - a)^2 / 12.\n"
            f"Var(X) = ({b} - {a})^2 / 12 = {(b-a)**2} / 12 = {_fmt(var,4)}."
        ),
    }


def build_expected_value_discrete(rng):
    # discrete rv with 3 outcomes
    vals = sorted(rng.sample([0, 1, 2, 3, 4, 5, 10], 3))
    probs = rng.choice([[0.2, 0.3, 0.5], [0.25, 0.25, 0.5], [0.3, 0.3, 0.4], [0.5, 0.3, 0.2]])
    ev = sum(v * p for v, p in zip(vals, probs))
    rows = ", ".join(f"P(X={v})={p:.2f}" for v, p in zip(vals, probs))
    terms = " + ".join(f"{v}x{p:.2f}" for v, p in zip(vals, probs))
    return {
        "topic": "Univariate Random Variables",
        "stem": (
            f"A discrete random variable X has the following distribution: {rows}. "
            f"Calculate E[X]."
        ),
        "correct": ev,
        "unit": "number",
        "round": 3,
        "solution": (
            f"E[X] = sum x P(X=x).\n"
            f"E[X] = {terms} = {_fmt(ev,3)}."
        ),
    }


# --------------------------------------------------------------------------
# Multivariate
# --------------------------------------------------------------------------
def build_covariance(rng):
    ex = rng.choice([2, 3, 4, 5])
    ey = rng.choice([1, 2, 3, 4])
    exy = ex * ey + rng.choice([1, 2, 3, -1, -2])
    cov = exy - ex * ey
    return {
        "topic": "Multivariate Random Variables",
        "stem": (
            f"For random variables X and Y, E[X] = {ex}, E[Y] = {ey}, and "
            f"E[XY] = {exy}. Calculate Cov(X, Y)."
        ),
        "correct": cov,
        "unit": "number",
        "round": 2,
        "solution": (
            f"Cov(X, Y) = E[XY] - E[X]E[Y].\n"
            f"Cov(X, Y) = {exy} - {ex} x {ey} = {_fmt(cov,2)}."
        ),
    }


def build_variance_sum(rng):
    vx = rng.choice([4, 9, 16, 25])
    vy = rng.choice([1, 4, 9, 16])
    cov = rng.choice([-2, 0, 1, 2, 3])
    var_sum = vx + vy + 2 * cov
    return {
        "topic": "Multivariate Random Variables",
        "stem": (
            f"For random variables X and Y, Var(X) = {vx}, Var(Y) = {vy}, and "
            f"Cov(X, Y) = {cov}. Calculate Var(X + Y)."
        ),
        "correct": var_sum,
        "unit": "number",
        "round": 2,
        "solution": (
            f"Var(X + Y) = Var(X) + Var(Y) + 2 Cov(X, Y).\n"
            f"Var(X + Y) = {vx} + {vy} + 2 x {cov} = {_fmt(var_sum,2)}."
        ),
    }


P_BUILDERS = [
    build_bayes,
    build_inclusion_exclusion,
    build_conditional,
    build_binomial,
    build_poisson,
    build_geometric,
    build_exponential,
    build_uniform_variance,
    build_expected_value_discrete,
    build_covariance,
    build_variance_sum,
]
