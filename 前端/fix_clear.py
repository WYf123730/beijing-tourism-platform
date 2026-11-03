import os

js_path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js\analysis.js"

with open(js_path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add buffer circle tracking in displayBufferResult
old1 = '    // 清除旧缓冲区'
if old1 not in c:
    old1 = '    // 绘制缓冲区（圆形）\n    const circle = new AMap.Circle({'
    new1 = '    // 清除旧缓冲区\n    if (window._bufferCircle) { map.remove(window._bufferCircle); window._bufferCircle = null; }\n    // 绘制缓冲区（圆形）\n    const circle = new AMap.Circle({'
    c = c.replace(old1, new1)

# 2. Track circle after map.add
old2 = '    map.add(circle);'
new2 = '    map.add(circle); window._bufferCircle = circle;'
c = c.replace(old2, new2)

# 3. Update clearAnalysis to remove buffer circle
old3 = '''function clearAnalysis() {
    accidentPoint = null;
    if (accidentMarker) { map.remove(accidentMarker); accidentMarker = null; }
    clearOverlays();
    clearPolylines(routePolylines);
    document.getElementById('accidentPoint').value = '';
    document.getElementById('analysisResultList').innerHTML = '<p class="hint">点击地图设置事故点后进行分析</p>';
    showTip('已清除分析结果', 'info');
}'''

new3 = '''function clearAnalysis() {
    accidentPoint = null;
    if (accidentMarker) { map.remove(accidentMarker); accidentMarker = null; }
    if (window._bufferCircle) { map.remove(window._bufferCircle); window._bufferCircle = null; }
    clearOverlays();
    clearPolylines(routePolylines);
    document.getElementById('accidentPoint').value = '';
    document.getElementById('analysisResultList').innerHTML = '<p class="hint">点击地图设置事故点后进行分析</p>';
    showTip('已清除分析结果（含地图标注）', 'info');
}'''

c = c.replace(old3, new3)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
