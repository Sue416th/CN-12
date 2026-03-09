from typing import Any, List, Optional

from pydantic import BaseModel


class POIResponse(BaseModel):
    id: int
    name: str
    city: Optional[str] = None
    district: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_level: Optional[int] = None
    estimated_duration: Optional[int] = None
    opening_hours: Optional[Any] = None
    ticket_info: Optional[str] = None
    booking_required: Optional[bool] = None
    tags: Optional[List[str]] = None
    highlight: Optional[str] = None
    best_season: Optional[str] = None
    recommended_visit_duration: Optional[int] = None
    is_accessible: Optional[bool] = None
    parking_available: Optional[bool] = None

    class Config:
        from_attributes = True
