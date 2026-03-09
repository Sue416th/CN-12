from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_orchestrator
from app.models.poi import POI
from app.schemas.itinerary import (
    ItineraryCreateRequest,
    ItineraryDetailResponse,
    ItineraryListItem,
    ItineraryResponse,
)
from app.schemas.poi import POIResponse
from app.services.itinerary_service import ItineraryService
from app.services.poi_service import POIService


router = APIRouter()


@router.post("/itineraries/pre_trip", response_model=ItineraryResponse)
async def create_itinerary_pre_trip(
    payload: ItineraryCreateRequest,
    db: Session = Depends(get_db),
    orchestrator=Depends(get_orchestrator),
):
    """
    Pre-trip: 使用多智能体编排生成行程，并持久化到数据库。
    支持多城市、多日、个性化推荐。
    """
    try:
        context: Dict[str, Any] = {
            "db": db,
            "user_id": payload.user_id,
            "city": payload.city,
            "constraints": {
                "start_date": payload.start_date,
                "end_date": payload.end_date,
                "budget_level": payload.budget_level,
                "interests": payload.interests,
            },
            "budget_level": payload.budget_level,
            "travel_style": payload.travel_style,
            "group_type": payload.group_type,
            "interests": payload.interests,
        }

        result_context = await orchestrator.run_pre_trip_flow(context)

        if "error" in result_context:
            error_msg = result_context.get("error", "Unknown error")
            error_detail = result_context.get("error_detail", "")
            full_error = f"{error_msg}\n{error_detail}" if error_detail else error_msg
            raise HTTPException(status_code=500, detail=full_error)

        itinerary = result_context.get("itinerary")
        if not itinerary:
            raise HTTPException(status_code=500, detail="行程生成失败")

        if isinstance(itinerary, dict) and itinerary.get("error"):
            raise HTTPException(status_code=400, detail=itinerary["error"])

        return itinerary
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to generate itinerary: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"行程生成失败: {str(e)}")


@router.get("/itineraries", response_model=List[ItineraryListItem])
def list_itineraries(
    user_id: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取用户的行程列表。"""
    svc = ItineraryService(db)
    return svc.list_by_user(user_id=user_id, limit=limit)


@router.get("/itineraries/{itinerary_id}", response_model=ItineraryDetailResponse)
def get_itinerary(
    itinerary_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """获取行程详情。"""
    svc = ItineraryService(db)
    detail = svc.get_by_id(itinerary_id=itinerary_id, user_id=user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="行程不存在")
    return detail


@router.post("/itineraries/{itinerary_id}/optimize")
def optimize_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
):
    """优化现有行程顺序"""
    svc = ItineraryService(db)
    result = svc.optimize_itinerary(itinerary_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.delete("/itineraries/{itinerary_id}")
def delete_itinerary(
    itinerary_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """删除行程"""
    svc = ItineraryService(db)
    success = svc.delete_itinerary(itinerary_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="行程不存在或删除失败")
    return {"message": "删除成功", "itinerary_id": itinerary_id}


@router.get("/pois", response_model=List[POIResponse])
def list_pois(
    city: str = None,
    category: str = None,
    db: Session = Depends(get_db),
):
    """获取景点列表（支持按城市/类别筛选）。"""
    svc = POIService(db)
    svc._ensure_sample_pois()

    if city:
        pois = svc.get_by_city(city)
    elif category:
        pois = svc.get_by_category(category)
    else:
        pois = db.query(POI).all()

    return pois


@router.get("/pois/search", response_model=List[POIResponse])
def search_pois(
    keyword: str,
    city: str = None,
    category: str = None,
    db: Session = Depends(get_db),
):
    """搜索景点"""
    svc = POIService(db)
    svc._ensure_sample_pois()
    return svc.search(keyword, city, category)


@router.get("/pois/{poi_id}/realtime")
def get_poi_realtime(
    poi_id: int,
    db: Session = Depends(get_db),
):
    """Get POI realtime data (crowd level, open status, etc.)"""
    from app.services.external_api import poi_realtime_api

    # Get POI info
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Get realtime data (synchronous call)
    realtime_data = poi_realtime_api.get_realtime_data(poi.name, poi.id)

    return {
        "poi_id": poi_id,
        "poi_name": poi.name,
        "realtime": realtime_data,
    }


@router.get("/pois/{poi_id}/history")
def get_poi_history(
    poi_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Get POI historical crowd data"""
    from app.services.external_api import poi_realtime_api

    # Get POI info
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise HTTPException(status_code=404, detail="POI not found")

    # Get historical data (synchronous call)
    history_data = poi_realtime_api.get_historical_data(poi.name, days)

    return {
        "poi_id": poi_id,
        "poi_name": poi.name,
        "history": history_data,
    }


# ============== User Profile APIs ==============

from app.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserBehaviorCreate,
    UserBehaviorResponse,
)
from app.services.user_profile_service import UserProfileService
from app.services.behavior_tracker import BehaviorTracker
from app.services.agent_monitor import get_monitor


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get user profile"""
    svc = UserProfileService(db)
    profile = svc.get_profile(user_id)
    if not profile:
        # Return default profile
        return {
            "id": 0,
            "user_id": user_id,
            "interests": [],
            "budget_level": "medium",
            "travel_style": "balanced",
            "group_type": "solo",
            "fitness_level": "medium",
            "cultural_preferences": {},
            "preferred_categories": [],
            "tags": [],
            "profile_vector_id": None,
            "extended_info": {},
            "total_trips": 0,
            "total_pois_visited": 0,
            "last_active_at": None,
            "notes": None,
        }
    return profile


@router.post("/users/{user_id}/profile", response_model=UserProfileResponse)
def create_or_update_profile(
    user_id: int,
    data: UserProfileCreate,
    db: Session = Depends(get_db),
):
    """Create or update user profile"""
    try:
        svc = UserProfileService(db)

        # Convert Pydantic model to dict
        profile_data = data.model_dump(exclude={"user_id"})

        print(f"[DEBUG] Updating profile for user_id={user_id}, data={profile_data}")

        profile = svc.update_profile(user_id, profile_data)

        print(f"[DEBUG] Profile updated successfully, id={profile.id}")

        return profile
    except Exception as e:
        import traceback
        print(f"[ERROR] Failed to update profile: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.post("/users/{user_id}/behaviors", response_model=UserBehaviorResponse)
def add_user_behavior(
    user_id: int,
    data: UserBehaviorCreate,
    db: Session = Depends(get_db),
):
    """Add user behavior record"""
    svc = UserProfileService(db)

    # Convert Pydantic model to dict
    behavior_data = data.model_dump(exclude={"user_id"})

    behavior = svc.add_behavior(user_id=user_id, **behavior_data)
    return behavior


@router.get("/users/{user_id}/behaviors", response_model=List[UserBehaviorResponse])
def get_user_behaviors(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get user behavior history"""
    svc = UserProfileService(db)
    return svc.get_behaviors(user_id, limit)


