/* clipboard.js — copy a problem to the clipboard as clean plain text.
 *
 * Used from both the exam view (problem + choices only, no answer) and the
 * review view (problem + choices + correct answer + worked solution), so a
 * candidate can paste it into an LLM for a personal walk-through.
 *
 * Includes a fallback (document.execCommand) for iPad/Safari contexts where
 * navigator.clipboard is unavailable (e.g. non-HTTPS origins).
 */
const Clipboard = (() => {

  function formatProblem(q, { includeSolution }) {
    const lines = [];
    lines.push(`Question ${q.n} — ${q.topic}`);
    lines.push('');
    lines.push(q.stem);
    lines.push('');
    Object.entries(q.choices).forEach(([letter, text]) => {
      lines.push(`${letter}. ${text}`);
    });
    if (includeSolution) {
      lines.push('');
      lines.push(`Correct answer: ${q.answer} (${q.answerValue})`);
      lines.push('');
      lines.push('Worked solution:');
      lines.push(q.solution);
    } else {
      lines.push('');
      lines.push('Please walk me through how to solve this step by step.');
    }
    return lines.join('\n');
  }

  function _fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, ta.value.length);
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  function _flash(btn, ok) {
    if (!btn) return;
    const original = btn.innerHTML;
    btn.classList.add(ok ? 'copied' : 'copy-failed');
    btn.innerHTML = ok
      ? '<span class="copy-icon">✓</span> Copied'
      : '<span class="copy-icon">!</span> Copy failed';
    clearTimeout(btn._copyT);
    btn._copyT = setTimeout(() => {
      btn.classList.remove('copied', 'copy-failed');
      btn.innerHTML = original;
    }, 1600);
  }

  async function copyProblem(q, btn, opts = {}) {
    if (!q) return;
    const text = formatProblem(q, { includeSolution: !!opts.includeSolution });
    let ok = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        ok = true;
      } else {
        ok = _fallbackCopy(text);
      }
    } catch (e) {
      ok = _fallbackCopy(text);
    }
    _flash(btn, ok);
  }

  return { copyProblem, formatProblem };
})();
