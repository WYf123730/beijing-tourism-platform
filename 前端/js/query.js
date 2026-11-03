/**
 * 空间查询模块
 * POI 绘制查询、结果展示、分页
 */

// ==================== 公用工具函数 ====================

function haversine(lat1, lng1, lat2, lng2) {
    /** Haversine 公式计算两点间距离（米）*/
    const R = 6371000;
    const toRad = deg => deg * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLng = toRad(lng2 - lng1);
    const a = Math.sin(dLat / 2) ** 2
            + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2))
            * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

let queryPage = 1;
let queryTotal = 0;
let queryPageSize = 500;  // 改为大容量，一次性返回全部结果
let queryResults = [];
let queryCategory = '';
let drawnOverlays = [];  // 跟踪绘制的图形，用于清除

// 保存最后一次查询的类型和参数，用于分页重新查询
let lastQueryType = null;
let lastQueryParams = {};

// ==================== 绘制事件处理 ====================

function onDrawPointClick(e) {
    const lng = e.lnglat.getLng();
    const lat = e.lnglat.getLat();
    map.off('click', onDrawPointClick);

    // 添加点标记
    const marker = new AMap.Marker({
        position: [lng, lat],
        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
        anchor: 'bottom-center',
    });
    map.add(marker);
    drawnOverlays.push(marker);

    // 执行点查询
    queryPointPOI(lat, lng);
    showTip(`正在查询点 (${lng.toFixed(4)}, ${lat.toFixed(4)}) 附近POI`, 'info');
}

function onRectDraw(e) {
    try {
        if (!e || !e.obj) {
            showTip('绘制对象无效', 'error');
            return;
        }
        // 将绘制的图形添加到地图
        map.add(e.obj);
        drawnOverlays.push(e.obj);

        const bounds = e.obj.getBounds();
        if (!bounds) { showTip('获取矩形范围失败', 'error'); return; }
        const southWest = bounds.getSouthWest();
        const northEast = bounds.getNorthEast();
        if (!southWest || !northEast) { showTip('获取矩形边界失败', 'error'); return; }

        queryRectPOI(
            southWest.getLat(), southWest.getLng(),
            northEast.getLat(), northEast.getLng()
        );
        // 关闭绘制工具（保留已画好的图形）
        if (mouseTool) { mouseTool.close(); }
    } catch(err) {
        console.error('矩形绘制处理失败:', err);
        showTip('矩形查询失败: ' + err.message, 'error');
    }
}

function onCircleDraw(e) {
    try {
        if (!e || !e.obj) {
            showTip('绘制对象无效', 'error');
            return;
        }
        map.add(e.obj);
        drawnOverlays.push(e.obj);

        // 高德 MouseTool 绘制的圆形实际返回的是 Polygon 对象
        // 需要从顶点计算中心和半径
        let path = null;
        let center = null;
        let radius = 0;

        // 尝试获取路径（Polygon用getPath，Circle用getCenter+getRadius）
        if (e.obj.getPath) {
            path = e.obj.getPath();
        } else if (e.obj.getCenter && e.obj.getRadius) {
            center = e.obj.getCenter();
            radius = e.obj.getRadius();
        }

        if (path && path.length > 0) {
            // 从多边形顶点计算中心（取所有顶点的平均坐标）
            let sumLng = 0, sumLat = 0, count = path.length;
            for (let i = 0; i < count; i++) {
                sumLng += path[i].getLng();
                sumLat += path[i].getLat();
            }
            const centerLat = sumLat / count;
            const centerLng = sumLng / count;

            // 用 Haversine 公式计算中心到各顶点的平均距离（米），比平面近似更准确
            let totalDist = 0;
            for (let i = 0; i < count; i++) {
                totalDist += haversine(centerLat, centerLng, path[i].getLat(), path[i].getLng());
            }
            radius = totalDist / count;
            center = { getLat: () => centerLat, getLng: () => centerLng };
        }

        if (!center || !radius) {
            showTip('获取圆形参数失败', 'error');
            return;
        }

        queryCirclePOI(center.getLat(), center.getLng(), radius);
        showTip(`正在查询半径 ${radius.toFixed(0)}m 内的POI`, 'info');
        // 关闭绘制工具（保留已画好的图形）
        if (mouseTool) { mouseTool.close(); }
    } catch(err) {
        console.error('圆形绘制处理失败:', err);
        showTip('圆形查询失败: ' + err.message, 'error');
    }
}

