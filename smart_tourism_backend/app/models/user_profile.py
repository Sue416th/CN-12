from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.common import Base, TimeStampedMixin


class UserProfile(Base, TimeStampedMixin):
    """
    用户画像模型 - 存储用户的多维度特征信息
    用于个性化推荐和行程规划
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)

    # 兴趣偏好 (JSON数组)
    interests = Column(JSON, nullable=True, default=list)

    # 预算等级: low/medium/high
    budget_level = Column(String(20), nullable=True, default="medium")

    # 旅行风格: relaxed/balanced/intensive
    travel_style = Column(String(20), nullable=True, default="balanced")

    # 出行人群: solo/couple/family/friends
    group_type = Column(String(20), nullable=True, default="solo")

    # 体能偏好: low/medium/high (每日步行时间)
    fitness_level = Column(String(20), nullable=True, default="medium")

    # 文化偏好权重 (JSON)
    # {"history": 0.8, "nature": 0.5, "food": 0.9, ...}
    cultural_preferences = Column(JSON, nullable=True, default=dict)

    # 偏好类别 (JSON数组)
    preferred_categories = Column(JSON, nullable=True, default=list)

    # 标签 (JSON数组)
    tags = Column(JSON, nullable=True, default=list)

    # 用户画像向量ID (用于向量检索)
    profile_vector_id = Column(String(64), nullable=True)

    # 扩展信息 (JSON)
    # 包含更多详细信息如: 饮食偏好, 住宿偏好, 交通偏好等
    extended_info = Column(JSON, nullable=True, default=dict)

    # 统计信息
    total_trips = Column(Integer, default=0)
    total_pois_visited = Column(Integer, default=0)
    last_active_at = Column(DateTime, nullable=True)

    # 备注
    notes = Column(Text, nullable=True)


class UserBehavior(Base, TimeStampedMixin):
    """
    用户行为记录 - 用于分析用户偏好
    """
    __tablename__ = "user_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)

    # 行为类型: view/visit/rate/bookmark/share
    behavior_type = Column(String(20), nullable=False, index=True)

    # 关联POI ID
    poi_id = Column(Integer, ForeignKey("pois.id"), nullable=True, index=True)

    # 关联行程ID
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=True, index=True)

    # 评分 (如果适用)
    rating = Column(Float, nullable=True)

    # 停留时长(分钟)
    duration = Column(Integer, nullable=True)

    # 扩展数据 (JSON)
    extra_data = Column(JSON, nullable=True, default=dict)
