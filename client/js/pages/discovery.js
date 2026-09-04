/**
 * Discovery Page View (Route: #/colleges)
 * Search, faceted filters (State, Type, Cost, Admit Rate), sorting, and paginated results.
 */
import { API } from '../api.js?v=4.0';
import { renderCollegeCard } from '../components/college-card.js';
import { formatMetricValue } from '../components/metric-card.js';

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
];

export const DiscoveryPage = {
  params: {
    q: '',
    state: '',
    type: '',
    max_net_price: '',
    min_admit_rate: '',
    max_admit_rate: '',
    sort: 'relevance',
    limit: 12,
    offset: 0
  },

  debounceTimer: null,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-header">
        <div class="page-title-group">
          <h1>Explore Premier Colleges</h1>
          <p class="page-subtitle">Search 165+ premier universities with verified Scorecard data and multi-dimensional fit scoring.</p>
        </div>
      </div>

      <!-- Search & Filters Container -->
      <section class="card" style="margin-bottom: 28px;">
        <div style="display: flex; flex-direction: column; gap: 20px;">
          <!-- Main Search Input -->
          <div style="position: relative;">
            <input 
              type="text" 
              id="discovery-search" 
              class="input-text" 
              placeholder="Search by college name, alias, city, or state (e.g. FSU, UCF, Bama, Florida, Michigan)..." 
              value="${this.params.q}"
              style="width: 100%; padding: 12px 16px 12px 42px; font-size: 1rem;"
            />
            <span style="position: absolute; left: 16px; top: 50%; transform: translateY(-50%); display: flex; align-items: center; color: var(--text-muted);">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </span>

          </div>

          <!-- Faceted Filter Controls -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: flex-end;">
            <div class="form-group" style="margin-bottom: 0;">
              <label for="filter-state" class="form-label">State</label>
              <select id="filter-state" class="select-input">
                <option value="">All States</option>
                ${US_STATES.map(st => `<option value="${st}" ${this.params.state === st ? 'selected' : ''}>${st}</option>`).join('')}
              </select>
            </div>

            <div class="form-group" style="margin-bottom: 0;">
              <label for="filter-type" class="form-label">Institution Type</label>
              <select id="filter-type" class="select-input">
                <option value="">All Types</option>
                <option value="public" ${this.params.type === 'public' ? 'selected' : ''}>Public</option>
                <option value="private_nonprofit" ${this.params.type === 'private_nonprofit' ? 'selected' : ''}>Private Non-Profit</option>
                <option value="private_forprofit" ${this.params.type === 'private_forprofit' ? 'selected' : ''}>Private For-Profit</option>
              </select>
            </div>

            <div class="form-group" style="margin-bottom: 0;">
              <label for="filter-sort" class="form-label">Sort By</label>
              <select id="filter-sort" class="select-input">
                <option value="relevance" ${this.params.sort === 'relevance' || !this.params.sort ? 'selected' : ''}>Relevance / Featured</option>
                <option value="name_asc" ${this.params.sort === 'name_asc' ? 'selected' : ''}>Name (A–Z)</option>
                <option value="name_desc" ${this.params.sort === 'name_desc' ? 'selected' : ''}>Name (Z–A)</option>
                <option value="net_price_asc" ${this.params.sort === 'net_price_asc' ? 'selected' : ''}>Net Price (Low–High)</option>
                <option value="net_price_desc" ${this.params.sort === 'net_price_desc' ? 'selected' : ''}>Net Price (High–Low)</option>
                <option value="earnings_desc" ${this.params.sort === 'earnings_desc' ? 'selected' : ''}>10-Yr Earnings (High–Low)</option>
                <option value="admit_rate_asc" ${this.params.sort === 'admit_rate_asc' ? 'selected' : ''}>Admit Rate (Most Selective)</option>
                <option value="admit_rate_desc" ${this.params.sort === 'admit_rate_desc' ? 'selected' : ''}>Admit Rate (Least Selective)</option>
              </select>
            </div>


            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; gap: 8px;">
                <button type="button" id="reset-filters-btn" class="btn btn-secondary" style="width: 100%;">
                  Reset Filters
                </button>
              </div>
            </div>
          </div>

          <!-- Price & Admit Rate Sliders -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; border-top: 1px solid var(--color-border-subtle); padding-top: 16px;">
            <div>
              <div class="form-label">
                <span>Max Annual Net Price</span>
                <span id="price-slider-val" class="slider-val-badge">
                  ${this.params.max_net_price ? formatMetricValue(Number(this.params.max_net_price), 'currency') : 'Any Price'}
                </span>
              </div>
              <input 
                type="range" 
                id="slider-max-price" 
                class="range-slider" 
                min="10000" 
                max="80000" 
                step="5000" 
                value="${this.params.max_net_price || 80000}" 
                style="width: 100%;"
              />
            </div>

            <div>
              <div class="form-label">
                <span>Max Acceptance Rate</span>
                <span id="admit-slider-val" class="slider-val-badge">
                  ${this.params.max_admit_rate ? `${Math.round(Number(this.params.max_admit_rate) * 100)}%` : '100%'}
                </span>
              </div>
              <input 
                type="range" 
                id="slider-max-admit" 
                class="range-slider" 
                min="5" 
                max="100" 
                step="5" 
                value="${this.params.max_admit_rate ? Math.round(Number(this.params.max_admit_rate) * 100) : 100}" 
                style="width: 100%;"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- Results Grid Container -->
      <section aria-label="College Search Results">
        <div id="discovery-results-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px;">
          <span id="discovery-count" style="font-size: 0.9375rem; font-weight: 700; color: var(--text-secondary);">
            Loading colleges…
          </span>
        </div>

        <div id="discovery-grid" class="college-card-grid">
          <div class="loading-screen" style="grid-column: 1 / -1;">
            <div class="spinner"></div>
            <p class="loading-text">Fetching flagship colleges…</p>
          </div>
        </div>

        <!-- Pagination Controls -->
        <div id="discovery-pagination" style="display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 36px;"></div>
      </section>
    `;

    DiscoveryPage.bindFilters(container, state);
    await DiscoveryPage.fetchResults(container, state);
  },

  bindFilters(container, state) {
    const searchInput = container.querySelector('#discovery-search');
    const stateSelect = container.querySelector('#filter-state');
    const typeSelect = container.querySelector('#filter-type');
    const sortSelect = container.querySelector('#filter-sort');
    const priceSlider = container.querySelector('#slider-max-price');
    const priceValBadge = container.querySelector('#price-slider-val');
    const admitSlider = container.querySelector('#slider-max-admit');
    const admitValBadge = container.querySelector('#admit-slider-val');
    const resetBtn = container.querySelector('#reset-filters-btn');

    // Debounced Search & Instant Enter
    searchInput?.addEventListener('input', (e) => {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.params.q = e.target.value.trim();
        this.params.offset = 0;
        this.fetchResults(container, state);
      }, 250);
    });

    searchInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(this.debounceTimer);
        this.params.q = e.target.value.trim();
        this.params.offset = 0;
        this.fetchResults(container, state);
      }
    });


    stateSelect?.addEventListener('change', (e) => {
      this.params.state = e.target.value;
      this.params.offset = 0;
      this.fetchResults(container, state);
    });

    typeSelect?.addEventListener('change', (e) => {
      this.params.type = e.target.value;
      this.params.offset = 0;
      this.fetchResults(container, state);
    });

    sortSelect?.addEventListener('change', (e) => {
      this.params.sort = e.target.value;
      this.params.offset = 0;
      this.fetchResults(container, state);
    });

    priceSlider?.addEventListener('input', (e) => {
      const val = Number(e.target.value);
      if (val >= 80000) {
        this.params.max_net_price = '';
        priceValBadge.textContent = 'Any Price';
      } else {
        this.params.max_net_price = val;
        priceValBadge.textContent = formatMetricValue(val, 'currency');
      }
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.params.offset = 0;
        this.fetchResults(container, state);
      }, 300);
    });

    admitSlider?.addEventListener('input', (e) => {
      const val = Number(e.target.value);
      if (val >= 100) {
        this.params.max_admit_rate = '';
        admitValBadge.textContent = '100%';
      } else {
        this.params.max_admit_rate = (val / 100).toFixed(2);
        admitValBadge.textContent = `${val}%`;
      }
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.params.offset = 0;
        this.fetchResults(container, state);
      }, 300);
    });

    resetBtn?.addEventListener('click', () => {
      this.params = {
        q: '',
        state: '',
        type: '',
        max_net_price: '',
        min_admit_rate: '',
        max_admit_rate: '',
        sort: 'name_asc',
        limit: 12,
        offset: 0
      };
      this.render(container, state);
    });
  },

  async fetchResults(container, state) {
    const grid = container.querySelector('#discovery-grid');
    const countLabel = container.querySelector('#discovery-count');
    const paginationContainer = container.querySelector('#discovery-pagination');

    if (!grid) return;

    grid.innerHTML = `
      <div class="loading-screen" style="grid-column: 1 / -1;">
        <div class="spinner"></div>
        <p class="loading-text">Loading matching colleges…</p>
      </div>
    `;

    try {
      const data = await API.getColleges(this.params);
      const items = data.items || [];
      const total = data.total || items.length;

      if (countLabel) {
        countLabel.textContent = `Showing ${items.length} of ${total} Colleges`;
      }


      if (items.length === 0) {
        grid.innerHTML = `
          <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 48px 20px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 14px; background: #eff6ff; color: #2563eb; margin-bottom: 14px;">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <h3 style="font-size: 1.25rem; font-weight: 700;">No colleges match your filters</h3>

            <p style="color: var(--text-secondary); margin: 8px 0 16px;">Try adjusting your price slider, admit rate, or state search.</p>
          </div>
        `;
        if (paginationContainer) paginationContainer.innerHTML = '';
        return;
      }

      // Check saved status against portfolio
      const rawSaved = window.app?.getSavedColleges ? window.app.getSavedColleges() : (state.portfolio?.saved_colleges || state.portfolio?.colleges || state.portfolio?.items || []);
      const savedIds = new Set(rawSaved.map(c => String(c.college_id || c.id)));

      grid.innerHTML = items.map(college => {
        const id = String(college.id);
        const isSaved = savedIds.has(id);
        const inCompare = state.compareList.includes(id);

        return renderCollegeCard(college, {
          isSaved,
          inCompare,
          fitScore: college.fit_score || null
        });
      }).join('');

      // Render Pagination
      const totalPages = Math.ceil(total / this.params.limit);
      const currentPage = Math.floor(this.params.offset / this.params.limit) + 1;

      if (totalPages > 1 && paginationContainer) {
        paginationContainer.innerHTML = `
          <button 
            type="button" 
            class="btn btn-sm btn-secondary" 
            id="page-prev-btn" 
            ${currentPage <= 1 ? 'disabled' : ''}
          >
            ← Previous
          </button>
          <span style="font-size: 0.875rem; font-weight: 600; color: var(--text-secondary);">
            Page ${currentPage} of ${totalPages}
          </span>
          <button 
            type="button" 
            class="btn btn-sm btn-secondary" 
            id="page-next-btn" 
            ${currentPage >= totalPages ? 'disabled' : ''}
          >
            Next →
          </button>
        `;

        paginationContainer.querySelector('#page-prev-btn')?.addEventListener('click', () => {
          if (currentPage > 1) {
            this.params.offset -= this.params.limit;
            this.fetchResults(container, state);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        });

        paginationContainer.querySelector('#page-next-btn')?.addEventListener('click', () => {
          if (currentPage < totalPages) {
            this.params.offset += this.params.limit;
            this.fetchResults(container, state);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }
        });
      } else if (paginationContainer) {
        paginationContainer.innerHTML = '';
      }

    } catch (err) {
      console.error('Failed to load colleges', err);
      grid.innerHTML = `
        <div class="card" style="grid-column: 1 / -1; text-align: center; padding: 48px;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Failed to load colleges</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  }
};
