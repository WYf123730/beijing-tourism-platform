/**
 * 综合分析模块
 * 缓冲区分析、叠置分析
 */

let accidentPoint = null;
// 存储叠置分析生成的多边形，用于清除
let tempZonePolygons = [];

// ==================== 地图点击设置事故点 ====================

function onMapClick(e) {
    const lng = e.lnglat.getLng();
    const lat = e.lnglat.getLat();

    // TSP起点选择模式（优先处理）
    if (typeof tspWaitingForClick !== 'undefined' && tspWaitingForClick) {
        handleTspMapClick(lat, lng);
        return;
    }

    // 根据不同模块处理点击
    if (currentModule === 'analysis') {
        setAccidentPoint(lat, lng);
    } else if (currentModule === 'route' && currentRouteTab === 'drive') {
        // 按当前模式设置起点或终点
        if (typeof drivePickMode === 'undefined') drivePickMode = 'origin';
        if (drivePickMode === 'dest') {
            // 设终点
            window.driveDestCoords = { lat, lng, name: '地图选点' };
            document.getElementById('driveDest').value = '地图选点 (' + lng.toFixed(4) + ', ' + lat.toFixed(4) + ')';
            if (driveEndMarker) { map.remove(driveEndMarker); driveEndMarker = null; }
            driveEndMarker = new AMap.Marker({
                position: [lng, lat],
                icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
                anchor: 'bottom-center',
                label: { content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;">终点</div>', offset: new AMap.Pixel(-20, -40) },
            });
            map.add(driveEndMarker);
            showTip('终点已设置，点击"规划路线"查看驾车方案', 'success');
        } else {
            // 设起点
            window.driveOriginCoords = { lat, lng, name: '地图选点' };
            document.getElementById('driveOrigin').value = '地图选点 (' + lng.toFixed(4) + ', ' + lat.toFixed(4) + ')';
            if (driveStartMarker) { map.remove(driveStartMarker); driveStartMarker = null; }
            driveStartMarker = new AMap.Marker({
                position: [lng, lat],
                icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
                anchor: 'bottom-center',
                label: { content: '<div style="background:#34a853;color:#fff;padding:2px 8px;border-radius:4px;">起点</div>', offset: new AMap.Pixel(-20, -40) },
            });
            map.add(driveStartMarker);
            showTip('起点已设置，点击"规划路线"查看驾车方案', 'success');
        }
        clearPolylines(routePolylines);
    } else if (currentModule === 'route' && currentRouteTab === 'bus') {
        // 公交——设置站点（可循环重置）
        if (!window.busStartCoords) {
            setBusStartFromMap(lat, lng);
        } else if (!window.busEndCoords) {
            setBusEndFromMap(lat, lng);
        } else {
            // 已设完起点终点，再次点击从头设置
            if (busStartMarker) map.remove(busStartMarker);
            if (busEndMarker) map.remove(busEndMarker);
            busStartMarker = null;
            busEndMarker = null;
            window.busStartCoords = null;
            window.busEndCoords = null;
            document.getElementById('busStart').value = '';
            document.getElementById('busEnd').value = '';
            setBusStartFromMap(lat, lng);
            showTip('已重置，请继续点击设置终点站', 'info');
        }
    }
}

function setAccidentPoint(lat, lng) {
    accidentPoint = { lat, lng };

    // 清除旧标记
    if (accidentMarker) map.remove(accidentMarker);

    // 添加事故点标记
    accidentMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
        anchor: 'bottom-center',
        label: {
            content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;font-weight:bold;">⚠️ 事故点</div>',
            offset: new AMap.Pixel(-35, -40),
        },
    });
    map.add(accidentMarker);

    document.getElementById('accidentPoint').value = `(${lng.toFixed(6)}, ${lat.toFixed(6)})`;
    showTip('已设置事故点，可进行缓冲区或叠置分析', 'success');
}

// ==================== 驾车路径从地图点击 ====================

