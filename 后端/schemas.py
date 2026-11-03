"""
Pydantic 请求/响应模型定义
包含所有API接口的请求体和响应体校验模型
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 统一响应格式 ====================

class ResponseModel(BaseModel):
    """统一响应格式"""
    code: int = 200
    msg: str = "成功"
    data: Any = None


class PageResponseModel(BaseModel):
    """分页响应格式"""
    code: int = 200
    msg: str = "成功"
    data: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 10


# ==================== 用户模块 ====================

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户信息修改请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")


# ==================== 景点模块 ====================

class ScenicSpotCreate(BaseModel):
    """景点创建请求"""
    name: str = Field(..., max_length=100, description="景点名称")
    description: Optional[str] = Field(None, description="景点描述")
    address: Optional[str] = Field(None, max_length=255, description="地址")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    category: Optional[str] = Field(None, max_length=50, description="景点主分类: cultural/urban/natural")
    subcategory: Optional[str] = Field(None, max_length=50, description="景点子分类: museum/park/school/landmark/temple/street/palace/other")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    open_time: Optional[str] = Field(None, max_length=100, description="开放时间")
    ticket_price: Optional[str] = Field(None, max_length=50, description="门票价格")
    rating: Optional[float] = Field(None, ge=0, le=10, description="评分")


class ScenicSpotUpdate(BaseModel):
    """景点修改请求"""
    name: Optional[str] = Field(None, max_length=100, description="景点名称")
    description: Optional[str] = Field(None, description="景点描述")
    address: Optional[str] = Field(None, max_length=255, description="地址")
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    category: Optional[str] = Field(None, max_length=50, description="景点主分类")
    subcategory: Optional[str] = Field(None, max_length=50, description="景点子分类")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    open_time: Optional[str] = Field(None, max_length=100, description="开放时间")
    ticket_price: Optional[str] = Field(None, max_length=50, description="门票价格")
    rating: Optional[float] = Field(None, ge=0, le=10, description="评分")


# ==================== 空间查询模块 ====================

class PointQuery(BaseModel):
    """点加半径查询POI请求"""
    lat: float = Field(..., description="中心点纬度")
    lng: float = Field(..., description="中心点经度")
    radius: float = Field(500.0, ge=0, description="查询半径（米）")
    category: Optional[str] = Field(None, description="POI类别过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(500, ge=1, le=5000, description="每页条数")


class RectQuery(BaseModel):
    """矩形范围查询POI请求"""
    min_lat: float = Field(..., description="最小纬度")
    min_lng: float = Field(..., description="最小经度")
    max_lat: float = Field(..., description="最大纬度")
    max_lng: float = Field(..., description="最大经度")
    category: Optional[str] = Field(None, description="POI类别过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(500, ge=1, le=5000, description="每页条数")


class CircleQuery(BaseModel):
    """圆形范围查询POI请求"""
    lat: float = Field(..., description="圆心纬度")
    lng: float = Field(..., description="圆心经度")
    radius: float = Field(..., ge=0, description="半径（米）")
    category: Optional[str] = Field(None, description="POI类别过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(500, ge=1, le=5000, description="每页条数")


class PolygonQuery(BaseModel):
    """多边形范围查询POI请求"""
    coordinates: List[List[float]] = Field(..., description="多边形顶点坐标列表 [[lng,lat], ...]")
    category: Optional[str] = Field(None, description="POI类别过滤")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(500, ge=1, le=5000, description="每页条数")


# ==================== 路径规划模块 ====================

class DriveRouteRequest(BaseModel):
    """驾车路径规划请求"""
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    dest_lat: float = Field(..., description="终点纬度")
    dest_lng: float = Field(..., description="终点经度")


class TSPRequest(BaseModel):
    """旅行商分析请求"""
    origin_lat: float = Field(..., description="起点纬度")
    origin_lng: float = Field(..., description="起点经度")
    spots: List[Dict[str, Any]] = Field(..., description="景点坐标列表 [{\"lat\":..., \"lng\":..., \"name\":...}]")


class POICreate(BaseModel):
    """POI创建请求"""
    name: str = Field(..., max_length=100, description="POI名称")
    category: str = Field(..., max_length=50, description="POI类别")
    address: Optional[str] = Field('', max_length=255, description="地址")
    longitude: float = Field(..., description="经度")
    latitude: float = Field(..., description="纬度")
    phone: Optional[str] = Field('', max_length=20, description="电话")


class POIUpdate(BaseModel):
    """POI修改请求"""
    name: Optional[str] = Field(None, max_length=100, description="POI名称")
    category: Optional[str] = Field(None, max_length=50, description="POI类别")
    address: Optional[str] = Field(None, max_length=255, description="地址")
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    phone: Optional[str] = Field(None, max_length=20, description="电话")


class BusRouteRequest(BaseModel):
    """公交换乘查询请求"""
    start_lat: float = Field(..., description="起点纬度")
    start_lng: float = Field(..., description="起点经度")
    end_lat: float = Field(..., description="终点纬度")
    end_lng: float = Field(..., description="终点经度")


# ==================== 综合分析模块 ====================

class BufferAnalysisRequest(BaseModel):
    """缓冲区分析请求"""
    lat: float = Field(..., description="事故点纬度")
    lng: float = Field(..., description="事故点经度")
    radius: float = Field(1000.0, ge=0, description="缓冲区半径（米）")


class OverlayAnalysisRequest(BaseModel):
    """叠置分析请求"""
    lat: float = Field(..., description="事故点纬度")
    lng: float = Field(..., description="事故点经度")
