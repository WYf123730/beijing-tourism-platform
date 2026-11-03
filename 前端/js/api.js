/**
 * API 调用封装模块
 * 封装所有后端 API 调用，统一处理请求和响应
 */
const API_BASE = '/api';  // 相对路径，适配公网和本地访问

// ==================== HTTP 请求工具 ====================

function getToken() {
    return localStorage.getItem('token');
}

function getAuthHeaders() {
    const token = getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

async function apiGet(path, params = {}) {
    let url = `${API_BASE}${path}`;
    const query = Object.keys(params)
        .filter(k => params[k] !== undefined && params[k] !== null)
        .map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
        .join('&');
    if (query) url += '?' + query;

    const resp = await fetch(url, {
        method: 'GET',
        headers: getAuthHeaders(),
    });
    return resp.json();
}

async function apiPost(path, data = {}) {
    const resp = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
    });
    return resp.json();
}

async function apiPut(path, data = {}) {
    const resp = await fetch(`${API_BASE}${path}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
    });
    return resp.json();
}

async function apiDelete(path) {
    const resp = await fetch(`${API_BASE}${path}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
    });
    return resp.json();
}

// ==================== 用户 API ====================

async function apiRegister(data) {
    return apiPost('/user/register', data);
}

async function apiLogin(data) {
    return apiPost('/user/login', data);
}

async function apiGetUserInfo() {
    return apiGet('/user/info');
}

async function apiUpdateUserInfo(data) {
    return apiPut('/user/info', data);
}

// ==================== 景点 API ====================

async function apiGetScenicList(params = {}) {
    return apiGet('/scenic/', params);
}

async function apiGetScenicDetail(id) {
    return apiGet(`/scenic/${id}`);
}

async function apiSearchScenic(params) {
    return apiGet('/scenic/search/list', params);
}

async function apiNearbyScenic(params) {
    return apiGet('/scenic/nearby/list', params);
}

async function apiCreateScenic(data) {
    return apiPost('/scenic/', data);
}

async function apiUpdateScenic(id, data) {
    return apiPut(`/scenic/${id}`, data);
}

async function apiDeleteScenic(id) {
    return apiDelete(`/scenic/${id}`);
}

// ==================== POI 空间查询 API ====================

async function apiGetPoiCategories(params) {
    return apiGet('/poi/categories', params);
}

async function apiQueryPoiPoint(data) {
    return apiPost('/poi/query/point', data);
}

async function apiQueryPoiRect(data) {
    return apiPost('/poi/query/rect', data);
}

async function apiQueryPoiCircle(data) {
    return apiPost('/poi/query/circle', data);
}

async function apiQueryPoiPolygon(data) {
    return apiPost('/poi/query/polygon', data);
}

// ==================== 路径规划 API ====================

async function apiPlanDrive(data) {
    return apiPost('/route/drive', data);
}

async function apiPlanTsp(data) {
    return apiPost('/route/tsp', data);
}

async function apiQueryBus(data) {
    return apiPost('/route/bus', data);
}

async function apiGetBusStations() {
    return apiGet('/route/bus/stations');
}

// ==================== 综合分析 API ====================

async function apiBufferAnalysis(data) {
    return apiPost('/analysis/buffer', data);
}

async function apiOverlayAnalysis(data) {
    return apiPost('/analysis/overlay', data);
}

// ==================== 天气 API ====================

async function apiGetCityWeather(city) {
    return apiGet(`/weather/${encodeURIComponent(city)}`);
}

async function apiCreatePoi(data) {
    return apiPost('/poi/create', data);
}
async function apiUpdatePoi(id, data) {
    return apiPut('/poi/update/' + id, data);
}
async function apiDeletePoi(id) {
    return apiDelete('/poi/delete/' + id);
}
async function apiGetPoiDetail(id) {
    return apiGet('/poi/detail/' + id);
}

async function apiGetAttractionsWeather() {
    return apiGet('/weather/attractions/all');
}
