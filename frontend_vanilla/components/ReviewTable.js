/**
 * ReviewTable Component
 *
 * A reusable, paginated table for displaying review activity.
 * Supports "dashboard mode" (simple list) and "full mode" (pagination + filters).
 */
class ReviewTable {
    /**
     * @param {string} selector - CSS selector for the container element
     * @param {Object} options - Configuration options
     * @param {number} options.limit - Number of items per page
     * @param {boolean} options.paginate - Whether to show pagination controls
     * @param {number} options.projectId - Filter by project ID (optional)
     * @param {Function} options.onRowClick - Callback when a row is clicked (optional)
     */
    constructor(selector, options = {}) {
        this.container = document.querySelector(selector);
        if (!this.container) {
            console.error(`ReviewTable: Container ${selector} not found`);
            return;
        }

        this.options = {
            limit: 10,
            paginate: true,
            projectId: null,
            ...options
        };

        this.state = {
            items: [],
            total: 0,
            skip: 0,
            loading: false,
            error: null
        };

        this.init();
    }

    async init() {
        this.renderLayout();
        await this.fetchData();
    }

    renderLayout() {
        this.container.innerHTML = `
            <div class="rt-wrapper">
                <div class="table-wrap">
                    <table class="rt-table">
                        <thead>
                            <tr>
                                <th>Project</th>
                                <th>Checklist</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th style="text-align:center">Total</th>
                                <th style="text-align:center">Compliant</th>
                                <th style="text-align:center">Amber</th>
                                <th style="text-align:center">Critical</th>
                                <th style="text-align:center">Human</th>
                                <th style="text-align:center">Score</th>
                                <th>Date</th>
                                <th style="text-align:right">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="rt-body">
                            <tr><td colspan="12" class="rt-loading"><span class="spinner"></span> Loading reviews...</td></tr>
                        </tbody>
                    </table>
                </div>
                ${this.options.paginate ? `
                <div class="rt-pagination" style="display:none">
                    <div class="rt-pagination-info">Showing <span class="rt-range">0-0</span> of <span class="rt-total">0</span></div>
                    <div class="rt-pagination-btns">
                        <button class="btn btn-ghost btn-sm rt-prev" disabled>Previous</button>
                        <button class="btn btn-ghost btn-sm rt-next" disabled>Next</button>
                    </div>
                </div>
                ` : ''}
            </div>
        `;

        if (!document.getElementById('rt-styles')) {
            const style = document.createElement('style');
            style.id = 'rt-styles';
            style.textContent = `
                .rt-wrapper { width: 100%; }
                .rt-loading { text-align: center; padding: 40px !important; color: #64748b; }
                .rt-error { text-align: center; padding: 40px !important; color: #f87171; }
                .rt-pagination { display: flex; align-items: center; justify-content: space-between; padding: 16px; background: #0f172a; border: 1px solid #334155; border-top: none; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }
                .rt-pagination-info { font-size: 13px; color: #64748b; }
                .rt-pagination-btns { display: flex; gap: 8px; }
                .rt-table td { vertical-align: middle; }
                .rt-score-val { font-weight: 700; }
                .rt-score-green { color: #4ade80; }
                .rt-score-amber { color: #fb923c; }
                .rt-score-red { color: #f87171; }
                .rt-score-na { color: #64748b; }
                .rt-type { text-transform: capitalize; }
            `;
            document.head.appendChild(style);
        }

        if (this.options.paginate) {
            this.container.querySelector('.rt-prev').onclick = () => this.prevPage();
            this.container.querySelector('.rt-next').onclick = () => this.nextPage();
        }
    }

    async fetchData() {
        this.state.loading = true;
        this.updateTableState();

        try {
            const token = localStorage.getItem('rb_token');
            let url = `/api/reports/activity?skip=${this.state.skip}&limit=${this.options.limit}`;
            if (this.options.projectId) url += `&project_id=${this.options.projectId}`;

            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Failed to fetch reviews');

            const data = await res.json();
            this.state.items = data.reports || [];
            this.state.total = data.total || 0;
            this.state.error = null;
        } catch (err) {
            this.state.error = err.message;
            this.state.items = [];
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    updateTableState() {
        const tbody = this.container.querySelector('.rt-body');
        if (this.state.loading) {
            tbody.innerHTML = `<tr><td colspan="12" class="rt-loading"><span class="spinner"></span> Loading reviews...</td></tr>`;
        } else if (this.state.error) {
            tbody.innerHTML = `<tr><td colspan="12" class="rt-error">Error: ${this.state.error}</td></tr>`;
        }
    }

    render() {
        const tbody = this.container.querySelector('.rt-body');

        if (this.state.items.length === 0 && !this.state.loading) {
            tbody.innerHTML = `<tr><td colspan="12" class="empty-state"><div class="icon">&#128196;</div><p>No reviews found.</p></td></tr>`;
            if (this.options.paginate) this.container.querySelector('.rt-pagination').style.display = 'none';
            return;
        }

        tbody.innerHTML = this.state.items.map(item => this.renderRow(item)).join('');

        tbody.querySelectorAll('.rt-stop-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const jobId = parseInt(btn.dataset.jobId, 10);
                this.stopReview(btn, jobId);
            });
        });

