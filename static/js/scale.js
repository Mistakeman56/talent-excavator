/**
 * static/js/scale.js — 天赋维度量表测评页交互逻辑
 *
 * 本文件管理量表测评页面的所有前端交互，包括：
 * 1. 题目加载 — 从 API 获取一级量表题目并扁平化
 * 2. 答题交互 — 选择选项、自动跳转下一题、手动导航
 * 3. 进度保存 — 使用 localStorage 自动保存答题进度
 * 4. 进度恢复 — 页面加载时检测并恢复上次的答题进度
 * 5. 答案提交 — 提交到后端计算得分
 *
 * 量表结构：
 * - 一级量表：20道题，5个维度（认知洞察型/创造表达型/社交协同型/系统推动型/身体感知型）
 * - 每个维度4道题，其中包含反向计分题
 * - 用户选择1-5分（完全不符合 → 完全符合）
 *
 * 答题流程：
 * ┌─────────────────────────────────────────────────────────────┐
 * │  欢迎页面（scaleWelcome）                                    │
 * │  ┌──────────────────────────────────────────────────────┐   │
 * │  │  [开始测评] 按钮                                      │   │
 * │  └──────────────────────────────────────────────────────┘   │
 * │                            ↓ 点击按钮                        │
 * │  检测 localStorage 是否有未完成的进度                        │
 * │                            ↓ 有进度则提示恢复                │
 * │  答题页面（scaleScreen）                                     │
 * │  ┌──────────────────────────────────────────────────────┐   │
 * │  │  进度条 + 题目编号 + 维度标签                          │   │
 * │  │  题目文本                                              │   │
 * │  │  选项列表（1-5分）                                     │   │
 * │  │  [上一题] [下一题/提交]                                │   │
 * │  └──────────────────────────────────────────────────────┘   │
 * │                            ↓ 选择选项自动跳转                │
 * │  最后一题 → 点击提交                                        │
 * │                            ↓                                │
 * │  跳转到结果页面                                              │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 依赖：
 * - utils.js: 提供 escapeHtml() 等公共工具函数
 */

// ============================================================
// 量表状态
// ============================================================
const scaleState = {
    questions: [],        // 扁平化后的题目数组
    currentIndex: 0,      // 当前题目索引
    answers: {},          // 用户答案 {"q1": 4, "q2": 5, ...}
    scaleData: null,      // 原始量表数据（包含维度信息和选项配置）
    isTransitioning: false // 防止快速点击导致跳转混乱的锁
};

// localStorage 存储键名
const SCALE_STORAGE_KEY = 'scale_progress';

// ============================================================
// 进度保存/恢复函数
// ============================================================

/**
 * 保存当前答题进度到 localStorage
 *
 * 说明：
 * - 每次选择选项后自动调用
 * - 保存的数据结构：{ answers, currentIndex, timestamp }
 * - timestamp 用于判断进度是否过期（可选）
 */
function saveProgress() {
    const data = {
        answers: scaleState.answers,
        currentIndex: scaleState.currentIndex,
        timestamp: Date.now()
    };
    localStorage.setItem(SCALE_STORAGE_KEY, JSON.stringify(data));
}

/**
 * 从 localStorage 加载保存的进度
 * @returns {Object|null} 保存的进度数据，如果没有则返回 null
 */
function loadSavedProgress() {
    try {
        const raw = localStorage.getItem(SCALE_STORAGE_KEY);
        if (!raw) return null;
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

/**
 * 清除保存的进度（提交成功后调用）
 */
function clearProgress() {
    localStorage.removeItem(SCALE_STORAGE_KEY);
}

// ============================================================
// DOM 元素引用
// ============================================================
const els = {
    welcomeScreen: document.getElementById('scaleWelcome'),    // 欢迎页面
    scaleScreen: document.getElementById('scaleScreen'),       // 答题页面
    btnStart: document.getElementById('btnStartScale'),        // 开始按钮
    progressFill: document.getElementById('scaleProgressFill'),// 进度条填充
    progressText: document.getElementById('progressText'),     // 进度文本
    questionNumber: document.getElementById('questionNumber'), // 题目编号
    questionText: document.getElementById('questionText'),     // 题目文本
    optionsList: document.getElementById('optionsList'),       // 选项列表
    btnPrev: document.getElementById('btnPrev'),               // 上一题按钮
    btnNext: document.getElementById('btnNext'),               // 下一题按钮
    submitLoading: document.getElementById('submitLoading')    // 提交加载状态
};

// ============================================================
// 初始化函数
// ============================================================

/**
 * 初始化量表 — 加载题目并渲染第一题
 *
 * 说明：
 * - 从 API 获取一级量表题目数据
 * - 将按维度组织的题目扁平化为一维数组
 * - 每道题添加 dimension、dimensionName、globalIndex 属性
 * - 渲染第一题
 */
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

        // 将按维度组织的题目扁平化为一维数组
        let index = 0;
        for (const [dimKey, dimData] of Object.entries(data.data.dimensions)) {
            for (const q of dimData.questions) {
                scaleState.questions.push({
                    ...q,
                    dimension: dimKey,           // 维度标识（如 "cognitive"）
                    dimensionName: dimData.name, // 维度名称（如 "认知洞察型"）
                    globalIndex: index++         // 全局索引
                });
            }
        }

        renderQuestion(0);
    } catch (err) {
        alert('网络错误：' + err.message);
    }
}

