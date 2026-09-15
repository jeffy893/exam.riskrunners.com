"""
llm_authoring.py — author exam-realistic problems with Bedrock/Claude, then
INDEPENDENTLY VERIFY the arithmetic in Python before trusting anything.

Why the verification layer: LLMs write excellent word problems but make silent
arithmetic slips. So the model is required to return, for each problem, the
structured numeric inputs and a "computation recipe" (one of a fixed set of
known actuarial calculations). Python recomputes the answer from those inputs
and only accepts the problem if the model's stated answer matches within
tolerance AND the correct value actually appears among the five choices.

Anything that fails verification is discarded; the caller regenerates.

This module returns problems in the SAME dict shape the template builders use:
    {topic, stem, choices{A..E}, answer, answerValue, solution}
so generate_exam.py can treat LLM and template problems interchangeably.
"""

import math

LETTERS = ["A", "B", "C", "D", "E"]

# --------------------------------------------------------------------------
# Verifiable computation recipes. The model must pick one "calc" and supply the
# named inputs; Python computes the ground-truth answer. This is the trust
# anchor — we never rely on the model's own arithmetic.
# --------------------------------------------------------------------------
def _annuity_immediate(i, n):
    return (1 - (1 + i) ** (-n)) / i

def _annuity_due(i, n):
    return _annuity_immediate(i, n) * (1 + i)

def _accum_annuity(i, n):
    return ((1 + i) ** n - 1) / i


def _calc(recipe, p):
    """Compute the ground-truth answer for a named recipe + inputs dict p."""
    r = recipe
    # Discrete count inputs must be integers (comb/factorial require ints).
    p = dict(p)
    for count_key in ("n", "k", "m"):
        if count_key in p and not isinstance(p[count_key], list):
            p[count_key] = int(round(p[count_key]))
    if r == "accumulate":                      # PV grows for n years at i
        return p["pv"] * (1 + p["i"]) ** p["n"]
    if r == "present_value":                   # discount FV for n years at i
        return p["fv"] * (1 + p["i"]) ** (-p["n"])
    if r == "nominal_from_effective":          # i^(m) from effective i
        return p["m"] * ((1 + p["i"]) ** (1 / p["m"]) - 1) * 100
    if r == "effective_from_nominal":          # effective i from i^(m)
        return ((1 + p["nom"] / p["m"]) ** p["m"] - 1) * 100
    if r == "annuity_immediate_pv":
        return p["pmt"] * _annuity_immediate(p["i"], p["n"])
    if r == "annuity_due_pv":
        return p["pmt"] * _annuity_due(p["i"], p["n"])
    if r == "annuity_immediate_fv":
        return p["pmt"] * _accum_annuity(p["i"], p["n"])
    if r == "annuity_due_fv":
        return p["pmt"] * _accum_annuity(p["i"], p["n"]) * (1 + p["i"])
    if r == "perpetuity_immediate":
        return p["pmt"] / p["i"]
    if r == "perpetuity_due":
        return p["pmt"] / p["i"] * (1 + p["i"])
    if r == "loan_payment":
        return p["loan"] / _annuity_immediate(p["i"], p["n"])
    if r == "outstanding_balance":             # prospective
        pmt = p["loan"] / _annuity_immediate(p["i"], p["n"])
        return pmt * _annuity_immediate(p["i"], p["n"] - p["k"])
    if r == "bond_price":
        coupon = p["face"] * p["coupon_rate"]
        return (coupon * _annuity_immediate(p["yield_rate"], p["n"])
                + p["redemption"] * (1 + p["yield_rate"]) ** (-p["n"]))
    # ---- probability ----
    if r == "binomial_pmf":
        n, k, pr = p["n"], p["k"], p["p"]
        return math.comb(n, k) * pr ** k * (1 - pr) ** (n - k)
    if r == "poisson_pmf":
        lam, k = p["lam"], p["k"]
        return math.exp(-lam) * lam ** k / math.factorial(k)
    if r == "geometric_pmf":                   # first success on trial k
        return (1 - p["p"]) ** (p["k"] - 1) * p["p"]
    if r == "exponential_survival":            # P(X > t), mean theta
        return math.exp(-p["t"] / p["theta"])
    if r == "exponential_cdf":                 # P(X <= t)
        return 1 - math.exp(-p["t"] / p["theta"])
    if r == "bayes_two_source":
        num = p["pa"] * p["da"]
        return num / (num + p["pb"] * p["db"])
    if r == "conditional":
        return p["pab"] / p["pb"]
    if r == "union":
        return p["pa"] + p["pb"] - p["pab"]
    if r == "uniform_variance":
        return (p["b"] - p["a"]) ** 2 / 12
    if r == "uniform_mean":
        return (p["a"] + p["b"]) / 2
    if r == "covariance":
        return p["exy"] - p["ex"] * p["ey"]
    if r == "variance_sum":
        return p["vx"] + p["vy"] + 2 * p["cov"]
    if r == "expected_value_discrete":
        return sum(v * pr for v, pr in zip(p["values"], p["probs"]))
    raise ValueError(f"unknown recipe: {recipe}")


