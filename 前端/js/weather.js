/**
 * 天气预报模块
 * 展示各景区天气信息，从后端API获取
 */

let weatherData = null;

// ==================== 加载天气 ====================

async function loadWeather() {
    const displayEl = document.getElementById('weatherDisplay');

    try {
        // 先加载北京总体天气作为主显示
        const result = await apiGetCityWeather('北京');
        if (result.code === 200) {
            displayMainWeather(result.data);
        } else {
            displayEl.innerHTML = '<p>正在获取北京天气...</p>';
        }

        // 同时加载各景区详细天气
        const attractionsResult = await apiGetAttractionsWeather();
        if (attractionsResult.code === 200) {
            displayAttractionsWeather(attractionsResult.data.attractions);
            // 也在地图上添加天气标记
            addWeatherMarkersToMap(attractionsResult.data.attractions);
        }

    } catch (e) {
        displayEl.innerHTML = '<p class="hint">获取天气数据失败</p>';
        showTip('天气数据获取失败', 'error');
    }
}

// ==================== 主要天气展示 ====================

function getWeatherIcon(weather) {
    var map = {'晴':'☀️','多云':'⛅','阴':'☁️','小雨':'🌦️','中雨':'🌧️','大雨':'🌧️','暴雨':'🌊','雷阵雨':'⛈️','阵雨':'🌦️','小雪':'🌨️','中雪':'❄️','大雪':'❄️','雾':'🌫️','霾':'😷','扬沙':'🏜️','浮尘':'🌫️','晴间多云':'🌤️'};
    return map[weather] || '🌡️';
}

function displayMainWeather(data) {
    const displayEl = document.getElementById('weatherDisplay');
    const weather = data.weather_data || {};
    var source = data.source || 'realtime';

    var wicon = getWeatherIcon(weather.weather || '');
    var html = '<div class="weather-main">' + wicon + ' ' + (weather.temperature || '--') + '°C</div>';
    html += '<div class="weather-desc">' + (weather.weather || '--') + ' · ' + (weather.city || '北京') + '</div>';
    html += '<div class="weather-detail">';
    html += '<span>💨 ' + (weather.winddirection || '--') + '风 ' + (weather.windpower || '--') + '级</span>';
    html += '<span>💧 ' + (weather.humidity || '--') + '% 湿度</span>';
    html += '</div>';
    html += '<div style="font-size:11px;color:var(--text-secondary);margin-top:8px;">';
    html += '⏱️ ' + (weather.reporttime || data.updated_at || '--');
    html += ' <span style="background:#34a853;color:#fff;padding:1px 6px;border-radius:3px;font-size:10px;margin-left:4px;">实时</span>';
    html += '</div>';

    if (weather.forecast && weather.forecast.length > 0) {
        html += '<div style="margin-top:12px;"><h4>📅 天气预报</h4><div style="display:flex;gap:8px;overflow-x:auto;padding:8px 0;">';
        weather.forecast.forEach(function(day) {
            html += '<div style="min-width:80px;text-align:center;background:rgba(255,255,255,0.6);border-radius:6px;padding:6px;">';
            html += '<div style="font-size:12px;font-weight:600;">' + (day.date || '--') + '</div>';
            html += '<div style="font-size:11px;">' + (day.dayweather || '--') + '</div>';
            html += '<div style="font-size:13px;">' + (day.daytemp || '--') + '°</div>';
            html += '</div>';
        });
        html += '</div></div>';
    }

    displayEl.innerHTML = html;
}

// ==================== 景区天气展示 ====================

function displayAttractionsWeather(attractions) {
    const listEl = document.getElementById('weatherDetailList');

    if (!attractions || attractions.length === 0) {
        listEl.innerHTML = '<p class="hint">暂无景区天气数据</p>';
        return;
    }

    var html = '<h4>🏞️ 景区天气 <span style="font-size:11px;background:#34a853;color:#fff;padding:1px 6px;border-radius:3px;font-weight:normal;margin-left:4px;">实时</span></h4>';

    attractions.forEach(function(spot) {
        var wd = spot.weather || {};
        var temp = wd.temperature || '--';
        var desc = wd.weather || '--';
        var wicon = getWeatherIcon(desc);
        var district = spot.district || '';
        var reportTime = wd.reporttime || '';
        html += '<div class="result-item" onclick="flyTo(' + spot.longitude + ',' + spot.latitude + ',13)">';
        html += '<h4>' + spot.name + ' <span style="font-size:16px;">' + wicon + '</span></h4>';
        html += '<p><span style="font-size:20px;font-weight:700;color:var(--primary);">' + temp + '°C</span> <span style="margin-left:4px;font-size:13px;">' + desc + '</span>';
        if (district) html += ' <span style="font-size:11px;color:#999;">(' + district + ')</span>';
        html += '</p>';
        html += '<p style="font-size:11px;color:var(--text-secondary);">' + (spot.address || '') + '</p>';
        if (reportTime) html += '<p style="font-size:10px;color:#999;">⏱️ ' + reportTime + '</p>';
        html += '</div>';
    });

    listEl.innerHTML = html;
}

// ==================== 刷新天气 ====================

async function refreshWeather() {
    showTip('正在刷新天气数据...', 'info');
    await loadWeather();
    showTip('天气数据已刷新', 'success');
}

// ==================== 在地图上添加天气标记 ====================

function addWeatherMarkersToMap(attractions) {
    if (!attractions) return;

    attractions.forEach(function(spot) {
        var weather = spot.weather || {};
        var temp = weather.temperature || '--';
        var desc = weather.weather || '';
        var district = spot.district || '';

        var marker = new AMap.Marker({
            position: [spot.longitude, spot.latitude],
            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
            anchor: 'bottom-center',
            label: {
                content: '<div style="background:rgba(255,255,255,0.92);padding:3px 10px;border-radius:16px;border:2px solid #1a73e8;font-size:12px;font-weight:600;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,0.12);">' +
                    spot.name + ' ' + temp + '°C ' + desc +
                    (district ? ' <span style="font-size:10px;color:#888;">(' + district + ')</span>' : '') +
                '</div>',
                offset: new AMap.Pixel(-70, -42),
            },
        });
        marker.on('click', function() {
            showInfoWindow(
                '<div style="padding:8px;max-width:200px;">' +
                '<h4 style="margin:0 0 4px;">' + spot.name + '</h4>' +
                '<p style="margin:2px 0;font-size:13px;">🌡️ ' + temp + '°C ' + desc + '</p>' +
                (district ? '<p style="margin:2px 0;font-size:12px;color:#666;">\u{1F4CD} ' + district + '</p>' : '') +
                '</div>',
                [spot.longitude, spot.latitude]
            );
        });
        map.add(marker);
        weatherMarkers.push(marker);
    });
}
