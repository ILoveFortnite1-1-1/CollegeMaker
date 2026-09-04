/**
 * College Portfolio — Main SPA Application Entrypoint
 * Manages client-side routing, global state, toast notifications, guest cookie sync, and UI lifecycles.
 */
import { API } from './api.js?v=4.0';
import { DashboardPage } from './pages/dashboard.js';
import { DiscoveryPage } from './pages/discovery.js';
import { ProfilePage } from './pages/profile.js';
import { ComparePage } from './pages/compare.js';
import { TrackerPage } from './pages/tracker.js';
import { SettingsPage } from './pages/settings.js';
import { AidComparisonPage } from './pages/aid-comparison.js';
import { CalendarPage } from './pages/calendar.js';
import { EssaysPage } from './pages/essays.js';
import { WhatIfPage } from './pages/what-if.js';
import { ProvenanceDrawer } from './components/provenance-drawer.js';
import { SavedModal } from './components/saved-modal.js';


class CollegePortfolioApp {
  constructor() {
    this.state = {
      currentRoute: 'dashboard',
      routeParams: {},
      portfolio: null,
      compareList: this.loadCompareList(),
      cookieBlocked: !navigator.cookieEnabled
    };

    this.routes = {
      '': DashboardPage,
      'dashboard': DashboardPage,
      'colleges': DiscoveryPage,
      'compare': ComparePage,
      'tracker': TrackerPage,
      'settings': SettingsPage,
      'aid': AidComparisonPage,
      'aid-comparison': AidComparisonPage,
      'calendar': CalendarPage,
      'deadlines': CalendarPage,
      'essays': EssaysPage,
      'what-if': WhatIfPage,
      'scenario': WhatIfPage
    };
  }

  async init() {
    console.log('Initializing College Portfolio SPA...');


    // Initialize drawer & modals
    ProvenanceDrawer.init();

    // Check cookie support
    this.checkCookieHealth();

    // Attach global event listeners
    this.bindGlobalEvents();

    // Fetch initial portfolio in background
    try {
      const p = await API.getPortfolio();
      this.setPortfolio(p);
      this.updatePortfolioIndicators();
    } catch (err) {
      console.warn('Initial portfolio sync notice:', err.message);
    }

    // Record visitor page load hit
    this.recordPageVisit();

    // Initialize routing
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute();
  }

  /**
   * Record page visit hit and update visitor counter in footer
   */
  async recordPageVisit() {
    try {
      const res = await API.recordVisit();
      const countEl = document.getElementById('visitor-count-num');
      if (countEl && res.total_visits) {
        countEl.textContent = res.total_visits.toLocaleString();
      }
    } catch (err) {
      console.warn('Visit count record notice:', err.message);
    }
  }


