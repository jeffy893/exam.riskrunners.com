/* storage.js — per-device persistence of exam results.
 *
 * The site itself is static; the ONLY dynamic per-user state is "which exams
 * has this person taken, and what did they score." We keep that in
 * localStorage keyed by exam id, so the home/library screens can show a
 * "Taken" badge and the last score, and the review screen can reload answers.
 *
 * Shape stored under key `rr_exam_results`:
 *   {
 *     "<examId>": {
 *        answers: { "1": "C", "2": "A", ... },   // question number -> chosen letter
 *        correct: 24,
 *        total: 30,
 *        elapsedSeconds: 5123,
 *        completedAt: "2026-09-14T..."
 *     }
 *   }
 */
const Storage = (() => {
  const KEY = 'rr_exam_results';

  function _all() {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || {};
    } catch (e) {
      return {};
    }
  }

  function _save(obj) {
    try {
      localStorage.setItem(KEY, JSON.stringify(obj));
    } catch (e) {
      /* storage full / disabled — fail silently, site still works */
    }
  }

  return {
    getResult(examId) {
      return _all()[examId] || null;
    },
    hasTaken(examId) {
      return !!_all()[examId];
    },
    saveResult(examId, result) {
      const all = _all();
      all[examId] = result;
      _save(all);
    },
    clearResult(examId) {
      const all = _all();
      delete all[examId];
      _save(all);
    }
  };
})();
