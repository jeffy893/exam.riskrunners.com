/* pdf.js — client-side PDF export using jsPDF.
 *
 * Three exports:
 *   build(exam, withSolutions=false)
 *      false -> "Problems" PDF: one problem per page.
 *      true  -> "Solutions" PDF: problem on a page, its solution on the next
 *               page, so a reader can see a problem without seeing the answer.
 *   buildScorecard(exam, result) -> a one/two page results summary.
 *
 * Every document opens with an Integral MASS cover page carrying the author's
 * contact details and the Risk Runners signature links, and repeats a compact
 * footer signature on every page.
 */
const PDF = (() => {
  const AUTHOR = 'Jefferson Richards';
  const EMAIL = 'jefferson@richards.plus';
  const LINKS = [
    'Risk Runners Codebase — github.com/jeffy893/riskrunners',
    'Street Math — street.riskrunners.com',
    'Connect with the Founder — jeffersonrichards.com',
    'Actuarial Wiki — www.riskrunners.com'
  ];

  // color palette (matches the site's academic indigo)
  const INK = [43, 42, 38];
  const INDIGO = [58, 74, 122];
  const MUTED = [138, 133, 119];

  const MARGIN = 56;          // pt
  const LOGO_URL = 'assets/rr-exam-logo.png';
  let doc, pageW, pageH, contentW;
  let _logoData = null;       // cached { dataUrl, w, h }

  // Load the logo once as a data URL (jsPDF needs raster data, not a URL).
  function _loadLogo() {
    if (_logoData !== null) return Promise.resolve(_logoData);
    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          canvas.getContext('2d').drawImage(img, 0, 0);
          _logoData = {
            dataUrl: canvas.toDataURL('image/png'),
            w: img.naturalWidth,
            h: img.naturalHeight
          };
        } catch (e) {
          _logoData = false;  // canvas tainted or failed; skip logo gracefully
        }
        resolve(_logoData);
      };
      img.onerror = () => { _logoData = false; resolve(_logoData); };
      img.src = LOGO_URL;
    });
  }

  function _newDoc() {
    const { jsPDF } = window.jspdf;
    doc = new jsPDF({ unit: 'pt', format: 'letter' });
    pageW = doc.internal.pageSize.getWidth();
    pageH = doc.internal.pageSize.getHeight();
    contentW = pageW - MARGIN * 2;
  }

  function _footerSignature() {
    const total = doc.internal.getNumberOfPages();
    for (let i = 1; i <= total; i++) {
      doc.setPage(i);
      doc.setDrawColor(226, 218, 201);
      doc.setLineWidth(0.5);
      doc.line(MARGIN, pageH - 42, pageW - MARGIN, pageH - 42);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(...MUTED);
      doc.text('\u00A9 ' + new Date().getFullYear() +
        ' Integral MASS  \u2022  ' + AUTHOR + '  \u2022  ' + EMAIL,
        MARGIN, pageH - 28);
      doc.text('exam.riskrunners.com', pageW - MARGIN, pageH - 28, { align: 'right' });
      if (i > 1) {
        doc.text('Page ' + (i - 1), pageW / 2, pageH - 28, { align: 'center' });
      }
    }
  }

  function _coverPage(exam, docType) {
    // Top brand — logo if we have it, otherwise a text header.
    if (_logoData && _logoData.dataUrl) {
      const logoW = 190;
      const logoH = logoW * (_logoData.h / _logoData.w);
      doc.addImage(_logoData.dataUrl, 'PNG',
        (pageW - logoW) / 2, MARGIN, logoW, logoH, undefined, 'FAST');
    } else {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(...INDIGO);
      doc.text('RISK RUNNERS  \u2022  ACTUARIAL EXAM PREP',
        pageW / 2, MARGIN + 6, { align: 'center' });
      doc.setDrawColor(...INDIGO);
      doc.setLineWidth(1.5);
      doc.line(MARGIN, MARGIN + 16, pageW - MARGIN, MARGIN + 16);
    }

    // Title block
    let y = pageH * 0.38;
    doc.setFont('times', 'bold');
    doc.setFontSize(30);
    doc.setTextColor(...INK);
    doc.text(`Exam ${exam.track}`, pageW / 2, y, { align: 'center' });
    y += 30;
    doc.setFontSize(18);
    doc.setTextColor(...INDIGO);
    doc.text(exam.trackName || '', pageW / 2, y, { align: 'center' });
    y += 34;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(13);
    doc.setTextColor(...INK);
    doc.text(docType, pageW / 2, y, { align: 'center' });

    y += 40;
    doc.setFontSize(10.5);
    doc.setTextColor(...MUTED);
    doc.text(
      `${exam.questions.length} questions  \u2022  5 choices each  \u2022  ` +
      `${exam.config.timeLimitMinutes} minute time limit`,
      pageW / 2, y, { align: 'center' });
    y += 16;
    doc.text('Society of Actuaries — Exam ' + exam.track + ' practice set',
      pageW / 2, y, { align: 'center' });

    // Author / contact block
    y = pageH * 0.72;
    doc.setDrawColor(226, 218, 201);
    doc.setLineWidth(0.5);
    doc.line(MARGIN, y, pageW - MARGIN, y);
    y += 22;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10.5);
    doc.setTextColor(...INK);
    doc.text('Prepared by ' + AUTHOR, pageW / 2, y, { align: 'center' });
    y += 15;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(...MUTED);
    doc.text(EMAIL, pageW / 2, y, { align: 'center' });
    y += 18;
    LINKS.forEach(l => {
      doc.text(l, pageW / 2, y, { align: 'center' });
      y += 12;
    });
    y += 6;
    doc.setFont('helvetica', 'italic');
    doc.text('\u00A9 ' + new Date().getFullYear() + ' Integral MASS. All rights reserved.',
      pageW / 2, y, { align: 'center' });
  }

  // Write a problem starting at top of the current page. Returns nothing; each
  // problem is designed to own its page.
  function _renderProblem(q) {
    let y = MARGIN + 10;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...INDIGO);
    doc.text('Question ' + q.n, MARGIN, y);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    doc.setTextColor(...MUTED);
    doc.text(q.topic.toUpperCase(), pageW - MARGIN, y, { align: 'right' });

    y += 22;
    doc.setFont('times', 'normal');
    doc.setFontSize(12);
    doc.setTextColor(...INK);
    const stem = doc.splitTextToSize(q.stem, contentW);
    doc.text(stem, MARGIN, y);
    y += stem.length * 15 + 14;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    Object.entries(q.choices).forEach(([letter, text]) => {
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...INDIGO);
      doc.text(letter + '.', MARGIN, y);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...INK);
      const lines = doc.splitTextToSize(String(text), contentW - 24);
      doc.text(lines, MARGIN + 22, y);
      y += lines.length * 14 + 8;
    });
  }

  function _renderSolution(q) {
    let y = MARGIN + 10;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...INDIGO);
    doc.text('Solution to Question ' + q.n, MARGIN, y);
    y += 22;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(47, 125, 111);   // teal
    doc.text('Correct answer: ' + q.answer + '   (' + q.answerValue + ')', MARGIN, y);
    y += 22;

    doc.setFont('courier', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...INK);
    const sol = doc.splitTextToSize(q.solution, contentW);
    sol.forEach(line => {
      if (y > pageH - 70) { doc.addPage(); y = MARGIN + 10; }
      doc.text(line, MARGIN, y);
      y += 15;
    });
  }

  async function build(exam, withSolutions) {
    if (!window.jspdf) { App.toast('PDF library still loading — try again.'); return; }
    await _loadLogo();
    _newDoc();
    _coverPage(exam, withSolutions ? 'Problems & Solutions' : 'Practice Problems');

    exam.questions.forEach(q => {
      doc.addPage();
      _renderProblem(q);
      if (withSolutions) {
        doc.addPage();
        _renderSolution(q);
      }
    });

    _footerSignature();
    const suffix = withSolutions ? 'problems-solutions' : 'problems';
    doc.save(`${exam.track}-practice-exam-${suffix}.pdf`);
    App.toast('PDF downloaded.');
  }

  async function buildScorecard(exam, res) {
    if (!window.jspdf) { App.toast('PDF library still loading — try again.'); return; }
    await _loadLogo();
    _newDoc();
    _coverPage(exam, 'Exam Scorecard');
    doc.addPage();

    let y = MARGIN + 20;
    doc.setFont('times', 'bold');
    doc.setFontSize(22);
    doc.setTextColor(...INK);
    doc.text('Scorecard', MARGIN, y);
    y += 34;

    const pct = Math.round((res.correct / res.total) * 100);
    const rows = [
      ['Exam', `${exam.track} — ${exam.trackName}`],
      ['Score', `${res.correct} / ${res.total}  (${pct}%)`],
    ];
    if (exam.track === 'P') {
      const scaled = Math.round((res.correct / res.total) * 10);
      rows.push(['Scaled score', `${scaled} / 10  (${scaled >= 6 ? 'Pass' : 'Below 6'})`]);
    }
    rows.push(['Time used', formatDuration(res.elapsedSeconds) +
      ` of ${exam.config.timeLimitMinutes} min`]);
    rows.push(['Completed', new Date(res.completedAt).toLocaleString()]);

    doc.setFontSize(12);
    rows.forEach(([k, v]) => {
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(...INDIGO);
      doc.text(k, MARGIN, y);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(...INK);
      doc.text(String(v), MARGIN + 130, y);
      y += 24;
    });

    y += 10;
    doc.setDrawColor(226, 218, 201);
    doc.line(MARGIN, y, pageW - MARGIN, y);
    y += 26;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...INK);
    doc.text('Answer key', MARGIN, y);
    y += 20;

    doc.setFont('courier', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...INK);
    exam.questions.forEach(q => {
      const chosen = res.answers[q.n] || '-';
      const mark = chosen === q.answer ? 'correct' : (chosen === '-' ? 'blank' : 'wrong');
      if (y > pageH - 70) { doc.addPage(); y = MARGIN + 20; }
      doc.text(
        `Q${String(q.n).padStart(2, '0')}   your: ${chosen}   key: ${q.answer}   ${mark}`,
        MARGIN, y);
      y += 15;
    });

    _footerSignature();
    doc.save(`${exam.track}-scorecard.pdf`);
    App.toast('Scorecard downloaded.');
  }

  function formatDuration(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    if (h) return `${h}h ${m}m`;
    return `${m} min`;
  }

  return { build, buildScorecard };
})();
