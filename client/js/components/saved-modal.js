/**
 * Saved Colleges Modal Component
 * Opens an interactive overlay showing all currently saved colleges with quick profile, compare, and remove controls.
 */
import { API } from '../api.js?v=4.0';
import { getCollegeImageUrl, getCampusSvgDataUri } from '../utils/college-images.js';
import { formatMetricValue } from './metric-card.js';

export const SavedModal = {


  initialized: false,

  init() {
    if (this.initialized) return;
    this.initialized = true;

    const modalHtml = `
      <div id="saved-colleges-modal" class="modal-overlay hidden" style="position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(4px); z-index: 9999; display: none; align-items: center; justify-content: center; padding: 20px;">
        <div class="modal-card" style="background: #ffffff; width: 100%; max-width: 620px; max-height: 85vh; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); display: flex; flex-direction: column; overflow: hidden; border: 1px solid #e2e8f0;">
          
          <!-- Modal Header -->
          <div style="padding: 20px 24px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; background: #f8fafc;">
            <div>
              <h3 id="saved-modal-title" style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin: 0;">Saved Colleges</h3>
              <p style="font-size: 0.8125rem; color: #64748b; margin: 2px 0 0 0;">Your current portfolio list</p>
            </div>
            <button id="close-saved-modal" style="background: none; border: none; font-size: 1.5rem; color: #64748b; cursor: pointer; padding: 4px 8px; border-radius: 6px; line-height: 1;" aria-label="Close saved modal">&times;</button>
          </div>

          <!-- Modal Body -->
          <div id="saved-modal-body" style="padding: 20px 24px; overflow-y: auto; flex: 1;">
            <!-- Populated dynamically -->
          </div>

          <!-- Modal Footer -->
          <div style="padding: 16px 24px; border-top: 1px solid #e2e8f0; background: #f8fafc; display: flex; justify-content: space-between; align-items: center;">
            <a href="#/compare" id="saved-modal-compare-link" class="btn btn-secondary btn-sm" style="font-weight: 600;">
              Compare All Saved
            </a>
            <button id="close-saved-modal-btn" class="btn btn-primary btn-sm">
              Done
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const overlay = document.getElementById('saved-colleges-modal');
    const closeBtn1 = document.getElementById('close-saved-modal');
    const closeBtn2 = document.getElementById('close-saved-modal-btn');

    const closeModal = () => {
      overlay.classList.add('hidden');
      overlay.style.display = 'none';
    };

    closeBtn1?.addEventListener('click', closeModal);
    closeBtn2?.addEventListener('click', closeModal);
    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal();
    });
  },

  open() {
    this.init();
    const overlay = document.getElementById('saved-colleges-modal');
    const body = document.getElementById('saved-modal-body');
    const title = document.getElementById('saved-modal-title');

    const savedColleges = window.app?.getSavedColleges() || [];

    title.textContent = `Saved Colleges (${savedColleges.length})`;

    if (savedColleges.length === 0) {
      body.innerHTML = `
        <div style="text-align: center; padding: 40px 20px; color: #64748b;">
          <div style="font-size: 3rem; margin-bottom: 12px;">☆</div>
          <h4 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">No Colleges Saved Yet</h4>
          <p style="font-size: 0.875rem; margin-bottom: 20px;">Explore colleges and click "Save College" to build your portfolio.</p>
          <a href="#/colleges" class="btn btn-primary" onclick="document.getElementById('saved-colleges-modal').style.display='none';">
            Explore Colleges →
          </a>
        </div>
      `;
    } else {
      body.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 12px;">
          ${savedColleges.map(c => {
            const cid = c.id || c.college_id;
            const name = c.college_name || c.name;
            const city = c.location?.city || c.city || '';
            const state = c.location?.state || c.state || '';
            const admit = c.admit_rate ?? c.summary?.acceptance_rate?.value ?? c.acceptance_rate;
            const price = c.net_price ?? c.summary?.average_net_price?.value ?? c.net_price_average;
            const tag = c.tag || c.fit_category || 'Target';

            let tagBg = '#dbeafe';
            let tagColor = '#1e40af';
            if (tag === 'Reach') { tagBg = '#ffedd5'; tagColor = '#c2410c'; }
            else if (tag === 'Likely') { tagBg = '#dcfce7'; tagColor = '#15803d'; }

            const imgUrl = getCollegeImageUrl(c, 'card');

            return `
              <div class="saved-item-row" style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff; gap: 14px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 200px;">
                  <img src="${imgUrl}" alt="${name}" style="width: 48px; height: 48px; border-radius: 8px; object-fit: cover; flex-shrink: 0; background: #0f172a;" onerror="this.onerror=null; this.src='${getCampusSvgDataUri(name, cid)}';" />
                  <div style="flex: 1; min-width: 0;">

                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                      <a href="#/colleges/${cid}" class="saved-college-link" data-cid="${cid}" style="font-size: 0.95rem; font-weight: 700; color: #0f172a; text-decoration: none;">
                        ${name}
                      </a>
                      <span style="font-size: 0.6875rem; font-weight: 700; padding: 2px 7px; border-radius: 999px; background: ${tagBg}; color: ${tagColor};">
                        ${tag}
                      </span>
                    </div>
                    <div style="font-size: 0.8125rem; color: #64748b;">
                      ${city}${state ? `, ${state}` : ''} • Admit: ${formatMetricValue(admit, 'percent')} • Net Price: ${price ? `$${price.toLocaleString()}` : '—'}
                    </div>

                  </div>
                </div>

                <div style="display: flex; align-items: center; gap: 8px;">
                  <a href="#/colleges/${cid}" class="btn btn-sm btn-ghost view-profile-btn" data-cid="${cid}" style="font-size: 0.8125rem; font-weight: 600;">
                    View Profile ↗
                  </a>
                  <button class="btn btn-sm btn-outline-danger remove-saved-btn" data-cid="${cid}" style="font-size: 0.8125rem; padding: 4px 10px; border: 1px solid #f87171; color: #dc2626; background: #fff; border-radius: 6px; cursor: pointer;">
                    Remove
                  </button>
                </div>
              </div>
            `;

          }).join('')}
        </div>
      `;

      // Bind view profile links to close modal on navigate
      body.querySelectorAll('.saved-college-link, .view-profile-btn').forEach(link => {
        link.addEventListener('click', () => {
          overlay.style.display = 'none';
          overlay.classList.add('hidden');
        });
      });

      // Bind remove buttons
      body.querySelectorAll('.remove-saved-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const cid = btn.getAttribute('data-cid');
          btn.disabled = true;
          btn.textContent = 'Removing…';
          try {
            const updated = await API.saveCollege(cid); // toggle save off
            if (window.app?.setPortfolio) window.app.setPortfolio(updated);
            if (window.app?.updatePortfolioIndicators) window.app.updatePortfolioIndicators();
            window.app.showToast('College removed from your portfolio', 'info');

            // Re-open/refresh modal content in place
            SavedModal.open();

            // Update any matching save buttons on the current page in-place
            document.querySelectorAll(`[data-action="toggle-save"][data-college-id="${cid}"]`).forEach(b => {
              if (b.classList.contains('btn-save')) {
                b.classList.remove('saved');
                b.setAttribute('aria-label', 'Save to portfolio');
                b.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display: inline-block; vertical-align: middle; margin-right: 3px;"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg><span>Save</span>`;
              } else {
                b.className = 'btn btn-secondary';
                b.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="display: inline-block; vertical-align: middle; margin-right: 4px;"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg><span>Save College</span>`;
              }
            });

            // Update dashboard silently if visible without full page refresh or scroll reset
            if (window.location.hash === '' || window.location.hash === '#/' || window.location.hash === '#/dashboard') {
              const appRoot = document.getElementById('app-root');
              if (appRoot && window.app?.state) {
                const currentScrollY = window.scrollY;
                import('../pages/dashboard.js').then(({ DashboardPage }) => {
                  DashboardPage.render(appRoot, window.app.state, { silent: true }).then(() => {
                    window.scrollTo({ top: currentScrollY, behavior: 'instant' });
                  });
                });
              }
            }
          } catch (err) {
            window.app.showToast(`Error removing: ${err.message}`, 'error');
            btn.disabled = false;
            btn.textContent = 'Remove';
          }


        });
      });
    }

    overlay.classList.remove('hidden');
    overlay.style.display = 'flex';
  }
};
