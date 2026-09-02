/**
 * Horizontal Bar Chart Component: Top Recruiting Industries
 * Matches profile bottom right in image1.jpg
 */

export function renderHorizontalBarChart(data = null) {
  const defaultItems = [
    { label: 'Finance', pct: 28 },
    { label: 'Consulting', pct: 25 },
    { label: 'Technology', pct: 20 },
    { label: 'Accounting', pct: 10 },
    { label: 'Government', pct: 7 },
    { label: 'Other', pct: 10 }
  ];

  const items = data || defaultItems;

  const rows = items.map(item => `
    <div style="margin-bottom: 10px;">
      <div style="display: flex; justify-content: space-between; font-size: 0.8125rem; margin-bottom: 3px;">
        <span style="font-weight: 500; color: #334155;">${item.label}</span>
        <span style="font-weight: 600; color: #0f172a;">${item.pct}%</span>
      </div>
      <div style="width: 100%; height: 7px; background: #f1f5f9; border-radius: 9999px; overflow: hidden;">
        <div style="width: ${item.pct}%; height: 100%; background: #2563eb; border-radius: 9999px; transition: width 0.6s ease;"></div>
      </div>
    </div>
  `).join('');

  return `
    <div class="horizontal-bar-chart" style="width: 100%;">
      ${rows}
    </div>
  `;
}
