from typing import Any, Dict, List, Optional
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility


class VectorService:
    """
    Vector storage service for user profiles and POI embeddings
    Uses Milvus for similarity search
    """

    COLLECTION_NAME = "user_profiles"
    DIMENSION = 128  # Profile vector dimension

    def __init__(self):
        self.connected = False
        self._connect()

    def _connect(self):
        """Connect to Milvus"""
        try:
            # Try to connect to Milvus
            connections.connect(
                host="localhost",
                port="19530"
            )
            self.connected = True
            self._ensure_collection()
        except Exception as e:
            print(f"Warning: Milvus not available: {e}")
            self.connected = False

    def _ensure_collection(self):
        """Ensure collection exists"""
        if not self.connected:
            return

        try:
            if not utility.has_collection(self.COLLECTION_NAME):
                # Create collection schema
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="user_id", dtype=DataType.INT64),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.DIMENSION),
                    FieldSchema(name="interests", dtype=DataType.VARCHAR, max_length=500),
                    FieldSchema(name="budget_level", dtype=DataType.VARCHAR, max_length=20),
                    FieldSchema(name="travel_style", dtype=DataType.VARCHAR, max_length=20),
                    FieldSchema(name="fitness_level", dtype=DataType.VARCHAR, max_length=20),
                    FieldSchema(name="profile_json", dtype=DataType.VARCHAR, max_length=4000),
                ]
                schema = CollectionSchema(fields, description="User profile vectors")
                collection = Collection(self.COLLECTION_NAME, schema)

                # Create index
                index_params = {
                    "metric_type": "IP",  # Inner product for cosine similarity
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                collection.create_index("vector", index_params)
            else:
                collection = Collection(self.COLLECTION_NAME)
                collection.load()
        except Exception as e:
            print(f"Warning: Failed to ensure collection: {e}")
            self.connected = False

    def is_connected(self) -> bool:
        """Check if Milvus is connected"""
        return self.connected

    def profile_to_vector(self, profile: Dict[str, Any]) -> List[float]:
        """
        Convert user profile to vector embedding
        Uses simple hashing-based embedding
        """
        # Collect all profile features
        features = []

        # Interests (weighted)
        interests = profile.get("interests", [])
        interest_weights = {
            "culture": 0.9, "food": 0.85, "nature": 0.8,
            "religion": 0.6, "entertainment": 0.7, "shopping": 0.5,
            "photography": 0.65, "sports": 0.7, "wellness": 0.6
        }
        for interest in interests:
            weight = interest_weights.get(interest.lower(), 0.5)
            features.append(weight)

        # Budget level (0-1)
        budget_map = {"low": 0.3, "medium": 0.6, "high": 1.0}
        budget = budget_map.get(profile.get("budget_level", "medium").lower(), 0.6)
        features.append(budget)

        # Travel style
        style_map = {"relaxed": 0.3, "balanced": 0.5, "intensive": 0.9}
        style = style_map.get(profile.get("travel_style", "balanced").lower(), 0.5)
        features.append(style)

        # Fitness level
        fitness_map = {"low": 0.3, "medium": 0.6, "high": 1.0}
        fitness = fitness_map.get(profile.get("fitness_level", "medium").lower(), 0.6)
        features.append(fitness)

        # Cultural preferences
        cultural = profile.get("cultural_preferences", {})
        if isinstance(cultural, dict) and "dimensions" in cultural:
            dims = cultural.get("dimensions", {})
            for dim in ["history", "art", "tradition", "modern", "nature", "food_culture"]:
                features.append(dims.get(dim, 0.3))

        # Group type
        group_map = {"solo": 0.3, "couple": 0.5, "family": 0.7, "friends": 0.6}
        group = group_map.get(profile.get("group_type", "solo").lower(), 0.3)
        features.append(group)

        # Pad or truncate to fixed dimension
        while len(features) < self.DIMENSION:
            features.append(0.0)
        features = features[:self.DIMENSION]

        # Normalize
        vector = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def upsert_profile(
        self,
        user_id: int,
        profile: Dict[str, Any],
    ) -> Optional[str]:
        """Insert or update user profile vector"""
        if not self.connected:
            return None

        try:
            collection = Collection(self.COLLECTION_NAME)
            collection.load()

            # Generate vector
            vector = self.profile_to_vector(profile)

            # Prepare data
            import json
            interests_str = ",".join(profile.get("interests", []))
            profile_json = json.dumps(profile, ensure_ascii=False)

            data = [[user_id], [vector], [interests_str],
                   [profile.get("budget_level", "medium")],
                   [profile.get("travel_style", "balanced")],
                   [profile.get("fitness_level", "medium")],
                   [profile_json]]

            # Check if exists
            expr = f"user_id == {user_id}"
            results = collection.query(expr, output_fields=["id"])
            
            if results:
                # Update - delete first then insert
                collection.delete(expr)
            
            # Insert
            collection.insert(data)
            collection.flush()

            return f"user_{user_id}"

        except Exception as e:
            print(f"Error upserting profile: {e}")
            return None

    def search_similar_users(
        self,
        profile: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar users based on profile"""
        if not self.connected:
            return []

        try:
            collection = Collection(self.COLLECTION_NAME)
            collection.load()

            vector = self.profile_to_vector(profile)

            search_params = {"metric_type": "IP", "params": {"nprobe": 10}}

            results = collection.search(
                data=[vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                output_fields=["user_id", "interests", "budget_level", "travel_style"]
            )

            similar_users = []
            for hits in results:
                for hit in hits:
                    similar_users.append({
                        "user_id": hit.entity.get("user_id"),
                        "interests": hit.entity.get("interests", "").split(","),
                        "budget_level": hit.entity.get("budget_level"),
                        "travel_style": hit.entity.get("travel_style"),
                        "score": hit.score
                    })

            return similar_users

        except Exception as e:
            print(f"Error searching similar users: {e}")
            return []

    def delete_profile(self, user_id: int) -> bool:
        """Delete user profile vector"""
        if not self.connected:
            return False

        try:
            collection = Collection(self.COLLECTION_NAME)
            expr = f"user_id == {user_id}"
            collection.delete(expr)
            collection.flush()
            return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False


# Singleton instance
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Get vector service singleton"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
