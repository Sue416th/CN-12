from sqlalchemy import Column, Integer, String, Float, Text, Boolean, JSON
from app.models.common import Base, TimeStampedMixin


class POI(Base, TimeStampedMixin):
    """
    Point of Interest (景点/兴趣点) 完整信息模型。
    包含位置、评分、价格、开放时间等详细信息，支持智能行程规划。
    """

    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    city = Column(String(64), nullable=True, index=True)
    district = Column(String(64), nullable=True)
    category = Column(String(64), nullable=True, index=True)
    sub_category = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    address = Column(String(256), nullable=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    rating = Column(Float, nullable=True, default=0.0)
    review_count = Column(Integer, nullable=True, default=0)
    price_level = Column(Integer, nullable=True, default=1)
    estimated_duration = Column(Integer, nullable=True, default=120)
    opening_hours = Column(JSON, nullable=True)
    closed_days = Column(JSON, nullable=True)
    ticket_info = Column(String(256), nullable=True)
    booking_required = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)
    images = Column(JSON, nullable=True)
    highlight = Column(Text, nullable=True)
    best_season = Column(String(128), nullable=True)
    recommended_visit_duration = Column(Integer, nullable=True, default=120)
    is_accessible = Column(Boolean, default=True)
    parking_available = Column(Boolean, default=False)
    official_website = Column(String(256), nullable=True)
    phone = Column(String(32), nullable=True)
