/**
 * static/js/main.js — AI 深度访谈页交互逻辑
 *
 * 本文件管理 AI 访谈页面的所有前端交互，包括：
 * 1. 状态管理 — 跟踪访谈轮数、加载状态、报告按钮状态
 * 2. DOM 操作 — 渲染 AI 消息、用户消息、思考气泡
 * 3. API 调用 — 开始访谈、提交回答、生成报告、恢复访谈
 * 4. 事件绑定 — 按钮点击、键盘快捷键（Enter 发送）
 *
 * 页面结构：
 * ┌─────────────────────────────────────────────────────────────┐
 * │  首页 Hero 区域                                              │
 * │  ┌──────────────────────────────────────────────────────┐   │
 * │  │  [开始 AI 深度访谈]  [继续上次访谈]  [40 题快速测评]  │   │
 * │  └──────────────────────────────────────────────────────┘   │
 * └─────────────────────────────────────────────────────────────┘
 *                            ↓ 点击按钮
 * ┌─────────────────────────────────────────────────────────────┐
 * │  聊天浮层（chatOverlay）                                     │
 * │  ┌──────────────────────────────────────────────────────┐   │
 * │  │  头部：轮数 + 进度条 + 关闭按钮                       │   │
 * │  ├──────────────────────────────────────────────────────┤   │
 * │  │  对话历史区域（chatHistory）                          │   │
 * │  │  ┌────────────────────────────────────────────────┐  │   │
 * │  │  │  AI 分析卡片（关键信号/天赋假设/HUMAN 3.0判断） │  │   │
 * │  │  │  AI 问题气泡                                    │  │   │
 * │  │  │  用户回答气泡                                   │  │   │
 * │  │  │  ...                                           │  │   │
 * │  │  └────────────────────────────────────────────────┘  │   │
 * │  ├──────────────────────────────────────────────────────┤   │
 * │  │  输入区域：文本框 + 发送按钮 / 报告按钮              │   │
 * │  └──────────────────────────────────────────────────────┘   │
 * └─────────────────────────────────────────────────────────────┘
 *
 * 依赖：
 * - utils.js: 提供 escapeHtml() 等公共工具函数
 */

// ============================================================
// 状态管理
// ============================================================
// 使用全局 state 对象跟踪访谈的所有状态
// 这些状态会在 API 调用成功后更新
const state = {
    round: 0,              // 当前访谈轮数（从1开始）
    isLoading: false,      // 是否正在等待 AI 响应
    canReport: false,      // 是否可以生成报告（>= MIN_QUESTIONS）
    suggestReport: false,  // 是否建议生成报告（>= SUGGEST_REPORT_AT）
    forceReport: false,    // 是否强制生成报告（>= MAX_QUESTIONS）
    isResumed: false       // 是否是恢复的访谈（区别于新开始的访谈）
};

// ============================================================
// DOM 元素引用
// ============================================================
// 缓存常用的 DOM 元素，避免重复查询
// 这些元素在 HTML 模板中定义（templates/index.html）
const els = {
    chatOverlay: document.getElementById('chatOverlay'),       // 聊天浮层容器
    chatHistory: document.getElementById('chatHistory'),       // 对话历史区域
    roundNum: document.getElementById('roundNum'),             // 轮数显示
    progressFill: document.getElementById('progressFill'),     // 进度条填充
    userInput: document.getElementById('userInput'),           // 用户输入框
    btnStart: document.getElementById('btnStart'),             // 开始访谈按钮
    btnResume: document.getElementById('btnResume'),           // 继续访谈按钮
    btnSend: document.getElementById('btnSend'),               // 发送按钮
    btnReport: document.getElementById('btnReport'),           // 生成报告按钮
    inputArea: document.getElementById('inputArea'),           // 输入区域容器
    reportNotice: document.getElementById('reportNotice'),     // 报告就绪提示
    reportActions: document.getElementById('reportActions')    // 报告操作区域
};

// ============================================================
// 工具函数
// ============================================================

/**
 * 显示加载状态（AI 思考中）
 * @param {string} text - 加载提示文本
 *
 * 说明：
 * - 禁用输入框和发送按钮，防止用户重复提交
 * - 在对话历史中添加一个带动画的思考气泡
 */
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

