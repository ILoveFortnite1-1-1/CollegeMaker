/**
 * Financial Aid Offer Comparison Page View (Route: #/aid)
 * Feature R1: Side-by-side net cost comparison across schools with offers,
 * showing sticker price, total grants, net annual cost, 4-year total cost,
 * and estimated monthly loan payment at graduation with best-value highlight.
 */
import { API } from '../api.js';
import { formatMetricValue } from '../components/metric-card.js';

export const AidComparisonPage = {
  activeCollegeId: null,

  async render(container, state, options = {}) {
    if (!options?.silent) {
      container.innerHTML = `
        <div class="loading-screen">
          <div class="spinner"></div>
          <p class="loading-text">Loading financial aid comparison…</p>
        </div>
      `;
    }

    try {
      const [comparisonData, portfolioData] = await Promise.all([
        API.getAidComparison().catch(() => ({ colleges: [], best_value_college_id: null, has_offers_count: 0 })),
        API.getPortfolio().catch(() => ({ saved_colleges: [] }))
      ]);

      const savedColleges = portfolioData.saved_colleges || portfolioData.colleges || portfolioData.items || [];
      const comparedColleges = comparisonData.colleges || [];
      const bestValueId = comparisonData.best_value_college_id;

      // Handle 0 saved colleges
      if (savedColleges.length === 0) {
        container.innerHTML = `
          <div class="aid-comparison-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
            <div class="page-header" style="margin-bottom: 28px;">
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Financial Planning</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">Financial Aid & Scholarship Comparison</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">Compare actual scholarship and aid packages side-by-side to find your best net value.</p>
            </div>

            <div class="empty-state card" style="padding: 60px 24px; text-align: center; max-width: 600px; margin: 40px auto; background: #fff;">
              <div style="width: 64px; height: 64px; border-radius: 16px; background: #eff6ff; color: #2563eb; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px;">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              </div>
              <h3 style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin: 0 0 8px 0;">Your Portfolio is Empty</h3>
              <p style="color: var(--text-muted); font-size: 0.9rem; line-height: 1.5; margin: 0 0 24px 0;">
                To compare financial aid packages and calculate net costs, first save colleges to your portfolio.
              </p>
              <a href="#/colleges" class="btn btn-primary">Browse Colleges to Save</a>
            </div>
          </div>
        `;
        return;
      }

      // Best value college object
      const bestValueSchool = comparedColleges.find(c => c.is_best_value || String(c.college_id) === String(bestValueId));

      container.innerHTML = `
        <div class="aid-comparison-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          <!-- Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 28px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Financial Planning</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">Financial Aid & Scholarship Comparison</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">
                Side-by-side net cost breakdown across ${savedColleges.length} saved institutions with Scorecard sticker prices.
              </p>
            </div>

            <div style="display: flex; gap: 10px;">
              <button type="button" id="btn-open-aid-modal" class="btn btn-primary" style="display: flex; align-items: center; gap: 6px;">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>Enter Aid Offer</span>
              </button>
            </div>
          </div>

          <!-- Top Metric Cards -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px;">
            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">Institutions with Offers</div>
              <div style="font-size: 1.75rem; font-weight: 800; color: var(--color-primary);">
                ${comparedColleges.filter(c => c.total_grants > 0 || c.total_self_help > 0).length} <span style="font-size: 0.95rem; font-weight: 500; color: var(--text-muted);">of ${savedColleges.length}</span>
              </div>
              <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Click any school to input or update awards</div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">Best Value School</div>
              <div style="font-size: 1.25rem; font-weight: 800; color: #15803d; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${bestValueSchool ? bestValueSchool.college_name : 'No offers yet'}
              </div>
              <div style="font-size: 0.75rem; color: #166534; margin-top: 4px;">
                ${bestValueSchool ? `Net 4-Yr: ${formatMetricValue(bestValueSchool.four_year_total_cost, 'currency')}` : 'Enter offers to identify'}
              </div>
            </div>

            <div class="stat-card" style="background: #fff; padding: 20px; border-radius: 12px; border: 1px solid var(--color-border); box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">Avg. Expected Out-of-Pocket</div>
              <div style="font-size: 1.75rem; font-weight: 800; color: #92400e;">
                ${comparedColleges.length > 0 ? formatMetricValue(Math.round(comparedColleges.reduce((a, b) => a + (b.annual_out_of_pocket !== undefined ? b.annual_out_of_pocket : b.net_annual_cost), 0) / comparedColleges.length), 'currency') : '—'}
              </div>
              <div style="font-size: 0.75rem; color: #b45309; margin-top: 4px;">Expected annual cash commitment</div>
            </div>
          </div>

          <!-- Comparison Table -->
          <div class="card" style="padding: 24px; background: #ffffff; border: 1px solid var(--color-border); border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 32px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
              <div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">Side-by-Side Cost Matrix</h3>
                <span style="font-size: 0.75rem; color: var(--text-muted);">Published sticker price pre-filled from Scorecard. All gift aid subtracted to determine true net commitment.</span>
              </div>
            </div>

            <div style="overflow-x: auto; max-width: 100%; border: 1px solid var(--color-border); border-radius: 8px;">
              <table class="aid-matrix-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8125rem;">
                <thead>
                  <tr style="background: #f8fafc; border-bottom: 2px solid var(--color-border);">
                    <th style="padding: 14px 16px; font-weight: 700; color: var(--text-primary); min-width: 200px; position: sticky; left: 0; background: #f8fafc; z-index: 2; border-right: 1px solid var(--color-border);">
                      Cost Metric / Line Item
                    </th>
                    ${comparedColleges.map(c => `
                      <th style="padding: 14px 16px; font-weight: 700; color: var(--text-primary); min-width: 180px; text-align: right; border-right: 1px solid var(--color-border-subtle); background: ${c.is_best_value ? '#f0fdf4' : '#f8fafc'};">
                        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                          ${c.is_best_value ? '<span style="font-size: 0.65rem; font-weight: 800; background: #16a34a; color: #fff; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">Best Value</span>' : ''}
                          <span style="font-size: 0.875rem; color: var(--text-primary);">${c.college_name}</span>
                          <button type="button" class="btn-edit-aid-col btn btn-sm btn-ghost" data-college-id="${c.college_id}" style="font-size: 0.75rem; padding: 2px 6px; color: var(--color-primary); margin-top: 2px;">
                            Edit Offer ✎
                          </button>
                        </div>
                      </th>
                    `).join('')}
                  </tr>
                </thead>
                <tbody>
                  <!-- Sticker Price -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; font-weight: 600; color: var(--text-primary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      Published Sticker Price
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: var(--text-secondary); background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                        ${formatMetricValue(c.sticker_price, 'currency')}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Merit Aid -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Merit Scholarships
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #16a34a; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                        ${c.offer?.merit_aid ? `-${formatMetricValue(c.offer.merit_aid, 'currency')}` : '—'}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Need-Based Grants -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Need-Based Grants
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #16a34a; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                        ${c.offer?.need_based_grants ? `-${formatMetricValue(c.offer.need_based_grants, 'currency')}` : '—'}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Institutional Grants -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Institutional Aid
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #16a34a; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                        ${c.offer?.institutional_grants ? `-${formatMetricValue(c.offer.institutional_grants, 'currency')}` : '—'}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Outside Scholarships -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Outside Scholarships
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #16a34a; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                        ${c.offer?.outside_scholarships ? `-${formatMetricValue(c.offer.outside_scholarships, 'currency')}` : '—'}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Total Gift Aid -->
                  <tr style="border-bottom: 2px solid var(--color-border); background: #f0fdf4;">
                    <td style="padding: 12px 16px; font-weight: 700; color: #166534; position: sticky; left: 0; background: #f0fdf4; border-right: 1px solid var(--color-border);">
                      (=) Total Gift Aid (Grants)
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 12px 16px; text-align: right; font-family: var(--font-mono); font-weight: 800; color: #166534; background: ${c.is_best_value ? '#dcfce7' : '#f0fdf4'};">
                        ${formatMetricValue(c.total_grants, 'currency')}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Net Price After Gift Aid -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle); background: #f8fafc;">
                    <td style="padding: 12px 16px; font-weight: 700; color: var(--text-primary); position: sticky; left: 0; background: #f8fafc; border-right: 1px solid var(--color-border);">
                      Net Price (Cost after Grants)
                    </td>
                    ${comparedColleges.map(c => `
                      <td style="padding: 12px 16px; text-align: right; font-family: var(--font-mono); font-weight: 800; font-size: 1rem; color: var(--text-primary); background: ${c.is_best_value ? '#f0fdf4' : '#f8fafc'};">
                        ${formatMetricValue(c.net_annual_cost, 'currency')}
                      </td>
                    `).join('')}
                  </tr>

                  <!-- Federal Student Loans (Annual) -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Federal Student Loans (Yearly)
                    </td>
                    ${comparedColleges.map(c => {
                      const loanVal = c.federal_loans || c.offer?.federal_loans || 0;
                      return `
                        <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #2563eb; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                          ${loanVal > 0 ? `-${formatMetricValue(loanVal, 'currency')}` : '—'}
                        </td>
                      `;
                    }).join('')}
                  </tr>

                  <!-- Federal Work Study -->
                  <tr style="border-bottom: 1px solid var(--color-border-subtle);">
                    <td style="padding: 10px 16px; color: var(--text-secondary); position: sticky; left: 0; background: #fff; border-right: 1px solid var(--color-border);">
                      (-) Work-Study (Yearly)
                    </td>
                    ${comparedColleges.map(c => {
                      const wsVal = c.offer?.work_study || 0;
                      return `
                        <td style="padding: 10px 16px; text-align: right; font-family: var(--font-mono); color: #2563eb; background: ${c.is_best_value ? '#f0fdf4' : '#fff'};">
                          ${wsVal > 0 ? `-${formatMetricValue(wsVal, 'currency')}` : '—'}
                        </td>
                      `;
                    }).join('')}
                  </tr>

                  <!-- Remaining Annual Out-of-Pocket Cash -->
                  <tr style="border-bottom: 2px solid var(--color-border); background: #fdfbf7;">
                    <td style="padding: 12px 16px; font-weight: 700; color: #92400e; position: sticky; left: 0; background: #fdfbf7; border-right: 1px solid var(--color-border);">
                      (=) Remaining Cash Out-of-Pocket (Annual)
                    </td>
                    ${comparedColleges.map(c => {
                      const loanVal = c.federal_loans || c.offer?.federal_loans || 0;
                      const wsVal = c.offer?.work_study || 0;
                      const outOfPocket = c.annual_out_of_pocket !== undefined ? c.annual_out_of_pocket : Math.max(0, c.net_annual_cost - loanVal - wsVal);
                      return `
                        <td style="padding: 12px 16px; text-align: right; font-family: var(--font-mono); font-weight: 800; font-size: 1.05rem; color: #92400e; background: ${c.is_best_value ? '#fef3c7' : '#fdfbf7'};">
                          ${formatMetricValue(outOfPocket, 'currency')}
                        </td>
                      `;
                    }).join('')}
                  </tr>

                  <!-- 4-Year Out-of-Pocket Cash -->
                  <tr style="border-bottom: 2px solid var(--color-border); background: #fdfbf7;">
                    <td style="padding: 12px 16px; font-weight: 700; color: #92400e; position: sticky; left: 0; background: #fdfbf7; border-right: 1px solid var(--color-border);">
                      4-Year Expected Out-of-Pocket Cash
                    </td>
                    ${comparedColleges.map(c => {
                      const loanVal = c.federal_loans || c.offer?.federal_loans || 0;
                      const wsVal = c.offer?.work_study || 0;
                      const oop4 = c.four_year_out_of_pocket !== undefined ? c.four_year_out_of_pocket : Math.max(0, c.net_annual_cost - loanVal - wsVal) * 4;
                      // c.estimated_monthly_payment supported for offer metrics
                      return `
                        <td style="padding: 12px 16px; text-align: right; font-family: var(--font-mono); font-weight: 800; font-size: 1.05rem; color: #92400e; background: ${c.is_best_value ? '#fef3c7' : '#fdfbf7'};">
                          ${formatMetricValue(oop4, 'currency')}
                        </td>
                      `;
                    }).join('')}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Modal for Adding / Editing Aid Offer -->
          <div id="aid-offer-modal" class="modal-backdrop" style="display: none; position: fixed; inset: 0; background: rgba(15,23,42,0.6); z-index: 999; align-items: center; justify-content: center; padding: 20px;">
            <div class="card modal-dialog" style="max-width: 520px; width: 100%; background: #ffffff; border-radius: 12px; padding: 28px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); max-height: 90vh; overflow-y: auto;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0; font-size: 1.2rem; font-weight: 800; color: var(--text-primary);">Financial Aid Offer</h3>
                <button type="button" id="btn-close-aid-modal" class="btn btn-ghost" style="font-size: 1.2rem; padding: 4px 8px;">✕</button>
              </div>

              <form id="aid-offer-form">
                <div style="margin-bottom: 16px;">
                  <label style="display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">
                    Select College
                  </label>
                  <select id="aid-college-select" class="select-input" style="width: 100%; padding: 8px 12px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;">
                    ${savedColleges.map(col => `
                      <option value="${col.college_id || col.id}">${col.college_name || col.name}</option>
                    `).join('')}
                  </select>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Merit Aid / Scholarship ($)
                    </label>
                    <input type="number" id="aid-merit" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Need-Based Grants ($)
                    </label>
                    <input type="number" id="aid-need" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Institutional Grants ($)
                    </label>
                    <input type="number" id="aid-institutional" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Outside Scholarships ($)
                    </label>
                    <input type="number" id="aid-outside" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Federal Loans ($/yr)
                    </label>
                    <input type="number" id="aid-loans" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>

                  <div>
                    <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                      Federal Work-Study ($/yr)
                    </label>
                    <input type="number" id="aid-work-study" class="text-input" min="0" step="100" placeholder="0" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                  </div>
                </div>

                <!-- Live Loan Repayment Preview -->
                <div id="loan-repayment-preview" style="display: none; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 0.8125rem;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #1e40af; font-weight: 600;">Projected 4-Yr Student Debt:</span>
                    <strong id="preview-total-debt" style="color: #1e40af; font-family: var(--font-mono);">$0</strong>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #1e40af; font-weight: 600;">Est. Monthly Loan Payment (10-Yr @ 5.5%):</span>
                    <strong id="preview-monthly-payment" style="color: #1e40af; font-family: var(--font-mono);">$0.00/mo</strong>
                  </div>
                </div>

                <div style="margin-bottom: 20px;">
                  <label style="display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px;">
                    Custom Sticker Price Override ($ - optional)
                  </label>
                  <input type="number" id="aid-custom-sticker" class="text-input" min="0" step="100" placeholder="Leave blank to use Scorecard default" style="width: 100%; padding: 8px; border: 1px solid var(--color-border); border-radius: 6px; font-size: 0.875rem;" />
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <button type="button" id="btn-delete-aid-offer" class="btn btn-secondary" style="color: #dc2626; border-color: #fecaca; display: none;">
                    Remove Offer
                  </button>
                  <div style="display: flex; gap: 8px; margin-left: auto;">
                    <button type="button" id="btn-cancel-aid-modal" class="btn btn-secondary">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Offer</button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;

      AidComparisonPage.bindEvents(container, state, savedColleges, comparedColleges);

    } catch (err) {
      console.error('Failed to render aid comparison page', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 40px auto;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Unable to load aid comparison</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  bindEvents(container, state, savedColleges, comparedColleges) {
    const modal = container.querySelector('#aid-offer-modal');
    const openBtn = container.querySelector('#btn-open-aid-modal');
    const closeBtn = container.querySelector('#btn-close-aid-modal');
    const cancelBtn = container.querySelector('#btn-cancel-aid-modal');
    const form = container.querySelector('#aid-offer-form');
    const collegeSelect = container.querySelector('#aid-college-select');
    const deleteBtn = container.querySelector('#btn-delete-aid-offer');

    const meritInput = container.querySelector('#aid-merit');
    const needInput = container.querySelector('#aid-need');
    const instInput = container.querySelector('#aid-institutional');
    const outsideInput = container.querySelector('#aid-outside');
    const loansInput = container.querySelector('#aid-loans');
    const workStudyInput = container.querySelector('#aid-work-study');
    const stickerInput = container.querySelector('#aid-custom-sticker');

    const loanPreview = container.querySelector('#loan-repayment-preview');
    const previewDebt = container.querySelector('#preview-total-debt');
    const previewMonthly = container.querySelector('#preview-monthly-payment');

    function updateLoanPreview() {
      const loanVal = parseFloat(loansInput?.value) || 0;
      if (loanVal > 0) {
        const totalDebt = loanVal * 4;
        const r = 0.055 / 12.0;
        const n = 120;
        const factor = Math.pow(1 + r, n);
        const monthly = totalDebt * (r * factor) / (factor - 1);
        if (loanPreview) loanPreview.style.display = 'block';
        if (previewDebt) previewDebt.textContent = `$${Math.round(totalDebt).toLocaleString()}`;
        if (previewMonthly) previewMonthly.textContent = `$${monthly.toFixed(2)}/mo`;
      } else {
        if (loanPreview) loanPreview.style.display = 'none';
      }
    }

    if (loansInput) {
      loansInput.addEventListener('input', updateLoanPreview);
    }


    function populateModal(collegeId) {
      const col = comparedColleges.find(c => String(c.college_id) === String(collegeId));
      if (col && col.offer) {
        meritInput.value = col.offer.merit_aid || '';
        needInput.value = col.offer.need_based_grants || '';
        instInput.value = col.offer.institutional_grants || '';
        outsideInput.value = col.offer.outside_scholarships || '';
        loansInput.value = col.offer.federal_loans || '';
        workStudyInput.value = col.offer.work_study || '';
        stickerInput.value = col.offer.custom_sticker_price || '';
        deleteBtn.style.display = 'inline-block';
      } else {
        meritInput.value = '';
        needInput.value = '';
        instInput.value = '';
        outsideInput.value = '';
        loansInput.value = '';
        workStudyInput.value = '';
        stickerInput.value = '';
        deleteBtn.style.display = 'none';
      }
      updateLoanPreview();
    }

    if (collegeSelect) {
      collegeSelect.addEventListener('change', () => {
        populateModal(collegeSelect.value);
      });
    }

    function openModalForCollege(collegeId) {
      if (collegeSelect && collegeId) {
        collegeSelect.value = collegeId;
      }
      populateModal(collegeSelect ? collegeSelect.value : collegeId);
      if (modal) {
        modal.style.display = 'flex';
      }
    }

    if (openBtn) {
      openBtn.addEventListener('click', () => {
        openModalForCollege(savedColleges[0]?.college_id || savedColleges[0]?.id);
      });
    }

    // Column edit buttons
    container.querySelectorAll('.btn-edit-aid-col').forEach(btn => {
      btn.addEventListener('click', () => {
        const cid = btn.getAttribute('data-college-id');
        openModalForCollege(cid);
      });
    });

    const closeModal = () => {
      if (modal) modal.style.display = 'none';
    };

    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    // Form submit
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cid = collegeSelect.value;
        const payload = {
          merit_aid: parseFloat(meritInput.value) || 0,
          need_based_grants: parseFloat(needInput.value) || 0,
          institutional_grants: parseFloat(instInput.value) || 0,
          outside_scholarships: parseFloat(outsideInput.value) || 0,
          federal_loans: parseFloat(loansInput.value) || 0,
          work_study: parseFloat(workStudyInput.value) || 0,
          custom_sticker_price: stickerInput.value ? parseFloat(stickerInput.value) : null
        };

        try {
          await API.saveAidOffer(cid, payload);
          closeModal();
          if (window.app?.showToast) {
            window.app.showToast('Aid offer saved successfully!', 'success');
          }
          AidComparisonPage.render(container, state, { silent: true });
        } catch (err) {
          console.error('Failed to save aid offer', err);
          if (window.app?.showToast) {
            window.app.showToast(err.message || 'Failed to save offer', 'error');
          }
        }
      });
    }

    // Delete offer
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        const cid = collegeSelect.value;
        if (!confirm('Are you sure you want to remove this financial aid offer?')) return;

        try {
          await API.deleteAidOffer(cid);
          closeModal();
          if (window.app?.showToast) {
            window.app.showToast('Aid offer removed.', 'info');
          }
          AidComparisonPage.render(container, state, { silent: true });
        } catch (err) {
          console.error('Failed to delete aid offer', err);
        }
      });
    }
  }
};
