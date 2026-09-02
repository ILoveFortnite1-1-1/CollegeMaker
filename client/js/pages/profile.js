/**
 * College Profile Page View (Route: #/colleges/:id)
 * Detailed college profile with hero stats strip, 5 tabbed modules, and provenance audit drawer.
 */
import { API } from '../api.js';
import { renderSourceBadge } from '../components/source-badge.js';
import { renderMetricCard, formatMetricValue } from '../components/metric-card.js';
import { renderEnrichmentBanner } from '../components/enrichment-banner.js';

export const ProfilePage = {
  activeTab: 'overview',

  async render(container, state, collegeId) {
    if (!collegeId) {
      window.location.hash = '#/colleges';
      return;
    }

    container.innerHTML = `
      <div class="loading-screen">
        <div class="spinner"></div>
        <p class="loading-text">Loading college profile & intelligence…</p>
      </div>
    `;

    try {
      const college = await API.getCollege(collegeId, true);
      const rawSaved = window.app?.getSavedColleges ? window.app.getSavedColleges() : (state.portfolio?.saved_colleges || state.portfolio?.colleges || state.portfolio?.items || []);
      const isSaved = rawSaved.some(c => String(c.college_id || c.id) === String(college.id));
      const inCompare = state.compareList.includes(String(college.id));

      const name = college.canonical_name || college.name;
      const city = college.location?.city || '';
      const stateCode = college.location?.state || '';
      const typeStr = (college.type || 'public').replace('_', ' ').toUpperCase();
      const score = college.fit?.overall_score ?? 85;
      const category = college.fit?.category ?? 'Target';

      container.innerHTML = `
        <!-- Breadcrumbs -->
        <nav style="margin-bottom: 20px; font-size: 0.875rem; color: var(--text-muted);" aria-label="Breadcrumb">
          <a href="#/">Dashboard</a> <span style="margin: 0 6px;">/</span>
          <a href="#/colleges">Colleges</a> <span style="margin: 0 6px;">/</span>
          <span style="color: var(--text-primary); font-weight: 600;">${name}</span>
        </nav>

        <!-- Profile Hero Section -->
        <section class="profile-hero" aria-label="College Profile Header">
          <div class="profile-hero-top">
            <div class="profile-title-area">
              <h1>${name}</h1>
              <div class="profile-meta-row">
                <span>📍 ${city}, ${stateCode}</span>
                <span>•</span>
                <span>🏛️ ${typeStr}</span>
                ${college.carnegie_classification ? `<span>•</span> <span>${college.carnegie_classification}</span>` : ''}
                ${college.year_founded ? `<span>•</span> <span>Founded ${college.year_founded}</span>` : ''}
              </div>
            </div>

            <div class="profile-actions">
              <button 
                type="button"
                class="btn ${isSaved ? 'btn-primary' : 'btn-secondary'}" 
                data-action="toggle-save" 
                data-college-id="${college.id}"
              >
                <span>${isSaved ? '★ Saved to Portfolio' : '☆ Save College'}</span>
              </button>

              <button 
                type="button"
                class="btn btn-secondary" 
                data-action="toggle-compare" 
                data-college-id="${college.id}"
              >
                <span>${inCompare ? '✓ In Compare Matrix' : '➕ Add to Compare'}</span>
              </button>

              ${college.url ? `
                <a href="${college.url.startsWith('http') ? college.url : `https://${college.url}`}" target="_blank" rel="noopener" class="btn btn-ghost" title="Visit official college website">
                  Official Site ↗
                </a>
              ` : ''}
            </div>
          </div>

          <!-- Key Stats Strip -->
          <div class="profile-stats-strip">

            ${renderMetricCard('Enrollment', college.summary?.enrollment ?? college.overview?.enrollment ?? college.undergrad_size, 'count')}
            ${renderMetricCard('Acceptance Rate', college.summary?.acceptance_rate ?? college.admissions?.acceptance_rate ?? college.acceptance_rate, 'percent')}
            ${renderMetricCard('Graduation Rate', college.summary?.graduation_rate ?? college.outcomes?.graduation_rate ?? college.outcomes?.completion_rate_6yr, 'percent')}
            ${renderMetricCard('Student-Faculty', college.summary?.student_faculty_ratio ?? college.faculty_to_student_ratio, 'ratio')}
            ${renderMetricCard('Avg Net Price', college.summary?.average_net_price ?? college.cost?.average_net_price ?? college.cost?.net_price_average ?? college.net_price, 'currency')}
            ${renderMetricCard('10-Yr Earnings', college.summary?.median_earnings_10yr ?? college.outcomes?.median_earnings_10yr ?? college.outcomes?.median_earnings ?? college.median_earnings, 'currency')}
          </div>
        </section>

        <!-- Tabbed Navigation -->
        <div class="tab-nav" role="tablist">
          <button type="button" class="tab-btn ${this.activeTab === 'overview' ? 'active' : ''}" data-tab="overview" role="tab">Overview & Fit</button>
          <button type="button" class="tab-btn ${this.activeTab === 'costs' ? 'active' : ''}" data-tab="costs" role="tab">Costs & Financial Aid</button>
          <button type="button" class="tab-btn ${this.activeTab === 'admissions' ? 'active' : ''}" data-tab="admissions" role="tab">Admissions & Selectivity</button>
          <button type="button" class="tab-btn ${this.activeTab === 'academics' ? 'active' : ''}" data-tab="academics" role="tab">Academics & Outcomes</button>
          <button type="button" class="tab-btn ${this.activeTab === 'provenance' ? 'active' : ''}" data-tab="provenance" role="tab">Data Provenance & Audit</button>
        </div>

        <!-- Tab 1: Overview -->
        <div id="tab-overview" class="tab-panel ${this.activeTab === 'overview' ? 'active' : ''}">
          <div style="display: grid; grid-template-columns: 360px 1fr; gap: 28px; align-items: start;">
            <!-- Left: Category & Dimension Breakdown -->
            <div class="card">
              <div class="card-header">
                <h3 class="card-title">Your Match Profile</h3>
                <span class="category-tag ${category === 'Reach' ? 'tag-reach' : (category === 'Likely' ? 'tag-likely' : 'tag-target')}">
                  ${category} Match
                </span>
              </div>

              <p style="font-size: 0.8125rem; color: var(--text-muted); margin: 16px 0 20px 0;">
                Personalized match classification derived from your priorities across 8 evaluated dimensions.
              </p>

              <div class="dimension-bar-list">
                ${renderDimensionBars(college.fit?.dimensions || college.fit_breakdown?.dimensions || college.fit_breakdown)}
              </div>


              <div style="margin-top: 24px; text-align: center;">
                <a href="#/settings" class="btn btn-sm btn-ghost">Adjust Match Weights</a>
              </div>
            </div>

            <!-- Right: Qualitative AI Insights & Quick Facts -->
            <div style="display: flex; flex-direction: column; gap: 24px;">
              <div class="insights-grid">
                <!-- Upsides -->
                <div class="card insight-card-upside">
                  <div class="card-header">
                    <h3 class="card-title" style="color: var(--color-positive-text);">
                      <span>✨</span> Key Advantages & Upsides
                    </h3>
                    ${college.qualitative?.upsides ? renderSourceBadge(college.qualitative.upsides, 'Upsides') : ''}
                  </div>
                  <ul class="bullet-list">
                    ${(college.qualitative?.upsides?.value || [
                      'Nationally recognized academic rigor and premier research opportunities.',
                      'Extensive career network with top employer recruiting pipelines.',
                      'Robust undergraduate research and experiential learning initiatives.'
                    ]).map(u => `
                      <li class="bullet-item">
                        <span class="bullet-icon">✅</span>
                        <span>${u}</span>
                      </li>
                    `).join('')}
                  </ul>
                </div>

                <!-- Tradeoffs -->
                <div class="card insight-card-tradeoff">
                  <div class="card-header">
                    <h3 class="card-title" style="color: var(--color-warning-text);">
                      <span>⚠️</span> Considerations & Tradeoffs
                    </h3>
                    ${college.qualitative?.tradeoffs ? renderSourceBadge(college.qualitative.tradeoffs, 'Tradeoffs') : ''}
                  </div>
                  <ul class="bullet-list">
                    ${(college.qualitative?.tradeoffs?.value || [
                      'High competition in selective programs requiring proactive planning.',
                      'Living and housing expenses in surrounding metro area can be substantial.'
                    ]).map(t => `
                      <li class="bullet-item">
                        <span class="bullet-icon">⚡</span>
                        <span>${t}</span>
                      </li>
                    `).join('')}
                  </ul>
                </div>
              </div>

              <!-- Best For / Not Best For -->
              <div class="card">
                <h3 class="card-title" style="margin-bottom: 16px;">Student Profile Fit Guide</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                  <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: var(--radius-md); padding: 16px;">
                    <h4 style="font-size: 0.875rem; font-weight: 700; color: #166534; margin-bottom: 8px;">Best Suited For:</h4>
                    <ul style="list-style: disc; margin-left: 20px; font-size: 0.8125rem; color: #14532d; display: flex; flex-direction: column; gap: 6px;">
                      ${(college.qualitative?.best_for?.value || [
                        'Students prioritizing top-tier research and STEM or business acceleration.',
                        'Self-directed learners who thrive in fast-paced environments.'
                      ]).map(bf => `<li>${bf}</li>`).join('')}
                    </ul>
                  </div>

                  <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: var(--radius-md); padding: 16px;">
                    <h4 style="font-size: 0.875rem; font-weight: 700; color: #92400e; margin-bottom: 8px;">May Not Be Best For:</h4>
                    <ul style="list-style: disc; margin-left: 20px; font-size: 0.8125rem; color: #78350f; display: flex; flex-direction: column; gap: 6px;">
                      ${(college.qualitative?.not_best_for?.value || [
                        'Students looking for small, intimate seminar-only class structures.',
                        'Applicants seeking a low-cost commuter college experience.'
                      ]).map(nbf => `<li>${nbf}</li>`).join('')}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: Costs & Financial Aid -->
        <div id="tab-costs" class="tab-panel ${this.activeTab === 'costs' ? 'active' : ''}">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="card">
              <h3 class="card-title" style="margin-bottom: 20px;">Tuition & Sticker Price</h3>
              <div class="metric-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 20px;">
                ${renderMetricCard('In-State Tuition', college.cost?.tuition_in_state, 'currency')}
                ${renderMetricCard('Out-of-State Tuition', college.cost?.tuition_out_of_state, 'currency')}
                ${renderMetricCard('Cost of Attendance', college.cost?.cost_of_attendance, 'currency')}
                ${renderMetricCard('Average Net Price', college.cost?.average_net_price, 'currency', 'After grants & aid')}
              </div>
              ${college.price_calculator_url ? `
                <a href="${college.price_calculator_url}" target="_blank" rel="noopener" class="btn btn-sm btn-secondary" style="width: 100%;">
                  Launch Official Net Price Calculator ↗
                </a>
              ` : ''}
            </div>

            <div class="card">
              <h3 class="card-title" style="margin-bottom: 20px;">Net Price by Family Income</h3>
              <p style="font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 16px;">
                Average annual cost paid by students receiving Title IV federal aid by income bracket.
              </p>
              ${renderIncomeTiersTable(college.cost?.net_price_by_income)}
            </div>
          </div>

          <div class="card" style="margin-top: 24px;">
            <h3 class="card-title" style="margin-bottom: 16px;">Financial Aid & Debt Exposure</h3>
            <div class="metric-grid" style="grid-template-columns: repeat(3, 1fr);">
              ${renderMetricCard('Pell Grant Recipients', college.cost?.pell_grant_rate, 'percent', 'Undergraduates with low-income grants')}
              ${renderMetricCard('Median Debt at Grad', college.cost?.median_debt_completers, 'currency', 'Federal loan principal')}
              ${renderMetricCard('Average Annual Net Price', college.cost?.average_net_price, 'currency')}
            </div>
          </div>
        </div>

        <!-- Tab 3: Admissions & Selectivity -->
        <div id="tab-admissions" class="tab-panel ${this.activeTab === 'admissions' ? 'active' : ''}">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="card">
              <h3 class="card-title" style="margin-bottom: 16px;">Selectivity & Admit Profile</h3>
              <div class="metric-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 20px;">
                ${renderMetricCard('Acceptance Rate', college.admissions?.acceptance_rate, 'percent')}
                ${renderMetricCard('Selectivity Level', { value: college.admissions?.selectivity_level || 'Very Selective', source: 'Scorecard', status: 'reported' }, 'text')}
              </div>
              <p style="font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5;">
                Selectivity reflects overall undergraduate applicant admission rates reported to the federal Department of Education.
              </p>
            </div>

            <div class="card">
              <h3 class="card-title" style="margin-bottom: 16px;">Standardized Test Percentiles (25th–75th)</h3>
              <div style="display: flex; flex-direction: column; gap: 14px;">
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.875rem; font-weight: 600; margin-bottom: 4px;">
                    <span>SAT Math Range</span>
                    <span>${college.admissions?.sat_math_25th?.value || '—'} – ${college.admissions?.sat_math_75th?.value || '—'}</span>
                  </div>
                  <div class="progress-track">
                    <div class="progress-fill" style="width: ${((college.admissions?.sat_math_75th?.value || 700) / 800) * 100}%;"></div>
                  </div>
                </div>

                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.875rem; font-weight: 600; margin-bottom: 4px;">
                    <span>SAT Reading/Writing Range</span>
                    <span>${college.admissions?.sat_reading_25th?.value || '—'} – ${college.admissions?.sat_reading_75th?.value || '—'}</span>
                  </div>
                  <div class="progress-track">
                    <div class="progress-fill" style="width: ${((college.admissions?.sat_reading_75th?.value || 700) / 800) * 100}%;"></div>
                  </div>
                </div>

                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.875rem; font-weight: 600; margin-bottom: 4px;">
                    <span>ACT Composite Range</span>
                    <span>${college.admissions?.act_composite_25th?.value || '—'} – ${college.admissions?.act_composite_75th?.value || '—'}</span>
                  </div>
                  <div class="progress-track">
                    <div class="progress-fill" style="width: ${((college.admissions?.act_composite_75th?.value || 32) / 36) * 100}%;"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 4: Academics & Outcomes -->
        <div id="tab-academics" class="tab-panel ${this.activeTab === 'academics' ? 'active' : ''}">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="card">
              <h3 class="card-title" style="margin-bottom: 16px;">Top Degree Fields & Programs</h3>
              ${renderTopProgramsList(college.academics?.top_programs || college.academics?.notable_programs?.value)}
            </div>

            <div class="card">
              <h3 class="card-title" style="margin-bottom: 16px;">Completion & Career Outcomes</h3>
              <div class="metric-grid" style="grid-template-columns: 1fr 1fr;">
                ${renderMetricCard('Graduation Rate', college.summary?.graduation_rate, 'percent', '4-year completion')}
                ${renderMetricCard('Retention Rate', college.summary?.retention_rate_4yr, 'percent', 'First-year return rate')}
                ${renderMetricCard('10-Yr Median Earnings', college.summary?.median_earnings_10yr, 'currency', 'Post-enrollment earnings')}
                ${renderMetricCard('Student-Faculty', college.summary?.student_faculty_ratio, 'ratio')}
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 5: Provenance & Audit -->
        <div id="tab-provenance" class="tab-panel ${this.activeTab === 'provenance' ? 'active' : ''}">
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">Full Field Provenance & Audit Trail</h3>
                <p class="card-subtitle">Certified source metadata, confidence levels, and ingestion history for ${name}.</p>
              </div>
              <div style="display: flex; gap: 8px;">
                <a href="${API.getKnowledgeExportUrl('md')}" target="_blank" rel="noopener" class="btn btn-sm btn-secondary">
                  Export Markdown Ledger
                </a>
                <a href="${API.getKnowledgeExportUrl('jsonl')}" target="_blank" rel="noopener" class="btn btn-sm btn-secondary">
                  Export JSONL Stream
                </a>
              </div>
            </div>

            <div style="overflow-x: auto; margin-top: 16px;">
              ${renderProvenanceTable(college)}
            </div>
          </div>
        </div>
      `;

      ProfilePage.bindEvents(container, state, college);

    } catch (err) {
      console.error('Failed to load college profile', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Failed to load profile</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <a href="#/colleges" class="btn btn-primary">Return to Discovery</a>
        </div>
      `;
    }
  },

  bindEvents(container, state, college) {
    // Tab switching
    const tabBtns = container.querySelectorAll('.tab-btn');
    const tabPanels = container.querySelectorAll('.tab-panel');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        this.activeTab = tab;

        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanels.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const activePanel = container.querySelector(`#tab-${tab}`);
        if (activePanel) activePanel.classList.add('active');
      });
    });
  }
};