/**
 * 隐藏加载状态
 *
 * 说明：
 * - 恢复输入框和发送按钮的可用状态
 * - 移除思考气泡
 * - 自动聚焦到输入框
 */
function hideLoading() {
    state.isLoading = false;
    els.userInput.disabled = false;
    els.btnSend.disabled = false;
    els.userInput.focus();

    const bubble = document.getElementById('thinkingBubble');
    if (bubble) bubble.remove();
}

/**
 * 更新进度条和轮数显示
 * @param {number} round - 当前轮数
 *
 * 说明：
 * - 进度条宽度 = (轮数 / 最大轮数) * 100%
 * - 最大轮数硬编码为 20（与 config.py 中的 MAX_QUESTIONS 一致）
 */
function updateProgress(round) {
    const maxRounds = 20;
    const pct = Math.min((round / maxRounds) * 100, 100);
    els.progressFill.style.width = pct + '%';
    els.roundNum.textContent = round;
}

/**
 * 滚动对话历史到底部
 *
 * 说明：
 * - 每次添加新消息后调用，确保用户能看到最新的对话
 */
function scrollToBottom() {
    els.chatHistory.scrollTop = els.chatHistory.scrollHeight;
}

// ============================================================
// 渲染函数
// ============================================================

/**
 * 渲染 AI 消息（分析卡片 + 问题气泡）
 * @param {Object} data - AI 解析后的结构化数据
 * @param {number} round - 当前轮数
 *
 * 说明：
 * AI 消息由两部分组成：
 * 1. 分析卡片：显示关键信号、天赋假设、HUMAN 3.0 判断
 * 2. 问题气泡：显示 AI 的下一个问题
 *
 * HTML 结构示例：
 * <div class="message-block ai-msg">
 *   <div class="ai-analysis">
 *     <div class="analysis-section">关键信号</div>
 *     <div class="analysis-section">天赋假设</div>
 *     <div class="analysis-section">HUMAN 3.0 判断</div>
 *   </div>
 *   <div class="message-row ai-row">
 *     <div class="message-avatar ai">AI</div>
 *     <div class="ai-question">问题内容</div>
 *   </div>
 * </div>
 */
