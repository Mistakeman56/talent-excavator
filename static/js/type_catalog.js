/**
 * 72种人格图鉴 — 交互逻辑（分组显示版）
 */
(function() {
    let allTypes = [];
    let dimensions = {};
    let currentType = '';
    let searchKeyword = '';

    // 大类型配置
    const TYPE_GROUPS = {
        'C': {
            name: '认知洞察型',
            icon: '🧠',
            desc: '天赋核心在于「想」——理解复杂系统、发现底层模式、追问本质',
            color: '#0066cc',
            colorLight: 'rgba(0, 102, 204, 0.1)',
            colorBorder: 'rgba(0, 102, 204, 0.3)'
        },
        'R': {
            name: '关系创造型',
            icon: '💚',
            desc: '天赋核心在于「连接」——深度共情、网络编织、关系创造',
            color: '#34c759',
            colorLight: 'rgba(52, 199, 89, 0.1)',
            colorBorder: 'rgba(52, 199, 89, 0.3)'
        },
        'B': {
            name: '身体实践型',
            icon: '⚡',
            desc: '天赋核心在于「做」——用双手和身体去感知世界、改变世界',
            color: '#ff9500',
            colorLight: 'rgba(255, 149, 0, 0.1)',
            colorBorder: 'rgba(255, 149, 0, 0.3)'
        },
        'S': {
            name: '系统引领型',
            icon: '👑',
            desc: '天赋核心在于「推动」——在混乱中建立秩序、带领大家往前走',
            color: '#af52de',
            colorLight: 'rgba(175, 82, 222, 0.1)',
            colorBorder: 'rgba(175, 82, 222, 0.3)'
        }
    };

    // DOM 元素
    const searchInput = document.getElementById('searchInput');
    const catalogGroups = document.getElementById('catalogGroups');
    const catalogEmpty = document.getElementById('catalogEmpty');
    const btnResetFilter = document.getElementById('btnResetFilter');

    // 初始化
    loadCatalog();

    // 加载数据
    async function loadCatalog() {
        try {
            const res = await fetch('/api/talent-type/catalog');
            const data = await res.json();
            if (!data.success) {
                catalogGroups.innerHTML = '<p style="text-align:center; color: var(--body-muted); padding: 40px;">加载失败</p>';
                return;
            }
            allTypes = data.types;
            dimensions = data.dimensions;
            renderGroups();
        } catch (err) {
            catalogGroups.innerHTML = '<p style="text-align:center; color: var(--body-muted); padding: 40px;">网络错误</p>';
        }
    }

    // 按大类型分组渲染
    function renderGroups() {
        const filtered = filterTypes();

        // 按首字母分组
        const groups = {};
        filtered.forEach(type => {
            const groupKey = type.code[0];
            if (!groups[groupKey]) groups[groupKey] = [];
            groups[groupKey].push(type);
        });

        // 更新统计
        updateStats(filtered);

        if (filtered.length === 0) {
            catalogGroups.style.display = 'none';
            catalogEmpty.style.display = 'block';
            return;
        }

        catalogGroups.style.display = 'block';
        catalogEmpty.style.display = 'none';

        // 确定要显示的组
        const groupsToShow = currentType ? [currentType] : ['C', 'R', 'B', 'S'];

        let html = '';
        groupsToShow.forEach(groupKey => {
            const types = groups[groupKey] || [];
            if (types.length === 0) return;

            const group = TYPE_GROUPS[groupKey];
            html += `
                <div class="catalog-group" data-group="${groupKey}">
                    <div class="catalog-group-header" style="border-left: 4px solid ${group.color};">
                        <div class="catalog-group-title">
                            <span class="catalog-group-icon">${group.icon}</span>
                            <h2>${group.name}</h2>
                            <span class="catalog-group-count">${types.length} 种</span>
                        </div>
                        <p class="catalog-group-desc">${group.desc}</p>
                    </div>
                    <div class="catalog-grid">
                        ${types.map(type => renderCard(type, group)).join('')}
                    </div>
                </div>
            `;
        });

        catalogGroups.innerHTML = html;

        // 绑定卡片点击事件
        catalogGroups.querySelectorAll('.catalog-card').forEach(card => {
            card.addEventListener('click', function() {
                openDetail(this.dataset.code);
            });
        });
    }

    // 渲染单个卡片
    function renderCard(type, group) {
        return `
            <div class="catalog-card ${type.has_detail ? 'has-detail' : ''}" 
                 data-code="${type.code}"
                 style="--group-color: ${group.color}; --group-color-light: ${group.colorLight}; --group-color-border: ${group.colorBorder};">
                <div class="catalog-card-header">
                    <span class="catalog-code">${type.code}</span>
                    ${type.has_detail ? '<span class="catalog-badge">详细报告</span>' : ''}
                </div>
                <h3 class="catalog-name">${escapeHtml(type.name)}</h3>
                <p class="catalog-tagline">${escapeHtml(type.tagline)}</p>
                <div class="catalog-dims">
                    <span class="catalog-dim">${type.dim2.code} ${escapeHtml(type.dim2.name)}</span>
                    <span class="catalog-dim">${type.dim3.code} ${escapeHtml(type.dim3.name)}</span>
                    <span class="catalog-dim">${type.dim4.code} ${escapeHtml(type.dim4.name)}</span>
                </div>
            </div>
        `;
    }

    // 筛选逻辑
    function filterTypes() {
        return allTypes.filter(type => {
            // 大类型筛选
            if (currentType && type.code[0] !== currentType) return false;

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

    // 更新统计
    function updateStats(filtered) {
        const hasFilter = currentType || searchKeyword;
        btnResetFilter.style.display = hasFilter ? 'inline' : 'none';
    }

    // 搜索输入
    searchInput.addEventListener('input', function(e) {
        searchKeyword = e.target.value.trim();
        renderGroups();
    });

    // 大类型标签点击
    document.querySelectorAll('.type-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.type-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentType = this.dataset.type;
            renderGroups();
        });
    });

    // 重置筛选
    btnResetFilter.addEventListener('click', function() {
        currentType = '';
        searchKeyword = '';
        searchInput.value = '';
        document.querySelectorAll('.type-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.type === '');
        });
        renderGroups();
    });

    // 打开详情弹窗
    window.openDetail = function(code) {
        const type = allTypes.find(t => t.code === code);
        if (!type) return;

        const group = TYPE_GROUPS[type.code[0]];
        const body = document.getElementById('detailModalBody');
        let html = `
            <div class="catalog-detail-header" style="border-top: 3px solid ${group.color};">
                <div class="catalog-detail-type" style="color: ${group.color};">
                    <span class="catalog-detail-icon">${group.icon}</span>
                    <span class="catalog-detail-group">${group.name}</span>
                </div>
                <span class="catalog-detail-code">${type.code}</span>
                <h2 class="catalog-detail-name">${escapeHtml(type.name)}</h2>
                <p class="catalog-detail-tagline">${escapeHtml(type.tagline)}</p>
            </div>

            <div class="catalog-detail-dims">
                <div class="catalog-detail-dim" style="border-left: 3px solid ${group.color};">
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
                    <h3 style="color: ${group.color};">详细解读</h3>
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
                    <p>该类型暂无详细报告，可通过 <a href="/talent-type" style="color: ${group.color};">40题测评</a> 获取你的专属解读。</p>
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
