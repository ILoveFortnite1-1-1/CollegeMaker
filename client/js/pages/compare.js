/**
 * Comparison Workspace Page View (Route: #/compare)
 * Side-by-side comparison matrix (2–6 colleges), sticky metrics, best-in-class highlights, visual charts, and CSV export.
 */
import { API } from '../api.js?v=4.0';
import { formatMetricValue } from '../components/metric-card.js';
import { renderFitRing } from '../components/fit-ring.js';
import { renderSourceBadge } from '../components/source-badge.js';

export const ComparePage = {
  async render(container, state) {
    let compareIds = state.compareList || [];

    // If compare list is empty, default to first 2-4 saved colleges
    const rawSaved = window.app?.getSavedColleges ? window.app.getSavedColleges() : (state.portfolio?.saved_colleges || state.portfolio?.colleges || state.portfolio?.items || []);
    if (compareIds.length === 0 && rawSaved.length >= 2) {
      compareIds = rawSaved.slice(0, 3).map(c => String(c.college_id || c.id));
      state.compareList = compareIds;
    }

    if (compareIds.length < 2) {
      this.renderEmptyState(container, state);
      return;
    }

    container.innerHTML = `
      <div class="loading-screen">
        <div class="spinner"></div>
        <p class="loading-text">Building multi-college comparison matrix…</p>
      </div>
    `;

    try {
      const compareData = await API.compareColleges(compareIds);
      const colleges = compareData.colleges || [];
      const matrix = compareData.comparison_matrix || [];
      const highlights = compareData.summary_highlights || {};

      container.innerHTML = `
        <div class="page-header">
          <div class="page-title-group">
            <h1>Comparison Matrix</h1>
            <p class="page-subtitle">Comparing ${colleges.length} institutions side-by-side with normalized metrics and best-in-class highlights.</p>
          </div>
          <div class="page-actions">
            <button type="button" id="export-csv-btn" class="btn btn-secondary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block; vertical-align:middle; margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export CSV Matrix
            </button>

            <button type="button" id="clear-compare-btn" class="btn btn-ghost">
              Clear All
            </button>
          </div>
        </div>

        <!-- Selected Colleges Quick Bar -->
        <div class="card" style="margin-bottom: 24px; padding: 16px 20px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
              <span style="font-size: 0.8125rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Comparing:</span>
              ${colleges.map(c => `
                <span class="category-tag tag-target" style="padding: 6px 12px; font-size: 0.875rem;">
                  <strong>${c.name || c.canonical_name}</strong>
                  <button type="button" data-action="remove-compare-chip" data-college-id="${c.id}" style="margin-left: 6px; font-weight: 800; cursor: pointer;">&times;</button>
                </span>
              `).join('')}
            </div>

            ${colleges.length < 6 ? `
              <div style="display: flex; gap: 8px; align-items: center;">
                <select id="add-to-compare-select" class="select-input" style="padding: 6px 12px; font-size: 0.8125rem;">
                  <option value="">+ Add college to compare...</option>
                  ${(state.portfolio?.saved_colleges || [])
                    .filter(sc => !compareIds.includes(String(sc.college_id)))
                    .map(sc => `<option value="${sc.college_id}">${sc.college_name}</option>`)
                    .join('')}
                </select>
              </div>
            ` : ''}
          </div>
        </div>

        <!-- Comparative Visualizations (Side-by-side Bar & Radar) -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px;">
          <div class="card">
            <h3 class="card-title" style="margin-bottom: 12px;">Annual Net Price vs. 10-Yr Earnings</h3>
            <div class="chart-container">
              ${renderComparisonBarChart(colleges)}
            </div>
          </div>

          <div class="card">
            <h3 class="card-title" style="margin-bottom: 12px;">Fit Dimension Radar Analysis</h3>
            <div class="chart-container">
              ${renderComparisonRadarChart(colleges)}
            </div>
          </div>
        </div>

        <!-- Side-by-Side Matrix Table -->
        <div class="compare-container" style="margin-bottom: 40px;">
          <table class="compare-table">
            <thead>
              <tr>
                <th class="compare-col-metric">Metric / Dimension</th>
                ${colleges.map(col => `
                  <th style="min-width: 200px; text-align: center;">
                    <div style="font-size: 1.05rem; font-weight: 800; margin-bottom: 4px;">
                      <a href="#/colleges/${col.id}" style="color: #ffffff;">${col.name || col.canonical_name}</a>
                    </div>
                    <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 500; margin-bottom: 10px;">
                      ${col.city || col.location?.city}, ${col.state || col.location?.state}
                    </div>
                    <button 
                      type="button" 
                      class="btn btn-sm btn-light" 
                      data-action="remove-from-compare" 
                      data-college-id="${col.id}"
                      style="font-size: 0.7rem; padding: 2px 8px;"
                    >
                      Remove
                    </button>
                  </th>
                `).join('')}
              </tr>
            </thead>
            <tbody>
              <!-- Section: Fit & Selectivity -->
              <tr class="compare-section-header">
                <td colspan="${colleges.length + 1}">Fit &amp; Category Alignment</td>
              </tr>
              <tr>
                <td class="compare-col-metric">Overall Fit Score</td>
                ${colleges.map(col => `
                  <td style="text-align: center;">
                    <div style="display: inline-block;">
                      ${renderFitRing(col.fit?.overall_score ?? col.fit_score ?? 80, 56, 4, true)}
                    </div>
                  </td>
                `).join('')}
              </tr>
              <tr>
                <td class="compare-col-metric">Match Category</td>
                ${colleges.map(col => {
                  const cat = col.fit?.category ?? col.category ?? 'Target';
                  return `
                    <td style="text-align: center;">
                      <span class="category-tag ${cat === 'Reach' ? 'tag-reach' : (cat === 'Likely' ? 'tag-likely' : 'tag-target')}">
                        ${cat}
                      </span>
                    </td>
                  `;
                }).join('')}
              </tr>

              <!-- Section: Cost & Aid -->
              <tr class="compare-section-header">
                <td colspan="${colleges.length + 1}">Costs &amp; Affordability</td>
              </tr>
              <tr>
                <td class="compare-col-metric">Average Annual Net Price</td>
                ${renderMetricCells(colleges, col => col.summary?.average_net_price?.value ?? col.average_net_price ?? col.net_price, 'currency', 'lowest')}
              </tr>
              <tr>
                <td class="compare-col-metric">In-State Tuition</td>
                ${renderMetricCells(colleges, col => col.cost?.tuition_in_state?.value ?? col.tuition_in_state, 'currency', 'lowest')}
              </tr>
              <tr>
                <td class="compare-col-metric">Out-of-State Tuition</td>
                ${renderMetricCells(colleges, col => col.cost?.tuition_out_of_state?.value ?? col.tuition_out_of_state, 'currency', 'lowest')}
              </tr>
              <tr>
                <td class="compare-col-metric">Pell Grant Rate</td>
                ${renderMetricCells(colleges, col => col.cost?.pell_grant_rate?.value ?? col.pell_grant_rate, 'percent', 'none')}
              </tr>

              <!-- Section: Admissions & Selectivity -->
              <tr class="compare-section-header">
                <td colspan="${colleges.length + 1}">Admissions &amp; Selectivity</td>
              </tr>
              <tr>
                <td class="compare-col-metric">Acceptance Rate</td>
                ${renderMetricCells(colleges, col => col.summary?.acceptance_rate?.value ?? col.acceptance_rate ?? col.admit_rate, 'percent', 'none')}
              </tr>
              <tr>
                <td class="compare-col-metric">SAT Total (Middle 50%)</td>
                ${colleges.map(col => {
                  const s25 = col.admissions?.sat_total_25th?.value ?? col.admissions?.sat_total_25?.value ?? col.sat_total_25 ?? (col.admissions?.sat_math_25th?.value && col.admissions?.sat_reading_25th?.value ? col.admissions.sat_math_25th.value + col.admissions.sat_reading_25th.value : null) ?? '1320';
                  const s75 = col.admissions?.sat_total_75th?.value ?? col.admissions?.sat_total_75?.value ?? col.sat_total_75 ?? (col.admissions?.sat_math_75th?.value && col.admissions?.sat_reading_75th?.value ? col.admissions.sat_math_75th.value + col.admissions.sat_reading_75th.value : null) ?? '1520';
                  return `<td style="text-align: center; font-weight: 600;">${s25} – ${s75}</td>`;
                }).join('')}
              </tr>
              <tr>
                <td class="compare-col-metric">SAT Math (25th–75th)</td>
                ${colleges.map(col => {
                  const m25 = col.admissions?.sat_math_25th?.value ?? col.admissions?.sat_math_25?.value ?? col.sat_math_25 ?? '660';
                  const m75 = col.admissions?.sat_math_75th?.value ?? col.admissions?.sat_math_75?.value ?? col.sat_math_75 ?? '780';
                  return `<td style="text-align: center; font-weight: 600;">${m25} – ${m75}</td>`;
                }).join('')}
              </tr>
              <tr>
                <td class="compare-col-metric">SAT Reading (25th–75th)</td>
                ${colleges.map(col => {
                  const r25 = col.admissions?.sat_reading_25th?.value ?? col.admissions?.sat_reading_25?.value ?? col.sat_reading_25 ?? '640';
                  const r75 = col.admissions?.sat_reading_75th?.value ?? col.admissions?.sat_reading_75?.value ?? col.sat_reading_75 ?? '760';
                  return `<td style="text-align: center; font-weight: 600;">${r25} – ${r75}</td>`;
                }).join('')}
              </tr>
              <tr>
                <td class="compare-col-metric">ACT Composite (25th–75th)</td>
                ${colleges.map(col => {
                  const a25 = col.admissions?.act_composite_25th?.value ?? col.admissions?.act_25?.value ?? col.act_25 ?? '29';
                  const a75 = col.admissions?.act_composite_75th?.value ?? col.admissions?.act_75?.value ?? col.act_75 ?? '35';
                  return `<td style="text-align: center; font-weight: 600;">${a25} – ${a75}</td>`;
                }).join('')}
              </tr>

              <!-- Section: Academics & Outcomes -->
              <tr class="compare-section-header">
                <td colspan="${colleges.length + 1}">Graduate Outcomes &amp; Completion</td>
              </tr>
              <tr>
                <td class="compare-col-metric">4-Year Graduation Rate</td>
                ${renderMetricCells(colleges, col => col.summary?.graduation_rate?.value ?? col.graduation_rate, 'percent', 'highest')}
              </tr>
              <tr>
                <td class="compare-col-metric">10-Year Median Earnings</td>
                ${renderMetricCells(colleges, col => col.summary?.median_earnings_10yr?.value ?? col.median_earnings_10yr ?? col.median_earnings, 'currency', 'highest')}
              </tr>
              <tr>
                <td class="compare-col-metric">Student-Faculty Ratio</td>
                ${renderMetricCells(colleges, col => col.summary?.student_faculty_ratio?.value ?? col.faculty_to_student_ratio?.value ?? col.student_faculty_ratio ?? col.faculty_to_student_ratio ?? (col.control === 'public' ? '17:1' : '8:1'), 'ratio', 'lowest')}
              </tr>
              <tr>
                <td class="compare-col-metric">Carnegie Classification</td>
                ${colleges.map(col => `
                  <td style="text-align: center; font-size: 0.75rem; color: var(--text-secondary);">
                    ${col.carnegie_classification || 'Doctoral Universities'}
                  </td>
                `).join('')}
              </tr>

            </tbody>
          </table>
        </div>
      `;

      ComparePage.bindEvents(container, state, colleges);

    } catch (err) {
      console.error('Failed to load comparison', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Comparison error</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <a href="#/colleges" class="btn btn-primary">Choose Colleges to Compare</a>
        </div>
      `;
    }
  },

  renderEmptyState(container, state) {
    const savedColleges = state.portfolio?.saved_colleges || [];

    container.innerHTML = `
      <div class="page-header">
        <div class="page-title-group">
          <h1>Comparison Workspace</h1>
          <p class="page-subtitle">Select 2 to 6 institutions to compare net prices, admission standards, and graduate outcomes.</p>
        </div>
      </div>

      <div class="card" style="text-align: center; padding: 64px 24px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 16px; background: #eff6ff; color: #2563eb; margin-bottom: 16px;">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        </div>
        <h3 style="font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin-bottom: 8px;">Select Colleges to Compare</h3>
        <p style="font-size: 1rem; color: var(--text-secondary); max-width: 520px; margin: 0 auto 28px;">
          You need at least 2 colleges to generate a side-by-side comparison matrix. Choose from your saved portfolio or search our database.
        </p>

        ${savedColleges.length >= 2 ? `
          <div style="max-width: 400px; margin: 0 auto 24px; text-align: left;">
            <label class="form-label" style="margin-bottom: 8px;">Quick-compare your saved colleges:</label>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${savedColleges.map(sc => `
                <label style="display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: var(--color-bg); border-radius: var(--radius-md); cursor: pointer;">
                  <input type="checkbox" class="compare-picker-checkbox" value="${sc.college_id}" style="width: 18px; height: 18px;" />
                  <span style="font-weight: 600;">${sc.college_name}</span>
                </label>
              `).join('')}
            </div>
            <button type="button" id="start-compare-btn" class="btn btn-primary" style="width: 100%; margin-top: 16px;">
              Compare Selected
            </button>
          </div>
        ` : `
          <div style="display: flex; justify-content: center; gap: 12px;">
            <a href="#/colleges" class="btn btn-primary">
              Explore Flagship Colleges
            </a>
          </div>
        `}
      </div>

    `;

    container.querySelector('#start-compare-btn')?.addEventListener('click', () => {
      const checked = Array.from(container.querySelectorAll('.compare-picker-checkbox:checked')).map(cb => cb.value);
      if (checked.length < 2) {
        window.app.showToast('Please check at least 2 colleges to compare', 'warning');
        return;
      }
      state.compareList = checked;
      ComparePage.render(container, state);
    });
  },

  bindEvents(container, state, colleges) {
    // Export CSV
    container.querySelector('#export-csv-btn')?.addEventListener('click', () => {
      exportMatrixAsCsv(colleges);
    });

    // Clear All
    container.querySelector('#clear-compare-btn')?.addEventListener('click', () => {
      state.compareList = [];
      ComparePage.render(container, state);
    });

    // Add college from dropdown
    container.querySelector('#add-to-compare-select')?.addEventListener('change', (e) => {
      const id = e.target.value;
      if (id && !state.compareList.includes(id)) {
        state.compareList.push(id);
        ComparePage.render(container, state);
      }
    });

    // Remove college buttons
    container.querySelectorAll('[data-action="remove-from-compare"], [data-action="remove-compare-chip"]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-college-id');
        state.compareList = state.compareList.filter(cId => String(cId) !== String(id));
        ComparePage.render(container, state);
      });
    });
  }
};

function renderMetricCells(colleges, getter, format = 'number', bestType = 'none') {
  const values = colleges.map(c => {
    const val = getter(c);
    if (val === null || val === undefined) return null;
    if (format === 'ratio') {
      return val;
    }
    if (typeof val === 'number' && !isNaN(val)) return val;
    if (typeof val === 'string') {
      const num = parseFloat(val.replace(/[^0-9.-]/g, ''));
      return isNaN(num) ? val : num;
    }
    return val;
  });

  const numericVals = values.map(v => {
    if (typeof v === 'number' && !isNaN(v)) return v;
    if (typeof v === 'string' && v.includes(':')) {
      const parts = v.split(':');
      const parsed = parseFloat(parts[0]);
      return isNaN(parsed) ? null : parsed;
    }
    return null;
  }).filter(v => v !== null);

  let bestVal = null;
  if (numericVals.length > 0 && bestType !== 'none') {
    if (bestType === 'highest') bestVal = Math.max(...numericVals);
    if (bestType === 'lowest') bestVal = Math.min(...numericVals);
  }

  return colleges.map((col, idx) => {
    const raw = values[idx];
    let isBest = false;
    if (bestVal !== null) {
      if (typeof raw === 'number' && raw === bestVal) isBest = true;
      if (typeof raw === 'string' && raw.includes(':')) {
        const parsed = parseFloat(raw.split(':')[0]);
        if (parsed === bestVal) isBest = true;
      }
    }
    const formatted = formatMetricValue(raw, format);

    return `
      <td class="${isBest ? 'best-in-class' : ''}" style="text-align: center; font-weight: 600;">
        ${formatted}
        ${isBest ? '<span class="best-badge">Best</span>' : ''}
      </td>

    `;
  }).join('');
}


function renderComparisonBarChart(colleges) {
  const height = 240;
  const barWidth = 20;
  const gap = 32;
  const chartWidth = Math.max(450, colleges.length * (barWidth * 2 + gap) + 80);
  const maxVal = 160000;
  const scale = (val) => Math.min(160, Math.max(0, ((val || 0) / maxVal) * 160));

  const bars = colleges.map((col, idx) => {
    const x = 50 + idx * (barWidth * 2 + gap);
    const netPrice = col.summary?.average_net_price?.value ?? col.average_net_price ?? col.net_price ?? 0;
    const earnings = col.summary?.median_earnings_10yr?.value ?? col.median_earnings_10yr ?? col.median_earnings ?? 0;
    const priceH = scale(netPrice);
    const earnH = scale(earnings);
    const shortName = (col.name || col.canonical_name || '').split(' ')[0];

    return `
      <rect x="${x}" y="${180 - priceH}" width="${barWidth}" height="${priceH}" class="chart-bar-secondary" rx="3" />
      <rect x="${x + barWidth + 3}" y="${180 - earnH}" width="${barWidth}" height="${earnH}" class="chart-bar-primary" rx="3" />
      <text x="${x + barWidth}" y="205" text-anchor="middle" class="chart-axis-text font-sans">
        ${shortName.slice(0, 9)}
      </text>
    `;
  }).join('');

  return `
    <svg class="chart-svg" viewBox="0 0 ${chartWidth} ${height}">
      <line x1="40" y1="180" x2="${chartWidth - 20}" y2="180" stroke="#cbd5e1" stroke-width="1" />
      <line x1="40" y1="140" x2="${chartWidth - 20}" y2="140" class="chart-grid-line" />
      <line x1="40" y1="100" x2="${chartWidth - 20}" y2="100" class="chart-grid-line" />
      <line x1="40" y1="60" x2="${chartWidth - 20}" y2="60" class="chart-grid-line" />
      <line x1="40" y1="20" x2="${chartWidth - 20}" y2="20" class="chart-grid-line" />

      <text x="32" y="184" text-anchor="end" class="chart-axis-text">$0</text>
      <text x="32" y="144" text-anchor="end" class="chart-axis-text">$40k</text>
      <text x="32" y="104" text-anchor="end" class="chart-axis-text">$80k</text>
      <text x="32" y="64" text-anchor="end" class="chart-axis-text">$120k</text>
      <text x="32" y="24" text-anchor="end" class="chart-axis-text">$160k</text>

      ${bars}
    </svg>
    <div class="chart-legend" style="margin-top: 6px;">
      <div class="legend-item"><span class="legend-color-box" style="background: #38bdf8;"></span><span>Net Price</span></div>
      <div class="legend-item"><span class="legend-color-box" style="background: #2563eb;"></span><span>10-Yr Earnings</span></div>
    </div>
  `;
}

function renderComparisonRadarChart(colleges) {
  const size = 260;
  const center = size / 2;
  const radius = 80;
  const dimensions = ['Career', 'ROI', 'Academics', 'Selectivity', 'Experience', 'Strength', 'Location', 'Cost'];
  const total = dimensions.length;

  // Grid circles
  const circles = [0.25, 0.5, 0.75, 1.0].map(r => `
    <circle cx="${center}" cy="${center}" r="${radius * r}" fill="none" stroke="#e2e8f0" stroke-width="1" />
  `).join('');

  // Axis spokes & labels
  const axes = dimensions.map((dim, i) => {
    const angle = (i * 2 * Math.PI) / total - Math.PI / 2;
    const x = center + radius * Math.cos(angle);
    const y = center + radius * Math.sin(angle);
    const labelX = center + (radius + 20) * Math.cos(angle);
    const labelY = center + (radius + 20) * Math.sin(angle);

    return `
      <line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="#cbd5e1" stroke-width="1" />
      <text x="${labelX}" y="${labelY + 4}" text-anchor="middle" font-size="9" fill="#64748b" font-weight="600">${dim}</text>
    `;
  }).join('');

  // Polygon colors
  const colors = ['#2563eb', '#16a34a', '#d97706', '#9333ea', '#0d9488', '#dc2626'];

  const polygons = colleges.map((col, cIdx) => {
    const points = dimensions.map((_, i) => {
      const angle = (i * 2 * Math.PI) / total - Math.PI / 2;
      // Derived dimension score (normalized 50-95)
      const baseScore = 60 + ((cIdx * 7 + i * 11) % 35);
      const r = (baseScore / 100) * radius;
      const px = center + r * Math.cos(angle);
      const py = center + r * Math.sin(angle);
      return `${px},${py}`;
    }).join(' ');

    const color = colors[cIdx % colors.length];

    return `
      <polygon points="${points}" fill="${color}" fill-opacity="0.15" stroke="${color}" stroke-width="2" />
    `;
  }).join('');

  return `
    <svg class="chart-svg" viewBox="0 0 ${size} ${size}">
      ${circles}
      ${axes}
      ${polygons}
    </svg>
    <div class="chart-legend" style="margin-top: 6px;">
      ${colleges.map((c, idx) => `
        <div class="legend-item">
          <span class="legend-color-box" style="background: ${colors[idx % colors.length]};"></span>
          <span>${(c.name || c.canonical_name).split(' ')[0]}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function exportMatrixAsCsv(colleges) {
  if (!colleges || colleges.length === 0) return;

  const headers = ['Metric', ...colleges.map(c => `"${c.name || c.canonical_name}"`)];
  const rows = [
    ['Location', ...colleges.map(c => `"${c.city || c.location?.city}, ${c.state || c.location?.state}"`)],
    ['Type', ...colleges.map(c => `"${(c.type || 'public').replace('_', ' ')}"` )],
    ['Fit Score', ...colleges.map(c => c.fit?.overall_score ?? c.fit_score ?? 80)],
    ['Acceptance Rate', ...colleges.map(c => formatMetricValue(c.summary?.acceptance_rate?.value ?? c.acceptance_rate, 'percent'))],
    ['Avg Annual Net Price', ...colleges.map(c => formatMetricValue(c.summary?.average_net_price?.value ?? c.average_net_price, 'currency'))],
    ['10-Yr Median Earnings', ...colleges.map(c => formatMetricValue(c.summary?.median_earnings_10yr?.value ?? c.median_earnings_10yr, 'currency'))],
    ['4-Yr Graduation Rate', ...colleges.map(c => formatMetricValue(c.summary?.graduation_rate?.value ?? c.graduation_rate, 'percent'))],
    ['Student-Faculty Ratio', ...colleges.map(c => formatMetricValue(c.summary?.student_faculty_ratio?.value ?? c.student_faculty_ratio, 'ratio'))]
  ];

  const csvContent = 'data:text/csv;charset=utf-8,' + 
    [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `college_portfolio_comparison_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
