/**
 * Bar Chart Components — horizontal and vertical SVG bar charts.
 * renderNetPriceBarChart: Net price by school (sorted cheapest → priciest)
 * renderEarningsBarChart: 10-yr median earnings by school (sorted highest → lowest)
 * renderGradRateBarChart: Graduation rate by school (sorted highest → lowest)
 */

const CAT_COLORS = { Reach: '#f97316', Target: '#10b981', Likely: '#3b82f6' };

/** Shared horizontal bar chart renderer */
function _horizontalBars({ data, width, height, barColor, format, subtitle }) {
  if (!data || data.length === 0) {
    return `<p style="font-size:0.8125rem;color:#94a3b8;text-align:center;padding:32px 0;">No data yet — save colleges to see this chart.</p>`;
  }

  const pad = { top: 8, right: 70, bottom: 8, left: 130 };
  const barH = 22;
  const gap = 10;
  const totalH = data.length * (barH + gap) + pad.top + pad.bottom;
  const innerW = width - pad.left - pad.right;

  const maxVal = Math.max(...data.map(d => d.value)) || 1;

  const bars = data.map((d, i) => {
    const y = pad.top + i * (barH + gap);
    const bw = Math.max(4, (d.value / maxVal) * innerW);
    const fill = d.color || barColor || '#3b82f6';
    const label = format === 'currency'
      ? (d.value >= 1000 ? `$${Math.round(d.value / 1000)}K` : `$${Math.round(d.value)}`)
      : format === 'percent'
      ? `${Math.round(d.value * 100)}%`
      : `${d.value}`;

    const shortName = d.name.length > 16 ? d.name.slice(0, 15) + '…' : d.name;

    return `
      <g>
        <text x="${pad.left - 8}" y="${y + barH / 2 + 4}" font-size="10" fill="#374151" text-anchor="end" title="${d.name}">${shortName}</text>
        <rect x="${pad.left}" y="${y}" width="${bw.toFixed(1)}" height="${barH}" fill="${fill}" rx="3" opacity="0.88">
          <title>${d.name}: ${label}</title>
        </rect>
        <text x="${pad.left + bw + 5}" y="${y + barH / 2 + 4}" font-size="9.5" fill="#374151" font-weight="600">${label}</text>
      </g>
    `;
  }).join('');

  return `
    <div style="width:100%; overflow:visible;">
      ${subtitle ? `<p style="font-size:0.75rem;color:#64748b;margin:0 0 10px;">${subtitle}</p>` : ''}
      <svg width="100%" height="${totalH}" viewBox="0 0 ${width} ${totalH}" style="overflow:visible; display:block;">
        ${bars}
      </svg>
    </div>
  `;
}

/** Net price bar chart — sorted cheapest first */
export function renderNetPriceBarChart(colleges = [], width = 360) {
  if (!colleges || colleges.length === 0) {
    return _horizontalBars({ data: [], width, format: 'currency' });
  }
  const data = colleges
    .map(c => {
      const val = c.net_price ?? c.average_net_price ?? c.college?.costs?.net_price_average?.value ?? c.summary?.average_net_price?.value ?? c.cost?.average_net_price ?? 0;
      return {
        name: c.college_name || c.canonical_name || c.name || 'College',
        value: Number(val) || 0,
        color: CAT_COLORS[c.category || c.tag] || '#3b82f6'
      };
    })
    .filter(d => d.value > 0)
    .sort((a, b) => a.value - b.value);

  return _horizontalBars({
    data,
    width,
    format: 'currency',
    subtitle: 'Average net price after grants & aid (cheapest first)'
  });
}

/** 10-yr earnings bar chart — sorted highest first */
export function renderEarningsBarChart(colleges = [], width = 360) {
  if (!colleges || colleges.length === 0) {
    return _horizontalBars({ data: [], width, format: 'currency' });
  }
  const data = colleges
    .map(c => {
      const val = c.median_earnings ?? c.median_earnings_10yr ?? c.college?.outcomes?.median_earnings_10yr?.value ?? c.summary?.median_earnings_10yr?.value ?? 0;
      return {
        name: c.college_name || c.canonical_name || c.name || 'College',
        value: Number(val) || 0,
        color: CAT_COLORS[c.category || c.tag] || '#10b981'
      };
    })
    .filter(d => d.value > 0)
    .sort((a, b) => b.value - a.value);

  return _horizontalBars({
    data,
    width,
    format: 'currency',
    subtitle: 'Estimated median 10-yr earnings post-enrollment (highest first)'
  });
}

/** Graduation rate bar chart — sorted highest first */
export function renderGradRateBarChart(colleges = [], width = 360) {
  if (!colleges || colleges.length === 0) {
    return _horizontalBars({ data: [], width, format: 'percent' });
  }
  const data = colleges
    .map(c => {
      const gr = c.graduation_rate ?? c.summary?.graduation_rate?.value ?? c.college?.outcomes?.completion_rate_6yr?.value ?? null;
      return {
        name: c.college_name || c.canonical_name || c.name || 'College',
        value: gr !== null && gr !== undefined ? Number(gr) : null,
        color: CAT_COLORS[c.category || c.tag] || '#8b5cf6'
      };
    })
    .filter(d => d.value !== null && d.value > 0)
    .sort((a, b) => b.value - a.value);

  return _horizontalBars({
    data,
    width,
    format: 'percent',
    subtitle: '4-year graduation rate (highest first)'
  });
}

/** Acceptance rate comparison bar chart — sorted most selective first */
export function renderAdmitRateBarChart(colleges = [], width = 360) {
  if (!colleges || colleges.length === 0) {
    return _horizontalBars({ data: [], width, format: 'percent' });
  }
  const data = colleges
    .map(c => {
      const val = c.admit_rate ?? c.acceptance_rate ?? c.college?.admissions?.acceptance_rate?.value ?? c.summary?.acceptance_rate?.value ?? null;
      return {
        name: c.college_name || c.canonical_name || c.name || 'College',
        value: val !== null && val !== undefined ? Number(val) : null,
        color: CAT_COLORS[c.category || c.tag] || '#f97316'
      };
    })
    .filter(d => d.value !== null && d.value > 0)
    .sort((a, b) => a.value - b.value);

  return _horizontalBars({
    data,
    width,
    format: 'percent',
    subtitle: 'Acceptance rate (most selective first)'
  });
}


