"""
Content bank + problem builders for the SOA Exam FM (Financial Mathematics).

Each builder is a pure function that takes a random.Random instance and returns
a dict describing ONE fully-worked multiple-choice problem:

    {
        "topic":   "<syllabus topic>",
        "stem":    "<question text>",
        "correct": <float>,                 # the numeric answer value
        "unit":    "<optional unit / formatting hint>",
        "solution":"<step-by-step worked solution>",
        "round":   <int decimals for choice formatting>,
    }

The generator (generate_exam.py) turns `correct` into 5 lettered choices by
sprinkling plausible distractors around it, shuffles them, and records which
letter is correct. Because every builder draws its numbers from the RNG, two
generation runs almost never produce identical numbers, satisfying the
"don't just rewrite the same numbers" requirement.

Topics follow the SOA FM syllabus:
  - Time Value of Money
  - Annuities
  - Loans / Amortization
  - Bonds
  - General Cash Flows & Portfolios (yield rates, duration)
  - Immunization
"""

import math


def _fmt(x, nd=2):
    return f"{x:,.{nd}f}"


# --------------------------------------------------------------------------
# Time Value of Money
# --------------------------------------------------------------------------
def build_tvm_accumulation(rng):
    pv = rng.choice([500, 750, 1000, 1200, 1500, 2000, 2500, 3000])
    i = rng.choice([0.03, 0.04, 0.045, 0.05, 0.055, 0.06, 0.07, 0.08])
    n = rng.randint(4, 15)
    fv = pv * (1 + i) ** n
    return {
        "topic": "Time Value of Money",
        "stem": (
            f"An investment of {_fmt(pv,0)} is made in a fund that earns an annual "
            f"effective interest rate of {i*100:.1f}%. Calculate the accumulated "
            f"value of the fund at the end of {n} years."
        ),
        "correct": fv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"The accumulated value uses AV = PV(1 + i)^n.\n"
            f"AV = {_fmt(pv,0)} x (1 + {i:.3f})^{n}\n"
            f"AV = {_fmt(pv,0)} x {_fmt((1+i)**n,5)}\n"
            f"AV = {_fmt(fv,2)}."
        ),
    }


def build_tvm_present_value(rng):
    fv = rng.choice([5000, 8000, 10000, 12000, 15000, 20000])
    i = rng.choice([0.03, 0.04, 0.05, 0.06, 0.07, 0.08])
    n = rng.randint(5, 20)
    pv = fv / (1 + i) ** n
    return {
        "topic": "Time Value of Money",
        "stem": (
            f"A payment of {_fmt(fv,0)} will be received {n} years from now. Using an "
            f"annual effective interest rate of {i*100:.1f}%, calculate the present "
            f"value of this payment."
        ),
        "correct": pv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"Discount the future payment: PV = FV(1 + i)^(-n).\n"
            f"PV = {_fmt(fv,0)} x (1 + {i:.3f})^(-{n})\n"
            f"PV = {_fmt(fv,0)} / {_fmt((1+i)**n,5)}\n"
            f"PV = {_fmt(pv,2)}."
        ),
    }


def build_tvm_nominal_rate(rng):
    i_eff = rng.choice([0.06, 0.08, 0.09, 0.10, 0.12])
    m = rng.choice([2, 4, 12])
    nominal = m * ((1 + i_eff) ** (1 / m) - 1)
    return {
        "topic": "Time Value of Money",
        "stem": (
            f"An account earns an annual effective interest rate of {i_eff*100:.0f}%. "
            f"Calculate the nominal annual interest rate compounded "
            f"{ {2:'semiannually',4:'quarterly',12:'monthly'}[m] } that is equivalent "
            f"to this effective rate."
        ),
        "correct": nominal * 100,
        "unit": "percent",
        "round": 4,
        "solution": (
            f"Set (1 + i^(m)/m)^m = 1 + i.\n"
            f"i^(m) = m[(1 + i)^(1/m) - 1]\n"
            f"i^(m) = {m}[(1 + {i_eff:.2f})^(1/{m}) - 1]\n"
            f"i^(m) = {m} x {_fmt((1+i_eff)**(1/m)-1,6)}\n"
            f"i^(m) = {_fmt(nominal*100,4)}%."
        ),
    }


