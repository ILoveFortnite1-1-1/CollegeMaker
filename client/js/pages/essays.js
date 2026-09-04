/**
 * Essay Tracker Page View (Route: #/essays)
 * Feature R3: Essay cards with prompt, word limit, word count progress bar,
 * draft status indicators ('Not Started', 'Drafting', 'Reviewing', 'Final'),
 * applied colleges reuse tracking, "Used for N schools" badge, and full CRUD modals.
 */
import { API } from '../api.js';

export const EssaysPage = {
  statusFilter: 'all',
  categoryFilter: 'all', // 'all', 'supplemental', 'common_app'
  editingEssayId: null,

  isCommonAppEssay(essay) {
    if (!essay) return false;
    if (essay.is_common_app === true || essay.is_common_app_main === true) return true;
    if (essay.essay_type === 'Common App' || essay.type === 'Common App') return true;
    const title = (essay.title || '').toLowerCase();
    if (title.includes('common app') || title.includes('personal statement')) return true;
    return false;
  },

  async render(container, state, options = {}) {
    if (!options?.silent) {
      container.innerHTML = `
        <div class="loading-screen">
          <div class="spinner"></div>
          <p class="loading-text">Loading essay portfolio…</p>
        </div>
      `;
    }

    try {
      const [essayData, portfolioData] = await Promise.all([
        API.getEssays().catch(() => ({ essays: [], count: 0 })),
        API.getPortfolio().catch(() => ({ saved_colleges: [] }))
      ]);

      const essays = essayData.essays || [];
      const savedColleges = (portfolioData.portfolio && portfolioData.portfolio.colleges)
        || portfolioData.saved_colleges
        || portfolioData.colleges
        || portfolioData.items
        || (window.app?.getSavedColleges ? window.app.getSavedColleges() : [])
        || state?.portfolio?.saved_colleges
        || state?.portfolio?.colleges
        || [];
      const collegeMap = {};
      savedColleges.forEach(c => {
        collegeMap[String(c.college_id || c.id)] = c.canonical_name || c.college_name || c.name;
      });

      // Filter essays by category and status
      const filteredEssays = essays.filter(e => {
        const isCommon = this.isCommonAppEssay(e);
        if (this.categoryFilter === 'supplemental' && isCommon) return false;
        if (this.categoryFilter === 'common_app' && !isCommon) return false;
        if (this.statusFilter !== 'all' && (e.draft_status || e.status) !== this.statusFilter) return false;
        return true;
      });

      // Categorization metrics
      const totalCount = essays.length;
      const supplementalEssays = essays.filter(e => !this.isCommonAppEssay(e));
      const commonAppEssays = essays.filter(e => this.isCommonAppEssay(e));
      const suppCount = supplementalEssays.length;
      const commonCount = commonAppEssays.length;

      const finalCount = essays.filter(e => (e.draft_status || e.status) === 'Final').length;
      const draftingCount = essays.filter(e => (e.draft_status || e.status) === 'Drafting' || (e.draft_status || e.status) === 'Reviewing').length;
      const reusedCount = essays.filter(e => (e.colleges && e.colleges.length > 1)).length;
      const totalWords = essays.reduce((sum, e) => sum + (e.current_word_count || e.word_count || 0), 0);

      // College supplemental needs breakdown ("ones needed")
      const collegeNeeds = savedColleges.map(c => {
        const cid = String(c.college_id || c.id);
        const name = c.canonical_name || c.college_name || c.name;
        const needsSupp = c.tracker?.has_supplemental_essays !== false;
        const assignedEssays = supplementalEssays.filter(e => (e.colleges || []).some(sc => String(sc) === cid));
        return {
          id: cid,
          name: name,
          needsSupp: needsSupp,
          assignedCount: assignedEssays.length,
          completedCount: assignedEssays.filter(e => (e.draft_status || e.status) === 'Final').length
        };
      });

      container.innerHTML = `
        <div class="essays-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 28px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Admissions Writing</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">Supplemental &amp; Common App Essays</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">
                Track college-specific supplemental essays separately from your generic Common App personal statement, monitor word counts, and track reuse across schools.
              </p>
            </div>

            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
              <button type="button" id="btn-apply-common-app-all" class="btn btn-secondary" style="display: flex; align-items: center; gap: 6px; background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; font-weight: 600;" title="Assign your Common App personal statement to all saved colleges in 1 click">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M9 14l2 2 4-4"/></svg>
                <span>Apply Common App Essay to All</span>
              </button>
              <button type="button" id="btn-new-essay" class="btn btn-primary" style="display: flex; align-items: center; gap: 6px;">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>New Essay</span>
              </button>
            </div>
          </div>

          <!-- Top Metric Cards Strip -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Supplemental Essays</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #0284c7;">${suppCount}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">College-specific prompts</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Common App Essay</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #7c3aed;">${commonCount > 0 ? `${commonCount} Drafted` : '0'}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Generic personal statement</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Ready (Final Drafts)</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #16a34a;">${finalCount}</div>
              <div style="font-size: 0.75rem; color: #166534; margin-top: 4px;">Ready to submit</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">In Progress</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #d97706;">${draftingCount}</div>
              <div style="font-size: 0.75rem; color: #92400e; margin-top: 4px;">Drafting or reviewing</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Reused Prompts</div>
              <div style="font-size: 1.6rem; font-weight: 800; color: #2563eb;">${reusedCount}</div>
              <div style="font-size: 0.75rem; color: #1e40af; margin-top: 4px;">Used across 2+ schools</div>
            </div>
          </div>

          <!-- Section: Supplemental Essays Needed by College -->
          ${savedColleges.length > 0 ? `
            <div class="card" style="background: #ffffff; border: 1px solid var(--color-border); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
                <div>
                  <h3 style="font-size: 1rem; font-weight: 700; color: var(--text-primary); margin: 0 0 2px 0;">
                    Supplemental Essays by College
                  </h3>
                  <p style="font-size: 0.8125rem; color: var(--text-secondary); margin: 0;">
                    Track and manage college-specific supplemental essays for your saved schools.
                  </p>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px;">
                ${collegeNeeds.map(cn => `
                  <div style="border: 1px solid var(--color-border); border-radius: 8px; padding: 12px 14px; background: #fafbfc; display: flex; justify-content: space-between; align-items: center;">
                    <div style="min-width: 0; margin-right: 12px;">
                      <strong style="display: block; font-size: 0.875rem; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        ${cn.name}
                      </strong>
                      <div style="display: flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 0.75rem;">
                        <span style="color: var(--text-muted); font-family: var(--font-mono);">
                          ${cn.assignedCount} drafted
                        </span>
                      </div>
                    </div>

                    <button type="button" class="btn btn-sm btn-ghost btn-add-supp-for-college" data-college-id="${cn.id}" style="font-size: 0.75rem; padding: 4px 10px; border: 1px solid var(--color-border); background: #fff; white-space: nowrap;">
                      + Supplement
                    </button>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Filter Toolbars -->
          <div class="filter-toolbar" style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;">
            <!-- Category Tabs -->
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-right: 4px;">Category:</span>
              <button type="button" class="btn btn-sm ${this.categoryFilter === 'all' ? 'btn-primary' : 'btn-secondary'} filter-category-btn" data-category="all">
                All Essays (${totalCount})
              </button>
              <button type="button" class="btn btn-sm ${this.categoryFilter === 'supplemental' ? 'btn-primary' : 'btn-secondary'} filter-category-btn" data-category="supplemental">
                College Supplementals (${suppCount})
              </button>
              <button type="button" class="btn btn-sm ${this.categoryFilter === 'common_app' ? 'btn-primary' : 'btn-secondary'} filter-category-btn" data-category="common_app">
                Common App Personal Statement (${commonCount})
              </button>
            </div>

            <!-- Status Tabs -->
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-right: 4px;">Status:</span>
              <button type="button" class="btn btn-sm ${this.statusFilter === 'all' ? 'btn-primary' : 'btn-secondary'} filter-status-btn" data-status="all">
                All Status
              </button>
              <button type="button" class="btn btn-sm ${this.statusFilter === 'Not Started' ? 'btn-primary' : 'btn-secondary'} filter-status-btn" data-status="Not Started">
                Not Started
              </button>
              <button type="button" class="btn btn-sm ${this.statusFilter === 'Drafting' ? 'btn-primary' : 'btn-secondary'} filter-status-btn" data-status="Drafting">
                Drafting
              </button>
              <button type="button" class="btn btn-sm ${this.statusFilter === 'Reviewing' ? 'btn-primary' : 'btn-secondary'} filter-status-btn" data-status="Reviewing">
                Reviewing
              </button>
              <button type="button" class="btn btn-sm ${this.statusFilter === 'Final' ? 'btn-primary' : 'btn-secondary'} filter-status-btn" data-status="Final">
                Final (${finalCount})
              </button>
            </div>
          </div>

          <!-- Essay Card Grid -->
          ${filteredEssays.length === 0 ? `
            <div class="card empty-state" style="padding: 48px 24px; text-align: center; background: #fff; border-radius: 12px; border: 1px dashed var(--color-border);">
              <div style="width: 56px; height: 56px; border-radius: 12px; background: #f1f5f9; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 14px;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              </div>
              <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin: 0 0 6px 0;">No Essays in this View</h3>
              <p style="font-size: 0.875rem; color: var(--text-muted); margin: 0 0 18px 0;">
                ${this.categoryFilter === 'supplemental'
                  ? 'No supplemental essays found. College supplemental essays are separate from your main Common App essay.'
                  : (this.categoryFilter === 'common_app'
                    ? 'No Common App personal statement drafted yet. Create your generic 650-word personal statement.'
                    : (this.statusFilter !== 'all' ? `No essays currently marked as "${this.statusFilter}".` : 'Start organizing your essays by creating your first entry.'))}
              </p>
              <button type="button" class="btn btn-primary btn-sm" id="btn-empty-new-essay">+ Add Essay</button>
            </div>
          ` : `
            <div class="essay-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px;">
              ${filteredEssays.map(essay => this.renderEssayCard(essay, collegeMap)).join('')}
            </div>
          `}

          <!-- Essay CRUD Modal -->
          <div id="essay-modal" class="modal-backdrop" style="display: none; position: fixed; inset: 0; background: rgba(15,23,42,0.6); z-index: 999; align-items: center; justify-content: center; padding: 20px;">
            <div class="card modal-dialog" style="max-width: 580px; width: 100%; background: #ffffff; border-radius: 12px; padding: 28px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 id="essay-modal-title" style="margin: 0; font-size: 1.25rem; font-weight: 800; color: var(--text-primary);">New Essay</h3>
                <button type="button" id="btn-close-essay-modal" class="btn btn-ghost" style="font-size: 1.2rem; padding: 4px 8px;">✕</button>
              </div>

              <form id="essay-form">
                <!-- Essay Category Selector -->
                <div style="margin-bottom: 16px;">
                  <label style="display: block; font-size: 0.8125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
                    Essay Type *
                  </label>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <label id="label-cat-supp" style="display: flex; align-items: flex-start; gap: 8px; padding: 10px; border: 1px solid var(--color-primary); border-radius: 8px; cursor: pointer; background: #f0fdf4;">
                      <input type="radio" name="essay_category_radio" id="radio-essay-supp" value="Supplemental" checked style="margin-top: 2px;" />
                      <div>
                        <strong style="display: block; font-size: 0.8125rem; color: var(--text-primary);">College Supplemental</strong>
                        <span style="font-size: 0.725rem; color: var(--text-secondary); display: block;">Specific prompt required by one or more colleges</span>
                      </div>
                    </label>

                    <label id="label-cat-common" style="display: flex; align-items: flex-start; gap: 8px; padding: 10px; border: 1px solid var(--color-border); border-radius: 8px; cursor: pointer; background: #fff;">
                      <input type="radio" name="essay_category_radio" id="radio-essay-common" value="Common App" style="margin-top: 2px;" />
                      <div>
                        <strong style="display: block; font-size: 0.8125rem; color: var(--text-primary);">Common App Main Essay</strong>
                        <span style="font-size: 0.725rem; color: var(--text-secondary); display: block;">Generic 650-word personal statement for all schools</span>
                      </div>
                    </label>
                  </div>
                </div>

                <div style="margin-bottom: 16px;">
                  <label style="display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Essay Title / Label *
                  </label>
                  <input type="text" id="essay-input-title" class="text-input" placeholder="e.g. Why Major Supplement, Leadership Experience" required style="width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                </div>

                <div style="margin-bottom: 16px;">
                  <label style="display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Official Prompt Text *
                  </label>
                  <textarea id="essay-input-prompt" class="text-input" rows="3" placeholder="Paste the university's exact prompt text here..." required style="width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem; resize: vertical;"></textarea>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Word Limit
                    </label>
                    <input type="number" id="essay-input-limit" class="text-input" min="1" placeholder="650" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Current Word Count
                    </label>
                    <input type="number" id="essay-input-count" class="text-input" min="0" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Draft Status
                    </label>
                    <select id="essay-input-status" class="select-input" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;">
                      <option value="Not Started">Not Started</option>
                      <option value="Drafting">Drafting</option>
                      <option value="Reviewing">Reviewing</option>
                      <option value="Final">Final</option>
                    </select>
                  </div>
                </div>

                <div id="essay-colleges-wrapper" style="margin-bottom: 16px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <label style="font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin: 0;">
                      Assigned Colleges
                    </label>
                    <button type="button" id="btn-select-all-colleges" class="btn btn-sm btn-ghost" style="font-size: 0.725rem; color: var(--color-primary); padding: 2px 6px;">
                      Select All (${savedColleges.length})
                    </button>
                  </div>
                  <div id="essay-colleges-checklist" style="max-height: 140px; overflow-y: auto; border: 1px solid var(--color-border); border-radius: 6px; padding: 8px 12px; display: flex; flex-direction: column; gap: 6px; background: #f8fafc;">
                    ${savedColleges.map(c => `
                      <label style="display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; cursor: pointer;">
                        <input type="checkbox" class="essay-college-cb" value="${c.college_id || c.id}" />
                        <span>${c.canonical_name || c.college_name || c.name}</span>
                      </label>
                    `).join('')}
                  </div>
                  <div id="essay-common-notice" style="display: none; background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 10px 12px; margin-top: 8px; font-size: 0.75rem; color: #7c3aed;">
                    <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                      <span>This generic personal statement automatically applies to all Common App universities.</span>
                      <button type="button" id="btn-modal-check-all-common" class="btn btn-sm" style="background: #7c3aed; color: #fff; font-size: 0.7rem; padding: 3px 8px; border-radius: 4px; white-space: nowrap;">
                        ✓ Link to All Schools
                      </button>
                    </div>
                  </div>
                </div>

                <div style="margin-bottom: 24px;">
                  <label style="display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Working Draft / Outline Notes (Optional)
                  </label>
                  <textarea id="essay-input-content" class="text-input" rows="4" placeholder="Draft notes, topic ideas, or text..." style="width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem; resize: vertical;"></textarea>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 10px;">
                  <button type="button" id="btn-cancel-essay-modal" class="btn btn-secondary">Cancel</button>
                  <button type="submit" class="btn btn-primary" id="btn-save-essay-submit">Save Essay</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;

      EssaysPage.bindEvents(container, state, essays, savedColleges);

    } catch (err) {
      console.error('Failed to render essays page', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 40px auto;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Unable to load essays</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  renderEssayCard(essay, collegeMap) {
    const status = essay.draft_status || essay.status || 'Not Started';
    const limit = essay.word_limit || 650;
    const count = essay.current_word_count || essay.word_count || 0;
    const pct = Math.min(100, Math.round((count / limit) * 100));
    const isOver = count > limit;
    const colleges = essay.colleges || [];
    const reuseCount = colleges.length;
    const isCommon = this.isCommonAppEssay(essay);

    // Status pill style
    const statusStyles = {
      'Not Started': 'background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;',
      'Drafting': 'background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe;',
      'Reviewing': 'background: #fef3c7; color: #92400e; border: 1px solid #fde68a;',
      'Final': 'background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;'
    };
    const pillStyle = statusStyles[status] || statusStyles['Not Started'];

    // Progress bar color
    const barColor = isOver ? '#ef4444' : (pct >= 90 ? '#10b981' : '#3b82f6');

    return `
      <div class="essay-card card" style="background: #fff; border: 1px solid var(--color-border); border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); display: flex; flex-direction: column; justify-content: space-between;">
        <div>
          <!-- Top Row: Category Badge & Status -->
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 8px; flex-wrap: wrap;">
            ${isCommon ? `
              <span class="category-badge" style="background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; font-size: 0.725rem; font-weight: 700; padding: 3px 8px; border-radius: 4px;">
                Common App Personal Statement
              </span>
            ` : (reuseCount > 1 ? `
              <span class="reuse-badge" style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.725rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; display: inline-flex; align-items: center; gap: 4px;">
                Supplemental (Used for ${reuseCount} schools)
              </span>
            ` : (reuseCount === 1 ? `
              <span style="background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; font-size: 0.725rem; font-weight: 600; padding: 3px 8px; border-radius: 4px;">
                College Supplemental (1 school)
              </span>
            ` : `
              <span style="background: #f8fafc; color: #94a3b8; border: 1px dashed var(--color-border); font-size: 0.725rem; padding: 3px 8px; border-radius: 4px;">
                College Supplemental (Unassigned)
              </span>
            `))}

            <span class="essay-status-pill" style="font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; ${pillStyle}">
              ${status}
            </span>
          </div>

          <!-- Essay Title -->
          <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); margin: 0 0 8px 0; line-height: 1.3;">
            ${essay.title || 'Untitled Essay'}
          </h3>

          <!-- Prompt Preview -->
          <div style="background: #f8fafc; border-left: 3px solid var(--color-border-strong); padding: 8px 12px; border-radius: 4px; margin-bottom: 16px;">
            <p style="font-size: 0.8125rem; color: var(--text-secondary); margin: 0; line-height: 1.45; max-height: 60px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
              "${essay.prompt}"
            </p>
          </div>

          <!-- Word Count Meter -->
          <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; margin-bottom: 4px;">
              <span style="color: var(--text-muted);">Word Progress:</span>
              <span style="font-weight: 700; font-family: var(--font-mono); color: ${isOver ? '#dc2626' : 'var(--text-primary)'};">
                ${count} / ${limit} words
                ${isOver ? ` <span style="color: #dc2626; font-size: 0.7rem;">(+${count - limit} over)</span>` : ''}
              </span>
            </div>
            <div class="progress-track" style="height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden;">
              <div class="progress-fill" style="width: ${pct}%; height: 100%; background: ${barColor}; border-radius: 4px; transition: width 0.3s ease;"></div>
            </div>
          </div>

          <!-- Associated Schools Chips -->
          ${!isCommon && colleges.length > 0 ? `
            <div style="margin-bottom: 16px;">
              <span style="display: block; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px; letter-spacing: 0.04em;">Required By Colleges:</span>
              <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                ${colleges.map(cid => `
                  <span style="font-size: 0.725rem; background: #f1f5f9; color: var(--text-secondary); padding: 2px 8px; border-radius: 4px; border: 1px solid var(--color-border);">
                    ${collegeMap[cid] || cid}
                  </span>
                `).join('')}
              </div>
            </div>
          ` : (isCommon ? `
            <div style="margin-bottom: 16px;">
              <span style="font-size: 0.725rem; color: #7c3aed; background: #f3e8ff; padding: 3px 8px; border-radius: 4px; display: inline-block;">
                Shared across all Common App schools
              </span>
            </div>
          ` : '')}
        </div>

        <!-- Action Footer -->
        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--color-border-subtle); margin-top: 8px;">
          <button type="button" class="btn-delete-essay btn btn-sm btn-ghost" data-essay-id="${essay.id}" style="color: #dc2626; padding: 4px 8px; font-size: 0.75rem;">
            Delete
          </button>
          <div style="display: flex; gap: 8px; align-items: center;">
            ${isCommon ? `
              <button type="button" class="btn-card-apply-all btn btn-sm btn-ghost" data-essay-id="${essay.id}" style="color: #7c3aed; font-weight: 600; font-size: 0.75rem; border: 1px solid #ddd6fe; background: #faf5ff; padding: 4px 8px;" title="Apply this Common App essay to all saved colleges in 1 click">
                ✓ Apply to All
              </button>
            ` : ''}
            <button type="button" class="btn-edit-essay btn btn-sm btn-secondary" data-essay-id="${essay.id}" style="padding: 4px 12px; font-size: 0.75rem; font-weight: 600;">
              Edit Essay ✎
            </button>
          </div>
        </div>
      </div>
    `;
  },

  bindEvents(container, state, essays, savedColleges = []) {
    const getActiveColleges = () => {
      if (savedColleges && savedColleges.length > 0) return savedColleges;
      return (window.app?.getSavedColleges ? window.app.getSavedColleges() : [])
        || state?.portfolio?.saved_colleges
        || state?.portfolio?.colleges
        || [];
    };

    const modal = container.querySelector('#essay-modal');
    const newBtn = container.querySelector('#btn-new-essay');
    const emptyNewBtn = container.querySelector('#btn-empty-new-essay');
    const closeBtn = container.querySelector('#btn-close-essay-modal');
    const cancelBtn = container.querySelector('#btn-cancel-essay-modal');
    const form = container.querySelector('#essay-form');
    const modalTitle = container.querySelector('#essay-modal-title');

    const radioSupp = container.querySelector('#radio-essay-supp');
    const radioCommon = container.querySelector('#radio-essay-common');
    const labelCatSupp = container.querySelector('#label-cat-supp');
    const labelCatCommon = container.querySelector('#label-cat-common');
    const collegesWrapper = container.querySelector('#essay-colleges-wrapper');
    const commonNotice = container.querySelector('#essay-common-notice');

    const titleInput = container.querySelector('#essay-input-title');
    const promptInput = container.querySelector('#essay-input-prompt');
    const limitInput = container.querySelector('#essay-input-limit');
    const countInput = container.querySelector('#essay-input-count');
    const statusSelect = container.querySelector('#essay-input-status');
    const contentInput = container.querySelector('#essay-input-content');
    const collegeCbs = container.querySelectorAll('.essay-college-cb');

    // Category Filter buttons
    container.querySelectorAll('.filter-category-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.categoryFilter = btn.getAttribute('data-category');
        this.render(container, state, { silent: true });
      });
    });

    // Status Filter buttons
    container.querySelectorAll('.filter-status-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.statusFilter = btn.getAttribute('data-status');
        this.render(container, state, { silent: true });
      });
    });

    // Radio category change in modal
    const syncCategoryUI = () => {
      const isCommon = radioCommon && radioCommon.checked;
      if (labelCatSupp && labelCatCommon) {
        if (isCommon) {
          labelCatCommon.style.background = '#f5f3ff';
          labelCatCommon.style.borderColor = '#8b5cf6';
          labelCatSupp.style.background = '#fff';
          labelCatSupp.style.borderColor = 'var(--color-border)';
          if (commonNotice) commonNotice.style.display = 'block';
        } else {
          labelCatSupp.style.background = '#f0fdf4';
          labelCatSupp.style.borderColor = 'var(--color-primary)';
          labelCatCommon.style.background = '#fff';
          labelCatCommon.style.borderColor = 'var(--color-border)';
          if (commonNotice) commonNotice.style.display = 'none';
        }
      }
    };

    if (radioSupp) radioSupp.addEventListener('change', syncCategoryUI);
    if (radioCommon) radioCommon.addEventListener('change', syncCategoryUI);

    const openModal = (essay = null, preselectedCollegeId = null) => {
      this.editingEssayId = essay ? essay.id : null;
      if (essay) {
        modalTitle.textContent = 'Edit Essay';
        titleInput.value = essay.title || '';
        promptInput.value = essay.prompt || '';
        limitInput.value = essay.word_limit || 650;
        countInput.value = essay.current_word_count || essay.word_count || 0;
        statusSelect.value = essay.draft_status || essay.status || 'Not Started';
        contentInput.value = essay.content || '';

        const isCommon = this.isCommonAppEssay(essay);
        if (isCommon && radioCommon) {
          radioCommon.checked = true;
        } else if (radioSupp) {
          radioSupp.checked = true;
        }

        const assigned = new Set(essay.colleges || []);
        collegeCbs.forEach(cb => {
          cb.checked = assigned.has(cb.value);
        });
      } else {
        modalTitle.textContent = 'New Essay';
        titleInput.value = '';
        promptInput.value = '';
        limitInput.value = 650;
        countInput.value = 0;
        statusSelect.value = 'Not Started';
        contentInput.value = '';

        if (radioSupp) radioSupp.checked = true;

        collegeCbs.forEach(cb => {
          cb.checked = preselectedCollegeId ? String(cb.value) === String(preselectedCollegeId) : false;
        });
      }

      syncCategoryUI();
      if (modal) modal.style.display = 'flex';
    };

    const closeModal = () => {
      if (modal) modal.style.display = 'none';
      this.editingEssayId = null;
    };

    if (newBtn) newBtn.addEventListener('click', () => openModal(null));
    if (emptyNewBtn) emptyNewBtn.addEventListener('click', () => openModal(null));
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // "+ Supplement" quick button per college
    container.querySelectorAll('.btn-add-supp-for-college').forEach(btn => {
      btn.addEventListener('click', () => {
        const cid = btn.getAttribute('data-college-id');
        openModal(null, cid);
      });
    });

    // Edit button clicks
    container.querySelectorAll('.btn-edit-essay').forEach(btn => {
      btn.addEventListener('click', () => {
        const eid = btn.getAttribute('data-essay-id');
        const essay = essays.find(e => String(e.id) === String(eid));
        if (essay) openModal(essay);
      });
    });

    // Delete button clicks
    container.querySelectorAll('.btn-delete-essay').forEach(btn => {
      btn.addEventListener('click', async () => {
        const eid = btn.getAttribute('data-essay-id');
        if (!confirm('Are you sure you want to delete this essay entry?')) return;

        try {
          await API.deleteEssay(eid);
          if (window.app?.showToast) {
            window.app.showToast('Essay deleted.', 'info');
          }
          this.render(container, state, { silent: true });
        } catch (err) {
          console.error('Failed to delete essay', err);
          if (window.app?.showToast) {
            window.app.showToast(err.message || 'Delete failed', 'error');
          }
        }
      });
    });

    // "Apply Common App Essay to All" top button
    const applyCommonBtn = container.querySelector('#btn-apply-common-app-all');
    if (applyCommonBtn) {
      applyCommonBtn.addEventListener('click', async () => {
        const collegesList = getActiveColleges();
        const allCollegeIds = collegesList.map(c => String(c.college_id || c.id || c));

        applyCommonBtn.disabled = true;
        applyCommonBtn.textContent = 'Applying...';

        try {
          const existingCommon = essays.find(e => this.isCommonAppEssay(e));
          if (existingCommon) {
            await API.updateEssay(existingCommon.id, {
              colleges: allCollegeIds,
              is_common_app: true,
              essay_type: 'Common App'
            });
          } else {
            await API.createEssay({
              title: 'Common App Personal Statement',
              prompt: 'Share an essay on any topic of your choice or one of the official Common App prompts.',
              word_limit: 650,
              current_word_count: 0,
              word_count: 0,
              draft_status: 'Drafting',
              is_common_app: true,
              essay_type: 'Common App',
              colleges: allCollegeIds,
              content: ''
            });
          }

          if (allCollegeIds.length > 0) {
            try {
              await API.toggleRequirementAll('Common App Main Essay', true);
            } catch (err) {}
          }

          if (window.app?.showToast) {
            window.app.showToast(
              allCollegeIds.length > 0
                ? `Common App Personal Statement applied to all ${allCollegeIds.length} schools!`
                : 'Common App Personal Statement created!',
              'success'
            );
          }
          await this.render(container, state, { silent: true });
        } catch (err) {
          console.error('Failed to apply Common App essay to all', err);
          if (window.app?.showToast) {
            window.app.showToast(err.message || 'Failed to apply Common App essay', 'error');
          }
          applyCommonBtn.disabled = false;
          applyCommonBtn.textContent = 'Apply Common App Essay to All';
        }
      });
    }

    // Card "Apply to All" button clicks
    container.querySelectorAll('.btn-card-apply-all').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const eid = btn.getAttribute('data-essay-id');
        const collegesList = getActiveColleges();
        const allCollegeIds = collegesList.map(c => String(c.college_id || c.id || c));
        try {
          btn.disabled = true;
          btn.textContent = 'Applying...';
          await API.updateEssay(eid, {
            colleges: allCollegeIds,
            is_common_app: true,
            essay_type: 'Common App'
          });
          if (allCollegeIds.length > 0) {
            try {
              await API.toggleRequirementAll('Common App Main Essay', true);
            } catch (err) {}
          }
          if (window.app?.showToast) {
            window.app.showToast(
              allCollegeIds.length > 0
                ? `Common App essay applied to all ${allCollegeIds.length} schools!`
                : 'Common App essay updated!',
              'success'
            );
          }
          await this.render(container, state, { silent: true });
        } catch (err) {
          console.error(err);
          btn.disabled = false;
          btn.textContent = '✓ Apply to All';
        }
      });
    });

    // Select All in modal
    const selectAllBtn = container.querySelector('#btn-select-all-colleges');
    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', () => {
        const allChecked = Array.from(collegeCbs).every(cb => cb.checked);
        collegeCbs.forEach(cb => { cb.checked = !allChecked; });
        selectAllBtn.textContent = allChecked ? `Select All (${collegeCbs.length})` : 'Deselect All';
      });
    }

    // Link All in Common notice
    const linkAllCommonBtn = container.querySelector('#btn-modal-check-all-common');
    if (linkAllCommonBtn) {
      linkAllCommonBtn.addEventListener('click', () => {
        collegeCbs.forEach(cb => { cb.checked = true; });
        linkAllCommonBtn.textContent = '✓ All Linked';
      });
    }

    // Form submit (create or update)
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const isCommon = radioCommon && radioCommon.checked;
        const collegesList = getActiveColleges();
        const selectedColleges = isCommon
          ? collegesList.map(c => String(c.college_id || c.id || c))
          : Array.from(collegeCbs).filter(cb => cb.checked).map(cb => cb.value);

        const payload = {
          title: titleInput.value.trim(),
          prompt: promptInput.value.trim(),
          word_limit: limitInput.value ? parseInt(limitInput.value, 10) : 650,
          word_count: countInput.value ? parseInt(countInput.value, 10) : 0,
          current_word_count: countInput.value ? parseInt(countInput.value, 10) : 0,
          draft_status: statusSelect.value,
          essay_type: isCommon ? 'Common App' : 'Supplemental',
          is_common_app: Boolean(isCommon),
          content: contentInput.value.trim(),
          colleges: selectedColleges
        };

        try {
          if (this.editingEssayId) {
            await API.updateEssay(this.editingEssayId, payload);
            if (window.app?.showToast) {
              window.app.showToast('Essay updated successfully!', 'success');
            }
          } else {
            await API.createEssay(payload);
            if (window.app?.showToast) {
              window.app.showToast('Essay created successfully!', 'success');
            }
          }
          if (isCommon) {
            try {
              await API.toggleRequirementAll('Common App Main Essay', payload.draft_status === 'Final');
            } catch (err) {}
          }
          closeModal();
          this.render(container, state, { silent: true });
        } catch (err) {
          console.error('Failed to save essay', err);
          if (window.app?.showToast) {
            window.app.showToast(err.message || 'Failed to save essay', 'error');
          }
        }
      });
    }
  }
};