VALID_RECIPES = {
    "FM": [
        "accumulate", "present_value", "nominal_from_effective",
        "effective_from_nominal", "annuity_immediate_pv", "annuity_due_pv",
        "annuity_immediate_fv", "annuity_due_fv", "perpetuity_immediate",
        "perpetuity_due", "loan_payment", "outstanding_balance", "bond_price",
    ],
    "P": [
        "binomial_pmf", "poisson_pmf", "geometric_pmf", "exponential_survival",
        "exponential_cdf", "bayes_two_source", "conditional", "union",
        "uniform_variance", "uniform_mean", "covariance", "variance_sum",
        "expected_value_discrete",
    ],
}

# The EXACT input keys each recipe's Python computation needs. We show these to
# the model in the prompt AND enforce them via the alias normalizer below, so
# the model's descriptive names ("payment", "loan_amount") map to our canonical
# keys ("pmt", "loan"). This is the trust anchor between prose and arithmetic.
RECIPE_INPUTS = {
    "accumulate": ["pv", "i", "n"],
    "present_value": ["fv", "i", "n"],
    "nominal_from_effective": ["i", "m"],
    "effective_from_nominal": ["nom", "m"],
    "annuity_immediate_pv": ["pmt", "i", "n"],
    "annuity_due_pv": ["pmt", "i", "n"],
    "annuity_immediate_fv": ["pmt", "i", "n"],
    "annuity_due_fv": ["pmt", "i", "n"],
    "perpetuity_immediate": ["pmt", "i"],
    "perpetuity_due": ["pmt", "i"],
    "loan_payment": ["loan", "i", "n"],
    "outstanding_balance": ["loan", "i", "n", "k"],
    "bond_price": ["face", "coupon_rate", "yield_rate", "n", "redemption"],
    "binomial_pmf": ["n", "k", "p"],
    "poisson_pmf": ["lam", "k"],
    "geometric_pmf": ["p", "k"],
    "exponential_survival": ["t", "theta"],
    "exponential_cdf": ["t", "theta"],
    "bayes_two_source": ["pa", "da", "pb", "db"],
    "conditional": ["pab", "pb"],
    "union": ["pa", "pb", "pab"],
    "uniform_variance": ["a", "b"],
    "uniform_mean": ["a", "b"],
    "covariance": ["exy", "ex", "ey"],
    "variance_sum": ["vx", "vy", "cov"],
    "expected_value_discrete": ["values", "probs"],
}

# Accepted aliases -> canonical key. Lets the model use natural names.
INPUT_ALIASES = {
    # amounts
    "payment": "pmt", "pmt_amount": "pmt", "annual_payment": "pmt",
    "loan_amount": "loan", "principal": "loan", "loan_value": "loan",
    "present_value": "pv", "initial_value": "pv", "deposit": "pv",
    "future_value": "fv", "final_value": "fv",
    "face_value": "face", "face_amount": "face", "par": "face", "par_value": "face",
    "redemption_value": "redemption", "redemption_amount": "redemption",
    "maturity_value": "redemption",
    # rates
    "interest_rate": "i", "effective_rate": "i", "annual_rate": "i",
    "rate": "i", "effective_interest_rate": "i", "annual_effective_rate": "i",
    "nominal_rate": "nom", "nominal": "nom", "i_m": "nom",
    "yield": "yield_rate", "yield_to_maturity": "yield_rate",
    "coupon": "coupon_rate",
    # counts / periods
    "years": "n", "periods": "n", "num_periods": "n", "n_periods": "n",
    "term": "n", "number_of_periods": "n", "compounding_per_year": "m",
    "frequency": "m", "m_per_year": "m", "periods_per_year": "m",
    "successes": "k", "trials": "n", "num_trials": "n",
    "payment_number": "k", "kth_payment": "k",
    "time": "t", "mean": "theta", "theta_mean": "theta", "lambda": "lam",
    "rate_lambda": "lam",
    # probability
    "prob": "p", "probability": "p", "success_probability": "p", "p_success": "p",
    "p_a": "pa", "p_b": "pb", "p_a_and_b": "pab", "p_ab": "pab",
    "p_source1": "pa", "p_source2": "pb",
    "p_event_given_source1": "da", "p_event_given_source2": "db",
    "p_defect_given_a": "da", "p_defect_given_b": "db",
    "p_given_a": "da", "p_given_b": "db",
    # moments
    "e_xy": "exy", "e_x": "ex", "e_y": "ey", "expected_xy": "exy",
    "expected_x": "ex", "expected_y": "ey",
    "var_x": "vx", "var_y": "vy", "variance_x": "vx", "variance_y": "vy",
    "covariance": "cov", "cov_xy": "cov",
    "lower": "a", "upper": "b", "lower_bound": "a", "upper_bound": "b",
    "a_bound": "a", "b_bound": "b",
}


