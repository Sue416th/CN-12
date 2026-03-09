"""
Knowledge Graph Service - Neo4j Integration
知识图谱服务 - 存储POI关系、用户-POI交互知识
"""
from typing import Any, Dict, List, Optional, Tuple
from neo4j import GraphDatabase
import json


class KnowledgeGraphService:
    """
    Knowledge Graph Service using Neo4j
    
    图谱设计：
    1. POI节点 - 景点信息
    2. User节点 - 用户信息  
    3. Category节点 - POI类别
    4. 关系类型：
       - (User)-[:VISITED]->(POI)
       - (User)-[:LIKES]->(Category)
       - (POI)-[:NEARBY]->(POI)
       - (POI)-[:SAME_CATEGORY]->(Category)
       - (POI)-[:RECOMMENDED_WITH]->(POI)
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_constraints()
    
    def _ensure_constraints(self):
        """Create constraints if not exist"""
        with self.driver.session() as session:
            # User constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) 
                REQUIRE u.user_id IS UNIQUE
            """)
            # POI constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (p:POI) 
                REQUIRE p.poi_id IS UNIQUE
            """)
            # Category constraint
            session.run("""
                CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) 
                REQUIRE c.name IS UNIQUE
            """)
    
    def close(self):
        """Close connection"""
        self.driver.close()
    
    # ==================== User Node Operations ====================
    
    def create_user(self, user_id: int, profile: Dict[str, Any]) -> bool:
        """Create or update user node"""
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {user_id: $user_id})
                SET u.interests = $interests,
                    u.budget_level = $budget_level,
                    u.travel_style = $travel_style,
                    u.fitness_level = $fitness_level,
                    u.cultural_preferences = $cultural_preferences,
                    u.profile_vector_id = $profile_vector_id,
                    u.updated_at = timestamp()
            """,
                user_id=user_id,
                interests=json.dumps(profile.get("interests", [])),
                budget_level=profile.get("budget_level", "medium"),
                travel_style=profile.get("travel_style", "balanced"),
                fitness_level=profile.get("fitness_level", "medium"),
                cultural_preferences=json.dumps(profile.get("cultural_preferences", {})),
                profile_vector_id=profile.get("profile_vector_id"),
            )
        return True
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile from knowledge graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})
                RETURN u
            """, user_id=user_id)
            
            record = result.single()
            if record:
                u = record["u"]
                return {
                    "user_id": u.get("user_id"),
                    "interests": json.loads(u.get("interests", "[]")),
                    "budget_level": u.get("budget_level"),
                    "travel_style": u.get("travel_style"),
                    "fitness_level": u.get("fitness_level"),
                    "cultural_preferences": json.loads(u.get("cultural_preferences", "{}")),
                }
        return None
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preference in knowledge graph"""
        with self.driver.session() as session:
            # Build SET clause dynamically
            set_clauses = []
            params = {"user_id": user_id}
            
            for key, value in preferences.items():
                set_clauses.append(f"u.{key} = ${key}")
                if isinstance(value, (dict, list)):
                    params[key] = json.dumps(value)
                else:
                    params[key] = value
            
            if set_clauses:
                query = f"""
                    MATCH (u:User {{user_id: $user_id}})
                    SET {', '.join(set_clauses)}, u.updated_at = timestamp()
                """
                session.run(query, **params)
        return True
    
    # ==================== POI Node Operations ====================
    
    def create_poi(self, poi_id: str, poi_data: Dict[str, Any]) -> bool:
        """Create or update POI node"""
        with self.driver.session() as session:
            session.run("""
                MERGE (p:POI {poi_id: $poi_id})
                SET p.name = $name,
                    p.category = $category,
                    p.city = $city,
                    p.latitude = $latitude,
                    p.longitude = $longitude,
                    p.rating = $rating,
                    p.price_level = $price_level,
                    p.tags = $tags,
                    p.description = $description,
                    p.updated_at = timestamp()
            """,
                poi_id=poi_id,
                name=poi_data.get("name", ""),
                category=poi_data.get("category", ""),
                city=poi_data.get("city", ""),
                latitude=poi_data.get("latitude", 0.0),
                longitude=poi_data.get("longitude", 0.0),
                rating=poi_data.get("rating", 0.0),
                price_level=poi_data.get("price_level", 0),
                tags=json.dumps(poi_data.get("tags", [])),
                description=poi_data.get("description", ""),
            )
            
            # Create category relationship
            category = poi_data.get("category")
            if category:
                session.run("""
                    MATCH (p:POI {poi_id: $poi_id})
                    MERGE (c:Category {name: $category})
                    MERGE (p)-[:SAME_CATEGORY]->(c)
                """, poi_id=poi_id, category=category)
        return True
    
    def get_poi(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """Get POI data"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:POI {poi_id: $poi_id})
                RETURN p
            """, poi_id=poi_id)
            
            record = result.single()
            if record:
                p = record["p"]
                return {
                    "poi_id": p.get("poi_id"),
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "city": p.get("city"),
                    "latitude": p.get("latitude"),
                    "longitude": p.get("longitude"),
                    "rating": p.get("rating"),
                    "price_level": p.get("price_level"),
                    "tags": json.loads(p.get("tags", "[]")),
                    "description": p.get("description"),
                }
        return None
    
    # ==================== User-POI Relationship Operations ====================
    
    def record_visit(
        self,
        user_id: int,
        poi_id: str,
        rating: Optional[float] = None,
        duration: Optional[int] = None,
    ) -> bool:
        """Record user visit to POI"""
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:POI {poi_id: $poi_id})
                MERGE (u)-[r:VISITED]->(p)
                SET r.visit_count = coalesce(r.visit_count, 0) + 1,
                    r.last_visit = timestamp(),
                    r.rating = $rating,
                    r.duration = $duration
            """,
                user_id=user_id,
                poi_id=poi_id,
                rating=rating,
                duration=duration,
            )
        return True
    
    def record_like(self, user_id: int, poi_id: str) -> bool:
        """Record user likes a POI"""
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MATCH (p:POI {poi_id: $poi_id})
                MERGE (u)-[r:LIKES]->(p)
                SET r.like_count = coalesce(r.like_count, 0) + 1,
                    r.last_like = timestamp()
            """,
                user_id=user_id,
                poi_id=poi_id,
            )
        return True
    
    def record_preference(self, user_id: int, category: str, strength: float = 1.0) -> bool:
        """Record user's category preference"""
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {user_id: $user_id})
                MERGE (c:Category {name: $category})
                MERGE (u)-[r:PREFERS]->(c)
                SET r.strength = $strength,
                    r.last_update = timestamp()
            """,
                user_id=user_id,
                category=category,
                strength=strength,
            )
        return True
    
    # ==================== Recommendation Queries ====================
    
    def get_similar_users(
        self,
        user_id: int,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar users based on preferences"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u1:User {user_id: $user_id})-[:PREFERS]->(c:Category)<-[:PREFERS]-(u2:User)
                WITH u2, count(c) as common_interests
                ORDER BY common_interests DESC
                LIMIT $limit
                RETURN u2.user_id as user_id, 
                       u2.interests as interests,
                       common_interests
            """, user_id=user_id, limit=limit)
            
            return [
                {
                    "user_id": record["user_id"],
                    "interests": json.loads(record["interests"]) if record["interests"] else [],
                    "common_interests": record["common_interests"],
                }
                for record in result
            ]
    
    def get_recommended_pois(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get POI recommendations based on user preferences and similar users"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[:PREFERS]->(c:Category)<-[:SAME_CATEGORY]-(p:POI)
                WHERE NOT (u)-[:VISITED]->(p)
                WITH p, c.name as category
                ORDER BY p.rating DESC
                LIMIT $limit
                RETURN p.poi_id as poi_id,
                       p.name as name,
                       p.category as category,
                       p.rating as rating,
                       p.price_level as price_level,
                       category
            """, user_id=user_id, limit=limit)
            
            return [
                {
                    "poi_id": record["poi_id"],
                    "name": record["name"],
                    "category": record["category"],
                    "rating": record["rating"],
                    "price_level": record["price_level"],
                    "matched_category": record["category"],
                }
                for record in result
            ]
    
    def get_poi_relations(
        self,
        poi_id: str,
        radius_km: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """Get nearby POIs and related POIs"""
        with self.driver.session() as session:
            # Get current POI location
            result = session.run("""
                MATCH (p:POI {poi_id: $poi_id})
                RETURN p.latitude as lat, p.longitude as lng
            """, poi_id=poi_id)
            
            record = result.single()
            if not record:
                return []
            
            lat, lng = record["lat"], record["lng"]
            
            # Find nearby POIs (simplified - in production use proper geo queries)
            nearby_result = session.run("""
                MATCH (p1:POI {poi_id: $poi_id})
                MATCH (p2:POI)
                WHERE p1 <> p2
                WITH p2, 
                     point.distance(
                         point({latitude: p1.latitude, longitude: p1.longitude}),
                         point({latitude: p2.latitude, longitude: p2.longitude})
                     ) / 1000 as distance_km
                WHERE distance_km <= $radius_km
                RETURN p2.poi_id as poi_id,
                       p2.name as name,
                       p2.category as category,
                       distance_km
                ORDER BY distance_km
                LIMIT 20
            """, poi_id=poi_id, radius_km=radius_km)
            
            return [
                {
                    "poi_id": r["poi_id"],
                    "name": r["name"],
                    "category": r["category"],
                    "distance_km": r["distance_km"],
                }
                for r in nearby_result
            ]
    
    def get_user_poi_history(
        self,
        user_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get user's POI visit history"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:VISITED]->(p:POI)
                RETURN p.poi_id as poi_id,
                       p.name as name,
                       p.category as category,
                       r.rating as user_rating,
                       r.visit_count as visit_count,
                       r.last_visit as last_visit
                ORDER BY r.last_visit DESC
                LIMIT $limit
            """, user_id=user_id, limit=limit)
            
            return [
                {
                    "poi_id": record["poi_id"],
                    "name": record["name"],
                    "category": record["category"],
                    "user_rating": record["user_rating"],
                    "visit_count": record["visit_count"],
                    "last_visit": record["last_visit"],
                }
                for record in result
            ]
    
    # ==================== Statistics & Analytics ====================
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user interaction statistics"""
        with self.driver.session() as session:
            # Visit count
            visit_result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:VISITED]->(p:POI)
                RETURN count(r) as visit_count, 
                       sum(r.visit_count) as total_visits,
                       avg(r.rating) as avg_rating
            """, user_id=user_id)
            
            visit_record = visit_result.single()
            
            # Like count
            like_result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:LIKES]->(p:POI)
                RETURN count(r) as like_count
            """, user_id=user_id)
            
            like_record = like_result.single()
            
            # Category preferences
            pref_result = session.run("""
                MATCH (u:User {user_id: $user_id})-[r:PREFERS]->(c:Category)
                RETURN c.name as category, r.strength as strength
                ORDER BY r.strength DESC
            """, user_id=user_id)
            
            categories = {r["category"]: r["strength"] for r in pref_result}
            
            return {
                "unique_pois_visited": visit_record["visit_count"] if visit_record else 0,
                "total_visits": visit_record["total_visits"] if visit_record else 0,
                "average_rating": float(visit_record["avg_rating"]) if visit_record and visit_record["avg_rating"] else 0.0,
                "total_likes": like_record["like_count"] if like_record else 0,
                "top_categories": categories,
            }


# ==================== Singleton Instance ====================
_kg_service: Optional[KnowledgeGraphService] = None


def get_kg_service() -> KnowledgeGraphService:
    """Get knowledge graph service singleton"""
    global _kg_service
    if _kg_service is None:
        from app.config import settings
        _kg_service = KnowledgeGraphService(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )
    return _kg_service
