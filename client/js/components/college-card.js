/**
 * College Card Component
 * Renders college preview cards for discovery, dashboard, and search results.
 */
import { formatMetricValue } from './metric-card.js';
import { renderSourceBadge } from './source-badge.js';

export function renderCollegeCard(college, options = {}) {
  const {
    isSaved = false,
    inCompare = false,
    variant = 'grid',
    fitScore = null,
    category = null,
    userNote = ''
  } = options;

  const id = college.id || college.unitid;
  const name = college.name || college.canonical_name;
  const city = college.city || college.location?.city || '';
  const state = college.state || college.location?.state || '';
  const locationStr = [city, state].filter(Boolean).join(', ');
  
  // Type formatting
  const rawType = college.type || (college.ownership === 1 ? 'public' : 'private_nonprofit');
  const typeLabel = rawType.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());

  // Metrics extraction (handles both flat search item & full canonical model)
  const admitRate = college.acceptance_rate ?? college.summary?.acceptance_rate?.value ?? college.admissions?.acceptance_rate?.value;
  const netPrice = college.average_net_price ?? college.summary?.average_net_price?.value ?? college.cost?.average_net_price?.value;
  const earnings = college.median_earnings_10yr ?? college.summary?.median_earnings_10yr?.value ?? college.outcomes?.median_earnings?.value;
  const gradRate = college.graduation_rate ?? college.summary?.graduation_rate?.value ?? college.outcomes?.graduation_rate?.value;

  // Fit & Category
  let rawScore = fitScore ?? college.fit?.overall_score ?? college.fit_score ?? college.composite_score ?? null;
  if (typeof rawScore === 'object' && rawScore !== null) {
    rawScore = rawScore.overall ?? rawScore.score ?? rawScore.overall_score ?? null;
  }
  const score = (rawScore !== null && !isNaN(Number(rawScore))) ? Number(rawScore) : 80;

  const matchCategory = category ?? college.fit?.category ?? college.category ?? college.tag ?? (
    admitRate !== null && admitRate !== undefined ? (admitRate < 0.18 ? 'Reach' : (admitRate > 0.48 ? 'Likely' : 'Target')) : 'Target'
  );

  let categoryTagClass = 'tag-target';
  if (matchCategory === 'Reach') categoryTagClass = 'tag-reach';
  if (matchCategory === 'Likely') categoryTagClass = 'tag-likely';

  // Extract tracker completion if saved
  const tracker = college.tracker || college.application_tracker || null;
  const trackerPct = tracker ? (tracker.completion_percentage ?? 0) : null;
  const trackerPlan = tracker?.plan || null;

  // Generate university initial monogram
  const initials = name.split(' ').map(w => w[0]).filter(Boolean).slice(0, 2).join('');

  return `
    <article class="college-card ${variant === 'compact' ? 'college-card-compact' : ''}" data-college-id="${id}">
      <div class="college-card-top">
        <div style="display: flex; gap: 12px; align-items: flex-start; flex: 1;">
          <div class="college-avatar" style="width: 44px; height: 44px; border-radius: 8px; background: linear-gradient(135deg, #1e293b, #0f172a); color: #fff; font-weight: 700; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.06); border: 1px solid #cbd5e1;">
            ${initials}
          </div>
          <div class="college-card-info" style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 2px;">
              <h3 class="college-card-name" style="margin: 0; font-size: 1.05rem; font-weight: 700; line-height: 1.3;">
                <a href="#/colleges/${id}" style="color: inherit; text-decoration: none;">${name}</a>
              </h3>
              <span class="category-tag ${categoryTagClass}" style="flex-shrink: 0;">${matchCategory}</span>
            </div>
            <div class="college-card-location" style="color: #64748b; font-size: 0.8125rem;">
              <span>${locationStr}</span>
              ${typeLabel ? `<span>•</span><span>${typeLabel}</span>` : ''}
            </div>
            ${trackerPct !== null ? `
              <div style="margin-top: 6px; display: flex; align-items: center; gap: 6px;">
                <div style="flex: 1; height: 5px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
                  <div style="width: ${trackerPct}%; height: 100%; background: ${trackerPct >= 100 ? '#10b981' : '#3b82f6'}; border-radius: 9999px;"></div>
                </div>
                <span style="font-size: 0.7rem; font-weight: 600; color: #475569;">${trackerPct}% App</span>
              </div>
            ` : ''}
          </div>
        </div>
      </div>

      <div class="college-card-stats">
        <div class="college-stat-item">
          <span class="college-stat-label">Admit Rate</span>
          <span class="college-stat-val">${formatMetricValue(admitRate, 'percent')}</span>
        </div>
        <div class="college-stat-item">
          <span class="college-stat-label">Avg Net Price</span>
          <span class="college-stat-val">${formatMetricValue(netPrice, 'currency')}</span>
        </div>
        <div class="college-stat-item">
          <span class="college-stat-label">10-Yr Earnings</span>
          <span class="college-stat-val">${formatMetricValue(earnings, 'currency')}</span>
        </div>
      </div>

      ${userNote ? `
        <div style="font-size: 0.8125rem; color: var(--text-secondary); background: #f8fafc; padding: 8px 12px; border-radius: var(--radius-sm); border-left: 3px solid var(--color-primary);">
          <strong>Note:</strong> ${userNote}
        </div>
      ` : ''}

      <div class="college-card-footer">
        <label class="compare-toggle-label">
          <input 
            type="checkbox" 
            class="compare-checkbox" 
            data-college-id="${id}"
            ${inCompare ? 'checked' : ''}
          />
          <span>Compare</span>
        </label>

        <div style="display: flex; align-items: center; gap: 8px;">
          <button 
            type="button"
            class="btn-save ${isSaved ? 'saved' : ''}" 
            data-action="toggle-save" 
            data-college-id="${id}"
            aria-label="${isSaved ? 'Remove from portfolio' : 'Save to portfolio'}"
          >
            <span>${isSaved ? '★' : '☆'}</span>
            <span>${isSaved ? 'Saved' : 'Save'}</span>
          </button>
          <a href="#/colleges/${id}" class="btn btn-sm btn-secondary">View Profile</a>
        </div>
      </div>
    </article>
  `;
}