// ============================================================
// 渲染函数
// ============================================================

/**
 * 渲染指定索引的题目
 * @param {number} index - 题目索引
 *
 * 说明：
 * - 更新进度条、题目编号、题目文本
 * - 渲染选项列表（5个选项，标记已选中的）
 * - 更新导航按钮状态（第一题隐藏"上一题"，最后一题显示"提交"）
 */
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

    // 题目信息
    els.questionNumber.textContent = `第 ${index + 1} 题 · ${q.dimensionName}`;
    els.questionText.textContent = q.text;

    // 选项列表
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

    // 导航按钮状态
    els.btnPrev.style.visibility = index === 0 ? 'hidden' : 'visible';

    if (index === total - 1) {
        // 最后一题：显示"提交量表"按钮
        els.btnNext.innerHTML = `
            提交量表
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
        `;
    } else {
        // 非最后一题：显示"下一题"按钮
        els.btnNext.innerHTML = `
            下一题
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
        `;
    }
}

// ============================================================
// 答题交互函数
// ============================================================

/**
 * 选择选项
 * @param {string} questionId - 题目ID（如 "q1"）
 * @param {number} value - 选择的分值（1-5）
 *
 * 说明：
 * - 记录用户选择
 * - 更新 UI（标记选中状态）
 * - 保存进度到 localStorage
 * - 自动跳转到下一题（250ms 延迟，最后一题除外）
 */
function selectOption(questionId, value) {
    // 防止快速重复点击
    if (scaleState.isTransitioning) return;

    scaleState.answers[questionId] = value;
    saveProgress();

    // 更新UI（标记选中状态）
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
        }, 250);  // 250ms 延迟，让用户看到选中效果
    }
}

// ============================================================
// 导航按钮事件
// ============================================================

// 上一题按钮
els.btnPrev.addEventListener('click', () => {
    if (scaleState.currentIndex > 0) {
        scaleState.currentIndex--;
        renderQuestion(scaleState.currentIndex);
    }
});

// 下一题/提交按钮
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
        // 非最后一题：跳转到下一题
        scaleState.isTransitioning = true;
        scaleState.currentIndex++;
        renderQuestion(scaleState.currentIndex);
        scaleState.isTransitioning = false;
    } else {
        // 最后一题：提交量表
        submitScale();
    }
});

// ============================================================
// 提交函数
// ============================================================

/**
 * 提交量表答案
 *
 * 说明：
 * - 显示加载状态
 * - 调用 /api/scale/submit 接口
 * - 成功后清除 localStorage 进度
 * - 跳转到结果页面
 */
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

        // 成功：清除进度并跳转到结果页
        clearProgress();
        window.location.href = '/scale/result?session_id=' + data.session_id;

    } catch (err) {
        alert('网络错误：' + err.message);
        els.submitLoading.style.display = 'none';
    }
}

// ============================================================
// 开始按钮事件
// ============================================================

/**
 * 开始测评按钮点击事件
 *
 * 说明：
 * - 隐藏欢迎页面，显示答题页面
 * - 加载题目
 * - 检测 localStorage 是否有未完成的进度
 * - 如果有进度，提示用户是否继续
 */
els.btnStart.addEventListener('click', () => {
    els.welcomeScreen.style.display = 'none';
    els.scaleScreen.style.display = 'flex';
    initScale().then(() => {
        // 检测是否有保存的进度
        const saved = loadSavedProgress();
        if (saved && saved.answers && Object.keys(saved.answers).length > 0) {
            const count = Object.keys(saved.answers).length;
            if (confirm(`检测到上次未完成的答题进度（已答 ${count} 题），是否继续？`)) {
                // 恢复进度
                scaleState.answers = saved.answers;
                scaleState.currentIndex = Math.min(saved.currentIndex || 0, scaleState.questions.length - 1);
                renderQuestion(scaleState.currentIndex);
            }
        }
    });
});