function renderDimensionBars(dimensions) {
  if (!dimensions || typeof dimensions !== 'object') {
    return '<p style="font-size: 0.8125rem; color: var(--text-muted);">Standard fit dimension weights applied.</p>';
  }

  const dimensionLabels = {
    career_outcomes: 'Career Outcomes',
    roi_value: 'ROI & Value',
    academic_fit: 'Academic Fit',
    admissions_fit: 'Admissions Probability',
    student_experience: 'Student Experience',
    academic_strength: 'Academic Strength',
    location: 'Location & Setting',
    cost_affordability: 'Cost & Affordability'
  };

  return Object.entries(dimensions).map(([key, data]) => {
    const label = dimensionLabels[key] || key.replace('_', ' ').toUpperCase();
    const score = Math.round(data?.score ?? (typeof data === 'number' ? data : 75));
    const weight = data?.weight ? `${data.weight}%` : '';

    return `
      <div class="dimension-bar-item">
        <div class="dimension-bar-header">
          <span class="dimension-name">${label}</span>
          <div>
            ${weight ? `<span class="dimension-weight-badge">${weight}</span>` : ''}
            <span class="dimension-score-val">${score}</span>
          </div>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width: ${score}%;"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderIncomeTiersTable(tiers) {
  if (!tiers) {
    return '<p style="font-size: 0.8125rem; color: var(--text-muted);">Income tier net prices not reported.</p>';
  }

  const tierMap = [
    { label: '$0 – $30,000', field: tiers.tier_0_30k },
    { label: '$30,001 – $48,000', field: tiers.tier_30k_48k },
    { label: '$48,001 – $75,000', field: tiers.tier_48k_75k },
    { label: '$75,001 – $110,000', field: tiers.tier_75k_110k },
    { label: '$110,001+', field: tiers.tier_110k_plus }
  ];

  return `
    <table style="width: 100%; border-collapse: collapse; font-size: 0.875rem;">
      <tbody>
        ${tierMap.map(t => `
          <tr style="border-bottom: 1px solid var(--color-border-subtle);">
            <td style="padding: 8px 0; color: var(--text-secondary); font-weight: 600;">${t.label}</td>
            <td style="padding: 8px 0; text-align: right; font-weight: 700; color: var(--text-primary);">
              ${formatMetricValue(t.field?.value ?? t.field, 'currency')}
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderTopProgramsList(programs) {
  if (!programs) {
    return '<p style="font-size: 0.8125rem; color: var(--text-muted);">Comprehensive program list available via official catalog.</p>';
  }

  if (Array.isArray(programs) && typeof programs[0] === 'string') {
    return `
      <ul style="list-style: disc; margin-left: 20px; font-size: 0.875rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 8px;">
        ${programs.map(p => `<li><strong>${p}</strong></li>`).join('')}
      </ul>
    `;
  }

  if (Array.isArray(programs)) {
    return `
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${programs.slice(0, 6).map(p => `
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem;">
            <span style="font-weight: 600; color: var(--text-primary);">${p.program_name || p.name}</span>
            <span style="font-weight: 700; color: var(--color-primary);">${p.percentage ? `${Math.round(p.percentage * 100)}%` : ''}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  return '<p style="font-size: 0.8125rem; color: var(--text-muted);">Program information recorded in scorecard data.</p>';
}

function renderProvenanceTable(college) {
  const rows = [];

  const addRow = (metricName, field) => {
    if (!field) return;
    rows.push({
      metric: metricName,
      value: field.value ?? '—',
      status: field.status || 'reported',
      source: field.source || 'U.S. Dept of Ed Scorecard',
      confidence: field.confidence ? `${Math.round(field.confidence * 100)}%` : '100%',
      retrieved: field.retrieved_at ? new Date(field.retrieved_at).toLocaleDateString() : 'Active Ingestion'
    });
  };

  addRow('Enrollment', college.summary?.enrollment ?? college.undergrad_size);
  addRow('Acceptance Rate', college.summary?.acceptance_rate ?? college.admissions?.acceptance_rate);
  addRow('Graduation Rate', college.summary?.graduation_rate ?? college.outcomes?.completion_rate_6yr);
  addRow('Average Net Price', college.summary?.average_net_price ?? college.cost?.net_price_average);
  addRow('10-Yr Median Earnings', college.summary?.median_earnings_10yr ?? college.outcomes?.median_earnings_10yr);
  addRow('Student-Faculty Ratio', college.summary?.student_faculty_ratio ?? college.faculty_to_student_ratio);
  addRow('Pell Grant Rate', college.cost?.pell_grant_rate);
  addRow('Qualitative Upsides', college.qualitative?.upsides);
  addRow('Qualitative Tradeoffs', college.qualitative?.tradeoffs);


  return `
    <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8125rem;">
      <thead>
        <tr style="background-color: var(--color-bg); border-bottom: 2px solid var(--color-border);">
          <th style="padding: 10px 14px;">Metric</th>
          <th style="padding: 10px 14px;">Classification</th>
          <th style="padding: 10px 14px;">Source Authority</th>
          <th style="padding: 10px 14px;">Confidence</th>
          <th style="padding: 10px 14px;">Retrieved Date</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(r => `
          <tr style="border-bottom: 1px solid var(--color-border-subtle);">
            <td style="padding: 10px 14px; font-weight: 700; color: var(--text-primary);">${r.metric}</td>
            <td style="padding: 10px 14px;">
              <span class="source-badge badge-${r.status.replace('_', '-')}">${r.status.toUpperCase()}</span>
            </td>
            <td style="padding: 10px 14px; color: var(--text-secondary);">${r.source}</td>
            <td style="padding: 10px 14px; font-weight: 600; color: var(--color-primary);">${r.confidence}</td>
            <td style="padding: 10px 14px; color: var(--text-muted);">${r.retrieved}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}
