from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class UserProfileBase(BaseModel):
    """User profile base schema"""
    interests: Optional[List[str]] = None
    budget_level: Optional[str] = "medium"
    travel_style: Optional[str] = "balanced"
    group_type: Optional[str] = "solo"
    fitness_level: Optional[str] = "medium"
    cultural_preferences: Optional[Dict[str, float]] = None
    preferred_categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class UserProfileCreate(UserProfileBase):
    """Create user profile"""
    user_id: int


class UserProfileUpdate(BaseModel):
    """Update user profile - all fields optional"""
    interests: Optional[List[str]] = None
    budget_level: Optional[str] = None
    travel_style: Optional[str] = None
    group_type: Optional[str] = None
    fitness_level: Optional[str] = None
    cultural_preferences: Optional[Dict[str, float]] = None
    preferred_categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    extended_info: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    """User profile response"""
    id: int
    user_id: int
    profile_vector_id: Optional[str] = None
    extended_info: Optional[Dict[str, Any]] = None
    total_trips: int = 0
    total_pois_visited: int = 0
    last_active_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class UserBehaviorBase(BaseModel):
    """User behavior base schema"""
    behavior_type: str
    poi_id: Optional[int] = None
    itinerary_id: Optional[int] = None
    rating: Optional[float] = None
    duration: Optional[int] = None


class UserBehaviorCreate(UserBehaviorBase):
    """Create user behavior"""
    user_id: int


class UserBehaviorResponse(UserBehaviorBase):
    """User behavior response"""
    id: int
    user_id: int
    extra_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileWithStats(UserProfileResponse):
    """User profile with statistics"""
    recent_behaviors: Optional[List[UserBehaviorResponse]] = None
    top_visited_pois: Optional[List[Dict[str, Any]]] = None
