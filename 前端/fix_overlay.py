import os

js_path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js\analysis.js"

with open(js_path, 'r', encoding='utf-8') as f:
    c = f.read()

old = """    // 显示结果
    let html = `<h4>🔲 叠置分析结果</h4>`;
    html += `<div class=\"result-item\">
        <p><strong>事故点:</strong> (${data.accident_point.lng.toFixed(4)}, ${data.accident_point.lat.toFixed(4)})</p>
    </div>`;

    if (data.overlapped_zones && data.overlapped_zones.length > 0) {
        html += `<h4>覆盖的区域 (${data.zones_count}个)</h4>`;
        data.overlapped_zones.forEach(zone => {
            html += `<div class=\"result-item\" style=\"padding:6px 10px;\">
                <p><strong>${zone.name}</strong></p>
                <p>${zone.description || ''}</p>
                <p>类型: ${zone.type || '未分类'}</p>
            </div>`;
        });
    } else {
        html += `<div class=\"result-item\"><p>事故点未落入任何预设区域</p></div>`;
    }

    html += `<h4>附近救援资源 (${data.resources_count}个)</h4>`;
    data.nearby_resources.forEach(res => {
        html += `<div class=\"result-item\" style=\"padding:6px 10px;font-size:12px;\">
            <p><strong>${res.name}</strong> <span class=\"distance\">${res.distance}m</span></p>
            <p>${res.type} | ${res.phone || '无电话'}</p>
        </div>`;
    });

    listEl.innerHTML = html;
    showTip('叠置分析完成', 'success');
}"""

new = """    // 显示结果
    var html = '<h4>🔲 叠置分析结果</h4>';
    html += '<div class=\"result-item\">';
    html += '<p><strong>事故点:</strong> (' + data.accident_point.lng.toFixed(4) + ', ' + data.accident_point.lat.toFixed(4) + ')</p>';
    html += '</div>';

    html += '<h4>覆盖的区域 (' + data.zones_count + '个)</h4>';
    if (data.overlapped_zones && data.overlapped_zones.length > 0) {
        data.overlapped_zones.forEach(function(zone) {
            html += '<div class=\"result-item\" style=\"padding:6px 10px;\">';
            html += '<p><strong>' + zone.name + '</strong></p>';
            html += '<p>' + (zone.description || '') + '</p>';
            html += '<p>类型: ' + (zone.type || '未分类') + '</p></div>';
        });
    } else {
        html += '<div class=\"result-item\"><p>事故点不在预设区域内，但附近仍有救援资源:</p></div>';
    }

    html += '<h4>附近救援资源 (' + data.resources_count + '个)</h4>';
    if (data.nearby_resources && data.nearby_resources.length > 0) {
        data.nearby_resources.forEach(function(res) {
            html += '<div class=\"result-item\" style=\"padding:6px 10px;font-size:12px;\" onclick=\"flyTo(' + res.longitude + ',' + res.latitude + ',16)\">';
            html += '<p><strong>' + res.name + '</strong> <span class=\"distance\">' + res.distance + 'm</span></p>';
            html += '<p>' + res.type + ' | ' + (res.phone || '无电话') + '</p></div>';
        });
    } else {
        html += '<div class=\"result-item\"><p>附近暂无救援资源数据</p></div>';
    }

    listEl.innerHTML = html;
    showTip('叠置分析完成', 'success');
}"""

c = c.replace(old, new)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(c)
print('Overlay display fixed')
