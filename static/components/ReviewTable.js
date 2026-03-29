/**
 * ReviewTable Component
 * 
 * A reusable, paginated table for displaying autonomous review jobs.
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
                            <tr><td colspan="11" class="rt-loading"><span class="spinner"></span> Loading reviews...</td></tr>
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

        // Add internal styles if not present
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
            let url = `/api/reports/history?skip=${this.state.skip}&limit=${this.options.limit}`;
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
            tbody.innerHTML = `<tr><td colspan="11" class="rt-loading"><span class="spinner"></span> Loading reviews...</td></tr>`;
        } else if (this.state.error) {
            tbody.innerHTML = `<tr><td colspan="11" class="rt-error">Error: ${this.state.error}</td></tr>`;
        }
    }

    render() {
        const tbody = this.container.querySelector('.rt-body');
        
        if (this.state.items.length === 0 && !this.state.loading) {
            tbody.innerHTML = `<tr><td colspan="11" class="empty-state"><div class="icon">&#128196;</div><p>No reviews found.</p></td></tr>`;
            if (this.options.paginate) this.container.querySelector('.rt-pagination').style.display = 'none';
            return;
        }

        tbody.innerHTML = this.state.items.map(item => this.renderRow(item)).join('');
        
        if (this.options.paginate) {
            this.renderPagination();
        }
    }

    renderRow(item) {
        const date = item.generated_at ? new Date(item.generated_at).toLocaleDateString('en-GB', { day:'2-digit', month:'short' }) : '–';
        const score = this.renderScore(item.compliance_score);
        const status = this.renderStatus(item.status);
        
        return `
            <tr>
                <td style="font-family:monospace;font-size:12px;color:#94a3b8;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${this.esc(item.project_name)}">${this.esc(item.project_name)}</td>
                <td>${this.esc(item.checklist_name)}</td>
                <td>${status}</td>
                <td style="text-align:center"><span class="badge badge-gray" style="background:#1e293b22;min-width:32px;justify-content:center;color:#e2e8f0;font-family:monospace">${item.total_items || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-green" style="background:#14532d22;min-width:24px;justify-content:center">${item.green_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-amber" style="background:#78350f22;min-width:24px;justify-content:center">${item.amber_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-red" style="background:#7f1d1d22;min-width:24px;justify-content:center">${item.red_count || 0}</span></td>
                <td style="text-align:center"><span class="badge badge-gray" style="background:#1e293b22;min-width:24px;justify-content:center">${item.skipped_count || 0}</span></td>
                <td style="text-align:center">${score}</td>
                <td style="color:#64748b;font-size:12px;white-space:nowrap">${date}</td>
                <td style="text-align:right">
                    <a href="/history/${item.job_id}" class="btn btn-ghost btn-sm">View Report</a>
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
        const [cls, label] = map[(status || '').toLowerCase()] || ['badge-gray', status || '–'];
        return `<span class="badge ${cls}">${label}</span>`;
    }

    renderScore(score) {
        if (score === null || score === undefined) return '<span class="rt-score-na">–</span>';
        const pct = Math.round(score);
        const cls = pct >= 75 ? 'rt-score-green' : pct >= 50 ? 'rt-score-amber' : 'rt-score-red';
        return `<span class="rt-score-val ${cls}">${pct}%</span>`;
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

    esc(str) {
        return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
}
