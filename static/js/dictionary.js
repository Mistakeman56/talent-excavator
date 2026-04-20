// ===== 词典状态 =====
const dictState = {
    entries: [],
    categories: [],
    currentCategory: '',
    currentKeyword: ''
};

// ===== DOM 元素 =====
const els = {
    searchInput: document.getElementById('searchInput'),
    categoryTags: document.getElementById('categoryTags'),
    dictEntries: document.getElementById('dictEntries'),
    dictEmpty: document.getElementById('dictEmpty'),
    dictModal: document.getElementById('dictModal'),
    modalBody: document.getElementById('modalBody')
};

// ===== 初始化 =====
async function initDictionary() {
    try {
        const res = await fetch('/api/dictionary');
        const data = await res.json();
        
        if (!data.success) {
            els.dictEntries.innerHTML = '<p style="text-align:center; color: var(--text-muted); padding: 40px;">加载失败</p>';
            return;
        }
        
        dictState.entries = data.entries;
        dictState.categories = data.categories;
        
        renderCategories();
        renderEntries();
    } catch (err) {
        els.dictEntries.innerHTML = '<p style="text-align:center; color: var(--text-muted); padding: 40px;">网络错误</p>';
    }
}

// ===== 渲染分类标签 =====
function renderCategories() {
    let html = '<button class="tag active" data-category="">全部</button>';
    
    for (const cat of dictState.categories) {
        html += `<button class="tag" data-category="${cat}">${cat}</button>`;
    }
    
    els.categoryTags.innerHTML = html;
    
    // 绑定点击事件
    els.categoryTags.querySelectorAll('.tag').forEach(tag => {
        tag.addEventListener('click', () => {
            els.categoryTags.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
            tag.classList.add('active');
            dictState.currentCategory = tag.dataset.category;
            filterAndRender();
        });
    });
}

// ===== 渲染词条列表 =====
function renderEntries(entriesToRender) {
    const entries = entriesToRender || dictState.entries;
    
    if (entries.length === 0) {
        els.dictEntries.style.display = 'none';
        els.dictEmpty.style.display = 'block';
        return;
    }
    
    els.dictEntries.style.display = 'block';
    els.dictEmpty.style.display = 'none';
    
    let currentCat = '';
    let html = '';
    
    for (const entry of entries) {
        // 分类标题
        if (entry.category !== currentCat) {
            currentCat = entry.category;
            html += `<h3 class="dict-category-title">${currentCat}</h3>`;
        }
        
        html += `
            <div class="dict-card" onclick="openModal(${entry.id})">
                <div class="dict-card-header">
                    <h4 class="dict-term">${entry.term}</h4>
                    <span class="dict-cat-badge">${entry.category}</span>
                </div>
                <p class="dict-definition">${truncate(entry.definition, 100)}</p>
                ${entry.related_terms ? `<div class="dict-related">相关：${entry.related_terms}</div>` : ''}
            </div>
        `;
    }
    
    els.dictEntries.innerHTML = html;
}

// ===== 筛选 =====
function filterAndRender() {
    let filtered = dictState.entries;
    
    // 分类筛选
    if (dictState.currentCategory) {
        filtered = filtered.filter(e => e.category === dictState.currentCategory);
    }
    
    // 关键词搜索
    if (dictState.currentKeyword) {
        const kw = dictState.currentKeyword.toLowerCase();
        filtered = filtered.filter(e => 
            e.term.toLowerCase().includes(kw) ||
            e.definition.toLowerCase().includes(kw) ||
            (e.related_terms && e.related_terms.toLowerCase().includes(kw))
        );
    }
    
    renderEntries(filtered);
}

// ===== 搜索输入 =====
els.searchInput.addEventListener('input', (e) => {
    dictState.currentKeyword = e.target.value.trim();
    filterAndRender();
});

// ===== 详情弹窗 =====
function openModal(entryId) {
    const entry = dictState.entries.find(e => e.id === entryId);
    if (!entry) return;
    
    els.modalBody.innerHTML = `
        <div class="dict-modal-cat">${entry.category}</div>
        <h2 class="dict-modal-title">${entry.term}</h2>
        <div class="dict-modal-section">
            <h5>定义</h5>
            <p>${entry.definition}</p>
        </div>
        ${entry.example ? `
        <div class="dict-modal-section">
            <h5>例子</h5>
            <p class="dict-modal-example">${entry.example}</p>
        </div>
        ` : ''}
        ${entry.related_terms ? `
        <div class="dict-modal-section">
            <h5>相关概念</h5>
            <div class="dict-modal-related">
                ${entry.related_terms.split(',').map(t => `<span class="related-tag">${t.trim()}</span>`).join('')}
            </div>
        </div>
        ` : ''}
    `;
    
    els.dictModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    els.dictModal.style.display = 'none';
    document.body.style.overflow = '';
}

// 点击ESC关闭
 document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

// ===== 工具函数 =====
function truncate(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// ===== 启动 =====
initDictionary();
