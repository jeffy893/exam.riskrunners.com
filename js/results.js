/* results.js — scorecard + solution review.
 *
 * showScore()  : rendered right after completing an exam (scorecard on top,
 *                full review with collapsible solutions below).
 * showReview() : reached from the library for an already-taken exam. Identical
 *                review, using the saved answers.
 *
 * The scorecard can be downloaded as a PDF (via the PDF module). Solutions are
 * collapsed by default and expand individually.
 */
const Results = (() => {
  let current = null;
  let result = null;

  function showScore(exam, res) {
    current = exam; result = res;
    renderScorecard(exam, res, true);
    renderReview(exam, res);
    App.showView('view-results');
    App.setActiveNav('library-' + exam.track);
  }

  function showReview(exam, res) {
    current = exam; result = res;
    renderScorecard(exam, res, false);
    renderReview(exam, res);
    App.showView('view-results');
    App.setActiveNav('library-' + exam.track);
  }

  function renderScorecard(exam, res, justFinished) {
    const pct = Math.round((res.correct / res.total) * 100);
    // P is graded 0-10 (6+ passes); FM is scored by correct count (passing
    // mark for practice guidance ~70%). We show both a clear count and, for P,
    // the scaled score.
    let verdict, verdictClass, extra = '';
    if (exam.track === 'P') {
      const scaled = Math.round((res.correct / res.total) * 10);
      const pass = scaled >= 6;
      verdict = pass ? 'Pass' : 'Keep practicing';
      verdictClass = pass ? 'pass' : 'fail';
      extra = `<div class="score-detail">Scaled score: <strong>${scaled} / 10</strong> &nbsp;(6 or higher passes)</div>`;
    } else {
      const pass = pct >= 70;
      verdict = pass ? 'Strong result' : 'Keep practicing';
      verdictClass = pass ? 'pass' : 'fail';
      extra = `<div class="score-detail">A score around 70% is a common practice benchmark for FM.</div>`;
    }

    const wrap = document.getElementById('scorecard-wrap');
    wrap.innerHTML = `
      <div class="scorecard" id="scorecard">
        <div class="score-ring" style="--pct:${pct}">
          <div class="score-inner">
            <span class="score-num">${res.correct}</span>
            <span class="score-den">of ${res.total}</span>
          </div>
        </div>
        <div class="score-verdict ${verdictClass}">${verdict}</div>
        <div class="score-detail">
          ${exam.track} Practice Exam &middot; ${pct}% correct<br>
          Time used: ${formatDuration(res.elapsedSeconds)} of ${exam.config.timeLimitMinutes} min allowed
          ${res.elapsedSeconds > exam.config.timeLimitMinutes * 60
            ? ` &middot; <span style="color:var(--rose)">over time</span>` : ''}
        </div>
        ${extra}
        <div class="score-actions">
          <button class="btn btn-secondary" id="btn-download-scorecard">Download Scorecard (PDF)</button>
          <button class="btn btn-secondary" data-nav="library-${exam.track}">Back to Library</button>
        </div>
      </div>`;

    document.getElementById('btn-download-scorecard').onclick = () => {
      App.toast('Building scorecard…');
      PDF.buildScorecard(exam, res);
    };
  }

  function renderReview(exam, res) {
    const wrap = document.getElementById('review-questions');
    wrap.innerHTML = '';

    exam.questions.forEach(q => {
      const chosen = res.answers[q.n];
      const card = document.createElement('div');
      card.className = 'question-card';

      const choices = Object.entries(q.choices).map(([letter, text]) => {
        let cls = 'choice';
        if (letter === q.answer) cls += ' correct';
        else if (letter === chosen) cls += ' incorrect';
        return `
          <div class="${cls}">
            <span class="choice-letter">${letter}</span>
            <span class="choice-text">${escapeHtml(text)}</span>
          </div>`;
      }).join('');

      const yourAnswer = chosen
        ? `You answered <strong>${chosen}</strong>${chosen === q.answer ? ' ✓' : ' ✗'}`
        : `<em>Not answered</em>`;

      card.innerHTML = `
        <div class="question-head">
          <span class="question-num">Question ${q.n}</span>
          <span class="question-topic">${escapeHtml(q.topic)}</span>
        </div>
        <div class="question-stem">${escapeHtml(q.stem)}</div>
        <div class="choice-list">${choices}</div>
        <div class="solution">
          <button class="solution-toggle" data-toggle="${q.n}">
            <span class="chevron">▶</span> Show solution
          </button>
          <div class="solution-body" id="sol-${q.n}">
            <div class="solution-answer">Correct answer: ${q.answer} &nbsp;|&nbsp; ${yourAnswer}</div>${escapeHtml(q.solution)}
          </div>
        </div>`;
      wrap.appendChild(card);
    });

    wrap.onclick = (e) => {
      const btn = e.target.closest('.solution-toggle');
      if (!btn) return;
      const n = btn.dataset.toggle;
      const body = document.getElementById('sol-' + n);
      const open = body.classList.toggle('open');
      btn.classList.toggle('open', open);
      btn.querySelector('.chevron').nextSibling.textContent =
        open ? ' Hide solution' : ' Show solution';
    };
  }

  function formatDuration(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    if (h) return `${h}h ${m}m`;
    return `${m} min`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  return { showScore, showReview };
})();
