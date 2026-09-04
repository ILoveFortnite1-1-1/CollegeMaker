/**
 * Admissions Chances Gauge Component (Feature R4)
 * Renders visual range bar / gauge comparing student stats against 25th/75th percentiles
 * with Reach / Target / Likely / Safety classification.
 */

export function renderChancesGauge(data, options = {}) {
  if (!data) {
    return `
      <div class="chances-gauge-card empty">
        <p class="text-muted" style="font-size: 0.875rem; margin: 0;">Admissions chances data currently unavailable.</p>
      </div>
    `;
  }

  const classification = data.classification || data.category || 'Target';
  const classLower = classification.toLowerCase();
  const acceptanceRate = typeof data.acceptance_rate === 'number' 
    ? (data.acceptance_rate <= 1 ? (data.acceptance_rate * 100).toFixed(1) : data.acceptance_rate.toFixed(1))
    : null;
  const probability = typeof data.overall_probability === 'number'
    ? Math.round(data.overall_probability * 100)
    : (typeof data.admissions_probability === 'number' ? Math.round(data.admissions_probability * 100) : null);

  const testStatus = data.test_status || {};
  const gpaStatus = data.gpa_status || {};
  const summary = data.summary || data.rationale || '';

  // Determine test score numbers
  const testType = testStatus.test_type || (testStatus.student_sat ? 'SAT' : (testStatus.student_act ? 'ACT' : 'SAT'));
  const isSAT = testType.toUpperCase() === 'SAT';
  const minScale = isSAT ? 800 : 15;
  const maxScale = isSAT ? 1600 : 36;
  const p25 = testStatus.percentile_25 || (isSAT ? 1200 : 25);
  const p75 = testStatus.percentile_75 || (isSAT ? 1450 : 31);
  const studentScore = testStatus.student_score || testStatus.student_sat || testStatus.student_act || null;

  // Calculate percentage positions for range bar
  const clamp = (val, min, max) => Math.min(Math.max(val, min), max);
  const toPct = (val) => clamp(((val - minScale) / (maxScale - minScale)) * 100, 2, 98);

  const leftPct25 = toPct(p25);
  const leftPct75 = toPct(p75);
  const widthMiddle = Math.max(leftPct75 - leftPct25, 4);
  const studentPct = studentScore ? toPct(studentScore) : null;

  // Semantic styles for badge
  const badgeClasses = {
    safety: 'badge-safety',
    likely: 'badge-likely',
    target: 'badge-target',
    reach: 'badge-reach'
  };
  const badgeClass = badgeClasses[classLower] || 'badge-target';

  return `
    <div class="chances-gauge-widget ${options.compact ? 'compact' : ''}">
      <!-- Header Row: Classification and Probability -->
      <div class="chances-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="category-tag tag-${classLower} ${badgeClass}" style="font-size: 0.875rem; font-weight: 700; padding: 4px 12px;">
            ${classification}
          </span>
          ${probability !== null ? `
            <span style="font-size: 0.875rem; font-weight: 600; color: var(--text-secondary);">
              ~${probability}% estimated admit rate
            </span>
          ` : ''}
        </div>
        ${acceptanceRate !== null ? `
          <div style="font-size: 0.8125rem; color: var(--text-muted);">
            School Admit Rate: <strong style="color: var(--text-primary);">${acceptanceRate}%</strong>
          </div>
        ` : ''}
      </div>

      <!-- Range Bar Container -->
      <div class="chances-bar-container" style="margin: 20px 0 16px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px;">
          <span>${testType} Middle 50% Benchmark: <strong>${p25} – ${p75}</strong></span>
          ${studentScore ? `<span>Your ${testType}: <strong style="color: var(--color-primary);">${studentScore}</strong></span>` : ''}
        </div>

        <!-- Horizontal Track -->
        <div class="chances-track" style="position: relative; height: 16px; background: #f1f5f9; border-radius: 8px; border: 1px solid var(--color-border); overflow: visible;">
          <!-- Reach Zone (< 25th) -->
          <div style="position: absolute; left: 0; width: ${leftPct25}%; height: 100%; background: #fef3c7; border-top-left-radius: 7px; border-bottom-left-radius: 7px; opacity: 0.6;" title="Below 25th Percentile (Reach)"></div>

          <!-- Target Zone (25th - 75th Middle 50%) -->
          <div style="position: absolute; left: ${leftPct25}%; width: ${widthMiddle}%; height: 100%; background: #dbeafe; border-left: 2px solid #3b82f6; border-right: 2px solid #3b82f6;" title="Middle 50% Range (Target)"></div>

          <!-- Likely / Safety Zone (> 75th) -->
          <div style="position: absolute; left: ${leftPct75}%; right: 0; height: 100%; background: #dcfce7; border-top-right-radius: 7px; border-bottom-right-radius: 7px; opacity: 0.7;" title="Above 75th Percentile (Likely/Safety)"></div>

          <!-- Student Score Pin -->
          ${studentPct !== null ? `
            <div class="student-score-pin" style="position: absolute; left: ${studentPct}%; top: -6px; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; z-index: 5;">
              <div style="width: 12px; height: 12px; background: #2563eb; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 1px 4px rgba(0,0,0,0.3);"></div>
              <div style="width: 2px; height: 16px; background: #2563eb;"></div>
              <div style="margin-top: 2px; font-size: 0.7rem; font-weight: 800; color: #1e40af; background: #ffffff; padding: 1px 6px; border-radius: 4px; border: 1px solid #bfdbfe; box-shadow: 0 1px 3px rgba(0,0,0,0.06); white-space: nowrap;">
                You: ${studentScore}
              </div>
            </div>
          ` : ''}
        </div>

        <!-- Scale Labels -->
        <div style="position: relative; height: 20px; margin-top: ${studentScore ? '24px' : '6px'}; font-size: 0.75rem; color: var(--text-muted);">
          <span style="position: absolute; left: 0;">${minScale}</span>
          <span style="position: absolute; left: ${leftPct25}%; transform: translateX(-50%); font-weight: 600; color: var(--text-secondary);">${p25}</span>
          <span style="position: absolute; left: ${leftPct75}%; transform: translateX(-50%); font-weight: 600; color: var(--text-secondary);">${p75}</span>
          <span style="position: absolute; right: 0;">${maxScale}</span>
        </div>
      </div>

      <!-- Additional Details: GPA & Rationale -->
      <div class="chances-details" style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--color-border-subtle);">
        ${gpaStatus.student_gpa ? `
          <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.8125rem;">
            <span style="color: var(--text-secondary);">Student Unweighted GPA:</span>
            <strong style="color: var(--text-primary);">${gpaStatus.student_gpa.toFixed(2)}</strong>
          </div>
        ` : ''}

        ${summary ? `
          <p style="font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.45; margin: 0;">
            ${summary}
          </p>
        ` : ''}

        ${!studentScore && !gpaStatus.student_gpa ? `
          <div style="background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid var(--color-border); font-size: 0.75rem; color: var(--text-muted); display: flex; align-items: center; justify-content: space-between;">
            <span>Want personalized positioning? Set your GPA and SAT/ACT in Preferences.</span>
            <a href="#/settings" class="btn btn-sm btn-ghost" style="padding: 2px 8px; font-size: 0.75rem;">Set Scores →</a>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}