function onPolygonDraw(e) {
    try {
        if (!e || !e.obj) {
            showTip('绘制对象无效', 'error');
            return;
        }
        map.add(e.obj);
        drawnOverlays.push(e.obj);

        const path = e.obj.getPath();
        if (!path || path.length < 3) {
            showTip('多边形顶点不足', 'error');
            return;
        }
        const coords = path.map(p => [p.getLng(), p.getLat()]);

        queryPolygonPOI(coords);
        showTip('正在查询多边形范围内的POI', 'info');
        // 关闭绘制工具（保留已画好的图形）
        if (mouseTool) { mouseTool.close(); }
    } catch(err) {
        console.error('多边形绘制处理失败:', err);
        showTip('多边形查询失败: ' + err.message, 'error');
    }
}

// ==================== POI 类别切换 ====================

function onPoiCategoryChange() {
    queryCategory = document.getElementById('poiCategory').value;
}

// 分类标签点击（替代下拉框）
function selectPoiCategory(el, value) {
    // 切换标签高亮
    document.querySelectorAll('#poiCategoryTags .cat-tag').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    // 同步隐藏的select
    document.getElementById('poiCategory').value = value;
    onPoiCategoryChange();
    // 如果已经画过范围，按新类别重新查询
    reQueryWithCategory();
}

// ==================== API 查询 ====================

// 获取当前选中的POI类别
function getCurrentPoiCategory() {
    return document.getElementById('poiCategory').value || undefined;
}

// 用上一次的查询范围+当前类别重新查询
function reQueryWithCategory() {
    if (!lastQueryType) {
        showTip('请先在地图上绘制查询范围', 'warning');
        return;
    }
    queryPage = 1;
    rerunLastQuery();
}

function clearOldQueryMarkers() {
    // 发起新查询前清除旧的POI标记，避免旧标记与新标记重叠
    clearMarkers(queryMarkers);
}

