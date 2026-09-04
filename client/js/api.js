/**
 * College Portfolio — Client API Wrapper
 * Handles all async communication with backend REST endpoints at /api/*
 * Includes credential / cookie propagation, typed error handling, and offline resilience.
 */

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

class ApiClient {
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
  }

  /**
   * Core fetch handler with JSON parsing and standardized error handling.
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    const config = {
      ...options,
      credentials: 'same-origin', // Ensure first-party cookie college_portfolio_id is sent/received
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    // If body is empty for GET / HEAD, remove headers
    if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);

      // Handle 204 No Content
      if (response.status === 204) {
        return { success: true };
      }

      // Check Content-Type
      const contentType = response.headers.get('content-type') || '';
      let data = null;

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMsg = data?.message || data?.error || data?.detail || `API Request failed with status ${response.status}`;
        throw new ApiError(errorMsg, response.status, data);
      }

      return data;
    } catch (err) {
      if (err instanceof ApiError) {
        throw err;
      }
      // Network or parsing errors
      throw new ApiError(err.message || 'Network connection failure', 0, null);
    }
  }

  // ==========================================
  // Health & System
  // ==========================================
  async getHealth() {
    return this.request('/health');
  }

  // ==========================================
  // College Discovery & Profile
  // ==========================================
  /**
   * Search and filter colleges
   * @param {Object} params - { q, state, type, max_net_price, min_admit_rate, max_admit_rate, limit, offset, sort }
   */
  async getColleges(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val);
      }
    });
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/colleges${queryString}`);
  }

  /**
   * Search colleges (alias for getColleges)
   * @param {Object} params - { q, state, type, max_net_price, min_admit_rate, max_admit_rate, limit, offset, sort }
   */
  async searchColleges(params = {}) {
    return this.getColleges(params);
  }


  /**
   * Get single college detailed profile
   * @param {string} id - College UnitID or slug
   * @param {boolean} calculateFit - Whether to calculate student fit score
   */
  async getCollege(id, calculateFit = true) {
    return this.request(`/colleges/${encodeURIComponent(id)}?calculate_fit=${calculateFit}`);
  }

  /**
   * Trigger AI enrichment refresh for college
   * @param {string} id - College UnitID or slug
   * @param {boolean} force - Force refresh even if cached
   */
  async refreshCollege(id, force = false) {
    return this.request(`/colleges/${encodeURIComponent(id)}/refresh`, {
      method: 'POST',
      body: { force }
    });
  }

  // ==========================================
  // Cookie-Based Guest Portfolio
  // ==========================================
  /**
   * Get current student portfolio (items, summary, preferences, fit weights)
   */
  async getPortfolio() {
    return this.request('/portfolio');
  }

  /**
   * Save a college to portfolio
   * @param {string} collegeId - UnitID of college
   * @param {string} userNote - Optional student note
   */
  async saveCollege(collegeId, userNote = '') {
    return this.request('/portfolio/colleges', {
      method: 'POST',
      body: {
        college_id: String(collegeId),
        user_note: userNote
      }
    });
  }

  /**
   * Remove a college from portfolio
   * @param {string} collegeId - UnitID of college
   */
  async removeSavedCollege(collegeId) {
    return this.request(`/portfolio/colleges/${encodeURIComponent(collegeId)}`, {
      method: 'DELETE'
    });
  }

  /**
   * Update student preferences and fit weights
   * @param {Object} preferences - { gpa, sat, act, annual_budget, target_state, preferred_majors }
   * @param {Object} fitWeights - 8 dimension weights
   */
  async updatePreferences(preferences = {}, fitWeights = {}) {
    return this.request('/portfolio/preferences', {
      method: 'PUT',
      body: {
        preferences,
        fit_weights: fitWeights
      }
    });
  }

  /**
   * Clear all saved colleges in portfolio
   */
  async clearPortfolio() {
    return this.request('/portfolio', {
      method: 'DELETE'
    });
  }

  /**
   * Update application tracker for a saved college
   * @param {string} collegeId - UnitID of college
   * @param {Object} trackerData - Application milestones, plan, checklists, deadlines, decision
   */
  async updateApplicationTracker(collegeId, trackerData = {}) {
    return this.request(`/portfolio/colleges/${encodeURIComponent(collegeId)}/tracker`, {
      method: 'PUT',
      body: trackerData
    });
  }

  /**
   * Bulk update application milestones for ALL saved colleges
   * @param {Object} trackerData - Application milestones (e.g. { transcripts_submitted: true })
   */
  async bulkUpdateApplicationTracker(trackerData = {}) {
    return this.request('/portfolio/tracker/bulk', {
      method: 'PUT',
      body: trackerData
    });
  }

  /**
   * Reset application milestones across ALL saved colleges
   */
  async resetApplicationTracker() {
    return this.request('/portfolio/tracker/reset', {
      method: 'POST'
    });
  }



  // ==========================================
  // Multi-College Comparison
  // ==========================================
  /**
   * Compare 2 to 6 colleges side-by-side
   * @param {Array<string>} collegeIds - Array of 2 to 6 college UnitIDs
   */
  async compareColleges(collegeIds = []) {
    if (!collegeIds || collegeIds.length === 0) {
      throw new ApiError('Please select at least 2 colleges to compare', 400);
    }
    const idsString = collegeIds.map(encodeURIComponent).join(',');
    return this.request(`/compare?ids=${idsString}`);
  }

  // ==========================================
  // Knowledge Ledger & Audit
  // ==========================================
  /**
   * Get audit history for a specific college
   * @param {string} collegeId - UnitID or slug
   */
  async getKnowledgeAudit(collegeId) {
    return this.request(`/knowledge/colleges/${encodeURIComponent(collegeId)}`);
  }

  /**
   * Export knowledge ledger file URL
   * @param {string} format - 'md' or 'jsonl'
   */
  getKnowledgeExportUrl(format = 'md') {
    return `${this.baseUrl}/knowledge/export?format=${encodeURIComponent(format)}`;
  }
  /**
   * Record page visit (increment unique hit counter)
   */
  async recordVisit() {
    return this.request('/stats/visit', { method: 'POST' });
  }

  // ==========================================
  // R1: Financial Aid Offer Comparison
  // ==========================================
  /**
   * Get side-by-side financial aid comparison across saved colleges
   */
  async getAidComparison() {
    return this.request('/portfolio/aid/comparison');
  }

  /**
   * Save or update financial aid offer for a college
   * @param {string} collegeId - College UnitID
   * @param {Object} aidData - Financial aid offer details
   */
  async saveAidOffer(collegeId, aidData) {
    return this.request(`/portfolio/aid/${encodeURIComponent(collegeId)}`, {
      method: 'POST',
      body: aidData
    });
  }

  /**
   * Delete financial aid offer for a college
   * @param {string} collegeId - College UnitID
   */
  async deleteAidOffer(collegeId) {
    return this.request(`/portfolio/aid/${encodeURIComponent(collegeId)}`, {
      method: 'DELETE'
    });
  }

  // ==========================================
  // R2: Deadline Calendar
  // ==========================================
  /**
   * Get aggregated deadlines across all saved colleges plus 14-day upcoming list
   */
  async getCalendar() {
    return this.request('/portfolio/calendar');
  }

  // ==========================================
  // R3: Essay Tracker
  // ==========================================
  /**
   * List all essay entries in the student's portfolio
   */
  async getEssays() {
    return this.request('/portfolio/essays');
  }

  /**
   * Create a new essay entry
   * @param {Object} essayData - Essay payload
   */
  async createEssay(essayData) {
    return this.request('/portfolio/essays', {
      method: 'POST',
      body: essayData
    });
  }

  /**
   * Update an existing essay entry
   * @param {string} essayId - Essay ID
   * @param {Object} essayData - Updated essay payload
   */
  async updateEssay(essayId, essayData) {
    return this.request(`/portfolio/essays/${encodeURIComponent(essayId)}`, {
      method: 'PUT',
      body: essayData
    });
  }

  /**
   * Delete an essay entry
   * @param {string} essayId - Essay ID
   */
  async deleteEssay(essayId) {
    return this.request(`/portfolio/essays/${encodeURIComponent(essayId)}`, {
      method: 'DELETE'
    });
  }

  // ==========================================
  // R4: Admissions Chances Estimator
  // ==========================================
  /**
   * Get admissions chances evaluation for a single college
   * @param {string} collegeId - College UnitID
   * @param {Object} params - Optional { gpa, sat, act } overrides
   */
  async getCollegeChances(collegeId, params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val);
      }
    });
    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/colleges/${encodeURIComponent(collegeId)}/chances${queryString}`);
  }

  /**
   * Get admissions chances evaluation across all saved colleges
   */
  async getPortfolioChances() {
    return this.request('/portfolio/chances');
  }

  // ==========================================
  // R5: "What-If" Scenario Modeling
  // ==========================================
  /**
   * Run in-memory what-if scenario simulation without persisting changes
   * @param {Object} payload - Scenario overrides { college_id, hypothetical_major, is_in_state, annual_aid_amount, budget_max_annual, gpa, sat_score, act_score }
   */
  async simulateScenario(payload) {
    return this.request('/portfolio/scenario', {
      method: 'POST',
      body: payload
    });
  }

  // ==========================================
  // R6: Alumni Outcomes Deep Dive
  // ==========================================
  /**
   * Retrieve Scorecard field-of-study earnings by major for a college
   * @param {string} collegeId - College UnitID
   */
  async getCollegeFieldOfStudy(collegeId) {
    return this.request(`/colleges/${encodeURIComponent(collegeId)}/field-of-study`);
  }

  // ==========================================
  // R7: Per-School Requirements Checklist
  // ==========================================
  /**
   * Get requirements checklist for a specific college
   * @param {string} collegeId - College UnitID
   */
  async getCollegeChecklist(collegeId) {
    return this.request(`/portfolio/tracker/${encodeURIComponent(collegeId)}/checklist`);
  }

  /**
   * Add a checklist item to a saved college
   * @param {string} collegeId - College UnitID
   * @param {Object} itemData - Checklist item { name, required, completed, deadline, notes }
   */
  async addChecklistItem(collegeId, itemData) {
    return this.request(`/portfolio/tracker/${encodeURIComponent(collegeId)}/checklist`, {
      method: 'POST',
      body: itemData
    });
  }

  /**
   * Update or toggle a checklist item
   * @param {string} collegeId - College UnitID
   * @param {string} itemId - Checklist item ID
   * @param {Object} itemData - Updated properties
   */
  async updateChecklistItem(collegeId, itemId, itemData) {
    return this.request(`/portfolio/tracker/${encodeURIComponent(collegeId)}/checklist/${encodeURIComponent(itemId)}`, {
      method: 'PUT',
      body: itemData
    });
  }

  /**
   * Delete a checklist item
   * @param {string} collegeId - College UnitID
   * @param {string} itemId - Checklist item ID
   */
  async deleteChecklistItem(collegeId, itemId) {
    return this.request(`/portfolio/tracker/${encodeURIComponent(collegeId)}/checklist/${encodeURIComponent(itemId)}`, {
      method: 'DELETE'
    });
  }

  /**
   * Get cross-school requirement checklist matrix
   */
  async getRequirementsMatrix() {
    return this.request('/portfolio/requirements-matrix');
  }

  /**
   * Mark a requirement as done (or incomplete) across all saved colleges in one click
   * @param {string} requirementName - Requirement name
   * @param {boolean|null} completed - Target status (true = done, false = needed, null = auto-toggle)
   */
  async toggleRequirementAll(requirementName, completed = null) {
    return this.request('/portfolio/requirements-matrix/toggle-all', {
      method: 'POST',
      body: { requirement_name: requirementName, completed },
    });
  }

  /**
   * Mark all requirements across all saved colleges as done (or incomplete) in one click
   * @param {boolean} completed - Target status (default true)
   */
  async toggleAllRequirements(completed = true) {
    return this.request('/portfolio/requirements-matrix/toggle-everything', {
      method: 'POST',
      body: { completed },
    });
  }

  /**
   * Mark all requirements for a single college as done (or incomplete) in one click
   * @param {string} collegeId - College UnitID
   * @param {boolean} completed - Target status (default true)
   */
  async toggleCollegeChecklistAll(collegeId, completed = true) {
    return this.request(`/portfolio/tracker/${encodeURIComponent(collegeId)}/checklist/bulk`, {
      method: 'POST',
      body: { completed },
    });
  }
}

export const API = new ApiClient();
if (typeof window !== 'undefined') {
  window.API = API;
  window.API_VERSION = '4.0';
  console.log('[College Portfolio] API Client v4.0 loaded with', Object.getOwnPropertyNames(Object.getPrototypeOf(API)).filter(m => m !== 'constructor').length, 'methods');
}