# --------------------------------------------------------------------------
# Annuities
# --------------------------------------------------------------------------
def build_annuity_immediate_pv(rng):
    pmt = rng.choice([100, 150, 200, 250, 300, 500, 1000])
    i = rng.choice([0.03, 0.04, 0.05, 0.06, 0.07, 0.08])
    n = rng.randint(8, 25)
    a = (1 - (1 + i) ** (-n)) / i
    pv = pmt * a
    return {
        "topic": "Annuities",
        "stem": (
            f"An annuity pays {_fmt(pmt,0)} at the end of each year for {n} years. "
            f"Using an annual effective interest rate of {i*100:.0f}%, calculate the "
            f"present value of the annuity."
        ),
        "correct": pv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"For an annuity-immediate, PV = PMT x a(n|i) where a(n|i) = (1 - v^n)/i.\n"
            f"a({n}|{i:.2f}) = (1 - (1 + {i:.2f})^(-{n})) / {i:.2f} = {_fmt(a,5)}\n"
            f"PV = {_fmt(pmt,0)} x {_fmt(a,5)} = {_fmt(pv,2)}."
        ),
    }


def build_annuity_due_fv(rng):
    pmt = rng.choice([200, 300, 400, 500, 750, 1000])
    i = rng.choice([0.04, 0.05, 0.06, 0.07, 0.08])
    n = rng.randint(6, 20)
    s = ((1 + i) ** n - 1) / i
    fv = pmt * s * (1 + i)  # annuity-due
    return {
        "topic": "Annuities",
        "stem": (
            f"Deposits of {_fmt(pmt,0)} are made at the BEGINNING of each year for "
            f"{n} years into a fund earning an annual effective rate of {i*100:.0f}%. "
            f"Calculate the accumulated value of the fund at the end of {n} years."
        ),
        "correct": fv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"For an annuity-due, AV = PMT x s-double-dot(n|i) = PMT x s(n|i) x (1 + i).\n"
            f"s({n}|{i:.2f}) = ((1 + {i:.2f})^{n} - 1)/{i:.2f} = {_fmt(s,5)}\n"
            f"AV = {_fmt(pmt,0)} x {_fmt(s,5)} x (1 + {i:.2f}) = {_fmt(fv,2)}."
        ),
    }


def build_perpetuity(rng):
    pmt = rng.choice([50, 80, 100, 120, 200, 250])
    i = rng.choice([0.04, 0.05, 0.06, 0.08, 0.10])
    pv = pmt / i
    return {
        "topic": "Annuities",
        "stem": (
            f"A perpetuity pays {_fmt(pmt,0)} at the end of each year forever. Using an "
            f"annual effective interest rate of {i*100:.0f}%, calculate its present value."
        ),
        "correct": pv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"A perpetuity-immediate has PV = PMT / i.\n"
            f"PV = {_fmt(pmt,0)} / {i:.2f} = {_fmt(pv,2)}."
        ),
    }


def build_increasing_annuity(rng):
    base = rng.choice([100, 200, 300])
    i = rng.choice([0.05, 0.06, 0.08])
    n = rng.randint(5, 12)
    adue = (1 - (1 + i) ** (-n)) / i * (1 + i)
    a = (1 - (1 + i) ** (-n)) / i
    Ia = (adue - n * (1 + i) ** (-n)) / i
    pv = base * Ia
    return {
        "topic": "Annuities",
        "stem": (
            f"An annuity pays {_fmt(base,0)} at the end of year 1, {_fmt(2*base,0)} at "
            f"the end of year 2, increasing by {_fmt(base,0)} each year, for {n} years. "
            f"At an annual effective rate of {i*100:.0f}%, calculate the present value."
        ),
        "correct": pv,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"PV = P x (Ia)(n|i), where (Ia)(n|i) = (a-due(n|i) - n v^n)/i.\n"
            f"a-due({n}|{i:.2f}) = {_fmt(adue,5)}, v^{n} = {_fmt((1+i)**(-n),5)}\n"
            f"(Ia) = ({_fmt(adue,5)} - {n} x {_fmt((1+i)**(-n),5)}) / {i:.2f} = {_fmt(Ia,5)}\n"
            f"PV = {_fmt(base,0)} x {_fmt(Ia,5)} = {_fmt(pv,2)}."
        ),
    }


