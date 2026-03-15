"""
MySQL Database Connection Module
"""
import json
from typing import Optional, Dict, Any, List
import aiomysql


class Database:
    def __init__(self):
        self.pool: Optional[aiomysql.Pool] = None

    async def init_pool(self, host: str = "127.0.0.1", port: int = 3306,
                        user: str = "root", password: str = "",
                        db: str = "trailmark", minsize: int = 1, maxsize: int = 10):
        """Initialize database connection pool"""
        self.pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=db,
            minsize=minsize,
            maxsize=maxsize,
            charset='utf8mb4',
            autocommit=True
        )
        print(f"Connected to MySQL at {host}:{port}, database: {db}")

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute(self, query: str, args: tuple = None) -> Optional[Any]:
        """Execute a query and return result"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchone()

    async def execute_many(self, query: str, args: tuple = None) -> Optional[Any]:
        """Execute a query with multiple rows"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchall()

    async def execute_insert(self, query: str, args: tuple = None) -> int:
        """Execute insert and return last row id"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return cur.lastrowid

    async def execute_update(self, query: str, args: tuple = None) -> int:
        """Execute update and return affected rows"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return cur.rowcount


# Global database instance
_db: Optional[Database] = None


async def get_db() -> Database:
    """Get database instance"""
    global _db
    if _db is None:
        _db = Database()
    return _db


async def init_db(host: str = "127.0.0.1", port: int = 3306,
                  user: str = "root", password: str = "",
                  db: str = "trailmark"):
    """Initialize database connection"""
    global _db
    _db = Database()
    await _db.init_pool(host=host, port=port, user=user, password=password, db=db)
    return _db


# Profile operations
async def save_user_profile(user_id: int, profile: Dict[str, Any]) -> int:
    """Save or update user profile"""
    db = await get_db()

    # Convert lists/dicts to JSON
    interests = json.dumps(profile.get("interests", []))
    cultural_preferences = json.dumps(profile.get("cultural_preferences", {}))
    refined_interests = json.dumps(profile.get("refined_interests", []))
    preferred_categories = json.dumps(profile.get("preferred_categories", []))
    budget_info = json.dumps(profile.get("budget_info", {}))
    fitness_info = json.dumps(profile.get("fitness_info", {}))

    query = """
        INSERT INTO user_profiles
        (user_id, interests, budget_level, travel_style, group_type, fitness_level,
         age_group, has_children, price_sensitivity, cultural_preferences, refined_interests,
         preferred_categories, budget_info, fitness_info, pace_preference)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        interests = VALUES(interests),
        budget_level = VALUES(budget_level),
        travel_style = VALUES(travel_style),
        group_type = VALUES(group_type),
        fitness_level = VALUES(fitness_level),
        age_group = VALUES(age_group),
        has_children = VALUES(has_children),
        price_sensitivity = VALUES(price_sensitivity),
        cultural_preferences = VALUES(cultural_preferences),
        refined_interests = VALUES(refined_interests),
        preferred_categories = VALUES(preferred_categories),
        budget_info = VALUES(budget_info),
        fitness_info = VALUES(fitness_info),
        pace_preference = VALUES(pace_preference)
    """

    return await db.execute_insert(query, (
        user_id, interests, profile.get("budget_level", "medium"),
        profile.get("travel_style", "balanced"), profile.get("group_type", "solo"),
        profile.get("fitness_level", "medium"), profile.get("age_group", "adult"),
        profile.get("has_children", False), profile.get("price_sensitivity", 0.5),
        cultural_preferences, refined_interests, preferred_categories,
        budget_info, fitness_info, profile.get("pace_preference", "balanced")
    ))


async def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile by user_id"""
    db = await get_db()
    query = "SELECT * FROM user_profiles WHERE user_id = %s LIMIT 1"
    row = await db.execute(query, (user_id,))

    if row:
        # Convert JSON fields back to Python objects
        row["interests"] = json.loads(row["interests"]) if row.get("interests") else []
        row["cultural_preferences"] = json.loads(row["cultural_preferences"]) if row.get("cultural_preferences") else {}
        row["refined_interests"] = json.loads(row["refined_interests"]) if row.get("refined_interests") else []
        row["preferred_categories"] = json.loads(row["preferred_categories"]) if row.get("preferred_categories") else []
        row["budget_info"] = json.loads(row["budget_info"]) if row.get("budget_info") else {}
        row["fitness_info"] = json.loads(row["fitness_info"]) if row.get("fitness_info") else {}

    return row


# Trip operations
async def save_trip(trip_id: str, user_id: int, city: str, title: str, days: int,
                    start_date: Optional[str], end_date: Optional[str],
                    status: str, profile: Dict[str, Any], itinerary: Dict[str, Any]) -> str:
    """Save or update trip"""
    db = await get_db()

    profile_json = json.dumps(profile)
    itinerary_json = json.dumps(itinerary)

    query = """
        INSERT INTO trips
        (id, user_id, city, title, days, start_date, end_date, status, itinerary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        days = VALUES(days),
        start_date = VALUES(start_date),
        end_date = VALUES(end_date),
        status = VALUES(status),
        itinerary = VALUES(itinerary)
    """

    await db.execute_insert(query, (
        trip_id, user_id, city, title, days, start_date, end_date, status, itinerary_json
    ))
    return trip_id


async def get_trip(trip_id: str) -> Optional[Dict[str, Any]]:
    """Get trip by id"""
    db = await get_db()
    query = "SELECT * FROM trips WHERE id = %s LIMIT 1"
    row = await db.execute(query, (trip_id,))

    if row and row.get("itinerary"):
        row["itinerary"] = json.loads(row["itinerary"])

    return row


async def get_user_trips(user_id: int) -> List[Dict[str, Any]]:
    """Get all trips for a user"""
    db = await get_db()
    query = "SELECT * FROM trips WHERE user_id = %s ORDER BY created_at DESC"
    rows = await db.execute_many(query, (user_id,))

    for row in rows:
        if row.get("itinerary"):
            row["itinerary"] = json.loads(row["itinerary"])

    return rows


async def delete_trip(trip_id: str) -> bool:
    """Delete a trip"""
    db = await get_db()
    query = "DELETE FROM trips WHERE id = %s"
    affected = await db.execute_update(query, (trip_id,))
    return affected > 0


async def save_trip_evaluation(
    trip_id: str,
    user_id: int,
    trip_title: str,
    feedback: Dict[str, Any],
    analysis: Dict[str, Any],
) -> str:
    """Save or update one evaluation for a trip."""
    db = await get_db()

    feedback_json = json.dumps(feedback, ensure_ascii=False)
    analysis_json = json.dumps(analysis, ensure_ascii=False)
    query = """
        INSERT INTO trip_evaluations
        (trip_id, user_id, trip_title, feedback, analysis)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        user_id = VALUES(user_id),
        trip_title = VALUES(trip_title),
        feedback = VALUES(feedback),
        analysis = VALUES(analysis)
    """
    await db.execute_insert(query, (trip_id, user_id, trip_title, feedback_json, analysis_json))
    return trip_id


async def get_trip_evaluation(trip_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Get one trip evaluation by trip id and user id."""
    db = await get_db()
    query = """
        SELECT trip_id, user_id, trip_title, feedback, analysis, created_at, updated_at
        FROM trip_evaluations
        WHERE trip_id = %s AND user_id = %s
        LIMIT 1
    """
    row = await db.execute(query, (trip_id, user_id))
    if not row:
        return None

    if row.get("feedback"):
        row["feedback"] = json.loads(row["feedback"])
    if row.get("analysis"):
        row["analysis"] = json.loads(row["analysis"])
    return row
