/**
 * Dashboard Page View (Route: #/)
 * Matches image1.jpg: 5 hero stat cards, Cost vs Early Career Pay scatter plot,
 * Career Outlook donut chart, Rankings leaderboard, and College Application Tracker.
 */
import { API } from '../api.js';
import { renderCollegeCard } from '../components/college-card.js';
import { formatMetricValue } from '../components/metric-card.js';
import { renderScatterChart } from '../components/scatter-chart.js';
import { renderDonutChart } from '../components/donut-chart.js';
import { renderNetPriceBarChart, renderEarningsBarChart, renderGradRateBarChart, renderAdmitRateBarChart } from '../components/bar-chart.js';
import { SavedModal } from '../components/saved-modal.js';


export const DashboardPage = {
  async render(container, state, options = {}) {
    if (!options?.silent) {
      container.innerHTML = `
        <div class="loading-screen">
          <div class="spinner"></div>
          <p class="loading-text">Loading your college portfolio…</p>
        </div>
      `;
    }


    try {
      const [portfolioData, chancesData] = await Promise.all([
        API.getPortfolio(),
        API.getPortfolioChances().catch(() => null)
      ]);

      if (window.app?.setPortfolio) {
        window.app.setPortfolio(portfolioData);
      } else {
        state.portfolio = portfolioData;
      }

      const savedColleges = portfolioData.saved_colleges || portfolioData.colleges || portfolioData.items || [];
      const summary = portfolioData.summary || {
        saved_count: savedColleges.length,
        average_net_price: null,
        average_earnings_10yr: null,
        average_admit_rate: null,
        mix_breakdown: { reach_count: 0, target_count: 0, likely_count: 0 }
      };

      const dist = chancesData?.distribution || {
        Reach: summary.mix_breakdown?.reach_count || 0,
        Target: summary.mix_breakdown?.target_count || 0,
        Likely: summary.mix_breakdown?.likely_count || 0,
        Safety: 0
      };

      // Calculate accurate stats
      let avgPrice = summary.average_net_price;
      let avgEarnings = summary.average_earnings_10yr;
      let avgAdmit = summary.average_admit_rate;

      if (savedColleges.length > 0) {
        const prices = savedColleges.map(c => c.net_price).filter(Boolean);
        if (prices.length) avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;

        const earnings = savedColleges.map(c => c.median_earnings).filter(Boolean);
        if (earnings.length) avgEarnings = earnings.reduce((a, b) => a + b, 0) / earnings.length;

        const admits = savedColleges.map(c => c.admit_rate).filter(Boolean);
        if (admits.length) avgAdmit = admits.reduce((a, b) => a + b, 0) / admits.length;
      }

      // Application tracker statistics
      let appsSubmitted = 0;
      let appMilestonesDone = 0;
      let appMilestonesTotal = savedColleges.length * 11;
      savedColleges.forEach(col => {
        const t = col.tracker || col.application_tracker || {};
        if (t.application_submitted) appsSubmitted++;
        const core = [
          t.research_completed, t.transcripts_requested, t.transcripts_submitted,
          t.test_scores_sent, t.essays_completed, t.counselor_rec_requested,
          t.teacher_rec_requested, t.application_fee_paid, t.application_submitted,
          t.portal_account_checked, t.financial_aid_submitted
        ];
        appMilestonesDone += core.filter(Boolean).length;
      });
      const overallAppProgress = appMilestonesTotal > 0 ? Math.round((appMilestonesDone / appMilestonesTotal) * 100) : 0;

      // Top school for header badge
      const topSchool = savedColleges[0] || null;

      container.innerHTML = `
        <div class="dashboard-container" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          
          <!-- Top Header matching image1.jpg -->
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 500; color: #64748b;">Welcome back!</span>
              <h1 style="font-size: 2.1rem; font-weight: 800; color: #0f172a; margin: 2px 0 6px 0;">Your College Portfolio</h1>
              <div style="font-size: 0.875rem; color: #475569; font-weight: 500;">
                <span id="saved-header-count-link" style="color: #2563eb; font-weight: 700; cursor: pointer; text-decoration: underline;" title="Click to view all saved colleges">${savedColleges.length} saved schools</span> • Flagships & Saved List
              </div>

            </div>

            ${topSchool ? `
              <div style="display: flex; align-items: center; gap: 12px; background: #fff; padding: 10px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="width: 32px; height: 32px; border-radius: 6px; background: #0f172a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem;">
                  ★
                </div>
                <div>
                  <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #2563eb; letter-spacing: 0.04em;">Top Priority</div>
                  <div style="font-size: 0.95rem; font-weight: 700; color: #0f172a;">${topSchool.college_name || topSchool.name}</div>
                </div>
              </div>
            ` : ''}
          </div>

          <!-- 5 Stat Cards Strip matching image1.jpg -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 28px;">
            <!-- Card 1: Schools In List -->
            <div class="stat-card" id="saved-schools-stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #93c5fd; box-shadow: 0 1px 4px rgba(37,99,235,0.08); cursor: pointer; transition: all 0.2s ease;" title="Click to view all saved colleges in detail">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #2563eb;">${savedColleges.length}</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
              </div>
              <div style="font-size: 0.8125rem; font-weight: 700; color: #1e293b;">Saved Schools</div>
              <div style="font-size: 0.75rem; color: #2563eb; font-weight: 600; margin-top: 2px; display: flex; align-items: center; gap: 4px;">
                <span>View List</span> <span style="font-size: 0.85rem;">→</span>
              </div>
            </div>


            <!-- Card 2: Average Net Price -->
            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">${formatMetricValue(avgPrice, 'currency')}</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              </div>
              <div style="font-size: 0.8125rem; font-weight: 600; color: #1e293b;">Average Net Price</div>
              <div style="font-size: 0.75rem; color: #64748b;">(Est. after aid)</div>
            </div>

            <!-- Card 3: Avg Early Career Pay -->
            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">${formatMetricValue(avgEarnings, 'currency')}</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
              </div>
              <div style="font-size: 0.8125rem; font-weight: 600; color: #1e293b;">Avg. 10-Yr Earnings</div>
              <div style="font-size: 0.75rem; color: #64748b;">(Post-grad outcome)</div>
            </div>

            <!-- Card 4: Average Acceptance Rate -->
            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #0f172a;">${formatMetricValue(avgAdmit, 'percent')}</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div style="font-size: 0.8125rem; font-weight: 600; color: #1e293b;">Average Acceptance Rate</div>
              <div style="font-size: 0.75rem; color: #64748b;">Admissions selectivity</div>
            </div>


            <!-- Card 5: Admissions Chances 4-Tier Distribution (Feature R4) -->
            <div class="stat-card" style="background: #fff; padding: 18px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <div style="font-size: 0.8125rem; font-weight: 700; color: #1e293b; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <span>Admissions Chances</span>
                <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 500;">4 Tiers</span>
              </div>
              <div style="display: flex; flex-direction: column; gap: 3px; font-size: 0.75rem;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span style="display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #f59e0b;"></span> Reach
                  </span>
                  <span style="font-weight: 700; color: #0f172a;">${dist.Reach || 0}</span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span style="display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #2563eb;"></span> Target
                  </span>
                  <span style="font-weight: 700; color: #0f172a;">${dist.Target || 0}</span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span style="display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #0d9488;"></span> Likely
                  </span>
                  <span style="font-weight: 700; color: #0f172a;">${dist.Likely || 0}</span>
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span style="display: flex; align-items: center; gap: 6px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #16a34a;"></span> Safety
                  </span>
                  <span style="font-weight: 700; color: #0f172a;">${dist.Safety || 0}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Application Tracker Callout Strip -->
          <div style="background: linear-gradient(135deg, #1e293b, #0f172a); color: #fff; padding: 18px 24px; border-radius: 12px; margin-bottom: 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
            <div style="display: flex; align-items: center; gap: 16px;">
              <div style="width: 44px; height: 44px; border-radius: 10px; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; color: #60a5fa;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
              </div>

              <div>
                <div style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #60a5fa;">Application Tracker</div>
                <div style="font-size: 1.15rem; font-weight: 700;">
                  ${savedColleges.length > 0 ? `${overallAppProgress}% Complete Across Saved Colleges` : 'Ready to Start Your Applications'}
                </div>
                <div style="font-size: 0.8125rem; color: #cbd5e1; margin-top: 2px;">
                  Track transcripts, supplemental essays, test scores, recommendation letters, and decisions.
                </div>
              </div>
            </div>
            <a href="#/tracker" class="btn btn-primary" style="background: #2563eb; color: #fff; font-weight: 600; border: none; padding: 8px 18px;">
              Open Application Tracker →
            </a>
          </div>

          ${savedColleges.length > 0 ? `
            <!-- "Your Schools" Section matching image1.jpg -->
            <section style="margin-bottom: 40px;" aria-label="Saved Colleges">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 12px;">
                <div>
                  <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin: 0;">Your Schools</h2>
                  <p style="font-size: 0.8125rem; color: #64748b; margin: 2px 0 0 0;">Your saved institutions and application progress</p>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                  <a href="#/colleges" class="btn btn-sm btn-secondary">+ Add More Schools</a>
                  <a href="#/compare" class="btn btn-sm btn-secondary">Compare All</a>
                </div>
              </div>

              <div class="college-card-grid">
                ${savedColleges.map(item => {
                  const inCompare = state.compareList.includes(String(item.college_id));
                  return renderCollegeCard({
                    id: item.college_id,
                    name: item.college_name,
                    location: item.location ? { city: item.location.split(',')[0], state: item.location.split(',')[1]?.trim() } : {},
                    type: item.type,
                    average_net_price: item.net_price,
                    acceptance_rate: item.admit_rate,
                    median_earnings_10yr: item.median_earnings,
                    category: item.category,
                    tracker: item.tracker
                  }, {
                    isSaved: true,
                    inCompare,
                    category: item.category,
                    userNote: item.user_note
                  });
                }).join('')}
              </div>
            </section>

            <!-- "Portfolio Insights" 6-Chart Grid -->
            <section style="margin-bottom: 40px;" aria-label="Portfolio Insights">
              <h2 style="font-size: 1.3rem; font-weight: 800; color: #0f172a; margin-bottom: 16px;">Portfolio Insights</h2>
              
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                
                <!-- Chart 1: Cost vs. Early Career Earnings Scatter -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                  <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Cost vs. Earnings</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0 0;">Net price vs. 10-yr career pay by school</p>
                  </div>
                  <div style="margin-top: 10px;">
                    ${renderScatterChart(savedColleges, 300, 200)}
                  </div>
                </div>

                <!-- Chart 2: Avg Net Price Bar Chart -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                  <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Net Price Comparison</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0 0;">After grants & aid applied</p>
                  </div>
                  <div style="margin-top: 10px;">
                    ${renderNetPriceBarChart(savedColleges, 360)}
                  </div>
                </div>

                <!-- Chart 3: Avg 10-Yr Earnings Bar Chart -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                  <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Avg. Income by School</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0 0;">Estimated 10-yr post-grad earnings</p>
                  </div>
                  <div style="margin-top: 10px;">
                    ${renderEarningsBarChart(savedColleges, 360)}
                  </div>
                </div>

                <!-- Chart 4: Admission Rate Comparison -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                  <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Acceptance Rate</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0 0;">Most selective first</p>
                  </div>
                  <div style="margin-top: 10px;">
                    ${renderAdmitRateBarChart(savedColleges, 360)}
                  </div>
                </div>

                <!-- Chart 5: Top Schools by Alumni Earnings Leaderboard -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; flex-direction: column;">
                  <div style="margin-bottom: 12px;">
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Top Schools by Earnings</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0 0;">10-year post-enrollment median compensation</p>
                  </div>
                  
                  <div class="custom-scrollbar" style="flex: 1; display: flex; flex-direction: column; gap: 8px; max-height: 320px; overflow-y: auto; padding-right: 6px;">
                    ${[...savedColleges].sort((a, b) => (b.median_earnings || 0) - (a.median_earnings || 0)).map((col, idx) => `
                      <div style="display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.8125rem;">
                        <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                          <span style="font-weight: 700; color: ${idx === 0 ? '#2563eb' : '#64748b'}; background: ${idx === 0 ? '#eff6ff' : '#f8fafc'}; width: 22px; height: 22px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0;">#${idx + 1}</span>
                          <span style="font-weight: 600; color: #0f172a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${col.college_name || col.name}
                          </span>
                        </div>
                        <span style="font-weight: 700; color: #059669; margin-left: 8px; flex-shrink: 0;">
                          ${formatMetricValue(col.median_earnings, 'currency')}
                        </span>
                      </div>
                    `).join('')}
                  </div>

                  <a href="#/compare" style="margin-top: 14px; font-size: 0.8125rem; font-weight: 600; color: #2563eb; text-decoration: none;">
                    View Full Comparisons →
                  </a>
                </div>

                <!-- Chart 6: Application Checklist Summary & Progress -->
                <div class="card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between;">
                  <div>
                    <h3 style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0;">Application Progress</h3>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 14px 0;">Checklist milestones across your schools</p>
                    
                    <!-- overall progress bar -->
                    <div style="margin-bottom: 16px;">
                      <div style="display:flex;justify-content:space-between;font-size:0.8rem;font-weight:600;color:#374151;margin-bottom:4px;">
                        <span>Overall Progress</span><span>${overallAppProgress}%</span>
                      </div>
                      <div style="height:8px;background:#e2e8f0;border-radius:9999px;overflow:hidden;">
                        <div style="width:${overallAppProgress}%;height:100%;background:${overallAppProgress >= 100 ? '#10b981' : overallAppProgress >= 50 ? '#3b82f6' : '#f59e0b'};border-radius:9999px;transition:width 0.5s;"></div>
                      </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 6px; font-size: 0.8125rem;">
                      <div style="display: flex; justify-content: space-between; padding: 5px 8px; background: #f8fafc; border-radius: 6px;">
                        <span>Submitted Apps</span>
                        <span style="font-weight: 700; color: #059669;">${appsSubmitted} / ${savedColleges.length}</span>
                      </div>
                      <div style="display: flex; justify-content: space-between; padding: 5px 8px; background: #f8fafc; border-radius: 6px;">
                        <span>Milestones Done</span>
                        <span style="font-weight: 700; color: #0f172a;">${appMilestonesDone} / ${appMilestonesTotal}</span>
                      </div>
                    </div>

                    <!-- Per-College Application Progress Bars (Scrollable with all colleges) -->
                    <div style="margin-top: 16px;">
                      <div style="font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">
                        All Schools (${savedColleges.length})
                      </div>
                      <div class="custom-scrollbar" style="display: flex; flex-direction: column; gap: 8px; max-height: 220px; overflow-y: auto; padding-right: 6px;">
                        ${savedColleges.map(c => {
                          const tracker = c.tracker || c.application_tracker || {};
                          const pct = tracker.completion_percentage ?? 0;
                          const cname = c.college_name || c.canonical_name || c.name || 'College';
                          return `
                            <div style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;">
                              <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; font-weight: 600; color: #0f172a; margin-bottom: 4px;">
                                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px;">${cname}</span>
                                <span style="color: ${pct >= 100 ? '#10b981' : pct > 0 ? '#2563eb' : '#94a3b8'}; font-weight: 700;">${pct}%</span>
                              </div>
                              <div style="height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
                                <div style="width: ${pct}%; height: 100%; background: ${pct >= 100 ? '#10b981' : pct > 0 ? '#2563eb' : '#cbd5e1'}; border-radius: 9999px;"></div>
                              </div>
                            </div>
                          `;
                        }).join('')}
                      </div>
                    </div>
                  </div>

                  <a href="#/tracker" class="btn btn-sm btn-primary" style="margin-top: 14px; text-align: center;">
                    Manage Application Tracker
                  </a>
                </div>



              </div>
            </section>
          ` : `
            <div class="card" style="text-align: center; padding: 64px 24px; background: #fff; border-radius: 12px; border: 1px solid #e2e8f0;">
              <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 16px; background: #eff6ff; color: #2563eb; margin-bottom: 16px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
              </div>
              <h3 style="font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">Your College List is Empty</h3>
              <p style="font-size: 1rem; color: #64748b; max-width: 500px; margin: 0 auto 24px;">
                Explore our comprehensive database of 50+ U.S. flagship universities. Save schools to build your list, track application milestones, and compare earnings.
              </p>
              <a href="#/colleges" class="btn btn-lg btn-primary">
                Explore Flagship Colleges
              </a>
            </div>

          `}

          <!-- Quick Add / Search Row -->
          <div class="card" style="margin-top: 32px; background: #fff; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;">
              <div>
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 0 0 4px 0;">Quick Add to Portfolio</h3>
                <p style="font-size: 0.8125rem; color: #64748b; margin: 0;">Search by name or state to immediately add a college to your tracker.</p>
              </div>
              <div style="display: flex; gap: 10px; flex: 1; max-width: 460px;">
                <input 
                  type="text" 
                  id="quick-search-input" 
                  class="input-text" 
                  placeholder="Search college (e.g., Stanford, MIT, Texas, Florida)..." 
                  style="flex: 1;"
                />
                <button type="button" id="quick-search-btn" class="btn btn-secondary">Search</button>
              </div>
            </div>
            <div id="quick-search-results" style="margin-top: 14px; display: none;"></div>
          </div>

        </div>
      `;

      // Attach Quick Search Handlers
      DashboardPage.bindEvents(container, state);

    } catch (err) {
      console.error('Failed to render dashboard', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Unable to load portfolio</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  bindEvents(container, state) {
    const quickInput = container.querySelector('#quick-search-input');
    const quickBtn = container.querySelector('#quick-search-btn');
    const quickResults = container.querySelector('#quick-search-results');

    const handleQuickSearch = async () => {
      const q = quickInput?.value?.trim();
      if (!q || !quickResults) return;

      quickResults.style.display = 'block';
      quickResults.innerHTML = `
        <div style="padding: 12px; text-align: center; color: var(--text-muted);">
          <div class="spinner-sm" style="display: inline-block; vertical-align: middle; margin-right: 8px;"></div>
          Searching colleges...
        </div>
      `;

      try {
        const res = await API.searchColleges({ q, limit: 5 });
        const items = res.items || res.colleges || [];

        if (items.length === 0) {
          quickResults.innerHTML = `
            <div style="padding: 12px; font-size: 0.875rem; color: var(--text-secondary); text-align: center;">
              No colleges found matching "${q}". <a href="#/colleges">Try full search</a>
            </div>
          `;
          return;
        }

        quickResults.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${items.map(col => `
              <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius-sm);">
                <div>
                  <strong><a href="#/colleges/${col.id}">${col.canonical_name || col.name}</a></strong>
                  <span style="font-size: 0.8125rem; color: var(--text-muted); margin-left: 8px;">
                    ${col.location?.city || ''}, ${col.location?.state || ''}
                  </span>

                </div>
                <button 
                  type="button" 
                  class="btn btn-sm btn-primary" 
                  data-action="quick-add" 
                  data-college-id="${col.id}"
                >
                  Save
                </button>
              </div>
            `).join('')}
          </div>
        `;
      } catch (err) {
        quickResults.innerHTML = `
          <div style="padding: 12px; color: var(--color-destructive); font-size: 0.875rem;">
            Search error: ${err.message}
          </div>
        `;
      }
    };

    // Saved Schools Stat Card & Header Link Click -> Open Saved Modal
    const savedCard = container.querySelector('#saved-schools-stat-card');
    const headerCountLink = container.querySelector('#saved-header-count-link');
    [savedCard, headerCountLink].forEach(el => {
      if (el) {
        el.addEventListener('click', () => {
          SavedModal.open();
        });
      }
    });


    quickBtn?.addEventListener('click', handleQuickSearch);

    let quickDebounce = null;
    quickInput?.addEventListener('input', () => {
      clearTimeout(quickDebounce);
      const val = quickInput.value.trim();
      if (!val) {
        if (quickResults) {
          quickResults.style.display = 'none';
          quickResults.innerHTML = '';
        }
        return;
      }
      quickDebounce = setTimeout(handleQuickSearch, 250);
    });

    quickInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        clearTimeout(quickDebounce);
        handleQuickSearch();
      }
    });


    // Delegate Quick Add click
    quickResults?.addEventListener('click', async (e) => {
      const btn = e.target.closest('[data-action="quick-add"]');
      if (btn) {
        const id = btn.getAttribute('data-college-id');
        btn.disabled = true;
        btn.textContent = 'Saving…';
        try {
          const updated = await API.saveCollege(id);
          if (window.app?.setPortfolio) window.app.setPortfolio(updated);
          if (window.app?.updatePortfolioIndicators) window.app.updatePortfolioIndicators();
          window.app?.showToast('College added to your portfolio!', 'success');
          // Re-render dashboard silently without flash or scroll jump
          const currentScrollY = window.scrollY;
          await DashboardPage.render(container, state, { silent: true });
          window.scrollTo({ top: currentScrollY, behavior: 'instant' });
        } catch (err) {

          window.app?.showToast(`Failed to save: ${err.message}`, 'error');
          btn.disabled = false;
          btn.textContent = 'Save';
        }
      }
    });
  }
};
