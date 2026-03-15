"""
Trip Planning API Routes
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.agents.user_profile_agent import UserProfileAgent
from src.agents.itinerary_planner_agent import ItineraryPlannerAgent


router = APIRouter(prefix="/api/trip", tags=["trip"])

# In-memory storage for trips (in production, use database)
trips_storage: Dict[str, Dict[str, Any]] = {}


# Request models
class UserProfileRequest(BaseModel):
    user_id: int = 1
    interests: List[str] = []
    budget_level: str = "medium"
    travel_style: str = "balanced"
    group_type: str = "solo"
    fitness_level: str = "medium"
    age_group: str = "adult"
    has_children: bool = False
    price_sensitivity: float = 0.5


class TripCreateRequest(BaseModel):
    user_id: int = 1
    city: str = "hangzhou"
    start_date: str = None
    end_date: str = None
    days: int = 3
    profile: UserProfileRequest = None


class TripUpdateRequest(BaseModel):
    title: str = None
    status: str = None


# User Profile Agent
user_profile_agent = UserProfileAgent()

# Itinerary Planner Agent
itinerary_planner_agent = ItineraryPlannerAgent()


@router.post("/create")
async def create_trip(request: TripCreateRequest):
    """
    Create a new trip with user profile and generate itinerary
    """
    try:
        user_id = request.user_id
        
        # If profile is provided, use it; otherwise create default
        if request.profile:
            profile_context = {
                "user_id": user_id,
                "interests": request.profile.interests,
                "budget_level": request.profile.budget_level,
                "travel_style": request.profile.travel_style,
                "group_type": request.profile.group_type,
                "fitness_level": request.profile.fitness_level,
                "age_group": request.profile.age_group,
                "has_children": request.profile.has_children,
                "price_sensitivity": request.profile.price_sensitivity,
            }
        else:
            profile_context = {
                "user_id": user_id,
                "interests": [],
                "budget_level": "medium",
                "travel_style": "balanced",
                "group_type": "solo",
                "fitness_level": "medium",
            }
        
        # Run user profile agent
        profile_result = await user_profile_agent.run(profile_context)
        
        # Prepare itinerary context
        itinerary_context = {
            "user_id": user_id,
            "city": request.city,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "days": request.days,
            "profile_info": profile_result.get("user_profile", {}),
        }
        
        # Run itinerary planner agent
        itinerary_result = await itinerary_planner_agent.run(itinerary_context)
        
        # Get generated itinerary
        itinerary = itinerary_result.get("itinerary", {})
        itinerary_id = itinerary_result.get("itinerary_id", f"trip_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Save trip
        trip_data = {
            "id": itinerary_id,
            "user_id": user_id,
            "city": request.city,
            "title": f"{request.city.title()} Trip - {request.days} Days",
            "days": request.days,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "status": "Planning",
            "profile": profile_result.get("user_profile", {}),
            "itinerary": itinerary,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        trips_storage[itinerary_id] = trip_data
        
        return {
            "success": True,
            "trip": trip_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")


@router.get("/list")
async def list_trips(user_id: int = 1):
    """
    Get all trips for a user
    """
    user_trips = [
        trip for trip in trips_storage.values() 
        if trip.get("user_id") == user_id
    ]
    
    # Sort by created_at descending
    user_trips.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "success": True,
        "trips": user_trips,
        "total": len(user_trips)
    }


@router.get("/detail/{trip_id}")
async def get_trip_detail(trip_id: str):
    """
    Get detailed trip information
    """
    trip = trips_storage.get(trip_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return {
        "success": True,
        "trip": trip
    }


@router.put("/update/{trip_id}")
async def update_trip(trip_id: str, request: TripUpdateRequest):
    """
    Update trip information
    """
    trip = trips_storage.get(trip_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if request.title:
        trip["title"] = request.title
    if request.status:
        trip["status"] = request.status
    
    trip["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "trip": trip
    }


@router.delete("/delete/{trip_id}")
async def delete_trip(trip_id: str):
    """
    Delete a trip
    """
    if trip_id not in trips_storage:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    del trips_storage[trip_id]
    
    return {
        "success": True,
        "message": "Trip deleted successfully"
    }


@router.post("/profile/analyze")
async def analyze_profile(request: UserProfileRequest):
    """
    Analyze user profile without creating a trip
    """
    try:
        context = {
            "user_id": request.user_id,
            "interests": request.interests,
            "budget_level": request.budget_level,
            "travel_style": request.travel_style,
            "group_type": request.group_type,
            "fitness_level": request.fitness_level,
            "age_group": request.age_group,
            "has_children": request.has_children,
            "price_sensitivity": request.price_sensitivity,
        }
        
        result = await user_profile_agent.run(context)
        
        return {
            "success": True,
            "profile": result.get("user_profile", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze profile: {str(e)}")
