/**
 * 景点检索模块
 * 关键词搜索、景点展示、路径规划入口
 */

let scenicPage = 1;
let scenicTotal = 0;
let scenicResults = [];
let currentScenicId = null;

// HTML转义函数，用于安全地在onclick属性中嵌入字符串
function escAttr(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// ==================== 景点标记弹出窗口（含3个按钮） ====================

function showScenicSpotPopup(spot) {
    var catIcon = {cultural:'🏛️',urban:'🏙️',natural:'🌿',museum:'🏛️',park:'🌳',school:'🎓',landmark:'🗼',temple:'⛩️',palace:'🏯',street:'🚶',other:'📍'};
    var icon = catIcon[spot.subcategory] || catIcon[spot.category] || '📍';
    var firstImg = spot.images && spot.images.length > 0 ? spot.images[0] : null;

    var content = '<div style="max-width:280px;font-size:13px;">';
    // 图片区域
    if (firstImg) {
        content += '<div style="width:100%;height:140px;overflow:hidden;border-radius:8px 8px 0 0;margin:-12px -12px 8px -12px;background:#f0f0f0;">' +
            '<img src="' + firstImg + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display=\'none\'">' +
            '</div>';
    }
    // 标题
    content += '<h3 style="margin:0 0 4px;font-size:15px;color:#1a73e8;">' + icon + ' ' + spot.name + '</h3>';
    // 基本信息
    content += '<div style="font-size:12px;color:#666;line-height:1.6;">';
    content += '<p style="margin:2px 0;">⭐ ' + (spot.rating || '--') + ' | ' + (spot.ticket_price || '免费') + ' | ' + (spot.category || '') + '</p>';
    content += '<p style="margin:2px 0;">📍 ' + (spot.address || '') + '</p>';
    content += '<p style="margin:2px 0;">🕐 ' + (spot.open_time || '暂无') + '</p>';
    if (spot.description) {
        content += '<p style="margin:4px 0;color:#999;border-top:1px solid #eee;padding-top:4px;">' + spot.description.substring(0, 60) + (spot.description.length > 60 ? '...' : '') + '</p>';
    }
    content += '</div>';
    // 3个操作按钮
    var safeName = escAttr(spot.name || '');
    content += '<div style="display:flex;gap:6px;margin-top:10px;">';
    content += '<button onclick="event.stopPropagation();showScenicDetailWindow(' + JSON.stringify(spot).replace(/"/g, '&quot;') + ')" ' +
        'style="flex:1;padding:6px 4px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">📋 查看详细</button>';
    content += '<button onclick="event.stopPropagation();goDriveToSpot(' + spot.longitude + ',' + spot.latitude + ',\'' + safeName + '\')" ' +
        'style="flex:1;padding:6px 4px;background:#34a853;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">🚗 驾车</button>';
    content += '<button onclick="event.stopPropagation();addToTspList(' + spot.longitude + ',' + spot.latitude + ',\'' + safeName + '\')" ' +
        'style="flex:1;padding:6px 4px;background:#FF8800;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">➕ TSP</button>';
    content += '</div></div>';

    if (currentInfoWindow) currentInfoWindow.close();
    showInfoWindow(content, [spot.longitude, spot.latitude]);
}

// ==================== 景点详细情况（含多图） ====================

function showScenicDetailWindow(spot) {
    var catIcon = {cultural:'🏛️',urban:'🏙️',natural:'🌿',museum:'🏛️',park:'🌳',school:'🎓',landmark:'🗼',temple:'⛩️',palace:'🏯',street:'🚶',other:'📍'};
    var icon = catIcon[spot.subcategory] || catIcon[spot.category] || '📍';
    var images = spot.images || [];

    var content = '<div style="max-width:340px;font-size:13px;">';
    // 多图轮播区域
    if (images.length > 0) {
        content += '<div style="position:relative;margin:-12px -12px 10px -12px;">';
        content += '<div style="width:100%;height:180px;overflow:hidden;border-radius:8px 8px 0 0;background:#f0f0f0;">';
        // 显示第一张图
        content += '<img id="detailImg" src="' + images[0] + '" style="width:100%;height:100%;object-fit:cover;" onerror="this.style.display=\'none\'">';
        content += '</div>';
        // 缩略图导航
        if (images.length > 1) {
            content += '<div style="display:flex;gap:4px;margin-top:6px;overflow-x:auto;padding:2px 0;">';
            for (var i = 0; i < images.length; i++) {
                content += '<img src="' + images[i] + '" style="width:50px;height:40px;object-fit:cover;border-radius:4px;cursor:pointer;border:2px solid ' + (i === 0 ? '#1a73e8' : 'transparent') + ';" ' +
                    'onclick="document.getElementById(\'detailImg\').src=\'' + images[i] + '\';this.style.borderColor=\'#1a73e8\';Array.from(this.parentNode.children).forEach(function(c){if(c!==this)c.style.borderColor=\'transparent\';});" ' +
                    'onerror="this.style.display=\'none\'">';
            }
            content += '</div>';
        }
        content += '</div>';
    }

    // 标题和评分
    content += '<h3 style="margin:0 0 4px;font-size:16px;color:#1a73e8;">' + icon + ' ' + spot.name + '</h3>';
    content += '<div style="display:flex;gap:8px;margin-bottom:6px;">';
    content += '<span style="background:#e8f0fe;color:#1a73e8;padding:1px 8px;border-radius:3px;font-size:11px;">' + (spot.subcategory || spot.category || '未分类') + '</span>';
    if (spot.rating) content += '<span style="color:#f59e0b;">⭐ ' + spot.rating + '</span>';
    content += '</div>';

    // 详细信息
    content += '<div style="font-size:12px;color:#555;line-height:1.8;">';
    content += '<p style="margin:2px 0;">📌 <strong>地址：</strong>' + (spot.address || '暂无') + '</p>';
    content += '<p style="margin:2px 0;">💰 <strong>门票：</strong>' + (spot.ticket_price || '免费') + '</p>';
    content += '<p style="margin:2px 0;">🕐 <strong>开放时间：</strong>' + (spot.open_time || '暂无') + '</p>';
    content += '<p style="margin:2px 0;">📞 <strong>电话：</strong>' + (spot.phone || '暂无') + '</p>';
    if (spot.description) {
        content += '<p style="margin:4px 0;padding-top:6px;border-top:1px solid #eee;color:#666;">📖 ' + spot.description + '</p>';
    }
    content += '</div>';

    // 底部操作按钮
    var safeName = escAttr(spot.name || '');
    content += '<div style="display:flex;gap:6px;margin-top:10px;padding-top:8px;border-top:1px solid #eee;">';
    content += '<button onclick="event.stopPropagation();goDriveToSpot(' + spot.longitude + ',' + spot.latitude + ',\'' + safeName + '\')" ' +
        'style="flex:1;padding:6px;background:#34a853;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">🚗 驾车前往</button>';
    content += '<button onclick="event.stopPropagation();addToTspList(' + spot.longitude + ',' + spot.latitude + ',\'' + safeName + '\')" ' +
        'style="flex:1;padding:6px;background:#FF8800;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">➕ 加入TSP</button>';
    content += '<button onclick="event.stopPropagation();flyTo(' + spot.longitude + ',' + spot.latitude + ',15)" ' +
        'style="flex:0.6;padding:6px;background:#5f6368;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:11px;">📍 定位</button>';
    content += '</div></div>';

    if (currentInfoWindow) currentInfoWindow.close();
    showInfoWindow(content, [spot.longitude, spot.latitude]);
}

// ==================== 从景点跳转到驾车 ====================

function goDriveToSpot(lng, lat, name) {
    // 切换到路径规划模块
    switchModule('route');
    // 切换到驾车Tab
    if (typeof switchRouteTab === 'function') {
        switchRouteTab('drive');
    }

    // 清除旧终点标记（注意：driveEndMarker 是 let 变量，不用 window.）
    if (typeof driveEndMarker !== 'undefined' && driveEndMarker) {
        try { map.remove(driveEndMarker); } catch(e) {}
        driveEndMarker = null;
    }

    // 设置终点为景点坐标
    window.driveDestCoords = { lat: lat, lng: lng, name: name };
    document.getElementById('driveDest').value = name + ' (' + lng.toFixed(4) + ', ' + lat.toFixed(4) + ')';

    // 创建终点标记
    driveEndMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold;">终点: ' + name + '</div>', offset: new AMap.Pixel(-45, -40) },
    });
    map.add(driveEndMarker);

    // 清除旧路线结果
    document.getElementById('routeResultList').innerHTML = '';

    // 飞到终点位置查看
    flyTo(lng, lat, 14);

    // 设置起点提示，默认切到设起点模式
    document.getElementById('driveOrigin').value = '';
    document.getElementById('driveOrigin').placeholder = '点击"设起点"按钮选起点';
    if (typeof setDrivePickMode === 'function') setDrivePickMode('origin');

    showTip('终点已设为「' + name + '」，请在地图上点击选择起点位置', 'success');
}

