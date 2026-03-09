from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ItineraryItem(BaseModel):
    poi_id: int
    poi_name: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    start_time: datetime
    end_time: datetime
    note: Optional[str] = None
    culture_info: Optional[Dict[str, Any]] = None
    weather_alert: Optional[str] = None

    class Config:
        from_attributes = True


class ItineraryCreateRequest(BaseModel):
    user_id: int = 1
    city: str = "Hangzhou"
    start_date: datetime
    end_date: datetime
    budget_level: str = "medium"
    interests: List[str] = []
    travel_style: str = "balanced"
    group_type: str = "solo"


class ItineraryResponse(BaseModel):
    itinerary_id: int
    user_id: int
    name: Optional[str] = None
    city: Optional[str] = None
    days: Optional[int] = None
    budget_level: Optional[str] = None
    interests: Optional[List[str]] = None
    start_date: Optional[str] = None
    weather_info: Optional[Dict[str, Any]] = None
    weather_advice: Optional[List[str]] = None
    items: List[ItineraryItem]

    class Config:
        from_attributes = True


class ItineraryListItem(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    city: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ItineraryDetailResponse(BaseModel):
    itinerary_id: int
    user_id: int
    name: Optional[str] = None
    city: Optional[str] = None
    weather_info: Optional[Dict[str, Any]] = None
    weather_advice: Optional[List[str]] = None
    items: List[ItineraryItem]

    class Config:
        from_attributes = True
