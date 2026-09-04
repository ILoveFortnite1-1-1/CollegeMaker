/**
 * Alumni Outcomes Deep Dive Component (Feature R6)
 * Sortable table and horizontal bar chart of top majors by earnings
 * with preferred majors highlighted.
 */
import { formatMetricValue } from './metric-card.js';

export function renderOutcomesChart(data, options = {}) {
  const containerId = options.containerId || `outcomes-${Math.random().toString(36).substr(2, 9)}`;
  const programs = (data && (data.programs || data.items || (Array.isArray(data) ? data : []))) || [];

  if (!programs || programs.length === 0) {
    return `
      <div class="outcomes-empty" style="padding: 24px; text-align: center; background: #f8fafc; border-radius: 8px; border: 1px dashed var(--color-border);">
        <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0;">
          No field-of-study earnings reported for this institution.
        </p>
      </div>
    `;
  }

  // Normalize program data
  const normalized = programs.map(p => {
    const title = p.major_name || p.major_title || p.title || 'General Studies';
    const earnings = p.median_earnings_4yr ?? p.median_earnings ?? p.median_earnings_1yr ?? null;
    const earnings1yr = p.median_earnings_1yr ?? null;
    const debt = p.median_debt ?? null;
    const isPreferred = Boolean(p.is_preferred_major || p.is_preferred || p.is_preferred_match);
    const credential = p.credential_level || p.credential || "Bachelor's";

    return {
      cip_code: p.cip_code || '',
      title,
      earnings,
      earnings1yr,
      debt,
      isPreferred,
      credential
    };
  });

  // Top programs for horizontal bar chart (sorted by earnings desc, max 8)
  const sortedForChart = [...normalized]
    .filter(p => p.earnings && p.earnings > 0)
    .sort((a, b) => b.earnings - a.earnings)
    .slice(0, 8);

  const maxEarnings = sortedForChart.length > 0 ? Math.max(...sortedForChart.map(p => p.earnings)) : 100000;

  return `
    <div class="outcomes-deep-dive" id="${containerId}">
      <!-- Top Majors Bar Chart Section -->
      <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div>
            <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin: 0 0 2px 0;">
              Top Majors by Median Earnings
            </h4>
            <span style="font-size: 0.75rem; color: var(--text-muted);">
              4 years post-graduation median earnings (Scorecard CIP data)
            </span>
          </div>
          ${normalized.some(p => p.isPreferred) ? `
            <span style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: 600; color: #1e40af; background: #dbeafe; padding: 2px 8px; border-radius: 4px;">
              ★ Highlights your preferred major
            </span>
          ` : ''}
        </div>

        <div class="outcomes-bar-chart" style="display: flex; flex-direction: column; gap: 10px;">
          ${sortedForChart.map(prog => {
            const pct = Math.max(5, Math.min(100, Math.round((prog.earnings / maxEarnings) * 100)));
            const barColor = prog.isPreferred ? 'linear-gradient(90deg, #2563eb, #3b82f6)' : '#94a3b8';
            const labelColor = prog.isPreferred ? 'var(--color-primary)' : 'var(--text-primary)';

            return `
              <div class="outcome-bar-row" style="display: flex; flex-direction: column; gap: 3px;">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8125rem;">
                  <span style="font-weight: ${prog.isPreferred ? '700' : '500'}; color: ${labelColor}; display: flex; align-items: center; gap: 6px;">
                    ${prog.isPreferred ? '<span style="color: #2563eb;">★</span>' : ''}
                    ${prog.title}
                    ${prog.isPreferred ? '<span style="font-size: 0.7rem; background: #dbeafe; color: #1e40af; padding: 1px 6px; border-radius: 4px; font-weight: 700;">Preferred</span>' : ''}
                  </span>
                  <span style="font-weight: 700; color: var(--text-primary); font-family: var(--font-mono, monospace);">
                    ${formatMetricValue(prog.earnings, 'currency')}
                  </span>
                </div>
                <div class="bar-track" style="height: 10px; background: #f1f5f9; border-radius: 5px; overflow: hidden; width: 100%;">
                  <div class="bar-fill" style="width: ${pct}%; height: 100%; background: ${barColor}; border-radius: 5px; transition: width 0.3s ease;"></div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>

      <!-- Search & Filter Controls -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap;">
        <div style="position: relative; flex: 1; min-width: 200px; max-width: 320px;">
          <input 
            type="text" 
            class="outcomes-search-input text-input" 
            placeholder="Search programs by major..." 
            style="width: 100%; padding: 6px 12px 6px 30px; font-size: 0.8125rem; border-radius: 6px; border: 1px solid var(--color-border);"
            data-container="${containerId}"
          />
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted);"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <span style="font-size: 0.75rem; color: var(--text-muted);">
          Showing <strong class="outcomes-count">${normalized.length}</strong> programs
        </span>
      </div>

      <!-- Sortable Programs Table -->
      <div style="overflow-x: auto; border: 1px solid var(--color-border); border-radius: 8px;">
        <table class="outcomes-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8125rem;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 1px solid var(--color-border); color: var(--text-secondary); font-weight: 600;">
              <th style="padding: 10px 14px; cursor: pointer;" data-sort="title">Major / Field of Study ↕</th>
              <th style="padding: 10px 14px;">Degree</th>
              <th style="padding: 10px 14px; text-align: right; cursor: pointer;" data-sort="earnings">4-Yr Earnings ↕</th>
              <th style="padding: 10px 14px; text-align: right; cursor: pointer;" data-sort="debt">Median Debt ↕</th>
              <th style="padding: 10px 14px; text-align: right;">Debt/Salary</th>
            </tr>
          </thead>
          <tbody class="outcomes-tbody">
            ${renderOutcomesTableRows(normalized)}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

