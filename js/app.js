/* app.js — router, data loading, home + library rendering.
 *
 * Loads data/manifest.json once, then drives the single-page views:
 *   home  -> exam counts + track entry points
 *   library-FM / library-P -> list up to 10 exams (labelled #1..#N by position)
 *   exam  -> Exam module takes over
 *   results -> Results module takes over
 */
const App = (() => {
  let manifest = { FM: [], P: [] };
  const examCache = {};   // file -> exam JSON

  // ---- data ----
  async function loadManifest() {
    try {
      const res = await fetch('data/manifest.json', { cache: 'no-store' });
      if (!res.ok) throw new Error('manifest missing');
      manifest = await res.json();
      manifest.FM = manifest.FM || [];
      manifest.P = manifest.P || [];
    } catch (e) {
      manifest = { FM: [], P: [] };
    }
  }

  async function loadExam(file) {
    if (examCache[file]) return examCache[file];
    const res = await fetch(file, { cache: 'no-store' });
    if (!res.ok) throw new Error('exam file missing: ' + file);
    const data = await res.json();
    examCache[file] = data;
    return data;
  }

  // ---- view switching ----
  function showView(id) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    window.scrollTo(0, 0);
  }

  function setActiveNav(nav) {
    document.querySelectorAll('.nav-link').forEach(b => {
      b.classList.toggle('active', b.dataset.nav === nav);
    });
  }

  // ---- home ----
  function renderHome() {
    ['FM', 'P'].forEach(track => {
      const n = (manifest[track] || []).length;
      const el = document.getElementById('home-count-' + track);
      if (el) el.textContent = n === 0
        ? 'No exams yet'
        : `${n} exam${n === 1 ? '' : 's'} available`;
    });
    showView('view-home');
    setActiveNav('home');
  }

  // ---- library ----
  function renderLibrary(track) {
    const list = manifest[track] || [];
    document.getElementById('library-title').textContent =
      (track === 'FM' ? 'Exam FM' : 'Exam P') + ' — Library';

    const container = document.getElementById('library-list');
    container.innerHTML = '';

    if (list.length === 0) {
      container.innerHTML =
        `<div class="empty-state">No ${track} practice exams have been published yet.<br>
         Check back soon — new exams are added periodically.</div>`;
    } else {
      // Newest last in manifest; display #1..#N with newest highest number.
      list.forEach((entry, idx) => {
        const number = idx + 1;
        const result = Storage.getResult(entry.id);
        const row = document.createElement('div');
        row.className = 'exam-row';

        const badges = [];
        if (result) {
          badges.push('<span class="badge badge-taken">Taken</span>');
          badges.push(`<span class="badge badge-score">${result.correct}/${result.total}</span>`);
        }

        row.innerHTML = `
          <div class="exam-info">
            <div class="exam-title">${track} Practice Exam #${number} ${badges.join(' ')}</div>
            <div class="exam-sub">${entry.questions} questions &middot; ${formatMinutes(entry.timeLimitMinutes)} &middot; added ${formatDate(entry.created)}</div>
          </div>
          <div class="exam-actions">
            ${result
              ? `<button class="btn btn-secondary btn-small" data-review="${entry.file}">Review &amp; Solutions</button>`
              : ''}
            <button class="btn btn-secondary btn-small" data-pdf="${entry.file}">PDF: Problems</button>
            <button class="btn btn-secondary btn-small" data-pdf-sol="${entry.file}">PDF: Solutions</button>
            <button class="btn btn-primary btn-small" data-start="${entry.file}">
              ${result ? 'Retake' : 'Start Exam'}
            </button>
          </div>`;
        container.appendChild(row);
      });
    }

    showView('view-library');
    setActiveNav('library-' + track);
  }

  // ---- helpers ----
  function formatMinutes(min) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
  }
  function formatDate(iso) {
    try {
      return new Date(iso).toLocaleDateString(undefined,
        { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) { return ''; }
  }

  function toast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove('show'), 2600);
  }

  // ---- navigation dispatch ----
  function navigate(nav) {
    if (nav === 'home') return renderHome();
    if (nav === 'library-FM') return renderLibrary('FM');
    if (nav === 'library-P') return renderLibrary('P');
  }

  async function handleStart(file) {
    try {
      const exam = await loadExam(file);
      Exam.start(exam);
    } catch (e) {
      toast('Could not load that exam.');
    }
  }

  async function handleReview(file) {
    try {
      const exam = await loadExam(file);
      const result = Storage.getResult(exam.id);
      Results.showReview(exam, result);
    } catch (e) {
      toast('Could not load that exam.');
    }
  }

  async function handlePdf(file, withSolutions) {
    try {
      const exam = await loadExam(file);
      toast('Building PDF…');
      await PDF.build(exam, withSolutions);
    } catch (e) {
      toast('PDF export failed.');
      console.error(e);
    }
  }

  // ---- init ----
  async function init() {
    document.getElementById('footer-year').textContent = new Date().getFullYear();

    await loadManifest();
    renderHome();

    // Global click delegation
    document.addEventListener('click', (e) => {
      const t = e.target.closest('[data-nav]');
      if (t) { navigate(t.dataset.nav); return; }

      const start = e.target.closest('[data-start]');
      if (start) { handleStart(start.dataset.start); return; }

      const review = e.target.closest('[data-review]');
      if (review) { handleReview(review.dataset.review); return; }

      const pdf = e.target.closest('[data-pdf]');
      if (pdf) { handlePdf(pdf.dataset.pdf, false); return; }

      const pdfSol = e.target.closest('[data-pdf-sol]');
      if (pdfSol) { handlePdf(pdfSol.dataset.pdfSol, true); return; }
    });
  }

  return { init, showView, setActiveNav, renderLibrary, renderHome, toast, loadExam };
})();

document.addEventListener('DOMContentLoaded', App.init);
