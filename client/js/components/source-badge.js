/**
 * Source Badge Component
 * Renders semantic badges for data classification with click-to-inspect provenance.
 */

export function renderSourceBadge(fieldData, fieldName = 'Metric') {
  if (!fieldData) return '';

  const status = (fieldData.status || 'reported').toLowerCase().replace('-', '_');
  const year = fieldData.year ? ` '${String(fieldData.year).slice(-2)}` : '';
  const confidence = fieldData.confidence ? ` (${Math.round(fieldData.confidence * 100)}%)` : '';

  let label = 'Reported';
  let badgeClass = 'badge-reported';

  switch (status) {
    case 'reported':
      label = 'Reported';
      badgeClass = 'badge-reported';
      break;
    case 'calculated':
      label = 'Calculated';
      badgeClass = 'badge-calculated';
      break;
    case 'ai_derived':
    case 'ai-derived':
      label = 'AI-derived';
      badgeClass = 'badge-ai-derived';
      break;
    case 'estimated':
    case 'projected':
      label = 'Estimated';
      badgeClass = 'badge-estimated';
      break;
    case 'qualitative':
      label = 'Qualitative';
      badgeClass = 'badge-qualitative';
      break;
  }

  // Serialized data for the provenance drawer
  const serialized = encodeURIComponent(JSON.stringify({
    fieldName,
    ...fieldData
  }));

  return `
    <button 
      type="button"
      class="source-badge ${badgeClass}" 
      data-provenance="${serialized}"
      title="Click to view full provenance and data audit"
      aria-label="${label} data from ${fieldData.source || 'Scorecard'}"
    >
      <span class="source-badge-dot" style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: currentColor; opacity: 0.8; margin-right: 4px;"></span>
      <span>${label}${year}</span>
    </button>
  `;
}
