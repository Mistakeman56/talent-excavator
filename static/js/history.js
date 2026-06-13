/**
 * 历史记录页交互逻辑
 */
(function() {
    let allRecords = [];
    let currentFilter = 'all';
    let currentView = 'list';
    let selectedRecords = new Set();
    let compareChart = null;

    // 初始化
    loadHistory();

    // 筛选标签点击
    document.getElementById('filterTags').addEventListener('click', function(e) {
        const btn = e.target.closest('.tag');
        if (!btn) return;
        document.querySelectorAll('#filterTags .tag').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderList();
    });

    // 视图切换
    document.getElementById('viewToggle').addEventListener('click', function(e) {
        const btn = e.target.closest('.view-toggle-btn');
        if (!btn) return;
        document.querySelectorAll('.view-toggle-btn').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        currentView = btn.dataset.view;
        toggleView();
    });

    // 全选复选框事件绑定
    document.getElementById('selectAll').addEventListener('change', function() {
        selectAllRecords();
    });

    // 开始对比按钮事件绑定
    document.getElementById('compareBtn').addEventListener('click', function() {
        renderCompareView();
    });

    // 报告弹窗关闭事件绑定
    document.getElementById('reportModalOverlay').addEventListener('click', function() {
        closeReportModal();
    });
    document.getElementById('reportModalClose').addEventListener('click', function() {
        closeReportModal();
    });

    async function loadHistory() {
        try {
            const data = await apiFetch('/api/history');
            if (!data) return; // 已跳转登录页
            if (!data.success) {
                showEmpty('加载失败，请刷新重试');
                return;
            }
            allRecords = data.data || [];
            updateCounts(data.counts);
            renderList();
        } catch (err) {
            showEmpty('加载失败，请刷新重试');
        }
    }

    function updateCounts(counts) {
        document.getElementById('countAll').textContent = counts.total || 0;
        document.getElementById('countInterview').textContent = counts.interview || 0;
        document.getElementById('countScale').textContent = counts.scale || 0;
        document.getElementById('countTalentType').textContent = counts.talent_type || 0;
    }

    function toggleView() {
        const listView = document.getElementById('listView');
        const compareView = document.getElementById('compareView');

        if (currentView === 'list') {
            listView.style.display = 'block';
            compareView.style.display = 'none';
        } else {
            listView.style.display = 'none';
            compareView.style.display = 'block';
            renderCompareView();
        }
    }

    function renderList() {
        const container = document.getElementById('historyList');
        const records = currentFilter === 'all'
            ? allRecords
            : allRecords.filter(r => r.type === currentFilter);

        if (records.length === 0) {
            container.innerHTML = '';
            document.getElementById('historyEmpty').style.display = 'block';
            return;
        }
        document.getElementById('historyEmpty').style.display = 'none';

        let html = '';
        records.forEach(item => {
            const dateStr = formatDate(item.created_at);
            const typeIcon = item.type === 'interview' ? '🎙️' : item.type === 'scale' ? '📊' : '🧬';
            const isSelected = selectedRecords.has(item.id);
            html += `
                <div class="history-card" data-type="${item.type}" data-id="${item.id}">
                    <input type="checkbox" class="history-card-checkbox" data-id="${item.id}" ${isSelected ? 'checked' : ''}>
                    <div class="history-card-meta">
                        <span class="history-type-badge">${typeIcon} ${item.type_label}</span>
                        <span class="history-date">${dateStr}</span>
                    </div>
                    <h3 class="history-title">${escapeHtml(item.title)}</h3>
                    ${item.subtitle ? `<p class="history-subtitle">${escapeHtml(item.subtitle)}</p>` : ''}
                    <div class="history-actions">
                        <button class="history-btn" data-action="view" data-type="${item.type}" data-id="${item.id}" data-session-id="${item.session_id || ''}">查看结果</button>
                        ${item.type === 'interview' ? '<button class="history-btn" style="background:transparent;color:var(--primary);border:1px solid var(--primary);" data-action="export" data-id="' + item.id + '">导出对话</button>' : ''}
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;

        // 绑定事件委托
        container.querySelectorAll('.history-card-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleRecordSelection(parseInt(this.dataset.id), this.checked);
            });
        });
        container.querySelectorAll('[data-action="view"]').forEach(btn => {
            btn.addEventListener('click', function() {
                viewRecord(this.dataset.type, this.dataset.id, this.dataset.sessionId || '');
            });
        });
        container.querySelectorAll('[data-action="export"]').forEach(btn => {
            btn.addEventListener('click', function() {
                exportInterview(parseInt(this.dataset.id));
            });
        });
    }

    window.renderCompareView = function() {
        const records = currentFilter === 'all'
            ? allRecords
            : allRecords.filter(r => r.type === currentFilter);

        const selected = records.filter(r => selectedRecords.has(r.id));

        if (selected.length < 2) {
            document.getElementById('compareCharts').innerHTML = `
                <div class="compare-empty">
                    <p>请至少选择 2 条记录进行对比</p>
                    <p style="font-size: 0.85rem; color: var(--body-muted); margin-top: 8px;">在列表视图中勾选记录后切换到对比视图</p>
                </div>
            `;
            return;
        }

        // 渲染时间线
        renderTimeline(selected);

        // 渲染图表
        renderCompareCharts(selected);
    };

    function renderTimeline(records) {
        const container = document.getElementById('compareTimeline');
        const sorted = [...records].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

        let html = '';
        sorted.forEach(record => {
            const dateStr = formatDate(record.created_at);
            const typeIcon = record.type === 'interview' ? '🎙️' : record.type === 'scale' ? '📊' : '🧬';
            html += `
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">${dateStr}</div>
                    <div class="timeline-label">${typeIcon} ${escapeHtml(record.title)}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    function renderCompareCharts(records) {
        const container = document.getElementById('compareCharts');

        // 按类型分组
        const scaleRecords = records.filter(r => r.type === 'scale');
        const talentTypeRecords = records.filter(r => r.type === 'talent_type');

        let html = '';

        if (scaleRecords.length >= 2) {
            html += `
                <div class="compare-chart-card">
                    <h3 class="compare-chart-title">量表维度对比（雷达图）</h3>
                    <div class="compare-chart-container">
                        <canvas id="scaleRadarChart"></canvas>
                    </div>
                    <div class="compare-legend" id="scaleLegend"></div>
                </div>
            `;
        }

        if (talentTypeRecords.length >= 2) {
            html += `
                <div class="compare-chart-card">
                    <h3 class="compare-chart-title">类型学维度对比（柱状图）</h3>
                    <div class="compare-chart-container">
                        <canvas id="talentTypeBarChart"></canvas>
                    </div>
                    <div class="compare-legend" id="talentTypeLegend"></div>
                </div>
            `;
        }

        if (html === '') {
            html = `
                <div class="compare-empty">
                    <p>所选记录类型不支持对比</p>
                    <p style="font-size: 0.85rem; color: var(--body-muted); margin-top: 8px;">请选择同类型的记录（量表或类型学）进行对比</p>
                </div>
            `;
        }

        container.innerHTML = html;

        // 渲染图表
        if (scaleRecords.length >= 2) {
            renderScaleRadarChart(scaleRecords);
        }
        if (talentTypeRecords.length >= 2) {
            renderTalentTypeBarChart(talentTypeRecords);
        }
    }

    function renderScaleRadarChart(records) {
        const ctx = document.getElementById('scaleRadarChart').getContext('2d');
        const colors = ['#0066cc', '#34c759', '#ff9500', '#af52de', '#ff2d55', '#5856d6'];

        // 获取所有维度
        const dimensions = new Set();
        records.forEach(record => {
            if (record.dimensions) {
                Object.keys(record.dimensions).forEach(dim => dimensions.add(dim));
            }
        });
        const labels = Array.from(dimensions);

        // 准备数据
        const datasets = records.map((record, index) => {
            const data = labels.map(dim => record.dimensions[dim] || 0);
            return {
                label: formatDate(record.created_at),
                data: data,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '20',
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: colors[index % colors.length]
            };
        });

        // 销毁旧图表
        if (compareChart) {
            compareChart.destroy();
        }

        compareChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });

        // 渲染图例
        const legendContainer = document.getElementById('scaleLegend');
        let legendHtml = '';
        records.forEach((record, index) => {
            legendHtml += `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${colors[index % colors.length]}"></div>
                    <span>${formatDate(record.created_at)}</span>
                </div>
            `;
        });
        legendContainer.innerHTML = legendHtml;
    }

    function renderTalentTypeBarChart(records) {
        const ctx = document.getElementById('talentTypeBarChart').getContext('2d');
        const colors = ['#0066cc', '#34c759', '#ff9500', '#af52de', '#ff2d55', '#5856d6'];

        // 获取所有维度
        const dimensions = new Set();
        records.forEach(record => {
            if (record.scores) {
                Object.keys(record.scores).forEach(dim => dimensions.add(dim));
            }
        });
        const labels = Array.from(dimensions);

        // 准备数据
        const datasets = records.map((record, index) => {
            const data = labels.map(dim => record.scores[dim] || 0);
            return {
                label: formatDate(record.created_at),
                data: data,
                backgroundColor: colors[index % colors.length] + '80',
                borderColor: colors[index % colors.length],
                borderWidth: 1
            };
        });

        // 销毁旧图表
        if (compareChart) {
            compareChart.destroy();
        }

        compareChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });

        // 渲染图例
        const legendContainer = document.getElementById('talentTypeLegend');
        let legendHtml = '';
        records.forEach((record, index) => {
            legendHtml += `
                <div class="legend-item">
                    <div class="legend-color" style="background: ${colors[index % colors.length]}"></div>
                    <span>${formatDate(record.created_at)}</span>
                </div>
            `;
        });
        legendContainer.innerHTML = legendHtml;
    }

    window.toggleRecordSelection = function(id, checked) {
        if (checked) {
            selectedRecords.add(id);
        } else {
            selectedRecords.delete(id);
        }
        updateCompareButton();
    };

    window.selectAllRecords = function() {
        const records = currentFilter === 'all'
            ? allRecords
            : allRecords.filter(r => r.type === currentFilter);

        const checkboxes = document.querySelectorAll('.history-card-checkbox');
        const allChecked = records.every(r => selectedRecords.has(r.id));

        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
            const id = parseInt(cb.dataset.id);
            if (!allChecked) {
                selectedRecords.add(id);
            } else {
                selectedRecords.delete(id);
            }
        });

        updateCompareButton();
    };

    function updateCompareButton() {
        const btn = document.getElementById('compareBtn');
        if (btn) {
            btn.disabled = selectedRecords.size < 2;
        }
    }

    window.viewRecord = async function(type, id, sessionId) {
        if (type === 'talent_type' && sessionId) {
            window.location.href = '/talent-type/result/' + sessionId;
            return;
        }
        if (type === 'scale' && sessionId) {
            try {
                const data = await apiFetch('/api/history/scale/' + sessionId);
                if (!data) return; // 已跳转登录页
                if (!data.success) {
                    alert('加载记录失败');
                    return;
                }
                // 跳转到结果页
                window.location.href = '/scale/result?session_id=' + data.session_id;
            } catch (err) {
                alert('加载记录失败');
            }
            return;
        }
        if (type === 'interview') {
            try {
                const data = await apiFetch('/api/history/interview/' + id);
                if (!data) return; // 已跳转登录页
                if (!data.success) {
                    alert('加载报告失败');
                    return;
                }
                showReportModal(data.report);
            } catch (err) {
                alert('加载报告失败');
            }
            return;
        }
    };

    window.showReportModal = function(report) {
        const body = document.getElementById('reportModalBody');
        if (typeof marked !== 'undefined' && report) {
            body.innerHTML = DOMPurify.sanitize(marked.parse(report));
        } else {
            body.innerHTML = '<pre style="white-space:pre-wrap;">' + escapeHtml(report || '无报告内容') + '</pre>';
        }
        document.getElementById('reportModal').style.display = 'block';
        document.body.style.overflow = 'hidden';
    };

    window.closeReportModal = function() {
        document.getElementById('reportModal').style.display = 'none';
        document.body.style.overflow = '';
    };

    window.exportInterview = function(id) {
        window.location.href = '/api/history/interview/' + id + '/export';
    };

    function formatDate(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    }

    function showEmpty(msg) {
        document.getElementById('historyList').innerHTML = '';
        const empty = document.getElementById('historyEmpty');
        empty.style.display = 'block';
        empty.querySelector('p').textContent = msg;
    }
})();
