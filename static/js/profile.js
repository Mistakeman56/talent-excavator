/**
 * 个人天赋档案页交互逻辑
 */
(function () {
    const loading = document.getElementById('profileLoading');
    const content = document.getElementById('profileContent');
    const empty = document.getElementById('profileEmpty');
    const main = document.getElementById('profileMain');

    async function loadProfile() {
        try {
            const res = await fetch('/api/profile/summary');
            const data = await res.json();

            loading.style.display = 'none';
            content.style.display = 'block';

            if (!data.success || !data.has_data) {
                empty.style.display = 'block';
                return;
            }

            main.style.display = 'block';
            renderSummaryCard(data);
            renderInterviewSection(data.interview);
            renderScaleSection(data.scale);
            renderTalentTypeSection(data.talent_type);
            renderValidation(data.cross_validation);

        } catch (err) {
            loading.style.display = 'none';
            content.style.display = 'block';
            empty.style.display = 'block';
            empty.querySelector('h2').textContent = '加载失败';
            empty.querySelector('p').textContent = '请刷新重试';
        }
    }

    function renderSummaryCard(data) {
        const card = document.getElementById('profileSummaryCard');
        const tt = data.talent_type;
        const scale = data.scale;
        const iv = data.interview;

        let code = tt.has ? tt.type_code : '----';
        let name = tt.has ? tt.name : '待测评';
        let tagline = tt.has ? tt.tagline : '完成天赋类型学测评，获取你的 4 字母天赋代码';

        let topDim = '';
        if (scale.primary && scale.primary.top_dimensions && scale.primary.top_dimensions.length > 0) {
            topDim = scale.primary.top_dimensions[0].name;
        }

        let keywordsHtml = '';
        if (iv.has && iv.keywords && iv.keywords.length > 0) {
            keywordsHtml = iv.keywords.slice(0, 5).map(k =>
                '<span class="profile-keyword">' + escapeHtml(k) + '</span>'
            ).join('');
        }

        card.innerHTML = `
            <div class="profile-card-header">
                <div class="profile-type-code">${escapeHtml(code)}</div>
                <div class="profile-type-name">${escapeHtml(name)}</div>
                <div class="profile-tagline">${escapeHtml(tagline)}</div>
            </div>
            ${topDim ? '<div class="profile-top-dim">量表 Top 维度：<strong>' + escapeHtml(topDim) + '</strong></div>' : ''}
            ${keywordsHtml ? '<div class="profile-keywords">' + keywordsHtml + '</div>' : ''}
        `;
    }

    function renderInterviewSection(iv) {
        const el = document.getElementById('profileInterview');
        if (!iv.has) {
            el.innerHTML = `
                <div class="profile-section-card">
                    <div class="profile-section-header">
                        <span class="profile-section-icon">🎙️</span>
                        <h3>AI 深度访谈</h3>
                    </div>
                    <p class="profile-section-empty">尚未完成访谈</p>
                    <a href="/" class="btn-secondary-pill" style="font-size:14px; padding:8px 16px;">去访谈</a>
                </div>
            `;
            return;
        }

        const keywords = (iv.keywords || []).map(k =>
            '<span class="profile-tag">' + escapeHtml(k) + '</span>'
        ).join('');

        el.innerHTML = `
            <div class="profile-section-card">
                <div class="profile-section-header">
                    <span class="profile-section-icon">🎙️</span>
                    <h3>AI 深度访谈</h3>
                    <span class="profile-section-date">${formatDate(iv.created_at)}</span>
                </div>
                <div class="profile-section-body">
                    <div class="profile-label">识别到的天赋关键词</div>
                    <div class="profile-tags">${keywords || '<span class="profile-muted">未提取到关键词</span>'}</div>
                </div>
            </div>
        `;
    }

    function renderScaleSection(scale) {
        const el = document.getElementById('profileScale');
        if (!scale.primary) {
            el.innerHTML = `
                <div class="profile-section-card">
                    <div class="profile-section-header">
                        <span class="profile-section-icon">📊</span>
                        <h3>天赋维度量表</h3>
                    </div>
                    <p class="profile-section-empty">尚未完成量表</p>
                    <a href="/scale" class="btn-secondary-pill" style="font-size:14px; padding:8px 16px;">去测评</a>
                </div>
            `;
            return;
        }

        const scores = scale.primary.scores || {};
        const dims = Object.entries(scores).map(([key, val]) =>
            `<div class="profile-dim-item">
                <span class="profile-dim-name">${escapeHtml(val.name)}</span>
                <div class="profile-dim-bar">
                    <div class="profile-dim-fill" style="width: ${(val.score / 5) * 100}%"></div>
                </div>
                <span class="profile-dim-score">${val.score}</span>
            </div>`
        ).join('');

        let secondaryHtml = '';
        if (scale.secondary) {
            secondaryHtml = `
                <div class="profile-secondary">
                    <div class="profile-label">二级量表锁定</div>
                    <div class="profile-secondary-type">${escapeHtml(scale.secondary.talent_type || '未测评')}</div>
                </div>
            `;
        }

        el.innerHTML = `
            <div class="profile-section-card">
                <div class="profile-section-header">
                    <span class="profile-section-icon">📊</span>
                    <h3>天赋维度量表</h3>
                    <span class="profile-section-date">${formatDate(scale.primary.created_at)}</span>
                </div>
                <div class="profile-section-body">
                    <div class="profile-dims">${dims}</div>
                    ${secondaryHtml}
                </div>
            </div>
        `;

        setTimeout(() => renderScaleRadar(scores), 100);
    }

    function renderScaleRadar(scores) {
        const dims = Object.values(scores);
        if (dims.length === 0) return;

        const container = document.querySelector('#profileScale .profile-section-body');
        if (!container || container.querySelector('.profile-radar')) return;

        const radarDiv = document.createElement('div');
        radarDiv.className = 'profile-radar';
        radarDiv.style.width = '100%';
        radarDiv.style.height = '220px';
        container.insertBefore(radarDiv, container.firstChild);

        const textColor = getChartTextColor();
        const chart = echarts.init(radarDiv);
        chart.setOption({
            radar: {
                indicator: dims.map(d => ({ name: d.name, max: 5 })),
                radius: '65%',
                axisName: {
                    color: textColor,
                    fontSize: 12
                },
                splitLine: {
                    lineStyle: { color: isDarkMode() ? 'rgba(255,255,255,0.08)' : 'rgba(0,102,204,0.1)' }
                },
                splitArea: { areaStyle: { color: isDarkMode() ? ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.04)'] : ['rgba(0,102,204,0.02)', 'rgba(0,102,204,0.04)'] } }
            },
            series: [{
                type: 'radar',
                data: [{
                    value: dims.map(d => d.score),
                    areaStyle: { color: 'rgba(0,102,204,0.15)' },
                    lineStyle: { color: '#0066cc' },
                    itemStyle: { color: '#0066cc' }
                }]
            }]
        });
    }

    function renderTalentTypeSection(tt) {
        const el = document.getElementById('profileTalentType');
        if (!tt.has) {
            el.innerHTML = `
                <div class="profile-section-card">
                    <div class="profile-section-header">
                        <span class="profile-section-icon">🧬</span>
                        <h3>天赋类型学</h3>
                    </div>
                    <p class="profile-section-empty">尚未完成测评</p>
                    <a href="/talent-type" class="btn-secondary-pill" style="font-size:14px; padding:8px 16px;">去测评</a>
                </div>
            `;
            return;
        }

        const dims = tt.dimensions || {};
        const dimCards = Object.entries(dims).map(([key, val]) =>
            `<div class="profile-tt-dim">
                <div class="profile-tt-dim-label">${escapeHtml(val.name || key)}</div>
                <div class="profile-tt-dim-desc">${escapeHtml(val.desc || '')}</div>
            </div>`
        ).join('');

        el.innerHTML = `
            <div class="profile-section-card">
                <div class="profile-section-header">
                    <span class="profile-section-icon">🧬</span>
                    <h3>天赋类型学</h3>
                    <span class="profile-section-date">${formatDate(tt.created_at)}</span>
                </div>
                <div class="profile-section-body">
                    <div class="profile-tt-code">${escapeHtml(tt.type_code)}</div>
                    <div class="profile-tt-name">${escapeHtml(tt.name)}</div>
                    <div class="profile-tt-tagline">${escapeHtml(tt.tagline || '')}</div>
                    <div class="profile-tt-dims">${dimCards}</div>
                </div>
            </div>
        `;
    }

    function renderValidation(validation) {
        const el = document.getElementById('profileValidation');
        if (!validation) {
            el.style.display = 'none';
            return;
        }

        const confirmed = validation.confirmed || [];
        const conflicts = validation.conflicts || [];

        if (confirmed.length === 0 && conflicts.length === 0) {
            el.style.display = 'none';
            return;
        }

        let html = '<div class="profile-section-card"><div class="profile-section-header"><span class="profile-section-icon">🔗</span><h3>跨测评交叉验证</h3></div><div class="profile-section-body">';

        if (confirmed.length > 0) {
            html += '<div class="profile-validation-group"><div class="profile-label" style="color:#34c759;">互相验证</div>';
            html += confirmed.map(c => '<div class="profile-validation-item confirmed">✓ ' + escapeHtml(c) + '</div>').join('');
            html += '</div>';
        }

        if (conflicts.length > 0) {
            html += '<div class="profile-validation-group"><div class="profile-label" style="color:#ff9500;">有分歧</div>';
            html += conflicts.map(c => '<div class="profile-validation-item conflict">⚠ ' + escapeHtml(c) + '</div>').join('');
            html += '</div>';
        }

        html += '</div></div>';
        el.innerHTML = html;
        el.style.display = 'block';
    }

    function formatDate(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
    }

    loadProfile();
})();
