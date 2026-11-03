/**
 * 地图模块
 * 高德地图初始化、基础控件、量算工具
 */

let map = null;            // 地图实例
let mouseTool = null;      // 鼠标工具（绘制）
let measureLayer = null;   // 量算图层
let markerLayer = null;    // 标注图层
let drawLayer = null;      // 绘制图层
let currentInfoWindow = null; // 当前信息窗口
let routeLayer = null;     // 路线图层
let overlayLayer = null;   // 叠置分析图层

// 当前模块状态
let currentModule = 'map';
let currentDrawType = null;
let measureType = null;
let isMapReady = false;

// 存储信息
let queryMarkers = [];
let scenicMarkers = [];
let weatherMarkers = [];  // 天气标记（独立于景点标记）
let routeMarkers = [];
let routePolylines = [];
let tempAnalysisMarkers = [];  // 综合分析临时标记

// 工具状态
let accidentMarker = null;
let driveStartMarker = null;
let driveEndMarker = null;
let busStartMarker = null;
let busEndMarker = null;

// ==================== 地图初始化 ====================

function initMap(center = [116.397, 39.913], zoom = 13) {
    // 等待AMap加载完成（高德API异步加载时的保护）
    if (typeof AMap === 'undefined') {
        console.warn('AMap未就绪，等待加载...');
        var checkTimer = setInterval(function() {
            if (typeof AMap !== 'undefined') {
                clearInterval(checkTimer);
                console.log('AMap已就绪，开始初始化地图');
                _doInitMap(center, zoom);
            }
        }, 200);
        // 10秒超时
        setTimeout(function() {
            clearInterval(checkTimer);
            document.getElementById('mapTip').textContent = '⚠️ 地图加载超时，请检查网络和Key配置';
        }, 10000);
        return;
    }
    _doInitMap(center, zoom);
}

function _doInitMap(center, zoom) {
    // 通过plugin加载所有需要的控件和工具
    AMap.plugin([
        'AMap.Scale',
        'AMap.HawkEye',
        'AMap.MapType',
        'AMap.ToolBar',
        'AMap.MouseTool',
        'AMap.DistrictSearch',
    ], function() {
        // 所有插件加载完成后再初始化地图
        _initMapCore(center, zoom);
    });
}

function _initMapCore(center, zoom) {
    try {
        // 重置控件追踪
        _mapControls = {};
        map = new AMap.Map('map', {
            center: center,
            zoom: zoom,
            resizeEnable: true,
            mapStyle: 'amap://styles/light',
            features: ['bg', 'road', 'building', 'point'],
        });

        // 添加基础控件并存入_mapControls（供toggleControl使用）

        // 鼠标工具
        try {
            mouseTool = new AMap.MouseTool(map);
        } catch(e) {
            console.warn('MouseTool加载失败:', e);
        }

        // 创建图层
        markerLayer = new AMap.LabelsLayer({ zooms: [3, 20], zIndex: 120 });
        map.add(markerLayer);
        drawLayer = new AMap.LabelsLayer({ zooms: [3, 20], zIndex: 130 });
        map.add(drawLayer);
        routeLayer = new AMap.LabelsLayer({ zooms: [3, 20], zIndex: 140 });
        map.add(routeLayer);
        overlayLayer = new AMap.LabelsLayer({ zooms: [3, 20], zIndex: 125 });
        map.add(overlayLayer);

        // 地图点击事件
        map.on('click', onMapClick);

        // 鼠标移动显示坐标
        map.on('mousemove', function(e) {
            const lng = e.lnglat.getLng().toFixed(6);
            const lat = e.lnglat.getLat().toFixed(6);
            const infoBox = document.getElementById('mapInfoBox');
            if (infoBox) {
                infoBox.innerHTML = `<p>经度: ${lng} | 纬度: ${lat}</p>`;
            }
        });

        // 地图加载完成
        map.on('complete', function() {
            isMapReady = true;
            console.log('高德地图加载完成');
        });

        // 添加行政区划（轻量版）
        try {
            const district = new AMap.DistrictSearch({ level: 'city', subdistrict: 0 });
            district.search('北京市', function(status, result) {
                if (status === 'complete' && result.departmentList && result.departmentList[0]) {
                    const bounds = result.departmentList[0].boundaries;
                    if (bounds && bounds.length) {
                        const polygon = new AMap.Polygon({
                            path: bounds,
                            strokeColor: '#1a73e8',
                            strokeWeight: 2,
                            fillColor: '#1a73e8',
                            fillOpacity: 0.05,
                        });
                        map.add(polygon);
                    }
                }
            });
        } catch(e) {
            console.warn('DistrictSearch加载失败:', e);
        }

        initMapControls();
	        console.log('地图初始化完成');
    } catch(e) {
        console.error('地图初始化失败:', e);
        document.getElementById('mapTip').textContent = '⚠️ 地图加载失败，请检查高德Key和网络连接';
    }
}