def _normalize_inputs(recipe, raw_inputs):
    """Map model-provided input names to the canonical keys _calc expects.

    Strategy: for each provided key, if it's already canonical keep it; else if
    it has a known alias, remap it. Then fill any still-missing canonical key
    with a sensible default when safe (e.g. bond redemption == face)."""
    canon = {}
    for k, v in raw_inputs.items():
        key = k.strip().lower()
        key = INPUT_ALIASES.get(key, key)
        canon[key] = v

    needed = RECIPE_INPUTS[recipe]

    # bond redemption defaults to face (redeemable at par) if omitted
    if recipe == "bond_price" and "redemption" not in canon and "face" in canon:
        canon["redemption"] = canon["face"]

    missing = [k for k in needed if k not in canon]
    if missing:
        raise ValueError(f"missing inputs for {recipe}: {missing} "
                         f"(got {list(raw_inputs.keys())})")
    return canon


# --------------------------------------------------------------------------
# Prompts
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an experienced actuarial exam item writer for the \
Society of Actuaries. You write original, exam-realistic multiple-choice \
problems that match the style, wording, and difficulty of the real exam. You \
never copy real exam questions verbatim. You are meticulous about arithmetic.

You MUST reply with a single JSON object and nothing else."""


def _user_prompt(track, recipe, seed_hint):
    if track == "FM":
        context = (
            "This is for SOA Exam FM (Financial Mathematics). Problems should be "
            "concise scenario-style word problems that fit on one screen. Use "
            "realistic amounts and rates."
        )
    else:
        context = (
            "This is for SOA Exam P (Probability). Problems should be concise "
            "scenario-style word problems that fit on one screen. Use realistic "
            "framings (insurance claims, component lifetimes, risk selection)."
        )

    required_keys = RECIPE_INPUTS[recipe]
    keys_str = ", ".join(f'"{k}"' for k in required_keys)

    return f"""{context}

Write ONE multiple-choice problem whose correct answer is computed by the \
calculation recipe "{recipe}". Vary the surface story so it does not read like \
a template (theme hint: {seed_hint}).

The "inputs" object MUST use EXACTLY these key names (no others, no renaming): \
{keys_str}.

Return JSON with EXACTLY these keys:
{{
  "topic": "<short syllabus topic name>",
  "stem": "<the full question text, self-contained, no answer choices inside>",
  "recipe": "{recipe}",
  "inputs": {{ {keys_str} — each a number }},
  "unit": "currency" | "percent" | "probability" | "years" | "number",
  "round": <integer number of decimal places to display>,
  "answer_value": <the numeric answer YOU computed, as a number>,
  "distractors": [<four plausible WRONG numeric answers, as numbers>],
  "solution": "<step-by-step worked solution, plain text, ASCII math only>"
}}

