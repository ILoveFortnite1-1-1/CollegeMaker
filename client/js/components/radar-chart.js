/**
 * SVG Radar / Spider Web Chart Component
 * Renders an 8-axis polygon radar chart matching the original reference screenshot.
 */

export function renderRadarChart(dimensions = {}, size = 320) {
  // Default dimensions if missing
  const defaultLabels = [
    { key: 'academic', label: 'Academic Fit', val: 85 },
    { key: 'career', label: 'Career Potential', val: 90 },
    { key: 'roi', label: 'ROI / Value', val: 82 },
    { key: 'cost', label: 'Affordability', val: 78 },
    { key: 'admissions', label: 'Admissions Fit', val: 68 },
    { key: 'experience', label: 'Student Experience', val: 92 },
    { key: 'network', label: 'Network', val: 88 },
    { key: 'strength', label: 'Business/Econ Strength', val: 86 }
  ];

  const axes = defaultLabels.map(item => {
    let score = item.val;
    if (dimensions && typeof dimensions === 'object') {
      const d = dimensions[item.key] || dimensions[`${item.key}_fit`] || dimensions[`academic_${item.key}`];
      if (d) {
        score = typeof d === 'object' ? (d.raw_score ?? d.score ?? item.val) : d;
      }
    }
    return { ...item, score: Math.max(20, Math.min(100, Math.round(score))) };
  });

  const center = size / 2;
  const radius = (size - 90) / 2;
  const angleStep = (2 * Math.PI) / axes.length;

  // Generate concentric polygon grid levels (20%, 40%, 60%, 80%, 100%)
  const levels = [0.2, 0.4, 0.6, 0.8, 1.0];
  const gridPolygons = levels.map(level => {
    const points = axes.map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const x = center + radius * level * Math.cos(angle);
      const y = center + radius * level * Math.sin(angle);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
    return `<polygon points="${points}" fill="none" stroke="#e2e8f0" stroke-width="1" />`;
  }).join('');

  // Spoke lines
  const spokeLines = axes.map((_, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const x = center + radius * Math.cos(angle);
    const y = center + radius * Math.sin(angle);
    return `<line x1="${center}" y1="${center}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2,2" />`;
  }).join('');

  // Data polygon points
  const dataPoints = axes.map((axis, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const r = (axis.score / 100) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return { x, y, score: axis.score, label: axis.label };
  });

  const polygonPointsStr = dataPoints.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');

  // Outer labels
  const labelElements = axes.map((axis, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const labelRadius = radius + 22;
    const x = center + labelRadius * Math.cos(angle);
    const y = center + labelRadius * Math.sin(angle);

    let textAnchor = 'middle';
    if (Math.cos(angle) > 0.25) textAnchor = 'start';
    else if (Math.cos(angle) < -0.25) textAnchor = 'end';

    const dominantBaseline = Math.sin(angle) > 0.4 ? 'hanging' : (Math.sin(angle) < -0.4 ? 'auto' : 'middle');

    return `
      <text 
        x="${x.toFixed(1)}" 
        y="${y.toFixed(1)}" 
        text-anchor="${textAnchor}" 
        dominant-baseline="${dominantBaseline}"
        font-size="10.5" 
        font-weight="500" 
        fill="#475569"
        font-family="system-ui, -apple-system, sans-serif"
      >
        ${axis.label}
      </text>
    `;
  }).join('');

  // Vertex dots
  const vertexDots = dataPoints.map(p => `
    <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#2563eb" stroke="#ffffff" stroke-width="1.5">
      <title>${p.label}: ${p.score}/100</title>
    </circle>
  `).join('');

  return `
    <div class="radar-chart-container" style="display: flex; justify-content: center; align-items: center; width: 100%;">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="overflow: visible; max-width: 100%;">
        <!-- Grid Polygons -->
        ${gridPolygons}
        <!-- Spoke Lines -->
        ${spokeLines}
        <!-- Data Polygon -->
        <polygon points="${polygonPointsStr}" fill="rgba(37, 99, 235, 0.15)" stroke="#2563eb" stroke-width="2" stroke-linejoin="round" />
        <!-- Data Vertex Dots -->
        ${vertexDots}
        <!-- Axis Labels -->
        ${labelElements}
      </svg>
    </div>
  `;
}