// ==================== 地图控件管理 ====================

var _ctrlState = { overview: true, scale: true };
var _ctrlInstances = {};

function toggleControl2(type, show) {
    if (!map) return;
    try {
        if (show) {
            if (!_ctrlInstances[type]) {
                if (type === 'overview') _ctrlInstances[type] = new AMap.HawkEye({ isOpen: true });
                else if (type === 'scale') _ctrlInstances[type] = new AMap.Scale();
            }
            if (_ctrlInstances[type]) {
                map.addControl(_ctrlInstances[type]);
                _ctrlState[type] = true;
            }
        } else {
            if (_ctrlInstances[type]) {
                map.removeControl(_ctrlInstances[type]);
                _ctrlState[type] = false;
            }
        }
    } catch(e) {
        console.warn('toggleControl2:', e);
    }
}

// 地图初始化完成后加载控件
function initMapControls() {
    toggleControl2('overview', true);
    toggleControl2('scale', true);
}

// ==================== 量算工具 ====================

function enableMeasure(type) {
    if (!map) return;
    clearMeasure();

    // 清除之前的绘制
    if (mouseTool) mouseTool.close();

    if (type === 'distance') {
        mouseTool.rule({
            startMarkerOptions: { draggable: false },
            midMarkerOptions: { draggable: false },
            endMarkerOptions: { draggable: false },
            lineOptions: {
                strokeColor: '#FF8800',
                strokeWeight: 3,
                strokeStyle: 'solid',
                strokeOpacity: 0.8,
            },
            labelOptions: {
                text: '距离: {distance}',
                font: '14px Microsoft YaHei',
                fillColor: '#fff',
                strokeColor: '#FF8800',
                padding: '4, 6',
            },
        });
        measureType = 'distance';
        showTip('点击地图进行距离量算，双击结束', 'info');
    } else if (type === 'area') {
        mouseTool.measureArea({
            fillColor: '#1a73e8',
            fillOpacity: 0.3,
            strokeColor: '#1a73e8',
            strokeWeight: 2,
            labelOptions: {
                text: '面积: {area}',
                font: '14px Microsoft YaHei',
                fillColor: '#fff',
                strokeColor: '#1a73e8',
                padding: '4, 6',
            },
        });
        measureType = 'area';
        showTip('点击地图进行面积量算，双击结束', 'info');
    }
}

function clearMeasure() {
    if (mouseTool) {
        mouseTool.close(true);
    }
    measureType = null;
    showTip('已清除量算标注', 'info');
}

// ==================== 清除功能 ====================

