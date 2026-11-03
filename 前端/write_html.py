import os

path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\index.html"

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>北京文旅景点信息服务平台</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body,html { width:100%; height:100%; overflow:hidden; font-family:"PingFang SC","Microsoft YaHei",sans-serif; }
#container { width:100%; height:100%; }
:root { --header-bg-start:#1a3a6b; --header-bg-end:#0056b3; --panel-bg:rgba(255,255,255,0.92); --accent-color:#0056b3; --accent-gradient:linear-gradient(135deg,#0056b3 0%,#0070e0 100%); }
#header { position:absolute; top:0; left:0; right:0; height:48px; background:linear-gradient(135deg,var(--header-bg-start) 0%,var(--header-bg-end) 100%); box-shadow:0 2px 16px rgba(0,0,0,0.20); z-index:1000; display:flex; align-items:center; padding:0 20px; color:#fff; user-select:none; }
#header h1 { font-size:16px; font-weight:600; letter-spacing:2px; margin-left:8px; }
#header .sub { font-size:11px; opacity:0.65; margin-left:12px; }
#header .right-area { margin-left:auto; display:flex; align-items:center; gap:10px; }
#header .badge { background:rgba(255,255,255,0.12); border-radius:16px; padding:2px 14px; font-size:10px; }
#header .badge .dot { display:inline-block; width:6px; height:6px; background:#4ade80; border-radius:50%; margin-right:5px; }
#header .login-btn { background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.25); padding:3px 12px; border-radius:12px; font-size:10px; cursor:pointer; }
#weather-widget { position:absolute; top:58px; right:12px; z-index:1000; background:var(--panel-bg); backdrop-filter:blur(10px); border-radius:10px; padding:8px 14px; min-width:130px; box-shadow:0 2px 20px rgba(0,0,0,0.08); border:1px solid rgba(255,255,255,0.3); }
#weather-content { text-align:center; }
#weather-content .temp { font-size:20px; font-weight:700; }
#weather-content .desc { font-size:12px; color:#555; }
#weather-content .detail { font-size:10px; color:#999; }
#search-panel { position:absolute; top:58px; left:12px; z-index:1000; background:var(--panel-bg); backdrop-filter:blur(10px); border-radius:12px; padding:12px; width:340px; max-height:70vh; display:flex; flex-direction:column; box-shadow:0 2px 20px rgba(0,0,0,0.08); border:1px solid rgba(255,255,255,0.3); font-size:12px; overflow-y:auto; }
#search-panel::-webkit-scrollbar { width:3px; }
#search-panel::-webkit-scrollbar-thumb { background:#c1c9d6; border-radius:4px; }
.panel-section { margin-bottom:10px; border-bottom:1px solid #f0f2f5; padding-bottom:8px; }
.panel-section:last-child { border-bottom:none; margin-bottom:0; padding-bottom:0; }
.section-title { font-size:13px; font-weight:600; color:#1a3a5c; margin-bottom:6px; padding-left:8px; border-left:3px solid #1a73e8; }
.search-row { display:flex; gap:6px; margin-bottom:6px; }
.search-row input { flex:1; padding:6px 10px; border:1.5px solid #e8edf4; border-radius:8px; font-size:12px; outline:none; background:#f8faff; height:32px; }
.search-row input:focus { border-color:var(--accent-color); background:#fff; }
.search-row button { padding:6px 16px; background:var(--accent-gradient); color:#fff; border:none; border-radius:8px; cursor:pointer; font-size:12px; height:32px; }
.btn-group { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; }
.btn-group .cat-btn { padding:3px 12px; border:1.5px solid #e0e6ed; border-radius:16px; background:#f8faff; cursor:pointer; font-size:10px; color:#666; font-weight:500; }
.btn-group .cat-btn:hover { border-color:var(--accent-color); color:var(--accent-color); background:#eef4fe; }
.btn-group .cat-btn.active { border-color:var(--accent-color); background:var(--accent-gradient); color:#fff; }
.btn-group .cat-btn.primary { background:var(--accent-gradient); color:#fff; border-color:var(--accent-color); }
.btn-group .cat-btn.danger { background:linear-gradient(135deg,#e53935 0%,#b71c1c 100%); color:#fff; border-color:#e53935; }
.btn-group .cat-btn.warning { background:linear-gradient(135deg,#fb8c00 0%,#e65100 100%); color:#fff; border-color:#fb8c00; }
.input-row { display:flex; flex-direction:column; gap:4px; margin-bottom:4px; }
.input-row input { padding:5px 10px; border:1.5px solid #e8edf4; border-radius:6px; font-size:12px; outline:none; background:#f8faff; height:28px; }
.result-box { max-height:110px; overflow-y:auto; font-size:12px; padding-top:4px; margin-top:4px; min-height:30px; }
.result-box .empty { color:#b0b8c8; text-align:center; padding:10px 0; font-size:11px; }
.result-item { padding:4px 10px; border-radius:6px; cursor:pointer; margin-bottom:2px; border:1px solid transparent; }
.result-item:hover { background:rgba(0,86,179,0.05); }
.result-item .name { font-weight:600; font-size:12px; }
.result-item .addr { font-size:10px; color:#8a9ab0; margin-top:1px; }
#bottom-toolbar { position:absolute; bottom:24px; left:50%; transform:translateX(-50%); z-index:1000; background:rgba(255,255,255,0.94); backdrop-filter:blur(12px); border-radius:14px; box-shadow:0 2px 20px rgba(0,0,0,0.10); border:1px solid rgba(255,255,255,0.3); display:flex; align-items:center; gap:4px; padding:4px 10px; }
#bottom-toolbar .tool-btn { padding:3px 10px; border:1.5px solid transparent; border-radius:12px; background:transparent; cursor:pointer; font-size:10px; color:#555; height:26px; display:flex; align-items:center; gap:3px; white-space:nowrap; }
#bottom-toolbar .tool-btn:hover { background:#eef4fe; color:var(--accent-color); }
#bottom-toolbar .divider { width:1px; height:20px; background:#e0e0e0; margin:0 4px; }
#tip { position:absolute; bottom:68px; left:50%; transform:translateX(-50%); z-index:999; background:rgba(0,0,0,0.40); backdrop-filter:blur(6px); color:rgba(255,255,255,0.80); padding:4px 18px; border-radius:16px; font-size:10px; pointer-events:none; white-space:nowrap; }
#status { position:absolute; bottom:14px; right:14px; z-index:1000; background:rgba(0,0,0,0.45); color:#7fc9ff; padding:3px 12px; border-radius:6px; font-size:9px; pointer-events:none; }
.result-box::-webkit-scrollbar { width:3px; }
.result-box::-webkit-scrollbar-thumb { background:#d0d8e4; border-radius:3px; }
</style>
</head>
<body>
<div id="header">
  <h1>🏛️ 北京文旅</h1>
  <span class="sub">· 景点搜索 · 智能标注</span>
  <div class="right-area">
    <span class="badge"><span class="dot"></span>正常</span>
    <button class="login-btn" id="loginBtn" onclick="showLoginModal()">登录</button>
  </div>
</div>
<div id="container"></div>

<div id="weather-widget">
  <div id="weather-content"><div style="font-size:11px;color:#aaa;">加载天气中...</div></div>
</div>

<div id="search-panel">
  <div class="panel-section">
    <div class="section-title">🔍 空间查询</div>
    <div class="btn-group">
      <button class="cat-btn primary" onclick="enableDraw('point')">👆 点</button>
      <button class="cat-btn" onclick="enableDraw('rectangle')">⬜ 矩形</button>
      <button class="cat-btn" onclick="enableDraw('circle')">⭕ 圆形</button>
      <button class="cat-btn" onclick="enableDraw('polygon')">🔷 多边形</button>
      <button class="cat-btn" onclick="clearDrawLayer()">🗑️</button>
    </div>
    <div class="result-box" id="queryResultList"><div class="empty">选择范围查询</div></div>
  </div>

  <div class="panel-section">
    <div class="section-title">🎯 景点检索</div>
    <div class="search-row">
      <input id="scenicKeyword" placeholder="输入景点名称" onkeydown="if(event.key==='Enter') searchScenic()" />
      <button onclick="searchScenic()">搜索</button>
    </div>
    <div class="result-box" id="scenicResultList"><div class="empty">搜索景点</div></div>
  </div>

  <div class="panel-section">
    <div class="section-title">🗺️ 路径规划</div>
    <div class="btn-group">
      <button class="cat-btn primary" onclick="switchRouteTab('drive')">🚗 驾车</button>
      <button class="cat-btn" onclick="switchRouteTab('tsp')">📋 TSP</button>
      <button class="cat-btn" onclick="switchRouteTab('bus')">🚌 公交</button>
    </div>
    <div id="routeDrivePanel">
      <div class="input-row"><input id="driveOrigin" placeholder="点击地图设起点" readonly /><input id="driveDest" placeholder="点击景点设终点" readonly /></div>
      <div class="btn-group"><button class="cat-btn primary" onclick="planDriveRoute()">🚗 规划</button><button class="cat-btn" onclick="clearDrivePoints()">✕</button></div>
    </div>
    <div id="routeTspPanel" style="display:none">
      <div class="btn-group"><button class="cat-btn primary" onclick="planTspRoute()">📋 规划</button><button class="cat-btn" onclick="clearTspList()">🗑️</button></div>
    </div>
    <div id="routeBusPanel" style="display:none">
      <div class="input-row"><input id="busStart" placeholder="点击设起点" readonly /><input id="busEnd" placeholder="点击设终点" readonly /></div>
      <div class="btn-group"><button class="cat-btn primary" onclick="queryBusRoute()">🚌 查询</button><button class="cat-btn" onclick="clearBusPoints()">✕</button></div>
    </div>
    <div class="result-box" id="routeResultList"></div>
  </div>

  <div class="panel-section">
    <div class="section-title">🆘 救援分析</div>
    <div class="btn-group">
      <button class="cat-btn danger" onclick="enableAccidentMode()">📍 标记</button>
      <button class="cat-btn primary" onclick="runBufferAnalysis()">📊 缓冲区</button>
      <button class="cat-btn warning" onclick="runOverlayAnalysis()">🔲 叠置</button>
      <button class="cat-btn" onclick="clearAnalysis()">🗑️</button>
    </div>
    <div class="result-box" id="analysisResultList"><div class="empty">标记事故点</div></div>
  </div>

  <div class="panel-section">
    <div class="section-title">🌤️ 天气预报</div>
    <div class="btn-group"><button class="cat-btn primary" onclick="refreshWeather()">🔄 刷新</button></div>
    <div class="result-box" id="weatherDetailList"></div>
  </div>
</div>

<div id="bottom-toolbar">
  <button class="tool-btn" onclick="if(map)map.zoomIn()">🔍 +</button>
  <button class="tool-btn" onclick="if(map)map.zoomOut()">🔍 -</button>
  <button class="tool-btn" onclick="if(map)map.setZoomAndCenter(13,[116.397,39.913])">⛰️ 全幅</button>
  <span class="divider"></span>
  <button class="tool-btn" onclick="enableMeasure('distance')">↔️ 距离</button>
  <button class="tool-btn" onclick="enableMeasure('area')">⬛ 面积</button>
  <button class="tool-btn" onclick="clearMeasure()">✕</button>
</div>

<div id="tip">💡 选择查询方式后在地图上操作</div>
<div id="status"><span class="dot">●</span> 已加载</div>

<div id="loginModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;justify-content:center;align-items:center;">
  <div style="background:#fff;border-radius:12px;padding:20px;width:320px;">
    <h3 style="font-size:16px;color:#1a3a6b;margin-bottom:12px;">登录</h3>
    <div class="btn-group" style="margin-bottom:10px;">
      <button class="cat-btn active" onclick="switchAuthTab('login')">登录</button>
      <button class="cat-btn" onclick="switchAuthTab('register')">注册</button>
    </div>
    <div id="loginForm">
      <div class="input-row"><input id="loginUsername" placeholder="用户名" /></div>
      <div class="input-row"><input id="loginPassword" type="password" placeholder="密码" /></div>
      <button class="cat-btn primary" onclick="login()" style="width:100%;justify-content:center;">登录</button>
      <p id="loginError" style="color:#e53935;font-size:11px;"></p>
    </div>
    <div id="registerForm" style="display:none;">
      <div class="input-row"><input id="regUsername" placeholder="用户名" /></div>
      <div class="input-row"><input id="regPassword" type="password" placeholder="密码" /></div>
      <button class="cat-btn success" onclick="register()" style="width:100%;justify-content:center;">注册</button>
      <p id="registerError" style="color:#e53935;font-size:11px;"></p>
    </div>
  </div>
</div>

<script>window._AMapSecurityConfig={securityJsCode:'8ce5324e4e2b6d2581059ba506e444fd'}</script>
<script src="https://webapi.amap.com/maps?v=2.0&key=9439ed4fbbcd52b4a8110ec0dc4b55dd&plugin=AMap.Scale,AMap.HawkEye,AMap.MouseTool"></script>
<script src="js/api.js?v=25"></script>
<script src="js/auth.js?v=25"></script>
<script src="js/map.js?v=25"></script>
<script src="js/query.js?v=25"></script>
<script src="js/scenic.js?v=25"></script>
<script src="js/route.js?v=25"></script>
<script src="js/analysis.js?v=25"></script>
<script src="js/weather.js?v=25"></script>
<script src="js/app.js?v=25"></script>
</body>
</html>'''

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print('New index.html written')