function renderAIMessage(data, round) {
    const block = document.createElement('div');
    block.className = 'message-block ai-msg';

    const hasAnalysis = data.signal || data.hypothesis || data.judgment;
    const questionText = data.question || data.raw || '';

    let html = '';

    // AI 分析卡片（如果有分析数据）
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

/**
 * 渲染用户消息
 * @param {string} text - 用户输入的文本
 *
 * 说明：
 * - 用户消息显示在右侧，蓝色背景
 * - 使用 escapeHtml() 防止 XSS 攻击
 */
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

// ============================================================
// API 调用函数
// ============================================================

/**
 * 检查是否有未完成的访谈会话
 *
 * 说明：
 * - 页面加载时自动调用
 * - 如果有未完成的访谈，显示"继续上次访谈"按钮
 * - 按钮会显示已完成的轮数
 */
async function checkInterviewStatus() {
    try {
        const res = await fetch('/api/interview/status');
        const data = await res.json();
        if (data.success && data.has_active) {
            els.btnResume.style.display = 'inline-flex';
            els.btnResume.querySelector('.resume-round').textContent = data.round;
        }
    } catch (err) {
        // 静默失败，不影响页面正常使用
    }
}

/**
 * 恢复未完成的访谈
 *
 * 说明：
 * - 用户点击"继续上次访谈"按钮时调用
 * - 从服务器加载完整的对话历史
 * - 逐条渲染之前的消息，恢复聊天界面
 * - 根据轮数设置报告按钮状态
 */
async function resumeInterview() {
    // 打开聊天浮层
    if (els.chatOverlay) {
        els.chatOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    showLoading('正在恢复上次访谈...');

    try {
        const res = await fetch('/api/interview/resume');
        const data = await res.json();

        if (!data.success) {
            alert('恢复失败：' + data.error);
            hideLoading();
            return;
        }

        // 更新状态
        state.round = data.round;
        state.canReport = data.can_report;
        state.suggestReport = data.suggest_report;
        state.forceReport = data.force_report;
        state.isResumed = true;

        updateProgress(data.round);

        // 逐条渲染历史消息
        let assistantCount = 0;
        data.messages.forEach(msg => {
            if (msg.role === 'assistant') {
                assistantCount++;
                renderAIMessage(msg.data, assistantCount);
            } else if (msg.role === 'user' && msg.content !== '开始访谈') {
                renderUserMessage(msg.content);
            }
        });

        // 设置报告按钮状态
        if (data.can_report) {
            els.reportActions.style.display = 'flex';
        }
        if (data.suggest_report) {
            els.reportNotice.style.display = 'flex';
        }
        if (data.force_report) {
            els.reportNotice.innerHTML = '<span>✦</span> 已达到最大对话轮数，请生成报告';
            els.reportNotice.style.background = 'rgba(0,102,204,0.08)';
        }

    } catch (err) {
        alert('网络错误：' + err.message);
    } finally {
        hideLoading();
    }
}

/**
 * 开始新的访谈
 *
 * 说明：
 * - 用户点击"开始 AI 深度访谈"按钮时调用
 * - 先检查登录状态，未登录则跳转到登录页
 * - 调用 /api/start 接口创建新会话并获取 AI 开场白
 * - 渲染第一轮 AI 消息
 */
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
        // 网络错误继续尝试（后端会再次检查）
    }

    // 打开聊天浮层
    if (els.chatOverlay) {
        els.chatOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    showLoading('正在准备访谈...');

    try {
        const res = await fetch('/api/start', { method: 'POST' });
        const data = await res.json();

        if (!data.success) {
            alert('启动失败：' + data.error);
            hideLoading();
            return;
        }

        // 更新状态
        state.round = data.round;
        updateProgress(data.round);
        renderAIMessage(data.data, data.round);

    } catch (err) {
        alert('网络错误：' + err.message);
    } finally {
        hideLoading();
    }
}

/**
 * 提交用户回答，获取 AI 下一个问题
 * @param {string} message - 用户的回答内容
 *
 * 说明：
 * - 用户点击发送按钮或按 Enter 时调用
 * - 先渲染用户消息，再调用 API
 * - 根据返回数据更新报告按钮状态
 */
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

        // 更新状态
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
            els.reportNotice.style.background = 'rgba(0,102,204,0.08)';
        }

    } catch (err) {
        alert('网络错误：' + err.message);
    } finally {
        hideLoading();
    }
}

/**
 * 生成最终报告
 *
 * 说明：
 * - 用户点击"生成天赋报告"按钮时调用
 * - 调用 /api/report 接口，AI 根据完整对话生成报告
 * - 成功后跳转到报告展示页
 */
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

        // 跳转到报告页面
        window.location.href = data.redirect;

    } catch (err) {
        alert('网络错误：' + err.message);
        hideLoading();
    }
}

// ============================================================
// 事件绑定
// ============================================================

// 开始访谈按钮
els.btnStart.addEventListener('click', apiStart);

// 继续访谈按钮（可能不存在，需要判断）
if (els.btnResume) {
    els.btnResume.addEventListener('click', resumeInterview);
}

// 发送按钮点击
els.btnSend.addEventListener('click', () => {
    const text = els.userInput.value.trim();
    if (!text || state.isLoading) return;  // 空内容或正在加载时忽略

    els.userInput.value = '';  // 清空输入框
    renderUserMessage(text);   // 渲染用户消息
    apiChat(text);             // 调用 API
});

// 键盘快捷键：Enter 发送，Shift+Enter 换行
els.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        els.btnSend.click();
    }
});

// 生成报告按钮
els.btnReport.addEventListener('click', () => {
    if (confirm('确定要生成最终报告吗？生成后将结束本次访谈。')) {
        apiReport();
    }
});

// ============================================================
// 页面初始化
// ============================================================

// 自动聚焦到输入框
if (els.userInput) {
    els.userInput.focus();
}

// 页面加载时检查是否有未完成的访谈
checkInterviewStatus();