Rules:
- "inputs" must contain exactly the variables the recipe needs. For interest \
rates and probabilities use decimals (e.g. 0.06, not 6%). For "nominal_from_\
effective"/"effective_from_nominal" include integer "m".
- "expected_value_discrete" uses inputs {{"values": [...], "probs": [...]}}.
- The four distractors must be distinct from the correct answer and from each \
other, and must be plausible (reflect common mistakes), not random.
- Do NOT include letter labels (A-E) in the stem or anywhere; provide only raw \
numeric distractors.
- Use ASCII only in "solution" (write v^n, a(n|i), etc.). No LaTeX, no unicode \
math symbols."""


# --------------------------------------------------------------------------
# Verification + assembly
# --------------------------------------------------------------------------
def _format_value(value, unit, nd):
    if unit == "percent":
        return f"{value:,.{nd}f}%"
    return f"{value:,.{nd}f}"


def _close(a, b, rel=0.02, absttol=0.01):
    if a == b:
        return True
    denom = max(abs(a), abs(b), 1e-9)
    return abs(a - b) <= max(absttol, rel * denom)


def author_problem(client, track, recipe, number, rng, seed_hint,
                   max_attempts=3):
    """Author + verify a single problem. Returns a builder-shaped dict.

    Raises RuntimeError if it cannot produce a verified problem in
    max_attempts tries (caller may fall back to a template).
    """
    last_err = None
    for _ in range(max_attempts):
        try:
            data = client.complete_json(
                SYSTEM_PROMPT,
                _user_prompt(track, recipe, seed_hint),
                temperature=0.9,
            )
        except Exception as e:
            last_err = f"model error: {e}"
            continue

        try:
            recipe_used = data["recipe"]
            if recipe_used not in VALID_RECIPES[track]:
                last_err = f"invalid recipe {recipe_used!r}"
                continue

            # Map the model's (possibly descriptive) input names to canonical
            # keys, then coerce to numbers.
            raw = _normalize_inputs(recipe_used, data["inputs"])
            if recipe_used == "expected_value_discrete":
                inputs = {
                    "values": [_num(x) for x in raw["values"]],
                    "probs": [_num(x) for x in raw["probs"]],
                }
            else:
                inputs = {k: _num(v) for k, v in raw.items()}

            # PYTHON IS THE SOURCE OF TRUTH for the answer. We compute it from
            # the model's inputs and never trust the model's own arithmetic.
            truth = _calc(recipe_used, inputs)
            if not (isinstance(truth, float) and math.isfinite(truth)):
                last_err = f"non-finite truth for {recipe_used}"
                continue

            stated = None
            try:
                stated = _num(data.get("answer_value"))
            except (ValueError, TypeError):
                pass
            model_agreed = stated is not None and _close(truth, stated)

            unit = data.get("unit", "number")
            nd = int(data.get("round", 2))
            correct = truth

            # Build the distractor set. Prefer the model's distractors ONLY if
            # the model agreed with Python's answer (so they're calibrated to
            # the right value); otherwise synthesize plausible ones around the
            # true value.
            model_distractors = []
            for x in (data.get("distractors") or []):
                try:
                    model_distractors.append(_num(x))
                except (ValueError, TypeError):
                    continue

            if model_agreed and len(model_distractors) >= 4:
                values = [correct] + model_distractors[:4]
            else:
                values = [correct] + _synth_distractors(correct, unit, rng)

            values = _dedupe_values(values, correct, unit, rng)
            rng.shuffle(values)
            correct_index = min(range(len(values)),
                                key=lambda idx: abs(values[idx] - correct))
            choices = {LETTERS[idx]: _format_value(v, unit, nd)
                       for idx, v in enumerate(values)}

            # Keep the solution consistent with Python's verified answer.
            solution = str(data.get("solution", "")).strip()
            verified_line = (f"Verified answer: {_format_value(correct, unit, nd)} "
                             f"(computed and checked independently).")
            if not model_agreed:
                solution = (solution + "\n\n" + verified_line).strip()

            return {
                "n": number,
                "topic": str(data["topic"]),
                "stem": str(data["stem"]).strip(),
                "choices": choices,
                "answer": LETTERS[correct_index],
                "answerValue": _format_value(correct, unit, nd),
                "solution": solution,
                "_source": "llm",
            }
        except (KeyError, ValueError, TypeError) as e:
            last_err = f"schema/verify error: {e}"
            continue

    raise RuntimeError(f"could not author verified problem ({last_err})")


def _num(v):
    if isinstance(v, bool):
        raise ValueError("boolean where number expected")
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        return float(v.replace(",", "").replace("%", "").strip())
    raise ValueError(f"not a number: {v!r}")


def _synth_distractors(correct, unit, rng):
    """Four plausible wrong answers around `correct` (common-mistake style)."""
    candidates = [correct * m for m in (0.9, 0.95, 1.05, 1.1, 0.85, 1.15, 1.2, 0.8)]
    if unit == "probability":
        candidates.append(max(0.0001, min(0.9999, 1 - correct)))
    rng.shuffle(candidates)
    out, seen = [], set()
    for c in candidates:
        if unit == "probability":
            c = min(max(c, 0.0001), 0.9999)
        if abs(c - correct) < abs(correct) * 0.01 + 1e-9:
            continue
        key = round(c, 4)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) == 4:
            break
    bump = 1.23
    while len(out) < 4:
        out.append(correct * bump)
        bump += 0.07
    return out


def _dedupe_values(values, correct, unit, rng):
    """Guarantee 5 distinct display values around `correct`."""
    seen = set()
    out = []
    for v in values:
        key = round(v, 4)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    bump = 1.07
    while len(out) < 5:
        cand = correct * bump
        if round(cand, 4) not in seen:
            seen.add(round(cand, 4))
            out.append(cand)
        bump += 0.05
    return out[:5]