function setDriveOriginFromMap(lat, lng) {
    window.driveOriginCoords = { lat, lng, name: '地图选点' };
    document.getElementById('driveOrigin').value = `地图选点 (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    if (driveStartMarker) map.remove(driveStartMarker);
    driveStartMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#34a853;color:#fff;padding:2px 8px;border-radius:4px;">起点</div>', offset: new AMap.Pixel(-20, -40) },
    });
    map.add(driveStartMarker);
    showTip('已设置驾车起点，点击地图设置终点', 'info');
}

function setDriveDestFromMap(lat, lng) {
    window.driveDestCoords = { lat, lng, name: '地图选点' };
    document.getElementById('driveDest').value = `地图选点 (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    if (driveEndMarker) map.remove(driveEndMarker);
    driveEndMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;">终点</div>', offset: new AMap.Pixel(-20, -40) },
    });
    map.add(driveEndMarker);
    showTip('已设置驾车终点，点击"规划驾车路线"', 'success');
}

// ==================== 公交站点从地图点击 ====================

function setBusStartFromMap(lat, lng) {
    window.busStartCoords = { lat, lng, name: '地图选点' };
    document.getElementById('busStart').value = `地图选点 (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    if (busStartMarker) map.remove(busStartMarker);
    busStartMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_s.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#34a853;color:#fff;padding:2px 8px;border-radius:4px;">起点站</div>', offset: new AMap.Pixel(-25, -40) },
    });
    map.add(busStartMarker);
    showTip('已设置公交起点，点击地图设置终点站', 'info');
}

function setBusEndFromMap(lat, lng) {
    window.busEndCoords = { lat, lng, name: '地图选点' };
    document.getElementById('busEnd').value = `地图选点 (${lng.toFixed(4)}, ${lat.toFixed(4)})`;

    if (busEndMarker) map.remove(busEndMarker);
    busEndMarker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_e.png',
        anchor: 'bottom-center',
        label: { content: '<div style="background:#ea4335;color:#fff;padding:2px 8px;border-radius:4px;">终点站</div>', offset: new AMap.Pixel(-25, -40) },
    });
    map.add(busEndMarker);
    showTip('已设置公交终点，点击"查询换乘"', 'info');
}

// ==================== 缓冲区分析 ====================

async function runBufferAnalysis() {
    if (!accidentPoint) {
        showTip('请先在地图上设置事故点', 'warning');
        return;
    }

    const radius = parseInt(document.getElementById('bufferRadius').value) || 1000;

    try {
        showTip('正在进行缓冲区分析...', 'info');
        const result = await apiBufferAnalysis({
            lat: accidentPoint.lat,
            lng: accidentPoint.lng,
            radius: radius,
        });

        if (result.code === 200) {
            displayBufferResult(result.data, radius);
        } else {
            showTip(result.msg || '分析失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

function displayBufferResult(data, radius) {
    const listEl = document.getElementById('analysisResultList');

    // 清除旧覆盖物
    clearOverlays();

    // 清除旧缓冲区
    if (window._bufferCircle) { map.remove(window._bufferCircle); window._bufferCircle = null; }
    // 绘制缓冲区（圆形）
    const circle = new AMap.Circle({
        center: [data.accident_point.lng, data.accident_point.lat],
        radius: radius,
        fillColor: '#1a73e8',
        fillOpacity: 0.15,
        strokeColor: '#1a73e8',
        strokeWeight: 2,
        strokeStyle: 'dashed',
    });
    map.add(circle); window._bufferCircle = circle;

    // 添加救援资源标记
    if (data.resources && data.resources.length > 0) {
        data.resources.forEach(res => {
            const marker = new AMap.Marker({
                position: [res.longitude, res.latitude],
                icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_g.png',
                anchor: 'bottom-center',
                label: {
                    content: `<div style="background:#34a853;color:#fff;padding:2px 6px;border-radius:3px;font-size:11px;">${res.name}</div>`,
                    offset: new AMap.Pixel(-35, -40),
                },
            });
            marker.on('click', function() {
                const content = createInfoContent(res.name, [
                    { label: '类型', value: res.type },
                    { label: '地址', value: res.address || '暂无' },
                    { label: '电话', value: res.phone || '暂无' },
                    { label: '容量', value: res.capacity || '暂无' },
                    { label: '距离', value: `${res.distance || 0}m` },
                ]);
                showInfoWindow(content, [res.longitude, res.latitude]);
            });
            map.add(marker);
            tempAnalysisMarkers.push(marker);  // 追踪以便清除
        });

        map.setFitView([circle, ...map.getAllOverlays().filter(o => o instanceof AMap.Marker)], false, [60, 60, 60, 60]);
    }

    // 显示结果
    let html = `<h4>📊 缓冲区分析结果</h4>`;
    html += `<div class="result-item">
        <p><strong>缓冲区半径:</strong> ${radius}m</p>
        <p><strong>救援资源总数:</strong> ${data.total_count} 个</p>
    </div>`;

    if (data.type_stats) {
        html += `<h4>资源类型分布</h4>`;
        Object.entries(data.type_stats).forEach(([type, count]) => {
            html += `<div class="result-item" style="padding:6px 10px;">
                <p>${type}: ${count} 个</p>
            </div>`;
        });
    }

    html += `<h4>资源列表</h4>`;
    data.resources.forEach((res, idx) => {
        html += `<div class="result-item" style="padding:6px 10px;font-size:12px;" onclick="flyTo(${res.longitude}, ${res.latitude}, 16)">
            <p><strong>${res.name}</strong> <span class="distance">${res.distance}m</span></p>
            <p>${res.type} | ${res.phone || '无电话'}</p>
        </div>`;
    });

    listEl.innerHTML = html;
    showTip(`缓冲区分析完成，找到 ${data.total_count} 个救援资源`, 'success');
}

// ==================== 清除分析结果 ====================

function clearAnalysis() {
    accidentPoint = null;
    if (accidentMarker) { map.remove(accidentMarker); accidentMarker = null; }
    if (window._bufferCircle) { map.remove(window._bufferCircle); window._bufferCircle = null; }
    // 清除叠置分析区域多边形
    if (tempZonePolygons && tempZonePolygons.length > 0) {
        tempZonePolygons.forEach(function(p) {
            if (p && map) { try { map.remove(p); } catch(e) {} }
        });
        tempZonePolygons = [];
    }
    // 清除叠置分析区域名称标记
    if (tempAnalysisMarkers && tempAnalysisMarkers.length > 0) {
        tempAnalysisMarkers.forEach(function(m) {
            if (m && map) { try { map.remove(m); } catch(e) {} }
        });
        tempAnalysisMarkers = [];
    }
    clearOverlays();
    clearPolylines(routePolylines);
    document.getElementById('accidentPoint').value = '';
    document.getElementById('analysisResultList').innerHTML = '<p class="hint">点击地图设置事故点后进行分析</p>';
    showTip('已清除分析结果（含地图标注）', 'info');
}

// ==================== 叠置分析 ====================

async function runOverlayAnalysis() {
    if (!accidentPoint) {
        showTip('请先在地图上设置事故点', 'warning');
        return;
    }

    try {
        showTip('正在进行叠置分析...', 'info');
        const result = await apiOverlayAnalysis({
            lat: accidentPoint.lat,
            lng: accidentPoint.lng,
        });

        if (result.code === 200) {
            displayOverlayResult(result.data);
        } else {
            showTip(result.msg || '分析失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

function displayOverlayResult(data) {
    try {
        const listEl = document.getElementById('analysisResultList');

        // 清除地图上旧的分析标注
        clearOverlays();
        clearMarkers(tempAnalysisMarkers);
        // 清除旧的叠置多边形
        if (tempZonePolygons && tempZonePolygons.length > 0) {
            tempZonePolygons.forEach(function(p) {
                if (p && map) { try { map.remove(p); } catch(e) {} }
            });
            tempZonePolygons = [];
        }

        // ======== 在地图上绘制结果 ========
        const pt = [data.accident_point.lng, data.accident_point.lat];

        // 绘制叠置分析区域多边形（核心保护区红色，其他蓝色）
        if (data.overlapped_zones && data.overlapped_zones.length > 0) {
            data.overlapped_zones.forEach(function(zone, idx) {
                if (zone.coordinates && zone.coordinates.length >= 3) {
                    var isCore = zone.type === '核心保护区';
                    var zoneColor = isCore ? '#ea4335' : '#1a73e8';
                    try {
                        var polygon = new AMap.Polygon({
                            path: zone.coordinates,
                            strokeColor: zoneColor,
                            strokeWeight: 2,
                            strokeOpacity: 0.8,
                            fillColor: zoneColor,
                            fillOpacity: 0.12,
                            bubble: true,
                        });
                        map.add(polygon);
                        tempZonePolygons.push(polygon);
                        // 添加区域名称标注
                        var lngs = zone.coordinates.map(function(c) { return c[0]; });
                        var lats = zone.coordinates.map(function(c) { return c[1]; });
                        var clng = lngs.reduce(function(a, b) { return a + b; }, 0) / lngs.length;
                        var clat = lats.reduce(function(a, b) { return a + b; }, 0) / lats.length;
                        var textMarker = new AMap.Text({
                            text: '\u{1F4CD} ' + zone.name,
                            position: [clng, clat],
                            style: {
                                'background-color': zoneColor,
                                'border-color': '#fff',
                                'color': '#fff',
                                'font-size': '12px',
                                'padding': '4px 10px',
                                'border-radius': '4px',
                            },
                        });
                        map.add(textMarker);
                        tempAnalysisMarkers.push(textMarker);
                    } catch(e) {
                        console.warn('绘制区域多边形失败:', e.message || e);
                    }
                } else {
                    // 没有坐标的用文字标记
                    var color2 = zoneColor || '#1a73e8';
                    try {
                        var textMarker2 = new AMap.Text({
                            text: '\u{1F4CD} ' + zone.name,
                            position: pt,
                            offset: new AMap.Pixel(-40, -20 + idx * 25),
                            style: {
                                'background-color': color2,
                                'border-color': '#fff',
                                'color': '#fff',
                                'font-size': '12px',
                                'padding': '4px 10px',
                                'border-radius': '4px',
                            },
                        });
                        map.add(textMarker2);
                        tempAnalysisMarkers.push(textMarker2);
                    } catch(e) {}
                }
            });
        }

        // 绘制附近救援资源标记
        if (data.nearby_resources && data.nearby_resources.length > 0) {
            data.nearby_resources.forEach(function(res) {
                try {
                    var marker = new AMap.Marker({
                        position: [res.longitude, res.latitude],
                        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_g.png',
                        anchor: 'bottom-center',
                    });
                    marker.on('click', function() {
                        showInfoWindow(
                            '<div style="padding:8px;"><h4 style="margin:0 0 6px;">' +
                            res.name + '</h4><p style="margin:2px 0;font-size:13px;">' +
                            res.type + ' | ' + (res.phone || '暂无电话') + '</p>' +
                            '<p style="margin:2px 0;font-size:12px;color:#666;">距离: ' +
                            (res.distance || 0) + 'm</p></div>',
                            [res.longitude, res.latitude]
                        );
                    });
                    map.add(marker);
                    tempAnalysisMarkers.push(marker);
                } catch(e) {}
            });
        }

        // ======== 在左侧面板显示结果 ========
        var html = '';
        html += '<div class="analysis-result-header">';
        html += '<h4 style="margin:0 0 4px;color:#1a73e8;">\u{1F532} 叠置分析结果</h4>';
        html += '<button class="tool-btn danger" onclick="clearAnalysisMapAnnotations()" style="font-size:11px;padding:3px 8px;float:right;">✖ 清除标注</button>';
        html += '<div style="clear:both;"></div></div>';

        html += '<div class="result-item" style="padding:8px 10px;margin:6px 0;">';
        html += '<p><strong>⚠️ 事故点:</strong> (' +
            data.accident_point.lng.toFixed(4) + ', ' + data.accident_point.lat.toFixed(4) + ')</p>';
        html += '</div>';

        var zonesLen = (data.overlapped_zones && data.overlapped_zones.length) || 0;
        html += '<h4 style="margin:8px 0 4px;font-size:14px;color:#5f6368;">\u{1F4CD} 覆盖的区域 (' + zonesLen + '个)</h4>';
        if (zonesLen > 0) {
            html += '<div style="max-height:180px;overflow-y:auto;">';
            data.overlapped_zones.forEach(function(zone) {
                var zoneType = zone.type || '未分类';
                var isCore = zone.type === '核心保护区';
                var coreColor = isCore ? '#ea4335' : '#1a73e8';
                var bgStyle = isCore ? 'border-left:3px solid #ea4335;background:#fef2f2;' : 'border-left:3px solid #1a73e8;';
                html += '<div class="result-item" style="padding:6px 10px;margin:3px 0;' + bgStyle + '">';
                html += '<p style="font-weight:600;color:' + coreColor + ';font-size:13px;">' +
                    (isCore ? '🔴 ' : '🔵 ') + zone.name + '</p>';
                html += '<p style="font-size:12px;color:#5f6368;">' + (zone.description || '') + '</p>';
                html += '<p style="font-size:12px;color:#5f6368;">类型: ' + zoneType + '</p></div>';
            });
            html += '</div>';
        } else {
            html += '<div class="result-item"><p>事故点不在预设区域内</p></div>';
        }

        var resCount = data.resources_count || 0;
        html += '<h4 style="margin:8px 0 4px;font-size:14px;color:#5f6368;">\u{1F692} 附近救援资源 (' + resCount + '个)</h4>';
        if (data.nearby_resources && data.nearby_resources.length > 0) {
            html += '<div style="max-height:200px;overflow-y:auto;">';
            data.nearby_resources.forEach(function(res) {
                html += '<div class="result-item" style="padding:6px 10px;margin:3px 0;font-size:12px;" onclick="flyTo(' +
                        res.longitude + ',' + res.latitude + ',16)">';
                html += '<p><strong>' + res.name + '</strong> <span class="distance">' +
                        (res.distance || 0) + 'm</span></p>';
                html += '<p style="color:#5f6368;">' + (res.type || '') + ' | ' +
                        (res.phone || '无电话') + '</p></div>';
            });
            html += '</div>';
        } else {
            html += '<div class="result-item"><p>附近暂无救援资源数据</p></div>';
        }

        listEl.innerHTML = html;
        showTip('叠置分析完成，共找到 ' + resCount + ' 个救援资源', 'success');

    } catch(e) {
        console.error('叠置分析显示失败:', e);
        var listEl = document.getElementById('analysisResultList');
        if (listEl) {
            listEl.innerHTML = '<div class="result-item"><p style="color:red;">显示失败: ' + e.message + '</p></div>';
        }
        showTip('叠置分析显示失败', 'error');
    }
}

// 专门清除叠置分析地图标注
function clearAnalysisMapAnnotations() {
    clearMarkers(tempAnalysisMarkers);
    if (tempZonePolygons && tempZonePolygons.length > 0) {
        tempZonePolygons.forEach(function(p) {
            if (p && map) { try { map.remove(p); } catch(e) {} }
        });
        tempZonePolygons = [];
    }
    if (window._bufferCircle) {
        map.remove(window._bufferCircle);
        window._bufferCircle = null;
    }
    showTip('已清除分析标注', 'info');
}
