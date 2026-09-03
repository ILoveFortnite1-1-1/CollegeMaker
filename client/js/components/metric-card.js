/**
 * Metric Card Component
 * Formats and renders institutional metrics with provenance badges.
 */
import { renderSourceBadge } from './source-badge.js';

export function formatMetricValue(value, format = 'number') {
  if (value === null || value === undefined) {
    return '—';
  }

  // If already formatted ratio or string
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed === '' || trimmed === '—' || trimmed === 'null' || trimmed === 'undefined') return '—';
    if (format === 'ratio') {
      return trimmed.includes(':') ? trimmed : `${trimmed}:1`;
    }
    if (format === 'text') return trimmed;
    const num = Number(trimmed);
    if (isNaN(num)) return trimmed;
    value = num;
  }

  if (typeof value === 'number' && isNaN(value)) {
    return '—';
  }

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
      }).format(value);

    case 'percent':
    case 'percentage':
      const percentVal = value <= 1 ? value * 100 : value;
      return `${Math.round(percentVal)}%`;

    case 'ratio':
      return typeof value === 'string' && value.includes(':') ? value : `${value}:1`;

    case 'count':
      return new Intl.NumberFormat('en-US').format(value);

    case 'text':
      return String(value);

    default:
      return typeof value === 'number' ? new Intl.NumberFormat('en-US').format(value) : String(value);
  }
}


export function formatConfidence(conf) {
  if (conf === null || conf === undefined) return '100%';
  if (typeof conf === 'number') {
    if (isNaN(conf)) return '100%';
    return `${Math.round(conf <= 1 ? conf * 100 : conf)}%`;
  }
  const str = String(conf).toLowerCase().trim();
  if (str === 'reported' || str === 'verified' || str === 'high') return '100%';
  if (str === 'calculated') return '95%';
  if (str === 'ai_derived' || str === 'ai-derived') return '85%';
  if (str === 'qualitative') return '80%';
  if (str === 'estimated' || str === 'projected') return '75%';
  const parsed = parseFloat(str);
  if (!isNaN(parsed)) {
    return `${Math.round(parsed <= 1 ? parsed * 100 : parsed)}%`;
  }
  return '100%';
}

export function renderMetricCard(label, fieldData, format = 'number', helper = '') {
  const value = fieldData?.value ?? fieldData;
  const formattedVal = formatMetricValue(value, format);
  const badgeHtml = fieldData?.source ? renderSourceBadge(fieldData, label) : '';

  return `
    <div class="metric-card">
      <div class="metric-card-header">
        <span class="metric-label">${label}</span>
        ${badgeHtml}
      </div>
      <div class="metric-value-row">
        <span class="metric-value">${formattedVal}</span>
      </div>
      ${helper ? `<span class="metric-helper">${helper}</span>` : ''}
    </div>
  `;
}

