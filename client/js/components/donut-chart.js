/**
 * SVG Donut Chart Component: Career Outlook (All Schools)
 * Matches image1.jpg: Top Industries for Econ/Business/Undergrad Grads
 * Finance 29%, Consulting 24%, Technology 18%, Accounting 11%, Government 9%, Other 9%
 */

export function renderDonutChart(data = null, size = 180) {
  const defaultSlices = [
    { label: 'Finance', pct: 29, color: '#1e3a8a' },
    { label: 'Consulting', pct: 24, color: '#2563eb' },
    { label: 'Technology', pct: 18, color: '#0284c7' },
    { label: 'Accounting', pct: 11, color: '#10b981' },
    { label: 'Government', pct: 9, color: '#f59e0b' },
    { label: 'Other', pct: 9, color: '#94a3b8' }
  ];

  const slices = data || defaultSlices;
  const radius = size / 2;
  const strokeWidth = 32;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = 2 * Math.PI * normalizedRadius;

  let accumulatedPct = 0;
  const svgCircles = slices.map(s => {
    const strokeDashoffset = circumference - (s.pct / 100) * circumference;
    const rotation = (accumulatedPct / 100) * 360 - 90;
    accumulatedPct += s.pct;

    return `
      <circle
        cx="${radius}"
        cy="${radius}"
        r="${normalizedRadius}"
        fill="transparent"
        stroke="${s.color}"
        stroke-width="${strokeWidth}"
        stroke-dasharray="${circumference}"
        stroke-dashoffset="${strokeDashoffset}"
        transform="rotate(${rotation} ${radius} ${radius})"
        style="transition: stroke-dashoffset 0.5s ease;"
      >
        <title>${s.label}: ${s.pct}%</title>
      </circle>
    `;
  }).join('');

  const legendItems = slices.map(s => `
    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem; color: #475569; margin-bottom: 4px;">
      <span style="display: flex; align-items: center; gap: 6px;">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: ${s.color}; flex-shrink: 0;"></span>
        <span>${s.label}</span>
      </span>
      <span style="font-weight: 600; color: #0f172a; margin-left: 12px;">${s.pct}%</span>
    </div>
  `).join('');

  return `
    <div class="donut-chart-widget" style="display: flex; align-items: center; gap: 16px; width: 100%;">
      <div style="width: ${size}px; height: ${size}px; position: relative; flex-shrink: 0;">
        <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
          ${svgCircles}
        </svg>
      </div>
      <div class="donut-legend" style="flex: 1; min-width: 0;">
        ${legendItems}
      </div>
    </div>
  `;
}
