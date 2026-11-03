"""
数据模型定义
包含全部7张表的 SQLAlchemy ORM 模型
"""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped

from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = Column(String(50), unique=True, nullable=False, comment="用户名")
    password: Mapped[str] = Column(String(255), nullable=False, comment="密码（bcrypt加密）")
    nickname: Mapped[str] = Column(String(50), default="", comment="昵称")
    email: Mapped[str] = Column(String(100), default="", comment="电子邮箱")
    phone: Mapped[str] = Column(String(20), default="", comment="手机号")
    avatar: Mapped[str] = Column(String(500), default="", comment="头像URL")
    role: Mapped[str] = Column(String(20), default="user", comment="角色: user(普通用户)/admin(管理员)")

    # 软删除 & 时间戳（增强设计）
    is_deleted: Mapped[bool] = Column(Boolean, default=False, comment="软删除标志")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname or "",
            "email": self.email or "",
            "phone": self.phone or "",
            "avatar": self.avatar or "",
            "role": self.role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class Scenic(Base):
    """景点表"""
    __tablename__ = "scenic"
    __table_args__ = {"comment": "景点表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="景点ID")
    name: Mapped[str] = Column(String(100), nullable=False, comment="景点名称")
    description: Mapped[str] = Column(Text, default="", comment="景点描述")
    address: Mapped[str] = Column(String(255), default="", comment="详细地址")
    longitude: Mapped[float] = Column(Float, nullable=False, comment="经度(GCJ-02)")
    latitude: Mapped[float] = Column(Float, nullable=False, comment="纬度(GCJ-02)")
    category: Mapped[str] = Column(String(50), default="", comment="景点主分类: cultural/urban/natural")
    subcategory: Mapped[str] = Column(String(50), default="", comment="景点子分类: museum/park/school/landmark/temple/street/palace/other")
    images: Mapped[str] = Column(Text, default="[]", comment="图片URL数组(JSON字符串)")
    phone: Mapped[str] = Column(String(20), default="", comment="联系电话")
    open_time: Mapped[str] = Column(String(100), default="", comment="开放时间")
    ticket_price: Mapped[str] = Column(String(50), default="", comment="门票价格描述")
    rating: Mapped[float] = Column(Float, default=0.0, comment="评分")

    # 增强设计
    is_deleted: Mapped[bool] = Column(Boolean, default=False, comment="软删除标志")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def to_dict(self) -> dict:
        try:
            img_list = json.loads(self.images) if self.images else []
        except (json.JSONDecodeError, TypeError):
            img_list = []
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "address": self.address or "",
            "longitude": self.longitude,
            "latitude": self.latitude,
            "category": self.category or "",
            "subcategory": self.subcategory or "",
            "images": img_list,
            "phone": self.phone or "",
            "open_time": self.open_time or "",
            "ticket_price": self.ticket_price or "",
            "rating": self.rating or 0,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class POI(Base):
    """兴趣点表（医院、学校、公园等公众服务单位）"""
    __tablename__ = "pois"
    __table_args__ = {"comment": "兴趣点表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="POI ID")
    name: Mapped[str] = Column(String(100), nullable=False, comment="POI名称")
    category: Mapped[str] = Column(String(50), nullable=False, comment="分类: hospital/school/park/其他")
    address: Mapped[str] = Column(String(255), default="", comment="地址")
    longitude: Mapped[float] = Column(Float, nullable=False, comment="经度")
    latitude: Mapped[float] = Column(Float, nullable=False, comment="纬度")
    phone: Mapped[str] = Column(String(20), default="", comment="联系电话")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now, comment="创建时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "address": self.address or "",
            "longitude": self.longitude,
            "latitude": self.latitude,
            "phone": self.phone or "",
        }


class BusRoute(Base):
    """公交线路表"""
    __tablename__ = "bus_routes"
    __table_args__ = {"comment": "公交线路表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="线路ID")
    route_name: Mapped[str] = Column(String(100), nullable=False, comment="线路名称")
    start_station: Mapped[str] = Column(String(100), nullable=False, comment="始发站")
    end_station: Mapped[str] = Column(String(100), nullable=False, comment="终点站")
    stations: Mapped[str] = Column(JSON, nullable=False, comment="途经站点列表（JSON数组）")
    station_coords: Mapped[str] = Column(JSON, nullable=False, comment="站点坐标列表（JSON数组）")
    direction: Mapped[str] = Column(String(20), default="双向", comment="运行方向")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "route_name": self.route_name,
            "start_station": self.start_station,
            "end_station": self.end_station,
            "stations": self.stations if isinstance(self.stations, list) else [],
            "station_coords": self.station_coords if isinstance(self.station_coords, list) else [],
            "direction": self.direction,
        }


class BusStation(Base):
    """公交站点表"""
    __tablename__ = "bus_stations"
    __table_args__ = {"comment": "公交站点表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="站点ID")
    name: Mapped[str] = Column(String(100), nullable=False, comment="站点名称")
    longitude: Mapped[float] = Column(Float, nullable=False, comment="经度")
    latitude: Mapped[float] = Column(Float, nullable=False, comment="纬度")
    routes: Mapped[str] = Column(JSON, default=[], comment="途经线路列表")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "routes": self.routes if isinstance(self.routes, list) else [],
        }


class RescueResource(Base):
    """救援资源表"""
    __tablename__ = "rescue_resources"
    __table_args__ = {"comment": "救援资源表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="资源ID")
    name: Mapped[str] = Column(String(100), nullable=False, comment="资源名称")
    type: Mapped[str] = Column(String(50), default="医院", comment="资源类型: 医院/消防/警察局等")
    address: Mapped[str] = Column(String(255), default="", comment="地址")
    longitude: Mapped[float] = Column(Float, nullable=False, comment="经度")
    latitude: Mapped[float] = Column(Float, nullable=False, comment="纬度")
    phone: Mapped[str] = Column(String(20), default="", comment="联系电话")
    capacity: Mapped[str] = Column(String(100), default="", comment="容量/描述")
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now, comment="创建时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "address": self.address or "",
            "longitude": self.longitude,
            "latitude": self.latitude,
            "phone": self.phone or "",
            "capacity": self.capacity or "",
        }


class WeatherCache(Base):
    """天气缓存表"""
    __tablename__ = "weather_cache"
    __table_args__ = {"comment": "天气缓存表"}

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="缓存ID")
    city: Mapped[str] = Column(String(50), nullable=False, comment="城市名称")
    adcode: Mapped[str] = Column(String(20), nullable=False, comment="城市编码")
    weather_data: Mapped[str] = Column(JSON, nullable=False, comment="天气数据（JSON）")
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "city": self.city,
            "adcode": self.adcode,
            "weather_data": self.weather_data if isinstance(self.weather_data, dict) else {},
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
