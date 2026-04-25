/**
 * 天赋类型学测评 — 答题页交互逻辑
 */
(function () {
    const DIM_LABELS = {
        dim1: '认知模式',
        dim2: '专注方式',
        dim3: '驱动力',
        dim4: '价值取向'
    };

    let questions = [];
    let answers = {};
    let currentIndex = 0;

    // DOM
    const welcome = document.getElementById('ttWelcome');
    const screen = document.getElementById('ttScreen');
    const loading = document.getElementById('ttSubmitLoading');
    const btnStart = document.getElementById('ttBtnStart');
    const btnPrev = document.getElementById('ttBtnPrev');
    const btnNext = document.getElementById('ttBtnNext');
    const progressFill = document.getElementById('ttProgressFill');
    const progressText = document.getElementById('ttProgressText');
    const dimLabel = document.getElementById('ttDimLabel');
    const questionNum = document.getElementById('ttQuestionNum');
    const questionText = document.getElementById('ttQuestionText');
    const optionsEl = document.getElementById('ttOptions');

    // 加载题目
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

    // 渲染当前题目
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
            btn.innerHTML = '<span class="tt-option-letter">' + opt.key.toUpperCase() + '</span>' + opt.text;
            btn.addEventListener('click', () => {
                answers[q.id] = opt.key;
                renderQuestion();
                // 自动跳到下一题（最后一题除外，留给用户确认后手动提交）
                if (currentIndex < questions.length - 1) {
                    setTimeout(() => {
                        currentIndex++;
                        renderQuestion();
                    }, 250);
                }
            });
            optionsEl.appendChild(btn);
        });

        // 按钮状态
        btnPrev.style.visibility = currentIndex === 0 ? 'hidden' : 'visible';
        if (currentIndex === questions.length - 1) {
            btnNext.innerHTML = '提交结果<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12l3 3 5-5"/></svg>';
            btnNext.className = 'tt-btn-next tt-btn-submit';
        } else {
            btnNext.innerHTML = '下一题<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
            btnNext.className = 'tt-btn-next';
        }
        btnNext.disabled = !selected;
    }

    // 下一页
    function goNext() {
        if (currentIndex >= questions.length - 1) {
            submitAnswers();
            return;
        }
        currentIndex++;
        renderQuestion();
    }

    // 上一页
    function goPrev() {
        if (currentIndex > 0) {
            currentIndex--;
            renderQuestion();
        }
    }

    // 提交
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
                window.location.href = '/talent-type/result/' + data.session_id;
            } else {
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

    // 开始测评
    btnStart.addEventListener('click', async () => {
        if (questions.length === 0) {
            await loadQuestions();
        }
        if (questions.length === 0) return;
        welcome.style.display = 'none';
        screen.style.display = 'block';
        renderQuestion();
    });

    btnNext.addEventListener('click', goNext);
    btnPrev.addEventListener('click', goPrev);

    // 键盘快捷键
    document.addEventListener('keydown', (e) => {
        if (screen.style.display === 'none') return;
        const q = questions[currentIndex];
        if (!q) return;
        // 数字键选选项（自动跳转，跟量表逻辑一致）
        const optIndex = parseInt(e.key) - 1;
        if (optIndex >= 0 && optIndex < q.options.length) {
            answers[q.id] = q.options[optIndex].key;
            renderQuestion();
            if (currentIndex < questions.length - 1) {
                setTimeout(() => {
                    currentIndex++;
                    renderQuestion();
                }, 250);
            }
            return;
        }
        // Enter 跳到下一题 / 提交
        if (e.key === 'Enter') {
            if (answers[q.id] && !btnNext.disabled) goNext();
        }
    });
})();