function clearAllMarkers() {
    clearMarkers(queryMarkers);
    clearMarkers(scenicMarkers);
    clearMarkers(weatherMarkers);
    clearMarkers(routeMarkers);
    clearMarkers(tempAnalysisMarkers);
    clearPolylines(routePolylines);
    clearOverlays();
    clearDrawnOverlays();

    // 清除TSP起点标记和状态
    if (window.tspStartMarker) {
        map.remove(window.tspStartMarker);
        window.tspStartMarker = null;
    }
    if (typeof tspWaitingForClick !== 'undefined') tspWaitingForClick = false;
    if (typeof tspOriginCoords !== 'undefined') tspOriginCoords = null;

    // 清除事故点标记和状态
    if (accidentMarker) {
        map.remove(accidentMarker);
        accidentMarker = null;
    }
    if (typeof accidentPoint !== 'undefined') accidentPoint = null;

    // 重置路径规划状态
    window.driveOriginCoords = null;
    window.driveDestCoords = null;
    window.busStartCoords = null;
    window.busEndCoords = null;
    ['driveOrigin','driveDest','busStart','busEnd'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.value = '';
    });

    // 重置查询状态
    if (typeof queryPage !== 'undefined') queryPage = 1;
    if (typeof lastQueryType !== 'undefined') lastQueryType = null;
    if (typeof currentDrawType !== 'undefined') currentDrawType = null;

    // 清除分析叠置多边形
    if (typeof tempZonePolygons !== 'undefined' && tempZonePolygons) {
        tempZonePolygons.forEach(function(p) {
            if (p && map) { try { map.remove(p); } catch(e) {} }
        });
        tempZonePolygons.length = 0;
    }

    // 清除信息窗口
    if (currentInfoWindow) {
        currentInfoWindow.close();
        currentInfoWindow = null;
    }
}

function clearMarkers(markersArray) {
    if (!markersArray) return;
    markersArray.forEach(m => {
        if (m && map) {
            map.remove(m);
            m = null;
        }
    });
    markersArray.length = 0;
}

function clearPolylines(polylinesArray) {
    if (!polylinesArray) return;
    polylinesArray.forEach(p => {
        if (p && map) {
            map.remove(p);
            p = null;
        }
    });
    polylinesArray.length = 0;
}

function clearDrawnOverlays() {
    // 清除鼠标绘制的图形（点标记、矩形、圆形、多边形）
    if (typeof drawnOverlays !== 'undefined' && drawnOverlays) {
        drawnOverlays.forEach(obj => {
            if (obj && map) {
                map.remove(obj);
                obj = null;
            }
        });
        drawnOverlays.length = 0;
    }
    // 清除drawLayer标签层
    if (drawLayer) drawLayer.clear();
}

function clearOverlays() {
    // 清除所有独立的路径规划标记
    [driveStartMarker, driveEndMarker, busStartMarker, busEndMarker].forEach(m => {
        if (m && map) {
            map.remove(m);
        }
    });
    driveStartMarker = null;
    driveEndMarker = null;
    busStartMarker = null;
    busEndMarker = null;

    // 清除图层（LabelsLayer对象用clear()）
    [markerLayer, drawLayer, routeLayer, overlayLayer].forEach(layer => {
        if (layer && map) {
            try { layer.clear(); } catch(e) {}
        }
    });

    // 清除信息窗口
    if (currentInfoWindow) {
        currentInfoWindow.close();
        currentInfoWindow = null;
    }
}

// ==================== 添加标注工具 ====================

function addMarker(lng, lat, options = {}) {
    const icon = options.icon || 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png';
    const label = options.label || '';
    const marker = new AMap.Marker({
        position: [lng, lat],
        icon: icon,
        anchor: 'bottom-center',
        offset: new AMap.Pixel(-13, -30),
        label: label ? {
            content: `<div class="marker-label">${label}</div>`,
            offset: new AMap.Pixel(-50, -60),
        } : undefined,
        draggable: options.draggable || false,
    });

    if (options.click) {
        marker.on('click', options.click);
    }

    map.add(marker);
    return marker;
}

function addTextMarker(lng, lat, text, color = '#1a73e8') {
    const marker = new AMap.Text({
        text: text,
        position: [lng, lat],
        offset: new AMap.Pixel(-13, -30),
        style: {
            'background-color': color,
            'border-color': '#fff',
            'color': '#fff',
            'font-size': '12px',
            'padding': '4px 8px',
            'border-radius': '4px',
        },
    });
    map.add(marker);
    return marker;
}

