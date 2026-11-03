import os

js_dir = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js"
path = os.path.join(js_dir, "route.js")

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Update planTspRoute
old = "async function planTspRoute() {"
if old in c:
    idx = c.index(old)
    end_idx = c.index("}", idx) + 1
    old_func = c[idx:end_idx]
else:
    old_func = None

# Find the current planTspRoute function
import re
match = re.search(r'async function planTspRoute\(\) \{.*?\n\}', c, re.DOTALL)
if match:
    old_func = match.group()
    new_func = """async function planTspRoute() {
    if (tspSpots.length < 2) {
        showTip('请至少添加2个景点', 'warning');
        return;
    }

    try {
        showTip('正在进行旅行商分析...', 'info');
        const result = await apiPlanTsp({
            origin_lat: 39.913,
            origin_lng: 116.397,
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
                showTip('正在获取第' + (i+1) + '段驾车路线...', 'info');
                try {
                    var driveResult = await apiPlanDrive({
                        origin_lat: prevLat,
                        origin_lng: prevLng,
                        dest_lat: spot.latitude,
                        dest_lng: spot.longitude,
                    });
                    if (driveResult.code === 200 && driveResult.data && driveResult.data.paths && driveResult.data.paths.length > 0) {
                        allSegments.push({ from: prevName, to: spot.name, path: driveResult.data.paths[0] });
                    } else {
                        allSegments.push({ from: prevName, to: spot.name, path: null });
                    }
                } catch(e) {
                    allSegments.push({ from: prevName, to: spot.name, path: null });
                }
                prevLat = spot.latitude;
                prevLng = spot.longitude;
                prevName = spot.name;
            }
            displayTspResult(data, allSegments);
        } else {
            showTip(result.msg || '分析失败', 'error');
        }
    } catch (e) {
        showTip('网络错误', 'error');
    }
}"""
    c = c.replace(old_func, new_func)
    print("planTspRoute updated")
else:
    print("planTspRoute NOT found")

# Update displayTspResult to show detailed driving steps per segment
old_display = "function displayTspResult(data, allSegments) {"
if old_display not in c:
    old_display = "function displayTspResult(data) {"

# Find the segment display code
old_seg_loop = """    data.ordered_spots.forEach(function(item, idx) {
        var seg = segmentData[idx];
        var distKm = (seg.segDist / 1000).toFixed(1);
        html += '<div class=\"result-item\" style=\"padding:8px 10px;border-left:3px solid #34a853;margin:4px 0;\">';
        html += '<p><strong style=\"color:#34a853;\">⬇ 第' + (idx + 1) + '站</strong> → ' + item.name + '</p>';
        html += '<p style=\"font-size:12px;color:var(--text-secondary);margin-top:4px;\">';
        html += '📍 坐标: (' + item.longitude.toFixed(4) + ', ' + item.latitude.toFixed(4) + ')<br>';
        html += '🛣️ 距上一站: ' + distKm + ' km</p></div>';
    });"""

new_seg_loop = """    data.ordered_spots.forEach(function(item, idx) {
        var seg = segmentData[idx];
        var distKm = (seg.segDist / 1000).toFixed(1);
        var segInfo = (typeof allSegments !== 'undefined' && allSegments && allSegments[idx]) ? allSegments[idx] : null;

        html += '<div class=\"result-item\" style=\"padding:8px 10px;border-left:3px solid #34a853;margin:4px 0;\">';
        html += '<p><strong style=\"color:#34a853;\">⬇ 第' + (idx + 1) + '站</strong> → ' + item.name + '</p>';
        html += '<p style=\"font-size:12px;color:var(--text-secondary);margin-top:4px;\">';
        html += '📍 (' + item.longitude.toFixed(4) + ', ' + item.latitude.toFixed(4) + ') ';
        html += '🛣️ ' + distKm + ' km</p>';

        if (segInfo && segInfo.path) {
            var p = segInfo.path;
            html += '<p style=\"font-size:12px;color:#1a73e8;\">🚗 ' + (p.distance/1000).toFixed(1) + 'km \xb7 ' + Math.round(p.duration/60) + '分钟 \xb7 ' + (p.steps ? p.steps.length : 0) + '步</p>';
            if (p.steps && p.steps.length > 0) {
                html += '<div style=\"font-size:11px;color:var(--text-secondary);padding-left:8px;border-left:2px solid #ddd;margin-top:4px;\">';
                var maxSteps = Math.min(p.steps.length, 5);
                for (var s = 0; s < maxSteps; s++) {
                    html += '<div style=\"margin:2px 0;\">' + (s+1) + '. ' + p.steps[s].instruction + '</div>';
                }
                if (p.steps.length > 5) html += '<div>... 共' + p.steps.length + '步</div>';
                html += '</div>';
            }
        } else if (segInfo) {
            html += '<p style=\"font-size:12px;color:var(--danger);\">⚠️ 驾车路线获取失败</p>';
        }
        html += '</div>';
    });"""

if old_seg_loop in c:
    c = c.replace(old_seg_loop, new_seg_loop)
    print("Segment details updated")
else:
    print("Segment loop NOT found, checking...")
    # Try to find alternative pattern
    for line in c.split('\n'):
        if 'distKm' in line and 'item.name' in line:
            print("Found:", line.strip()[:80])

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
