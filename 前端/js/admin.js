/**
 * 景点管理模块
 * 增删改查景点（需要登录认证）
 */

let adminCurrentId = null;
let adminPage = 1;

// ==================== 初始化管理面板 ====================

function showAdminPanel() {
    const token = getToken();
    if (!token) {
        showTip('请先登录', 'warning');
        showLoginModal();
        return;
    }
    loadAdminList();
}

async function loadAdminList() {
    try {
        const result = await apiGetScenicList({ page: adminPage, size: 20 });
        if (result.code === 200) {
            renderAdminList(result.data, result.total, result.page);
        }
    } catch (e) {
        showTip('加载景点列表失败', 'error');
    }
}

function renderAdminList(data, total, page) {
    const listEl = document.getElementById('adminSpotList');
    if (!data || data.length === 0) {
        listEl.innerHTML = '<p class="hint">暂无景点数据</p>';
        return;
    }

    let html = `<div style="margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:13px;color:var(--text-secondary);">共 ${total} 个景点</span>
    </div>`;

    data.forEach(spot => {
        html += `
        <div class="admin-item" id="admin-${spot.id}">
            <div class="admin-item-info">
                <strong>${spot.name}</strong>
                <span style="font-size:12px;color:var(--text-secondary);">
                    ${spot.category || '未分类'} | ⭐${spot.rating || '--'} | ${spot.ticket_price || '免费'}
                </span>
                <span style="font-size:11px;color:var(--text-secondary);">
                    (${spot.longitude?.toFixed(4)}, ${spot.latitude?.toFixed(4)})
                </span>
            </div>
            <div class="admin-item-actions">
                <button class="btn-sm btn-edit" onclick="editAdminSpot(${spot.id})">✏️</button>
                <button class="btn-sm btn-delete" onclick="deleteAdminSpot(${spot.id},'${spot.name}')">🗑️</button>
            </div>
        </div>`;
    });

    // 分页
    const totalPages = Math.ceil(total / 20);
    if (totalPages > 1) {
        html += `
        <div class="pagination">
            <button ${page <= 1 ? 'disabled' : ''} onclick="adminPage--;loadAdminList()">上一页</button>
            <span>${page}/${totalPages}</span>
            <button ${page >= totalPages ? 'disabled' : ''} onclick="adminPage++;loadAdminList()">下一页</button>
        </div>`;
    }

    listEl.innerHTML = html;
}

// ==================== 新增景点 ====================

function showAddSpotForm() {
    adminCurrentId = null;
    document.getElementById('adminFormTitle').textContent = '新增景点';
    document.getElementById('adminForm').style.display = 'block';
    document.getElementById('adminList').style.display = 'none';
    // 清空表单
    ['name','description','address','category','longitude','latitude','phone','open_time','ticket_price','rating'].forEach(f => {
        document.getElementById(`af-${f}`).value = '';
    });
    document.getElementById('af-images').value = '';
    document.getElementById('adminFormError').textContent = '';
}

function cancelAdminForm() {
    document.getElementById('adminForm').style.display = 'none';
    document.getElementById('adminList').style.display = 'block';
}

async function saveAdminSpot() {
    const name = document.getElementById('af-name').value.trim();
    const longitude = parseFloat(document.getElementById('af-longitude').value);
    const latitude = parseFloat(document.getElementById('af-latitude').value);

    if (!name) { showError('景点名称必填'); return; }
    if (isNaN(longitude) || isNaN(latitude)) { showError('经纬度必填且为数字'); return; }

    const data = {
        name,
        description: document.getElementById('af-description').value.trim(),
        address: document.getElementById('af-address').value.trim(),
        category: document.getElementById('af-category').value,
        longitude,
        latitude,
        phone: document.getElementById('af-phone').value.trim(),
        open_time: document.getElementById('af-open_time').value.trim(),
        ticket_price: document.getElementById('af-ticket_price').value.trim(),
        rating: parseFloat(document.getElementById('af-rating').value) || 0,
        images: document.getElementById('af-images').value.trim()
            ? document.getElementById('af-images').value.split(',').map(s => s.trim()).filter(Boolean)
            : [],
    };

    try {
        let result;
        if (adminCurrentId) {
            result = await apiUpdateScenic(adminCurrentId, data);
        } else {
            result = await apiCreateScenic(data);
        }
        if (result.code === 200) {
            showTip(adminCurrentId ? '修改成功' : '新增成功', 'success');
            cancelAdminForm();
            loadAdminList();
            document.getElementById('adminFormError').textContent = '';
        } else {
            showError(result.msg || '操作失败');
        }
    } catch (e) {
        showError('网络错误');
    }

    function showError(msg) {
        document.getElementById('adminFormError').textContent = msg;
    }
}

// ==================== 修改景点 ====================

async function editAdminSpot(id) {
    try {
        const result = await apiGetScenicDetail(id);
        if (result.code !== 200) {
            showTip('获取景点详情失败', 'error');
            return;
        }
        const spot = result.data;
        adminCurrentId = spot.id;

        document.getElementById('adminFormTitle').textContent = '修改景点';
        document.getElementById('adminForm').style.display = 'block';
        document.getElementById('adminList').style.display = 'none';
        document.getElementById('adminFormError').textContent = '';

        document.getElementById('af-name').value = spot.name || '';
        document.getElementById('af-description').value = spot.description || '';
        document.getElementById('af-address').value = spot.address || '';
        document.getElementById('af-category').value = spot.category || '';
        document.getElementById('af-longitude').value = spot.longitude || '';
        document.getElementById('af-latitude').value = spot.latitude || '';
        document.getElementById('af-phone').value = spot.phone || '';
        document.getElementById('af-open_time').value = spot.open_time || '';
        document.getElementById('af-ticket_price').value = spot.ticket_price || '';
        document.getElementById('af-rating').value = spot.rating || '';
        document.getElementById('af-images').value = (spot.images || []).join(', ');

    } catch (e) {
        showTip('获取详情失败', 'error');
    }
}

// ==================== 删除景点 ====================

async function deleteAdminSpot(id, name) {
    if (!confirm(`确定要删除景点「${name}」吗？`)) return;

    try {
        const result = await apiDeleteScenic(id);
        if (result.code === 200) {
            showTip(`已删除「${name}」`, 'success');
            loadAdminList();
        } else {
            showTip(result.msg || '删除失败', 'error');
        }
    } catch (e) {
        showTip('删除失败: 网络错误', 'error');
    }
}


