/**
 * SVG Scatter Plot Component: Cost vs. Early Career Earnings
 * Matches original reference UI: X = Early Career Pay, Y = Net Price
 * Dots colored by category (Reach = orange, Target = green, Likely = blue).
 */

export function renderScatterChart(colleges = [], width = 340, height = 240) {
  if (!colleges || colleges.length === 0) {
    // Default mock data matching image1.jpg if empty
    colleges = [
      { name: 'Vanderbilt', net_price: 25804, earnings: 85900, category: 'Reach' },
      { name: 'UT Austin', net_price: 16620, earnings: 76200, category: 'Reach' },
      { name: 'Georgia Tech', net_price: 14621, earnings: 80100, category: 'Target' },
      { name: 'UVA', net_price: 20177, earnings: 75600, category: 'Target' },
      { name: 'Cornell', net_price: 23954, earnings: 83000, category: 'Reach' },
      { name: 'Emory', net_price: 26492, earnings: 72000, category: 'Reach' },
      { name: 'Florida', net_price: 11834, earnings: 62800, category: 'Target' },
      { name: 'Indiana', net_price: 10388, earnings: 55100, category: 'Likely' },
      { name: 'Rice', net_price: 22400, earnings: 82000, category: 'Reach' },
      { name: 'Michigan', net_price: 18500, earnings: 78000, category: 'Target' },
      { name: 'UNC Chapel Hill', net_price: 13200, earnings: 67000, category: 'Target' },
      { name: 'Ohio State', net_price: 19500, earnings: 61000, category: 'Likely' },
      { name: 'Penn State', net_price: 26000, earnings: 64000, category: 'Target' },
      { name: 'Wisconsin', net_price: 17000, earnings: 66000, category: 'Target' },
      { name: 'Purdue', net_price: 12500, earnings: 71000, category: 'Target' }
    ];
  }

  const padding = { top: 20, right: 25, bottom: 40, left: 45 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  // Dynamic scales based on colleges present
  const earningsList = colleges.map(c => Number(c.median_earnings_10yr ?? c.median_earnings ?? c.earnings ?? 0)).filter(v => v > 0);
  const costList = colleges.map(c => Number(c.average_net_price ?? c.net_price ?? 0)).filter(v => v > 0);

  const rawMinX = earningsList.length ? Math.min(...earningsList) : 40000;
  const rawMaxX = earningsList.length ? Math.max(...earningsList) : 100000;
  const rawMaxY = costList.length ? Math.max(...costList) : 50000;

  const minX = Math.max(0, Math.floor((rawMinX - 8000) / 10000) * 10000);
  const maxX = Math.max(minX + 30000, Math.ceil((rawMaxX + 8000) / 10000) * 10000);
  const minY = 0;
  const maxY = Math.max(35000, Math.ceil((rawMaxY + 6000) / 10000) * 10000);

  const scaleX = (val) => padding.left + ((val - minX) / (maxX - minX)) * innerW;
  const scaleY = (val) => padding.top + innerH - ((val - minY) / (maxY - minY)) * innerH;

  // Grid lines & labels
  const yStep = Math.round((maxY - minY) / 3 / 5000) * 5000 || 15000;
  const yTicks = [0, minY + yStep, minY + yStep * 2, maxY];
  const xStep = Math.round((maxX - minX) / 3 / 10000) * 10000 || 20000;
  const xTicks = [minX + xStep, minX + xStep * 2, maxX];

  const yGrid = yTicks.map(t => {
    const y = scaleY(t);
    return `
      <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#f1f5f9" stroke-width="1" />
      <text x="${padding.left - 6}" y="${y + 3}" font-size="9" fill="#94a3b8" text-anchor="end">$${t === 0 ? '0' : Math.round(t / 1000) + 'K'}</text>
    `;
  }).join('');

  const xGrid = xTicks.map(t => {
    const x = scaleX(t);
    return `
      <line x1="${x}" y1="${padding.top}" x2="${x}" y2="${padding.top + innerH}" stroke="#f1f5f9" stroke-width="1" />
      <text x="${x}" y="${padding.top + innerH + 16}" font-size="9" fill="#94a3b8" text-anchor="middle">$${Math.round(t / 1000)}K</text>
    `;
  }).join('');


  // Plot circles
  const dots = colleges.map(c => {
    const earnings = c.median_earnings_10yr ?? c.earnings ?? 70000;
    const cost = c.average_net_price ?? c.net_price ?? 20000;
    const cat = c.category ?? c.tag ?? 'Target';
    const cname = c.canonical_name || c.college_name || c.name || 'College';

    const cx = Math.max(padding.left + 5, Math.min(width - padding.right - 5, scaleX(earnings)));
    const cy = Math.max(padding.top + 5, Math.min(padding.top + innerH - 5, scaleY(cost)));

    let fill = '#10b981'; // Target (green)
    if (cat === 'Reach') fill = '#f97316'; // Reach (orange)
    else if (cat === 'Likely') fill = '#3b82f6'; // Likely (blue)

    return `
      <circle 
        cx="${cx.toFixed(1)}" 
        cy="${cy.toFixed(1)}" 
        r="5.5" 
        fill="${fill}" 
        opacity="0.85" 
        stroke="#ffffff" 
        stroke-width="1.5"
        style="cursor: pointer; transition: transform 0.2s, r 0.2s;"
      >
        <title>${cname}&#10;Category: ${cat}&#10;Net Price: $${Math.round(cost).toLocaleString()}&#10;Earnings: $${Math.round(earnings).toLocaleString()}</title>
      </circle>
    `;
  }).join('');

  return `
    <div class="scatter-chart-widget" style="width: 100%;">
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow: visible;">
        <!-- Axes lines -->
        <line x1="${padding.left}" y1="${padding.top + innerH}" x2="${width - padding.right}" y2="${padding.top + innerH}" stroke="#cbd5e1" stroke-width="1" />
        <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${padding.top + innerH}" stroke="#cbd5e1" stroke-width="1" />
        <!-- Grids -->
        ${yGrid}
        ${xGrid}
        <!-- Data Dots -->
        ${dots}
      </svg>
      <div style="display: flex; justify-content: center; gap: 16px; margin-top: 6px; font-size: 0.75rem; color: #64748b;">
        <span style="display: flex; align-items: center; gap: 4px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #f97316;"></span> Reach
        </span>
        <span style="display: flex; align-items: center; gap: 4px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span> Target
        </span>
        <span style="display: flex; align-items: center; gap: 4px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #3b82f6;"></span> Likely
        </span>
      </div>
    </div>
  `;
}
