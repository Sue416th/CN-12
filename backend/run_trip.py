"""
Trip Planning Backend Server
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from src.agents.user_profile_agent import UserProfileAgent
from src.agents.itinerary_planner_agent import ItineraryPlannerAgent
from src.agents.post_trip_evaluation_agent import PostTripEvaluationAgent
from src.navigation.main import router as navigation_router
from src.db import (
    init_db,
    get_db,
    save_trip,
    get_trip,
    get_user_trips,
    delete_trip as db_delete_trip,
    save_trip_evaluation,
    get_trip_evaluation,
)

app = FastAPI(title="Trip Planning API", version="1.0.0")
app.include_router(navigation_router, prefix="/api/navigation", tags=["navigation"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:3003", "http://127.0.0.1:3003", "http://localhost:3004", "http://127.0.0.1:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trips_storage: Dict[str, Dict[str, Any]] = {}
evaluations_storage: Dict[str, Dict[str, Any]] = {}

TRIPS_FILE = "trips_data.json"
EVALUATIONS_FILE = "trip_evaluations_data.json"

def load_trips_from_file():
    global trips_storage
    try:
        if os.path.exists(TRIPS_FILE):
            with open(TRIPS_FILE, 'r', encoding='utf-8') as f:
                trips_storage = json.load(f)
            print(f"Loaded {len(trips_storage)} trips from file")
    except Exception as e:
        print(f"Warning: Failed to load trips from file: {e}")

def save_trips_to_file():
    try:
        with open(TRIPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(trips_storage, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save trips to file: {e}")


def load_evaluations_from_file():
    global evaluations_storage
    try:
        if os.path.exists(EVALUATIONS_FILE):
            with open(EVALUATIONS_FILE, 'r', encoding='utf-8') as f:
                evaluations_storage = json.load(f)
            print(f"Loaded {len(evaluations_storage)} evaluations from file")
    except Exception as e:
        print(f"Warning: Failed to load evaluations from file: {e}")


def save_evaluations_to_file():
    try:
        with open(EVALUATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(evaluations_storage, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save evaluations to file: {e}")


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


class TripEvaluationRequest(BaseModel):
    user_id: int
    trip_id: str
    overall_satisfaction: int
    crowded_level: str = "Medium"
    schedule_reasonable: str = "Yes"
    transportation_convenience: str = "Good"
    review: str


user_profile_agent = UserProfileAgent()
itinerary_planner_agent = ItineraryPlannerAgent()
post_trip_evaluation_agent = PostTripEvaluationAgent()

db_initialized = False


async def ensure_trip_evaluations_table():
    db = await get_db()
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS trip_evaluations (
          id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
          trip_id VARCHAR(100) NOT NULL,
          user_id BIGINT UNSIGNED NOT NULL,
          trip_title VARCHAR(255),
          feedback JSON NOT NULL,
          analysis JSON NOT NULL,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uk_trip_evaluations_trip_id (trip_id),
          KEY idx_trip_evaluations_user_id (user_id),
          FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """
    await db.execute_update(create_table_sql)


@app.on_event("startup")
async def startup_event():
    global db_initialized

    load_trips_from_file()
    load_evaluations_from_file()
    print("Trips storage initialized from file")

    try:
        import os
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = int(os.getenv("DB_PORT", "3306"))
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "040416")
        db_name = os.getenv("DB_NAME", "trailmark")

        await init_db(host=db_host, port=db_port, user=db_user, password=db_password, db=db_name)
        await ensure_trip_evaluations_table()
        db_initialized = True
        print("Database connection initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize database: {e}")
        print("Will use in-memory storage as fallback")
        db_initialized = False

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
    db = await get_db()
    if db and db.pool:
        await db.close()
        print("Database connection closed")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Trip Planning API is running"}


@app.post("/api/trip/create")
async def create_trip(request: TripCreateRequest):
    try:
        user_id = request.user_id
        
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
        
        profile_result = await user_profile_agent.run(profile_context)
        
        itinerary_context = {
            "user_id": user_id,
            "city": request.city,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "days": request.days,
            "profile_info": profile_result.get("user_profile", {}),
        }
        
        itinerary_result = await itinerary_planner_agent.run(itinerary_context)
        
        itinerary = itinerary_result.get("itinerary", {})
        itinerary_id = itinerary_result.get("itinerary_id", f"trip_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
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
    if db_initialized:
        try:
            user_trips = await get_user_trips(user_id)
            if not user_trips:
                user_trips = [
                    trip for trip in trips_storage.values()
                    if trip.get("user_id") == user_id
                ]
            if user_trips:
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

    user_trips = [
        trip for trip in trips_storage.values()
        if trip.get("user_id") == user_id
    ]

    user_trips.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "success": True,
        "trips": user_trips,
        "total": len(user_trips)
    }


@app.get("/api/trip/detail/{trip_id}")
async def get_trip_detail(trip_id: str):
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

    trip = trips_storage.get(trip_id)

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return {
        "success": True,
        "trip": trip
    }


