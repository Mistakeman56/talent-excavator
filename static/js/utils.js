/**
 * 公共工具函数
 */

/**
 * HTML 转义，防止 XSS
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的安全文本
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 统一 API 调用函数，自动处理认证错误
 * @param {string} url - API 地址
 * @param {object} options - fetch 选项
 * @returns {Promise<object|null>} 返回解析后的 JSON 数据，如果未登录则返回 null 并跳转登录页
 */
async function apiFetch(url, options = {}) {
    const res = await fetch(url, options);
    const data = await res.json();
    if (data.error_code === 1001) {
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        return null;
    }
    return data;
}

/**
 * 检测当前是否为暗黑模式
 * @returns {boolean}
 */
function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
}

/**
 * 获取图表文字颜色（根据主题自适应）
 * @returns {string}
 */
function getChartTextColor() {
    return isDarkMode() ? '#a1a1a6' : '#86868b';
}

/**
 * 获取图表网格线颜色（根据主题自适应）
 * @returns {string}
 */
function getChartGridColor() {
    return isDarkMode() ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)';
}