# --------------------------------------------------------------------------
# Loans / Amortization
# --------------------------------------------------------------------------
def build_loan_payment(rng):
    loan = rng.choice([10000, 15000, 20000, 25000, 30000, 50000])
    i = rng.choice([0.04, 0.05, 0.06, 0.07, 0.08])
    n = rng.randint(5, 20)
    a = (1 - (1 + i) ** (-n)) / i
    pmt = loan / a
    return {
        "topic": "Loans and Amortization",
        "stem": (
            f"A loan of {_fmt(loan,0)} is repaid with level annual payments at the end "
            f"of each year for {n} years. The annual effective interest rate is "
            f"{i*100:.0f}%. Calculate the annual payment."
        ),
        "correct": pmt,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"Loan = PMT x a(n|i), so PMT = Loan / a(n|i).\n"
            f"a({n}|{i:.2f}) = (1 - (1 + {i:.2f})^(-{n}))/{i:.2f} = {_fmt(a,5)}\n"
            f"PMT = {_fmt(loan,0)} / {_fmt(a,5)} = {_fmt(pmt,2)}."
        ),
    }


def build_loan_outstanding_balance(rng):
    loan = rng.choice([20000, 30000, 40000, 50000])
    i = rng.choice([0.05, 0.06, 0.07, 0.08])
    n = rng.randint(10, 20)
    k = rng.randint(3, n - 3)
    a_n = (1 - (1 + i) ** (-n)) / i
    pmt = loan / a_n
    a_rem = (1 - (1 + i) ** (-(n - k))) / i
    ob = pmt * a_rem
    return {
        "topic": "Loans and Amortization",
        "stem": (
            f"A loan of {_fmt(loan,0)} is amortized with level annual payments over {n} "
            f"years at an annual effective rate of {i*100:.0f}%. Calculate the "
            f"outstanding loan balance immediately after the {k}th payment."
        ),
        "correct": ob,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"First find the level payment: PMT = Loan / a({n}|i) = "
            f"{_fmt(loan,0)} / {_fmt(a_n,5)} = {_fmt(pmt,2)}.\n"
            f"By the prospective method, the balance after payment {k} is the present "
            f"value of the remaining {n-k} payments:\n"
            f"OB = PMT x a({n-k}|{i:.2f}) = {_fmt(pmt,2)} x {_fmt(a_rem,5)} = {_fmt(ob,2)}."
        ),
    }


def build_loan_interest_principal(rng):
    loan = rng.choice([10000, 15000, 20000, 25000])
    i = rng.choice([0.05, 0.06, 0.07, 0.08])
    n = rng.randint(8, 15)
    k = rng.randint(2, n - 1)
    a_n = (1 - (1 + i) ** (-n)) / i
    pmt = loan / a_n
    interest_k = pmt * (1 - (1 + i) ** (-(n - k + 1)))
    return {
        "topic": "Loans and Amortization",
        "stem": (
            f"A loan of {_fmt(loan,0)} is repaid with level annual payments over {n} "
            f"years at {i*100:.0f}% annual effective. Calculate the interest portion of "
            f"the {k}th payment."
        ),
        "correct": interest_k,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"PMT = {_fmt(loan,0)} / a({n}|i) = {_fmt(pmt,2)}.\n"
            f"Interest in payment t equals PMT(1 - v^(n-t+1)).\n"
            f"I_{k} = {_fmt(pmt,2)} x (1 - (1 + {i:.2f})^(-({n}-{k}+1)))\n"
            f"I_{k} = {_fmt(pmt,2)} x {_fmt(1-(1+i)**(-(n-k+1)),5)} = {_fmt(interest_k,2)}."
        ),
    }


# --------------------------------------------------------------------------
# Bonds
# --------------------------------------------------------------------------
def build_bond_price(rng):
    face = rng.choice([1000, 5000])
    coupon_rate = rng.choice([0.04, 0.05, 0.06, 0.07])
    yield_rate = rng.choice([0.04, 0.05, 0.06, 0.07, 0.08])
    n = rng.randint(5, 20)
    coupon = face * coupon_rate
    a = (1 - (1 + yield_rate) ** (-n)) / yield_rate
    price = coupon * a + face * (1 + yield_rate) ** (-n)
    return {
        "topic": "Bonds",
        "stem": (
            f"A {n}-year bond with face amount {_fmt(face,0)} pays annual coupons at a "
            f"rate of {coupon_rate*100:.0f}% and is redeemable at par. Calculate the "
            f"price to yield an annual effective rate of {yield_rate*100:.0f}%."
        ),
        "correct": price,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"Price = Fr x a(n|i) + C v^n.\n"
            f"Coupon Fr = {_fmt(face,0)} x {coupon_rate:.2f} = {_fmt(coupon,2)}\n"
            f"a({n}|{yield_rate:.2f}) = {_fmt(a,5)}, v^{n} = {_fmt((1+yield_rate)**(-n),5)}\n"
            f"Price = {_fmt(coupon,2)} x {_fmt(a,5)} + {_fmt(face,0)} x "
            f"{_fmt((1+yield_rate)**(-n),5)} = {_fmt(price,2)}."
        ),
    }