  /**
   * Parse current hash route and render the appropriate page component
   */
  async handleRoute() {
    const rawHash = window.location.hash.slice(1).replace(/^\//, '');
    const segments = rawHash.split('/');
    const rootRoute = segments[0] || '';
    const param = segments[1] || null;

    const appRoot = document.getElementById('app-root');
    if (!appRoot) return;

    // Scroll to top
    window.scrollTo(0, 0);

    // Update active nav indicators
    this.updateActiveNav(rootRoute || 'dashboard');

    // Handle Profile Route /colleges/:id
    if (rootRoute === 'colleges' && param) {
      this.state.currentRoute = 'profile';
      this.state.routeParams = { collegeId: param };
      await ProfilePage.render(appRoot, this.state, param);
      return;
    }

    // Standard Routes
    const pageHandler = this.routes[rootRoute] || DashboardPage;
    this.state.currentRoute = rootRoute || 'dashboard';
    this.state.routeParams = {};

    await pageHandler.render(appRoot, this.state);
  }

  /**
   * Update navigation bar active states and compare count pill
   */
  updateActiveNav(activeName) {
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {
      const linkRoute = link.getAttribute('data-route');
      if (linkRoute === activeName || (activeName === '' && linkRoute === 'dashboard')) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Close mobile drawer if open
    this.closeMobileNav();

    // Update compare pill
    const compareBadge = document.getElementById('compare-count-badge');
    if (compareBadge) {
      compareBadge.textContent = this.state.compareList.length;
    }
  }

  /**
   * Safe access to saved colleges array across all response shapes
   */
  getSavedColleges() {
    const p = this.state.portfolio;
    if (!p) return [];
    if (Array.isArray(p.saved_colleges)) return p.saved_colleges;
    if (Array.isArray(p.colleges)) return p.colleges;
    if (Array.isArray(p.items)) return p.items;
    if (p.portfolio && Array.isArray(p.portfolio.colleges)) return p.portfolio.colleges;
    return [];
  }

  /**
   * Set and normalize portfolio state
   */
  setPortfolio(data) {
    if (!data) {
      this.state.portfolio = null;
      return;
    }
    const colleges = data.saved_colleges || data.colleges || data.items || (data.portfolio && data.portfolio.colleges) || [];
    this.state.portfolio = {
      ...data,
      saved_colleges: colleges,
      colleges: colleges,
      items: colleges
    };
  }

  /**
   * Update header saved portfolio counter badge
   */
  updatePortfolioIndicators() {
    const savedCountLabel = document.getElementById('saved-count-label');
    const savedColleges = this.getSavedColleges();
    if (savedCountLabel) {
      savedCountLabel.textContent = `${savedColleges.length} Saved`;
    }

    const compareBadge = document.getElementById('compare-count-badge');
    if (compareBadge) {
      compareBadge.textContent = this.state.compareList.length;
    }
  }

  /**
   * Cookie health & blocked detection
   */
  checkCookieHealth() {
    const banner = document.getElementById('cookie-banner');
    const bannerText = document.getElementById('cookie-banner-text');

    if (!banner) return;

    if (this.state.cookieBlocked) {
      banner.classList.add('warning-banner');
      banner.classList.remove('hidden');
      if (bannerText) {
        bannerText.innerHTML = '⚠️ <strong>Cookies are disabled in your browser.</strong> Your saved portfolio will only persist in temporary memory during this session.';
      }
    } else {
      const dismissed = localStorage.getItem('cp_cookie_dismissed');
      if (!dismissed) {
        banner.classList.remove('hidden');
      }
    }

    document.getElementById('dismiss-cookie-banner')?.addEventListener('click', () => {
      banner.classList.add('hidden');
      localStorage.setItem('cp_cookie_dismissed', 'true');
    });
  }

  /**
   * Global event delegations (Save, Compare, Mobile Menu)
   */
  bindGlobalEvents() {
    // Mobile navigation toggle
    const menuToggle = document.getElementById('menu-toggle');
    const mobileNav = document.getElementById('mobile-nav');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    const closeBtn = document.getElementById('mobile-nav-close');

    menuToggle?.addEventListener('click', () => {
      mobileNav?.classList.add('open');
      backdrop?.classList.add('open');
      backdrop?.style.setProperty('display', 'block');
    });

    const closeMenu = () => {
      mobileNav?.classList.remove('open');
      backdrop?.classList.remove('open');
      backdrop?.style.setProperty('display', 'none');
    };

    closeBtn?.addEventListener('click', closeMenu);
    backdrop?.addEventListener('click', closeMenu);

    // Header Saved Portfolio Pill Click -> Open Saved Modal
    const savedPill = document.getElementById('saved-portfolio-pill');
    const savedLabel = document.getElementById('saved-count-label');
    [savedPill, savedLabel].forEach(el => {
      if (el) {
        el.style.cursor = 'pointer';
        el.addEventListener('click', (e) => {
          e.preventDefault();
          SavedModal.open();
        });
      }
    });

    // Global Action Delegation for Toggle Save

    document.addEventListener('click', async (e) => {
      const saveBtn = e.target.closest('[data-action="toggle-save"]');
      if (saveBtn) {
        e.preventDefault();
        const collegeId = saveBtn.getAttribute('data-college-id');
        if (!collegeId) return;

        const savedList = this.getSavedColleges();
        const isCurrentlySaved = savedList.some(
          c => String(c.college_id || c.id) === String(collegeId)
        );

        saveBtn.disabled = true;

        try {
          if (isCurrentlySaved) {
            const updated = await API.removeSavedCollege(collegeId);
            this.setPortfolio(updated);
            this.showToast('Removed from your saved portfolio.', 'info');
          } else {
            const updated = await API.saveCollege(collegeId);
            this.setPortfolio(updated);
            this.showToast('Saved to your college portfolio!', 'success');
          }

          this.updatePortfolioIndicators();

          // Smoothly update save buttons across the current page without jarring reloads
          const newlySaved = !isCurrentlySaved;
          document.querySelectorAll(`[data-action="toggle-save"][data-college-id="${collegeId}"]`).forEach(btn => {
            if (btn.classList.contains('btn-save')) {
              btn.classList.toggle('saved', newlySaved);
              btn.setAttribute('aria-label', newlySaved ? 'Remove from portfolio' : 'Save to portfolio');
              btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="${newlySaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2.5" style="display: inline-block; vertical-align: middle; margin-right: 3px;"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg><span>${newlySaved ? 'Saved' : 'Save'}</span>`;
            } else {
              btn.className = `btn ${newlySaved ? 'btn-primary' : 'btn-secondary'}`;
              btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="${newlySaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2.5" style="display: inline-block; vertical-align: middle; margin-right: 4px;"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg><span>${newlySaved ? 'Saved to Portfolio' : 'Save College'}</span>`;
            }
          });

          // If on dashboard, update saved institutions list & charts silently in-place without reloading route or scrolling
          if (this.state.currentRoute === 'dashboard' || this.state.currentRoute === '') {
            const appRoot = document.getElementById('app-root');
            if (appRoot) {
              const currentScrollY = window.scrollY;
              await DashboardPage.render(appRoot, this.state, { silent: true });
              window.scrollTo({ top: currentScrollY, behavior: 'instant' });
            }
          }

        } catch (err) {
          this.showToast(`Error updating portfolio: ${err.message}`, 'error');
        } finally {
          saveBtn.disabled = false;
        }
        return;
      }

      // Global Action Delegation for Toggle Compare Button
      const compareBtn = e.target.closest('[data-action="toggle-compare"]');
      if (compareBtn) {
        e.preventDefault();
        const collegeId = String(compareBtn.getAttribute('data-college-id'));
        this.toggleCompareId(collegeId);
        this.handleRoute();
        return;
      }
    });

    // Delegate Checkbox for Compare
    document.addEventListener('change', (e) => {
      if (e.target.classList.contains('compare-checkbox')) {
        const collegeId = String(e.target.getAttribute('data-college-id'));
        this.toggleCompareId(collegeId);
      }
    });
  }

  toggleCompareId(collegeId) {
    if (this.state.compareList.includes(collegeId)) {
      this.state.compareList = this.state.compareList.filter(id => id !== collegeId);
      this.showToast('Removed from comparison list.', 'info');
    } else {
      if (this.state.compareList.length >= 6) {
        this.showToast('Comparison limit reached (max 6 colleges).', 'warning');
        return;
      }
      this.state.compareList.push(collegeId);
      this.showToast('Added to comparison matrix!', 'success');
    }

    this.saveCompareList(this.state.compareList);
    this.updatePortfolioIndicators();
  }

  loadCompareList() {
    try {
      const stored = localStorage.getItem('cp_compare_list');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  saveCompareList(list) {
    try {
      localStorage.setItem('cp_compare_list', JSON.stringify(list));
    } catch (e) {
      console.warn('Could not save compare list to local storage', e);
    }
  }

  closeMobileNav() {
    const mobileNav = document.getElementById('mobile-nav');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    mobileNav?.classList.remove('open');
    backdrop?.classList.remove('open');
    if (backdrop) backdrop.style.display = 'none';
  }

  /**
   * Toast notification system
   */
  showToast(message, type = 'info', duration = 3200) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    // Cap active notifications on screen at once to at most 2
    while (container.children.length >= 2) {
      const oldest = container.firstElementChild;
      if (oldest) oldest.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `
      <span>${icon}</span>
      <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.transition = 'opacity 0.3s, transform 0.3s';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(100%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

// Global App Singleton & Bootstrap
window.app = new CollegePortfolioApp();
document.addEventListener('DOMContentLoaded', () => {
  window.app.init();
});
