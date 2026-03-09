from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.common import Base, TimeStampedMixin


class Itinerary(Base, TimeStampedMixin):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String(128), nullable=True)
    city = Column(String(64), nullable=True)

    items = relationship("ItineraryItem", back_populates="itinerary", cascade="all, delete-orphan")


class ItineraryItem(Base, TimeStampedMixin):
    __tablename__ = "itinerary_items"

    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id", ondelete="CASCADE"), nullable=False, index=True)
    poi_id = Column(Integer, ForeignKey("pois.id"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    note = Column(String(256), nullable=True)

    itinerary = relationship("Itinerary", back_populates="items")
    poi = relationship("POI")

