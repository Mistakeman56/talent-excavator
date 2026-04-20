// ===== 结果展示 =====
const resultData = JSON.parse(localStorage.getItem('scaleResult') || '{}');

if (!resultData.scores) {
    document.getElementById('resultScreen').innerHTML = `
        <div class="welcome-card" style="text-align:center; padding: 60px 0;">
            <h2>暂无结果</h2>
            <p style="color: var(--text-secondary); margin: 16px 0;">请先完成一级量表测评</p>
            <a href="/scale" class="btn-start" style="text-decoration:none; display:inline-flex;">
                <span>去测评</span>
            </a>
        </div>
    `;
}

// ===== 渲染雷达图 =====
function renderRadarChart() {
    const scores = resultData.scores;
    const chartDom = document.getElementById('radarChart');
    const myChart = echarts.init(chartDom);
    
    const dimensions = [
        { key: 'cognitive', name: '认知洞察' },
        { key: 'creative', name: '创造表达' },
        { key: 'social', name: '社交连接' },
        { key: 'systemic', name: '系统推动' },
        { key: 'physical', name: '身体感知' }
    ];
    
    const indicator = dimensions.map(d => ({
        name: d.name,
        max: 5
    }));
    
    const values = dimensions.map(d => scores[d.key]?.score || 0);
    
    const option = {
        color: ['#d4a853'],
        radar: {
            indicator: indicator,
            shape: 'polygon',
            splitNumber: 5,
            axisName: {
                color: '#9ca3af',
                fontSize: 14
            },
            splitLine: {
                lineStyle: { color: 'rgba(212, 168, 83, 0.2)' }
            },
            splitArea: {
                areaStyle: { color: ['transparent', 'rgba(212, 168, 83, 0.05)'] }
            },
            axisLine: {
                lineStyle: { color: 'rgba(212, 168, 83, 0.3)' }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: values,
                name: '你的天赋维度',
                areaStyle: { color: 'rgba(212, 168, 83, 0.25)' },
                lineStyle: { color: '#d4a853', width: 2 },
                itemStyle: { color: '#d4a853' }
            }]
        }]
    };
    
    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

// ===== 渲染 Top3 维度 =====
function renderTopDimensions() {
    const container = document.getElementById('topDimensions');
    const top3 = resultData.top_dimensions || [];
    
    let html = '';
    top3.forEach((dim, i) => {
        const rankClass = i === 0 ? 'top-1' : i === 1 ? 'top-2' : 'top-3';
        const scores = resultData.scores || {};
        const desc = scores[dim.key]?.description || '';
        
        html += `
            <div class="dimension-card ${rankClass}">
                <div class="dim-rank">#${i + 1}</div>
                <div class="dim-info">
                    <h4>${dim.name}</h4>
                    <p>${desc}</p>
                    <div class="dim-score">${dim.score.toFixed(1)} / 5.0</div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// ===== 渲染得分条 =====
function renderScoreBars() {
    const container = document.getElementById('scoreBars');
    const scores = resultData.scores || {};
    
    const order = ['cognitive', 'creative', 'social', 'systemic', 'physical'];
    
    let html = '';
    for (const key of order) {
        const s = scores[key];
        if (!s) continue;
        
        const pct = (s.score / 5) * 100;
        
        html += `
            <div class="score-bar-item">
                <div class="score-bar-label">
                    <span>${s.name}</span>
                    <span class="score-bar-value">${s.score.toFixed(1)}</span>
                </div>
                <div class="score-bar-track">
                    <div class="score-bar-fill" style="width: ${pct}%"></div>
                </div>
                <p class="score-bar-desc">${s.description}</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// ===== 二级量表 =====
function initSecondary() {
    const topDim = resultData.top_dimensions?.[0];
    if (!topDim) return;
    
    document.getElementById('secondaryCta').style.display = 'block';
    
    document.getElementById('btnSecondary').addEventListener('click', async () => {
        try {
            const res = await fetch('/api/scale/secondary/questions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dimension: topDim.key })
            });
            
            const data = await res.json();
            
            if (!data.success) {
                alert('加载二级量表失败');
                return;
            }
            
            // 保存二级量表数据并跳转
            localStorage.setItem('secondaryScaleData', JSON.stringify(data));
            localStorage.setItem('secondaryDimension', topDim.key);
            localStorage.setItem('primarySessionId', resultData.session_id);
            
            // 在当前页展示二级量表（简化版）
            startSecondaryScale(data);
            
        } catch (err) {
            alert('网络错误：' + err.message);
        }
    });
}

function startSecondaryScale(data) {
    document.getElementById('secondaryCta').style.display = 'none';
    
    const questions = data.questions;
    let currentIdx = 0;
    const answers = {};
    
    const container = document.getElementById('secondaryResult');
    container.style.display = 'block';
    
    function renderSecondaryQuestion() {
        const q = questions[currentIdx];
        const pct = ((currentIdx + 1) / questions.length) * 100;
        
        container.innerHTML = `
            <h2 class="result-title">二级深度量表 · ${data.dimension_name}</h2>
            <div class="scale-progress" style="margin-bottom: 24px;">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${pct}%"></div>
                </div>
                <span class="progress-text">${currentIdx + 1} / ${questions.length}</span>
            </div>
            <div class="question-card">
                <h3 class="question-text">${q.text}</h3>
                <div class="options-list">
                    ${[1,2,3,4,5].map(v => `
                        <div class="option-item ${answers[q.id] === v ? 'selected' : ''}" 
                             onclick="window.selectSecondary(${v})">
                            <span class="option-value">${v}</span>
                            <span class="option-label">${v === 1 ? '完全不像' : v === 2 ? '不太像' : v === 3 ? '一般' : v === 4 ? '比较像' : '非常像我'}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    window.selectSecondary = async function(value) {
        const q = questions[currentIdx];
        answers[q.id] = value;
        
        if (currentIdx < questions.length - 1) {
            currentIdx++;
            renderSecondaryQuestion();
        } else {
            // 提交二级量表
            container.innerHTML = '<div class="loading-overlay" style="position:relative; background:transparent;"><div class="loading-spinner"></div><p class="loading-text">正在分析...</p></div>';
            
            try {
                const res = await fetch('/api/scale/secondary/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        dimension: localStorage.getItem('secondaryDimension'),
                        answers: answers,
                        primary_session_id: localStorage.getItem('primarySessionId')
                    })
                });
                
                const result = await res.json();
                
                if (result.success) {
                    container.innerHTML = `
                        <h2 class="result-title">你的精准天赋类型</h2>
                        <div class="talent-type-card">
                            <div class="talent-badge">${result.dimension}</div>
                            <h3>${result.talent_type}</h3>
                            <p>${result.talent_description}</p>
                        </div>
                    `;
                }
            } catch (err) {
                alert('提交失败');
            }
        }
    };
    
    renderSecondaryQuestion();
}

// ===== 初始化 =====
if (resultData.scores) {
    renderRadarChart();
    renderTopDimensions();
    renderScoreBars();
    initSecondary();
}