async function queryPointPOI(lat, lng) {
    try {
        clearOldQueryMarkers();  // 清除旧POI标记，新查询结果到时与绘制范围一起出现
        lastQueryType = 'point';
        lastQueryParams = { lat, lng, radius: 500, page_size: queryPageSize };
        const result = await apiQueryPoiPoint({
            lat, lng, radius: 500,
            category: getCurrentPoiCategory(),
            page: queryPage,
            page_size: queryPageSize,
        });
        if (result.code === 200) {
            displayQueryResults(result.data, result.total, result.page, 'point');
        } else {
            showTip(result.msg || '查询失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

async function queryRectPOI(minLat, minLng, maxLat, maxLng) {
    try {
        clearOldQueryMarkers();  // 清除旧POI标记
        lastQueryType = 'rect';
        lastQueryParams = { min_lat: minLat, min_lng: minLng, max_lat: maxLat, max_lng: maxLng, page_size: queryPageSize };
        const result = await apiQueryPoiRect({
            min_lat: minLat, min_lng: minLng,
            max_lat: maxLat, max_lng: maxLng,
            category: getCurrentPoiCategory(),
            page: queryPage,
            page_size: queryPageSize,
        });
        if (result.code === 200) {
            displayQueryResults(result.data, result.total, result.page, 'rect');
        } else {
            showTip(result.msg || '查询失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

async function queryCirclePOI(lat, lng, radius) {
    try {
        clearOldQueryMarkers();  // 清除旧POI标记，让新绘制的圆形范围先展示
        lastQueryType = 'circle';
        lastQueryParams = { lat, lng, radius, page_size: queryPageSize };
        const result = await apiQueryPoiCircle({
            lat, lng, radius,
            category: getCurrentPoiCategory(),
            page: queryPage,
            page_size: queryPageSize,
        });
        if (result.code === 200) {
            displayQueryResults(result.data, result.total, result.page, 'circle');
        } else {
            showTip(result.msg || '查询失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

async function queryPolygonPOI(coordinates) {
    try {
        clearOldQueryMarkers();  // 清除旧POI标记
        lastQueryType = 'polygon';
        lastQueryParams = { coordinates, page_size: queryPageSize };
        const result = await apiQueryPoiPolygon({
            coordinates,
            category: getCurrentPoiCategory(),
            page: queryPage,
            page_size: queryPageSize,
        });
        if (result.code === 200) {
            displayQueryResults(result.data, result.total, result.page, 'polygon');
        } else {
            showTip(result.msg || '查询失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}

// ==================== 结果展示 ====================

function displayQueryResults(data, total, page, queryType) {
    queryResults = data;
    queryTotal = total;
    queryPage = page;

    const listEl = document.getElementById('queryResultList');
    if (!data || data.length === 0) {
        listEl.innerHTML = '<p class="hint">未查询到POI数据</p>';
        return;
    }

    // 清除旧标记
    clearMarkers(queryMarkers);

    // 在地图上添加标记
    const iconMap = {
        'hospital': 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
        'school': 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
        'park': 'https://webapi.amap.com/theme/v1.3/markers/n/mark_g.png',
    };

    data.forEach((poi, idx) => {
        const icon = iconMap[poi.category] || 'https://webapi.amap.com/theme/v1.3/markers/n/mark.png';
        const marker = new AMap.Marker({
            position: [poi.longitude, poi.latitude],
            icon: icon,
            anchor: 'bottom-center',
            offset: new AMap.Pixel(-13, -30),
            label: {
                content: `<div style="background:#fff;padding:2px 6px;border-radius:3px;font-size:12px;border:1px solid #ddd;white-space:nowrap;">${poi.name}</div>`,
                offset: new AMap.Pixel(-50, -50),
            },
        });

        marker.on('click', function() {
            const content = createInfoContent(poi.name, [
                { label: '类别', value: getCategoryName(poi.category) },
                { label: '地址', value: poi.address || '暂无' },
                { label: '电话', value: poi.phone || '暂无' },
            ]);
            showInfoWindow(content, [poi.longitude, poi.latitude]);
        });

        map.add(marker);
        queryMarkers.push(marker);
    });

    // 构建结果列表
    let html = `<p style="margin-bottom:8px;font-size:13px;color:var(--text-secondary);">共找到 ${total} 个POI</p>`;
    data.forEach((poi, idx) => {
        const distance = poi.distance ? `<span class="distance">距离: ${poi.distance}m</span>` : '';
        html += `
            <div class="result-item" onclick="flyTo(${poi.longitude}, ${poi.latitude}, 15)">
                <h4>${getCategoryIcon(poi.category)} ${poi.name}</h4>
                <p>类别: ${getCategoryName(poi.category)}</p>
                <p>地址: ${poi.address || '暂无'}</p>
                <p>电话: ${poi.phone || '暂无'} ${distance}</p>
            </div>
        `;
    });

    // 分页
    const totalPages = Math.ceil(total / queryPageSize);
    if (totalPages > 1) {
        html += `
            <div class="pagination">
                <button ${page <= 1 ? 'disabled' : ''} onclick="queryPrevPage()">上一页</button>
                <span>第 ${page}/${totalPages} 页</span>
                <button ${page >= totalPages ? 'disabled' : ''} onclick="queryNextPage()">下一页</button>
            </div>
        `;
    }

    listEl.innerHTML = html;
}

function getCategoryName(category) {
    const names = {'hospital':'🏥 医院','school':'🏫 学校','park':'🌳 公园','mall':'🛍️ 购物','bank':'🏦 银行','restaurant':'🍜 餐饮','hotel':'🏨 酒店','gas_station':'⛽ 加油站','library':'📚 图书馆','stadium':'🏟️ 体育馆','theater':'🎭 剧院'};
    return names[category] || category || '其他';
}

function getCategoryIcon(category) {
    const icons = {'hospital':'🏥','school':'🏫','park':'🌳','mall':'🛍️','bank':'🏦','restaurant':'🍜','hotel':'🏨','gas_station':'⛽','library':'📚','stadium':'🏟️','theater':'🎭','police':'👮','fire':'🚒'};
    return icons[category] || '📍';
}

// ==================== 分页 ====================

function queryPrevPage() {
    if (queryPage > 1) {
        queryPage--;
        rerunLastQuery();
    }
}

function queryNextPage() {
    queryPage++;
    rerunLastQuery();
}

async function rerunLastQuery() {
    if (!lastQueryType) {
        showTip('请先绘制查询范围', 'warning');
        return;
    }
    try {
        // 用保存的几何参数 + 当前选中的类别
        const category = getCurrentPoiCategory();
        const params = { ...lastQueryParams, category, page: queryPage, page_size: queryPageSize };
        let result;
        switch (lastQueryType) {
            case 'point':
                result = await apiQueryPoiPoint(params);
                break;
            case 'rect':
                result = await apiQueryPoiRect(params);
                break;
            case 'circle':
                result = await apiQueryPoiCircle(params);
                break;
            case 'polygon':
                result = await apiQueryPoiPolygon({ coordinates: lastQueryParams.coordinates, category, page: queryPage, page_size: queryPageSize });
                break;
        }
        if (result && result.code === 200) {
            displayQueryResults(result.data, result.total, result.page, lastQueryType);
        } else {
            showTip((result && result.msg) || '查询失败', 'error');
        }
    } catch (e) {
        showTip('分页查询失败', 'error');
    }
}