        if (this.options.paginate) {
            this.renderPagination();
        }
    }

    stopReview(btn, jobId) {
        const wrapper = btn.parentElement;
        btn.style.display = 'none';
        const confirmEl = document.createElement('span');
        confirmEl.style.cssText = 'display:inline-flex;align-items:center;gap:4px;';
        confirmEl.innerHTML = `
            <span style="font-size:11px;color:#f87171;white-space:nowrap;">Stop review?</span>
            <button class="btn btn-sm" style="background:#ef4444;color:#fff;padding:3px 8px;font-size:11px;border:none;border-radius:6px;cursor:pointer;">Yes</button>
            <button class="btn btn-ghost btn-sm" style="padding:3px 8px;font-size:11px;">No</button>
        `;
        wrapper.appendChild(confirmEl);

        const [yesBtn, noBtn] = confirmEl.querySelectorAll('button');

        noBtn.onclick = () => {
            confirmEl.remove();
            btn.style.display = '';
        };

        yesBtn.onclick = async () => {
            yesBtn.disabled = true;
            noBtn.disabled = true;
            yesBtn.textContent = '...';
            try {
                const token = localStorage.getItem('rb_token');
                const res = await fetch(`/api/autonomous-reviews/${jobId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `HTTP ${res.status}`);
                }
                await this.fetchData();
            } catch (err) {
                confirmEl.remove();
                btn.style.display = '';
                this.toast(`Stop failed: ${err.message}`);
            }
        };
    }

    renderRow(item) {
        const date = item.generated_at
            ? new Date(item.generated_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
            : '-';
        const score = this.renderScore(item.compliance_score);
        const status = this.renderStatus(item.status);
        const traceCount = item.llm_audit_count || 0;
        const isAutonomous = (item.review_type || '').toLowerCase() === 'autonomous';
        const summaryHref = isAutonomous && item.job_id ? `/history/${item.job_id}` : `/projects-ui/${item.project_id || ''}`;
        const traceHref = isAutonomous && item.job_id ? `/history/${item.job_id}?tab=ai-trace` : '';
        const dateTooltip = this.formatDateTooltip(item);
        const typeBadge = this.renderType(item.review_type);

        return `
            <tr>
                <td style="font-family:monospace;font-size:12px;color:#94a3b8;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${this.esc(item.project_name)}">${this.esc(item.project_name)}</td>
                <td><a href="${summaryHref}" style="color:inherit;text-decoration:none;">${this.esc(item.checklist_name)}</a></td>
                <td>${typeBadge}</td>
                <td>${status}</td>
                <td style="text-align:center"><span class="badge badge-gray" style="background:#1e293b22;min-width:32px;justify-content:center;color:#e2e8f0;font-family:monospace">${item.total_items || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-green" style="background:#14532d22;min-width:24px;justify-content:center">${item.green_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-amber" style="background:#78350f22;min-width:24px;justify-content:center">${item.amber_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-red" style="background:#7f1d1d22;min-width:24px;justify-content:center">${item.red_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-gray" style="background:#1e293b22;min-width:24px;justify-content:center">${item.skipped_count || 0}</span></td>
                <td style="text-align:center">${score}</td>
                <td style="color:#64748b;font-size:12px;white-space:nowrap" title="${this.esc(dateTooltip)}">${date}</td>
                <td style="text-align:right;white-space:nowrap">
                    <div style="display:flex;gap:6px;justify-content:flex-end">
                        <a href="${summaryHref}" class="btn btn-ghost btn-sm" style="text-decoration:none;" title="View review">Open</a>
                        ${isAutonomous && traceCount > 0 ? `<a href="${traceHref}" class="btn btn-ghost btn-sm" style="text-decoration:none;" title="View AI trace">AI Trace (${traceCount})</a>` : ''}
                        ${isAutonomous && ['running', 'queued', 'pending'].includes((item.status || '').toLowerCase()) ? `<button class="btn btn-ghost btn-sm rt-stop-btn" data-job-id="${item.job_id}" style="color:#f87171;border-color:#991b1b;" title="Stop this review">Stop</button>` : ''}
                    </div>
                </td>
            </tr>
        `;
    }

    renderStatus(status) {
        const map = {
            completed: ['badge-green', 'Completed'],
            running: ['badge-blue', 'Running'],
            queued: ['badge-gray', 'Queued'],
            pending: ['badge-gray', 'Queued'],
            failed: ['badge-red', 'Failed'],
            error: ['badge-red', 'Error'],
        };
        const [cls, label] = map[(status || '').toLowerCase()] || ['badge-gray', status || '-'];
        return `<span class="badge ${cls}">${label}</span>`;
    }

    renderType(type) {
        const normalized = (type || 'online').toLowerCase();
        const map = {
            autonomous: ['badge-blue', 'Autonomous'],
            offline: ['badge-amber', 'Offline'],
            online: ['badge-green', 'Online'],
        };
        const [cls, label] = map[normalized] || ['badge-gray', type || '-'];
        return `<span class="badge ${cls} rt-type">${label}</span>`;
    }

    renderScore(score) {
        if (score === null || score === undefined) return '<span class="rt-score-na">-</span>';
        const pct = Math.round(score);
        const cls = pct >= 75 ? 'rt-score-green' : pct >= 50 ? 'rt-score-amber' : 'rt-score-red';
        return `<span class="rt-score-val ${cls}">${pct}%</span>`;
    }

    formatDateTooltip(item) {
        const lines = [];
        const startedAt = this.formatDateTime(item.started_at || item.created_at);
        const completedAt = this.formatDateTime(item.completed_at);
        const duration = this.formatDuration(item.duration_seconds);

        if (startedAt) lines.push(`Started: ${startedAt}`);
        if (completedAt) lines.push(`Completed: ${completedAt}`);
        if (duration) lines.push(`Duration: ${duration}`);

        if (lines.length === 0) {
            const generatedAt = this.formatDateTime(item.generated_at);
            return generatedAt ? `Recorded: ${generatedAt}` : 'Time details unavailable';
        }

        return lines.join('\n');
    }

    formatDateTime(value) {
        if (!value) return '';
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) return '';
        return parsed.toLocaleString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    }

    formatDuration(seconds) {
        if (!Number.isFinite(seconds) || seconds < 0) return '';
        if (seconds < 60) return `${seconds}s`;

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        const parts = [];

        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (remainingSeconds > 0 || parts.length === 0) parts.push(`${remainingSeconds}s`);

        return parts.join(' ');
    }

    renderPagination() {
        const pag = this.container.querySelector('.rt-pagination');
        pag.style.display = 'flex';

        const start = this.state.skip + 1;
        const end = Math.min(this.state.skip + this.options.limit, this.state.total);

        this.container.querySelector('.rt-range').textContent = `${start}-${end}`;
        this.container.querySelector('.rt-total').textContent = this.state.total;

        const prevBtn = this.container.querySelector('.rt-prev');
        const nextBtn = this.container.querySelector('.rt-next');

        prevBtn.disabled = this.state.skip === 0;
        nextBtn.disabled = end >= this.state.total;
    }

    nextPage() {
        if (this.state.skip + this.options.limit < this.state.total) {
            this.state.skip += this.options.limit;
            this.fetchData();
        }
    }

    prevPage() {
        if (this.state.skip - this.options.limit >= 0) {
            this.state.skip -= this.options.limit;
            this.fetchData();
        }
    }

    refresh() {
        this.state.skip = 0;
        return this.fetchData();
    }

    toast(msg, type = 'error') {
        if (typeof window.toast === 'function') {
            window.toast(msg, type);
            return;
        }
        let el = document.getElementById('rt-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'rt-toast';
            el.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);padding:10px 20px;border-radius:8px;font-size:13px;font-weight:500;z-index:9999;pointer-events:none;transition:opacity .3s;max-width:480px;text-align:center;';
            document.body.appendChild(el);
        }
        el.textContent = msg;
        el.style.background = type === 'error' ? '#7f1d1d' : type === 'success' ? '#14532d' : '#1e3a5f';
        el.style.color = '#f1f5f9';
        el.style.opacity = '1';
        clearTimeout(el._t);
        el._t = setTimeout(() => { el.style.opacity = '0'; }, 3500);
    }

    esc(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
}
