"""
Trip Planning Backend Server
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

from src.agents.user_profile_agent import UserProfileAgent
from src.agents.itinerary_planner_agent import ItineraryPlannerAgent
from src.db import init_db, save_trip, get_trip, get_user_trips, delete_trip as db_delete_trip

app = FastAPI(title="Trip Planning API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:3003", "http://127.0.0.1:3003", "http://localhost:3004", "http://127.0.0.1:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for trips (fallback if DB not available)
trips_storage: Dict[str, Dict[str, Any]] = {}

# JSON file for persistent storage
TRIPS_FILE = "trips_data.json"

def load_trips_from_file():
    """Load trips from JSON file"""
    global trips_storage
    try:
        if os.path.exists(TRIPS_FILE):
            with open(TRIPS_FILE, 'r', encoding='utf-8') as f:
                trips_storage = json.load(f)
            print(f"Loaded {len(trips_storage)} trips from file")
    except Exception as e:
        print(f"Warning: Failed to load trips from file: {e}")

def save_trips_to_file():
    """Save trips to JSON file"""
    try:
        with open(TRIPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(trips_storage, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save trips to file: {e}")


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


# Initialize agents
user_profile_agent = UserProfileAgent()
itinerary_planner_agent = ItineraryPlannerAgent()

# Database initialized flag
db_initialized = False


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global db_initialized

    # Load trips from file (同步函数)
    load_trips_from_file()
    print("Trips storage initialized from file")

    try:
        # Get database config from environment or use defaults
        import os
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = int(os.getenv("DB_PORT", "3306"))
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "040416")
        db_name = os.getenv("DB_NAME", "trailmark")

        await init_db(host=db_host, port=db_port, user=db_user, password=db_password, db=db_name)
        db_initialized = True
        print("Database connection initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize database: {e}")
        print("Will use in-memory storage as fallback")
        db_initialized = False

    # Initialize vector service (Milvus)
    try:
        from src.agents.vector_service import get_vector_service
        vector_service = get_vector_service()
        vector_service.connect()
        vector_service.create_collection_if_not_exists()
        print("Milvus vector service initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize Milvus: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    from src.db import get_db
    db = await get_db()
    if db and db.pool:
        await db.close()
        print("Database connection closed")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Trip Planning API is running"}


@app.post("/api/trip/create")
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
        
        # Save trip to database
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

        # Try to save to MySQL, fallback to in-memory
        if db_initialized:
            try:
                await save_trip(
                    trip_id=itinerary_id,
                    user_id=user_id,
                    city=request.city,
                    title=trip_data["title"],
                    days=request.days,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    status="Planning",
                    profile=profile_result.get("user_profile", {}),
                    itinerary=itinerary
                )
                trip_data["stored_in_db"] = True
                print(f"Trip saved to MySQL: {itinerary_id}")
            except Exception as e:
                print(f"Warning: Failed to save trip to MySQL: {e}")
                trips_storage[itinerary_id] = trip_data
                save_trips_to_file()
                trip_data["stored_in_db"] = False
        else:
            trips_storage[itinerary_id] = trip_data
            save_trips_to_file()
            trip_data["stored_in_db"] = False
        
        return {
            "success": True,
            "trip": trip_data
        }
        
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}\n{traceback.format_exc()}")


@app.get("/api/trip/list")
async def list_trips(user_id: int = 1):
    """
    Get all trips for a user
    """
    # Try to get from MySQL, fallback to in-memory
    if db_initialized:
        try:
            user_trips = await get_user_trips(user_id)
            # Convert to frontend format
            for trip in user_trips:
                trip["created_at"] = trip.get("created_at", "").isoformat() if hasattr(trip.get("created_at", ""), 'isoformat') else str(trip.get("created_at", ""))
                trip["updated_at"] = trip.get("updated_at", "").isoformat() if hasattr(trip.get("updated_at", ""), 'isoformat') else str(trip.get("updated_at", ""))
                trip["profile"] = json.loads(trip.get("itinerary", "{}")).get("profile", {}) if trip.get("itinerary") else {}

            return {
                "success": True,
                "trips": user_trips,
                "total": len(user_trips)
            }
        except Exception as e:
            print(f"Warning: Failed to get trips from MySQL: {e}")

    # Fallback to in-memory storage
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


@app.get("/api/trip/detail/{trip_id}")
async def get_trip_detail(trip_id: str):
    """
    Get detailed trip information
    """
    # Try to get from MySQL first
    if db_initialized:
        try:
            trip = await get_trip(trip_id)
            if trip:
                return {
                    "success": True,
                    "trip": trip
                }
        except Exception as e:
            print(f"Warning: Failed to get trip from MySQL: {e}")

    # Fallback to in-memory storage
    trip = trips_storage.get(trip_id)

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return {
        "success": True,
        "trip": trip
    }


@app.put("/api/trip/update/{trip_id}")
async def update_trip(trip_id: str, request: TripUpdateRequest):
    """
    Update trip information
    """
    # Try to get from MySQL first
    if db_initialized:
        try:
            trip = await get_trip(trip_id)
            if trip:
                # Update in memory first
                if request.title:
                    trip["title"] = request.title
                if request.status:
                    trip["status"] = request.status

                trip["updated_at"] = datetime.now().isoformat()

                # Save back to MySQL
                try:
                    await save_trip(
                        trip_id=trip_id,
                        user_id=trip.get("user_id", 1),
                        city=trip.get("city", ""),
                        title=trip.get("title", ""),
                        days=trip.get("days", 3),
                        start_date=str(trip.get("start_date", "")) if trip.get("start_date") else None,
                        end_date=str(trip.get("end_date", "")) if trip.get("end_date") else None,
                        status=trip.get("status", "Planning"),
                        profile=trip.get("profile", {}),
                        itinerary=trip.get("itinerary", {})
                    )
                except Exception as e:
                    print(f"Warning: Failed to update trip in MySQL: {e}")

                return {
                    "success": True,
                    "trip": trip
                }
        except Exception as e:
            print(f"Warning: Failed to get trip from MySQL: {e}")

    # Fallback to in-memory storage
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


@app.delete("/api/trip/delete/{trip_id}")
async def delete_trip(trip_id: str):
    """
    Delete a trip
    """
    # Try to delete from MySQL
    if db_initialized:
        try:
            deleted = await db_delete_trip(trip_id)
            if deleted:
                return {
                    "success": True,
                    "message": "Trip deleted successfully"
                }
        except Exception as e:
            print(f"Warning: Failed to delete trip from MySQL: {e}")

    # Fallback to in-memory storage
    if trip_id not in trips_storage:
        raise HTTPException(status_code=404, detail="Trip not found")

    del trips_storage[trip_id]
    save_trips_to_file()

    return {
        "success": True,
        "message": "Trip deleted successfully"
    }


@app.post("/api/trip/profile/analyze")
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
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to analyze profile: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)
