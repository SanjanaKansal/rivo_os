/**
 * Shared UI Components for Rivo OS Dashboard
 */
const UI = {
    formatTime(dateStr) {
        if (!dateStr) return '-';
        const s = Math.floor((new Date() - new Date(dateStr)) / 1000);
        if (s < 60) return 'Just now';
        if (s < 3600) return `${Math.floor(s / 60)}m ago`;
        if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
        if (s < 172800) return 'Yesterday';
        return `${Math.floor(s / 86400)}d ago`;
    },

    row(cells, options = {}) {
        const { isHeader, className = '' } = options;
        const baseClass = isHeader ? 'grid-row header-row' : 'grid-row';
        return `<div class="${baseClass} ${className}">${cells.map(c =>
            `<div class="${c.class || ''}" ${c.title ? `title="${c.title}"` : ''}>${c.content}</div>`
        ).join('')}</div>`;
    },

    headerRow(columns) {
        return this.row(columns.map(col => ({
            content: col, class: 'text-xs font-medium text-gray-500 uppercase'
        })), { isHeader: true });
    },

    dataRow(cells) { return this.row(cells); },

    empty(message) {
        return `<div class="px-6 py-8 text-center text-sm text-gray-400">${message}</div>`;
    },

    tab(label, count, isActive, dataAttr) {
        return `<button data-${dataAttr.key}="${dataAttr.value}" class="tab-btn ${isActive ? 'active' : ''}">${label}<span class="tab-count">${count}</span></button>`;
    },

    group(header, content, index, meta = '') {
        return `
            <div class="grid-group" data-group="${index}">
                <div class="group-header" onclick="UI.toggleGroup(${index})">
                    <div class="flex items-center gap-2">
                        <svg class="group-chevron w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                        ${header}
                    </div>
                    ${meta ? `<div class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">${meta}</div>` : ''}
                </div>
                <div class="group-content">${content}</div>
            </div>`;
    },

    toggleGroup(idx) {
        document.querySelector(`[data-group="${idx}"]`)?.classList.toggle('collapsed');
    },

    refreshBtn(elementId, callback) {
        const icon = document.getElementById(elementId);
        if (icon) { icon.style.transform = 'rotate(180deg)'; setTimeout(() => icon.style.transform = '', 300); }
        callback();
    },

    modal: {
        show(id) { document.getElementById(id)?.classList.remove('hidden'); },
        hide(id) { document.getElementById(id)?.classList.add('hidden'); }
    },

    // Badges
    badge(value, type) {
        return `<span class="ui-badge ui-badge-${type}">${value}</span>`;
    },

    // Quality bar
    qualityBar(percent) {
        const color = percent >= 70 ? '#10b981' : percent >= 40 ? '#f59e0b' : '#ef4444';
        return `<div class="flex items-center gap-2">
            <div class="ui-quality-bar flex-1"><div class="ui-quality-fill" style="width:${percent}%;background:${color}"></div></div>
            <span class="text-xs text-gray-500 w-8">${percent}%</span>
        </div>`;
    },

    // Filter buttons
    filterBtn(label, value, isActive) {
        return `<button data-period="${value}" class="ui-filter-btn ${isActive ? 'active' : ''}">${label}</button>`;
    },

    // Stats cells helper - generates badge/quality cells from stats object
    statsCells(stats) {
        return `
            <div class="text-center">${stats.total}</div>
            <div class="text-center">${this.badge(stats.pending, 'pending')}</div>
            <div class="text-center">${this.badge(stats.valid, 'valid')}</div>
            <div class="text-center">${this.badge(stats.spam, 'spam')}</div>
            <div>${this.qualityBar(stats.quality)}</div>`;
    },

    // Stats table header
    statsTableHeader(columns = ['Name', 'Total', 'Pending', 'Valid', 'Spam', 'Quality']) {
        return `<div class="grid-row header-row grid-row-6 bg-gray-50 dark:bg-gray-900">
            ${columns.map(col => `<div class="text-xs font-medium text-gray-500 uppercase ${col !== columns[0] && col !== 'Quality' ? 'text-center' : ''}">${col}</div>`).join('')}
        </div>`;
    },

    // Stats group - collapsible row with stats
    statsGroup(label, subLabel, stats, childRows, index) {
        return `
            <div class="grid-group" data-group="${index}">
                <div class="stats-group-header grid-row-6" onclick="UI.toggleGroup(${index})">
                    <div class="flex items-center gap-2">
                        <svg class="group-chevron w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                        <div>
                            <div class="text-sm font-medium text-gray-900 dark:text-gray-200">${label}</div>
                            ${subLabel ? `<div class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">${subLabel}</div>` : ''}
                        </div>
                    </div>
                    ${this.statsCells({ ...stats, total: `<span class="text-sm font-semibold text-gray-900 dark:text-gray-200">${stats.total}</span>` })}
                </div>
                <div class="group-content">${childRows}</div>
            </div>`;
    },

    // Stats row - nested row inside statsGroup
    statsRow(label, stats) {
        return `<div class="grid-row stats-row-sub grid-row-6">
            <div class="pl-6 text-xs text-gray-600 dark:text-gray-400">${label}</div>
            ${this.statsCells({ ...stats, total: `<span class="text-xs text-gray-600 dark:text-gray-400">${stats.total}</span>` })}
        </div>`;
    }
};

// Shared CSS styles - using CSS variables from components.css
const sharedStyles = `
<style id="shared-styles">
/* Grid rows */
.grid-row { display: grid; gap: 0.75rem; padding: 0.75rem 1.5rem; align-items: center; border-bottom: 1px solid var(--color-border-light); }
.grid-row:last-child { border-bottom: none; }
.grid-row:hover { background: var(--color-bg); }
.grid-row.header-row:hover { background: transparent; }

/* Groups - collapsible sections */
.grid-group { border-bottom: 1px solid var(--color-border-light); }
.grid-group:last-child { border-bottom: none; }
.group-header { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1.5rem; cursor: pointer; user-select: none; }
.group-header:hover { background: var(--color-bg); }
.group-chevron { transition: transform 0.2s; }
.grid-group.collapsed .group-chevron { transform: rotate(-90deg); }
.grid-group.collapsed .group-content { display: none; }
.group-content { border-top: 1px solid var(--color-border-light); }

/* Badges in stats */
.ui-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 2rem; padding: 0.25rem 0.5rem; font-size: 0.75rem; font-weight: 600; border-radius: 0.375rem; }
.ui-badge-pending { background: var(--color-pending-bg); color: var(--color-pending-text); }
.ui-badge-valid { background: var(--color-valid-bg); color: var(--color-valid-text); }
.ui-badge-spam { background: var(--color-spam-bg); color: var(--color-spam-text); }

/* Quality bar */
.ui-quality-bar { height: 6px; background: var(--color-border); border-radius: 3px; overflow: hidden; }
.ui-quality-fill { height: 100%; border-radius: 3px; }

/* Filter buttons */
.ui-filter-btn { padding: 0.375rem 0.75rem; font-size: 0.75rem; font-weight: 500; color: var(--color-text-secondary); border-radius: 0.375rem; border: none; background: none; cursor: pointer; }
.ui-filter-btn:hover { color: var(--color-text); }
.ui-filter-btn.active { background: #111827; color: white; }
.dark .ui-filter-btn.active { background: #f3f4f6; color: #111827; }

/* Stats group (6-column grid for campaigns) */
.grid-row-6 { display: grid; grid-template-columns: 2.5fr 1fr 0.8fr 0.8fr 0.8fr 1fr; gap: 1rem; padding: 0.75rem 1.5rem; align-items: center; }
.stats-group-header { cursor: pointer; user-select: none; }
.stats-group-header:hover { background: var(--color-bg); }
.stats-row-sub { background: var(--color-bg); }
.stats-row-sub:hover { background: var(--color-border-light); }
</style>
`;

if (!document.getElementById('shared-styles')) {
    document.head.insertAdjacentHTML('beforeend', sharedStyles);
}