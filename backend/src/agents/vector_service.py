"""
Milvus Vector Service - User Profile Vector Storage
"""
import json
import numpy as np
from typing import Dict, List, Optional, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility


class VectorService:
    def __init__(self):
        self.host = "localhost"
        self.port = 19530
        self.collection_name = "user_profiles"
        self.connected = False
        self.collection = None

    def connect(self) -> bool:
        """Connect to Milvus"""
        try:
            if not connections.has_connection("default"):
                connections.connect(host=self.host, port=self.port)

            self.connected = True
            print(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            self.connected = False
            return False

    def is_connected(self) -> bool:
        """Check if connected to Milvus"""
        if not self.connected:
            return self.connect()
        return True

    def create_collection_if_not_exists(self) -> bool:
        """Create collection if not exists"""
        try:
            if not self.is_connected():
                return False

            # Check if collection exists
            if utility.has_collection(self.collection_name):
                # Collection exists, just load it
                self.collection = Collection(self.collection_name)
                self.collection.load()
                print(f"Collection '{self.collection_name}' loaded successfully")
                return True

            # Create new collection
            fields = [
                FieldSchema(name="user_id", dtype=DataType.INT64, is_primary=True, description="User ID"),
                FieldSchema(name="interests", dtype=DataType.VARCHAR, max_length=2000, description="User interests as JSON string"),
                FieldSchema(name="budget_level", dtype=DataType.VARCHAR, max_length=50, description="Budget level: low/medium/high"),
                FieldSchema(name="travel_style", dtype=DataType.VARCHAR, max_length=50, description="Travel style: relaxed/balanced/intensive"),
                FieldSchema(name="group_type", dtype=DataType.VARCHAR, max_length=50, description="Group type: solo/couple/family/group"),
                FieldSchema(name="fitness_level", dtype=DataType.VARCHAR, max_length=50, description="Fitness level: low/medium/high"),
                FieldSchema(name="age_group", dtype=DataType.VARCHAR, max_length=50, description="Age group: youth/adult/senior"),
                FieldSchema(name="has_children", dtype=DataType.VARCHAR, max_length=10, description="Has children: true/false"),
                FieldSchema(name="price_sensitivity", dtype=DataType.FLOAT, description="Price sensitivity 0-1"),
                FieldSchema(name="refined_interests", dtype=DataType.VARCHAR, max_length=2000, description="Refined interests as JSON string"),
                FieldSchema(name="cultural_preferences", dtype=DataType.VARCHAR, max_length=2000, description="Cultural preferences as JSON string"),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128, description="Profile embedding vector"),
            ]

            schema = CollectionSchema(fields, description="User profile vectors for trip recommendation")
            self.collection = Collection(self.collection_name, schema)

            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128}
            }
            self.collection.create_index(field_name="embedding", index_params=index_params)
            self.collection.load()
            print(f"Collection '{self.collection_name}' created successfully")
            return True
        except Exception as e:
            print(f"Failed to create collection: {e}")
            return False

    def upsert_profile(self, user_id: int, profile: Dict[str, Any]) -> Optional[str]:
        """Save user profile vector to Milvus"""
        try:
            if not self.create_collection_if_not_exists():
                return None

            # Generate embedding from profile (simplified)
            embedding = self._generate_profile_embedding(profile)

            # Convert has_children to string
            has_children_str = "true" if profile.get("has_children", False) else "false"

            entities = [
                [user_id],
                [json.dumps(profile.get("interests", []))],
                [profile.get("budget_level", "medium")],
                [profile.get("travel_style", "balanced")],
                [profile.get("group_type", "solo")],
                [profile.get("fitness_level", "medium")],
                [profile.get("age_group", "adult")],
                [has_children_str],
                [float(profile.get("price_sensitivity", 0.5))],
                [json.dumps(profile.get("refined_interests", []))],
                [json.dumps(profile.get("cultural_preferences", {}))],
                [embedding.tolist()],
            ]

            # Delete existing profile first (upsert behavior)
            try:
                self.collection.delete(f"user_id == {user_id}")
                self.collection.flush()
            except Exception:
                pass  # Ignore if no existing record

            self.collection.insert(entities)
            self.collection.flush()
            print(f"User profile saved to Milvus for user_id: {user_id}")
            return str(user_id)
        except Exception as e:
            print(f"Failed to upsert profile: {e}")
            return None

    def search_similar(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict]:
        """Search similar profiles"""
        try:
            if not self.is_connected():
                return []

            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["user_id", "interests", "budget_level", "fitness_level",
                               "travel_style", "group_type", "age_group", "has_children",
                               "price_sensitivity", "refined_interests", "cultural_preferences"]
            )

            similar_profiles = []
            for hit in results[0]:
                similar_profiles.append({
                    "user_id": hit.entity.get("user_id"),
                    "interests": json.loads(hit.entity.get("interests", "[]")),
                    "budget_level": hit.entity.get("budget_level"),
                    "fitness_level": hit.entity.get("fitness_level"),
                    "travel_style": hit.entity.get("travel_style"),
                    "group_type": hit.entity.get("group_type"),
                    "age_group": hit.entity.get("age_group"),
                    "has_children": hit.entity.get("has_children"),
                    "price_sensitivity": hit.entity.get("price_sensitivity"),
                    "refined_interests": json.loads(hit.entity.get("refined_interests", "[]")),
                    "cultural_preferences": json.loads(hit.entity.get("cultural_preferences", "{}")),
                    "distance": hit.distance
                })
            return similar_profiles
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def _generate_profile_embedding(self, profile: Dict[str, Any]) -> np.ndarray:
        """Generate embedding vector from profile"""
        # Create a deterministic embedding based on profile attributes
        interests = profile.get("interests", [])
        budget = profile.get("budget_level", "medium")
        fitness = profile.get("fitness_level", "medium")
        travel_style = profile.get("travel_style", "balanced")
        group_type = profile.get("group_type", "solo")
        age_group = profile.get("age_group", "adult")
        price_sensitivity = profile.get("price_sensitivity", 0.5)

        # Create a unique seed from all profile attributes
        seed = hash(
            str(interests) + budget + fitness + travel_style +
            group_type + age_group + str(price_sensitivity)
        ) % (2**31)
        np.random.seed(seed)
        embedding = np.random.randn(128)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)


# Global instance
_vector_service = None

def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
