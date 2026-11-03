import os

js_dir = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js"

# ===== 1. Update api.js with POI CRUD =====
path = os.path.join(js_dir, "api.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

if 'apiDeletePoi' not in c:
    # Add POI CRUD functions before apiGetAttractionsWeather
    new_funcs = """
async function apiCreatePoi(data) {
    return apiPost('/poi/create', data);
}
async function apiUpdatePoi(id, data) {
    return apiPut('/poi/update/' + id, data);
}
async function apiDeletePoi(id) {
    return apiDelete('/poi/delete/' + id);
}
async function apiGetPoiDetail(id) {
    return apiGet('/poi/detail/' + id);
}

"""
    c = c.replace("async function apiGetAttractionsWeather", new_funcs + "async function apiGetAttractionsWeather")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('api.js - POI CRUD added')
else:
    print('api.js - already updated')

# ===== 2. Update admin.js with full POI CRUD =====
path = os.path.join(js_dir, "admin.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the POI admin section completely
old_poi = """// ==================== POI 管理 ====================

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

new_poi = """// ==================== POI 管理 ====================

let poiAdminPage = 1;
let poiEditId = null;

async function loadPoiAdminList() {
    try {
        const result = await apiGetPoiCategories({ page: poiAdminPage, page_size: 20 });
        if (result.code === 200) {
            renderPoiAdminList(result.data, result.total, result.page);
        } else {
            // Fallback
            const r = await apiGetPoiCategories({ category: '', page: 1, page_size: 50 });
            if (r.code === 200) renderPoiAdminList(r.data, r.total, r.page);
        }
    } catch (e) {
        showTip('加载POI列表失败', 'error');
    }
}

function renderPoiAdminList(data, total, page) {
    const listEl = document.getElementById('adminPoiList');
    if (!data || data.length === 0) {
        listEl.innerHTML = '<p class="hint">暂无POI数据</p>';
        return;
    }

    const catIcons = {hospital:'🏥',school:'🏫',park:'🌳',mall:'🛍️',bank:'🏦',restaurant:'🍜',hotel:'🏨',gas_station:'⛽',library:'📚',stadium:'🏟️',theater:'🎭'};

    let html = '<div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">';
    html += '<span style="font-size:13px;color:var(--text-secondary);">共 ' + total + ' 个POI</span>';
    html += '<button class="tool-btn" onclick="showAddPoiForm()" style="padding:4px 10px;font-size:12px;">➕ 新增POI</button></div>';

    data.forEach(function(poi) {
        var icon = catIcons[poi.category] || '📍';
        html += '<div class="admin-item" id="poi-admin-' + poi.id + '">';
        html += '<div class="admin-item-info">';
        html += '<strong>' + icon + ' ' + poi.name + '</strong>';
        html += '<span style="font-size:12px;color:var(--text-secondary);">' + poi.category + ' | (' + poi.longitude.toFixed(4) + ', ' + poi.latitude.toFixed(4) + ')</span>';
        html += '<span style="font-size:11px;color:var(--text-secondary);">' + (poi.address || '') + '</span>';
        html += '</div>';
        html += '<div class="admin-item-actions">';
        html += '<button class="btn-sm btn-edit" onclick="editPoi(' + poi.id + ')">✏️</button>';
        html += '<button class="btn-sm btn-delete" onclick="deletePoi(' + poi.id + ",'" + poi.name.replace(/'/g,"") + "')" + '">🗑️</button>';
        html += '</div></div>';
    });

    var totalPages = Math.ceil(total / 20);
    if (totalPages > 1) {
        html += '<div class="pagination">';
        html += '<button ' + (page <= 1 ? 'disabled' : '') + ' onclick="poiAdminPage--;loadPoiAdminList()">上一页</button>';
        html += '<span>' + page + '/' + totalPages + '</span>';
        html += '<button ' + (page >= totalPages ? 'disabled' : '') + ' onclick="poiAdminPage++;loadPoiAdminList()">下一页</button>';
        html += '</div>';
    }

    listEl.innerHTML = html;
}

function showAddPoiForm() {
    poiEditId = null;
    document.getElementById('poiFormTitle').textContent = '新增POI';
    document.getElementById('poiForm').style.display = 'block';
    document.getElementById('adminPoiSection').style.display = 'none';
    ['poi-name','poi-category','poi-address','poi-longitude','poi-latitude','poi-phone'].forEach(function(f) {
        document.getElementById(f).value = '';
    });
    document.getElementById('poiFormError').textContent = '';
}

function cancelPoiForm() {
    document.getElementById('poiForm').style.display = 'none';
    document.getElementById('adminPoiSection').style.display = 'block';
}

async function savePoi() {
    var name = document.getElementById('poi-name').value.trim();
    var category = document.getElementById('poi-category').value;
    var lng = parseFloat(document.getElementById('poi-longitude').value);
    var lat = parseFloat(document.getElementById('poi-latitude').value);

    if (!name) { document.getElementById('poiFormError').textContent = 'POI名称必填'; return; }
    if (isNaN(lng) || isNaN(lat)) { document.getElementById('poiFormError').textContent = '经纬度必填且为数字'; return; }

    var data = {
        name: name,
        category: category,
        address: document.getElementById('poi-address').value.trim(),
        longitude: lng,
        latitude: lat,
        phone: document.getElementById('poi-phone').value.trim(),
    };

    try {
        var result;
        if (poiEditId) {
            result = await apiUpdatePoi(poiEditId, data);
        } else {
            result = await apiCreatePoi(data);
        }
        if (result.code === 200) {
            showTip(poiEditId ? '修改成功' : '新增成功', 'success');
            cancelPoiForm();
            loadPoiAdminList();
        } else {
            document.getElementById('poiFormError').textContent = result.msg || '操作失败';
        }
    } catch (e) {
        document.getElementById('poiFormError').textContent = '网络错误';
    }
}

async function editPoi(id) {
    try {
        var r = await apiGetPoiDetail(id);
        if (r.code !== 200) { showTip('获取详情失败', 'error'); return; }
        var poi = r.data;
        poiEditId = poi.id;
        document.getElementById('poiFormTitle').textContent = '修改POI';
        document.getElementById('poiForm').style.display = 'block';
        document.getElementById('adminPoiSection').style.display = 'none';
        document.getElementById('poi-name').value = poi.name || '';
        document.getElementById('poi-category').value = poi.category || 'hospital';
        document.getElementById('poi-address').value = poi.address || '';
        document.getElementById('poi-longitude').value = poi.longitude || '';
        document.getElementById('poi-latitude').value = poi.latitude || '';
        document.getElementById('poi-phone').value = poi.phone || '';
        document.getElementById('poiFormError').textContent = '';
    } catch(e) {
        showTip('获取详情失败', 'error');
    }
}

async function deletePoi(id, name) {
    if (!confirm('确定要删除POI「' + name + '」吗？')) return;
    try {
        var result = await apiDeletePoi(id);
        if (result.code === 200) {
            showTip('已删除「' + name + '」', 'success');
            loadPoiAdminList();
        } else {
            showTip(result.msg || '删除失败', 'error');
        }
    } catch(e) {
        showTip('删除失败: ' + e.message, 'error');
    }
}
"""

c = c.replace(old_poi, new_poi)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('admin.js - POI CRUD replaced')

print('Done!')
