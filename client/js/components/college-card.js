/**
 * College Card Component
 * Renders college preview cards for discovery, dashboard, and search results.
 */
import { formatMetricValue } from './metric-card.js';
import { renderSourceBadge } from './source-badge.js';
import { getCollegeImageUrl, getCampusSvgDataUri } from '../utils/college-images.js';

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
  
  // Extract location display
  let locationStr = 'Location Not Specified';
  if (college.location) {
    if (typeof college.location === 'string') {
      locationStr = college.location;
    } else if (college.location.city && college.location.state) {
      locationStr = `${college.location.city}, ${college.location.state}`;
    } else if (college.location.state) {
      locationStr = college.location.state;
    }
  } else if (college.city || college.state) {
    locationStr = [college.city, college.state].filter(Boolean).join(', ');
  }

  // Institution Type
  const rawType = college.type || college.control || (college.ownership === 1 ? 'public' : 'private_nonprofit');
  const typeLabel = rawType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

  // Category Tag
  const matchCategory = category || college.fit_category || college.fit?.category || 'Target';

  let categoryTagClass = 'tag-target';
  if (matchCategory === 'Reach') categoryTagClass = 'tag-reach';
  if (matchCategory === 'Likely') categoryTagClass = 'tag-likely';

  // Metrics extraction
  const netPrice = college.average_net_price ?? college.net_price ?? college.cost?.average_net_price ?? college.cost?.net_price_average;
  const admitRate = college.acceptance_rate ?? college.admissions?.acceptance_rate ?? college.admit_rate;
  const earnings = college.median_earnings_10yr ?? college.median_earnings ?? college.outcomes?.median_earnings_10yr ?? college.outcomes?.median_earnings;

  // Extract tracker completion if saved
  const tracker = college.tracker || college.application_tracker || null;
  const trackerPct = tracker ? (tracker.completion_percentage ?? 0) : null;

  // University campus photo with SVG fallback
  const imageUrl = getCollegeImageUrl(college, 'card');
  const fallbackSvg = getCampusSvgDataUri(name, id);

  return `
    <article class="college-card ${variant === 'compact' ? 'college-card-compact' : ''}" data-college-id="${id}">
      <!-- Campus Photography Banner -->
      <div class="college-card-media">
        <img 
          src="${imageUrl}" 
          alt="${name} campus" 
          loading="lazy"
          onerror="this.onerror=null; this.src='${fallbackSvg}';"
        />
        <div class="college-card-media-overlay"></div>

        <div class="college-card-media-badge">
          <span class="category-tag ${categoryTagClass}">${matchCategory}</span>
        </div>
      </div>

      <div class="college-card-top">
        <div style="flex: 1; min-width: 0;">
          <h3 class="college-card-name" style="margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 700; line-height: 1.35;">
            <a href="#/colleges/${id}" style="color: inherit; text-decoration: none;">${name}</a>
          </h3>
          <div class="college-card-location" style="color: #64748b; font-size: 0.8125rem;">
            <span>${locationStr}</span>
            ${typeLabel ? `<span>•</span><span>${typeLabel}</span>` : ''}
          </div>
          ${trackerPct !== null ? `
            <div style="margin-top: 8px; display: flex; align-items: center; gap: 6px;">
              <div style="flex: 1; height: 5px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
                <div style="width: ${trackerPct}%; height: 100%; background: ${trackerPct >= 100 ? '#10b981' : '#3b82f6'}; border-radius: 9999px;"></div>
              </div>
              <span style="font-size: 0.7rem; font-weight: 600; color: #475569;">${trackerPct}% App</span>
            </div>
          ` : ''}
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
            <svg width="13" height="13" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2.5" style="display: inline-block; vertical-align: middle; margin-right: 3px;"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
            <span>${isSaved ? 'Saved' : 'Save'}</span>
          </button>
          <a href="#/colleges/${id}" class="btn btn-sm btn-secondary">View Profile</a>
        </div>
      </div>
    </article>
  `;
}
