/**
 * Fit Ring Component
 * Renders a circular SVG progress ring displaying the 0-100 fit score with score-based coloring.
 * Matches original reference UI styling.
 */

export function renderFitRing(score, size = 68, strokeWidth = 5, showLabel = true, confidence = null) {
  // Extract number safely from number, string, or nested object
  let rawVal = score;
  if (typeof rawVal === 'object' && rawVal !== null) {
    rawVal = rawVal.overall ?? rawVal.score ?? rawVal.overall_score ?? rawVal.composite_score ?? rawVal.value ?? 80;
  }
  const parsed = parseFloat(rawVal);
  const numericScore = isNaN(parsed) ? 80 : Math.max(0, Math.min(100, Math.round(parsed)));

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (numericScore / 100) * circumference;

  let colorClass = 'score-low';
  let strokeColor = '#ef4444';
  if (numericScore >= 85) {
    colorClass = 'score-high';
    strokeColor = '#10b981';
  } else if (numericScore >= 75) {
    colorClass = 'score-med';
    strokeColor = '#059669';
  } else if (numericScore >= 65) {
    colorClass = 'score-mod';
    strokeColor = '#2563eb';
  } else {
    colorClass = 'score-low';
    strokeColor = '#f59e0b';
  }

  const confidenceBadge = confidence !== null ? `
    <span class="fit-confidence-dot" title="Data Confidence: ${Math.round(confidence * 100)}%"></span>
  ` : '';

  return `
    <div class="fit-ring-wrapper" style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
      <div class="fit-ring-container" style="width: ${size}px; height: ${size}px; position: relative;" title="Fit Score: ${numericScore}/100">
        <svg class="fit-ring-svg" width="${size}" height="${size}" style="transform: rotate(-90deg); display: block;">
          <circle
            class="fit-ring-bg"
            cx="${size / 2}"
            cy="${size / 2}"
            r="${radius}"
            stroke="#e2e8f0"
            stroke-width="${strokeWidth}"
            fill="none"
          />
          <circle
            class="fit-ring-progress ${colorClass}"
            cx="${size / 2}"
            cy="${size / 2}"
            r="${radius}"
            stroke="${strokeColor}"
            stroke-width="${strokeWidth}"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="${offset}"
            stroke-linecap="round"
            fill="none"
            style="transition: stroke-dashoffset 0.6s ease;"
          />
        </svg>
        <div class="fit-ring-content" style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
          <span class="fit-ring-score ${colorClass}" style="font-weight: 700; font-size: ${size > 80 ? '2.1rem' : (size > 60 ? '1.35rem' : '0.95rem')}; color: #0f172a; line-height: 1;">
            ${numericScore}
          </span>
        </div>
        ${confidenceBadge}
      </div>
      ${showLabel ? `<span class="fit-ring-subcaption" style="font-size: 0.7rem; font-weight: 500; color: #64748b; letter-spacing: -0.01em;">Overall Fit</span>` : ''}
    </div>
  `;
}