@app.put("/api/trip/update/{trip_id}")
async def update_trip(trip_id: str, request: TripUpdateRequest):
    if db_initialized:
        try:
            trip = await get_trip(trip_id)
            if trip:
                if request.title:
                    trip["title"] = request.title
                if request.status:
                    trip["status"] = request.status

                trip["updated_at"] = datetime.now().isoformat()

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
                    trip["stored_in_db"] = False
                    trips_storage[trip_id] = trip
                    save_trips_to_file()

                return {
                    "success": True,
                    "trip": trip
                }
        except Exception as e:
            print(f"Warning: Failed to get trip from MySQL: {e}")

    trip = trips_storage.get(trip_id)

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if request.title:
        trip["title"] = request.title
    if request.status:
        trip["status"] = request.status

    trip["updated_at"] = datetime.now().isoformat()
    save_trips_to_file()

    return {
        "success": True,
        "trip": trip
    }


@app.delete("/api/trip/delete/{trip_id}")
async def delete_trip(trip_id: str):
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

    if trip_id not in trips_storage:
        raise HTTPException(status_code=404, detail="Trip not found")

    del trips_storage[trip_id]
    save_trips_to_file()

    return {
        "success": True,
        "message": "Trip deleted successfully"
    }


@app.post("/api/trip/evaluate")
async def evaluate_trip_feedback(request: TripEvaluationRequest):
    review_text = (request.review or "").strip()
    if not review_text:
        raise HTTPException(status_code=400, detail="Review is required")

    composite_review = (
        f"Overall satisfaction: {request.overall_satisfaction}/5. "
        f"Crowded level: {request.crowded_level}. "
        f"Schedule reasonable: {request.schedule_reasonable}. "
        f"Transportation convenience: {request.transportation_convenience}. "
        f"Review: {review_text}"
    )

    try:
        analysis = post_trip_evaluation_agent.evaluate(composite_review)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate feedback: {str(e)}")

    feedback_payload = {
        "overall_satisfaction": request.overall_satisfaction,
        "crowded_level": request.crowded_level,
        "schedule_reasonable": request.schedule_reasonable,
        "transportation_convenience": request.transportation_convenience,
        "review": review_text,
    }

    trip = None
    try:
        trip = await get_trip(request.trip_id) if db_initialized else trips_storage.get(request.trip_id)
    except Exception:
        trip = trips_storage.get(request.trip_id)
    trip_title = (trip or {}).get("title", request.trip_id)

    if db_initialized:
        try:
            await save_trip_evaluation(
                trip_id=request.trip_id,
                user_id=request.user_id,
                trip_title=trip_title,
                feedback=feedback_payload,
                analysis=analysis,
            )
        except Exception as e:
            print(f"Warning: Failed to save trip evaluation to MySQL: {e}")
            db_key = f"{request.user_id}:{request.trip_id}"
            evaluations_storage[db_key] = {
                "trip_id": request.trip_id,
                "user_id": request.user_id,
                "trip_title": trip_title,
                "feedback": feedback_payload,
                "analysis": analysis,
            }
            save_evaluations_to_file()
    else:
        db_key = f"{request.user_id}:{request.trip_id}"
        evaluations_storage[db_key] = {
            "trip_id": request.trip_id,
            "user_id": request.user_id,
            "trip_title": trip_title,
            "feedback": feedback_payload,
            "analysis": analysis,
        }
        save_evaluations_to_file()

    return {
        "success": True,
        "trip_id": request.trip_id,
        "user_id": request.user_id,
        "trip_title": trip_title,
        "feedback": feedback_payload,
        "analysis": analysis,
    }


@app.get("/api/trip/evaluate/{trip_id}")
async def get_trip_evaluation_result(trip_id: str, user_id: int = Query(...)):
    if db_initialized:
        try:
            row = await get_trip_evaluation(trip_id, user_id)
            if row:
                return {
                    "success": True,
                    "trip_id": row["trip_id"],
                    "user_id": row["user_id"],
                    "trip_title": row.get("trip_title"),
                    "feedback": row.get("feedback", {}),
                    "analysis": row.get("analysis", {}),
                }
        except Exception as e:
            print(f"Warning: Failed to fetch trip evaluation from MySQL: {e}")

    db_key = f"{user_id}:{trip_id}"
    row = evaluations_storage.get(db_key)
    if row:
        return {
            "success": True,
            "trip_id": row["trip_id"],
            "user_id": row["user_id"],
            "trip_title": row.get("trip_title"),
            "feedback": row.get("feedback", {}),
            "analysis": row.get("analysis", {}),
        }

    raise HTTPException(status_code=404, detail="Trip evaluation not found")


@app.post("/api/trip/profile/analyze")
async def analyze_profile(request: UserProfileRequest):
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
        
        profile_result = await user_profile_agent.run(context)
        
        return {
            "success": True,
            "profile": profile_result.get("user_profile", {})
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to analyze profile: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)
