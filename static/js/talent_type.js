/**
 * static/js/talent_type.js — 天赋类型学测评页交互逻辑
 *
 * 本文件管理天赋类型学测评页面的所有前端交互，包括：
 * 1. 题目加载 — 从 API 获取 40 道情境迫选题
 * 2. 答题交互 — 单击选中、双击选中并跳转、键盘快捷键
 * 3. 进度保存 — 使用 localStorage 自动保存答题进度
 * 4. 进度恢复 — 页面加载时检测并恢复上次的答题进度
 * 5. 答案提交 — 提交到后端计算 4 字母类型代码
 *
 * 测评设计：
 * - 40 道情境迫选题，分 4 个模组
 * - Module I (t1-t12) → 第1位字母：天赋形态（C/R/B/S）
 * - Module II (t13-t22) → 第2位字母：能量模式（D/R/V）
 * - Module III (t23-t30) → 第3位字母：驱动来源（A/H）
 * - Module IV (t31-t40) → 第4位字母：兴趣指向（M/C/P）
 * - 总组合 = 4 × 3 × 2 × 3 = 72 种天赋类型
 *
 * 答题交互：
 * - 单击选项：选中（不跳转）
 * - 双击选项：选中并跳到下一题
 * - 数字键（1-2）：快速选择选项
 * - Enter：跳到下一题 / 提交
 *
 * 依赖：
 * - utils.js: 提供 escapeHtml() 等公共工具函数
 */
