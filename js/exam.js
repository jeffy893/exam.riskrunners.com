/* exam.js — the timed exam-taking experience.
 *
 * Renders all 30 questions in one scrollable view. A sticky top bar holds the
 * timer and a progress bar (both float with the page). The timer counts DOWN
 * from the exam's time limit; when it hits zero it goes negative and turns red
 * but KEEPS RUNNING — the candidate is never forced to stop. "Complete Exam"
 * (available at top and bottom) ends the attempt and hands off to Results.
 */
const Exam = (() => {
  let current = null;      // exam JSON
  let answers = {};        // qNum -> letter
  let startTs = 0;
  let limitSeconds = 0;
  let timerId = null;

  function start(exam) {
    current = exam;
    answers = {};
    startTs = Date.now();
    limitSeconds = (exam.config.timeLimitMinutes || 0) * 60;

    document.getElementById('exam-label').textContent =
      `${exam.track} • ${exam.questions.length} questions`;
    renderQuestions();
    updateProgress();
    App.showView('view-exam');
    App.setActiveNav('library-' + exam.track);
    startTimer();
    bindControls();
  }

  function renderQuestions() {
    const wrap = document.getElementById('exam-questions');
    wrap.innerHTML = '';
    current.questions.forEach(q => {
      const card = document.createElement('div');
      card.className = 'question-card';
      card.id = 'q-' + q.n;

      const choices = Object.entries(q.choices).map(([letter, text]) => `
        <div class="choice" data-q="${q.n}" data-choice="${letter}">
          <span class="choice-letter">${letter}</span>
          <span class="choice-text">${escapeHtml(text)}</span>
        </div>`).join('');

      card.innerHTML = `
        <div class="question-head">
          <span class="question-num">Question ${q.n}</span>
          <div class="question-head-right">
            <span class="question-topic">${escapeHtml(q.displayTopic || q.topic)}</span>
            <button class="btn-copy" data-copy="${q.n}" title="Copy problem to clipboard" aria-label="Copy problem to clipboard">
              <span class="copy-icon">⧉</span> Copy
            </button>
          </div>
        </div>
        <div class="question-stem">${escapeHtml(q.stem)}</div>
        <div class="choice-list">${choices}</div>`;
      wrap.appendChild(card);
    });
  }

  function bindControls() {
    const wrap = document.getElementById('exam-questions');
    wrap.onclick = (e) => {
      const copyBtn = e.target.closest('.btn-copy');
      if (copyBtn) {
        const q = current.questions.find(x => String(x.n) === copyBtn.dataset.copy);
        Clipboard.copyProblem(q, copyBtn, { includeSolution: false });
        return;
      }

      const choice = e.target.closest('.choice');
      if (!choice) return;
      const qNum = choice.dataset.q;
      const letter = choice.dataset.choice;
      answers[qNum] = letter;
      // visually select within this question
      choice.parentElement.querySelectorAll('.choice')
        .forEach(c => c.classList.remove('selected'));
      choice.classList.add('selected');
      updateProgress();
    };

    document.getElementById('btn-complete').onclick = complete;
  }

  function updateProgress() {
    const answered = Object.keys(answers).length;
    const total = current.questions.length;
    document.getElementById('progress-text').textContent =
      `${answered} of ${total} answered`;
    document.getElementById('progress-fill').style.width =
      `${(answered / total) * 100}%`;
  }

  // ---- timer ----
  function startTimer() {
    stopTimer();
    tick();
    timerId = setInterval(tick, 1000);
  }
  function stopTimer() {
    if (timerId) { clearInterval(timerId); timerId = null; }
  }
  function elapsedSeconds() {
    return Math.floor((Date.now() - startTs) / 1000);
  }
  function tick() {
    const remaining = limitSeconds - elapsedSeconds();
    const el = document.getElementById('exam-timer');
    if (remaining >= 0) {
      el.classList.remove('overtime');
      el.textContent = formatClock(remaining);
    } else {
      el.classList.add('overtime');
      el.textContent = '-' + formatClock(Math.abs(remaining));
    }
  }
  function formatClock(totalSec) {
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    const mm = String(m).padStart(2, '0');
    const ss = String(s).padStart(2, '0');
    return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
  }

  // ---- completion ----
  function complete() {
    const answered = Object.keys(answers).length;
    const total = current.questions.length;
    const unanswered = total - answered;
    if (unanswered > 0) {
      const ok = confirm(
        `You have ${unanswered} unanswered question${unanswered === 1 ? '' : 's'}. ` +
        `Unanswered questions are marked incorrect. Complete the exam anyway?`);
      if (!ok) return;
    }

    stopTimer();

    let correct = 0;
    current.questions.forEach(q => {
      if (answers[q.n] === q.answer) correct++;
    });

    const result = {
      answers: { ...answers },
      correct,
      total,
      elapsedSeconds: elapsedSeconds(),
      completedAt: new Date().toISOString()
    };
    Storage.saveResult(current.id, result);
    Results.showScore(current, result);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  return { start };
})();
