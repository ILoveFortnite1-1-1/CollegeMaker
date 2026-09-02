/**
 * Metric Card Component
 * Formats and renders institutional metrics with provenance badges.
 */
import { renderSourceBadge } from './source-badge.js';

export function formatMetricValue(value, format = 'number') {
  if (value === null || value === undefined || isNaN(value)) {
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
      return `${value}:1`;

    case 'count':
      return new Intl.NumberFormat('en-US').format(value);

    default:
      return String(value);
  }
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
