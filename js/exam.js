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
  let formulaLoaded = false;   // lazy-load the PDF into the iframe on first open

  // Map each track to its formula-sheet PDF (rendered inline by the browser).
  const FORMULA_PDF = {
    FM: 'assets/Actuary_FM_Formulas1.pdf',
    P:  'assets/Actuary_P_Formulas1.pdf'
  };

  function start(exam) {
    current = exam;
    answers = {};
    startTs = Date.now();
    limitSeconds = (exam.config.timeLimitMinutes || 0) * 60;

    document.getElementById('exam-label').textContent =
      `${exam.track} • ${exam.questions.length} questions`;
    renderQuestions();
    updateProgress();
    setupFormulaSheet(exam.track);
    App.showView('view-exam');
    App.setActiveNav('library-' + exam.track);
    startTimer();
    bindControls();
  }

  // ---- formula sheet (in-page slide-up viewer) ----
  //
  // We render the PDF ourselves with pdf.js instead of leaning on an <iframe>.
  // On iPad Safari the native iframe PDF viewer only showed page 1, ignored the
  // fit-width hint (so it opened absurdly zoomed in), and swallowed touch
  // scrolling. Rendering every page to a <canvas> inside our own scroll
  // container fixes all three: all pages show, scrolling works, and a zoom
  // factor lets the reader scale in and out.
  let formulaDoc = null;        // loaded pdfjs document for the current track
  let formulaZoom = 1;          // multiplier applied on top of fit-to-width
  let formulaRenderToken = 0;   // guards against overlapping re-renders
  const FORMULA_ZOOM_MIN = 0.5;
  const FORMULA_ZOOM_MAX = 4;

  function pdfjsLib() {
    return window['pdfjsLib'] || (window.pdfjsLib);
  }

  function setupFormulaSheet(track) {
    const btn = document.getElementById('btn-formula');
    const panel = document.getElementById('formula-panel');
    const closeBtn = document.getElementById('btn-formula-close');
    const title = document.getElementById('formula-panel-title');
    const pages = document.getElementById('formula-pages');
    if (!btn || !panel || !pages) return;

    const src = FORMULA_PDF[track] || '';
    formulaLoaded = false;
    formulaDoc = null;
    formulaZoom = 1;
    pages.innerHTML = '';
    closeFormula();

    title.textContent = `Exam ${track} — Formula Sheet`;
    btn.style.display = src ? 'inline-flex' : 'none';

    btn.onclick = () => {
      if (panel.classList.contains('open')) { closeFormula(); return; }
      openFormula();
      if (!formulaLoaded && src) {
        formulaLoaded = true;
        loadFormula(src);
      }
    };
    closeBtn.onclick = closeFormula;

    document.getElementById('formula-zoom-in').onclick  = () => changeZoom(1.25);
    document.getElementById('formula-zoom-out').onclick = () => changeZoom(0.8);
    document.getElementById('formula-zoom-reset').onclick = () => { formulaZoom = 1; renderFormulaPages(); };

    bindPinchZoom();
  }

  async function loadFormula(src) {
    const pages = document.getElementById('formula-pages');
    const lib = pdfjsLib();
    if (!lib) {
      pages.innerHTML = '<div class="formula-msg">Viewer failed to load. Check your connection and reopen.</div>';
      return;
    }
    lib.GlobalWorkerOptions.workerSrc =
      'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    pages.innerHTML = '<div class="formula-msg"><div class="spinner"></div>Loading formula sheet…</div>';
    try {
      formulaDoc = await lib.getDocument(src).promise;
      await renderFormulaPages();
    } catch (e) {
      console.error(e);
      pages.innerHTML = '<div class="formula-msg">Could not display the formula sheet.</div>';
    }
  }

  // Renders every page into its own canvas, sized to fit the panel width and
  // scaled by the current zoom. Re-run whenever zoom changes or the panel opens.
  async function renderFormulaPages() {
    if (!formulaDoc) return;
    const scroll = document.getElementById('formula-scroll');
    const pages = document.getElementById('formula-pages');
    const token = ++formulaRenderToken;

    // Available width for a page (minus a little breathing room), times zoom.
    const baseWidth = Math.max(240, (scroll.clientWidth || 320) - 24);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    pages.innerHTML = '';
    for (let n = 1; n <= formulaDoc.numPages; n++) {
      if (token !== formulaRenderToken) return;   // superseded by a newer render
      const page = await formulaDoc.getPage(n);
      const unscaled = page.getViewport({ scale: 1 });
      const fitScale = (baseWidth / unscaled.width) * formulaZoom;
      const viewport = page.getViewport({ scale: fitScale });

      const canvas = document.createElement('canvas');
      canvas.className = 'formula-page';
      canvas.width = Math.floor(viewport.width * dpr);
      canvas.height = Math.floor(viewport.height * dpr);
      canvas.style.width = viewport.width + 'px';
      canvas.style.height = viewport.height + 'px';
      pages.appendChild(canvas);

      const ctx = canvas.getContext('2d');
      await page.render({
        canvasContext: ctx,
        viewport,
        transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null
      }).promise;
    }
  }

  function changeZoom(factor) {
    const next = Math.min(FORMULA_ZOOM_MAX, Math.max(FORMULA_ZOOM_MIN, formulaZoom * factor));
    if (Math.abs(next - formulaZoom) < 0.001) return;
    formulaZoom = next;
    renderFormulaPages();
  }

  // Pinch-to-zoom on touch devices, debounced so we re-render once the gesture
  // settles rather than on every move event.
  function bindPinchZoom() {
    const scroll = document.getElementById('formula-scroll');
    if (!scroll || scroll._pinchBound) return;
    scroll._pinchBound = true;

    let startDist = 0;
    let startZoom = 1;
    let pinching = false;
    let settleTimer = null;

    const dist = (t) => {
      const dx = t[0].clientX - t[1].clientX;
      const dy = t[0].clientY - t[1].clientY;
      return Math.hypot(dx, dy);
    };

    scroll.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        pinching = true;
        startDist = dist(e.touches);
        startZoom = formulaZoom;
      }
    }, { passive: true });

    scroll.addEventListener('touchmove', (e) => {
      if (!pinching || e.touches.length !== 2) return;
      e.preventDefault();   // stop the page from also pinch-zooming
      const ratio = dist(e.touches) / (startDist || 1);
      const target = Math.min(FORMULA_ZOOM_MAX, Math.max(FORMULA_ZOOM_MIN, startZoom * ratio));
      if (Math.abs(target - formulaZoom) > 0.01) {
        formulaZoom = target;
        clearTimeout(settleTimer);
        settleTimer = setTimeout(renderFormulaPages, 90);
      }
    }, { passive: false });

    scroll.addEventListener('touchend', (e) => {
      if (e.touches.length < 2) pinching = false;
    }, { passive: true });

    // Re-fit on rotation / resize while the panel is open (iPad orientation).
    let resizeTimer = null;
    window.addEventListener('resize', () => {
      const panel = document.getElementById('formula-panel');
      if (!formulaDoc || !panel || !panel.classList.contains('open')) return;
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(renderFormulaPages, 200);
    });
  }

  function openFormula() {
    const btn = document.getElementById('btn-formula');
    const panel = document.getElementById('formula-panel');
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    if (btn) btn.setAttribute('aria-expanded', 'true');
    // Re-render to the panel's actual width once it has slid into place.
    if (formulaDoc) setTimeout(renderFormulaPages, 340);
  }

  function closeFormula() {
    const btn = document.getElementById('btn-formula');
    const panel = document.getElementById('formula-panel');
    if (!panel) return;
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    if (btn) btn.setAttribute('aria-expanded', 'false');
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

    // Escape closes the formula sheet if it's open.
    document.onkeydown = (e) => {
      if (e.key === 'Escape') {
        const panel = document.getElementById('formula-panel');
        if (panel && panel.classList.contains('open')) closeFormula();
      }
    };
  }

  // Hide the formula button + panel when leaving the exam view.
  function teardownFormulaSheet() {
    closeFormula();
    const btn = document.getElementById('btn-formula');
    if (btn) btn.style.display = 'none';
    document.onkeydown = null;
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
    teardownFormulaSheet();

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