(function () {
    // ============================================================
    // 维度标签映射
    // ============================================================
    // 用于在题目上方显示当前题目所属的维度名称
    const DIM_LABELS = {
        dim1: '认知模式',    // Module I: 天赋形态
        dim2: '专注方式',    // Module II: 能量模式
        dim3: '驱动力',      // Module III: 驱动来源
        dim4: '价值取向'     // Module IV: 兴趣指向
    };

    // localStorage 存储键名
    const TT_STORAGE_KEY = 'tt_progress';

    // ============================================================
    // 状态变量
    // ============================================================
    let questions = [];   // 所有 40 道题目
    let answers = {};     // 用户答案 {"t1": "a", "t2": "c", ...}
    let currentIndex = 0; // 当前题目索引

    // ============================================================
    // 进度保存/恢复函数
    // ============================================================

    /**
     * 保存当前答题进度到 localStorage
     *
     * 说明：
     * - 每次选择选项后自动调用
     * - 保存的数据结构：{ answers, currentIndex, timestamp }
     */
    function saveProgress() {
        const data = { answers, currentIndex, timestamp: Date.now() };
        localStorage.setItem(TT_STORAGE_KEY, JSON.stringify(data));
    }

    /**
     * 从 localStorage 加载保存的进度
     * @returns {Object|null} 保存的进度数据，如果没有则返回 null
     */
    function loadSavedProgress() {
        try {
            const raw = localStorage.getItem(TT_STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * 清除保存的进度（提交成功后调用）
     */
    function clearProgress() {
        localStorage.removeItem(TT_STORAGE_KEY);
    }

    // ============================================================
    // DOM 元素引用
    // ============================================================
    const welcome = document.getElementById('ttWelcome');        // 欢迎页面
    const screen = document.getElementById('ttScreen');          // 答题页面
    const loading = document.getElementById('ttSubmitLoading');  // 提交加载状态
    const btnStart = document.getElementById('ttBtnStart');      // 开始按钮
    const btnPrev = document.getElementById('ttBtnPrev');        // 上一题按钮
    const btnNext = document.getElementById('ttBtnNext');        // 下一题/提交按钮
    const progressFill = document.getElementById('ttProgressFill'); // 进度条填充
    const progressText = document.getElementById('ttProgressText'); // 进度文本
    const dimLabel = document.getElementById('ttDimLabel');      // 维度标签
    const questionNum = document.getElementById('ttQuestionNum');// 题目编号
    const questionText = document.getElementById('ttQuestionText'); // 题目文本
    const optionsEl = document.getElementById('ttOptions');      // 选项容器

    // ============================================================
    // 加载题目
    // ============================================================

    /**
     * 从 API 加载所有题目
     *
     * 说明：
     * - 调用 /api/talent-type/questions 接口
     * - 返回的题目不包含正确答案（迫选题没有对错之分）
     * - 每道题有 2 个选项，每个选项对应不同维度的得分权重
     */
    async function loadQuestions() {
        try {
            const resp = await fetch('/api/talent-type/questions');
            const data = await resp.json();
            if (data.success) {
                questions = data.questions;
            } else {
                alert('题目加载失败，请刷新重试');
            }
        } catch (e) {
            alert('网络错误，请检查连接后刷新');
        }
    }

    // ============================================================
    // 渲染函数
    // ============================================================

    /**
     * 渲染当前题目
     *
     * 说明：
     * - 更新进度条、维度标签、题目编号、题目文本
     * - 渲染选项列表（2个选项）
     * - 更新导航按钮状态
     *
     * 选项交互：
     * - 单击：选中（不跳转）— 方便用户修改答案
     * - 双击：选中并跳到下一题 — 快速答题
     */
    function renderQuestion() {
        const q = questions[currentIndex];
        const answerKey = q.id;
        const selected = answers[answerKey] || null;

        // 进度
        const pct = ((currentIndex) / questions.length) * 100;
        progressFill.style.width = pct + '%';
        progressText.textContent = (currentIndex + 1) + ' / ' + questions.length;

        // 元信息
        dimLabel.textContent = DIM_LABELS[q.dimension] || q.dimension;
        questionNum.textContent = '第 ' + (currentIndex + 1) + ' 题';
        questionText.textContent = q.text;

        // 选项
        optionsEl.innerHTML = '';
        q.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'tt-option' + (selected === opt.key ? ' selected' : '');
            btn.innerHTML = '<span class="tt-option-letter">' + opt.key.toUpperCase() + '</span>' + escapeHtml(opt.text);

            // 单击 = 选中（不跳转）
            btn.addEventListener('click', () => {
                answers[q.id] = opt.key;
                saveProgress();
                renderQuestion();
            });

            // 双击 = 选中并跳到下一题（最后一题双击不跳转，留给用户手动提交）
            btn.addEventListener('dblclick', () => {
                answers[q.id] = opt.key;
                saveProgress();
                renderQuestion();
                if (currentIndex < questions.length - 1) {
                    currentIndex++;
                    saveProgress();
                    renderQuestion();
                }
            });

            optionsEl.appendChild(btn);
        });

        // 按钮状态
        btnPrev.style.visibility = currentIndex === 0 ? 'hidden' : 'visible';

        if (currentIndex === questions.length - 1) {
            // 最后一题：显示"提交结果"按钮
            btnNext.innerHTML = '提交结果<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-5"/></svg>';
            btnNext.className = 'tt-btn-next tt-btn-submit';
        } else {
            // 非最后一题：显示"下一题"按钮
            btnNext.innerHTML = '下一题<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
            btnNext.className = 'tt-btn-next';
        }
        btnNext.disabled = !selected;  // 未选中时禁用按钮
    }

    // ============================================================
    // 导航函数
    // ============================================================

    /**
     * 跳到下一题或提交
     *
     * 说明：
     * - 最后一题：调用提交函数
     * - 其他题目：跳转到下一题
     */
    function goNext() {
        if (currentIndex >= questions.length - 1) {
            submitAnswers();
            return;
        }
        currentIndex++;
        saveProgress();
        renderQuestion();
    }

    /**
     * 跳到上一题
     */
    function goPrev() {
        if (currentIndex > 0) {
            currentIndex--;
            saveProgress();
            renderQuestion();
        }
    }

    // ============================================================
    // 提交函数
    // ============================================================

    /**
     * 提交答题结果
     *
     * 说明：
     * - 隐藏答题页面，显示加载状态
     * - 调用 /api/talent-type/submit 接口
     * - 成功后清除 localStorage 进度
     * - 跳转到结果页面
     */
    async function submitAnswers() {
        screen.style.display = 'none';
        loading.style.display = 'flex';

        try {
            const resp = await fetch('/api/talent-type/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers: answers })
            });
            const data = await resp.json();
            if (data.success) {
                clearProgress();
                window.location.href = '/talent-type/result/' + data.session_id;
            } else {
                if (data.need_login) {
                    alert('请先登录后再进行测评');
                    window.location.href = '/login';
                    return;
                }
                alert('提交失败：' + (data.error || '未知错误'));
                screen.style.display = 'block';
                loading.style.display = 'none';
            }
        } catch (e) {
            alert('网络错误，请重试');
            screen.style.display = 'block';
            loading.style.display = 'none';
        }
    }

    // ============================================================
    // 事件绑定
    // ============================================================

    // 开始测评按钮
    btnStart.addEventListener('click', async () => {
        if (questions.length === 0) {
            await loadQuestions();
        }
        if (questions.length === 0) return;

        // 检测是否有保存的进度
        const saved = loadSavedProgress();
        if (saved && saved.answers && Object.keys(saved.answers).length > 0) {
            const count = Object.keys(saved.answers).length;
            if (confirm(`检测到上次未完成的答题进度（已答 ${count}/${questions.length} 题），是否继续？`)) {
                // 恢复进度
                answers = saved.answers;
                currentIndex = Math.min(saved.currentIndex || 0, questions.length - 1);
            }
        }

        welcome.style.display = 'none';
        screen.style.display = 'block';
        renderQuestion();
    });

    // 导航按钮
    btnNext.addEventListener('click', goNext);
    btnPrev.addEventListener('click', goPrev);

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        // 答题页面未显示时忽略
        if (screen.style.display === 'none') return;
        const q = questions[currentIndex];
        if (!q) return;

        // 数字键选选项（仅选中，不跳转）
        const optIndex = parseInt(e.key) - 1;
        if (optIndex >= 0 && optIndex < q.options.length) {
            answers[q.id] = q.options[optIndex].key;
            saveProgress();
            renderQuestion();
            return;
        }

        // Enter 跳到下一题 / 提交
        if (e.key === 'Enter') {
            if (answers[q.id] && !btnNext.disabled) goNext();
        }
    });
})();