// ==================== 信息窗口 ====================

function showInfoWindow(content, position) {
    if (currentInfoWindow) {
        currentInfoWindow.close();
    }
    currentInfoWindow = new AMap.InfoWindow({
        content: content,
        offset: new AMap.Pixel(0, -30),
        closeWhenClickMap: true,
    });
    currentInfoWindow.open(map, position);
}

function createInfoContent(title, items = [], imageUrl = null) {
    let html = `<div class="scenic-info-window"><h3>${title}</h3>`;
    if (imageUrl) {
        html += `<img src="${imageUrl}" alt="${title}" onerror="this.style.display='none'">`;
    }
    items.forEach(item => {
        html += `<p><strong>${item.label}:</strong> ${item.value}</p>`;
    });
    html += '</div>';
    return html;
}

// ==================== 地图操作 ====================

function flyTo(lng, lat, zoom = 14) {
    if (map) {
        map.setZoomAndCenter(zoom, [lng, lat]);
    }
}

function fitBounds(bounds) {
    if (map && bounds) {
        map.setFitView(null, false, [60, 60, 60, 60]);
    }
}

// ==================== 绘制工具 ====================

function enableDraw(type) {
    if (!map) return;
    currentDrawType = type;
    if (mouseTool) mouseTool.close(true);

    // 开始新绘制前，清除之前的绘制图形和POI标记
    if (typeof drawnOverlays !== 'undefined') {
        drawnOverlays.forEach(obj => { if (obj && map) map.remove(obj); });
        drawnOverlays.length = 0;
    }
    clearMarkers(queryMarkers);
    if (typeof queryPage !== 'undefined') queryPage = 1;
    if (typeof lastQueryType !== 'undefined') lastQueryType = null;
    if (typeof queryResults !== 'undefined') queryResults = [];
    document.getElementById('queryResultList').innerHTML = '<p class="hint">请在地图上绘制查询范围</p>';

    switch (type) {
        case 'point':
            showTip('请在地图上点击选择查询点', 'info');
            map.on('click', onDrawPointClick);
            break;
        case 'rectangle':
            mouseTool.rectangle({
                fillColor: '#1a73e8',
                fillOpacity: 0.2,
                strokeColor: '#1a73e8',
                strokeWeight: 2,
            });
            mouseTool.on('draw', onRectDraw);
            showTip('在地图上拖动绘制矩形查询范围', 'info');
            break;
        case 'circle':
            mouseTool.circle({
                fillColor: '#34a853',
                fillOpacity: 0.2,
                strokeColor: '#34a853',
                strokeWeight: 2,
            });
            mouseTool.on('draw', onCircleDraw);
            showTip('在地图上拖动绘制圆形查询范围', 'info');
            break;
        case 'polygon':
            mouseTool.polygon({
                fillColor: '#ea4335',
                fillOpacity: 0.2,
                strokeColor: '#ea4335',
                strokeWeight: 2,
            });
            mouseTool.on('draw', onPolygonDraw);
            showTip('点击地图绘制多边形，双击结束', 'info');
            break;
    }
}

function clearDrawLayer() {
    if (mouseTool) {
        mouseTool.close(true);
    }
    if (drawLayer) drawLayer.clear();
    // 清除直接添加到地图的绘制图形
    if (typeof drawnOverlays !== 'undefined') {
        drawnOverlays.forEach(obj => { if (obj && map) map.remove(obj); });
        drawnOverlays.length = 0;
    }
    // 同时清除上次查询的POI标记
    clearMarkers(queryMarkers);
    // 重置查询状态
    if (typeof queryPage !== 'undefined') queryPage = 1;
    if (typeof lastQueryType !== 'undefined') lastQueryType = null;
    if (typeof queryResults !== 'undefined') queryResults = [];
    map.off('click', onDrawPointClick);
    currentDrawType = null;
    document.getElementById('queryResultList').innerHTML = '<p class="hint">请在地图上绘制查询范围</p>';
    showTip('已清除绘制', 'info');
}
