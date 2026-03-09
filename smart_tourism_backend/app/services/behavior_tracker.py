from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime


class BehaviorTracker:
    """
    Automatic behavior tracking service
    Tracks user interactions and updates profiles accordingly
    """

    def __init__(self, db: Session):
        self.db = db
        from app.services.user_profile_service import UserProfileService
        self.profile_service = UserProfileService(db)

    def track_poi_view(
        self,
        user_id: int,
        poi_id: int,
        poi_data: Optional[Dict[str, Any]] = None,
    ):
        """Track POI view event"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="view",
            poi_id=poi_id,
            extra_data={
                "poi_name": poi_data.get("name") if poi_data else None,
                "poi_category": poi_data.get("category") if poi_data else None,
            }
        )

    def track_poi_visit(
        self,
        user_id: int,
        poi_id: int,
        itinerary_id: int,
        duration: Optional[int] = None,
        rating: Optional[float] = None,
        poi_data: Optional[Dict[str, Any]] = None,
    ):
        """Track POI visit event (user actually visited)"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="visit",
            poi_id=poi_id,
            itinerary_id=itinerary_id,
            duration=duration,
            rating=rating,
            extra_data={
                "poi_name": poi_data.get("name") if poi_data else None,
                "poi_category": poi_data.get("category") if poi_data else None,
            }
        )

    def track_poi_rating(
        self,
        user_id: int,
        poi_id: int,
        rating: float,
        poi_data: Optional[Dict[str, Any]] = None,
    ):
        """Track POI rating event"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="rate",
            poi_id=poi_id,
            rating=rating,
            extra_data={
                "poi_name": poi_data.get("name") if poi_data else None,
            }
        )

    def track_bookmark(
        self,
        user_id: int,
        poi_id: int,
        poi_data: Optional[Dict[str, Any]] = None,
    ):
        """Track bookmark event"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="bookmark",
            poi_id=poi_id,
            extra_data={
                "poi_name": poi_data.get("name") if poi_data else None,
            }
        )

    def track_share(
        self,
        user_id: int,
        itinerary_id: int,
    ):
        """Track itinerary share event"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="share",
            itinerary_id=itinerary_id,
        )

    def track_search(
        self,
        user_id: int,
        keyword: str,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """Track search event"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="search",
            extra_data={
                "keyword": keyword,
                "filters": filters,
            }
        )

    def track_itinerary_create(
        self,
        user_id: int,
        itinerary_id: int,
        city: str,
        days: int,
    ):
        """Track itinerary creation"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type="create_itinerary",
            itinerary_id=itinerary_id,
            extra_data={
                "city": city,
                "days": days,
            }
        )

    def track_feedback(
        self,
        user_id: int,
        feedback_type: str,  # like, dislike, helpful, not_helpful
        target_type: str,  # poi, itinerary, recommendation
        target_id: int,
        content: Optional[str] = None,
    ):
        """Track user feedback on recommendations"""
        self.profile_service.add_behavior(
            user_id=user_id,
            behavior_type=feedback_type,
            extra_data={
                "target_type": target_type,
                "target_id": target_id,
                "content": content,
            }
        )

    def update_profile_from_behavior(self, user_id: int):
        """Update user profile based on recent behaviors"""
        analysis = self.profile_service.analyze_preferences(user_id)
        
        if not analysis:
            return None

        # Extract insights
        new_interests = []
        new_cultural_prefs = {}
        
        # Analyze top visited POI categories
        if "top_visited_pois" in analysis and analysis["top_pois"]:
            # This would require POI service to get categories
            pass

        # Update profile if significant changes detected
        if new_interests or new_cultural_prefs:
            profile = self.profile_service.get_profile(user_id)
            if profile:
                updates = {}
                if new_interests:
                    existing = profile.interests or []
                    updates["interests"] = list(set(existing + new_interests))
                if new_cultural_prefs:
                    existing_prefs = profile.cultural_preferences or {}
                    updates["cultural_preferences"] = {**existing_prefs, **new_cultural_prefs}
                
                if updates:
                    self.profile_service.update_profile(user_id, updates)
                    return updates
        
        return None