@router.get("/users/{user_id}/analysis")
def get_user_analysis(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get user preference analysis based on behavior history"""
    svc = UserProfileService(db)

    # Get profile
    profile = svc.get_profile(user_id)

    # Analyze behaviors
    analysis = svc.analyze_preferences(user_id)

    return {
        "user_id": user_id,
        "profile": profile,
        "analysis": analysis,
    }


# ============== Behavior Tracking APIs ==============

@router.post("/users/{user_id}/track/view")
def track_poi_view(
    user_id: int,
    poi_id: int,
    poi_name: str = None,
    poi_category: str = None,
    db: Session = Depends(get_db),
):
    """Track POI view event"""
    tracker = BehaviorTracker(db)
    tracker.track_poi_view(
        user_id=user_id,
        poi_id=poi_id,
        poi_data={"name": poi_name, "category": poi_category}
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/track/visit")
def track_poi_visit(
    user_id: int,
    poi_id: int,
    itinerary_id: int = None,
    duration: int = None,
    rating: float = None,
    poi_name: str = None,
    poi_category: str = None,
    db: Session = Depends(get_db),
):
    """Track POI visit event"""
    tracker = BehaviorTracker(db)
    tracker.track_poi_visit(
        user_id=user_id,
        poi_id=poi_id,
        itinerary_id=itinerary_id,
        duration=duration,
        rating=rating,
        poi_data={"name": poi_name, "category": poi_category}
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/track/rate")
def track_poi_rating(
    user_id: int,
    poi_id: int,
    rating: float,
    poi_name: str = None,
    db: Session = Depends(get_db),
):
    """Track POI rating event"""
    tracker = BehaviorTracker(db)
    tracker.track_poi_rating(
        user_id=user_id,
        poi_id=poi_id,
        rating=rating,
        poi_data={"name": poi_name}
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/track/bookmark")
def track_bookmark(
    user_id: int,
    poi_id: int,
    poi_name: str = None,
    db: Session = Depends(get_db),
):
    """Track bookmark event"""
    tracker = BehaviorTracker(db)
    tracker.track_bookmark(
        user_id=user_id,
        poi_id=poi_id,
        poi_data={"name": poi_name}
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/track/feedback")
def track_feedback(
    user_id: int,
    feedback_type: str,
    target_type: str,
    target_id: int,
    content: str = None,
    db: Session = Depends(get_db),
):
    """Track user feedback on recommendations"""
    tracker = BehaviorTracker(db)
    tracker.track_feedback(
        user_id=user_id,
        feedback_type=feedback_type,
        target_type=target_type,
        target_id=target_id,
        content=content
    )
    return {"status": "ok"}


@router.post("/users/{user_id}/track/search")
def track_search(
    user_id: int,
    keyword: str,
    city: str = None,
    category: str = None,
    db: Session = Depends(get_db),
):
    """Track search event"""
    tracker = BehaviorTracker(db)
    tracker.track_search(
        user_id=user_id,
        keyword=keyword,
        filters={"city": city, "category": category}
    )
    return {"status": "ok"}


# ============== Agent Monitoring APIs ==============

@router.get("/monitor/status")
def get_agent_status():
    """Get agent system health status"""
    monitor = get_monitor()
    return monitor.get_health_status()


@router.get("/monitor/stats")
def get_agent_stats(agent_name: str = None):
    """Get detailed agent statistics"""
    monitor = get_monitor()
    return monitor.get_agent_stats(agent_name)
