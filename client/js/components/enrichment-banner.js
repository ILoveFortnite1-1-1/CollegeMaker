/**
 * Enrichment Banner Component
 * Displays live AI enrichment status, refresh trigger button, and degraded fallback alerts.
 */

export function renderEnrichmentBanner(collegeId, status = 'idle', message = '', lastEnriched = null) {
  let icon = '✨';
  let title = 'AI Qualitative Intelligence';
  let description = 'Real-time structured synthesis of institutional strengths, upsides, and campus tradeoffs.';
  let bannerClass = '';
  let showButton = true;
  let buttonText = 'Refresh AI Insights';
  let buttonDisabled = false;

  if (status === 'running') {
    icon = '<div class="spinner spinner-sm"></div>';
    title = 'Researching Current College Information…';
    description = 'Extracting structured facts via Gemini AI and committing to append-only master knowledge ledger.';
    bannerClass = 'running';
    showButton = true;
    buttonText = 'Analyzing…';
    buttonDisabled = true;
  } else if (status === 'ai_unavailable') {
    icon = 'ℹ️';
    title = 'Verified Institutional Data Mode';
    description = message || 'AI enrichment currently unavailable. Displaying certified U.S. Department of Education Scorecard data.';
    bannerClass = 'degraded';
    showButton = true;
    buttonText = 'Retry AI Analysis';
  } else if (status === 'completed' || lastEnriched) {
    icon = '✅';
    title = 'Enriched & Audited';
    const dateStr = lastEnriched ? new Date(lastEnriched).toLocaleDateString() : 'Recently';
    description = `Verified against latest institutional data and committed to master knowledge ledger (${dateStr}).`;
    showButton = true;
    buttonText = 'Re-Analyze';
  }

  return `
    <div class="enrichment-banner ${bannerClass}" id="enrichment-banner-${collegeId}">
      <div class="enrichment-left">
        <span class="enrichment-icon">${icon}</span>
        <div class="enrichment-text-group">
          <h4>${title}</h4>
          <p>${description}</p>
        </div>
      </div>
      ${showButton ? `
        <div class="enrichment-actions">
          <button 
            type="button"
            class="btn btn-sm btn-secondary" 
            id="refresh-ai-btn-${collegeId}"
            data-college-id="${collegeId}"
            ${buttonDisabled ? 'disabled' : ''}
          >
            <span>✨</span> ${buttonText}
          </button>
        </div>
      ` : ''}
    </div>
  `;
}