// ==================== 分类标签点击（替代下拉框） ====================

function selectScenicCategory(el, value) {
    document.querySelectorAll('#scenicCategoryTags .cat-tag').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('scenicCategory').value = value;
    searchScenic();
}

function selectScenicSubcategory(el, value) {
    document.querySelectorAll('#scenicSubcategoryTags .cat-tag').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('scenicSubcategory').value = value;
    searchScenic();
}

// ==================== 搜索 ====================

async function searchScenic() {
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
        const result = await apiSearchScenic(params);

        if (result.code === 200) {
            displayScenicResults(result.data, result.total, result.page);
        } else {
            showTip(result.msg || '搜索失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

// ==================== 结果展示 ====================

function displayScenicResults(data, total, page) {
    scenicResults = data;
    scenicTotal = total;
    scenicPage = page;

    const listEl = document.getElementById('scenicResultList');

    // 清除旧标记
    clearMarkers(scenicMarkers);

    if (!data || data.length === 0) {
        listEl.innerHTML = '<p class="hint">未找到相关景点</p>';
        return;
    }

    // 在地图上添加标记
    data.forEach((spot, idx) => {
        const marker = new AMap.Marker({
            position: [spot.longitude, spot.latitude],
            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
            anchor: 'bottom-center',
            offset: new AMap.Pixel(-13, -30),
            label: {
                content: `<div style="background:#1a73e8;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;white-space:nowrap;">${spot.name}</div>`,
                offset: new AMap.Pixel(-50, -50),
            },
        });

        marker.on('click', function() {
            // 点击景点标记：弹出信息窗口含3个操作按钮
            showScenicSpotPopup(spot);
        });

        map.add(marker);
        scenicMarkers.push(marker);
    });

    // 自适应视野
    if (data.length > 0) {
        const positions = data.map(s => [s.longitude, s.latitude]);
        map.setFitView(
            scenicMarkers,
            false,
            [60, 60, 60, 60]
        );
    }

    // 构建结果列表
    let html = `<p style="margin-bottom:8px;font-size:13px;color:var(--text-secondary);">共找到 ${total} 个景点</p>`;
    data.forEach((spot, idx) => {
        const firstImg = spot.images && spot.images.length > 0 ? spot.images[0] : null;
        html += `
            <div class="scenic-item" onclick="flyTo(${spot.longitude}, ${spot.latitude}, 15)">
                <h4>${spot.name} <span style="font-size:11px;background:#e8f0fe;color:#1a73e8;padding:1px 6px;border-radius:3px;">${spot.subcategory || spot.category || '未分类'}</span></h4>
                <p>⭐ ${spot.rating || '暂无评分'} | ${spot.category || '未分类'} | ${spot.ticket_price || '免费'}</p>
                <p>${spot.address || ''}</p>
                <p>${spot.description ? spot.description.substring(0, 60) + '...' : ''}</p>
                <div class="scenic-actions">
                    <button class="btn-view" onclick="event.stopPropagation();showScenicInfoWindow(${JSON.stringify(spot).replace(/"/g, '&quot;')})">📋 详情</button>
                    <button class="btn-set-start" onclick="event.stopPropagation();goDriveToSpot(${spot.longitude}, ${spot.latitude}, '${escAttr(spot.name)}')">🚗 驾车</button>
                    <button class="btn-tsp" onclick="event.stopPropagation();addToTspList(${spot.longitude}, ${spot.latitude}, '${escAttr(spot.name)}')">➕ TSP</button>
                </div>
            </div>
        `;
    });

    // 分页
    const totalPages = Math.ceil(total / 10);
    if (totalPages > 1) {
        html += `
            <div class="pagination">
                <button ${page <= 1 ? 'disabled' : ''} onclick="scenicPrevPage()">上一页</button>
                <span>第 ${page}/${totalPages} 页</span>
                <button ${page >= totalPages ? 'disabled' : ''} onclick="scenicNextPage()">下一页</button>
            </div>
        `;
    }

    listEl.innerHTML = html;
}

// ==================== 信息窗口 ====================

function showScenicInfoWindow(spot) {
    const firstImg = spot.images && spot.images.length > 0 ? spot.images[0] : null;

    const catIcon = {cultural:'🏛️',urban:'🏙️',natural:'🌿',museum:'🏛️',park:'🌳',school:'🎓',landmark:'🗼',temple:'⛩️',palace:'🏯',street:'🚶',other:'📍'};
    const icon = catIcon[spot.subcategory] || catIcon[spot.category] || '📍';
    let content = '<div class="scenic-info-window" style="max-width:280px;">';
    content += '<h3 style="font-size:15px;margin-bottom:6px;color:#1a73e8;">' + icon + ' ' + spot.name + '</h3>';
    if (firstImg) {
        content += '<img src="' + firstImg + '" alt="' + spot.name + '" style="width:100%;max-height:120px;object-fit:cover;border-radius:6px;margin:6px 0;" onerror="this.remove()">';
    } else {
        // 无图片时显示分类大图标
        content += '<div style="font-size:48px;text-align:center;padding:10px 0;">' + icon + '</div>';
    }
    content += '<div style="font-size:12px;color:var(--text-secondary);">';
    content += '<p style="margin:3px 0;"><strong>分类:</strong> ' + (spot.category || '未分类') + (spot.subcategory ? '·' + spot.subcategory : '') + '</p>';
    content += '<p style="margin:3px 0;"><strong>地址:</strong> ' + (spot.address || '暂无') + '</p>';
    content += '<p style="margin:3px 0;">⭐' + (spot.rating || '暂无') + ' | ' + (spot.ticket_price || '免费') + '</p>';
    content += '<p style="margin:3px 0;"><strong>时间:</strong> ' + (spot.open_time || '暂无') + '</p>';
    content += '<p style="margin:3px 0;"><strong>电话:</strong> ' + (spot.phone || '暂无') + '</p>';
    if (spot.description) {
        content += '<p style="margin:3px 0;border-top:1px solid #eee;padding-top:4px;">' + spot.description.substring(0,80) + (spot.description.length>80?'...':'') + '</p>';
    }
    content += '</div>';
    content += '<div style="display:flex;gap:6px;margin-top:8px;">';
        var sname = escAttr(spot.name || '');
        content += '<button style="flex:1;padding:4px;background:#1a73e8;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;" onclick="flyTo(' + spot.longitude + ',' + spot.latitude + ',15)">📍 查看</button>';
        content += '<button style="flex:1;padding:4px;background:#34a853;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:11px;" onclick="goDriveToSpot(' + spot.longitude + ',' + spot.latitude + ",'" + sname + "')\">🚗 驾车</button>";
    content += '</div></div>';

    // 关闭之前的信息窗口
    if (currentInfoWindow) {
        currentInfoWindow.close();
    }
    showInfoWindow(content, [spot.longitude, spot.latitude]);
}

// ==================== 分页 ====================

function scenicPrevPage() {
    if (scenicPage > 1) {
        scenicPage--;
        searchScenic();
    }
}

function scenicNextPage() {
    scenicPage++;
    searchScenic();
}

// ==================== 路径规划入口 ====================

function setDriveStart(lng, lat, name) {
    switchModule('route');
    document.querySelector('.route-tab[onclick*="drive"]').click();

    document.getElementById('driveOrigin').value = `${name} (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    // 添加起点标记
    if (driveStartMarker) map.remove(driveStartMarker);
    driveStartMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#34a853;color:#fff;padding:2px 8px;border-radius:4px;">起点</div>', offset: new AMap.Pixel(-20, -40) },
    });
    map.add(driveStartMarker);

    // 存储起点坐标
    window.driveOriginCoords = { lng, lat, name };
    showTip(`已设置起点: ${name}`, 'success');
}

function setDriveDest(lng, lat, name) {
    switchModule('route');
    document.querySelector('.route-tab[onclick*="drive"]').click();

    document.getElementById('driveDest').value = `${name} (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    if (driveEndMarker) map.remove(driveEndMarker);
    driveEndMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;">终点</div>', offset: new AMap.Pixel(-20, -40) },
    });
    map.add(driveEndMarker);

    window.driveDestCoords = { lng, lat, name };
    showTip(`已设置终点: ${name}`, 'success');
}
