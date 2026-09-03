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
}

export const API = new ApiClient();
if (typeof window !== 'undefined') {
  window.API = API;
}

