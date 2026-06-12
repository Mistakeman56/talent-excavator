// ===== 量表状态 =====
const scaleState = {
    questions: [],
    currentIndex: 0,
    answers: {},
    scaleData: null,
    isTransitioning: false  // 防止快速点击导致跳转混乱
};

const SCALE_STORAGE_KEY = 'scale_progress';

// ===== 进度保存/恢复 =====
function saveProgress() {
    const data = {
        answers: scaleState.answers,
        currentIndex: scaleState.currentIndex,
        timestamp: Date.now()
    };
    localStorage.setItem(SCALE_STORAGE_KEY, JSON.stringify(data));
}

function loadSavedProgress() {
    try {
        const raw = localStorage.getItem(SCALE_STORAGE_KEY);
        if (!raw) return null;
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

function clearProgress() {
    localStorage.removeItem(SCALE_STORAGE_KEY);
}

// ===== DOM 元素 =====
const els = {
    welcomeScreen: document.getElementById('scaleWelcome'),
    scaleScreen: document.getElementById('scaleScreen'),
    btnStart: document.getElementById('btnStartScale'),
    progressFill: document.getElementById('scaleProgressFill'),
    progressText: document.getElementById('progressText'),
    questionNumber: document.getElementById('questionNumber'),
    questionText: document.getElementById('questionText'),
    optionsList: document.getElementById('optionsList'),
    btnPrev: document.getElementById('btnPrev'),
    btnNext: document.getElementById('btnNext'),
    submitLoading: document.getElementById('submitLoading')
};

// ===== 初始化 =====
async function initScale() {
    try {
        const res = await fetch('/api/scale/questions');
        const data = await res.json();
        
        if (!data.success) {
            alert('加载量表失败');
            return;
        }
        
        scaleState.scaleData = data.data;
        scaleState.questions = [];
        
        // 将题目扁平化为数组
        let index = 0;
        for (const [dimKey, dimData] of Object.entries(data.data.dimensions)) {
            for (const q of dimData.questions) {
                scaleState.questions.push({
                    ...q,
                    dimension: dimKey,
                    dimensionName: dimData.name,
                    globalIndex: index++
                });
            }
        }
        
        renderQuestion(0);
    } catch (err) {
        alert('网络错误：' + err.message);
    }
}

// ===== 渲染题目 =====
function renderQuestion(index) {
    // 边界检查
    if (index < 0 || index >= scaleState.questions.length) {
        return;
    }
    const q = scaleState.questions[index];
    const total = scaleState.questions.length;
    
    // 进度条
    const pct = ((index + 1) / total) * 100;
    els.progressFill.style.width = pct + '%';
    els.progressText.textContent = `${index + 1} / ${total}`;
    
    // 题目
    els.questionNumber.textContent = `第 ${index + 1} 题 · ${q.dimensionName}`;
    els.questionText.textContent = q.text;
    
    // 选项
    const options = scaleState.scaleData.scoring.options;
    let optionsHtml = '';
    for (const opt of options) {
        const selected = scaleState.answers[q.id] === opt.value ? 'selected' : '';
        optionsHtml += `
            <div class="option-item ${selected}" data-value="${opt.value}" onclick="selectOption('${q.id}', ${opt.value})">
                <span class="option-value">${opt.value}</span>
                <span class="option-label">${opt.label}</span>
            </div>
        `;
    }
    els.optionsList.innerHTML = optionsHtml;
    
    // 导航按钮
    els.btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';
    
    if (index === total - 1) {
        els.btnNext.innerHTML = `
            提交量表
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
        `;
    } else {
        els.btnNext.innerHTML = `
            下一题
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
        `;
    }
}

// ===== 选择选项 =====
function selectOption(questionId, value) {
    // 防止快速重复点击
    if (scaleState.isTransitioning) return;

    scaleState.answers[questionId] = value;
    saveProgress();

    // 更新UI
    const items = els.optionsList.querySelectorAll('.option-item');
    items.forEach(item => {
        item.classList.toggle('selected', parseInt(item.dataset.value) === value);
    });

    // 自动跳到下一题（最后一题除外）
    if (scaleState.currentIndex < scaleState.questions.length - 1) {
        scaleState.isTransitioning = true;
        setTimeout(() => {
            scaleState.currentIndex++;
            saveProgress();
            renderQuestion(scaleState.currentIndex);
            scaleState.isTransitioning = false;
        }, 250);
    }
}

// ===== 导航 =====
els.btnPrev.addEventListener('click', () => {
    if (scaleState.currentIndex > 0) {
        scaleState.currentIndex--;
        renderQuestion(scaleState.currentIndex);
    }
});

els.btnNext.addEventListener('click', () => {
    // 防止快速重复点击
    if (scaleState.isTransitioning) return;

    const q = scaleState.questions[scaleState.currentIndex];
    if (!q) return;

    // 检查是否已选
    if (!scaleState.answers[q.id]) {
        alert('请先选择一个选项');
        return;
    }

    if (scaleState.currentIndex < scaleState.questions.length - 1) {
        scaleState.isTransitioning = true;
        scaleState.currentIndex++;
        renderQuestion(scaleState.currentIndex);
        // 立即按钮点击不需要延迟解锁
        scaleState.isTransitioning = false;
    } else {
        submitScale();
    }
});

// ===== 提交 =====
async function submitScale() {
    if (!els.submitLoading) {
        alert('页面元素异常，请刷新重试');
        return;
    }
    els.submitLoading.style.display = 'flex';

    try {
        const res = await fetch('/api/scale/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers: scaleState.answers })
        });

        const data = await res.json();

        if (!data.success) {
            if (data.need_login) {
                alert('请先登录后再进行测评');
                window.location.href = '/login';
                return;
            }
            alert('提交失败：' + data.error);
            els.submitLoading.style.display = 'none';
            return;
        }

        // 跳转到结果页
        clearProgress();
        window.location.href = '/scale/result?session_id=' + data.session_id;

    } catch (err) {
        alert('网络错误：' + err.message);
        els.submitLoading.style.display = 'none';
    }
}

// ===== 开始 =====
els.btnStart.addEventListener('click', () => {
    els.welcomeScreen.style.display = 'none';
    els.scaleScreen.style.display = 'flex';
    initScale().then(() => {
        const saved = loadSavedProgress();
        if (saved && saved.answers && Object.keys(saved.answers).length > 0) {
            const count = Object.keys(saved.answers).length;
            if (confirm(`检测到上次未完成的答题进度（已答 ${count} 题），是否继续？`)) {
                scaleState.answers = saved.answers;
                scaleState.currentIndex = Math.min(saved.currentIndex || 0, scaleState.questions.length - 1);
                renderQuestion(scaleState.currentIndex);
            }
        }
    });
});
