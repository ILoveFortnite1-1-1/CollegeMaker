/**
 * "What-If" Scenario Modeling Page View (Route: #/what-if)
 * Feature R5: Interactive sandbox to toggle hypothetical changes (major, residency in/out-of-state,
 * aid amounts, budget, test scores) and view current vs. what-if side-by-side with real-time
 * recalculated fit scores without persisting changes. Reuses fit-ring and metric-card components.
 */
import { API } from '../api.js?v=4.0';
import { renderFitRing } from '../components/fit-ring.js';
import { renderMetricCard, formatMetricValue } from '../components/metric-card.js';

export const WhatIfPage = {
  selectedCollegeId: null,
  activeResult: null,

  // Scenario state
  overrides: {
    hypothetical_major: '',
    is_in_state: null,
    annual_aid_amount: 0,
    annual_loan_amount: 0,
    budget_max_annual: null,
    gpa: null,
    sat_score: null
  },

  async render(container, state, options = {}) {
    if (!options?.silent) {
      container.innerHTML = `
        <div class="loading-screen">
          <div class="spinner"></div>
          <p class="loading-text">Loading scenario simulation sandbox…</p>
        </div>
      `;
    }

    try {
      const portfolioData = await API.getPortfolio().catch(() => ({ saved_colleges: [], preferences: {} }));
      const savedColleges = portfolioData.saved_colleges || portfolioData.colleges || portfolioData.items || [];
      const prefs = portfolioData.preferences || {};

      if (savedColleges.length === 0) {
        container.innerHTML = `
          <div class="what-if-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
            <div class="page-header" style="margin-bottom: 28px;">
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Scenario Modeling</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">"What-If" Admissions & Cost Simulator</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">Simulate hypothetical profile changes in real-time without saving.</p>
            </div>

            <div class="empty-state card" style="padding: 60px 24px; text-align: center; max-width: 600px; margin: 40px auto; background: #fff;">
              <div style="width: 64px; height: 64px; border-radius: 16px; background: #eff6ff; color: #2563eb; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              </div>
              <h3 style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin: 0 0 8px 0;">No Saved Colleges</h3>
              <p style="color: var(--text-muted); font-size: 0.9rem; margin: 0 0 24px 0;">Save colleges to your portfolio to test hypothetical "what-if" scenarios.</p>
              <a href="#/colleges" class="btn btn-primary">Browse Colleges</a>
            </div>
          </div>
        `;
        return;
      }

      // Default to first saved college
      if (!this.selectedCollegeId || !savedColleges.some(c => String(c.college_id || c.id) === String(this.selectedCollegeId))) {
        this.selectedCollegeId = String(savedColleges[0].college_id || savedColleges[0].id);
      }

      // Initial simulation call
      const simRes = await API.simulateScenario({
        college_id: this.selectedCollegeId,
        hypothetical_major: this.overrides.hypothetical_major || undefined,
        is_in_state: this.overrides.is_in_state !== null ? this.overrides.is_in_state : undefined,
        annual_aid_amount: this.overrides.annual_aid_amount || undefined,
        annual_loan_amount: this.overrides.annual_loan_amount || undefined,
        budget_max_annual: this.overrides.budget_max_annual || undefined
      }).catch(() => ({ results: [] }));

      const results = simRes.results || [];
      const res = results.find(r => String(r.college_id) === String(this.selectedCollegeId)) || results[0] || null;
      this.activeResult = res;

      container.innerHTML = `
        <div class="what-if-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Scenario Modeling</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">"What-If" Admissions & Cost Simulator</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">
                Tinker with hypothetical changes (major, aid, loans, residency, budget) in real-time without modifying your saved profile.
              </p>
            </div>

            <div style="display: flex; gap: 10px;">
              <button type="button" id="btn-reset-what-if" class="btn btn-secondary btn-sm" style="display: flex; align-items: center; gap: 6px;">
                <span>↺ Reset Overrides</span>
              </button>
            </div>
          </div>

          <!-- Controls Sandbox Card -->
          <div class="card" style="background: #ffffff; border: 1px solid var(--color-border); border-radius: 12px; padding: 24px; margin-bottom: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">
              <div style="font-size: 0.875rem; font-weight: 700; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.05em;">
                Simulation Parameters
              </div>

              <!-- Quick Presets -->
              <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                <button type="button" class="btn btn-sm btn-ghost preset-btn" data-preset="in_state" style="font-size: 0.75rem; padding: 3px 8px; border: 1px solid var(--color-border);">
                  In-State
                </button>
                <button type="button" class="btn btn-sm btn-ghost preset-btn" data-preset="merit_10k" style="font-size: 0.75rem; padding: 3px 8px; border: 1px solid var(--color-border);">
                  +$10k Aid
                </button>
                <button type="button" class="btn btn-sm btn-ghost preset-btn" data-preset="loan_5500" style="font-size: 0.75rem; padding: 3px 8px; border: 1px solid var(--color-border);">
                  +$5,500 Loan
                </button>
                <button type="button" class="btn btn-sm btn-ghost preset-btn" data-preset="cs_major" style="font-size: 0.75rem; padding: 3px 8px; border: 1px solid var(--color-border);">
                  CS Major
                </button>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px;">
              <!-- Select College -->
              <div>
                <label style="display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  Target College
                </label>
                <select id="sim-college-select" class="select-input" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.8125rem;">
                  ${savedColleges.map(c => `
                    <option value="${c.college_id || c.id}" ${String(c.college_id || c.id) === String(this.selectedCollegeId) ? 'selected' : ''}>
                      ${c.canonical_name || c.college_name || c.name}
                    </option>
                  `).join('')}
                </select>
              </div>

              <!-- Major Override -->
              <div>
                <label style="display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  Hypothetical Major
                </label>
                <input type="text" id="sim-input-major" class="text-input" placeholder="e.g. Computer Science, Finance" value="${this.overrides.hypothetical_major || ''}" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.8125rem;" />
              </div>

              <!-- Residency Toggle -->
              <div>
                <label style="display: block; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  Tuition Residency
                </label>
                <select id="sim-select-residency" class="select-input" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.8125rem;">
                  <option value="" ${this.overrides.is_in_state === null ? 'selected' : ''}>Default (Based on Home State)</option>
                  <option value="true" ${this.overrides.is_in_state === true ? 'selected' : ''}>In-State Tuition</option>
                  <option value="false" ${this.overrides.is_in_state === false ? 'selected' : ''}>Out-of-State Tuition</option>
                </select>
              </div>

              <!-- Additional Annual Aid -->
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  <span>Hypothetical Aid Award:</span>
                  <span id="label-aid-amount" style="color: var(--color-primary); font-family: var(--font-mono);">$${(this.overrides.annual_aid_amount || 0).toLocaleString()}</span>
                </div>
                <input type="range" id="sim-range-aid" min="0" max="60000" step="1000" value="${this.overrides.annual_aid_amount || 0}" style="width: 100%;" />
              </div>

              <!-- Hypothetical Yearly Loan -->
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  <span>Hypothetical Yearly Loan:</span>
                  <span id="label-loan-amount" style="color: var(--color-primary); font-family: var(--font-mono);">$${(this.overrides.annual_loan_amount || 0).toLocaleString()}</span>
                </div>
                <input type="range" id="sim-range-loan" min="0" max="30000" step="500" value="${this.overrides.annual_loan_amount || 0}" style="width: 100%;" />
              </div>

              <!-- Annual Budget Slider -->
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 4px;">
                  <span>Family Annual Budget:</span>
                  <span id="label-budget-amount" style="color: var(--color-primary); font-family: var(--font-mono);">${this.overrides.budget_max_annual ? `$${this.overrides.budget_max_annual.toLocaleString()}` : 'Default'}</span>
                </div>
                <input type="range" id="sim-range-budget" min="5000" max="85000" step="2500" value="${this.overrides.budget_max_annual || 35000}" style="width: 100%;" />
              </div>
            </div>
          </div>

          <!-- Side-by-Side Dual Comparison Display -->
          <div id="what-if-comparison-container">
            ${this.renderComparisonView(res)}
          </div>
        </div>
      `;

      WhatIfPage.bindEvents(container, state, savedColleges);

    } catch (err) {
      console.error('Failed to render what-if page', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 40px auto;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Simulation unavailable</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  renderComparisonView(res) {
    if (!res) {
      return `
        <div class="card" style="padding: 32px; text-align: center; color: var(--text-muted);">
          Select a college above to preview the what-if fit simulation.
        </div>
      `;
    }

    const baselineScore = Math.round(res.baseline_fit_score || 75);
    const whatIfScore = Math.round(res.what_if_fit_score || 75);
    const delta = res.fit_score_delta !== undefined ? res.fit_score_delta : (whatIfScore - baselineScore);
    const isPositive = delta > 0;
    const isNeutral = Math.abs(delta) < 0.1;

    const baseCat = res.baseline_category || 'Target';
    const whatIfCat = res.what_if_category || 'Target';

    const baseNet = res.baseline_net_price !== undefined ? res.baseline_net_price : 25000;
    const whatIfNet = res.what_if_net_price !== undefined ? res.what_if_net_price : 25000;
    const priceDelta = res.net_price_delta !== undefined ? res.net_price_delta : (whatIfNet - baseNet);

    const loanAmt = res.annual_loan_amount !== undefined ? res.annual_loan_amount : (this.overrides.annual_loan_amount || 0);
    const outOfPocket = res.what_if_out_of_pocket !== undefined ? res.what_if_out_of_pocket : Math.max(0, whatIfNet - loanAmt);
    const gradDebt = res.total_debt_at_graduation !== undefined ? res.total_debt_at_graduation : (loanAmt * 4);
    const monthlyPayment = res.estimated_monthly_payment !== undefined ? res.estimated_monthly_payment : 0.0;

    const dimDeltas = res.dimension_deltas || {};
    const baseDims = res.baseline_dimensions || {};
    const whatIfDims = res.what_if_dimensions || {};

    const dimLabels = {
      career_outcomes: 'Career Outcomes',
      roi_value: 'ROI & Value',
      academic_fit: 'Academic Fit',
      admissions_fit: 'Admissions Probability',
      student_experience: 'Student Experience',
      academic_strength: 'Academic Strength',
      location: 'Location Setting',
      cost_affordability: 'Cost & Affordability'
    };

    return `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: stretch;">
        <!-- Left: Baseline / Actual -->
        <div class="card" style="background: #ffffff; border: 1px solid var(--color-border); border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;">Current Baseline</span>
              <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); margin: 2px 0 0 0;">${res.college_name}</h3>
            </div>
            <span class="category-tag tag-${baseCat.toLowerCase()}" style="font-size: 0.8125rem; font-weight: 700; padding: 3px 10px;">
              ${baseCat}
            </span>
          </div>

          <!-- Fit Ring & Price Summary -->
          <div style="display: flex; align-items: center; justify-content: space-around; padding: 18px 12px; background: #f8fafc; border-radius: 10px; margin-bottom: 24px;">
            <div style="display: flex; flex-direction: column; align-items: center;">
              ${renderFitRing(baselineScore, 90, 8, true)}
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-top: 6px;">Baseline Fit</span>
            </div>

            <div style="text-align: right;">
              <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Annual Net Price</span>
              <strong style="font-size: 1.4rem; color: var(--text-primary); font-family: var(--font-mono);">${formatMetricValue(baseNet, 'currency')}</strong>
              <span style="font-size: 0.7rem; color: var(--text-muted); display: block;">After typical aid</span>
            </div>
          </div>

          <!-- Baseline Dimensions Breakdown -->
          <h4 style="font-size: 0.8125rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin: 0 0 12px 0; letter-spacing: 0.04em;">
            Fit Dimension Scores
          </h4>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${Object.entries(dimLabels).map(([key, label]) => {
              const val = Math.round(baseDims[key] || 70);
              return `
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 3px;">
                    <span style="color: var(--text-secondary); font-weight: 500;">${label}</span>
                    <strong style="color: var(--text-primary);">${val}</strong>
                  </div>
                  <div style="height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden;">
                    <div style="width: ${val}%; height: 100%; background: #94a3b8; border-radius: 3px;"></div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <!-- Right: What-If Scenario -->
        <div class="card" style="background: #ffffff; border: 2px solid ${isPositive ? '#86efac' : (isNeutral ? 'var(--color-border)' : '#fca5a5')}; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); position: relative;">
          <!-- Delta Badge Header -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--color-primary); letter-spacing: 0.05em;">What-If Simulation</span>
                <span class="score-delta-badge" style="font-size: 0.75rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; ${isPositive ? 'background: #dcfce7; color: #166534;' : (isNeutral ? 'background: #f1f5f9; color: #475569;' : 'background: #fee2e2; color: #991b1b;')}">
                  ${isPositive ? `+${delta.toFixed(1)} pts` : (isNeutral ? '0.0 pts' : `${delta.toFixed(1)} pts`)}
                </span>
              </div>
              <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); margin: 2px 0 0 0;">${res.college_name}</h3>
            </div>
            <span class="category-tag tag-${whatIfCat.toLowerCase()}" style="font-size: 0.8125rem; font-weight: 700; padding: 3px 10px;">
              ${whatIfCat}
            </span>
          </div>

          <!-- Fit Ring & Price Summary -->
          <div style="display: flex; align-items: center; justify-content: space-around; padding: 18px 12px; background: ${isPositive ? '#f0fdf4' : '#f8fafc'}; border-radius: 10px; margin-bottom: 24px; border: 1px solid ${isPositive ? '#bbf7d0' : 'var(--color-border-subtle)'};">
            <div style="display: flex; flex-direction: column; align-items: center;">
              ${renderFitRing(whatIfScore, 90, 8, true)}
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary); margin-top: 6px;">What-If Fit</span>
            </div>

            <div style="text-align: right;">
              <span style="font-size: 0.75rem; color: var(--text-muted); display: block;">Projected Net Price</span>
              <strong style="font-size: 1.4rem; color: ${whatIfNet === 0 ? '#15803d' : (priceDelta < 0 ? '#15803d' : 'var(--text-primary)')}; font-family: var(--font-mono);">${formatMetricValue(whatIfNet, 'currency')}</strong>
              ${whatIfNet === 0 ? `
                <span style="font-size: 0.75rem; font-weight: 700; color: #166534; display: block;">
                  Full-Ride / $0 Net Price
                </span>
              ` : (priceDelta !== 0 ? `
                <span style="font-size: 0.75rem; font-weight: 700; color: ${priceDelta < 0 ? '#166534' : '#991b1b'}; display: block;">
                  ${priceDelta < 0 ? `-${formatMetricValue(Math.abs(priceDelta), 'currency')}/yr` : `+${formatMetricValue(priceDelta, 'currency')}/yr`}
                </span>
              ` : '<span style="font-size: 0.7rem; color: var(--text-muted); display: block;">No net cost change</span>')}

              ${loanAmt > 0 ? `
                <div style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed var(--color-border); font-size: 0.75rem; text-align: right;">
                  <span style="color: var(--text-muted); display: block;">Expected Out-of-Pocket: <strong style="color: #15803d; font-family: var(--font-mono);">${formatMetricValue(outOfPocket, 'currency')}</strong></span>
                </div>
              ` : ''}
            </div>
          </div>

          <!-- What-If Dimensions Breakdown with Shift Indicators -->
          <h4 style="font-size: 0.8125rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin: 0 0 12px 0; letter-spacing: 0.04em;">
            Recalculated Dimensions &amp; Deltas
          </h4>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${Object.entries(dimLabels).map(([key, label]) => {
              const val = Math.round(whatIfDims[key] || baseDims[key] || 70);
              const d = Math.round(dimDeltas[key] || 0);
              const barFill = d > 0 ? '#16a34a' : (d < 0 ? '#dc2626' : '#2563eb');

              return `
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 3px;">
                    <span style="color: var(--text-primary); font-weight: ${d !== 0 ? '700' : '500'};">${label}</span>
                    <div style="display: flex; align-items: center; gap: 6px;">
                      <strong style="color: var(--text-primary);">${val}</strong>
                      ${d !== 0 ? `
                        <span style="font-size: 0.7rem; font-weight: 800; color: ${d > 0 ? '#15803d' : '#991b1b'};">
                          (${d > 0 ? `+${d}` : d})
                        </span>
                      ` : ''}
                    </div>
                  </div>
                  <div style="height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden;">
                    <div style="width: ${val}%; height: 100%; background: ${barFill}; border-radius: 3px; transition: width 0.3s ease;"></div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>
    `;
  },

  bindEvents(container, state, savedColleges) {
    const collegeSelect = container.querySelector('#sim-college-select');
    const majorInput = container.querySelector('#sim-input-major');
    const residencySelect = container.querySelector('#sim-select-residency');
    const aidRange = container.querySelector('#sim-range-aid');
    const aidLabel = container.querySelector('#label-aid-amount');
    const loanRange = container.querySelector('#sim-range-loan');
    const loanLabel = container.querySelector('#label-loan-amount');
    const budgetRange = container.querySelector('#sim-range-budget');
    const budgetLabel = container.querySelector('#label-budget-amount');
    const resetBtn = container.querySelector('#btn-reset-what-if');
    const comparisonContainer = container.querySelector('#what-if-comparison-container');

    let debounceTimer = null;

    const triggerSimulation = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(async () => {
        const payload = {
          college_id: this.selectedCollegeId,
          hypothetical_major: this.overrides.hypothetical_major || undefined,
          is_in_state: this.overrides.is_in_state !== null ? this.overrides.is_in_state : undefined,
          annual_aid_amount: this.overrides.annual_aid_amount !== undefined ? this.overrides.annual_aid_amount : undefined,
          annual_loan_amount: this.overrides.annual_loan_amount !== undefined ? this.overrides.annual_loan_amount : undefined,
          budget_max_annual: this.overrides.budget_max_annual || undefined
        };

        try {
          const simRes = await API.simulateScenario(payload);
          const results = simRes.results || [];
          const res = results.find(r => String(r.college_id) === String(this.selectedCollegeId)) || results[0] || null;
          this.activeResult = res;

          if (comparisonContainer) {
            comparisonContainer.innerHTML = this.renderComparisonView(res);
          }
        } catch (err) {
          console.error('Failed to rerun simulation', err);
        }
      }, 150);
    };

    if (collegeSelect) {
      collegeSelect.addEventListener('change', () => {
        this.selectedCollegeId = collegeSelect.value;
        triggerSimulation();
      });
    }

    if (majorInput) {
      majorInput.addEventListener('input', () => {
        this.overrides.hypothetical_major = majorInput.value.trim();
        triggerSimulation();
      });
    }

    if (residencySelect) {
      residencySelect.addEventListener('change', () => {
        const val = residencySelect.value;
        this.overrides.is_in_state = val === 'true' ? true : (val === 'false' ? false : null);
        triggerSimulation();
      });
    }

    if (aidRange) {
      aidRange.addEventListener('input', () => {
        const val = parseInt(aidRange.value, 10) || 0;
        this.overrides.annual_aid_amount = val;
        if (aidLabel) aidLabel.textContent = `$${val.toLocaleString()}`;
        triggerSimulation();
      });
    }

    if (loanRange) {
      loanRange.addEventListener('input', () => {
        const val = parseInt(loanRange.value, 10) || 0;
        this.overrides.annual_loan_amount = val;
        if (loanLabel) loanLabel.textContent = `$${val.toLocaleString()}`;
        triggerSimulation();
      });
    }

    if (budgetRange) {
      budgetRange.addEventListener('input', () => {
        const val = parseInt(budgetRange.value, 10) || 35000;
        this.overrides.budget_max_annual = val;
        if (budgetLabel) budgetLabel.textContent = `$${val.toLocaleString()}`;
        triggerSimulation();
      });
    }

    // Presets
    container.querySelectorAll('.preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const preset = btn.getAttribute('data-preset');
        if (preset === 'in_state') {
          this.overrides.is_in_state = true;
          if (residencySelect) residencySelect.value = 'true';
        } else if (preset === 'merit_10k') {
          this.overrides.annual_aid_amount = 10000;
          if (aidRange) aidRange.value = 10000;
          if (aidLabel) aidLabel.textContent = '$10,000';
        } else if (preset === 'loan_5500') {
          this.overrides.annual_loan_amount = 5500;
          if (loanRange) loanRange.value = 5500;
          if (loanLabel) loanLabel.textContent = '$5,500';
        } else if (preset === 'cs_major') {
          this.overrides.hypothetical_major = 'Computer Science';
          if (majorInput) majorInput.value = 'Computer Science';
        }
        triggerSimulation();
      });
    });

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.overrides = {
          hypothetical_major: '',
          is_in_state: null,
          annual_aid_amount: 0,
          annual_loan_amount: 0,
          budget_max_annual: null,
          gpa: null,
          sat_score: null
        };
        if (majorInput) majorInput.value = '';
        if (residencySelect) residencySelect.value = '';
        if (aidRange) aidRange.value = 0;
        if (aidLabel) aidLabel.textContent = '$0';
        if (loanRange) loanRange.value = 0;
        if (loanLabel) loanLabel.textContent = '$0';
        if (budgetRange) budgetRange.value = 35000;
        if (budgetLabel) budgetLabel.textContent = 'Default';
        triggerSimulation();
      });
    }
  }
};