def build_bond_premium_discount(rng):
    face = 1000
    coupon_rate = rng.choice([0.06, 0.07, 0.08])
    yield_rate = rng.choice([0.04, 0.05])
    n = rng.randint(8, 15)
    coupon = face * coupon_rate
    a = (1 - (1 + yield_rate) ** (-n)) / yield_rate
    price = coupon * a + face * (1 + yield_rate) ** (-n)
    premium = price - face
    return {
        "topic": "Bonds",
        "stem": (
            f"A {n}-year, {_fmt(face,0)} par bond pays {coupon_rate*100:.0f}% annual "
            f"coupons and is bought to yield {yield_rate*100:.0f}% annual effective. "
            f"Calculate the amount of premium in the purchase price."
        ),
        "correct": premium,
        "unit": "currency",
        "round": 2,
        "solution": (
            f"Since the coupon rate exceeds the yield, the bond sells at a premium.\n"
            f"Price = Fr x a(n|i) + C v^n = {_fmt(coupon,2)} x {_fmt(a,5)} + "
            f"{_fmt(face,0)} x {_fmt((1+yield_rate)**(-n),5)} = {_fmt(price,2)}\n"
            f"Premium = Price - Redemption = {_fmt(price,2)} - {_fmt(face,0)} = {_fmt(premium,2)}."
        ),
    }


# --------------------------------------------------------------------------
# General cash flows, yield rates, duration
# --------------------------------------------------------------------------
def build_macaulay_duration(rng):
    i = rng.choice([0.05, 0.06, 0.08, 0.10])
    n = rng.randint(3, 8)
    # level annuity of 1 per year
    times = list(range(1, n + 1))
    pvs = [(1 + i) ** (-t) for t in times]
    dur = sum(t * pv for t, pv in zip(times, pvs)) / sum(pvs)
    return {
        "topic": "General Cash Flows and Portfolios",
        "stem": (
            f"A cash flow stream pays 1 at the end of each year for {n} years. Using an "
            f"annual effective interest rate of {i*100:.0f}%, calculate the Macaulay "
            f"duration of the stream."
        ),
        "correct": dur,
        "unit": "years",
        "round": 4,
        "solution": (
            f"Macaulay duration = [sum t v^t CF_t] / [sum v^t CF_t].\n"
            f"Numerator = {_fmt(sum(t*pv for t,pv in zip(times,pvs)),5)}, "
            f"Denominator = {_fmt(sum(pvs),5)}\n"
            f"D = {_fmt(dur,4)} years."
        ),
    }


def build_dollar_weighted_yield(rng):
    a = rng.choice([10000, 20000, 50000])
    dep = rng.choice([2000, 5000, 8000])
    interest = rng.choice([800, 1200, 1500, 2000])
    # deposit at mid-year, simple-interest dollar weighted approximation
    b = a + dep + interest
    denom = a + dep * 0.5
    yield_rate = interest / denom
    return {
        "topic": "General Cash Flows and Portfolios",
        "stem": (
            f"A fund begins the year with {_fmt(a,0)}. A deposit of {_fmt(dep,0)} is made "
            f"at mid-year. The fund balance at year-end is {_fmt(b,0)}. Using the "
            f"dollar-weighted (simple interest) method, calculate the annual yield rate."
        ),
        "correct": yield_rate * 100,
        "unit": "percent",
        "round": 3,
        "solution": (
            f"Interest earned I = End - Begin - Deposits = {_fmt(b,0)} - {_fmt(a,0)} - "
            f"{_fmt(dep,0)} = {_fmt(interest,0)}.\n"
            f"Dollar-weighted yield i = I / (A + sum C_t (1 - t)).\n"
            f"i = {_fmt(interest,0)} / ({_fmt(a,0)} + {_fmt(dep,0)} x 0.5) = "
            f"{_fmt(interest,0)} / {_fmt(denom,2)} = {_fmt(yield_rate*100,3)}%."
        ),
    }


FM_BUILDERS = [
    build_tvm_accumulation,
    build_tvm_present_value,
    build_tvm_nominal_rate,
    build_annuity_immediate_pv,
    build_annuity_due_fv,
    build_perpetuity,
    build_increasing_annuity,
    build_loan_payment,
    build_loan_outstanding_balance,
    build_loan_interest_principal,
    build_bond_price,
    build_bond_premium_discount,
    build_macaulay_duration,
    build_dollar_weighted_yield,
]
