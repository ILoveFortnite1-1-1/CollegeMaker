/**
 * College Application Tracker Page (Route: #/tracker)
 * Based on the Application Tracker Template spreadsheet.
 * Allows students to track application plans, deadlines, requirements, and decisions.
 */
import { API } from '../api.js';
import { getCollegeImageUrl, getCampusSvgDataUri } from '../utils/college-images.js';

export const TrackerPage = {


  async render(container, state) {
    container.innerHTML = `
      <div class="loading-screen">
        <div class="spinner"></div>
        <p class="loading-text">Loading application tracker…</p>
      </div>
    `;

    try {
      const portfolioData = await API.getPortfolio();
      if (window.app?.setPortfolio) {
        window.app.setPortfolio(portfolioData);
      } else {
        state.portfolio = portfolioData;
      }

      const savedColleges = portfolioData.saved_colleges || portfolioData.colleges || portfolioData.items || [];

      if (savedColleges.length === 0) {
        container.innerHTML = `
          <div class="empty-state" style="padding: 60px 20px; text-align: center; max-width: 600px; margin: 0 auto;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 16px; background: #eff6ff; color: #2563eb; margin-bottom: 16px;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
            </div>
            <h2 style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-bottom: 8px;">Your Application Tracker is Empty</h2>
            <p style="color: #64748b; margin-bottom: 24px; line-height: 1.5;">
              Save colleges to your portfolio to track deadlines, supplemental essays, transcript submissions, recommendation letters, and admissions decisions in one place.
            </p>
            <a href="#/colleges" class="btn btn-primary">Browse Colleges to Add</a>
          </div>
        `;
        return;
      }

      // Calculate tracker summary stats
      let totalTracked = savedColleges.length;
      let submittedCount = 0;
      let acceptedCount = 0;
      let totalMilestonesCompleted = 0;
      let totalMilestonesPossible = totalTracked * 11;

      savedColleges.forEach(col => {
        const trk = col.tracker || col.application_tracker || {};
        if (trk.application_submitted || trk.status === 'Submitted') submittedCount++;
        if (trk.decision === 'Accepted') acceptedCount++;

        const core = [
          trk.research_completed,
          trk.transcripts_requested,
          trk.transcripts_submitted,
          trk.test_scores_sent,
          trk.essays_completed,
          trk.counselor_rec_requested,
          trk.teacher_rec_requested,
          trk.application_fee_paid,
          trk.application_submitted,
          trk.portal_account_checked,
          trk.financial_aid_submitted
        ];
        totalMilestonesCompleted += core.filter(Boolean).length;
      });

      const overallProgress = totalMilestonesPossible > 0 ? Math.round((totalMilestonesCompleted / totalMilestonesPossible) * 100) : 0;

      container.innerHTML = `
        <div class="tracker-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 28px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #2563eb;">Admissions Roadmap</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: #0f172a; margin: 4px 0;">College Application Tracker</h1>
              <p style="color: #64748b; margin: 0; font-size: 0.95rem;">Track deadlines, requirements, essays, and decisions across all ${totalTracked} saved schools.</p>
            </div>
            <div style="display: flex; gap: 10px;">
              <a href="#/colleges" class="btn btn-secondary btn-sm">+ Add More Schools</a>
            </div>
          </div>

          <!-- Top Stats Strip -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px;">
            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.8125rem; font-weight: 600; color: #64748b;">Applications Tracked</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
              </div>
              <div style="font-size: 1.75rem; font-weight: 800; color: #0f172a;">${totalTracked} Schools</div>
              <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">In your portfolio list</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.8125rem; font-weight: 600; color: #64748b;">Overall Completion</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
              </div>
              <div style="display: flex; align-items: baseline; gap: 8px;">
                <span style="font-size: 1.75rem; font-weight: 800; color: #2563eb;">${overallProgress}%</span>
                <span style="font-size: 0.8125rem; color: #64748b;">(${totalMilestonesCompleted}/${totalMilestonesPossible} items)</span>
              </div>
              <div style="width: 100%; height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; margin-top: 8px;">
                <div style="width: ${overallProgress}%; height: 100%; background: #2563eb; border-radius: 9999px;"></div>
              </div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.8125rem; font-weight: 600; color: #64748b;">Submitted</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <div style="font-size: 1.75rem; font-weight: 800; color: #059669;">${submittedCount} <span style="font-size: 1rem; font-weight: 500; color: #64748b;">of ${totalTracked}</span></div>
              <div style="font-size: 0.75rem; color: #059669; margin-top: 4px;">${totalTracked - submittedCount} in progress</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.8125rem; font-weight: 600; color: #64748b;">Decisions Received</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              </div>
              <div style="font-size: 1.75rem; font-weight: 800; color: #7c3aed;">${acceptedCount > 0 ? `${acceptedCount} Accepted` : 'Pending'}</div>
              <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">Record outcomes as they arrive</div>
            </div>
          </div>


          <!-- Application Cards / Table List -->
          <div style="display: flex; flex-direction: column; gap: 20px;" id="tracker-colleges-list">
            ${savedColleges.map((col, idx) => this.renderCollegeTrackerCard(col, idx)).join('')}
          </div>
        </div>
      `;

      this.bindEvents(container, state);
    } catch (err) {
      container.innerHTML = `
        <div class="error-banner" style="margin: 40px auto; max-width: 600px; padding: 24px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px;">
          <h3 style="color: #991b1b; margin-top: 0;">Error Loading Tracker</h3>
          <p style="color: #b91c1c;">${err.message}</p>
          <a href="#/" class="btn btn-primary">Return to Dashboard</a>
        </div>
      `;
    }
  },

  renderCollegeTrackerCard(college, idx) {
    const cid = String(college.college_id || college.id);
    const cname = college.college_name || college.canonical_name || college.name;
    const cat = college.category || college.fit_category || college.tag || 'Target';
    const loc = college.location || '';
    const tracker = college.tracker || college.application_tracker || {};

    const plan = tracker.plan || 'Regular Decision';
    const status = tracker.status || 'Not Started';
    const decision = tracker.decision || 'Pending';
    const priorityDeadline = tracker.priority_deadline || 'Nov 1, 2025';
    const regularDeadline = tracker.regular_deadline || 'Jan 1, 2026';
    const completionPct = tracker.completion_percentage ?? 0;

    let catBadgeClass = 'tag-target';
    if (cat === 'Reach') catBadgeClass = 'tag-reach';
    if (cat === 'Likely') catBadgeClass = 'tag-likely';

    return `
      <div class="tracker-college-card" data-college-id="${cid}" style="background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <!-- Top bar -->
        <div style="padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; background: #f8fafc; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; gap: 12px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <img src="${getCollegeImageUrl(college, 'card')}" alt="${cname}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; flex-shrink: 0; background: #0f172a;" onerror="this.onerror=null; this.src='${getCampusSvgDataUri(cname, cid)}';" />
            <div>

              <div style="display: flex; align-items: center; gap: 8px;">
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #0f172a;">
                  <a href="#/colleges/${cid}" style="color: inherit; text-decoration: none;">${cname}</a>
                </h3>
                <span class="category-tag ${catBadgeClass}">${cat}</span>
              </div>
              <div style="font-size: 0.8125rem; color: #64748b; margin-top: 2px;">${loc}</div>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 16px;">
            <div style="text-align: right;">
              <div style="font-size: 0.75rem; color: #64748b; font-weight: 500;">Application Progress</div>
              <div style="font-size: 1.1rem; font-weight: 800; color: ${completionPct >= 100 ? '#10b981' : '#2563eb'};">
                ${completionPct}% Done
              </div>
            </div>
            <div style="width: 80px; height: 8px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
              <div style="width: ${completionPct}%; height: 100%; background: ${completionPct >= 100 ? '#10b981' : '#2563eb'}; border-radius: 9999px;"></div>
            </div>
            <button type="button" class="btn btn-sm btn-secondary toggle-details-btn" data-college-id="${cid}" style="padding: 6px 12px;">
              Checklist & Deadlines ▾
            </button>
          </div>
        </div>

        <!-- Plan & Deadlines Quick Row -->
        <div style="padding: 12px 20px; display: flex; align-items: center; gap: 20px; font-size: 0.8125rem; flex-wrap: wrap; background: #fff; border-bottom: 1px dashed #e2e8f0;">
          <div>
            <span style="color: #64748b;">Plan:</span>
            <select class="tracker-input-plan" data-college-id="${cid}" style="margin-left: 6px; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.8125rem; font-weight: 600; color: #0f172a;">
              <option value="Regular Decision" ${plan === 'Regular Decision' ? 'selected' : ''}>Regular Decision</option>
              <option value="Early Action" ${plan === 'Early Action' ? 'selected' : ''}>Early Action</option>
              <option value="Early Decision" ${plan === 'Early Decision' ? 'selected' : ''}>Early Decision</option>
              <option value="Rolling Admissions" ${plan === 'Rolling Admissions' ? 'selected' : ''}>Rolling Admissions</option>
            </select>
          </div>

          <div>
            <span style="color: #64748b;">Priority Deadline:</span>
            <input type="text" class="tracker-input-deadline" data-college-id="${cid}" data-field="priority_deadline" value="${priorityDeadline}" style="margin-left: 6px; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.8125rem; width: 110px;" />
          </div>

          <div>
            <span style="color: #64748b;">Regular Deadline:</span>
            <input type="text" class="tracker-input-deadline" data-college-id="${cid}" data-field="regular_deadline" value="${regularDeadline}" style="margin-left: 6px; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.8125rem; width: 110px;" />
          </div>

          <div>
            <span style="color: #64748b;">Decision:</span>
            <select class="tracker-input-decision" data-college-id="${cid}" style="margin-left: 6px; padding: 2px 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.8125rem; font-weight: 600; color: #0f172a;">
              <option value="Pending" ${decision === 'Pending' ? 'selected' : ''}>Pending</option>
              <option value="Accepted" ${decision === 'Accepted' ? 'selected' : ''}>Accepted</option>
              <option value="Deferred" ${decision === 'Deferred' ? 'selected' : ''}>Deferred</option>
              <option value="Waitlisted" ${decision === 'Waitlisted' ? 'selected' : ''}>Waitlisted</option>
              <option value="Denied" ${decision === 'Denied' ? 'selected' : ''}>Denied</option>
            </select>
          </div>
        </div>

        <!-- Checklist Details (Collapsible) -->
        <div class="tracker-checklist-panel" id="checklist-${cid}" style="padding: 20px; background: #fdfdfe; border-top: 1px solid #e2e8f0; display: block;">
          <h4 style="margin: 0 0 14px 0; font-size: 0.875rem; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.05em;">
            Application Milestones Checklist
          </h4>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px;">
            ${this.renderCheckItem(cid, 'research_completed', 'Research college website & academic majors', tracker.research_completed)}
            ${this.renderCheckItem(cid, 'transcripts_requested', 'Request high school transcript', tracker.transcripts_requested)}
            ${this.renderCheckItem(cid, 'transcripts_submitted', 'Official transcript sent & verified', tracker.transcripts_submitted)}
            ${this.renderCheckItem(cid, 'test_scores_sent', 'Official SAT / ACT test scores sent', tracker.test_scores_sent)}
            ${this.renderCheckItem(cid, 'essays_completed', 'Supplemental essays written & polished', tracker.essays_completed)}
            ${this.renderCheckItem(cid, 'counselor_rec_requested', 'Counselor letter of recommendation', tracker.counselor_rec_requested)}
            ${this.renderCheckItem(cid, 'teacher_rec_requested', 'Teacher recommendation letters sent', tracker.teacher_rec_requested)}
            ${this.renderCheckItem(cid, 'application_fee_paid', 'Application fee paid or fee waiver verified', tracker.application_fee_paid)}
            ${this.renderCheckItem(cid, 'application_submitted', 'Application officially submitted', tracker.application_submitted)}
            ${this.renderCheckItem(cid, 'portal_account_checked', 'Check college portal for all received docs', tracker.portal_account_checked)}
            ${this.renderCheckItem(cid, 'financial_aid_submitted', 'FAFSA & CSS Profile / Financial Aid sent', tracker.financial_aid_submitted)}
          </div>

          <div style="margin-top: 14px; padding-top: 12px; border-top: 1px dashed #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; flex: 1; min-width: 250px;">
              <span style="font-size: 0.8125rem; color: #64748b; font-weight: 500;">Notes / Scholarship Deadlines:</span>
              <input type="text" class="tracker-input-notes" data-college-id="${cid}" value="${tracker.notes || ''}" placeholder="e.g. Merit scholarship deadline Dec 1..." style="flex: 1; padding: 4px 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.8125rem;" />
            </div>
            <a href="#/colleges/${cid}" class="btn btn-sm btn-secondary" style="font-size: 0.75rem;">View Full Profile</a>
          </div>
        </div>
      </div>
    `;
  },

  renderCheckItem(cid, field, label, checked) {
    return `
      <label style="display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; color: ${checked ? '#0f172a' : '#475569'}; background: ${checked ? '#f0fdf4' : '#fff'}; padding: 8px 10px; border-radius: 6px; border: 1px solid ${checked ? '#bbf7d0' : '#e2e8f0'}; cursor: pointer; transition: all 0.2s;">
        <input 
          type="checkbox" 
          class="tracker-checkbox" 
          data-college-id="${cid}" 
          data-field="${field}" 
          ${checked ? 'checked' : ''}
          style="accent-color: #10b981; width: 16px; height: 16px;"
        />
        <span style="${checked ? 'font-weight: 600; text-decoration: none;' : ''}">${label}</span>
      </label>
    `;
  },

  bindEvents(container, state) {
    // Checkbox toggles
    container.querySelectorAll('.tracker-checkbox').forEach(cb => {
      cb.addEventListener('change', async (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const field = e.target.getAttribute('data-field');
        const isChecked = e.target.checked;

        try {
          const updated = await API.updateApplicationTracker(cid, { [field]: isChecked });
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          window.app?.showToast('Progress updated!', 'success');
          TrackerPage.render(container, state);
        } catch (err) {
          window.app?.showToast(`Update error: ${err.message}`, 'error');
        }
      });
    });

    // Plan dropdown
    container.querySelectorAll('.tracker-input-plan').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const val = e.target.value;
        try {
          const updated = await API.updateApplicationTracker(cid, { plan: val });
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          window.app?.showToast(`Application plan set to ${val}`, 'success');
        } catch (err) {
          window.app?.showToast(`Error: ${err.message}`, 'error');
        }
      });
    });

    // Decision dropdown
    container.querySelectorAll('.tracker-input-decision').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const val = e.target.value;
        try {
          const updated = await API.updateApplicationTracker(cid, { decision: val });
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          window.app?.showToast(`Decision recorded: ${val}!`, 'success');
          TrackerPage.render(container, state);
        } catch (err) {
          window.app?.showToast(`Error: ${err.message}`, 'error');
        }
      });
    });

    // Deadlines inputs
    container.querySelectorAll('.tracker-input-deadline').forEach(input => {
      input.addEventListener('change', async (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const field = e.target.getAttribute('data-field');
        const val = e.target.value;
        try {
          const updated = await API.updateApplicationTracker(cid, { [field]: val });
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          window.app?.showToast('Deadline saved', 'success');
        } catch (err) {
          window.app?.showToast(`Error: ${err.message}`, 'error');
        }
      });
    });

    // Notes inputs
    container.querySelectorAll('.tracker-input-notes').forEach(input => {
      input.addEventListener('change', async (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const val = e.target.value;
        try {
          const updated = await API.updateApplicationTracker(cid, { notes: val });
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          window.app?.showToast('Notes saved', 'success');
        } catch (err) {
          window.app?.showToast(`Error: ${err.message}`, 'error');
        }
      });
    });

    // Collapsible checklist toggles
    container.querySelectorAll('.toggle-details-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const cid = e.target.getAttribute('data-college-id');
        const panel = container.querySelector(`#checklist-${cid}`);
        if (panel) {
          const isHidden = panel.style.display === 'none';
          panel.style.display = isHidden ? 'block' : 'none';
          e.target.textContent = isHidden ? 'Checklist & Deadlines ▾' : 'Checklist & Deadlines ▸';
        }
      });
    });
  }
};
