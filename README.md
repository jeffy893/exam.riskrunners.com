# Actuarial Exam Prep — exam.riskrunners.com

Full-length, timed practice exams for the Society of Actuaries **Exam FM**
(Financial Mathematics) and **Exam P** (Probability), with worked solutions and
downloadable PDFs.

The site itself is 100% static (HTML / CSS / vanilla JS) and deploys as a
GitHub Pages site. Exams are generated **offline** by a small Python pipeline
and committed as JSON, so the live site never needs a server or database.

**Live:** [exam.riskrunners.com](https://exam.riskrunners.com)

---

## How it works

```
Python generator  ──►  data/*.json  ──►  static site reads JSON with fetch()
 (run locally,          (committed         (timer, scoring, review,
  double-click)          to the repo)        PDF export — all client-side)
```

- **Backend (offline):** `generator/` builds a 30-question exam with fully
  worked solutions and writes it to `data/`.
- **Frontend (in the browser):** a single-page app lets you take a timed exam,
  see a scorecard, review every question with a collapsible solution, and
  export PDFs.

## Generating exams

Two double-click launchers (macOS `.command` files) run the pipeline:

- **`generate_fm.command`** — generate one new FM practice exam
- **`generate_p.command`** — generate one new P practice exam

Or from a terminal:

```bash
python3 generator/generate_exam.py FM                 # auto (LLM + fallback)
python3 generator/generate_exam.py P  --source bedrock # LLM only
python3 generator/generate_exam.py FM --source template # offline, no AWS
```

Each run creates a genuinely new exam, persists it under `data/`, and updates
`data/manifest.json`.

### Problem sources

Problems can be authored two ways; the generated exam records which in its
`source` and `llmQuestions` fields:

- **Bedrock (Amazon Bedrock / Anthropic Claude)** — the LLM writes exam-realistic
  scenario problems. Python then **independently verifies the arithmetic**: the
  model returns the numeric inputs, Python recomputes the answer from a fixed set
  of actuarial formulas, and only a verified value is placed among the choices.
  The LLM is trusted for the story; Python is the source of truth for the math.
- **Templates** — deterministic Python builders (offline, free). Used as a
  fallback in `auto` mode and for topics with no closed-form verifiable recipe
  (e.g. FM duration / dollar-weighted yield).

The LLM runs only in this **offline generator step** on your machine. The
published site stays a static GitHub Pages site reading JSON — no credentials
ever touch the deployed site.

### Configuration & credentials

Copy `.env.example` to `.env` (git-ignored) to set the region, model, and default
source. AWS auth uses the standard credential chain (`~/.aws/...`, env vars, SSO);
**no secrets are stored in the repo**. The default model is a cross-region
inference profile (`us.anthropic.claude-sonnet-4-5-...`).

### Syllabus-weighted topic mix

Question counts per topic follow the **official SOA syllabus weightings** (see
`generator/syllabus.py`), not a uniform mix, so a generated exam mirrors the real
exam's emphasis. Sourced from the current SOA syllabi:

| Exam FM topic | Weight | | Exam P topic | Weight |
|---|---|---|---|---|
| Time Value of Money | 5–15% | | General Probability | 23–30% |
| Annuities | 20–30% | | Univariate Random Variables | 44–50% |
| Loans | 15–25% | | Multivariate Random Variables | 23–30% |
| Bonds | 15–25% | | | |
| General Cash Flows / Portfolios / ALM | 20–30% | | | |

Each exam JSON records its realized `topicDistribution` and the `syllabusWeights`
it targeted. (Weightings sourced from the SOA syllabi; rephrased for compliance.)

### Rolling library of 10 (FIFO)

Each track keeps a maximum of **10** exams. Generating an 11th exam expunges the
oldest (deletes its file and manifest entry) — a first-in, first-out queue. The
site labels the surviving exams **#1–#10** by position. FM and P are separate
queues but share the same `data/` tree and manifest.

## Deploying

After generating, review locally then push:

```bash
python3 -m http.server 8000    # then open http://localhost:8000
git add -A
git commit -m "Add FM practice exam"
git push                        # GitHub Pages publishes from main
```

## Project structure

```
exam.riskrunners.com/
├── index.html              # single-page app (home / library / exam / results)
├── css/style.css           # calm "study desk" theme (paper + academic indigo)
├── assets/                 # branding
│   ├── rr-exam-logo.png        # full-res master (used in PDF covers)
│   ├── rr-exam-logo-web.png    # lightweight logo for nav + hero
│   ├── favicon.png             # tab / apple-touch icon
│   └── og-image.png            # 1200x630 social share card (link previews)
├── js/
│   ├── storage.js          # per-device result persistence (localStorage)
│   ├── pdf.js              # client-side PDF export (jsPDF)
│   ├── exam.js             # timed exam-taking (floating timer + progress bar)
│   ├── results.js          # scorecard + collapsible solution review
│   └── app.js              # router, manifest/exam loading, home + library
├── data/
│   ├── manifest.json       # index of available exams per track
│   ├── fm/<id>.json        # each FM exam
│   └── p/<id>.json         # each P exam
├── generator/
│   ├── generate_exam.py    # pipeline: build → persist → FIFO cap → manifest
│   ├── content_fm.py       # FM problem builders (TVM, annuities, loans, bonds…)
│   └── content_p.py        # P problem builders (probability, distributions…)
├── generate_fm.command     # double-click → generate FM exam
└── generate_p.command      # double-click → generate P exam
```

## Exam formats

| | Exam FM | Exam P |
|---|---|---|
| Questions | 30 | 30 |
| Choices | 5 | 5 |
| Time limit | 2h 30m (150 min) | 3h (180 min) |
| Avg / question | ~5 min | ~6 min |
| Scoring | correct-count (no penalty for guesses) | scaled 0–10, 6+ passes (no penalty) |

The in-exam timer counts down, then goes **negative and turns red** at zero but
keeps running — you are never forced to stop.

## PDF exports

Every exam offers two downloads (available even before taking it):

1. **Problems** — one problem per page.
2. **Problems & Solutions** — each problem on its own page, its solution on the
   next page (page break between), so you can read a problem without seeing the
   answer.

Both open with an Integral MASS cover page carrying contact details and the Risk
Runners signature links, with a compact signature repeated on every page. The
scorecard is also downloadable as a PDF.

## License / signature

&copy; Integral MASS. Prepared by Jefferson Richards — jefferson@richards.plus.
Signature links are shared with [state.riskrunners.com](https://state.riskrunners.com).
