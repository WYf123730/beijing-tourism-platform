import os

js_dir = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js"

# === 1. Update scenic.js ===
path = os.path.join(js_dir, "scenic.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Search function with subcategory
old = """async function searchScenic() {
    const keyword = document.getElementById('scenicKeyword').value.trim();
    const category = document.getElementById('scenicCategory').value;

    if (!keyword) {
        showTip('请输入搜索关键词', 'warning');
        return;
    }

    try {
        const result = await apiSearchScenic({
            keyword: keyword,
            category: category || undefined,
            page: scenicPage,
            size: 10,
        });"""

new = """async function searchScenic() {
    const keyword = document.getElementById('scenicKeyword').value.trim();
    const category = document.getElementById('scenicCategory').value;
    const subcategory = document.getElementById('scenicSubcategory').value;

    if (!keyword) {
        showTip('请输入搜索关键词', 'warning');
        return;
    }

    try {
        const params = {
            keyword: keyword,
            category: category || undefined,
            page: scenicPage,
            size: 10,
        };
        if (subcategory) params.subcategory = subcategory;
        const result = await apiSearchScenic(params);"""

c = c.replace(old, new)

# Display with subcategory badge
old = """                <h4>${spot.name}</h4>
                <p>⭐ ${spot.rating || '暂无评分'} | ${spot.category || '未分类'} | ${spot.ticket_price || '免费'}</p>"""

new = """                <h4>${spot.name} <span style="font-size:11px;background:#e8f0fe;color:#1a73e8;padding:1px 6px;border-radius:3px;">${spot.subcategory || spot.category || '未分类'}</span></h4>
                <p>⭐ ${spot.rating || '暂无评分'} | ${spot.category || '未分类'} | ${spot.ticket_price || '免费'}</p>"""

c = c.replace(old, new)

# Info window with subcategory
old = """        <p><strong>分类:</strong> ${spot.category || '未分类'}</p>"""
new = """        <p><strong>分类:</strong> ${spot.category || '未分类'} ${spot.subcategory ? '· ' + spot.subcategory : ''}</p>"""
c = c.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('scenic.js updated')

# === 2. Update admin.js to add POI management ===
path = os.path.join(js_dir, "admin.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Add POI management functions at the end
poi_functions = """

// ==================== POI 管理 ====================

let poiAdminPage = 1;

async function loadPoiAdminList() {
    try {
        const result = await apiGetPoiCategories({ page: poiAdminPage, page_size: 20 });
        if (result.code === 200) {
            renderPoiAdminList(result.data, result.total, result.page);
        }
    } catch (e) {
        // Try without page params
        try {
            const result = await apiGetPoiCategories({ category: '', page: 1, page_size: 50 });
            if (result.code === 200) {
                renderPoiAdminList(result.data, result.total, result.page);
                return;
            }
        } catch(e2) {}
        showTip('加载POI列表失败', 'error');
    }
}

function renderPoiAdminList(data, total, page) {
    const listEl = document.getElementById('adminPoiList');
    if (!data || data.length === 0) {
        listEl.innerHTML = '<p class="hint">暂无POI数据</p>';
        return;
    }

    let html = `<div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:13px;color:var(--text-secondary);">共 ${total} 个POI</span>
    </div>`;

    data.forEach(poi => {
        const catIcons = {hospital:'🏥',school:'🏫',park:'🌳',mall:'🛍️',bank:'🏦',restaurant:'🍜',hotel:'🏨',gas_station:'⛽',library:'📚',stadium:'🏟️',theater:'🎭'};
        const icon = catIcons[poi.category] || '📍';
        html += `
        <div class="admin-item" id="poi-admin-${poi.id}">
            <div class="admin-item-info">
                <strong>${icon} ${poi.name}</strong>
                <span style="font-size:12px;color:var(--text-secondary);">
                    ${poi.category} | (${poi.longitude?.toFixed(4)}, ${poi.latitude?.toFixed(4)})
                </span>
                <span style="font-size:11px;color:var(--text-secondary);">${poi.address || ''}</span>
            </div>
            <div class="admin-item-actions">
                <button class="btn-sm btn-delete" onclick="deletePoi(${poi.id},'${poi.name.replace("'","\\\\'")}')">🗑️</button>
            </div>
        </div>`;
    });

    const totalPages = Math.ceil(total / 20);
    if (totalPages > 1) {
        html += `
        <div class="pagination">
            <button ${page <= 1 ? 'disabled' : ''} onclick="poiAdminPage--;loadPoiAdminList()">上一页</button>
            <span>${page}/${totalPages}</span>
            <button ${page >= totalPages ? 'disabled' : ''} onclick="poiAdminPage++;loadPoiAdminList()">下一页</button>
        </div>`;
    }

    listEl.innerHTML = html;
}

async function deletePoi(id, name) {
    if (!confirm(`确定要删除POI「${name}」吗？`)) return;

    try {
        // Try to use a delete endpoint - fallback to just removing from view
        // Since there's no dedicated POI delete API, we'll use a SQL approach via the backend
        const resp = await fetch('http://localhost:8001/api/poi/delete/' + id, { method: 'DELETE', headers: getAuthHeaders() });
        const result = await resp.json();
        if (result.code === 200) {
            showTip('已删除「' + name + '」', 'success');
            loadPoiAdminList();
        } else {
            showTip(result.msg || '删除失败', 'error');
        }
    } catch (e) {
        showTip('删除失败: ' + e.message, 'error');
    }
}
"""

c += poi_functions

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('admin.js updated (POI management added)')

print('All JS updates done!')