export function renderOutcomesTableRows(programs) {
  if (!programs || programs.length === 0) {
    return `
      <tr>
        <td colspan="5" style="padding: 24px; text-align: center; color: var(--text-muted);">
          No matching programs found.
        </td>
      </tr>
    `;
  }

  return programs.map(p => {
    const rowBg = p.isPreferred ? '#eff6ff' : '#ffffff';
    const rowBorder = p.isPreferred ? '1px solid #bfdbfe' : '1px solid var(--color-border-subtle)';
    const debtRatio = (p.earnings && p.debt && p.earnings > 0) ? (p.debt / p.earnings).toFixed(2) : null;

    return `
      <tr style="background: ${rowBg}; border-bottom: ${rowBorder}; transition: background 0.15s ease;">
        <td style="padding: 10px 14px; font-weight: ${p.isPreferred ? '700' : '500'}; color: ${p.isPreferred ? '#1e40af' : 'var(--text-primary)'};">
          <div style="display: flex; align-items: center; gap: 6px;">
            ${p.isPreferred ? '<span style="color: #2563eb;">★</span>' : ''}
            <span>${p.title}</span>
            ${p.isPreferred ? '<span style="font-size: 0.65rem; background: #2563eb; color: #fff; padding: 1px 5px; border-radius: 3px; font-weight: 700;">YOUR MAJOR</span>' : ''}
          </div>
        </td>
        <td style="padding: 10px 14px; color: var(--text-secondary);">${p.credential}</td>
        <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: var(--text-primary); font-family: var(--font-mono, monospace);">
          ${formatMetricValue(p.earnings, 'currency')}
        </td>
        <td style="padding: 10px 14px; text-align: right; color: var(--text-secondary); font-family: var(--font-mono, monospace);">
          ${formatMetricValue(p.debt, 'currency')}
        </td>
        <td style="padding: 10px 14px; text-align: right; font-size: 0.75rem;">
          ${debtRatio ? `
            <span style="font-weight: 600; color: ${debtRatio < 0.6 ? '#16a34a' : (debtRatio < 1.0 ? '#d97706' : '#dc2626')};">
              ${debtRatio}x
            </span>
          ` : '<span style="color: var(--text-muted);">—</span>'}
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Attach interactive event listeners for search and sorting
 */
export function initOutcomesInteractions(container) {
  if (!container) return;

  const deepDives = container.querySelectorAll('.outcomes-deep-dive');
  deepDives.forEach(widget => {
    const searchInput = widget.querySelector('.outcomes-search-input');
    const tbody = widget.querySelector('.outcomes-tbody');
    const countEl = widget.querySelector('.outcomes-count');
    const sortHeaders = widget.querySelectorAll('th[data-sort]');

    // Extract initial data from rows
    const rows = Array.from(tbody.querySelectorAll('tr')).map(tr => {
      const isPref = tr.innerHTML.includes('YOUR MAJOR') || tr.innerHTML.includes('★');
      const titleEl = tr.querySelector('td:nth-child(1)');
      const credEl = tr.querySelector('td:nth-child(2)');
      const earnEl = tr.querySelector('td:nth-child(3)');
      const debtEl = tr.querySelector('td:nth-child(4)');

      const title = titleEl ? titleEl.textContent.replace('★', '').replace('YOUR MAJOR', '').trim() : '';
      const credential = credEl ? credEl.textContent.trim() : '';
      const earnText = earnEl ? earnEl.textContent.replace(/[$,]/g, '').trim() : '0';
      const debtText = debtEl ? debtEl.textContent.replace(/[$,]/g, '').trim() : '0';

      return {
        title,
        credential,
        earnings: isNaN(parseFloat(earnText)) ? null : parseFloat(earnText),
        debt: isNaN(parseFloat(debtText)) ? null : parseFloat(debtText),
        isPreferred: isPref
      };
    });

    let currentSort = { col: null, asc: false };

    function filterAndSort() {
      const q = (searchInput?.value || '').toLowerCase().trim();
      let filtered = rows.filter(r => !q || r.title.toLowerCase().includes(q));

      if (currentSort.col) {
        filtered.sort((a, b) => {
          let valA = a[currentSort.col];
          let valB = b[currentSort.col];
          if (valA === null) return 1;
          if (valB === null) return -1;
          if (typeof valA === 'string') {
            return currentSort.asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
          }
          return currentSort.asc ? valA - valB : valB - valA;
        });
      }

      if (tbody) tbody.innerHTML = renderOutcomesTableRows(filtered);
      if (countEl) countEl.textContent = filtered.length;
    }

    if (searchInput) {
      searchInput.addEventListener('input', () => filterAndSort());
    }

    sortHeaders.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (currentSort.col === col) {
          currentSort.asc = !currentSort.asc;
        } else {
          currentSort.col = col;
          currentSort.asc = false;
        }
        filterAndSort();
      });
    });
  });
}
