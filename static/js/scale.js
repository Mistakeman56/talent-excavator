// ===== 量表状态 =====
const scaleState = {
    questions: [],
    currentIndex: 0,
    answers: {},
    scaleData: null
};

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
    scaleState.answers[questionId] = value;
    
    // 更新UI
    const items = els.optionsList.querySelectorAll('.option-item');
    items.forEach(item => {
        item.classList.toggle('selected', parseInt(item.dataset.value) === value);
    });
    
    // 自动跳到下一题（最后一题除外）
    if (scaleState.currentIndex < scaleState.questions.length - 1) {
        setTimeout(() => {
            scaleState.currentIndex++;
            renderQuestion(scaleState.currentIndex);
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
    const q = scaleState.questions[scaleState.currentIndex];
    
    // 检查是否已选
    if (!scaleState.answers[q.id]) {
        alert('请先选择一个选项');
        return;
    }
    
    if (scaleState.currentIndex < scaleState.questions.length - 1) {
        scaleState.currentIndex++;
        renderQuestion(scaleState.currentIndex);
    } else {
        submitScale();
    }
});

// ===== 提交 =====
async function submitScale() {
    els.submitLoading.style.display = 'flex';
    
    try {
        const res = await fetch('/api/scale/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers: scaleState.answers })
        });
        
        const data = await res.json();
        
        if (!data.success) {
            alert('提交失败：' + data.error);
            els.submitLoading.style.display = 'none';
            return;
        }
        
        // 保存结果到 localStorage
        localStorage.setItem('scaleResult', JSON.stringify(data));
        
        // 跳转到结果页
        window.location.href = '/scale/result';
        
    } catch (err) {
        alert('网络错误：' + err.message);
        els.submitLoading.style.display = 'none';
    }
}

// ===== 开始 =====
els.btnStart.addEventListener('click', () => {
    els.welcomeScreen.style.display = 'none';
    els.scaleScreen.style.display = 'flex';
    initScale();
});
