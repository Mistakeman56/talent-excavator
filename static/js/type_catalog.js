/**
 * 72种人格图鉴 — 交互逻辑
 */
(function() {
    let allTypes = [];
    let dimensions = {};
    let filters = { dim1: '', dim2: '', dim3: '', dim4: '' };
    let searchKeyword = '';

    // DOM 元素
    const searchInput = document.getElementById('searchInput');
    const catalogGrid = document.getElementById('catalogGrid');
    const catalogEmpty = document.getElementById('catalogEmpty');
    const resultCount = document.getElementById('resultCount');
    const btnResetFilter = document.getElementById('btnResetFilter');

    // 初始化
    loadCatalog();

    // 加载数据
    async function loadCatalog() {
        try {
            const res = await fetch('/api/talent-type/catalog');
            const data = await res.json();
            if (!data.success) {
                catalogGrid.innerHTML = '<p style="text-align:center; color: var(--body-muted); padding: 40px;">加载失败</p>';
                return;
            }
            allTypes = data.types;
            dimensions = data.dimensions;
            renderGrid();
        } catch (err) {
            catalogGrid.innerHTML = '<p style="text-align:center; color: var(--body-muted); padding: 40px;">网络错误</p>';
        }
    }

    // 渲染网格
    function renderGrid() {
        const filtered = filterTypes();

        if (filtered.length === 0) {
            catalogGrid.style.display = 'none';
            catalogEmpty.style.display = 'block';
        } else {
            catalogGrid.style.display = 'grid';
            catalogEmpty.style.display = 'none';
        }

        resultCount.textContent = filtered.length;

        // 显示/隐藏重置按钮
        const hasFilter = Object.values(filters).some(v => v !== '') || searchKeyword !== '';
        btnResetFilter.style.display = hasFilter ? 'inline' : 'none';

        catalogGrid.innerHTML = filtered.map(type => `
            <div class="catalog-card ${type.has_detail ? 'has-detail' : ''}" data-code="${type.code}" onclick="openDetail('${type.code}')">
                <div class="catalog-card-header">
                    <span class="catalog-code">${type.code}</span>
                    ${type.has_detail ? '<span class="catalog-badge">详细报告</span>' : ''}
                </div>
                <h3 class="catalog-name">${escapeHtml(type.name)}</h3>
                <p class="catalog-tagline">${escapeHtml(type.tagline)}</p>
                <div class="catalog-dims">
                    <span class="catalog-dim" title="${escapeHtml(type.dim1.desc)}">${type.dim1.code} ${escapeHtml(type.dim1.name)}</span>
                    <span class="catalog-dim" title="${escapeHtml(type.dim2.desc)}">${type.dim2.code} ${escapeHtml(type.dim2.name)}</span>
                    <span class="catalog-dim" title="${escapeHtml(type.dim3.desc)}">${type.dim3.code} ${escapeHtml(type.dim3.name)}</span>
                    <span class="catalog-dim" title="${escapeHtml(type.dim4.desc)}">${type.dim4.code} ${escapeHtml(type.dim4.name)}</span>
                </div>
            </div>
        `).join('');
    }

    // 筛选逻辑
    function filterTypes() {
        return allTypes.filter(type => {
            // 维度筛选
            if (filters.dim1 && type.dim1.code !== filters.dim1) return false;
            if (filters.dim2 && type.dim2.code !== filters.dim2) return false;
            if (filters.dim3 && type.dim3.code !== filters.dim3) return false;
            if (filters.dim4 && type.dim4.code !== filters.dim4) return false;

            // 搜索筛选
            if (searchKeyword) {
                const kw = searchKeyword.toLowerCase();
                const matchCode = type.code.toLowerCase().includes(kw);
                const matchName = type.name.toLowerCase().includes(kw);
                const matchTagline = type.tagline.toLowerCase().includes(kw);
                if (!matchCode && !matchName && !matchTagline) return false;
            }

            return true;
        });
    }

    // 搜索输入
    searchInput.addEventListener('input', function(e) {
        searchKeyword = e.target.value.trim();
        renderGrid();
    });

    // 维度筛选标签点击
    document.querySelectorAll('.dim-filter-tags').forEach(group => {
        group.addEventListener('click', function(e) {
            const btn = e.target.closest('.tag');
            if (!btn) return;

            const dim = this.dataset.dim;
            group.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            filters[dim] = btn.dataset.value;
            renderGrid();
        });
    });

    // 重置筛选
    btnResetFilter.addEventListener('click', function() {
        filters = { dim1: '', dim2: '', dim3: '', dim4: '' };
        searchKeyword = '';
        searchInput.value = '';
        document.querySelectorAll('.dim-filter-tags .tag').forEach(t => {
            t.classList.toggle('active', t.dataset.value === '');
        });
        renderGrid();
    });

    // 打开详情弹窗
    window.openDetail = function(code) {
        const type = allTypes.find(t => t.code === code);
        if (!type) return;

        const body = document.getElementById('detailModalBody');
        let html = `
            <div class="catalog-detail-header">
                <span class="catalog-detail-code">${type.code}</span>
                <h2 class="catalog-detail-name">${escapeHtml(type.name)}</h2>
                <p class="catalog-detail-tagline">${escapeHtml(type.tagline)}</p>
            </div>

            <div class="catalog-detail-dims">
                <div class="catalog-detail-dim">
                    <span class="dim-label">天赋形态</span>
                    <span class="dim-value">${type.dim1.code} · ${escapeHtml(type.dim1.name)}</span>
                    <p class="dim-desc">${escapeHtml(type.dim1.desc)}</p>
                </div>
                <div class="catalog-detail-dim">
                    <span class="dim-label">能量模式</span>
                    <span class="dim-value">${type.dim2.code} · ${escapeHtml(type.dim2.name)}</span>
                    <p class="dim-desc">${escapeHtml(type.dim2.desc)}</p>
                </div>
                <div class="catalog-detail-dim">
                    <span class="dim-label">驱动来源</span>
                    <span class="dim-value">${type.dim3.code} · ${escapeHtml(type.dim3.name)}</span>
                    <p class="dim-desc">${escapeHtml(type.dim3.desc)}</p>
                </div>
                <div class="catalog-detail-dim">
                    <span class="dim-label">兴趣指向</span>
                    <span class="dim-value">${type.dim4.code} · ${escapeHtml(type.dim4.name)}</span>
                    <p class="dim-desc">${escapeHtml(type.dim4.desc)}</p>
                </div>
            </div>
        `;

        // 如果有详细报告
        if (type.has_detail && type.report) {
            const r = type.report;
            html += `
                <div class="catalog-detail-report">
                    <h3>详细解读</h3>
                    ${r.strength ? `
                    <div class="report-section">
                        <h4>核心优势</h4>
                        <p>${escapeHtml(r.strength)}</p>
                    </div>` : ''}
                    ${r.watch_out ? `
                    <div class="report-section">
                        <h4>⚠️ 需要注意</h4>
                        <p>${escapeHtml(r.watch_out)}</p>
                    </div>` : ''}
                    ${r.best_environment ? `
                    <div class="report-section">
                        <h4>最适合的环境</h4>
                        <p>${escapeHtml(r.best_environment)}</p>
                    </div>` : ''}
                    ${r.human30_insight ? `
                    <div class="report-section">
                        <h4>Human 3.0 洞察</h4>
                        <p>${escapeHtml(r.human30_insight)}</p>
                    </div>` : ''}
                    ${r.development_advice ? `
                    <div class="report-section">
                        <h4>发展建议</h4>
                        <p>${escapeHtml(r.development_advice)}</p>
                    </div>` : ''}
                </div>
            `;
        } else {
            html += `
                <div class="catalog-detail-no-report">
                    <p>该类型暂无详细报告，可通过 <a href="/talent-type">40题测评</a> 获取你的专属解读。</p>
                </div>
            `;
        }

        body.innerHTML = html;
        document.getElementById('detailModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    };

    // 关闭详情弹窗
    window.closeDetailModal = function() {
        document.getElementById('detailModal').style.display = 'none';
        document.body.style.overflow = '';
    };

    // ESC 关闭弹窗
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeDetailModal();
    });
})();
