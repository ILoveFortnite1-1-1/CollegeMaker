/**
 * Settings & Preferences Page View (Route: #/settings)
 * Student academic profile inputs, 8-dimension fit weight sliders, cookie privacy, and data management.
 */
import { API } from '../api.js';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
];

const DEFAULT_WEIGHTS = {
  career_outcomes: 25,
  roi_value: 20,
  academic_fit: 15,
  admissions_fit: 10,
  student_experience: 10,
  academic_strength: 10,
  location: 5,
  cost_affordability: 5
};

export const SettingsPage = {
  async render(container, state) {
    container.innerHTML = `
      <div class="loading-screen">
        <div class="spinner"></div>
        <p class="loading-text">Loading student settings…</p>
      </div>
    `;

    try {
      const portfolio = await API.getPortfolio();
      state.portfolio = portfolio;

      const prefs = portfolio.preferences || {};
      const weights = portfolio.fit_weights || DEFAULT_WEIGHTS;

      container.innerHTML = `
        <div class="page-header">
          <div class="page-title-group">
            <h1>Student Preferences &amp; Fit Weights</h1>
            <p class="page-subtitle">Customize your academic profile, calibrate fit scoring priorities, and manage local portfolio data.</p>
          </div>
        </div>

        <form id="settings-form" style="display: flex; flex-direction: column; gap: 32px;">
          <!-- Section 1: Academic & Financial Profile -->
          <div class="card">
            <h3 class="card-title" style="margin-bottom: 8px;">1. Academic &amp; Financial Profile</h3>
            <p style="font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 24px;">
              Used strictly to personalize admissions match tags (Reach/Target/Likely) and affordability evaluations.
            </p>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px;">
              <div class="form-group">
                <label for="input-gpa" class="form-label">High School GPA (Unweighted)</label>
                <input 
                  type="number" 
                  id="input-gpa" 
                  name="gpa" 
                  class="input-text" 
                  min="0.0" 
                  max="4.0" 
                  step="0.01" 
                  placeholder="e.g. 3.85" 
                  value="${prefs.gpa || ''}" 
                />
                <span class="form-helper">Scale: 0.00 – 4.00</span>
              </div>

              <div class="form-group">
                <label for="input-sat" class="form-label">SAT Score (Optional)</label>
                <input 
                  type="number" 
                  id="input-sat" 
                  name="sat" 
                  class="input-text" 
                  min="400" 
                  max="1600" 
                  step="10" 
                  placeholder="e.g. 1480" 
                  value="${prefs.sat || ''}" 
                />
                <span class="form-helper">Scale: 400 – 1600</span>
              </div>

              <div class="form-group">
                <label for="input-act" class="form-label">ACT Composite (Optional)</label>
                <input 
                  type="number" 
                  id="input-act" 
                  name="act" 
                  class="input-text" 
                  min="1" 
                  max="36" 
                  step="1" 
                  placeholder="e.g. 33" 
                  value="${prefs.act || ''}" 
                />
                <span class="form-helper">Scale: 1 – 36</span>
              </div>

              <div class="form-group">
                <label for="input-budget" class="form-label">Annual Family Budget ($)</label>
                <input 
                  type="number" 
                  id="input-budget" 
                  name="annual_budget" 
                  class="input-text" 
                  min="1000" 
                  max="100000" 
                  step="1000" 
                  placeholder="e.g. 35000" 
                  value="${prefs.annual_budget || ''}" 
                />
                <span class="form-helper">Target maximum annual out-of-pocket</span>
              </div>

              <div class="form-group">
                <label for="input-target-state" class="form-label">Preferred State</label>
                <select id="input-target-state" name="target_state" class="select-input">
                  <option value="">No State Preference</option>
                  ${US_STATES.map(st => `<option value="${st}" ${prefs.target_state === st ? 'selected' : ''}>${st}</option>`).join('')}
                </select>
                <span class="form-helper">Boosts location dimension for matching schools</span>
              </div>

              <div class="form-group">
                <label for="input-majors" class="form-label">Target Majors / Fields</label>
                <input 
                  type="text" 
                  id="input-majors" 
                  name="preferred_majors" 
                  class="input-text" 
                  placeholder="e.g. Computer Science, Economics" 
                  value="${Array.isArray(prefs.preferred_majors) ? prefs.preferred_majors.join(', ') : (prefs.preferred_majors || '')}" 
                />
                <span class="form-helper">Comma-separated interests</span>
              </div>
            </div>
          </div>

          <!-- Section 2: 8-Dimension Fit Weight Sliders -->
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">2. Fit Dimension Priorities &amp; Weights</h3>
                <p class="card-subtitle">Adjust how much each dimension contributes to your personalized 0–100 fit score.</p>
              </div>
              <div style="display: flex; align-items: center; gap: 12px;">
                <span id="total-weight-badge" class="slider-val-badge" style="background-color: var(--color-navy); color: #ffffff;">
                  Total: 100%
                </span>
                <button type="button" id="reset-weights-btn" class="btn btn-sm btn-secondary">
                  Reset Defaults
                </button>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
              ${renderWeightSlider('career_outcomes', 'Career Outcomes', 'Early-career median earnings, placement rates, and employer recruiting pipelines.', weights.career_outcomes ?? 25)}
              ${renderWeightSlider('roi_value', 'ROI / Value', 'Ratio of graduate earnings to annual net price and debt payback efficiency.', weights.roi_value ?? 20)}
              ${renderWeightSlider('academic_fit', 'Academic Fit', 'Majors offered, research facilities (R1/R2), and student-faculty ratio.', weights.academic_fit ?? 15)}
              ${renderWeightSlider('admissions_fit', 'Admissions Probability', 'Selectivity alignment based on your entered GPA and SAT/ACT percentiles.', weights.admissions_fit ?? 10)}
              ${renderWeightSlider('student_experience', 'Student Experience', 'First-to-second year retention rate, campus setting, and graduation velocity.', weights.student_experience ?? 10)}
              ${renderWeightSlider('academic_strength', 'Academic Strength', 'Program reputation, high-demand degree completion volume, and faculty depth.', weights.academic_strength ?? 10)}
              ${renderWeightSlider('location', 'Location & Setting', 'Alignment with your preferred geographic state and metropolitan setting.', weights.location ?? 5)}
              ${renderWeightSlider('cost_affordability', 'Cost & Affordability', 'Net price proximity to your targeted annual family budget.', weights.cost_affordability ?? 5)}
            </div>

            <div style="margin-top: 28px; display: flex; justify-content: flex-end; gap: 12px;">
              <button type="submit" id="save-settings-btn" class="btn btn-primary btn-lg">
                Save Preferences &amp; Recalibrate Scores
              </button>
            </div>
          </div>
        </form>

        <!-- Section 3: Cookie Privacy & Data Management -->
        <div class="card" style="margin-top: 32px; border-color: var(--color-border-strong);">
          <h3 class="card-title" style="margin-bottom: 8px;">3. Privacy &amp; Local Session Controls</h3>
          <p style="font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 20px;">
            College Portfolio operates on an anonymous guest model. Your portfolio is tied to a secure first-party cookie on this browser.
          </p>

          <div class="provenance-meta-box" style="margin-bottom: 20px;">
            <div class="provenance-row">
              <span class="provenance-label">Session Portfolio ID</span>
              <span class="provenance-value font-mono">${portfolio.portfolio_id || 'Generating session…'}</span>
            </div>
            <div class="provenance-row">
              <span class="provenance-label">Cookie Type</span>
              <span class="provenance-value">First-Party (HttpOnly, SameSite=Lax, Path=/)</span>
            </div>
            <div class="provenance-row">
              <span class="provenance-label">Saved Colleges Count</span>
              <span class="provenance-value">${portfolio.saved_colleges?.length || 0} colleges</span>
            </div>
          </div>

          <div style="display: flex; gap: 14px; flex-wrap: wrap;">
            <button type="button" id="export-portfolio-json-btn" class="btn btn-secondary">
              Export Portfolio (JSON)
            </button>
            <button type="button" id="clear-all-portfolio-btn" class="btn btn-destructive">
              Clear Portfolio &amp; Reset Session
            </button>
          </div>
        </div>

      `;

      SettingsPage.bindEvents(container, state, portfolio);

    } catch (err) {
      console.error('Failed to load settings', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3 style="color: var(--color-destructive);">Failed to load settings</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  bindEvents(container, state, portfolio) {
    const form = container.querySelector('#settings-form');
    const totalBadge = container.querySelector('#total-weight-badge');
    const resetWeightsBtn = container.querySelector('#reset-weights-btn');
    const sliders = container.querySelectorAll('.weight-slider');

    const updateTotalWeight = () => {
      let sum = 0;
      sliders.forEach(slider => {
        sum += Number(slider.value || 0);
      });
      if (totalBadge) {
        totalBadge.textContent = `Total: ${sum}%`;
        totalBadge.style.backgroundColor = sum === 100 ? 'var(--color-navy)' : 'var(--color-warning)';
      }
    };

    // Slider value sync
    sliders.forEach(slider => {
      slider.addEventListener('input', (e) => {
        const valSpan = container.querySelector(`#val-${e.target.name}`);
        if (valSpan) valSpan.textContent = `${e.target.value}%`;
        updateTotalWeight();
      });
    });

    // Reset weights
    resetWeightsBtn?.addEventListener('click', () => {
      Object.entries(DEFAULT_WEIGHTS).forEach(([name, val]) => {
        const slider = container.querySelector(`[name="${name}"]`);
        const valSpan = container.querySelector(`#val-${name}`);
        if (slider) slider.value = val;
        if (valSpan) valSpan.textContent = `${val}%`;
      });
      updateTotalWeight();
    });

    // Form Submit
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const saveBtn = container.querySelector('#save-settings-btn');
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<div class="spinner spinner-sm"></div> Saving…';
      }

      const rawGpa = form.elements['gpa']?.value;
      const rawSat = form.elements['sat']?.value;
      const rawAct = form.elements['act']?.value;
      const rawBudget = form.elements['annual_budget']?.value;
      const targetState = form.elements['target_state']?.value;
      const rawMajors = form.elements['preferred_majors']?.value;

      const preferences = {
        gpa: rawGpa ? parseFloat(rawGpa) : null,
        sat: rawSat ? parseInt(rawSat, 10) : null,
        act: rawAct ? parseInt(rawAct, 10) : null,
        annual_budget: rawBudget ? parseInt(rawBudget, 10) : null,
        target_state: targetState || null,
        preferred_majors: rawMajors ? rawMajors.split(',').map(m => m.trim()).filter(Boolean) : []
      };

      const fitWeights = {};
      sliders.forEach(slider => {
        fitWeights[slider.name] = parseInt(slider.value, 10);
      });

      try {
        const updated = await API.updatePreferences(preferences, fitWeights);
        state.portfolio = updated;
        window.app.showToast('Preferences and fit scoring priorities updated successfully!', 'success');
      } catch (err) {
        window.app.showToast(`Failed to update settings: ${err.message}`, 'error');
      } finally {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerHTML = 'Save Preferences &amp; Recalibrate Scores';
        }

      }
    });

    // Export Portfolio JSON
    container.querySelector('#export-portfolio-json-btn')?.addEventListener('click', () => {
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(portfolio, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `college_portfolio_backup_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });

    // Clear Portfolio
    container.querySelector('#clear-all-portfolio-btn')?.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear all saved colleges and reset your session? This action cannot be undone.')) {
        try {
          await API.clearPortfolio();
          if (window.app?.setPortfolio) window.app.setPortfolio(null);
          else state.portfolio = null;
          state.compareList = [];
          if (window.app?.updatePortfolioIndicators) window.app.updatePortfolioIndicators();
          window.app.showToast('Portfolio cleared successfully.', 'info');
          SettingsPage.render(container, state);
        } catch (err) {
          window.app.showToast(`Clear error: ${err.message}`, 'error');
        }
      }
    });
  }
};

function renderWeightSlider(name, label, description, initialVal) {
  return `
    <div class="form-group" style="background: var(--color-bg); padding: 16px; border-radius: var(--radius-md); border: 1px solid var(--color-border);">
      <div class="form-label" style="margin-bottom: 4px;">
        <span style="font-weight: 700; color: var(--text-primary);">${label}</span>
        <span id="val-${name}" class="slider-val-badge">${initialVal}%</span>
      </div>
      <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 12px; line-height: 1.4;">
        ${description}
      </p>
      <input 
        type="range" 
        name="${name}" 
        class="range-slider weight-slider" 
        min="0" 
        max="50" 
        step="5" 
        value="${initialVal}" 
        style="width: 100%;"
      />
    </div>
  `;
}
