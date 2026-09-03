import { formatConfidence } from './metric-card.js';

export class ProvenanceDrawer {

  static init() {
    const drawer = document.getElementById('provenance-drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    const closeBtn = document.getElementById('close-drawer-btn');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => ProvenanceDrawer.close());
    }

    if (backdrop) {
      backdrop.addEventListener('click', () => ProvenanceDrawer.close());
    }

    // Escape key listener
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        ProvenanceDrawer.close();
      }
    });

    // Delegate clicks on any element with data-provenance attribute
    document.addEventListener('click', (e) => {
      const target = e.target.closest('[data-provenance]');
      if (target) {
        e.preventDefault();
        try {
          const raw = decodeURIComponent(target.getAttribute('data-provenance'));
          const data = JSON.parse(raw);
          ProvenanceDrawer.open(data);
        } catch (err) {
          console.error('Failed to parse provenance data', err);
        }
      }
    });
  }

  static open(data) {
    const drawer = document.getElementById('provenance-drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    const content = document.getElementById('drawer-content');
    const title = document.getElementById('drawer-title');

    if (!drawer || !backdrop || !content) return;

    title.textContent = data.fieldName || 'Metric Provenance';

    const confStr = formatConfidence(data.confidence);
    const confNum = parseInt(confStr, 10) || 100;
    const retrievedDate = data.retrieved_at ? new Date(data.retrieved_at).toLocaleString() : 'Recent Ingestion';
    const sourceUrl = data.source_url ? `<a href="${data.source_url}" target="_blank" rel="noopener" class="text-link">View External Source ↗</a>` : 'Standard Regulatory Ingestion';

    content.innerHTML = `
      <div class="provenance-meta-box">
        <div class="provenance-row">
          <span class="provenance-label">Field Classification</span>
          <span class="provenance-value font-mono">${(data.status || 'reported').toUpperCase()}</span>
        </div>
        <div class="provenance-row">
          <span class="provenance-label">Source Provider</span>
          <span class="provenance-value">${data.source || 'U.S. Department of Education Scorecard'}</span>
        </div>
        <div class="provenance-row">
          <span class="provenance-label">Source Type</span>
          <span class="provenance-value">${data.source_type || 'government'}</span>
        </div>
        <div class="provenance-row">
          <span class="provenance-label">Data Year / Cohort</span>
          <span class="provenance-value">${data.year || 'Latest Reporting Period'}</span>
        </div>
        <div class="provenance-row">
          <span class="provenance-label">Last Ingested</span>
          <span class="provenance-value">${retrievedDate}</span>
        </div>
      </div>

      <div class="card">
        <h4 style="font-size: 0.9375rem; font-weight: 700; margin-bottom: 12px;">Confidence & Verification</h4>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
          <span style="font-size: 0.8125rem; color: var(--text-muted);">Data Integrity Confidence</span>
          <span style="font-size: 0.875rem; font-weight: 800; color: var(--color-primary);">${confStr}</span>
        </div>
        <div class="progress-track" style="height: 10px;">
          <div class="progress-fill" style="width: ${confNum}%;"></div>
        </div>

        <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 8px;">
          Adheres to strict precedence hierarchy: Government data is immutable and cannot be overwritten by automated models.
        </p>
      </div>

      <div class="card">
        <h4 style="font-size: 0.9375rem; font-weight: 700; margin-bottom: 8px;">Source Link & Verification</h4>
        <p style="font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 10px;">
          ${sourceUrl}
        </p>
        ${data.notes ? `
          <div style="background-color: var(--color-bg); padding: 10px; border-radius: var(--radius-sm); font-size: 0.8125rem;">
            <strong>Notes:</strong> ${data.notes}
          </div>
        ` : ''}
      </div>

      <div class="card" style="background-color: #0f172a; color: #ffffff;">
        <h4 style="font-size: 0.875rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">AUDIT LEDGER STREAM</h4>
        <p style="font-size: 0.75rem; color: #94a3b8; line-height: 1.5;">
          Every ingestion and AI enrichment run is permanently committed to <code>/knowledge/college-knowledge.md</code> and <code>/knowledge/college-knowledge.jsonl</code> with atomic timestamps.
        </p>
      </div>
    `;

    backdrop.classList.remove('hidden');
    drawer.classList.remove('hidden');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  static close() {
    const drawer = document.getElementById('provenance-drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    if (!drawer || !backdrop) return;

    drawer.classList.add('hidden');
    drawer.setAttribute('aria-hidden', 'true');
    backdrop.classList.add('hidden');
    document.body.style.overflow = '';
  }
}
