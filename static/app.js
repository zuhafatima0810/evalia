/**
 * Evalia - Production Frontend Application Controller
 * Handles CSV ingestion, live GPA scale toggling, student search/filtering,
 * PDF preview modals, and batch export triggers.
 * Strictly adheres to design.md with zero emojis.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  let activeScale = '10.0';
  let activeData = null;
  let activeStatusFilter = 'all';
  let searchQuery = '';

  // DOM Elements
  const dropzoneCard = document.getElementById('dropzoneCard');
  const csvFileInput = document.getElementById('csvFileInput');
  const btnBrowseFile = document.getElementById('btnBrowseFile');
  const btnLoadSampleDirect = document.getElementById('btnLoadSampleDirect');
  const btnLoadSampleNav = document.getElementById('btnLoadSampleNav');
  const alertBanner = document.getElementById('alertBanner');
  const alertTitle = document.getElementById('alertTitle');
  const alertMessage = document.getElementById('alertMessage');
  const alertErrorList = document.getElementById('alertErrorList');
  const alertCloseBtn = document.getElementById('alertCloseBtn');
  const resultsWorkspace = document.getElementById('resultsWorkspace');

  // Controls & KPI
  const scaleBtn10 = document.getElementById('scaleBtn10');
  const scaleBtn4 = document.getElementById('scaleBtn4');
  const scaleCaption = document.getElementById('scaleCaption');
  const btnExportExcel = document.getElementById('btnExportExcel');
  const btnDownloadAllPdf = document.getElementById('btnDownloadAllPdf');
  const btnClearResults = document.getElementById('btnClearResults');
  const btnToggleCreditsDrawer = document.getElementById('btnToggleCreditsDrawer');
  const badgeCreditsTotal = document.getElementById('badgeCreditsTotal');
  const creditsDrawerCard = document.getElementById('creditsDrawerCard');
  const creditsInputsGrid = document.getElementById('creditsInputsGrid');
  const btnApplyCredits = document.getElementById('btnApplyCredits');

  const kpiTotalStudents = document.getElementById('kpiTotalStudents');
  const kpiPassedFailedCount = document.getElementById('kpiPassedFailedCount');
  const kpiClassAverage = document.getElementById('kpiClassAverage');
  const kpiAvgGpa = document.getElementById('kpiAvgGpa');
  const kpiPassRate = document.getElementById('kpiPassRate');
  const kpiTopPerformer = document.getElementById('kpiTopPerformer');
  const kpiHighestScore = document.getElementById('kpiHighestScore');

  // Distribution
  const distributionBar = document.getElementById('distributionBar');
  const gradeChipsGrid = document.getElementById('gradeChipsGrid');

  // Table & Filters
  const searchInput = document.getElementById('searchInput');
  const filterPills = document.querySelectorAll('.filter-pill');
  const tableHeaderRow = document.getElementById('tableHeaderRow');
  const tableBody = document.getElementById('tableBody');
  const tableRecordCount = document.getElementById('tableRecordCount');
  const thGpa = document.getElementById('thGpa');

  // Modal
  const pdfModal = document.getElementById('pdfModal');
  const modalStudentName = document.getElementById('modalStudentName');
  const modalStudentMeta = document.getElementById('modalStudentMeta');
  const pdfPreviewFrame = document.getElementById('pdfPreviewFrame');
  const modalBtnNewTab = document.getElementById('modalBtnNewTab');
  const modalBtnDownload = document.getElementById('modalBtnDownload');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  // =========================================================================
  // ALERT / NOTIFICATION UTILITIES
  // =========================================================================
  function showAlert(title, message, errorList = []) {
    alertTitle.textContent = title || 'Notice';
    alertMessage.textContent = message || '';
    alertErrorList.innerHTML = '';

    if (errorList && errorList.length > 0) {
      alertErrorList.style.display = 'block';
      errorList.slice(0, 10).forEach(err => {
        const li = document.createElement('li');
        li.textContent = err;
        alertErrorList.appendChild(li);
      });
      if (errorList.length > 10) {
        const extraLi = document.createElement('li');
        extraLi.textContent = `... and ${errorList.length - 10} additional error(s).`;
        alertErrorList.appendChild(extraLi);
      }
    } else {
      alertErrorList.style.display = 'none';
    }

    alertBanner.style.display = 'flex';
    alertBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function hideAlert() {
    alertBanner.style.display = 'none';
  }

  alertCloseBtn.addEventListener('click', hideAlert);

  // =========================================================================
  // FILE SELECTION & DRAG-AND-DROP
  // =========================================================================
  btnBrowseFile.addEventListener('click', () => {
    csvFileInput.click();
  });

  csvFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleCsvUpload(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzoneCard.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzoneCard.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzoneCard.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzoneCard.classList.remove('dragover');
    });
  });

  dropzoneCard.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      handleCsvUpload(dt.files[0]);
    }
  });

  // =========================================================================
  // API REQUESTS: CSV UPLOAD & SAMPLE LOADING
  // =========================================================================
  async function handleCsvUpload(file) {
    hideAlert();
    if (!file.name.toLowerCase().endsWith('.csv')) {
      showAlert('Invalid File Format', 'Please upload a file ending with the .csv extension.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('scale', activeScale);

    try {
      btnBrowseFile.disabled = true;
      btnBrowseFile.textContent = 'Processing CSV...';

      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      const json = await res.json();
      if (!res.ok || !json.success) {
        showAlert('CSV Validation Error', json.message || 'Failed to parse CSV.', json.errors || []);
        return;
      }

      activeData = json.data;
      renderAll();
      resultsWorkspace.style.display = 'block';
      resultsWorkspace.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showAlert('Network Error', `Could not upload file: ${err.message}`);
    } finally {
      btnBrowseFile.disabled = false;
      btnBrowseFile.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        Select CSV File
      `;
    }
  }

  async function loadSampleCohort() {
    hideAlert();
    try {
      const res = await fetch(`/api/sample?scale=${activeScale}`);
      const json = await res.json();
      if (!res.ok || !json.success) {
        showAlert('Error', json.message || 'Could not load sample cohort.');
        return;
      }

      activeData = json.data;
      renderAll();
      resultsWorkspace.style.display = 'block';
      resultsWorkspace.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      showAlert('Network Error', `Could not load sample data: ${err.message}`);
    }
  }

  btnLoadSampleDirect.addEventListener('click', loadSampleCohort);
  btnLoadSampleNav.addEventListener('click', loadSampleCohort);

  // =========================================================================
  // LIVE GPA SCALE SWITCHING
  // =========================================================================
  async function switchGpaScale(newScale) {
    if (activeScale === newScale) return;
    activeScale = newScale;

    if (newScale === '10.0') {
      scaleBtn10.classList.add('active');
      scaleBtn4.classList.remove('active');
      scaleCaption.textContent = 'Standard 10.0 Scale (A+: 10, A: 9, B+: 8, B: 7, C: 6, D: 5, F: 0)';
    } else {
      scaleBtn4.classList.add('active');
      scaleBtn10.classList.remove('active');
      scaleCaption.textContent = 'Standard 4.0 Scale (A+: 4.0, A: 3.7, B+: 3.3, B: 3.0, C: 2.0, D: 1.0, F: 0.0)';
    }

    if (activeData) {
      try {
        const res = await fetch('/api/switch-scale', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scale: activeScale })
        });
        const json = await res.json();
        if (json.success && json.data) {
          activeData = json.data;
          renderAll();
        }
      } catch (e) {
        // Fallback: render with existing data client-side
        renderAll();
      }
    }
  }

  scaleBtn10.addEventListener('click', () => switchGpaScale('10.0'));
  scaleBtn4.addEventListener('click', () => switchGpaScale('4.0'));

  // =========================================================================
  // RENDERING ENGINE
  // =========================================================================
  function renderAll() {
    if (!activeData) return;
    renderKPIs();
    renderDistribution();
    renderCreditsDrawer();
    renderTable();
  }

  function renderKPIs() {
    const a = activeData.analytics;
    kpiTotalStudents.textContent = a.total_students;
    kpiPassedFailedCount.textContent = `${a.passed_count} Passed • ${a.failed_count} Remediated`;
    kpiClassAverage.textContent = `${a.class_average.toFixed(2)}%`;

    const avgGpa = activeScale === '10.0' ? a.avg_gpa_10 : a.avg_gpa_4;
    const maxGpa = activeScale === '10.0' ? '10.00' : '4.00';
    const totalCr = a.total_credits || activeData.total_credits || 0;
    kpiAvgGpa.textContent = `Weighted GPA: ${avgGpa.toFixed(2)} / ${maxGpa} (${totalCr} Credits)`;

    kpiPassRate.textContent = `${a.pass_rate.toFixed(1)}%`;
    kpiTopPerformer.textContent = a.top_performer || 'None';
    kpiHighestScore.textContent = `Cohort Rank #1 • ${a.highest_percentage.toFixed(2)}%`;
  }

  function renderDistribution() {
    const dist = activeData.analytics.grade_distribution;
    distributionBar.innerHTML = '';
    gradeChipsGrid.innerHTML = '';

    dist.forEach(item => {
      // Progress bar segment
      if (item.percentage > 0) {
        const seg = document.createElement('div');
        const safeGradeClass = item.grade.replace('+', '-plus');
        seg.className = `dist-bar-seg dist-bar-${safeGradeClass}`;
        seg.style.width = `${item.percentage}%`;
        seg.title = `${item.grade}: ${item.count} students (${item.percentage}%)`;
        distributionBar.appendChild(seg);
      }

      // Breakdown Card
      const chip = document.createElement('div');
      chip.className = 'grade-chip';
      const gp = activeScale === '10.0' ? item.points_10 : item.points_4;
      chip.innerHTML = `
        <div class="chip-grade">${item.grade}</div>
        <div class="chip-count">${item.count}</div>
        <div class="chip-pct">${item.percentage}% • ${gp.toFixed(1)} GP</div>
      `;
      gradeChipsGrid.appendChild(chip);
    });
  }

  function renderCreditsDrawer() {
    if (!activeData) return;
    const credits = activeData.subject_credits || {};
    const subjectCols = activeData.subject_columns || [];
    const totalCr = activeData.total_credits || Object.values(credits).reduce((sum, c) => sum + (parseFloat(c) || 0), 0);

    if (badgeCreditsTotal) {
      badgeCreditsTotal.textContent = `${totalCr} Cr`;
    }

    if (!creditsInputsGrid) return;
    creditsInputsGrid.innerHTML = '';

    subjectCols.forEach(subj => {
      const cr = credits[subj] !== undefined ? credits[subj] : 4;
      const card = document.createElement('div');
      card.className = 'credit-course-card';
      card.innerHTML = `
        <div class="credit-course-name" title="${subj}">${subj}</div>
        <div class="credit-input-group">
          <input type="number" step="0.5" min="0.5" max="20" class="credit-input-field" data-subject="${subj}" value="${cr}">
          <span class="credit-input-unit">Cr</span>
        </div>
      `;
      creditsInputsGrid.appendChild(card);
    });
  }

  function renderTable() {
    const students = activeData.students || [];
    const subjectCols = activeData.subject_columns || [];
    const subjCredits = activeData.subject_credits || {};

    // 1. Build Header Row Dynamically
    const gpaLabel = activeScale === '10.0' ? 'Weighted GPA (10.0)' : 'Weighted GPA (4.0)';
    let headerHtml = `
      <th class="col-center">Rank</th>
      <th>Student ID</th>
      <th>Name</th>
      <th>Class</th>
    `;

    subjectCols.forEach(col => {
      const cr = subjCredits[col] !== undefined ? subjCredits[col] : 4;
      headerHtml += `
        <th class="col-right">
          <div class="th-subject-wrap">
            <span>${col}</span>
            <span class="th-credit-badge">${cr} Cr</span>
          </div>
        </th>
      `;
    });

    headerHtml += `
      <th class="col-right">Total</th>
      <th class="col-right">Percentage</th>
      <th class="col-right" id="thGpa">${gpaLabel}</th>
      <th class="col-center">Grade</th>
      <th class="col-center">Status</th>
      <th class="col-center">Official Transcript</th>
    `;
    tableHeaderRow.innerHTML = headerHtml;

    // 2. Filter Students
    const query = searchQuery.trim().toLowerCase();
    const filtered = students.filter(s => {
      // Status filter
      if (activeStatusFilter !== 'all' && s.status !== activeStatusFilter) {
        return false;
      }
      // Text search
      if (query) {
        const matchName = s.name.toLowerCase().includes(query);
        const matchId = s.student_id.toLowerCase().includes(query);
        const matchClass = s.class_name.toLowerCase().includes(query);
        if (!matchName && !matchId && !matchClass) {
          return false;
        }
      }
      return true;
    });

    tableRecordCount.textContent = `Showing ${filtered.length} of ${students.length} students`;
    tableBody.innerHTML = '';

    if (filtered.length === 0) {
      const emptyRow = document.createElement('tr');
      const totalCols = 4 + subjectCols.length + 6;
      emptyRow.innerHTML = `
        <td colspan="${totalCols}" style="text-align: center; padding: 32px; color: var(--color-muted);">
          No student records match the active search or status filter.
        </td>
      `;
      tableBody.appendChild(emptyRow);
      return;
    }

    // 3. Render Student Rows
    filtered.forEach(s => {
      const tr = document.createElement('tr');

      const isFirst = s.rank === 1;
      const rankBadgeClass = isFirst ? 'rank-badge rank-first' : 'rank-badge';

      let rowHtml = `
        <td class="col-center"><span class="${rankBadgeClass}">${s.rank}</span></td>
        <td><code>${s.student_id}</code></td>
        <td class="student-name-cell">${s.name}</td>
        <td>${s.class_name}</td>
      `;

      // Subject scores
      const subjMap = {};
      s.subjects.forEach(sub => {
        subjMap[sub.subject] = sub;
      });

      subjectCols.forEach(sc => {
        const subData = subjMap[sc];
        const val = subData ? subData.marks_obtained.toFixed(1) : '--';
        const isSubFail = subData && subData.marks_obtained < 40;
        const style = isSubFail ? 'color: var(--color-semantic-error); font-weight: 600;' : '';
        rowHtml += `<td class="col-right" style="${style}">${val}</td>`;
      });

      const gpa = activeScale === '10.0' ? s.gpa_10 : s.gpa_4;
      const statusBadgeClass = s.status === 'Passed' ? 'status-badge badge-pass' : 'status-badge badge-fail';

      rowHtml += `
        <td class="col-right">${s.total_marks.toFixed(1)}</td>
        <td class="col-right"><b>${s.percentage.toFixed(2)}%</b></td>
        <td class="col-right"><b>${gpa.toFixed(2)}</b></td>
        <td class="col-center"><b>${s.grade}</b></td>
        <td class="col-center"><span class="${statusBadgeClass}">${s.status.toUpperCase()}</span></td>
        <td class="col-center">
          <div class="action-buttons">
            <button type="button" class="btn-icon btn-preview-pdf" data-id="${s.student_id}" title="Preview PDF Transcript" aria-label="Preview Transcript for ${s.name}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
            <a href="/api/pdf/${encodeURIComponent(s.student_id)}?scale=${activeScale}&download=1" class="btn-icon" title="Download PDF Transcript" aria-label="Download Transcript for ${s.name}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </a>
          </div>
        </td>
      `;

      tr.innerHTML = rowHtml;
      tableBody.appendChild(tr);
    });

    // Attach preview event listeners
    document.querySelectorAll('.btn-preview-pdf').forEach(btn => {
      btn.addEventListener('click', () => {
        const studentId = btn.getAttribute('data-id');
        openPdfPreview(studentId);
      });
    });
  }

  // =========================================================================
  // SEARCH & FILTER HANDLERS
  // =========================================================================
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value;
    renderTable();
  });

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeStatusFilter = pill.getAttribute('data-filter');
      renderTable();
    });
  });

  // =========================================================================
  // PDF PREVIEW MODAL
  // =========================================================================
  function openPdfPreview(studentId) {
    if (!activeData) return;
    const student = activeData.students.find(s => s.student_id === studentId);
    if (!student) return;

    modalStudentName.textContent = `${student.name} — Official Academic Transcript`;
    modalStudentMeta.textContent = `ID: ${student.student_id} • Class: ${student.class_name} • Rank: #${student.rank}`;

    const pdfUrl = `/api/pdf/${encodeURIComponent(studentId)}?scale=${activeScale}`;
    pdfPreviewFrame.src = pdfUrl;
    modalBtnNewTab.href = pdfUrl;
    modalBtnDownload.href = `${pdfUrl}&download=1`;

    pdfModal.style.display = 'flex';
  }

  function closePdfModal() {
    pdfModal.style.display = 'none';
    pdfPreviewFrame.src = 'about:blank';
  }

  modalCloseBtn.addEventListener('click', closePdfModal);
  pdfModal.addEventListener('click', (e) => {
    if (e.target === pdfModal) {
      closePdfModal();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && pdfModal.style.display === 'flex') {
      closePdfModal();
    }
  });

  // =========================================================================
  // COURSE CREDITS CONFIGURATION
  // =========================================================================
  if (btnToggleCreditsDrawer && creditsDrawerCard) {
    btnToggleCreditsDrawer.addEventListener('click', () => {
      const isHidden = window.getComputedStyle(creditsDrawerCard).display === 'none';
      creditsDrawerCard.style.display = isHidden ? 'block' : 'none';
      btnToggleCreditsDrawer.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
      if (isHidden) {
        creditsDrawerCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  }

  if (btnApplyCredits) {
    btnApplyCredits.addEventListener('click', async () => {
      if (!creditsInputsGrid) return;
      const inputs = creditsInputsGrid.querySelectorAll('.credit-input-field');
      const updatedCredits = {};
      let hasError = false;

      inputs.forEach(inp => {
        const val = parseFloat(inp.value);
        if (isNaN(val) || val <= 0) {
          hasError = true;
        } else {
          updatedCredits[inp.getAttribute('data-subject')] = val;
        }
      });

      if (hasError) {
        showAlert('Invalid Credit Allocation', 'Every course must have a positive numeric credit value (e.g. 1.0, 3.0, 4.0).');
        return;
      }

      try {
        btnApplyCredits.disabled = true;
        btnApplyCredits.textContent = 'Recalculating...';

        const res = await fetch('/api/update-credits', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ credits: updatedCredits })
        });

        const json = await res.json();
        if (!res.ok || !json.success) {
          showAlert('Calculation Error', json.message || 'Failed to update course credits.');
          return;
        }

        activeData = json.data;
        renderAll();
      } catch (err) {
        showAlert('Network Error', `Could not update course credits: ${err.message}`);
      } finally {
        btnApplyCredits.disabled = false;
        btnApplyCredits.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Apply Credits &amp; Recalculate
        `;
      }
    });
  }

  // =========================================================================
  // BATCH EXPORTS & ACTIONS
  // =========================================================================
  btnExportExcel.addEventListener('click', () => {
    window.location.href = `/api/export-excel?scale=${activeScale}`;
  });

  btnDownloadAllPdf.addEventListener('click', () => {
    window.location.href = `/api/download-all-pdfs?scale=${activeScale}`;
  });

  if (btnClearResults) {
    btnClearResults.addEventListener('click', () => {
      activeData = null;
      resultsWorkspace.style.display = 'none';
      if (creditsDrawerCard) creditsDrawerCard.style.display = 'none';
      if (csvFileInput) csvFileInput.value = '';
      if (searchInput) searchInput.value = '';
      searchQuery = '';
      activeStatusFilter = 'all';
      filterPills.forEach(p => {
        if (p.getAttribute('data-filter') === 'all') p.classList.add('active');
        else p.classList.remove('active');
      });
      fetch('/api/clear', { method: 'POST' }).catch(() => {});
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Results remain hidden on initial load until the user explicitly clicks
  // "Load Sample Dataset" or uploads their own CSV file.
});
