// ===== 状态管理 =====
const state = {
    round: 0,
    isLoading: false,
    canReport: false,
    suggestReport: false,
    forceReport: false
};

// ===== DOM 元素 =====
const els = {
    welcomeScreen: document.getElementById('welcomeScreen'),
    chatScreen: document.getElementById('chatScreen'),
    chatHistory: document.getElementById('chatHistory'),
    chatHeader: document.getElementById('chatHeader'),
    roundNum: document.getElementById('roundNum'),
    progressFill: document.getElementById('progressFill'),
    userInput: document.getElementById('userInput'),
    btnStart: document.getElementById('btnStart'),
    btnSend: document.getElementById('btnSend'),
    btnReport: document.getElementById('btnReport'),
    inputArea: document.getElementById('inputArea'),
    reportNotice: document.getElementById('reportNotice'),
    reportActions: document.getElementById('reportActions')
};

// ===== 工具函数 =====
function showLoading(text = 'AI 思考中...') {
    state.isLoading = true;
    els.userInput.disabled = true;
    els.btnSend.disabled = true;

    const bubble = document.createElement('div');
    bubble.className = 'thinking-bubble';
    bubble.id = 'thinkingBubble';
    bubble.innerHTML = `
        <div class="message-avatar ai">AI</div>
        <div class="thinking-dots">
            <span></span><span></span><span></span>
        </div>
        <span class="thinking-text">${escapeHtml(text)}</span>
    `;
    els.chatHistory.appendChild(bubble);
    scrollToBottom();
}

function hideLoading() {
    state.isLoading = false;
    els.userInput.disabled = false;
    els.btnSend.disabled = false;
    els.userInput.focus();

    const bubble = document.getElementById('thinkingBubble');
    if (bubble) bubble.remove();
}

function updateProgress(round) {
    const maxRounds = 15;
    const pct = Math.min((round / maxRounds) * 100, 100);
    els.progressFill.style.width = pct + '%';
    els.roundNum.textContent = round;
}

function scrollToBottom() {
    els.chatHistory.scrollTop = els.chatHistory.scrollHeight;
}

// ===== 渲染函数 =====
function renderAIMessage(data, round) {
    const block = document.createElement('div');
    block.className = 'message-block ai-msg';

    const hasAnalysis = data.signal || data.hypothesis || data.judgment;
    const questionText = data.question || data.raw || '';

    let html = '';

    // AI 分析卡片
    if (hasAnalysis) {
        html += `<div class="ai-analysis">`;
        if (data.signal) {
            html += `
                <div class="analysis-section">
                    <div class="analysis-label">关键信号</div>
                    <div class="analysis-content">${escapeHtml(data.signal)}</div>
                </div>
            `;
        }
        if (data.hypothesis) {
            html += `
                <div class="analysis-section">
                    <div class="analysis-label">天赋假设</div>
                    <div class="analysis-content">${escapeHtml(data.hypothesis)}</div>
                </div>
            `;
        }
        if (data.judgment) {
            html += `
                <div class="analysis-section">
                    <div class="analysis-label">人类3.0判断</div>
                    <div class="analysis-content">${escapeHtml(data.judgment)}</div>
                </div>
            `;
        }
        html += `</div>`;
    }

    // AI 问题气泡（带左侧头像）
    html += `
        <div class="message-row ai-row">
            <div class="message-avatar ai">AI</div>
            <div class="ai-question">
                <div class="question-header">
                    <span class="question-label">第 ${round} 轮</span>
                </div>
                <div class="question-text">${escapeHtml(questionText)}</div>
            </div>
        </div>
    `;

    block.innerHTML = html;
    els.chatHistory.appendChild(block);
    scrollToBottom();
}

function renderUserMessage(text) {
    const block = document.createElement('div');
    block.className = 'message-block user-msg';

    block.innerHTML = `
        <div class="message-row user-row">
            <div class="message-avatar user">你</div>
            <div class="user-answer">
                <div class="answer-header">
                    <span class="answer-label">你</span>
                </div>
                <div class="answer-text">${escapeHtml(text)}</div>
            </div>
        </div>
    `;

    els.chatHistory.appendChild(block);
    scrollToBottom();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== API 调用 =====
async function apiStart() {
    // 检查登录状态
    try {
        const authRes = await fetch('/api/auth/check');
        const authData = await authRes.json();
        if (!authData.authenticated) {
            window.location.href = '/login?next=/';
            return;
        }
    } catch (err) {
        // 网络错误继续尝试
    }

    // 切换界面
    els.welcomeScreen.style.display = 'none';
    els.chatScreen.style.display = 'flex';
    els.chatHeader.style.display = 'flex';

    showLoading('正在准备访谈...');

    try {
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            alert('启动失败：' + data.error);
            hideLoading();
            return;
        }

        state.round = data.round;
        updateProgress(data.round);
        renderAIMessage(data.data, data.round);

    } catch (err) {
        alert('网络错误：' + err.message);
    } finally {
        hideLoading();
    }
}

async function apiChat(message) {
    showLoading('AI 正在分析你的回答...');

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await res.json();

        if (!data.success) {
            alert('发送失败：' + data.error);
            hideLoading();
            return;
        }

        state.round = data.round;
        state.canReport = data.can_report;
        state.suggestReport = data.suggest_report;
        state.forceReport = data.force_report;

        updateProgress(data.round);
        renderAIMessage(data.data, data.round);

        // 更新报告按钮状态
        if (data.can_report) {
            els.reportActions.style.display = 'flex';
        }
        if (data.suggest_report) {
            els.reportNotice.style.display = 'flex';
        }
        if (data.force_report) {
            els.reportNotice.innerHTML = '<span>✦</span> 已达到最大对话轮数，请生成报告';
            els.reportNotice.style.background = 'linear-gradient(90deg, rgba(212,168,83,0.2), transparent)';
        }

    } catch (err) {
        alert('网络错误：' + err.message);
    } finally {
        hideLoading();
    }
}

async function apiReport() {
    showLoading('正在生成你的天赋报告，这可能需要一些时间...');

    try {
        const res = await fetch('/api/report', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            alert('生成报告失败：' + data.error);
            hideLoading();
            return;
        }

        window.location.href = data.redirect;

    } catch (err) {
        alert('网络错误：' + err.message);
        hideLoading();
    }
}

// ===== 事件绑定 =====
els.btnStart.addEventListener('click', apiStart);

els.btnSend.addEventListener('click', () => {
    const text = els.userInput.value.trim();
    if (!text || state.isLoading) return;

    els.userInput.value = '';
    renderUserMessage(text);
    apiChat(text);
});

els.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        els.btnSend.click();
    }
});

els.btnReport.addEventListener('click', () => {
    if (confirm('确定要生成最终报告吗？生成后将结束本次访谈。')) {
        apiReport();
    }
});

// ===== 自动聚焦 =====
if (els.userInput) {
    els.userInput.focus();
}
