import os

js_dir = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\js"

# === weather.js ===
path = os.path.join(js_dir, "weather.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Add weather icon function
old0 = "function displayMainWeather(data) {"
if old0 in c:
    icon_func = """function getWeatherIcon(weather) {
    var map = {'晴':'☀️','多云':'⛅','阴':'☁️','小雨':'🌦️','中雨':'🌧️','大雨':'🌧️','暴雨':'🌊','雷阵雨':'⛈️','阵雨':'🌦️','小雪':'🌨️','中雪':'❄️','大雪':'❄️','雾':'🌫️','霾':'😷','扬沙':'🏜️','浮尘':'🌫️','晴间多云':'🌤️'};
    return map[weather] || '🌡️';
}

""" + old0
    c = c.replace(old0, icon_func)

# Update main weather display
old1 = '    var wicon = getWeatherIcon(weather.weather || \'\');\n    var html = \'<div class="weather-main">\' + wicon + \' \' + (weather.temperature || \'--\') + \'°C</div>\';\n    html += \'<div class="weather-desc">\' + (weather.weather || \'--\') + \' · \' + (weather.city || \'北京\') + \'</div>\';'
old1_old = "    let html = `\n        <div class=\"weather-main\">${weather.temperature || '--'}°C</div>\n        <div class=\"weather-desc\">${weather.weather || '--'} · ${weather.city || '北京'}</div>"
new1 = """    var wicon = getWeatherIcon(weather.weather || '');
    var html = '<div class="weather-main">' + wicon + ' ' + (weather.temperature || '--') + '°C</div>';
    html += '<div class="weather-desc">' + (weather.weather || '--') + ' · ' + (weather.city || '北京') + '</div>';"""

if old1_old in c:
    c = c.replace(old1_old, new1)
elif old1 in c:
    pass

# Update attractions weather display
old2 = "attractions.forEach(spot => {"
old2_old = """attractions.forEach(spot => {
        const weather = spot.weather || {};
        const temp = weather.temperature || '--';
        const weatherDesc = weather.weather || '--';

        html += `
            <div class=\"result-item\" onclick=\"flyTo(${spot.longitude}, ${spot.latitude}, 13)\">
                <h4>${spot.name}</h4>
                <p>
                    <span style=\"font-size:20px;font-weight:700;color:var(--primary);\">${temp}°C</span>
                    <span style=\"margin-left:8px;\">${weatherDesc}</span>
                </p>
                <p style=\"font-size:11px;color:var(--text-secondary);\">${spot.address || ''}</p>
            </div>`;
        });

        listEl.innerHTML = html;"""

new2 = """attractions.forEach(function(spot) {
        var wd = spot.weather || {};
        var temp = wd.temperature || '--';
        var desc = wd.weather || '--';
        var wicon = getWeatherIcon(desc);
        html += '<div class=\"result-item\" onclick=\"flyTo(' + spot.longitude + ',' + spot.latitude + ',13)\">';
        html += '<h4>' + spot.name + ' <span style=\"font-size:16px;\">' + wicon + '</span></h4>';
        html += '<p><span style=\"font-size:20px;font-weight:700;color:var(--primary);\">' + temp + '°C</span> <span style=\"margin-left:4px;font-size:13px;\">' + desc + '</span></p>';
        html += '<p style=\"font-size:11px;color:var(--text-secondary);\">' + (spot.address || '') + '</p></div>';
    });

    listEl.innerHTML = html;"""

c = c.replace(old2_old, new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('weather.js - icons added')

# === query.js === Add POI category icons to results
path = os.path.join(js_dir, "query.js")
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Update the results display to include icons
old_poi = "html += `<div class=\"result-item\" onclick=\"flyTo(${poi.longitude}, ${poi.latitude}, 15)\">\n                <h4>${getCategoryIcon(poi.category)} ${poi.name}</h4>"
new_poi = """html += '<div class=\"result-item\" onclick=\"flyTo(' + poi.longitude + ',' + poi.latitude + ',15)\">';
                html += '<h4>' + getCategoryIcon(poi.category) + ' ' + poi.name + '</h4>';"""

c = c.replace(old_poi, new_poi)

# Update category icon function
old_icon = "function getCategoryIcon(category) {\n    const icons = { 'hospital': '🏥', 'school': '🏫', 'park': '🌳' };\n    return icons[category] || '📍';\n}"
new_icon = """function getCategoryIcon(category) {
    const icons = {'hospital':'🏥','school':'🏫','park':'🌳','mall':'🛍️','bank':'🏦','restaurant':'🍜','hotel':'🏨','gas_station':'⛽','library':'📚','stadium':'🏟️','theater':'🎭','police':'👮','fire':'🚒'};
    return icons[category] || '📍';
}"""
c = c.replace(old_icon, new_icon)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('query.js - icons updated')

# === CSS === Add info window style
css_path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\css\style.css"
with open(css_path, 'r', encoding='utf-8') as f:
    c = f.read()

# Make sure info window doesn't overflow
old_css = ".scenic-info-window {"
new_css = ".scenic-info-window { overflow-y: auto; max-height: 350px;"
if old_css in c:
    c = c.replace(old_css, new_css)

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(c)
print('CSS - info window max-height added')

print('All done!')
