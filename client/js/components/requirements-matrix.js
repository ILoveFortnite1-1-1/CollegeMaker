/**
 * Cross-School Requirements Matrix Component (Feature R7)
 * Renders cross-school requirements checklist matrix (schools as columns, requirements as rows)
 * with aggregate summary counts and interactive 1-click status toggling for all schools.
 */
import { API } from '../api.js?v=4.0';

export function renderRequirementsMatrix(data, options = {}) {
  const colleges = data?.colleges || [];
  const matrix = data?.matrix || [];
  const summaryCounts = data?.summary_counts || {};

  if (!colleges || colleges.length === 0) {
    return `
      <div class="card" style="padding: 32px; text-align: center; background: #fff;">
        <h4 style="color: var(--text-primary); margin: 0 0 8px 0; font-size: 1.1rem;">No Colleges to Track</h4>
        <p style="color: var(--text-muted); font-size: 0.875rem; margin: 0 0 16px 0;">
          Save colleges to your portfolio to generate a cross-school requirements checklist matrix.
        </p>
        <a href="#/colleges" class="btn btn-primary btn-sm">Browse Colleges</a>
      </div>
    `;
  }

  // Generate aggregate summary chips (clickable to mark done for all schools)
  const summaryChips = matrix
    .filter(row => row.total_schools_requiring > 0)
    .map(row => {
      const isComplete = row.completed_count >= row.total_schools_requiring;
      const chipBg = isComplete ? '#dcfce7' : '#eff6ff';
      const chipText = isComplete ? '#166534' : '#1e40af';
      const chipBorder = isComplete ? '#bbf7d0' : '#bfdbfe';

      return `
        <button type="button" class="summary-chip-btn" data-req-name="${encodeURIComponent(row.requirement_name)}" style="background: ${chipBg}; color: ${chipText}; border: 1px solid ${chipBorder}; padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; cursor: pointer; transition: all 0.15s ease;" title="Click to mark '${row.requirement_name}' done for all schools in 1 click">
          <span>${row.requirement_name}:</span>
          <strong>${row.total_schools_requiring} ${row.total_schools_requiring === 1 ? 'school' : 'schools'}</strong>
          <span style="opacity: 0.85;">(${row.completed_count} done)</span>
          <span style="font-size: 0.7rem; font-weight: 700; background: ${isComplete ? '#166534' : '#2563eb'}; color: #fff; padding: 1px 6px; border-radius: 10px; margin-left: 2px;">
            ${isComplete ? '✓ Done' : '✓ Mark All'}
          </span>
        </button>
      `;
    });

  return `
    <div class="requirements-matrix-widget card" style="padding: 24px; background: #ffffff; border: 1px solid var(--color-border); border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 24px;">
      <!-- Matrix Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin: 0;">
              Cross-School Requirements Matrix
            </h3>
            <span style="font-size: 0.75rem; font-weight: 700; background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px;">
              ${colleges.length} ${colleges.length === 1 ? 'School' : 'Schools'}
            </span>
          </div>
          <p style="font-size: 0.8125rem; color: var(--text-muted); margin: 4px 0 0 0;">
            Compare application components across colleges. Click a requirement or "✓ Done for All" to mark it done for every school in 1 click.
          </p>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <button type="button" id="btn-matrix-all-done" class="btn btn-sm btn-primary" style="font-size: 0.75rem; padding: 5px 12px; background: #059669; border-color: #059669; font-weight: 600;" title="Mark all requirements done across all schools in one click">
            ✓ Mark All Done
          </button>
          <button type="button" id="btn-matrix-all-clear" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 5px 12px;" title="Reset all requirements to needed">
            Clear All
          </button>
          <button type="button" id="btn-add-custom-matrix-req" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 5px 12px;">
            + Add Requirement
          </button>
        </div>
      </div>

      <!-- Aggregate Summary Strip (Clickable Chips) -->
      ${summaryChips.length > 0 ? `
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; padding-bottom: 14px; border-bottom: 1px solid var(--color-border-subtle);">
          ${summaryChips.join('')}
        </div>
      ` : ''}

      <!-- Interactive Matrix Table -->
      <div style="overflow-x: auto; max-width: 100%; border: 1px solid var(--color-border); border-radius: 8px;">
        <table class="matrix-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8125rem;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 2px solid var(--color-border);">
              <th style="padding: 12px 16px; font-weight: 700; color: var(--text-primary); min-width: 260px; position: sticky; left: 0; background: #f8fafc; z-index: 2; border-right: 1px solid var(--color-border);">
                Requirement (Click to Mark Done)
              </th>
              ${colleges.map(c => `
                <th style="padding: 12px 14px; font-weight: 700; color: var(--text-primary); min-width: 140px; text-align: center; border-right: 1px solid var(--color-border-subtle);">
                  <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                    <span style="font-size: 0.8125rem; line-height: 1.2;">${c.name}</span>
                    <button type="button" class="btn-toggle-col-all" data-college-id="${c.id}" title="Mark all requirements done for ${c.name} in one click" style="background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; border-radius: 4px; padding: 2px 6px; font-size: 0.6875rem; font-weight: 600; cursor: pointer;">
                      ✓ All Done
                    </button>
                  </div>
                </th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            ${matrix.length === 0 ? `
              <tr>
                <td colspan="${colleges.length + 1}" style="padding: 24px; text-align: center; color: var(--text-muted);">
                  No specific requirements recorded yet. Click "+ Add Requirement" above.
                </td>
              </tr>
            ` : matrix.map(row => {
              const isAllDone = row.completed_count >= row.total_schools_requiring && row.total_schools_requiring > 0;
              return `
                <tr style="border-bottom: 1px solid var(--color-border-subtle); transition: background 0.15s ease;">
                  <!-- Row Title with 1-Click Action -->
                  <td style="padding: 10px 16px; font-weight: 600; color: var(--text-primary); position: sticky; left: 0; background: #ffffff; z-index: 1; border-right: 1px solid var(--color-border);">
                    <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                      <div style="display: flex; flex-direction: column; align-items: flex-start; gap: 2px;">
                        <button type="button" class="matrix-req-name-btn" data-req-name="${encodeURIComponent(row.requirement_name)}" data-all-done="${isAllDone ? 'true' : 'false'}" title="Click to mark '${row.requirement_name}' done for all schools in 1 click" style="background: none; border: none; padding: 0; font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); text-align: left; cursor: pointer; text-decoration: underline; text-decoration-color: #cbd5e1; text-underline-offset: 3px;">
                          ${row.requirement_name}
                        </button>
                        <span style="font-size: 0.7rem; font-weight: 500; color: var(--text-muted);">
                          ${row.completed_count}/${row.total_schools_requiring} completed
                        </span>
                      </div>
                      <button type="button" class="btn-toggle-row-all" data-req-name="${encodeURIComponent(row.requirement_name)}" data-all-done="${isAllDone ? 'true' : 'false'}" title="Click to mark '${row.requirement_name}' done for all schools in 1 click" style="border: 1px solid ${isAllDone ? '#bbf7d0' : '#bfdbfe'}; background: ${isAllDone ? '#dcfce7' : '#eff6ff'}; color: ${isAllDone ? '#15803d' : '#1d4ed8'}; border-radius: 4px; padding: 3px 8px; font-size: 0.7rem; font-weight: 700; cursor: pointer; white-space: nowrap; transition: all 0.15s ease;">
                        ${isAllDone ? '✓ All Done' : '✓ Done for All'}
                      </button>
                    </div>
                  </td>

                  <!-- Cells per College -->
                  ${colleges.map(c => {
                    const status = row.schools?.[c.id] || { required: false, completed: false, id: null };
                    let cellMarkup = '';

                    if (status.required && status.completed) {
                      cellMarkup = `
                        <button type="button" class="matrix-cell-btn btn-done" data-college-id="${c.id}" data-item-id="${status.id || ''}" data-req-name="${encodeURIComponent(row.requirement_name)}" data-completed="true" data-required="true" style="border: none; cursor: pointer; background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; border-radius: 6px; padding: 4px 10px; font-size: 0.75rem; font-weight: 700; width: 100%; transition: all 0.15s ease;" title="Completed. Click to mark needed.">
                          ✓ Done
                        </button>
                      `;
                    } else if (status.required && !status.completed) {
                      cellMarkup = `
                        <button type="button" class="matrix-cell-btn btn-needed" data-college-id="${c.id}" data-item-id="${status.id || ''}" data-req-name="${encodeURIComponent(row.requirement_name)}" data-completed="false" data-required="true" style="border: none; cursor: pointer; background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; border-radius: 6px; padding: 4px 10px; font-size: 0.75rem; font-weight: 700; width: 100%; transition: all 0.15s ease;" title="Required. Click to mark completed.">
                          ○ Needed
                        </button>
                      `;
                    } else {
                      cellMarkup = `
                        <button type="button" class="matrix-cell-btn btn-optional" data-college-id="${c.id}" data-item-id="${status.id || ''}" data-req-name="${encodeURIComponent(row.requirement_name)}" data-completed="false" data-required="false" style="border: none; cursor: pointer; background: #f8fafc; color: #64748b; border: 1px dashed var(--color-border); border-radius: 6px; padding: 4px 10px; font-size: 0.75rem; width: 100%; transition: all 0.15s ease;" title="Not required. Click to activate.">
                          — Optional
                        </button>
                      `;
                    }

                    return `
                      <td style="padding: 8px 10px; text-align: center; border-right: 1px solid var(--color-border-subtle);">
                        ${cellMarkup}
                      </td>
                    `;
                  }).join('')}
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/**
 * Bind interactive toggles for matrix cells, bulk buttons, chips, and add requirement
 */
export function bindRequirementsMatrixEvents(container, onUpdate) {
  if (!container) return;

  // Add custom requirement modal/prompt
  const addBtn = container.querySelector('#btn-add-custom-matrix-req');
  if (addBtn) {
    addBtn.addEventListener('click', async () => {
      const reqName = prompt('Enter requirement name (e.g., "Arts Portfolio", "Alumni Interview", "CSS Profile"):');
      if (!reqName || !reqName.trim()) return;

      try {
        const matrixData = await API.getRequirementsMatrix();
        const colleges = matrixData?.colleges || [];
        if (colleges.length === 0) return;

        for (const c of colleges) {
          await API.addChecklistItem(c.id, {
            name: reqName.trim(),
            required: true,
            completed: false
          });
        }

        if (window.app?.showToast) {
          window.app.showToast(`Added "${reqName.trim()}" across saved schools.`, 'success');
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to add custom requirement', err);
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Failed to add requirement', 'error');
        }
      }
    });
  }

  // 1-Click "Mark All Done" across all schools and requirements
  const allDoneBtn = container.querySelector('#btn-matrix-all-done');
  if (allDoneBtn) {
    allDoneBtn.addEventListener('click', async () => {
      allDoneBtn.disabled = true;
      allDoneBtn.style.opacity = '0.6';
      try {
        await API.toggleAllRequirements(true);
        if (window.app?.showToast) {
          window.app.showToast('Marked all requirements done across all schools.', 'success');
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to mark all done', err);
        allDoneBtn.disabled = false;
        allDoneBtn.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  }

  // 1-Click "Clear All" across all schools and requirements
  const allClearBtn = container.querySelector('#btn-matrix-all-clear');
  if (allClearBtn) {
    allClearBtn.addEventListener('click', async () => {
      allClearBtn.disabled = true;
      allClearBtn.style.opacity = '0.6';
      try {
        await API.toggleAllRequirements(false);
        if (window.app?.showToast) {
          window.app.showToast('Reset all requirements to needed.', 'info');
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to clear all', err);
        allClearBtn.disabled = false;
        allClearBtn.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  }

  // 1-Click Summary Chips: click a chip to mark that requirement done for all schools
  const chipBtns = container.querySelectorAll('.summary-chip-btn');
  chipBtns.forEach(chip => {
    chip.addEventListener('click', async () => {
      const reqName = decodeURIComponent(chip.getAttribute('data-req-name') || '');
      if (!reqName) return;
      chip.disabled = true;
      chip.style.opacity = '0.6';
      try {
        await API.toggleRequirementAll(reqName, true);
        if (window.app?.showToast) {
          window.app.showToast(`Marked "${reqName}" done for all schools.`, 'success');
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to toggle chip requirement', err);
        chip.disabled = false;
        chip.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  });

  // 1-Click Row Actions: click requirement name or "✓ Done for All" button
  const rowBtns = container.querySelectorAll('.btn-toggle-row-all, .matrix-req-name-btn');
  rowBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const reqName = decodeURIComponent(btn.getAttribute('data-req-name') || '');
      const allDone = btn.getAttribute('data-all-done') === 'true';
      if (!reqName) return;

      btn.disabled = true;
      btn.style.opacity = '0.6';

      try {
        // Toggle target state: if all done, mark incomplete; otherwise mark done
        const targetState = allDone ? false : true;
        await API.toggleRequirementAll(reqName, targetState);
        if (window.app?.showToast) {
          window.app.showToast(
            targetState
              ? `Marked "${reqName}" done for all schools.`
              : `Marked "${reqName}" as needed for all schools.`,
            'success'
          );
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to toggle row requirement for all', err);
        btn.disabled = false;
        btn.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  });

  // 1-Click Column Action: click "✓ All Done" on a college header to mark all requirements for that school
  const colBtns = container.querySelectorAll('.btn-toggle-col-all');
  colBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const collegeId = btn.getAttribute('data-college-id');
      if (!collegeId) return;

      btn.disabled = true;
      btn.style.opacity = '0.6';

      try {
        await API.toggleCollegeChecklistAll(collegeId, true);
        if (window.app?.showToast) {
          window.app.showToast('Marked all requirements done for this school.', 'success');
        }
        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to toggle college requirements', err);
        btn.disabled = false;
        btn.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  });

  // Individual Cell toggle buttons
  const cellBtns = container.querySelectorAll('.matrix-cell-btn');
  cellBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const collegeId = btn.getAttribute('data-college-id');
      const itemId = btn.getAttribute('data-item-id');
      const reqName = decodeURIComponent(btn.getAttribute('data-req-name') || '');
      const isCompleted = btn.getAttribute('data-completed') === 'true';
      const isRequired = btn.getAttribute('data-required') === 'true';

      btn.disabled = true;
      btn.style.opacity = '0.5';

      try {
        if (itemId && itemId !== '') {
          if (!isRequired) {
            await API.updateChecklistItem(collegeId, itemId, { required: true, completed: false });
          } else {
            await API.updateChecklistItem(collegeId, itemId, { completed: !isCompleted });
          }
        } else {
          await API.addChecklistItem(collegeId, {
            name: reqName,
            required: true,
            completed: true
          });
        }

        if (typeof onUpdate === 'function') {
          onUpdate();
        }
      } catch (err) {
        console.error('Failed to toggle matrix item', err);
        btn.disabled = false;
        btn.style.opacity = '1';
        if (window.app?.showToast) {
          window.app.showToast(err.message || 'Update failed', 'error');
        }
      }
    });
  });
}

