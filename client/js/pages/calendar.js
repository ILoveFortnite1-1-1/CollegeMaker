/**
 * Deadline Calendar Page View (Route: #/calendar)
 * Feature R2: Visual month-view calendar aggregating application deadlines
 * (priority, regular, FAFSA, CSS Profile, scholarships, decision dates)
 * with 4-tier color coding, month switcher, and 14-day upcoming deadlines sidebar.
 */
import { API } from '../api.js?v=4.0';

export const CalendarPage = {
  currentDate: new Date(),
  selectedYear: new Date().getFullYear(),
  selectedMonth: new Date().getMonth(), // 0-indexed
  currentEvents: [],

  getEventGroupInfo(evt) {
    const rawTitle = (evt.title || '').trim();
    const lower = rawTitle.toLowerCase();

    let cleanTitle = rawTitle;
    let groupKey = '';

    if (lower.includes('early action') || lower.includes('priority / early') || lower.includes('early decision') || lower.includes('priority deadline')) {
      cleanTitle = 'Early Action / Priority';
      groupKey = 'early_action';
    } else if (lower.includes('regular decision')) {
      cleanTitle = 'Regular Decision';
      groupKey = 'regular_decision';
    } else if (lower.includes('fafsa')) {
      cleanTitle = 'FAFSA Priority Aid';
      groupKey = 'fafsa_aid';
    } else if (lower.includes('css profile')) {
      cleanTitle = 'CSS Profile Aid';
      groupKey = 'css_profile';
    } else if (lower.includes('merit scholarship')) {
      cleanTitle = 'Merit Scholarships';
      groupKey = 'merit_scholarships';
    } else if (lower.includes('scholarship')) {
      cleanTitle = rawTitle.replace(/\s*(Deadline|Milestone)$/i, '').trim() || 'Scholarships';
      groupKey = cleanTitle.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    } else if (lower.includes('decision notification') || lower.includes('admissions decision') || lower.includes('decision date') || lower.includes('decision release')) {
      cleanTitle = 'Admissions Decisions';
      groupKey = 'admissions_decisions';
    } else if (lower.includes('candidate reply') || lower.includes('decision day')) {
      cleanTitle = 'Candidate Reply Date';
      groupKey = 'reply_date';
    } else if (lower.includes('common application opens') || lower.includes('common app open')) {
      cleanTitle = 'Common App Opens';
      groupKey = 'common_app';
    } else {
      cleanTitle = rawTitle.replace(/\s*(Deadline|Milestone)$/i, '').trim() || rawTitle;
      groupKey = cleanTitle.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    }

    const category = evt.deadline_type || evt.category || 'app_deadline';
    return {
      groupKey: `${category}::${groupKey}`,
      cleanTitle,
      category
    };
  },

  async render(container, state, options = {}) {
    if (!options?.silent) {
      container.innerHTML = `
        <div class="loading-screen">
          <div class="spinner"></div>
          <p class="loading-text">Loading deadline calendar…</p>
        </div>
      `;
    }

    try {
      const [calendarData, portfolioData] = await Promise.all([
        API.getCalendar().catch(() => ({ events: [], upcoming_14_days: [] })),
        API.getPortfolio().catch(() => ({ saved_colleges: [] }))
      ]);

      const savedColleges = (portfolioData.portfolio && portfolioData.portfolio.colleges)
        || portfolioData.saved_colleges
        || portfolioData.colleges
        || portfolioData.items
        || (window.app?.getSavedColleges ? window.app.getSavedColleges() : [])
        || [];
      const collegeEvents = calendarData.events || [];
      const nationalEvents = calendarData.national_milestones || [];
      const hasSaved = savedColleges.length > 0;

      // Determine which events to display: merge national roadmap milestones with college deadlines
      const showNational = this.showNational !== false;
      let events = [];
      if (!hasSaved) {
        events = nationalEvents;
      } else if (showNational) {
        events = [...collegeEvents, ...nationalEvents];
      } else {
        events = collegeEvents;
      }
      events.sort((a, b) => (a.date > b.date ? 1 : (a.date < b.date ? -1 : 0)));
      this.currentEvents = events;

      // Group upcoming deadlines falling on same date & same type
      const upcoming14 = events.filter(e => 0 <= e.days_remaining && e.days_remaining <= 14);
      const upcomingGroupsMap = new Map();
      upcoming14.forEach(evt => {
        const info = this.getEventGroupInfo(evt);
        const uKey = `${evt.date}::${info.groupKey}`;
        if (!upcomingGroupsMap.has(uKey)) {
          upcomingGroupsMap.set(uKey, {
            key: uKey,
            date: evt.date,
            days_remaining: evt.days_remaining,
            cleanTitle: info.cleanTitle,
            category: info.category,
            category_label: evt.category_label || (info.category === 'app_deadline' ? 'Application Deadline' : info.category === 'financial_aid' ? 'Financial Aid' : info.category === 'scholarship' ? 'Scholarship' : 'Admissions Decision'),
            color: evt.color,
            items: []
          });
        }
        upcomingGroupsMap.get(uKey).items.push(evt);
      });
      const upcomingGroups = Array.from(upcomingGroupsMap.values());

      // If there are future events and user hasn't toggled month yet, default to first upcoming event's month
      if (events.length > 0 && !options.keepMonth) {
        const upcomingFirst = events.find(e => !e.is_past) || events[0];
        if (upcomingFirst && upcomingFirst.date) {
          const parts = upcomingFirst.date.split('-');
          if (parts.length >= 2) {
            this.selectedYear = parseInt(parts[0], 10);
            this.selectedMonth = parseInt(parts[1], 10) - 1;
          }
        }
      }

      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const monthTitle = `${monthNames[this.selectedMonth]} ${this.selectedYear}`;

      container.innerHTML = `
        <div class="calendar-page" style="max-width: 1200px; margin: 0 auto; padding-bottom: 60px;">
          <!-- Page Header -->
          <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px; flex-wrap: wrap; gap: 16px;">
            <div>
              <span style="font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-primary);">Admissions Roadmap</span>
              <h1 style="font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 4px 0;">Application Deadline Calendar</h1>
              <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">
                ${hasSaved
                  ? `Important dates automatically pulled across ${savedColleges.length} colleges, plus key national financial aid & decision milestones.`
                  : `Standard national admissions, FAFSA, and decision milestones pre-loaded below. Save colleges to track school-specific deadlines!`
                }
              </p>
            </div>

            <div style="display: flex; align-items: center; gap: 10px;">
              ${hasSaved ? `
                <a href="#/tracker" class="btn btn-secondary btn-sm" style="display: inline-flex; align-items: center; gap: 6px;">
                  <span>Set Dates in App Tracker</span> →
                </a>
              ` : `
                <a href="#/colleges" class="btn btn-primary btn-sm" style="display: inline-flex; align-items: center; gap: 6px;">
                  <span>+ Save Colleges to Track</span>
                </a>
              `}
            </div>
          </div>

          ${!hasSaved ? `
            <!-- Active National Roadmap Banner when no colleges saved -->
            <div class="card" style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background: #16a34a; color: #fff; font-size: 0.85rem; font-weight: 700;">★</span>
                <div>
                  <strong style="color: #15803d; font-size: 0.9rem; display: block;">National Admissions & Financial Aid Calendar Active</strong>
                  <span style="color: #166534; font-size: 0.8125rem;">Standard nationwide admissions deadlines, FAFSA, and decision dates are automatically loaded. Save colleges to track school-specific deadlines!</span>
                </div>
              </div>
              <a href="#/colleges" class="btn btn-sm btn-primary" style="font-size: 0.8125rem;">+ Discover Colleges</a>
            </div>
          ` : ''}

          <!-- Color Legend Bar -->
          <div class="calendar-legend card" style="padding: 12px 18px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; background: #fff; border: 1px solid var(--color-border); border-radius: 10px;">
            <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;">Categories:</span>
              <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap; font-size: 0.8125rem;">
                <span style="display: inline-flex; align-items: center; gap: 6px;">
                  <span style="width: 10px; height: 10px; border-radius: 50%; background: #2563eb;"></span>
                  <strong style="color: #1e40af;">Application (ED/EA/RD)</strong>
                </span>
                <span style="display: inline-flex; align-items: center; gap: 6px;">
                  <span style="width: 10px; height: 10px; border-radius: 50%; background: #059669;"></span>
                  <strong style="color: #166534;">Financial Aid (FAFSA/CSS)</strong>
                </span>
                <span style="display: inline-flex; align-items: center; gap: 6px;">
                  <span style="width: 10px; height: 10px; border-radius: 50%; background: #d97706;"></span>
                  <strong style="color: #92400e;">Scholarships</strong>
                </span>
                <span style="display: inline-flex; align-items: center; gap: 6px;">
                  <span style="width: 10px; height: 10px; border-radius: 50%; background: #7c3aed;"></span>
                  <strong style="color: #6b21a8;">Decision Date</strong>
                </span>
              </div>
            </div>

            ${hasSaved ? `
              <label style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.8125rem; font-weight: 600; color: var(--text-secondary); cursor: pointer; user-select: none;">
                <input type="checkbox" id="toggle-national-milestones" ${this.showNational !== false ? 'checked' : ''} style="cursor: pointer;" />
                <span>Include National Roadmap Dates</span>
              </label>
            ` : ''}
          </div>

          <!-- Main 2-Column Layout (Calendar Grid + 14-Day Sidebar) -->
          <div style="display: grid; grid-template-columns: 1fr 340px; gap: 24px; align-items: start;">
            
            <!-- Left: Calendar Month View -->
            <div class="calendar-card card" style="background: #fff; border: 1px solid var(--color-border); border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
              <!-- Month Switcher Header -->
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-subtle);">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <button type="button" id="btn-prev-month" class="btn btn-sm btn-ghost" style="padding: 6px 12px; font-weight: 700;" aria-label="Previous Month">‹ Prev</button>
                  <h2 style="font-size: 1.25rem; font-weight: 800; color: var(--text-primary); margin: 0; min-width: 180px; text-align: center;">
                    ${monthTitle}
                  </h2>
                  <button type="button" id="btn-next-month" class="btn btn-sm btn-ghost" style="padding: 6px 12px; font-weight: 700;" aria-label="Next Month">Next ›</button>
                </div>

                <button type="button" id="btn-today-month" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 5px 12px;">
                  Today
                </button>
              </div>

              <!-- Month Grid -->
              <div class="calendar-grid-wrapper">
                ${this.renderMonthGrid(this.selectedYear, this.selectedMonth, events)}
              </div>
            </div>

            <!-- Right: 14-Day Upcoming Deadlines Sidebar -->
            <div class="calendar-sidebar">
              <div class="card" style="background: #fff; border: 1px solid var(--color-border); border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--color-border-subtle);">
                  <h3 style="font-size: 1rem; font-weight: 800; color: var(--text-primary); margin: 0;">
                    Next 14 Days
                  </h3>
                  <span style="font-size: 0.75rem; font-weight: 700; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px;">
                    ${upcoming14.length} Due Soon
                  </span>
                </div>

                <div class="upcoming-deadlines-list" style="display: flex; flex-direction: column; gap: 12px;">
                  ${upcomingGroups.length === 0 ? `
                    <div style="text-align: center; padding: 28px 12px; color: var(--text-muted);">
                      <p style="font-size: 0.875rem; margin: 0 0 6px 0;">No upcoming deadlines in the next 14 days.</p>
                      <span style="font-size: 0.75rem;">All upcoming dates appear on the monthly grid.</span>
                    </div>
                  ` : upcomingGroups.map(group => {
                    let urgencyBadge = '';
                    if (group.days_remaining === 0) {
                      urgencyBadge = '<span style="background: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-weight: 800; font-size: 0.7rem;">DUE TODAY!</span>';
                    } else if (group.days_remaining === 1) {
                      urgencyBadge = '<span style="background: #fef3c7; color: #d97706; padding: 2px 6px; border-radius: 4px; font-weight: 800; font-size: 0.7rem;">TOMORROW</span>';
                    } else {
                      urgencyBadge = `<span style="background: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.7rem;">In ${group.days_remaining} days</span>`;
                    }

                    const categoryColors = {
                      app_deadline: '#2563eb',
                      financial_aid: '#059669',
                      scholarship: '#d97706',
                      decision: '#7c3aed'
                    };
                    const borderLeft = categoryColors[group.category] || '#2563eb';

                    return `
                      <div class="upcoming-item" style="padding: 10px 12px; background: #f8fafc; border-left: 3px solid ${borderLeft}; border-radius: 6px; border-top: 1px solid var(--color-border-subtle); border-right: 1px solid var(--color-border-subtle); border-bottom: 1px solid var(--color-border-subtle);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                          <span style="font-size: 0.75rem; font-weight: 700; color: var(--text-secondary);">${group.date}</span>
                          ${urgencyBadge}
                        </div>
                        <div style="font-size: 0.875rem; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; display: flex; align-items: center; justify-content: space-between;">
                          <span>${group.cleanTitle}</span>
                          ${group.items.length > 1 ? `
                            <span style="background: #e2e8f0; color: #334155; font-size: 0.6875rem; font-weight: 800; padding: 1px 6px; border-radius: 999px;">
                              ${group.items.length} schools
                            </span>
                          ` : ''}
                        </div>
                        <div style="font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px;">
                          ${group.items.length === 1 ? `
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                              <span>${group.items[0].college_name}</span>
                              ${group.items[0].college_id !== 'national'
                                ? `<a href="#/colleges/${group.items[0].college_id}" style="font-size: 0.75rem; color: var(--color-primary); font-weight: 600;">View Profile →</a>`
                                : `<span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">National Cycle</span>`
                              }
                            </div>
                          ` : `
                            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 2px;">
                              ${group.items.map(e => `
                                ${e.college_id !== 'national' ? `
                                  <a href="#/colleges/${e.college_id}" style="font-size: 0.72rem; background: #ffffff; border: 1px solid var(--color-border); color: var(--text-primary); padding: 1px 6px; border-radius: 4px; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 2px;">
                                    ${e.college_name.split(' ')[0]} <span style="color: var(--color-primary); font-size: 0.65rem;">→</span>
                                  </a>
                                ` : `
                                  <span style="font-size: 0.72rem; background: #e2e8f0; color: #475569; padding: 1px 6px; border-radius: 4px; font-weight: 600;">
                                    National
                                  </span>
                                `}
                              `).join('')}
                            </div>
                          `}
                        </div>
                      </div>
                    `;
                  }).join('')}
                </div>
              </div>

              <!-- Total Events Counter Summary -->
              <div class="card" style="margin-top: 16px; background: #f8fafc; border: 1px solid var(--color-border); border-radius: 10px; padding: 14px 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8125rem;">
                  <span style="color: var(--text-secondary);">Total Recorded Deadlines:</span>
                  <strong style="color: var(--text-primary); font-family: var(--font-mono);">${events.length}</strong>
                </div>
              </div>
            </div>

          </div>

          <!-- Interactive Day Details Modal -->
          <div id="calendar-day-modal" class="modal-backdrop" style="display: none; position: fixed; inset: 0; background: rgba(15,23,42,0.6); z-index: 9999; align-items: center; justify-content: center; padding: 20px;">
            <div class="card modal-dialog" style="max-width: 520px; width: 100%; background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); max-height: 85vh; overflow-y: auto;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-subtle);">
                <h3 id="day-modal-title" style="margin: 0; font-size: 1.15rem; font-weight: 800; color: var(--text-primary);">Deadlines</h3>
                <button type="button" id="btn-close-day-modal" class="btn btn-ghost" style="font-size: 1.25rem; padding: 4px 8px; line-height: 1;">✕</button>
              </div>
              <div id="day-modal-body" style="display: flex; flex-direction: column; gap: 10px;">
                <!-- Populated dynamically on day click -->
              </div>
              <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
                <button type="button" id="btn-dismiss-day-modal" class="btn btn-secondary btn-sm">Close</button>
              </div>
            </div>
          </div>

        </div>
      `;

      CalendarPage.bindEvents(container, state);

    } catch (err) {
      console.error('Failed to render deadline calendar', err);
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px; max-width: 600px; margin: 40px auto;">
          <h3 style="color: var(--color-destructive); font-size: 1.25rem;">Unable to load calendar</h3>
          <p style="color: var(--text-secondary); margin: 8px 0 20px;">${err.message}</p>
          <button type="button" class="btn btn-primary" onclick="window.location.reload()">Retry</button>
        </div>
      `;
    }
  },

  renderMonthGrid(year, month, events) {
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sun, 1 = Mon ...
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const todayDate = today.getDate();

    // Group events by day in this month
    const monthPrefix = `${year}-${String(month + 1).padStart(2, '0')}`;
    const eventsByDay = {};
    events.forEach(evt => {
      if (evt.date && evt.date.startsWith(monthPrefix)) {
        const dayNum = parseInt(evt.date.substring(8, 10), 10);
        if (!eventsByDay[dayNum]) eventsByDay[dayNum] = [];
        eventsByDay[dayNum].push(evt);
      }
    });

    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    let html = `
      <table class="calendar-table" style="width: 100%; border-collapse: collapse; table-layout: fixed;">
        <thead>
          <tr>
            ${weekdays.map(w => `
              <th style="padding: 8px 4px; text-align: center; font-size: 0.75rem; font-weight: 700; color: var(--text-muted); border-bottom: 1px solid var(--color-border);">
                ${w}
              </th>
            `).join('')}
          </tr>
        </thead>
        <tbody>
          <tr>
    `;

    // Padding for days before the 1st
    for (let i = 0; i < firstDayIndex; i++) {
      html += `<td style="padding: 4px; height: 95px; background: #fcfcfc; border: 1px solid var(--color-border-subtle); vertical-align: top; opacity: 0.3;"></td>`;
    }

    let currentDayIndex = firstDayIndex;

    for (let day = 1; day <= daysInMonth; day++) {
      if (currentDayIndex % 7 === 0 && day > 1) {
        html += `</tr><tr>`;
      }

      const isToday = isCurrentMonth && day === todayDate;
      const dayEvents = eventsByDay[day] || [];

      // Deduplicate generic national milestones if specific colleges already have that deadline on this day
      const dayColleges = dayEvents.filter(e => !e.is_national);
      const dayCollegesHasType = new Set(dayColleges.map(e => this.getEventGroupInfo(e).groupKey));
      
      const filteredDayEvents = dayEvents.filter(e => {
        if (e.is_national && dayCollegesHasType.has(this.getEventGroupInfo(e).groupKey)) {
          return false;
        }
        return true;
      });

      // Group multiple events of the same type on this day
      const groupedMap = new Map();
      filteredDayEvents.forEach(evt => {
        const info = this.getEventGroupInfo(evt);
        if (!groupedMap.has(info.groupKey)) {
          groupedMap.set(info.groupKey, {
            groupKey: info.groupKey,
            cleanTitle: info.cleanTitle,
            category: info.category,
            items: []
          });
        }
        groupedMap.get(info.groupKey).items.push(evt);
      });
      const dayGroups = Array.from(groupedMap.values());
      const cellDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

      html += `
        <td 
          class="calendar-day-cell" 
          data-day="${day}" 
          data-date="${cellDateStr}"
          data-has-events="${filteredDayEvents.length > 0}"
          style="padding: 6px; height: 105px; min-height: 105px; border: 1px solid var(--color-border); vertical-align: top; background: ${isToday ? '#f0fdf4' : '#fff'}; transition: background 0.15s ease; ${filteredDayEvents.length > 0 ? 'cursor: pointer;' : ''}"
        >
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 0.8125rem; font-weight: ${isToday ? '800' : '600'}; color: ${isToday ? '#15803d' : 'var(--text-primary)'}; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; ${isToday ? 'background: #dcfce7; border-radius: 50%;' : ''}">
              ${day}
            </span>
            ${filteredDayEvents.length > 0 ? `
              <span style="font-size: 0.65rem; font-weight: 700; background: #f1f5f9; color: var(--text-secondary); padding: 1px 5px; border-radius: 4px;" title="${filteredDayEvents.length} total events on this date">
                ${filteredDayEvents.length}
              </span>
            ` : ''}
          </div>

          <div style="display: flex; flex-direction: column; gap: 3px; max-height: 75px; overflow-y: auto;">
            ${dayGroups.map(group => {
              const bgColors = {
                app_deadline: '#dbeafe',
                financial_aid: '#dcfce7',
                scholarship: '#fef3c7',
                decision: '#f3e8ff'
              };
              const textColors = {
                app_deadline: '#1e40af',
                financial_aid: '#166534',
                scholarship: '#92400e',
                decision: '#7e22ce'
              };
              const borderColors = {
                app_deadline: '#2563eb',
                financial_aid: '#059669',
                scholarship: '#d97706',
                decision: '#7c3aed'
              };
              const badgeBgs = {
                app_deadline: '#bfdbfe',
                financial_aid: '#bbf7d0',
                scholarship: '#fde68a',
                decision: '#e9d5ff'
              };
              const bg = bgColors[group.category] || '#dbeafe';
              const text = textColors[group.category] || '#1e40af';
              const border = borderColors[group.category] || '#2563eb';
              const badgeBg = badgeBgs[group.category] || '#bfdbfe';

              if (group.items.length > 1) {
                // Multiple colleges have the same deadline: display the name and count badge next to it!
                const collegeList = group.items.map(e => e.is_national ? '• National Roadmap' : `• ${e.college_name}`).join('\n');
                const tooltip = `${group.cleanTitle} (${group.items.length} schools):\n${collegeList}\n\nClick to view full details`;

                return `
                  <div 
                    class="calendar-event-pill calendar-event-grouped" 
                    data-day="${day}"
                    data-date="${cellDateStr}"
                    title="${tooltip}"
                    style="background: ${bg}; color: ${text}; padding: 2px 6px; border-radius: 4px; font-size: 0.6875rem; font-weight: 700; cursor: pointer; border-left: 3px solid ${border}; display: flex; align-items: center; justify-content: space-between; gap: 4px; line-height: 1.3;"
                  >
                    <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${group.cleanTitle}</span>
                    <span style="background: ${badgeBg}; color: ${text}; padding: 0.5px 5px; border-radius: 999px; font-size: 0.65rem; font-weight: 800; line-height: 1; flex-shrink: 0;">${group.items.length}</span>
                  </div>
                `;
              } else {
                // Single college event on this day
                const evt = group.items[0];
                const schoolShort = evt.is_national ? 'National' : evt.college_name.split(' ')[0];
                const tooltip = `${evt.college_name}: ${evt.title}\n\nClick to view full details`;

                return `
                  <div 
                    class="calendar-event-pill" 
                    data-day="${day}"
                    data-date="${cellDateStr}"
                    title="${tooltip}"
                    style="background: ${bg}; color: ${text}; padding: 2px 6px; border-radius: 4px; font-size: 0.6875rem; font-weight: 700; cursor: pointer; border-left: 3px solid ${border}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.3;"
                  >
                    ${schoolShort}: ${group.cleanTitle}
                  </div>
                `;
              }
            }).join('')}
          </div>
        </td>
      `;

      currentDayIndex++;
    }

    // Padding for end of month
    const remainingDays = (7 - (currentDayIndex % 7)) % 7;
    for (let i = 0; i < remainingDays; i++) {
      html += `<td style="padding: 4px; height: 95px; background: #fcfcfc; border: 1px solid var(--color-border-subtle); vertical-align: top; opacity: 0.3;"></td>`;
    }

    html += `
          </tr>
        </tbody>
      </table>
    `;

    return html;
  },

  bindEvents(container, state) {
    const prevBtn = container.querySelector('#btn-prev-month');
    const nextBtn = container.querySelector('#btn-next-month');
    const todayBtn = container.querySelector('#btn-today-month');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.selectedMonth === 0) {
          this.selectedMonth = 11;
          this.selectedYear -= 1;
        } else {
          this.selectedMonth -= 1;
        }
        this.render(container, state, { silent: true, keepMonth: true });
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.selectedMonth === 11) {
          this.selectedMonth = 0;
          this.selectedYear += 1;
        } else {
          this.selectedMonth += 1;
        }
        this.render(container, state, { silent: true, keepMonth: true });
      });
    }

    if (todayBtn) {
      todayBtn.addEventListener('click', () => {
        const now = new Date();
        this.selectedYear = now.getFullYear();
        this.selectedMonth = now.getMonth();
        this.render(container, state, { silent: true, keepMonth: true });
      });
    }

    const toggleNat = container.querySelector('#toggle-national-milestones');
    if (toggleNat) {
      toggleNat.addEventListener('change', () => {
        this.showNational = toggleNat.checked;
        this.render(container, state, { silent: true, keepMonth: true });
      });
    }

    // Day Details Modal setup
    const dayModal = container.querySelector('#calendar-day-modal');
    const dayModalTitle = container.querySelector('#day-modal-title');
    const dayModalBody = container.querySelector('#day-modal-body');
    const closeDayModalBtn = container.querySelector('#btn-close-day-modal');
    const dismissDayModalBtn = container.querySelector('#btn-dismiss-day-modal');

    const closeDayModal = () => {
      if (dayModal) dayModal.style.display = 'none';
    };

    if (closeDayModalBtn) closeDayModalBtn.addEventListener('click', closeDayModal);
    if (dismissDayModalBtn) dismissDayModalBtn.addEventListener('click', closeDayModal);
    if (dayModal) {
      dayModal.addEventListener('click', (e) => {
        if (e.target === dayModal) closeDayModal();
      });
    }

    const openDayModal = (targetDate) => {
      if (!dayModal || !targetDate) return;
      const dayEvents = (this.currentEvents || []).filter(e => e.date === targetDate);
      if (dayEvents.length === 0) return;

      const [yr, mo, da] = targetDate.split('-');
      const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      const formattedDate = `${monthNames[parseInt(mo, 10) - 1]} ${parseInt(da, 10)}, ${yr}`;

      dayModalTitle.textContent = `${formattedDate} (${dayEvents.length} Event${dayEvents.length === 1 ? '' : 's'})`;

      const categoryColors = {
        app_deadline: { border: '#2563eb', bg: '#eff6ff', text: '#1e40af', label: 'Application Deadline' },
        financial_aid: { border: '#059669', bg: '#f0fdf4', text: '#166534', label: 'Financial Aid' },
        scholarship: { border: '#d97706', bg: '#fffbeb', text: '#92400e', label: 'Scholarship' },
        decision: { border: '#7c3aed', bg: '#faf5ff', text: '#7e22ce', label: 'Admissions Decision' }
      };

      dayModalBody.innerHTML = dayEvents.map(evt => {
        const cat = categoryColors[evt.deadline_type || evt.category] || categoryColors.app_deadline;
        return `
          <div style="padding: 12px 14px; background: ${cat.bg}; border-left: 4px solid ${cat.border}; border-radius: 8px; border-top: 1px solid var(--color-border-subtle); border-right: 1px solid var(--color-border-subtle); border-bottom: 1px solid var(--color-border-subtle); display: flex; justify-content: space-between; align-items: center; gap: 12px;">
            <div>
              <span style="display: inline-block; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; color: ${cat.text}; margin-bottom: 3px;">
                ${evt.category_label || cat.label}
              </span>
              <h4 style="font-size: 0.9375rem; font-weight: 800; color: var(--text-primary); margin: 0 0 3px 0;">
                ${evt.title}
              </h4>
              <p style="font-size: 0.8125rem; color: var(--text-secondary); margin: 0;">
                ${evt.college_name}
              </p>
            </div>
            <div>
              ${evt.college_id !== 'national' ? `
                <a href="#/colleges/${evt.college_id}" class="btn btn-sm btn-secondary" onclick="document.getElementById('calendar-day-modal').style.display='none';" style="font-size: 0.75rem; font-weight: 600; white-space: nowrap;">
                  View Profile →
                </a>
              ` : `
                <span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; white-space: nowrap;">
                  National
                </span>
              `}
            </div>
          </div>
        `;
      }).join('');

      dayModal.style.display = 'flex';
    };

    // Attach click handlers to day cells that have events
    const clickableCells = container.querySelectorAll('.calendar-day-cell[data-has-events="true"]');
    clickableCells.forEach(cell => {
      cell.addEventListener('click', () => {
        const targetDate = cell.getAttribute('data-date');
        openDayModal(targetDate);
      });
    });
  }
};
