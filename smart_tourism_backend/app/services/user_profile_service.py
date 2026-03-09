from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user_profile import UserProfile, UserBehavior


class UserProfileService:
    """User profile service - manage user profiles and behaviors"""

    def __init__(self, db: Session):
        self.db = db

    # Profile CRUD operations

    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by user_id"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def create_profile(self, user_id: int, data: Dict[str, Any]) -> UserProfile:
        """Create new user profile"""
        # Remove user_id from data if present to avoid duplicate
        data_copy = {k: v for k, v in data.items() if k != "user_id"}
        profile = UserProfile(user_id=user_id, **data_copy)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_profile(self, user_id: int, data: Dict[str, Any]) -> Optional[UserProfile]:
        """Update user profile"""
        profile = self.get_profile(user_id)

        # Filter out non-DB fields
        db_fields = [
            "interests", "budget_level", "travel_style", "group_type",
            "fitness_level", "cultural_preferences", "preferred_categories", "tags"
        ]
        filtered_data = {k: v for k, v in data.items() if k in db_fields}

        if not profile:
            return self.create_profile(user_id, filtered_data)

        # Don't update user_id - keep existing value
        for key, value in filtered_data.items():
            if key != "user_id" and hasattr(profile, key):
                setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def delete_profile(self, user_id: int) -> bool:
        """Delete user profile"""
        profile = self.get_profile(user_id)
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        return False

    # Behavior CRUD operations

    def add_behavior(self, user_id: int, behavior_type: str, poi_id: Optional[int] = None,
                    itinerary_id: Optional[int] = None, rating: Optional[float] = None,
                    duration: Optional[int] = None, extra_data: Optional[Dict] = None) -> UserBehavior:
        """Add user behavior record"""
        behavior = UserBehavior(
            user_id=user_id,
            behavior_type=behavior_type,
            poi_id=poi_id,
            itinerary_id=itinerary_id,
            rating=rating,
            duration=duration,
            extra_data=extra_data or {}
        )
        self.db.add(behavior)
        self.db.commit()
        self.db.refresh(behavior)
        return behavior

    def get_behaviors(self, user_id: int, limit: int = 20) -> List[UserBehavior]:
        """Get user behavior history"""
        return self.db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id
        ).order_by(UserBehavior.created_at.desc()).limit(limit).all()

    def get_poi_behaviors(self, user_id: int, poi_id: int) -> List[UserBehavior]:
        """Get behaviors for specific POI"""
        return self.db.query(UserBehavior).filter(
            UserBehavior.user_id == user_id,
            UserBehavior.poi_id == poi_id
        ).order_by(UserBehavior.created_at.desc()).all()

    # Analysis methods

    def analyze_preferences(self, user_id: int) -> Dict[str, Any]:
        """Analyze user preferences from behavior history"""
        behaviors = self.get_behaviors(user_id, limit=100)
        if not behaviors:
            return {}

        # Count behavior types
        behavior_counts = {}
        poi_visits = {}
        total_rating = 0
        rating_count = 0

        for b in behaviors:
            behavior_counts[b.behavior_type] = behavior_counts.get(b.behavior_type, 0) + 1
            if b.poi_id:
                poi_visits[b.poi_id] = poi_visits.get(b.poi_id, 0) + 1
            if b.rating:
                total_rating += b.rating
                rating_count += 1

        avg_rating = total_rating / rating_count if rating_count > 0 else None

        # Get top visited POIs
        sorted_pois = sorted(poi_visits.items(), key=lambda x: x[1], reverse=True)[:10]
        top_pois = [poi_id for poi_id, _ in sorted_pois]

        return {
            "behavior_counts": behavior_counts,
            "total_behaviors": len(behaviors),
            "avg_rating": avg_rating,
            "top_visited_pois": top_pois,
        }

    def update_stats(self, user_id: int) -> Optional[UserProfile]:
        """Update user profile statistics"""
        profile = self.get_profile(user_id)
        if not profile:
            return None

        # Count trips
        from app.models.itinerary import Itinerary
        trips_count = self.db.query(Itinerary).filter(Itinerary.user_id == user_id).count()
        profile.total_trips = trips_count

        # Count unique POIs visited
        from app.models.itinerary import ItineraryItem
        pois_count = self.db.query(ItineraryItem).join(Itinerary).filter(
            Itinerary.user_id == user_id
        ).distinct(ItineraryItem.poi_id).count()
        profile.total_pois_visited = pois_count

        profile.last_active_at = datetime.now()
        self.db.commit()
        self.db.refresh(profile)
        return profile
