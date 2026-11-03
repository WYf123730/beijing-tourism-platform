/**
 * 主应用入口模块
 * 模块切换、初始化、全局事件
 */

// ==================== 模块切换 ====================

function switchModule(module) {
    currentModule = module;

    // 更新导航按钮状态
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.nav-btn[data-module="${module}"]`).classList.add('active');

    // 更新面板
    document.querySelectorAll('.panel-content').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(`panel-${module}`);
    if (panel) panel.classList.add('active');

    // ==================== 彻底清除地图上的所有标注和绘制 ====================
    // 关闭鼠标工具
    if (mouseTool) mouseTool.close(true);
    if (map) map.off('click', onDrawPointClick);

    // 全面清除所有标记、路线、绘制图形、缓冲区、事故点等
    clearAllMarkers();
    clearDrawnOverlays();
    clearMarkers(routeMarkers);

    // 重置TSP起点
    if (window.tspStartMarker) {
        map.remove(window.tspStartMarker);
        window.tspStartMarker = null;
    }

    // 重置路径规划状态
    window.driveOriginCoords = null;
    window.driveDestCoords = null;
    window.busStartCoords = null;
    window.busEndCoords = null;
    document.getElementById('driveOrigin').value = '';
    document.getElementById('driveDest').value = '';
    document.getElementById('busStart').value = '';
    document.getElementById('busEnd').value = '';

    // ==================== 更新地图提示 ====================
    const tipMap = {
        'map': '使用左侧地图工具操作',
        'query': '选择绘制工具在地图上绘制查询范围',
        'scenic': '输入关键词搜索北京景点',
        'route': '选择路径规划方式，在地图上设置起点终点',
        'analysis': '点击地图设置事故点，进行救援分析',
        'weather': '查看各景区实时天气信息',
        'admin': '管理景点数据（增删改查）',
    };
    document.getElementById('mapTip').textContent = tipMap[module] || '选择功能模块开始操作';

    // 特殊模块加载数据
    if (module === 'weather') {
        loadWeather();
    } else if (module === 'route') {
        document.getElementById('routeResultList').innerHTML = '';
    } else if (module === 'admin') {
        showAdminPanel();
    }
}

// ==================== 提示消息 ====================

let tipTimer = null;

function showTip(message, type = 'info') {
    const tip = document.getElementById('mapTip');
    tip.textContent = message;

    // 根据类型改变颜色
    const colors = {
        'info': 'rgba(255,255,255,0.95)',
        'success': '#e8f5e9',
        'warning': '#fff3e0',
        'error': '#ffebee',
    };
    tip.style.background = colors[type] || colors.info;

    // 自动恢复
    if (tipTimer) clearTimeout(tipTimer);
    tipTimer = setTimeout(() => {
        tip.style.background = 'rgba(255,255,255,0.95)';
    }, 3000);
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('北京市文旅景点服务平台初始化中...');

    // 初始化地图
    initMap();

    // 初始化认证
    initAuth();

    // 设置默认模块
    switchModule('map');

    console.log('北京市文旅景点服务平台初始化完成');
});

// ==================== 左侧面板隐藏/显示 ====================

let panelVisible = true;

function togglePanel() {
    const panel = document.getElementById('sidePanel');
    const btn = document.getElementById('panelToggle');
    panelVisible = !panelVisible;

    if (panelVisible) {
        panel.classList.remove('panel-collapsed');
        btn.textContent = '◀';
        btn.title = '隐藏面板';
    } else {
        panel.classList.add('panel-collapsed');
        btn.textContent = '▶';
        btn.title = '显示面板';
    }

    // 通知地图重新计算大小
    if (map && typeof map.resize === 'function') {
        setTimeout(function() { map.resize(); }, 350);
    }
}

// ==================== 窗口大小调整 ====================

window.addEventListener('resize', function() {
    if (map) {
        map.resize();
    }
});

// ==================== 点击弹窗外关闭 ====================

window.addEventListener('click', function(e) {
    const modal = document.getElementById('loginModal');
    if (e.target === modal) {
        closeLoginModal();
    }
});
