/**
 * 天赋类型学测评 — 结果页渲染逻辑
 */
(function () {
    const DIM_ORDER = ['dim1', 'dim2', 'dim3', 'dim4'];
    const DIM_ICONS = {
        dim1: 'C',
        dim2: 'W',
        dim3: 'D',
        dim4: 'V'
    };
    const DIM_LABELS = {
        dim1: '天赋形态',
        dim2: '能量模式',
        dim3: '驱动来源',
        dim4: '兴趣指向'
    };
    const DIM_HIGH_LABELS = {
        dim1: '天赋信号强度',
        dim2: '能量匹配度',
        dim3: '驱动纯度',
        dim4: '兴趣聚焦度'
    };

    const loading = document.getElementById('resultLoading');
    const error = document.getElementById('resultError');
    const content = document.getElementById('resultContent');

    // 从 URL 获取 session_id
    const pathParts = window.location.pathname.split('/');
    const sessionId = pathParts[pathParts.length - 1];

    if (!sessionId || sessionId === 'result') {
        showError();
        return;
    }

    loadResult();

    async function loadResult() {
        try {
            const resp = await fetch('/api/talent-type/result/' + sessionId);
            const data = await resp.json();
            if (!data.success) {
                showError();
                return;
            }
            render(data);
        } catch (e) {
            showError();
        }
    }

    function showError() {
        loading.style.display = 'none';
        error.style.display = 'block';
    }

    function render(data) {
        const { type_code, dimensions, scores, report } = data;

        // 4字母展示
        const lettersEl = document.getElementById('typeCodeLetters');
        lettersEl.innerHTML = '';
        type_code.split('').forEach(letter => {
            const span = document.createElement('span');
            span.className = 'letter';
            span.textContent = letter;
            lettersEl.appendChild(span);
        });

        // 名称和 tagline
        document.getElementById('typeName').textContent = report.name;
        document.getElementById('typeTagline').textContent = report.tagline;

        // 维度详情
        const dimContainer = document.getElementById('dimensionDetails');
        dimContainer.innerHTML = '';
        DIM_ORDER.forEach(dimKey => {
            const dim = dimensions[dimKey];
            if (!dim) return;

            // 从 scores 中计算该维度获胜选项的占比
            const dimScores = scores[dimKey] || {};
            const myScore = dimScores[dim.key] || 0;
            const totalScore = Object.values(dimScores).reduce((a, b) => a + b, 0);
            const pct = totalScore > 0 ? Math.round((myScore / totalScore) * 100) : 0;

            const card = document.createElement('div');
            card.className = 'dim-card';
            card.innerHTML = `
                <div class="dim-card-header">
                    <div class="dim-card-icon">${DIM_ICONS[dimKey]}</div>
                    <div>
                        <div class="dim-card-label">${DIM_LABELS[dimKey]}</div>
                        <div class="dim-card-name">${dim.code} · ${dim.info.name}</div>
                    </div>
                </div>
                <div class="dim-card-desc">${dim.info.desc}</div>
                <div class="dim-score-bar">
                    <span class="dim-score-label">${DIM_HIGH_LABELS[dimKey]}</span>
                    <div class="dim-score-track">
                        <div class="dim-score-fill" style="width:${pct}%"></div>
                    </div>
                    <span class="dim-score-value">${pct}%</span>
                </div>
            `;
            dimContainer.appendChild(card);
        });

        // 解读报告（5个段落全部展示）
        const reportEl = document.getElementById('reportSection');
        reportEl.innerHTML = `
            <h3>核心优势</h3>
            <div class="report-text">${report.strength.replace(/\n/g, '<br>')}</div>
            <div style="margin-top:1.25rem;">
                <h3>⚠️ 需要注意</h3>
                <div class="report-text">${report.watch_out.replace(/\n/g, '<br>')}</div>
            </div>
            <div style="margin-top:1.25rem;">
                <h3>最适合的环境</h3>
                <div class="report-text">${report.best_environment.replace(/\n/g, '<br>')}</div>
            </div>
            <div style="margin-top:1.25rem;">
                <h3>Human 3.0 洞察</h3>
                <div class="report-text">${report.human30_insight.replace(/\n/g, '<br>')}</div>
            </div>
            <div style="margin-top:1.25rem;">
                <h3>发展建议</h3>
                <div class="report-text">${report.development_advice.replace(/\n/g, '<br>')}</div>
            </div>
        `;

        loading.style.display = 'none';
        content.style.display = 'block';
    }
})();