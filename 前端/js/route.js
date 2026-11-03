/**
 * 路径规划模块
 * 驾车路径规划、旅行商分析、公交换乘
 */

let currentRouteTab = 'drive';
let tspSpots = [];
let tspOriginCoords = null;  // TSP起点坐标
let routeResultData = null;
let tspWaitingForClick = false;  // 是否等待地图点击设TSP起点
let drivePickMode = 'origin';  // 驾车地图点击模式: 'origin' 设起点 / 'dest' 设终点

// ==================== Tab 切换 ====================

function switchRouteTab(tab) {
    currentRouteTab = tab;
    document.querySelectorAll('.route-tab').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.route-tab-content').forEach(el => el.classList.remove('active'));

    document.querySelector(`.route-tab[onclick*="${tab}"]`).classList.add('active');
    document.getElementById(`route-${tab}`).classList.add('active');
}

// ==================== 驾车路径规划 ====================

async function planDriveRoute() {
    const originInput = document.getElementById('driveOrigin').value;
    const destInput = document.getElementById('driveDest').value;

    let originCoords = window.driveOriginCoords;
    let destCoords = window.driveDestCoords;

    if (!originCoords || !destCoords) {
        showTip('请先在地图上设置起点和终点', 'warning');
        return;
    }

    try {
        showTip('正在规划驾车路线...', 'info');
        const result = await apiPlanDrive({
            origin_lat: originCoords.lat,
            origin_lng: originCoords.lng,
            dest_lat: destCoords.lat,
            dest_lng: destCoords.lng,
        });

        if (result.code === 200) {
            displayDriveResult(result.data);
        } else {
            showTip(result.msg || '路径规划失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

function displayDriveResult(data) {
    const listEl = document.getElementById('routeResultList');

    if (!data.paths || data.paths.length === 0) {
        listEl.innerHTML = '<p class="hint">未找到可行路线</p>';
        return;
    }

    // 清除旧路线
    clearPolylines(routePolylines);

    const path = data.paths[0];

    // 绘制路线
    if (path.polyline_points && path.polyline_points.length > 0) {
        const polyline = new AMap.Polyline({
            path: path.polyline_points,
            strokeColor: '#1a73e8',
            strokeWeight: 6,
            strokeStyle: 'solid',
            strokeOpacity: 0.8,
            lineJoin: 'round',
            lineCap: 'round',
        });
        map.add(polyline);
        routePolylines.push(polyline);
        map.setFitView([polyline], false, [60, 60, 60, 60]);
    }

    // 显示结果
    let html = `<h4>🚗 驾车路线规划</h4>`;
    html += `<div class="result-item">
        <p><strong>距离:</strong> ${(path.distance / 1000).toFixed(1)} km</p>
        <p><strong>预计耗时:</strong> ${Math.round(path.duration / 60)} 分钟</p>
        <p><strong>过路费:</strong> ${path.tolls || 0} 元</p>
    </div>`;

    if (path.steps && path.steps.length > 0) {
        html += `<h4>🧭 详细导航步骤 (${path.steps.length}步)</h4>`;
        var totalDistStep = 0, totalDurStep = 0;
        path.steps.forEach((step, idx) => {
            totalDistStep += step.distance || 0;
            totalDurStep += step.duration || 0;
            var icon = '⬆️';
            var dir = (step.instruction || '').includes('左转') ? '↰' : (step.instruction || '').includes('右转') ? '↱' : '⬆️';
            if ((step.instruction || '').includes('到达')) icon = '🏁';
            else if ((step.instruction || '').includes('直行')) icon = '⬆️';
            else if ((step.instruction || '').includes('进入')) icon = '🚗';
            else icon = dir;
            html += `<div class="result-item" style="padding:6px 10px;font-size:12px;display:flex;align-items:flex-start;gap:6px;">
                <span style="background:#1a73e8;color:#fff;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0;margin-top:1px;">${idx + 1}</span>
                <div style="flex:1;">
                    <p style="margin:0;">${icon} ${step.instruction}</p>
                    <p style="color:var(--text-secondary);margin:2px 0 0 0;font-size:11px;">${(step.distance / 1000).toFixed(1)}km · ${Math.round(step.duration / 60)}分钟</p>
                </div>
            </div>`;
        });
        html += `<div class="result-item" style="padding:6px 10px;font-size:11px;background:#e8f5e9;">
            <p>📊 合计: ${(totalDistStep/1000).toFixed(1)}km · ${Math.round(totalDurStep/60)}分钟 · ${path.steps.length}个导航点</p>
        </div>`;
    }

    listEl.innerHTML = html;
}

// ==================== TSP 旅行商分析 ====================

function searchTspSpots() {
    const keyword = document.getElementById('tspKeyword').value.trim();
    if (!keyword) {
        showTip('请输入关键词搜索景点', 'warning');
        return;
    }

    // 复用景点搜索
    document.getElementById('scenicKeyword').value = keyword;
    searchScenic();
    showTip('在搜索结果中点击"➕ TSP"按钮添加景点', 'info');
}

function addToTspList(lng, lat, name) {
    // 检查是否已存在
    if (tspSpots.some(s => s.lng === lng && s.lat === lat)) {
        showTip('该景点已在列表中', 'warning');
        return;
    }

    tspSpots.push({ lng, lat, name });
    updateTspListUI();
    showTip(`已添加: ${name}`, 'success');
}

function removeFromTspList(index) {
    tspSpots.splice(index, 1);
    updateTspListUI();
}

function clearTspList() {
    tspSpots = [];
    tspOriginCoords = null;
    tspWaitingForClick = false;
    updateTspListUI();
    clearPolylines(routePolylines);
    clearMarkers(routeMarkers);
    if (window.tspStartMarker) { map.remove(window.tspStartMarker); window.tspStartMarker = null; }
    document.getElementById('tspOrigin').value = '天安门 (默认)';
    document.getElementById('routeResultList').innerHTML = '';
    showTip('已清空TSP列表和地图标记', 'info');
}

function updateTspListUI() {
    const listEl = document.getElementById('tspSpotsList');

    if (tspSpots.length === 0) {
        listEl.innerHTML = '<p class="hint">已选景点将显示在这里</p>';
        return;
    }

    let html = `<p style="font-size:13px;color:var(--text-secondary);margin-bottom:4px;">已选 ${tspSpots.length} 个景点：</p>`;
    tspSpots.forEach((spot, idx) => {
        html += `
            <div class="result-item" style="padding:6px 10px;">
                <p><strong>${idx + 1}.</strong> ${spot.name}</p>
                <button style="float:right;padding:2px 8px;background:#ea4335;color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:11px;" onclick="removeFromTspList(${idx})">✕</button>
            </div>
        `;
    });

    listEl.innerHTML = html;
}

// 设置TSP起点（点击地图）
function setTspStartFromMap() {
    tspWaitingForClick = true;
    showTip('请在地图上点击选择TSP起点', 'info');
}

// 处理TSP起点地图点击
function handleTspMapClick(lat, lng) {
    tspOriginCoords = { lat, lng };
    tspWaitingForClick = false;
    document.getElementById('tspOrigin').value = `自定义起点 (${lng.toFixed(4)}, ${lat.toFixed(4)})`;
    // 添加标记
    if (window.tspStartMarker) map.remove(window.tspStartMarker);
    window.tspStartMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#FF8800;color:#fff;padding:2px 8px;border-radius:4px;">TSP起点</div>', offset: new AMap.Pixel(-25, -40) },
    });
    map.add(window.tspStartMarker);
    showTip('TSP起点已设置', 'success');
}

async function planTspRoute() {
    if (tspSpots.length < 2) {
        showTip('请至少添加2个景点', 'warning');
        return;
    }

    // 使用自定义起点或默认天安门
    const origin = tspOriginCoords || { lat: 39.913, lng: 116.397 };
    const originName = tspOriginCoords ? '自定义起点' : '天安门(默认)';

    try {
        showTip('正在进行旅行商分析...', 'info');
        const result = await apiPlanTsp({
            origin_lat: origin.lat,
            origin_lng: origin.lng,
            spots: tspSpots.map(s => ({ lat: s.lat, lng: s.lng, name: s.name })),
        });

        if (result.code === 200) {
            var data = result.data;
            var allSegments = [];
            var prevLat = data.origin.lat;
            var prevLng = data.origin.lng;
            var prevName = '起点(天安门)';

            for (var i = 0; i < data.ordered_spots.length; i++) {
                var spot = data.ordered_spots[i];
                showTip('正在获取第' + (i+1) + '/' + data.ordered_spots.length + '段驾车路线...', 'info');

                // 添加间隔避免高德API限流
                if (i > 0) {
                    await new Promise(r => setTimeout(r, 600));
                }

                try {
                    var driveResult = await apiPlanDrive({
                        origin_lat: prevLat,
                        origin_lng: prevLng,
                        dest_lat: spot.latitude,
                        dest_lng: spot.longitude,
                    });
                    if (driveResult.code === 200 && driveResult.data && driveResult.data.paths && driveResult.data.paths.length > 0) {
                        allSegments.push({ from: prevName, to: spot.name, path: driveResult.data.paths[0] });
                        showTip('第' + (i+1) + '段路线获取成功', 'success');
                    } else {
                        allSegments.push({ from: prevName, to: spot.name, path: null, error: driveResult?.msg || '路线规划失败' });
                        showTip('第' + (i+1) + '段路线获取失败，使用直线连接', 'warning');
                    }
                } catch(e) {
                    allSegments.push({ from: prevName, to: spot.name, path: null, error: e.message || '请求异常' });
                    showTip('第' + (i+1) + '段路线请求异常，使用直线连接', 'warning');
                }
                prevLat = spot.latitude;
                prevLng = spot.longitude;
                prevName = spot.name;
            }
            displayTspResult(data, allSegments, originName);
        } else {
            showTip(result.msg || '分析失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

function displayTspResult(data, allSegments, originName) {
    const listEl = document.getElementById('routeResultList');
    clearPolylines(routePolylines);
    clearMarkers(routeMarkers);

    // 绘制路线
    if (data.route_coords && data.route_coords.length > 1) {
        const polyline = new AMap.Polyline({
            path: data.route_coords,
            strokeColor: '#34a853',
            strokeWeight: 6,
            strokeStyle: 'dashed',
            strokeOpacity: 0.9,
            borderWeight: 2,
            outlineColor: '#fff',
        });
        map.add(polyline);
        routePolylines.push(polyline);

        // 起点标记（特殊颜色）
        const originMarker = new AMap.Marker({
            position: [data.origin.lng, data.origin.lat],
            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
            anchor: 'bottom-center',
            label: {
                content: '<div style="background:#FF8800;color:#fff;padding:2px 10px;border-radius:4px;font-weight:bold;">起点</div>',
                offset: new AMap.Pixel(-25, -40),
            },
        });
        map.add(originMarker);
        routeMarkers.push(originMarker);

        // 添加顺序标记
        data.ordered_spots.forEach((spot, idx) => {
            const colors = ['#1a73e8', '#ea4335', '#34a853', '#FF8800', '#9C27B0', '#00BCD4', '#FF5722', '#795548'];
            const marker = new AMap.Marker({
                position: [spot.longitude, spot.latitude],
                icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
                anchor: 'bottom-center',
                label: {
                    content: `<div style="background:${colors[idx % colors.length]};color:#fff;padding:4px 12px;border-radius:14px;font-size:13px;font-weight:bold;border:2px solid #fff;">${idx + 1}</div>`,
                    offset: new AMap.Pixel(-25, -40),
                },
            });
            marker.on('click', function() {
                showInfoWindow(`<div><h4>第${idx+1}站: ${spot.name}</h4></div>`, [spot.longitude, spot.latitude]);
            });
            map.add(marker);
            routeMarkers.push(marker);
        });

        // 自适应视野
        if (routeMarkers.length > 0) {
            map.setFitView(routeMarkers, false, [80, 80, 80, 80]);
        }
    }

    // 显示结果
    let html = `<h4>📋 最优游览顺序</h4>`;
    html += `<div class="result-item">
        <p><strong>总路程:</strong> ${(data.total_distance / 1000).toFixed(1)} km</p>
        <p><strong>景点数:</strong> ${data.spots_count} 个</p>
        <p style="font-size:12px;color:var(--text-secondary);">起点: ${originName || '天安门(默认)'}</p>
    </div>`;

    // 计算每段距离
    const origin = data.origin;
    let prevLng = origin.lng, prevLat = origin.lat;
    const segmentData = [];
    data.ordered_spots.forEach((spot, idx) => {
        const dlat = spot.latitude - prevLat;
        const dlng = spot.longitude - prevLng;
        const segDist = Math.sqrt(dlat*dlat + dlng*dlng) * 111320;
        segmentData.push({ spot, segDist });
        prevLng = spot.longitude;
        prevLat = spot.latitude;
    });

    html += `<h4 style="margin-top:12px;">详细路线</h4>`;
    html += `<div class="result-item" style="background:#fff3e0;padding:6px 10px;font-size:12px;">
        <p>🚩 <strong>起点</strong> ${originName || '天安门(默认)'} (${origin.lng.toFixed(4)}, ${origin.lat.toFixed(4)})</p>
    </div>`;
    data.ordered_spots.forEach((item, idx) => {
        const seg = segmentData[idx];
        const distKm = (seg.segDist / 1000).toFixed(1);
        const segInfo = (typeof allSegments !== 'undefined' && allSegments && allSegments[idx]) ? allSegments[idx] : null;
        html += `<div class="result-item" style="padding:8px 10px;border-left:3px solid #34a853;margin:4px 0;">
            <p><strong style="color:#34a853;">⬇ 第${idx + 1}站</strong> → ${item.name}</p>
            <p style="font-size:12px;color:var(--text-secondary);margin-top:4px;">
                📍 (${item.longitude.toFixed(4)}, ${item.latitude.toFixed(4)}) 🛣️ ${distKm} km
            </p>`;
        if (segInfo && segInfo.path) {
            const p = segInfo.path;
            html += `<p style="font-size:12px;color:#1a73e8;">🚗 ${(p.distance/1000).toFixed(1)}km · ${Math.round(p.duration/60)}分钟 · ${p.steps ? p.steps.length : 0}步</p>`;
            if (p.steps && p.steps.length > 0) {
                html += `<div style="font-size:11px;color:var(--text-secondary);padding-left:8px;border-left:2px solid #34a853;margin-top:4px;max-height:160px;overflow-y:auto;">`;
                var stepIconMap = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'];
                for (let s = 0; s < p.steps.length; s++) {
                    var si = stepIconMap[s] || (s+1);
                    var stepDist = (p.steps[s].distance / 1000).toFixed(1);
                    html += `<div style="margin:2px 0;display:flex;gap:4px;align-items:flex-start;">
                        <span style="color:#34a853;font-weight:bold;flex-shrink:0;font-size:11px;">${si}</span>
                        <span style="font-size:11px;">${p.steps[s].instruction}</span>
                        <span style="color:#999;flex-shrink:0;white-space:nowrap;font-size:10px;">${stepDist}km</span>
                    </div>`;
                }
                html += `<div style="margin-top:4px;padding-top:4px;border-top:1px solid #ddd;color:#1a73e8;font-weight:bold;font-size:11px;">
                    🚗 本段共${(p.distance/1000).toFixed(1)}km · ${Math.round(p.duration/60)}分钟 · ${p.steps.length}步
                </div>`;
                html += `</div>`;
            }
        } else {
            // 驾车API失败时显示直线距离估算
            var fallbackDist = distKm ? distKm : (seg ? (seg.segDist/1000).toFixed(1) : '--');
            var errMsg = (segInfo && segInfo.error) ? segInfo.error : '直线连接';
            html += `<p style="font-size:12px;color:#FF8800;">⚠️ ${errMsg} · 直线约${fallbackDist}km</p>`;
        }
        html += `</div>`;
    });
    html += `<div class="result-item" style="background:#e8f5e9;padding:6px 10px;font-size:12px;">
        <p>🏁 <strong>终点</strong> ${data.ordered_spots[data.ordered_spots.length-1].name}</p>
    </div>`;
    listEl.innerHTML = html;
}

// ==================== 驾车设起点/终点模式切换 ====================

function setDrivePickMode(mode) {
    drivePickMode = mode;
    // 按钮高亮切换
    var originBtn = document.getElementById('pickOriginBtn');
    var destBtn = document.getElementById('pickDestBtn');
    if (originBtn) {
        originBtn.style.background = mode === 'origin' ? '#1a73e8' : '#999';
        originBtn.style.boxShadow = mode === 'origin' ? '0 2px 6px rgba(26,115,232,0.2)' : 'none';
    }
    if (destBtn) {
        destBtn.style.background = mode === 'dest' ? '#ea4335' : '#999';
        destBtn.style.boxShadow = mode === 'dest' ? '0 2px 6px rgba(234,67,53,0.2)' : 'none';
    }
    showTip(mode === 'origin' ? '请在地图上点击设置起点' : '请在地图上点击设置终点', 'info');
}

// ==================== 清除起点终点 ====================

function clearDrivePoints() {
    // 清除起点标记
    if (driveStartMarker) { map.remove(driveStartMarker); driveStartMarker = null; }
    // 清除终点标记（可能是 scenic.js 中 goDriveToSpot 创建的）
    if (typeof driveEndMarker !== 'undefined' && driveEndMarker) {
        try { map.remove(driveEndMarker); } catch(e) {}
        driveEndMarker = null;
    }
    // 清除所有路径规划路线
    clearPolylines(routePolylines);
    clearMarkers(routeMarkers);
    // 重置坐标
    window.driveOriginCoords = null;
    window.driveDestCoords = null;
    // 清空输入框
    document.getElementById('driveOrigin').value = '';
    document.getElementById('driveDest').value = '';
    document.getElementById('routeResultList').innerHTML = '';
    showTip('已清除起点、终点和路线', 'info');
}

function clearBusPoints() {
    if (busStartMarker) map.remove(busStartMarker);
    if (busEndMarker) map.remove(busEndMarker);
    busStartMarker = null; busEndMarker = null;
    window.busStartCoords = null; window.busEndCoords = null;
    document.getElementById('busStart').value = '';
    document.getElementById('busEnd').value = '';
    document.getElementById('routeResultList').innerHTML = '';
    showTip('已清除公交起点和终点', 'info');
}

// ==================== 公交换乘 ====================

async function queryBusRoute() {
    if (!window.busStartCoords || !window.busEndCoords) {
        showTip('请在地图上点击设置起点和终点站（先点起点，再点终点）', 'warning');
        return;
    }

    const start = window.busStartCoords;
    const end = window.busEndCoords;

    try {
        showTip('正在查询公交换乘方案...', 'info');
        const result = await apiQueryBus({
            start_lat: start.lat,
            start_lng: start.lng,
            end_lat: end.lat,
            end_lng: end.lng,
        });

        if (result.code === 200) {
            displayBusResult(result.data);
        } else {
            showTip(result.msg || '查询失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

function displayBusResult(data) {
    const listEl = document.getElementById('routeResultList');
    clearPolylines(routePolylines);

    if (data.source === 'local' && data.paths && data.paths.length > 0) {
        let html = `<h4>🚌 公交换乘方案</h4>`;
        data.paths.forEach((path, idx) => {
            html += `<div class="result-item" style="margin-bottom:8px;">
                <p><strong>方案${idx + 1}</strong> · ${path.transfer_count || 0}次换乘 · 总距离${(path.total_distance/1000).toFixed(1)}km</p>`;
            if (path.segments && path.segments.length > 0) {
                path.segments.forEach((seg, si) => {
                    if (seg.route) {
                        html += `<p style="font-size:13px;color:#1a73e8;margin:4px 0;">🚌 乘坐 <strong>${seg.route}</strong> 从 ${seg.from} 到 ${seg.to}</p>`;
                    }
                });
            } else {
                html += `<p style="font-size:12px;color:var(--text-secondary);">${path.stations.join(' → ')}</p>`;
            }
            html += `</div>`;
        });
        listEl.innerHTML = html;
    } else if (data.source === 'amap' && data.transits) {
        let html = `<h4>🚌 公交换乘方案（高德）</h4>`;
        data.transits.slice(0, 3).forEach((transit, idx) => {
            const distance = transit.distance || 0;
            const duration = transit.duration || 0;
            html += `<div class="result-item">
                <p><strong>方案${idx + 1}</strong></p>
                <p>总距离: ${(distance / 1000).toFixed(1)} km</p>
                <p>预计耗时: ${Math.round(duration / 60)} 分钟</p>
                <p>步行距离: ${(transit.walking_distance || 0).toFixed(0)}m</p>
            </div>`;
        });
        listEl.innerHTML = html;
    } else {
        listEl.innerHTML = '<p class="hint">未找到换乘方案</p>';
    }
}

// 设置公交起点/终点（地图点击）
function setBusStart(lat, lng, name) {
    window.busStartCoords = { lat, lng, name };
    document.getElementById('busStart').value = `${name} (${lng.toFixed(4)}, ${lat.toFixed(4)})`;
    if (busStartMarker) map.remove(busStartMarker);
    busStartMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
        anchor: 'bottom-center',
    });
    map.add(busStartMarker);
}

function setBusEnd(lat, lng, name) {
    window.busEndCoords = { lat, lng, name };
    document.getElementById('busEnd').value = `${name} (${lng.toFixed(4)}, ${lat.toFixed(4)})`;
    if (busEndMarker) map.remove(busEndMarker);
    busEndMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
        anchor: 'bottom-center',
    });
    map.add(busEndMarker);
}
